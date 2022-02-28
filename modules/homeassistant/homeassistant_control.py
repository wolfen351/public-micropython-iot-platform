from modules.basic.basic_module import BasicModule
from modules.homeassistant.homeassistant_settings import HomeAssistantSettings
from modules.mqtt.mqtt import MQTTClient
from serial_log import SerialLog
import ubinascii
import machine
import network
from modules.web.web_processor import okayHeader, unquote
import ujson

class HomeAssistantControl(BasicModule):

    def __init__(self, basicSettings):
        self.client_id = ubinascii.hexlify(machine.unique_id())
        self.init = False
        self.status = None
        self.sta_if = network.WLAN(network.STA_IF)
        self.homeAssistantUrl = "homeassistant"
        self.homeAssistantSensorUrl = "%s/sensor/%s" % (self.homeAssistantUrl, self.client_id.decode('ascii'))
        self.homeAssistantLightUrl = "%s/light/%s" % (self.homeAssistantUrl, self.client_id.decode('ascii'))
        self.mqtt_port = 1883
        self.mqtt_user = None
        self.mqtt_password = None
        self.basicSettings = basicSettings
        self.telemetry = {}
        self.client = None
        self.configuredKeys = []
        self.version = b"1.0.0"
        self.ip = b"0.0.0.0"
        self.messageStr = b""
        self.commands = []

    #@micropython.native
    def start(self):
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

    #@micropython.native     
    def tick(self):
        if (self.enabled == b"Y"):
            if (self.sta_if.isconnected()):
                try:
                    if (not self.init):
                        self.init = True
                        self.connect_and_subscribe()
                    self.client.check_msg()
                except Exception as e:
                    self.connect_and_subscribe()
                    raise

    #@micropython.native
    def getTelemetry(self):
        return {}

    #@micropython.native
    def processTelemetry(self, telemetry):

        if (self.enabled != b"Y"):
            return

        if (self.client != None):
            
            for attr, value in self.telemetry.items():
                if (attr == "ip"):
                    self.ip = value
                if (attr == "version"):
                    self.version = value
                if (attr not in self.configuredKeys):
                    self.home_assistant_configure(attr)

            messageStr = ujson.dumps(telemetry)
            messageStr = messageStr.replace("/","_")
            # dont send duplicate messages
            if (self.messageStr != messageStr):
                SerialLog.log("Sending HA MQTT: ", messageStr)
                self.client.publish("%s/state" % self.homeAssistantSensorUrl, messageStr)
                self.messageStr = messageStr

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
                    self.client.publish(self.homeAssistantSensorUrl + "/ledprimaryrgbstate", ujson.dumps(state))

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
                    self.client.publish(self.homeAssistantSensorUrl + "/ledsecondaryrgbstate", ujson.dumps(state))
            self.telemetry = telemetry.copy()

    #@micropython.native
    def getCommands(self):
        c = self.commands
        self.commands = []
        return c

    #@micropython.native
    def processCommands(self, commands):
        pass

    #@micropython.native
    def getRoutes(self):
        return {
            b"/ha": b"/modules/homeassistant/web_ha.html", 
            b"/haloadsettings": self.loadhasettings,
            b"/hasavesettings": self.savehasettings,
        }

    # Internal Code 
    #@micropython.native
    def loadhasettings(self, params):
        settings =  self.getsettings()
        headers = okayHeader
        data = b"{ \"enable\": \"%s\", \"server\": \"%s\", \"subscribe\": \"%s\", \"publish\": \"%s\" }" % (settings[0], settings[1], settings[2], settings[3])
        return data, headers

    #@micropython.native
    def savehasettings(self, params):
        # Read form params
        enable = unquote(params.get(b"enable", None))
        server = unquote(params.get(b"server", None))
        subscribe = unquote(params.get(b"subscribe", None))
        publish = unquote(params.get(b"publish", None))
        settings = (enable, server, subscribe, publish)
        self.settings(settings)
        headers = b"HTTP/1.1 307 Temporary Redirect\r\nLocation: /\r\n"
        return b"", headers

    #@micropython.native
    def sub_cb(self, topic, msg):
        SerialLog.log("HA MQTT Command Received: ", topic, msg)
        self.commands.append(topic + b"/" + msg)

    #@micropython.native
    def connect_and_subscribe(self):
        self.client = MQTTClient(b"ha-"+self.client_id, self.mqtt_server, int(self.mqtt_port), self.mqtt_user, self.mqtt_port)
        self.client.set_callback(self.sub_cb)
        self.client.connect()
        self.client.subscribe(self.topic_sub)
        # Wipe all existing telemetry so we send a full update on connect
        self.telemetry = {} 
        self.configuredKeys = []
        SerialLog.log('Connected to %s HA MQTT broker, subscribed to %s topic' % (self.mqtt_server, self.topic_sub))

    #@micropython.native
    def get_basic_payload(self, name, uniqueid, attr):
        basicPayload = { 
            "~": self.homeAssistantSensorUrl,
            "name": "%s %s %s" % (self.basicSettings['ShortName'], self.client_id.decode('ascii'), name),
            "unique_id": uniqueid,
            "device": {
                "manufacturer": "Wolfen",
                "name": self.basicSettings["Name"],
                "sw_version": self.version,
                "identifiers": [ self.client_id.decode('ascii'), self.basicSettings["ShortName"], self.basicSettings["Name"] ],
                #"configuration_url": "http://" + self.ip,
            },
            "stat_t": "~/state",
            "val_tpl": "{{ value_json.%s }}" % (attr)
        }
        return basicPayload

    #@micropython.native
    def home_assistant_configure(self, key):
        
        if key not in self.configuredKeys:

            SerialLog.log("Configuring home assistant for:", key)

            self.configuredKeys.append(key)


            attr = key.replace("/","_")
            safeid = "%s_%s" % (self.client_id.decode('ascii'), key.replace("/","_")) #43jh34hg4_temp_jhgfddfdsfd
            if (key.startswith(b'temperature/')):
                payload = self.get_basic_payload("Temperature", safeid, attr) 
                payload.update({ "dev_cla": "temperature", "unit_of_meas": "C"})
                SerialLog.log("HA MQTT Sending: ", ujson.dumps(payload))
                self.client.publish("%s/temp%s/config" % (self.homeAssistantSensorUrl, safeid), ujson.dumps(payload))

            if (key.startswith(b'humidity/')):
                payload = self.get_basic_payload("Humidity", safeid, attr) 
                payload.update({ "dev_cla": "humidity", "unit_of_meas": "%RH"})
                SerialLog.log("HA MQTT Sending: ", ujson.dumps(payload))
                self.client.publish("%s/humidity%s/config" % (self.homeAssistantSensorUrl, safeid), ujson.dumps(payload))

            if (key.startswith(b'rssi')):
                payload = self.get_basic_payload("RSSI", safeid, attr) 
                payload.update({ "dev_cla": "signal_strength", "unit_of_meas": "dBm"})
                SerialLog.log("HA MQTT Sending: ", ujson.dumps(payload))
                self.client.publish("%s/rssi%s/config" % (self.homeAssistantSensorUrl, safeid), ujson.dumps(payload))
                
            if (key.startswith(b'ip')):
                payload = self.get_basic_payload("IP", safeid, attr) 
                SerialLog.log("HA MQTT Sending: ", ujson.dumps(payload))
                self.client.publish("%s/ip%s/config" % (self.homeAssistantSensorUrl, safeid), ujson.dumps(payload))

            if (key.startswith(b'ssid')):
                payload = self.get_basic_payload("SSID", safeid, attr) 
                SerialLog.log("HA MQTT Sending: ", ujson.dumps(payload))
                self.client.publish("%s/ssid%s/config" % (self.homeAssistantSensorUrl, safeid), ujson.dumps(payload))

            if (key.startswith(b'button')):
                payload = self.get_basic_payload("Onboard Button", safeid, attr) 
                SerialLog.log("HA MQTT Sending: ", ujson.dumps(payload))
                self.client.publish("%s/onboard_button%s/config" % (self.homeAssistantSensorUrl, safeid), ujson.dumps(payload))

            if (key.startswith(b'ledprimaryb')):
                payload = self.get_basic_payload("Primary Colour", safeid, attr) 
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
                SerialLog.log("HA MQTT Sending: ", ujson.dumps(payload))
                self.client.publish("%s/ledprimaryrgb%s/config" % (self.homeAssistantLightUrl, safeid), ujson.dumps(payload))
            if (key.startswith(b'ledsecondaryb')):
                payload = self.get_basic_payload("Secondary Colour", safeid, attr) 
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
                SerialLog.log("HA MQTT Sending: ", ujson.dumps(payload))
                self.client.publish("%s/ledsecondaryrgb%s/config" % (self.homeAssistantLightUrl, safeid), ujson.dumps(payload))



            # if (key.startswith(b'ledsecondary')):
            #     payload = self.get_basic_payload("Primary Colour", safeid, attr) 
            #     SerialLog.log("HA MQTT Sending: ", ujson.dumps(payload))
            #     self.client.publish("%s/ledsecondary%s/config" % (self.homeAssistantLightUrl, safeid), ujson.dumps(payload))

    #@micropython.native
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
        settings.write()
    
    #@micropython.native 
    def getsettings(self):
        s = (self.enabled, self.mqtt_server, self.topic_sub, self.topic_pub)
        return s


    
