from modules.basic.basic_module import BasicModule
from modules.mqtt.mqtt import MQTTClient
from serial_log import SerialLog
from ubinascii import hexlify
from machine import unique_id, reset
from network import WLAN, STA_IF
from modules.web.web_processor import okayHeader, unquote
from ujson import dumps, load
from time import ticks_ms, ticks_diff
from modules.ota.ota import local_version

class HomeAssistantControl(BasicModule):

    def __init__(self):
        self.haPrefixUrl = "homeassistant"
        self.deviceId = hexlify(unique_id()).decode('ascii')
        self.telemetry = {}
        self.client = None
        self.topics = {}
        self.version = local_version()
        self.ip = "0.0.0.0"
        self.commands = []
        self.connected = False
        self.lastConnectTime = 0
        self.lastConfigureTime = 0
        self.lastFullTelemetrySend = 0
        self.lastKeepAliveSend = 0
    
    def start(self):
        BasicModule.start(self)
        self.enabled = self.getPref("homeassistant", "enabled", "Y")
        self.mqtt_server = self.getPref("homeassistant", "mqtt_server", "mqtt.example.com")
        
        # set some defaults for timers
        self.lastConnectTime = ticks_ms() - 90000
        self.lastConfigureTime = ticks_ms() - 90000
        self.lastFullTelemetrySend = ticks_ms() - 90000

        if self.enabled != "Y":
            SerialLog.log("Home Assistant Integration Disabled")
        else:
            SerialLog.log("Home Assistant Integration Enabled")            
         
    def tick(self):
        if self.enabled == "Y" and WLAN(STA_IF).isconnected():
            if not self.connected:
                self.connect_and_subscribe()
            if self.connected:
                try:
                    self.client.check_msg()
                except:
                    self.connected = False
                    SerialLog.log("Error checking MQTT messages (HA)")
    
    def getTelemetry(self):
        # Convert lastConnectTime, lastFullTelemetrySend and lastConfigureTime to a human-readable format (seconds)
        lastConnectTimeS = ticks_diff(ticks_ms(), self.lastConnectTime) // 1000
        lastConfigureTimeS = ticks_diff(ticks_ms(), self.lastConfigureTime) // 1000
        lastFullTelemetrySendS = ticks_diff(ticks_ms(), self.lastFullTelemetrySend) // 1000

        return {
            "homeassistantserver": self.mqtt_server,
            "homeassistantconnected": self.connected,
            "homeassistantenabled": self.enabled,
            "homeassistantlastconnecttime": lastConnectTimeS,
            "homeassistantlastconfigtime": lastConfigureTimeS,
            "homeassistantlastfulltelemetrysend": lastFullTelemetrySendS
        }

    def processTelemetry(self, telemetry):

        # Capture critical telemetry
        if "ip" in telemetry:
            self.ip = telemetry["ip"]
        if "version" in telemetry:
            self.version = telemetry["version"]

        # if not enabled, or not connected to wifi, or not connected to HA, return
        if self.enabled != "Y" or not WLAN(STA_IF).isconnected() or not self.connected:
            return
        
        # wait until critical telemetry is received
        if self.ip == "0.0.0.0":
            return

        if ticks_diff(ticks_ms(), self.lastConfigureTime) > 3600000:
            SerialLog.log("Re-registering with Home Assistant, wiping all configured keys")
            self.lastConfigureTime = ticks_ms()
            self.topics.clear()

        for attr, value in telemetry.items():
            if attr.startswith('ledprimary'):
                attr = 'ledprimary'
            elif attr.startswith('ledsecondary'):
                attr = 'ledsecondary'
            if attr not in self.topics:
                self.home_assistant_configure(attr, value)

        # configure home assistant with a reboot button too
        if "rebootbtn" not in self.topics:
            self.home_assistant_configure("rebootbtn", 0)

        # configure home assistant with a reboot button too
        if "switch/messageled" not in self.topics:
            self.home_assistant_configure("switch/messageled", 0)


        if self.hasTelemetryChanged(telemetry):
            processed = set()
            for attr, value in telemetry.items():
                if attr.startswith('ledprimary'):
                    attr = 'ledprimary'
                elif attr.startswith('ledsecondary'):
                    attr = 'ledsecondary'
                if attr in processed:
                    continue
                if attr in self.topics:
                    if attr not in self.telemetry or self.telemetry[attr] != value:
                        self.sendSingleTelemetry(attr, value, telemetry)
                else:
                    SerialLog.log("No topic for %s" % (attr))
                processed.add(attr)

            self.telemetry = telemetry.copy()

    def sendSingleTelemetry(self, attr, value, telemetry):
        if isinstance(value, bytes):
            value = value.decode('ascii')

        if attr.startswith('ledprimary'):
            state = {
                "state": telemetry["ledstate"],
                "brightness": telemetry["ledbrightness"],
                "color_mode": "rgb",
                "color": {
                    "r": telemetry["ledprimaryr"],
                    "g": telemetry["ledprimaryg"],
                    "b": telemetry["ledprimaryb"]
                },
                "effect": telemetry["ledaction"]
            }
            self.safePublish("%s/state" % (self.topics['ledprimary']), dumps(state), True)

        elif attr.startswith('ledsecondary'):
            state = {
                "state": telemetry["ledstate"],
                "brightness": telemetry["ledbrightness"],
                "color_mode": "rgb",
                "color": {
                    "r": telemetry["ledsecondaryr"],
                    "g": telemetry["ledsecondaryg"],
                    "b": telemetry["ledsecondaryb"]
                },
                "effect": telemetry["ledaction"]
            }
            self.safePublish("%s/state" % (self.topics['ledsecondary']), dumps(state), True)
        else:
            self.safePublish("%s/state" % (self.topics[attr]), str(value), True)

    def getCommands(self):
        c = self.commands
        self.commands = []
        return c

    def processCommands(self, commands):
        # if commanded to reboot, do so
        if "/system/reboot" in commands:
            reset()

    def getRoutes(self):
        return {
            b"/ha": b"/modules/homeassistant/web_ha.html", 
            b"/haloadsettings": self.loadhasettings,
            b"/hasavesettings": self.savehasettings,
        }

    def hasTelemetryChanged(self, newTelemetry):
        if ticks_diff(ticks_ms(), self.lastFullTelemetrySend) > 60000:
            self.lastFullTelemetrySend = ticks_ms()
            return True

        for attr, value in newTelemetry.items():
            if value != self.telemetry.get(attr) and attr not in {"time", "voltage", "freeram", "rssi", "wifiUptime", "homeassistantlastconnecttime", "homeassistantlastconfigtime", "homeassistantlastfulltelemetrysend"}:
                return True
        return False
    
    def loadhasettings(self, params):
        headers = okayHeader
        data = b"{ \"enable\": \"%s\", \"server\": \"%s\", \"username\": \"%s\", \"password\":\"%s\" }" % (
            self.enabled, self.mqtt_server, self.getPref("homeassistant", "mqtt_user", ""), self.getPref("homeassistant", "mqtt_password", ""))
        return data, headers
    
    def savehasettings(self, params):
        self.setPref("homeassistant", "enabled", unquote(params.get(b"enable", None)))
        self.setPref("homeassistant", "mqtt_server", unquote(params.get(b"server", None)))
        self.setPref("homeassistant", "mqtt_user", unquote(params.get(b"username", None)))
        self.setPref("homeassistant", "mqtt_password", unquote(params.get(b"password", None)))

        headers = b"HTTP/1.1 307 Temporary Redirect\r\nLocation: /\r\n"

        # Reset the connection, load the new settings
        self.connected = False
        self.enabled = self.getPref("homeassistant", "enabled", "Y")
        self.mqtt_server = self.getPref("homeassistant", "mqtt_server", "mqtt.example.com")
        try:
          self.client.disconnect()
        except:
            pass

        return b"", headers

    def sub_cb(self, topic, msg):
        SerialLog.log("HA MQTT Command Received: ", topic, msg)
        
        msg = msg.decode('ascii')

        if b"ledprimary" in topic:
            base = "/ledprimary"
            self.commands.append("%s/%s" % (base, msg))
        elif b"ledsecondary" in topic:
            base = "/ledsecondary"
            self.commands.append("%s/%s" % (base, msg))
        else:
            self.commands.append(msg)
    
    def connect_and_subscribe(self):
        if ticks_diff(ticks_ms(), self.lastConnectTime) > 90000:
            SerialLog.log('Connecting to %s HA MQTT broker...' % (self.mqtt_server))
            self.lastConnectTime = ticks_ms()

            self.client = MQTTClient(b"ha-%s" % (self.deviceId), self.mqtt_server, 1883, self.getPref("homeassistant", "mqtt_user", ""), self.getPref("homeassistant", "mqtt_password", ""), 300)
            self.client.set_callback(self.sub_cb)
            self.client.set_last_will("%s/sensor/%s/keepalive" % (self.haPrefixUrl, self.deviceId), "offline", True)
            self.client.connect()
            self.telemetry.clear()
            self.topics.clear()
            self.client.subscribe("homeassistant/+/%s/+/command" % (self.deviceId))
            SerialLog.log('Connected to %s HA MQTT broker' % (self.mqtt_server))
            self.connected = True
            self.safePublish("%s/sensor/%s/keepalive" % (self.haPrefixUrl, self.deviceId), "online", False)
    
    def get_basic_payload(self, name, uniqueid, attr, value):
        wlan_mac = WLAN(STA_IF).config('mac')
        my_mac_addr = hexlify(wlan_mac, ':').decode().upper()

        basicPayload = { 
            "name": name,
            "uniq_id": uniqueid,
            "dev": {
                "cns": [["mac", my_mac_addr]],
                "mf": "Wolfen",
                "name": "%s - %s" % (self.getPref("web", "name", self.basicSettings["name"]), self.deviceId),
                "sw": self.version,
                "mdl": self.basicSettings["shortName"],
                "cu": "http://%s" % (self.ip)
            },
            "stat_t": "~/state",
            "avty_t": "%s/sensor/%s/keepalive" % (self.haPrefixUrl, self.deviceId),
            "pl_avail": "online",
        }
        if isinstance(value, (int, float)):
            basicPayload.update({
                 "unit_of_meas": "item(s)",
                  "stat_cla": "measurement"
                 })
        return basicPayload

    def home_assistant_configure(self, key, value):
        if key not in self.topics:
            attr = key.replace("/", "_")
            telemetryId = "%s_%s" % (self.deviceId, attr)

            nameLookup = load(open("modules/homeassistant/name.json", 'r'))
            uomLookup = load(open("modules/homeassistant/uom.json", 'r'))
            devClassLookup = load(open("modules/homeassistant/devclass.json", 'r'))

            lookupkey = key.split("/")[0].lower()
            name = nameLookup.get(lookupkey, nameLookup.get(key, key))
            uom = uomLookup.get(lookupkey, "")
            devclass = devClassLookup.get(lookupkey, "")
            telemetryType = "sensor"
                        
            if "/" in key:
                name = "%s %s" % (name, key.split("/")[1])
            payload = self.get_basic_payload(name, telemetryId, attr, value) 
            if uom:
                payload.update({ "unit_of_meas": uom })
            if devclass:
                payload.update({ "dev_cla": devclass })

            if key.startswith('ledprimary') or key.startswith('ledsecondary'):
                ledconfig = load(open("modules/homeassistant/ledprimary.json" if key.startswith('ledprimary') else "modules/homeassistant/ledsecondary.json", 'r'))
                payload.update(ledconfig)
                payload.update({ "unique_id": telemetryId })
                telemetryType = "light"

            if key.startswith('relay'):
                payload.update({ "payload_on": "/relay/on/"+key[-1], "payload_off": "/relay/off/"+key[-1], "cmd_t": "~/command", "state_off": 0, "state_on": 1 })
                telemetryType = "switch"

            if key.startswith('switch'):
                # get the part after switch/
                endbit = key.split("/")[1]
                payload.update({ "payload_on": "/switch/on/"+endbit, "payload_off": "/switch/off/"+endbit, "cmd_t": "~/command", "state_off": 0, "state_on": 1 })
                telemetryType = "switch"

            if key.startswith('mosfet'):
                payload.update({ "payload_on": "/mosfet/on/"+key[-1], "payload_off": "/mosfet/off/"+key[-1], "cmd_t": "~/command", "state_off": 0, "state_on": 1 })
                telemetryType = "switch"

            if key.startswith('trigger'):
                payload.update({ "payload_on": "/mosfet/on/"+key[-1], "payload_press": "/trigger/"+key[-1], "cmd_t": "~/command" })
                telemetryType = "button"                

            if key.startswith('rebootbtn'):
                payload.update({ "payload_on": "/system/reboot", "payload_press": "/system/reboot", "cmd_t": "~/command" })
                telemetryType = "button" 

            if key.startswith('button'):
                # get the part after button/
                endbit = key.split("/")[1]
                payload.update({ "payload_press": "/button/press/"+endbit, "cmd_t": "~/command" })
                telemetryType = "button" 

            if key.startswith('temperature'):
                payload.update({ "state_class": "measurement" })

            telemetryUrl = "%s/%s/%s/%s" % (self.haPrefixUrl, telemetryType, self.deviceId, telemetryId)
            payload.update({"~": telemetryUrl}),
            topic = "%s/config" % (telemetryUrl)
            self.topics[key] = telemetryUrl
            self.safePublish(topic, dumps(payload), True)

    def safePublish(self, topic, message, retain=False):
        try:
            self.client.publish(topic, message, retain)
        except OSError as e:
            SerialLog.log("Error publishing MQTT message: %s" % (e))
            self.connected = False

    def getIndexFileName(self):
        return { "homeassistant" : "/modules/homeassistant/homeassistant_index.html" }