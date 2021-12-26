from mqtt import MQTTClient
import ubinascii
import machine
import network
import time

class MQTTControl():
    def __init__(self):
        self.lights = None
        self.mqtt_server = "mqtt.wolfen.za.net"
        self.client_id = ubinascii.hexlify(machine.unique_id())
        self.topic_sub = b'light4/%s/command/#' % (self.client_id)
        self.topic_pub = b'light4/%s/status' % (self.client_id)
        self.client = None
        self.status = [None, None, None, time.time()]

    def sub_cb(self, topic, msg):
        print((topic, msg))
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
        print("Reading command param")
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
            self.client.publish(self.topic_pub + b"/up", "true")
            self.status[0] = "true"

        if (self.status[1] != self.sta_if.ifconfig()[0]):
            self.client.publish(self.topic_pub + b"/ip", self.sta_if.ifconfig()[0])
            self.status[1] = self.sta_if.ifconfig()[0]

        if (self.status[2] != self.sta_if.config('essid')):
            self.client.publish(self.topic_pub + b"/ssid", self.sta_if.config('essid'))
            self.status[2] = self.sta_if.config('essid')

        # Report RSSI every min
        if (self.status[3] < time.time()):
            self.client.publish(self.topic_pub + b"/rssi", str(self.sta_if.status('rssi')))
            self.status[3] = time.time() + 60

    def start(self, lights):
        self.lights = lights

        self.sta_if = network.WLAN(network.STA_IF)
        self.connect_and_subscribe()
        self.post_status()

        print("MQTT Client started")

    def tick(self):
        self.client.check_msg()
        self.post_status()
