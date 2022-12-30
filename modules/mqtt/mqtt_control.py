from modules.basic.basic_module import BasicModule
from modules.mqtt.mqtt import MQTTClient
from modules.mqtt.mqtt_settings import MqttSettings
from serial_log import SerialLog
import ubinascii
import machine
import network
from modules.web.web_processor import okayHeader, unquote

class MqttControl(BasicModule):

    def __init__(self):
        self.client_id = ubinascii.hexlify(machine.unique_id())
        self.init = False
        self.status = None
        self.sta_if = network.WLAN(network.STA_IF)
        self.mqtt_port = 1883
        self.mqtt_user = None
        self.mqtt_password = None
        self.telemetry = {}
        self.client = None
        self.commands = []

    def start(self):
        BasicModule.start(self)
        settings = MqttSettings()
        settings.load()
        self.enabled = settings.Enable
        self.mqtt_server = settings.Server
        if (settings.Subscribe != b""):
            self.topic_sub = settings.Subscribe
        else:
            self.topic_sub = b'%s/%s/command/#' % (self.basicSettings['shortName'], self.client_id)

        if (settings.Publish != b""):
            self.topic_pub = settings.Publish
        else:
            self.topic_pub = b'%s/%s/status' % (self.basicSettings['shortName'], self.client_id)

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
            
            for attr, value in telemetry.items():
                if (value != self.telemetry.get(attr)):
                    stuffToPost.append([attr, telemetry[attr]])

            if (len(stuffToPost) > 0):
                for bit in stuffToPost:
                    self.client.publish(self.topic_pub + b"/%s" % (bit[0]), str(bit[1]), True)

            self.telemetry = telemetry.copy()


    def getCommands(self):
        c = self.commands
        self.commands = []
        return c

    def processCommands(self, commands):
        pass

    def getRoutes(self):
        return {
            b"/mqtt": b"/modules/mqtt/web_mqtt.html", 
            b"/mqttloadsettings": self.loadmqttsettings,
            b"/mqttsavesettings": self.savemqttsettings,
        }

    # Internal Code 

    def loadmqttsettings(self, params):
        settings =  self.getsettings()
        headers = okayHeader
        data = b"{ \"enable\": \"%s\", \"server\": \"%s\", \"subscribe\": \"%s\", \"publish\": \"%s\" }" % (settings[0], settings[1], settings[2], settings[3])
        return data, headers

    def savemqttsettings(self, params):
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
        SerialLog.log("MQTT Command Received: ", topic, msg)
        self.commands.append(topic + b"/" + msg)

    def connect_and_subscribe(self):
        self.client = MQTTClient(b"mqtt-" + self.client_id, self.mqtt_server, int(self.mqtt_port), self.mqtt_user, self.mqtt_password)
        self.client.set_callback(self.sub_cb)
        self.client.connect()
        self.client.subscribe(self.topic_sub)
        SerialLog.log('Connected to %s MQTT broker, subscribed to %s topic' % (self.mqtt_server, self.topic_sub))        
        # resend all telemetry on connect
        self.telemetry = {}

    def settings(self, settingsVals):
        # Apply the new settings
        self.enabled = settingsVals[0]
        self.mqtt_server = settingsVals[1]

        if (settingsVals[2] != b""):
            self.topic_sub = settingsVals[2]
        else:
            self.topic_sub = b'%s/%s/command/#' % (self.basicSettings['shortName'], self.client_id)

        if (settingsVals[3] != b""):
            self.topic_pub = settingsVals[3]
        else: 
            self.topic_pub = b'%s/%s/status' % (self.basicSettings['shortName'], self.client_id)

        # Save the settings to disk
        settings = MqttSettings()
        settings.Enable = self.enabled
        settings.Server = self.mqtt_server
        settings.Subscribe = self.topic_sub
        settings.Publish = self.topic_pub
        settings.write()
    
    def getsettings(self):
        s = (self.enabled, self.mqtt_server, self.topic_sub, self.topic_pub)
        return s

