from modules.basic.basic_module import BasicModule
from modules.mqtt.mqtt import MQTTClient
from modules.mqtt.mqtt_settings import MqttSettings
from serial_log import SerialLog
from ubinascii import hexlify
from machine import unique_id, reset
import network
from modules.web.web_processor import okayHeader, unquote
from time import sleep, ticks_ms
from modules.ota.ota import local_version

class MqttControl(BasicModule):

    def __init__(self):
        self.client_id = hexlify(unique_id())
        self.init = False
        self.status = None
        self.sta_if = network.WLAN(network.STA_IF)
        self.mqtt_port = 1883
        self.mqtt_user = None
        self.mqtt_password = None
        self.telemetry = {}
        self.client = None
        self.commands = []
        self.lastConnectAttempt = 0

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
        if (self.enabled != b"Y"):
            return

        if (not self.sta_if.isconnected()):
            return
        
        if (not self.init and self.lastConnectAttempt + 120000 > ticks_ms()):
            return
        
        if (not self.init):
            self.init = True
            self.lastConnectAttempt = ticks_ms()
            self.connect_and_subscribe()

        try:
            self.client.check_msg()
        except Exception as e:
            self.init = False
            raise

    def getTelemetry(self):
        return {}

    def processTelemetry(self, telemetry):
        if (self.enabled != b"Y"):
            return

        if (not self.sta_if.isconnected()):
            return

        if (self.client != None and self.hasTelemetryChanged(telemetry)):
            for attr, value in telemetry.items():
                if (value != self.telemetry.get(attr)):
                    self.client.publish(self.topic_pub + b"/%s" % (attr), str(telemetry[attr]), retain=True)
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
    def hasTelemetryChanged(self, newTelemetry):
            thingsThatChanged = 0
            for attr, value in newTelemetry.items():
                if (value != self.telemetry.get(attr)):
                    if (attr != "time" and attr != "voltage" and attr != "freeram" and attr != "rssi"): # dont post the time, voltage or rssi every second
                        thingsThatChanged += 1
            return thingsThatChanged > 0

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
        # remove the part we subscribe to from the topic
        topic = topic.replace(self.topic_sub.replace(b"/#", b""), b"") 
        self.commands.append(b"%s/%s" % (topic, msg))

        # check for firmware update
        # if topic starts with iot-platform/version and the version is different, restart
        if (topic.startswith(b"iot-platform/version")):
            #convert msg to string
            msgs = msg.decode('ascii')
            if (msgs > local_version()):
                SerialLog.log("Server Firmware is newer than ours, restarting (we are on: ", local_version(), ")")
                # sleep for 5s, then reboot
                sleep(5)
                reset()
            elif (msgs < local_version()):
                SerialLog.log("Server Firmware is older than ours, not restarting (we are on: ", local_version(), ")")
            else:
                SerialLog.log("Firmware version match, no action (we are on: ", local_version(), ")")

    def connect_and_subscribe(self):
        self.client = MQTTClient(b"mqtt-%s" % (self.client_id), self.mqtt_server, int(self.mqtt_port), self.mqtt_user, self.mqtt_password, 300) # 300 second keepalive
        self.client.set_callback(self.sub_cb)
        self.client.connect()
        # Tell the server we are online
        self.client.publish(self.topic_pub + "/online", "1", True)
        # Tell the server if we lose connection
        self.client.lw_topic = self.topic_pub + "/online"
        self.client.lw_msg = "0"
        self.client.lw_retain = True
        # subscribe to the version topic for updates
        self.client.subscribe("iot-platform/version")
        # subscribe to the command topic
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

