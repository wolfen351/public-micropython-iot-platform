from modules.basic.basic_module import BasicModule
from modules.mqtt.mqtt import MQTTClient
from serial_log import SerialLog
from ubinascii import hexlify
from machine import unique_id
from network import WLAN, STA_IF
from modules.web.web_processor import okayHeader, unquote
from ujson import dumps, load
from time import time, ticks_ms

class HomeAssistantControl(BasicModule):

    def __init__(self):
        self.haPrefixUrl = "homeassistant"
        self.deviceId = hexlify(unique_id()).decode('ascii')
        self.telemetry = {}
        self.client = None
        self.lastConnectTime = 0 # to stop from spamming the reconnect
        self.topics = {}
        self.version = b"1.0.0"
        self.ip = b"0.0.0.0"
        self.commands = []
        self.lastConfigureTime = 0
        self.connected = False
        self.lastFullTelemetrySend = 0
    
    def start(self):
        BasicModule.start(self)
        self.enabled = self.getPref("homeassistant", "enabled", "Y")
        self.mqtt_server = self.getPref("homeassistant", "mqtt_server", "mqtt.wolfen.za.net")

        if (not self.enabled == b"Y"):
            SerialLog.log("Home Assistant Integration Disabled")
        else:
            SerialLog.log("Home Assistant Integration Enabled")            
         
    def tick(self):
        if (self.enabled == "Y" and WLAN(STA_IF).isconnected()):
            if (not self.connected):
                self.connect_and_subscribe()
            if (self.connected):
                self.client.check_msg()
    
    def getTelemetry(self):
        return {}

    
    def processTelemetry(self, telemetry):

        if (self.enabled != "Y"):
            return

        if (not WLAN(STA_IF).isconnected()):
            return

        # wait for mqtt connection
        if (not self.connected):
            return

        # record telemetry we may need
        if "ip" in self.telemetry:
            self.ip = self.telemetry["ip"]
        if "version" in self.telemetry:
            self.version = self.telemetry["version"]

        # wipe configured keys every hour, so we reregister with ha 
        if (time() - self.lastConfigureTime > 3600):
            SerialLog.log("Re-registering with Home Assistant, wiping all configured keys")
            self.lastConfigureTime = time()
            self.topics = {}

        # tell home assistant about any new keys
        for attr, value in telemetry.items():
            if attr not in self.topics:
                self.home_assistant_configure(attr, value)

        # tell home assistant about any new values
        if (self.hasTelemetryChanged(telemetry)):

            # publish all the separate telemetry values to homeassistant/sensor/deviceid/telemetryid/state
            for attr, value in telemetry.items():
                if (attr in self.topics):
                    # if value is bytes then convert to string first
                    if (isinstance(value, bytes)):
                        value = value.decode('ascii')
                    self.safePublish("%s/state" % (self.topics[attr]), str(value), True)
                else:
                    SerialLog.log("No topic for %s" % (attr))

            if ("ledprimary" in telemetry):
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
                self.safePublish("%s/%s/%s/ledprimaryrgbstate" % (self.haPrefixUrl, "light", self.deviceId), dumps(state), True)

            if ("ledsecondary" in telemetry):
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
                self.safePublish("%s/%s/%s/ledsecondaryrgbstate" % (self.haPrefixUrl, "light", self.deviceId), dumps(state), True)
            self.telemetry = telemetry.copy()

    
    def getCommands(self):
        c = self.commands
        self.commands = []
        return c

    
    def processCommands(self, commands):
        pass

    
    def getRoutes(self):
        return {
            b"/ha": b"/modules/homeassistant/web_ha.html", 
            b"/haloadsettings": self.loadhasettings,
            b"/hasavesettings": self.savehasettings,
        }

    # Internal Code 
    def hasTelemetryChanged(self, newTelemetry):
        thingsThatChanged = 0

        # every 60s send a full telemetry packet
        if (time() - self.lastFullTelemetrySend > 60):
            self.lastFullTelemetrySend = time()
            return True

        # otherwise send only the changes
        for attr, value in newTelemetry.items():
            if (value != self.telemetry.get(attr)):
                if (attr != "time" and attr != "voltage" and attr != "freeram" and attr != "rssi"): # dont post the time or voltage every second
                    thingsThatChanged += 1
        return thingsThatChanged > 0
    
    def loadhasettings(self, params):
        headers = okayHeader
        data = b"{ \"enable\": \"%s\", \"server\": \"%s\", \"username\": \"%s\", \"password\":\"%s\" }" % (self.enabled, self.mqtt_server, self.getPref("homeassistant", "mqtt_user", ""), self.getPref("homeassistant", "mqtt_password", ""))
        return data, headers
    
    def savehasettings(self, params):
        # Read form params
        self.setPref("homeassistant", "enabled", unquote(params.get(b"enable", None)))
        self.setPref("homeassistant", "mqtt_server", unquote(params.get(b"server", None)))
        self.setPref("homeassistant", "mqtt_user", unquote(params.get(b"username", None)))
        self.setPref("homeassistant", "mqtt_password", unquote(params.get(b"password", None)))

        headers = b"HTTP/1.1 307 Temporary Redirect\r\nLocation: /\r\n"
        return b"", headers

    
    def sub_cb(self, topic, msg):
        SerialLog.log("HA MQTT Command Received: ", topic, msg)
        # if the topic ends with command then add it to the commands list
        if (topic.endswith("command")):
            self.commands.append(msg)
    
    def connect_and_subscribe(self):
        if (self.lastConnectTime + 30000 < ticks_ms()):
            SerialLog.log('Connecting to %s HA MQTT broker...' % (self.mqtt_server))
            self.lastConnectTime = ticks_ms()

            self.client = MQTTClient(b"ha-%s" % (self.deviceId), self.mqtt_server, 1883, self.getPref("homeassistant", "mqtt_user", ""), self.getPref("homeassistant", "mqtt_password", ""))
            self.client.set_callback(self.sub_cb)
            self.client.connect()
            # Wipe all existing telemetry so we send a full update on connect
            self.telemetry = {} 
            self.topics = {}
            self.client.subscribe("homeassistant/switch/%s/+/command" % (self.deviceId))
            self.client.subscribe("homeassistant/light/%s/+/command" % (self.deviceId))
            SerialLog.log('Connected to %s HA MQTT broker' % (self.mqtt_server))
            self.connected = True
    
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
            "stat_t": "~/state"
        }
        # if the value is a number then update the payload
        if (isinstance(value, int) or isinstance(value, float)):
            basicPayload.update({
                 "unit_of_meas": "item(s)",
                  "stat_cla": "measurement"
                 })
        return basicPayload

    
    def home_assistant_configure(self, key, value):
        
        if key not in self.topics:
            attr = key.replace("/","_")
            telemetryId = "%s_%s" % (self.deviceId, attr) #43jh34hg4_temp_jhgfddfdsfd

            nameLookup = load(open("modules/homeassistant/name.json",'r'))
            uomLookup = load(open("modules/homeassistant/uom.json",'r'))
            devClassLookup = load(open("modules/homeassistant/devclass.json",'r'))

            lookupkey = key.split("/")[0]
            name = nameLookup.get(lookupkey, key)
            uom = uomLookup.get(lookupkey, "")
            devclass = devClassLookup.get(lookupkey, "")
            telemetryType = "sensor"
                        
            # if the key contains a / add the text after the / to the name
            if (key.find("/") > -1):
                name = name + " (%s)" % (key.split("/")[1])
            payload = self.get_basic_payload(name, telemetryId, attr, value) 
            if (uom != ""):
                payload.update({ "unit_of_meas": uom })
            if (devclass != ""):
                payload.update({ "dev_cla": devclass })

            if (key.startswith('ledprimaryb') or key.startswith('ledsecondaryb')):
                payload.pop("val_tpl")
                if (key.startswith('ledprimaryb')):
                    ledconfig = load(open("modules/homeassistant/ledprimary.json",'r'))
                else:
                    ledconfig = load(open("modules/homeassistant/ledsecondary.json",'r'))
                payload.update(ledconfig)
                payload.update( { "unique_id": telemetryId })
                telemetryType = "light"

            if (key.startswith('relay') or key.startswith('mosfet')):
                payload.update({ "payload_on": "/relay/on", "payload_off": "/relay/off", "cmd_t": "~/command", "state_off": 0, "state_on": 1 })
                telemetryType = "switch"

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
