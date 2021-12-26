from mqtt import MQTTClient
import ubinascii
import machine
import network

class MQTTControl():
    def __init__(self):
        self.lights = None
        self.mqtt_server = "mqtt.wolfen.za.net"
        self.client_id = ubinascii.hexlify(machine.unique_id())
        self.topic_sub = b'light4/%s/command' % (self.client_id)
        self.topic_pub = b'light4/%s/status' % (self.client_id)
        self.client = None

    def sub_cb(topic, msg):
        print((topic, msg))
        if topic == b'notification' and msg == b'received':
            print('ESP received hello message')

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


    def start(self, lights):
        self.lights = lights

        self.sta_if = network.WLAN(network.STA_IF)
        self.connect_and_subscribe()
        self.client.publish(self.topic_pub + b"/up", "true")
        self.client.publish(self.topic_pub + b"/ip", self.sta_if.ifconfig()[0])
        self.client.publish(self.topic_pub + b"/ssid", self.sta_if.config('essid'))
        self.client.publish(self.topic_pub + b"/rssi", str(self.sta_if.status('rssi')))
        print("MQTT Client started")

    def tick(self):
        self.client.check_msg()
