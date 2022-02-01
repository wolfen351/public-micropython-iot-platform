from basic_module import BasicModule
from mqtt import MQTTClient
from serial_log import SerialLog
from thingsboard_settings import ThingsboardSettings
import ubinascii
import machine
import network
from web_processor import okayHeader, unquote
import json

class ThingsboardControl(BasicModule):

    def __init__(self, basicSettings):
        self.client_id = ubinascii.hexlify(machine.unique_id())
        self.init = False
        self.status = None
        self.sta_if = network.WLAN(network.STA_IF)
        self.thingsBoardTelemetryUrl = b"v1/devices/me/telemetry"
        self.mqtt_port = 1883
        self.access_token = None
        self.basicSettings = basicSettings
        self.telemetry = {}
        self.enabled = b"N"
        self.client = None

    def start(self):
        settings = ThingsboardSettings()
        settings.load()
        self.enabled = settings.Enable
        self.mqtt_server = settings.Server
        if (settings.Subscribe != b""):
            self.topic_sub = settings.Subscribe
        else:
            self.topic_sub = b'thingsboard/sensor/%s/command/#' % (self.client_id)

        if (settings.Publish != b""):
            self.topic_pub = settings.Publish
        else:
            self.topic_pub = b"v1/devices/me/telemetry"
        
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

        if (self.client != None):
            stuffToPost = {}
            
            for attr, value in self.telemetry.items():
                if (value != telemetry[attr]):
                    stuffToPost.update({attr : telemetry[attr]})

            if (len(stuffToPost) > 0):
                messageStr = json.dumps(stuffToPost)
                SerialLog.log("Sending TB MQTT: ", messageStr)
                self.client.publish(self.thingsBoardTelemetryUrl, messageStr)

            self.telemetry = telemetry.copy()

    def getCommands(self):
        return []

    def processCommands(self, commands):
        pass

    def getRoutes(self):
        return {
            b"/tb": b"./web_tb.html", 
            b"/tbloadsettings": self.loadtbsettings,
            b"/tbsavesettings": self.savetbsettings,
        }

    # Internal Code 

    def sub_cb(self, topic, msg):
        SerialLog.log("TB MQTT Command Received: ", topic, msg)

    def connect_and_subscribe(self):
        self.client = MQTTClient(b"tb-" + self.client_id, self.mqtt_server, port=int(self.mqtt_port), user=self.access_token)
        self.client.set_callback(self.sub_cb)
        self.client.connect()
        self.client.subscribe(self.topic_sub)
        SerialLog.log('Connected to %s TB MQTT broker, subscribed to %s topic' % (self.mqtt_server, self.topic_sub))


    def settings(self, settingsVals):
        # Apply the new settings
        self.enabled = settingsVals[0]
        self.mqtt_server = settingsVals[1]

        if (settingsVals[2] != b""):
            self.topic_sub = settingsVals[2]
        else:
            self.topic_sub = b'thingsboard/sensor/%s/command/#' % (self.client_id)

        if (settingsVals[3] != b""):
            self.topic_pub = settingsVals[3]
        else: 
            self.topic_pub = b"v1/devices/me/telemetry"

        self.mqtt_port = settingsVals[4]
        self.access_token = settingsVals[5]

        # Save the settings to disk
        settings = ThingsboardSettings()
        settings.Enable = self.enabled
        settings.Server = self.mqtt_server
        settings.Subscribe = self.topic_sub
        settings.Publish = self.topic_pub
        settings.Port = self.mqtt_port
        settings.AccessToken = self.access_token
        settings.write()
    
    def getsettings(self):
        s = (self.enabled, self.mqtt_server, self.topic_sub, self.topic_pub, self.mqtt_port, self.access_token)
        return s

    def loadtbsettings(self, params):
        settings =  self.getsettings()
        headers = okayHeader
        data = b"{ \"enable\": \"%s\", \"server\": \"%s\", \"subscribe\": \"%s\", \"publish\": \"%s\", \"port\": %s, \"accesstoken\": \"%s\" }" % (settings[0], settings[1], settings[2], settings[3], str(settings[4]), settings[5])
        return data, headers

    def savetbsettings(self, params):
        # Read form params
        enable = unquote(params.get(b"enable", None))
        server = unquote(params.get(b"server", None))
        subscribe = unquote(params.get(b"subscribe", None))
        publish = unquote(params.get(b"publish", None))
        port = int(unquote(params.get(b"port", None)))
        accessToken = unquote(params.get(b"accesstoken", None))
        settings = (enable, server, subscribe, publish, port, accessToken)
        self.settings(settings)
        headers = b"HTTP/1.1 307 Temporary Redirect\r\nLocation: /\r\n"
        return b"", headers


    
