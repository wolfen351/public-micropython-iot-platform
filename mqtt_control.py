from mqtt import MQTTClient
from mqtt_settings import MqttSettings
import ubinascii
import machine
import network
import time

class MQTTControl():
    def __init__(self):
        self.client_id = ubinascii.hexlify(machine.unique_id())
        self.init = False

    def sub_cb(self, topic, msg):
        if topic.decode('ASCII').endswith(b'/on'):
            self.lights.command(1, msg)
        if topic.decode('ASCII').endswith(b'/off'):
            self.lights.command(0, msg)
        if topic.decode('ASCII').endswith(b'/auto'):
            self.lights.command(2, msg)

    def connect_and_subscribe(self):
        self.client = MQTTClient(self.client_id, self.mqtt_server)
        self.client.set_callback(self.sub_cb)
        self.client.connect()
        self.client.subscribe(self.topic_sub)
        print('Connected to %s MQTT broker, subscribed to %s topic' % (self.mqtt_server, self.topic_sub))

    def command(self, params):
        # Read form params
        on = 1
        off = 1
        auto = 1

        if (on != b""):
            self.lights.command(1, on)

        if (off != b""):
            self.lights.command(0, off)

        if (auto != b""):
            self.lights.command(2, auto)

    def post_status(self):

        if (self.status[0] != "true"):
            self.client.publish(self.topic_pub + b"/wifi/up", "true")
            self.status[0] = "true"

        if (self.status[1] != self.sta_if.ifconfig()[0]):
            self.client.publish(self.topic_pub + b"/wifi/ip", self.sta_if.ifconfig()[0])
            self.status[1] = self.sta_if.ifconfig()[0]

        if (self.status[2] != self.sta_if.config('essid')):
            self.client.publish(self.topic_pub + b"/wifi/ssid", self.sta_if.config('essid'))
            self.status[2] = self.sta_if.config('essid')

        # Report RSSI every min
        if (self.status[3] < time.time()):
            self.client.publish(self.topic_pub + b"/wifi/rssi", str(self.sta_if.status('rssi')))
            self.status[3] = time.time() + 60

        ms = self.mosfet.status()
        
        if (self.status[4] != ms[0]):
            self.client.publish(self.topic_pub + b"/mosfet/S1", str(ms[0]))
            self.status[4] = ms[0]

        if (self.status[5] != ms[1]):
            self.client.publish(self.topic_pub + b"/mosfet/S2", str(ms[1]))
            self.status[5] = ms[1]

        if (self.status[6] != ms[2]):
            self.client.publish(self.topic_pub + b"/mosfet/S3", str(ms[2]))
            self.status[6] = ms[2]

        if (self.status[7] != ms[3]):
            self.client.publish(self.topic_pub + b"/mosfet/S4", str(ms[3]))
            self.status[7] = ms[3]

        ls = self.lights.status()
        if (self.status[8] != ls[0]):
            self.client.publish(self.topic_pub + b"/light/L1", str(ls[0]))
            self.status[8] = ls[0]

        if (self.status[9] != ls[1]):
            self.client.publish(self.topic_pub + b"/light/L2", str(ls[1]))
            self.status[9] = ls[1]

        if (self.status[10] != ls[2]):
            self.client.publish(self.topic_pub + b"/light/L3", str(ls[2]))
            self.status[10] = ls[2]

        if (self.status[11] != ls[3]):
            self.client.publish(self.topic_pub + b"/light/L4", str(ls[3]))
            self.status[11] = ls[3]


    def start(self, lights, mosfet):
        self.status = [None, None, None, time.time(), None, None, None, None, None, None, None, None]
        self.lights = lights
        self.mosfet = mosfet

        settings = MqttSettings()
        settings.load()
        self.enabled = settings.Enable
        self.mqtt_server = settings.Server
        if (settings.Subscribe != b""):
            self.topic_sub = settings.Subscribe
        else:
            self.topic_sub = b'light4/%s/command/#' % (self.client_id)

        if (settings.Publish != b""):
            self.topic_pub = settings.Publish
        else:
            self.topic_pub = b'light4/%s/status' % (self.client_id)

    def settings(self, settingsVals):
        # Apply the new settings
        self.enabled = settingsVals[0]
        self.mqtt_server = settingsVals[1]

        if (settingsVals[2] != b""):
            self.topic_sub = settingsVals[2]
        else:
            self.topic_sub = b'light4/%s/command/#' % (self.client_id)

        if (settingsVals[3] != b""):
            self.topic_pub = settingsVals[3]
        else: 
            self.topic_pub = b'light4/%s/status' % (self.client_id)

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

    def tick(self):
        if (self.enabled == b"Y"):
            self.sta_if = network.WLAN(network.STA_IF)
            if (self.sta_if.isconnected()):
                try:
                    if (not self.init):
                        self.init = True
                        self.connect_and_subscribe()
                    self.client.check_msg()
                    self.post_status()
                except Exception as e:
                    self.connect_and_subscribe()
                    raise
