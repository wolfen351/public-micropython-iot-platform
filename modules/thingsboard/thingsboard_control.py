from modules.basic.basic_module import BasicModule
from modules.mqtt.mqtt import MQTTClient
from serial_log import SerialLog
from modules.thingsboard.thingsboard_settings import ThingsboardSettings
import ubinascii
import machine
import network
from modules.web.web_processor import okayHeader, unquote
import json

class ThingsboardControl(BasicModule):

    def __init__(self):
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
        if (settings.Publish != b""):
            self.topic_pub = settings.Publish
        else:
            self.topic_pub = b"v1/devices/me/telemetry"
        self.mqtt_port = settings.Port
        self.access_token = settings.AccessToken
        
    def tick(self):
        if (self.enabled == b"Y"):
            if (self.sta_if.isconnected()):
                try:
                    if (not self.init):
                        self.init = True
                        self.connect()
                    self.client.check_msg()
                except Exception as e:
                    self.connect()
                    raise

    def getTelemetry(self):
        return {}

    def processTelemetry(self, telemetry):

        if (self.enabled != b"Y"):
            return

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
            b"/tb": b"/modules/thingsboard/web_tb.html", 
            b"/tbloadsettings": self.loadtbsettings,
            b"/tbsavesettings": self.savetbsettings,
        }

    # Internal Code 

    def connect(self):
        self.client = MQTTClient(b"tb-" + self.client_id, self.mqtt_server, port=int(self.mqtt_port), user=self.access_token, password=self.access_token)
        self.client.connect()
        SerialLog.log('Connected to %s:%s TB MQTT broker' % (self.mqtt_server, str(self.mqtt_port)))


    def settings(self, settingsVals):
        # Apply the new settings
        self.enabled = settingsVals[0]
        self.mqtt_server = settingsVals[1]

        if (settingsVals[2] != b""):
            self.topic_pub = settingsVals[2]
        else: 
            self.topic_pub = b"v1/devices/me/telemetry"

        self.mqtt_port = settingsVals[3]
        self.access_token = settingsVals[4]

        # Save the settings to disk
        settings = ThingsboardSettings()
        settings.Enable = self.enabled
        settings.Server = self.mqtt_server
        settings.Publish = self.topic_pub
        settings.Port = self.mqtt_port
        settings.AccessToken = self.access_token
        settings.write()
    
    def getsettings(self):
        s = (self.enabled, self.mqtt_server, self.topic_pub, self.mqtt_port, self.access_token)
        return s

    def loadtbsettings(self, params):
        settings =  self.getsettings()
        headers = okayHeader
        data = b"{ \"enable\": \"%s\", \"server\": \"%s\", \"publish\": \"%s\", \"port\": %s, \"accesstoken\": \"%s\" }" % (settings[0], settings[1], settings[2], str(settings[3]), settings[4])
        return data, headers

    def savetbsettings(self, params):
        # Read form params
        enable = unquote(params.get(b"enable", None))
        server = unquote(params.get(b"server", None))
        publish = unquote(params.get(b"publish", None))
        port = int(unquote(params.get(b"port", None)))
        accessToken = unquote(params.get(b"accesstoken", None))
        settings = (enable, server, publish, port, accessToken)
        self.settings(settings)
        headers = b"HTTP/1.1 307 Temporary Redirect\r\nLocation: /\r\n"
        return b"", headers


    
