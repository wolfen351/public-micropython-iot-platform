from modules.basic.basic_module import BasicModule
from modules.homeassistant.homeassistant_settings import HomeAssistantSettings
from modules.mqtt.mqtt import MQTTClient
from serial_log import SerialLog
from ubinascii import hexlify
from machine import unique_id
import network
from modules.web.web_processor import okayHeader, unquote
from ujson import dumps
from time import time, ticks_ms

class HomeAssistantControl(BasicModule):

    def __init__(self):
        self.client_id = hexlify(unique_id())
        self.sta_if = network.WLAN(network.STA_IF)
        self.homeAssistantUrl = "homeassistant"
        self.homeAssistantSensorUrl = "%s/sensor/%s" % (self.homeAssistantUrl, self.client_id.decode('ascii'))
        self.homeAssistantLightUrl = "%s/light/%s" % (self.homeAssistantUrl, self.client_id.decode('ascii'))
        self.mqtt_port = 1883
        self.mqtt_user = None
        self.mqtt_password = None
        self.telemetry = {}
        self.client = None
        self.last_connect = 0 # to stop from spamming the reconnect
        self.configuredKeys = []
        self.version = b"1.0.0"
        self.ip = b"0.0.0.0"
        self.commands = []
        self.lastHourCheck = 0
        self.connected = False
        self.lastFullTelemetrySend = 0
    
    def start(self):
        BasicModule.start(self)
        settings = HomeAssistantSettings()
        settings.load()
        self.enabled = settings.Enable
        self.mqtt_server = settings.Server
        if (settings.Subscribe != b""):
            self.topic_sub = settings.Subscribe
        else:
            self.topic_sub = b'homeassistant/sensor/%s/command/#' % (self.client_id)

        if (settings.Publish != b""):
            self.topic_pub = settings.Publish
        else:
            self.topic_pub = b'homeassistant/sensor/%s/state' % (self.client_id)
        self.mqtt_user = settings.Username
        self.mqtt_password = settings.Password
        if (not self.enabled == b"Y"):
            SerialLog.log("Home Assistant Integration Disabled")
        else:
            SerialLog.log("Home Assistant Integration Enabled")            

         
    def tick(self):
        if (self.enabled == b"Y" and self.sta_if.isconnected()):
            if (not self.connected):
                self.connect_and_subscribe()
            if (self.connected):
                self.client.check_msg()
    
    def getTelemetry(self):
        return {}

    
    def processTelemetry(self, telemetry):

        if (self.enabled != b"Y"):
            return

        # wait for wifi connection
        if (not self.sta_if.isconnected()):
            return

        # wait for mqtt connection
        if (not self.connected):
            return

        # record telemetry we may need
        for attr, value in self.telemetry.items():
            if (attr == "ip"):
                self.ip = value
            if (attr == "version"):
                self.version = value

        # wipe configured keys every hour, so we reregister with ha 
        if (time() - self.lastHourCheck > 3600):
            SerialLog.log("Re-registering with Home Assistant, wiping all configured keys")
            self.lastHourCheck = time()
            self.configuredKeys = []         

        # tell home assistant about any new keys
        for attr, value in self.telemetry.items():
            if (attr not in self.configuredKeys):
                self.home_assistant_configure(attr, value)

        # tell home assistant about any new values
        if (self.hasTelemetryChanged(telemetry)):
            messageToSend = dumps(telemetry).replace("/","_")
            self.safePublish("%s/state" % self.homeAssistantSensorUrl, messageToSend)

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
                self.safePublish(self.homeAssistantSensorUrl + "/ledprimaryrgbstate", dumps(state))

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
                self.safePublish(self.homeAssistantSensorUrl + "/ledsecondaryrgbstate", dumps(state))
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
        settings =  self.getsettings()
        headers = okayHeader
        data = b"{ \"enable\": \"%s\", \"server\": \"%s\", \"subscribe\": \"%s\", \"publish\": \"%s\", \"username\": \"%s\", \"password\":\"%s\" }" % (settings[0], settings[1], settings[2], settings[3], settings[4], settings[5])
        return data, headers

    
    def savehasettings(self, params):
        # Read form params
        enable = unquote(params.get(b"enable", None))
        server = unquote(params.get(b"server", None))
        subscribe = unquote(params.get(b"subscribe", None))
        publish = unquote(params.get(b"publish", None))
        username = unquote(params.get(b"username", None))
        password = unquote(params.get(b"password", None))
        settings = (enable, server, subscribe, publish, username, password)
        self.settings(settings)
        headers = b"HTTP/1.1 307 Temporary Redirect\r\nLocation: /\r\n"
        return b"", headers

    
    def sub_cb(self, topic, msg):
        SerialLog.log("HA MQTT Command Received: ", topic, msg)
        self.commands.append(b"%s/%s" % (topic, msg))

    
    def connect_and_subscribe(self):
        if (self.last_connect + 30000 < ticks_ms()):
            SerialLog.log('Connecting to %s HA MQTT broker...' % (self.mqtt_server))
            self.last_connect = ticks_ms()

            self.client = MQTTClient(b"ha-%s" % (self.client_id), self.mqtt_server, int(self.mqtt_port), self.mqtt_user, self.mqtt_password)
            self.client.set_callback(self.sub_cb)
            self.client.connect()
            self.client.subscribe(self.topic_sub)
            # Wipe all existing telemetry so we send a full update on connect
            self.telemetry = {} 
            self.configuredKeys = []
            SerialLog.log('Connected to %s HA MQTT broker, subscribed to %s topic' % (self.mqtt_server, self.topic_sub))
            self.connected = True
    
    def get_basic_payload(self, name, uniqueid, attr, value):

        wlan_mac = self.sta_if.config('mac')
        my_mac_addr = hexlify(wlan_mac, ':').decode().upper()

        basicPayload = { 
            "~": self.homeAssistantSensorUrl,
            "name": "%s %s" % (self.getPref("web", "name", self.basicSettings["name"]), name),
            "unique_id": uniqueid,
            "device": {
                "connections": [["mac", my_mac_addr]],
                "manufacturer": "Wolfen",
                "name": "%s - %s" % (self.getPref("web", "name", self.basicSettings["name"]), self.client_id.decode('ascii')),
                "sw_version": self.version,
                "model": self.basicSettings["shortName"],
                "configuration_url": "http://%s" % (self.ip)
            },
            "stat_t": "~/state",
            "unit_of_meas": '%',
            "val_tpl": "{{ value_json.%s }}" % (attr)
        }
        # if the value is a number then update the payload
        if (isinstance(value, int) or isinstance(value, float)):
            basicPayload.update({ "unit_of_measurement": "unit" })
        return basicPayload

    
    def home_assistant_configure(self, key, value):
        
        if key not in self.configuredKeys:
            self.configuredKeys.append(key)
            attr = key.replace("/","_")
            safeid = "%s_%s" % (self.client_id.decode('ascii'), key.replace("/","_")) #43jh34hg4_temp_jhgfddfdsfd
            if (key.startswith(b'temperature/')):
                payload = self.get_basic_payload("Temperature", safeid, attr, value) 
                payload.update({ "dev_cla": "temperature", "unit_of_meas": "\u00b0C"})
                self.safePublish("%s/temp%s/config" % (self.homeAssistantSensorUrl, safeid), dumps(payload))
            elif (key.startswith(b'humidity/')):
                payload = self.get_basic_payload("Humidity", safeid, attr, value) 
                payload.update({ "dev_cla": "humidity", "unit_of_meas": "%"})
                self.safePublish("%s/humidity%s/config" % (self.homeAssistantSensorUrl, safeid), dumps(payload))
            elif (key.startswith(b'rssi')):
                payload = self.get_basic_payload("RSSI", safeid, attr, value) 
                payload.update({ "dev_cla": "signal_strength", "unit_of_meas": "dBm"})
                self.safePublish("%s/rssi%s/config" % (self.homeAssistantSensorUrl, safeid), dumps(payload))
            elif (key.startswith(b'ip')):
                payload = self.get_basic_payload("IP", safeid, attr, value) 
                self.safePublish("%s/ip%s/config" % (self.homeAssistantSensorUrl, safeid), dumps(payload))
            elif (key.startswith(b'ssid')):
                payload = self.get_basic_payload("SSID", safeid, attr, value) 
                self.safePublish("%s/ssid%s/config" % (self.homeAssistantSensorUrl, safeid), dumps(payload))
            elif (key.startswith(b'ac_mode')):
                payload = self.get_basic_payload("ac_mode", safeid, attr, value) 
                self.safePublish("%s/ac_mode%s/config" % (self.homeAssistantSensorUrl, safeid), dumps(payload))
            elif (key.startswith(b'ac_setpoint')):
                payload = self.get_basic_payload("ac_setpoint", safeid, attr, value) 
                payload.update({ "dev_cla": "temperature", "unit_of_meas": "\u00b0C"})
                self.safePublish("%s/ac_setpoint%s/config" % (self.homeAssistantSensorUrl, safeid), dumps(payload))
            elif (key.startswith(b'button')):
                payload = self.get_basic_payload("Onboard Button", safeid, attr, value) 
                self.safePublish("%s/onboard_button%s/config" % (self.homeAssistantSensorUrl, safeid), dumps(payload))
            elif (key.startswith(b'ledprimaryb')):
                payload = self.get_basic_payload("Primary Colour", safeid, attr, value) 
                payload.pop("val_tpl")
                payload.update({ 
	                    "brightness": True,
	                    "brightness_scale": 255,
	                    "color_mode": True,
	                    "command_topic": "~/command/ledprimary",
	                    "effect": True,
	                    "effect_list": ["none", "switch", "fade", "cycle", "bounce", "rainbow"],
	                    "json_attributes_topic": "~/ledprimaryrgbstate",
	                    "schema": "json",
	                    "supported_color_modes": ["rgb"],
	                    "unique_id": safeid,
                        "stat_t": "~/ledprimaryrgbstate",
                })
                self.safePublish("%s/ledprimaryrgb%s/config" % (self.homeAssistantLightUrl, safeid), dumps(payload))
            elif (key.startswith(b'ledsecondaryb')):
                payload = self.get_basic_payload("Secondary Colour", safeid, attr, value) 
                payload.pop("val_tpl")
                payload.update({ 
	                    "brightness": True,
	                    "brightness_scale": 255,
	                    "color_mode": True,
	                    "command_topic": "~/command/ledsecondary",
	                    "effect": True,
	                    "effect_list": ["none", "switch", "fade", "cycle", "bounce", "rainbow"],
	                    "json_attributes_topic": "~/ledprimaryrgbstate",
	                    "schema": "json",
	                    "supported_color_modes": ["rgb"],
	                    "unique_id": safeid,
                        "stat_t": "~/ledsecondaryrgbstate",
                })
                self.safePublish("%s/ledsecondaryrgb%s/config" % (self.homeAssistantLightUrl, safeid), dumps(payload))
            else:
                payload = self.get_basic_payload(attr, safeid, attr, value) 
                self.safePublish("%s/ssid%s/config" % (self.homeAssistantSensorUrl, safeid), dumps(payload))                
    
    def settings(self, settingsVals):
        # Apply the new settings
        self.enabled = settingsVals[0]
        self.mqtt_server = settingsVals[1]

        if (settingsVals[2] != b""):
            self.topic_sub = settingsVals[2]
        else:
            self.topic_sub = b'homeassistant/sensor/%s/command/#' % (self.client_id)

        if (settingsVals[3] != b""):
            self.topic_pub = settingsVals[3]
        else: 
            self.topic_pub = b'homeassistant/sensor/%s/state' % (self.client_id)

        # Save the settings to disk
        settings = HomeAssistantSettings()
        settings.Enable = self.enabled
        settings.Server = self.mqtt_server
        settings.Subscribe = self.topic_sub
        settings.Publish = self.topic_pub
        settings.Username = self.mqtt_user
        settings.Password = self.mqtt_password
        settings.write()
    
     
    def getsettings(self):
        s = (self.enabled, self.mqtt_server, self.topic_sub, self.topic_pub, self.mqtt_user, self.mqtt_password)
        return s

    def safePublish(self, topic, message):
        try:
            self.client.publish(topic, message)
        except OSError as e:
            SerialLog.log("Error publishing MQTT message: %s" % (e))
            self.connected = False
            


    
