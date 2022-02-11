from modules.basic.basic_module import BasicModule
from modules.homeassistant.homeassistant_settings import HomeAssistantSettings
from modules.mqtt.mqtt import MQTTClient
from serial_log import SerialLog
import ubinascii
import machine
import network
import time
from modules.web.web_processor import okayHeader, unquote

class HomeAssistantControl(BasicModule):

    def __init__(self, basicSettings):
        self.client_id = ubinascii.hexlify(machine.unique_id())
        self.init = False
        self.status = None
        self.sta_if = network.WLAN(network.STA_IF)
        self.homeAssistantUrl = "homeassistant"
        self.homeAssistantSensorUrl = "%s/sensor/%s" % (self.homeAssistantUrl, self.client_id.decode('ascii'))
        self.homeAssistantButtonUrl = "%s/button/%s" % (self.homeAssistantUrl, self.client_id.decode('ascii'))
        self.mqtt_port = 1883
        self.mqtt_user = None
        self.mqtt_password = None
        self.basicSettings = basicSettings
        self.telemetry = {}
        self.client = None
        self.configuredKeys = []

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

    def getTelemetry(self):
        return {}

    def processTelemetry(self, telemetry):

        if (self.enabled != b"Y"):
            return

        if (self.client != None):
            stuffToPost = []
            
            for attr, value in self.telemetry.items():
                if (value != telemetry[attr]):
                    stuffToPost.append([attr, telemetry[attr]])

            if (len(stuffToPost) > 0):
                messageStr = "{ "
                for bit in stuffToPost:
                    self.home_assistant_configure(bit[0])

                    j = bit[0].replace("/","_")
                    messageStr += '"' + j + '": '
                    if (isinstance(bit[1],int) or isinstance(bit[1],float)):
                        messageStr += str(bit[1]) +', '
                    else:
                        messageStr += '"' + bit[1] + '", '
                messageStr = messageStr[0: -2] + "}" # remove final comma and add }

                SerialLog.log("Sending HA MQTT: ", messageStr)
                self.client.publish("%s/state" % self.homeAssistantSensorUrl, messageStr)

            self.telemetry = telemetry.copy()

    def getCommands(self):
        return []

    def processCommands(self, commands):
        pass

    def getRoutes(self):
        return {
            b"/ha": b"/modules/homeassistant/web_ha.html", 
            b"/haloadsettings": self.loadhasettings,
            b"/hasavesettings": self.savehasettings,
        }

    # Internal Code 

    def loadhasettings(self, params):
        settings =  self.getsettings()
        headers = okayHeader
        data = b"{ \"enable\": \"%s\", \"server\": \"%s\", \"subscribe\": \"%s\", \"publish\": \"%s\" }" % (settings[0], settings[1], settings[2], settings[3])
        return data, headers

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

    def sub_cb(self, topic, msg):
        SerialLog.log("HA MQTT Command Received: ", topic, msg)

    def connect_and_subscribe(self):
        self.client = MQTTClient(b"ha-"+self.client_id, self.mqtt_server, int(self.mqtt_port), self.mqtt_user, self.mqtt_port)
        self.client.set_callback(self.sub_cb)
        self.client.connect()
        self.client.subscribe(self.topic_sub)
        SerialLog.log('Connected to %s HA MQTT broker, subscribed to %s topic' % (self.mqtt_server, self.topic_sub))

    def home_assistant_configure(self, key):
        
        if key not in self.configuredKeys:
            self.configuredKeys.append(key)
            if (key.startswith(b'temperature/')):
                id = key.replace("temperature/","")
                j = key.replace("/","_")
                self.client.publish("%s/temp%s/config" % (self.homeAssistantSensorUrl, id), '{"name":"%s %s %s", "dev_cla":"temperature","stat_t":"%s/state","unit_of_meas":"°C","val_tpl":"{%% if value_json.%s %%} {{value_json.%s}} {%% else %%} {{ state.state }} {%% endif %%}"}' % (self.basicSettings['ShortName'], self.client_id.decode('ascii'), id, self.homeAssistantSensorUrl, j, j) )

            if (key.startswith(b'humidity/')):
                id = key.replace("humidity/","")
                j = key.replace("/","_")
                self.client.publish("%s/humidity%s/config" % (self.homeAssistantSensorUrl, id), '{"name":"%s %s %s", "dev_cla":"humidity","stat_t":"%s/state","unit_of_meas":"%%RH","val_tpl":"{%% if value_json.%s %%} {{value_json.%s}} {%% else %%} {{ state.state }} {%% endif %%}"}' % (self.basicSettings['ShortName'], self.client_id.decode('ascii'), id, self.homeAssistantSensorUrl, j, j) )

            if (key.startswith(b'rssi')):
                self.client.publish("%s/rssi/config" % self.homeAssistantSensorUrl, '{"name":"%s %s Wifi", "dev_cla":"signal_strength","stat_t":"%s/state","unit_of_meas":"dBm","val_tpl":"{%% if value_json.rssi %%} {{value_json.rssi}} {%% else %%} {{ state.state }} {%% endif %%}"}' % (self.basicSettings['ShortName'], self.client_id.decode('ascii'), self.homeAssistantSensorUrl) )

            if (key.startswith(b'ip')):
                self.client.publish("%s/ip/config" % self.homeAssistantSensorUrl, '{"name":"%s %s IP", "dev_cla":"None","stat_t":"%s/state","val_tpl":"{%% if value_json.ip %%} {{value_json.ip}} {%% else %%} {{ state.state }} {%% endif %%}"}' % (self.basicSettings['ShortName'], self.client_id.decode('ascii'), self.homeAssistantSensorUrl) )

            if (key.startswith(b'ssid')):
                self.client.publish("%s/ssid/config" % self.homeAssistantSensorUrl, '{"name":"%s %s SSID", "dev_cla":"None","stat_t":"%s/state","val_tpl":"{%% if value_json.ssid %%} {{value_json.sdis}} {%% else %%} {{ state.state }} {%% endif %%}"}' % (self.basicSettings['ShortName'], self.client_id.decode('ascii'), self.homeAssistantSensorUrl) )

            if (key.startswith(b'button')):
                self.client.publish("%s/onboard_button/config" % self.homeAssistantButtonUrl, '{"name":"%s %s Onboard Button", "dev_cla":"None","stat_t":"%s/state","val_tpl":"{%% if value_json.onboard_button %%} {{value_json.onboard_button}} {%% else %%} {{ state.state }} {%% endif %%}"}' % (self.basicSettings['ShortName'], self.client_id.decode('ascii'), self.homeAssistantButtonUrl) )

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
    
    def getsettings(self):
        s = (self.enabled, self.mqtt_server, self.topic_sub, self.topic_pub)
        return s


    
