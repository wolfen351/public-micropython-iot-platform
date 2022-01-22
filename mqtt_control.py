from mqtt import MQTTClient
from mqtt_settings import MqttSettings
from serial_log import SerialLog
import ubinascii
import machine
import network
import time

class MQTTControl():
    def __init__(self):
        self.client_id = ubinascii.hexlify(machine.unique_id())
        self.init = False
        self.status = None
        self.sta_if = network.WLAN(network.STA_IF)

    def sub_cb(self, topic, msg):
        SerialLog.log("MQTT: ", topic, msg)

    def connect_and_subscribe(self):
        self.client = MQTTClient(self.client_id, self.mqtt_server)
        self.client.set_callback(self.sub_cb)
        self.client.connect()
        self.client.subscribe(self.topic_sub)
        SerialLog.log('Connected to %s MQTT broker, subscribed to %s topic' % (self.mqtt_server, self.topic_sub))
        self.home_assistant_configure()

    def home_assistant_configure(self):
        homeAssistantUrl = "homeassistant/sensor/%s" % self.client_id.decode('ascii')
        self.client.publish("%s/config" % homeAssistantUrl, '{"name":"temp_sensor_%s","dev_cla":"temperature","stat_t":"%s/state","unit_of_meas":"C","val_tpl":"{{value_json.temperature}}"}' % (self.client_id.decode('ascii'), homeAssistantUrl) )
#        self.client.publish("%s/config" % homeAssistantUrl, '{"name":"temp_sensor_%s","device_class":"temperature","state_topic":"%s/state","unit_of_meas":"°C","val_tpl":"{{value_json.temperature}}"}' % (self.client_id, homeAssistantUrl))

    def post_status(self):

        if (self.status == None):
            self.status = [None, None, None, time.time(), None, None, None, None, None, None, None, None, None, None]

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

        if (self.status[4] != self.temp.currentTemp()):
            self.client.publish(self.topic_pub + b"/temp/current", str(self.temp.currentTemp()))
            self.status[4] = self.temp.currentTemp()

    def start(self, temp):

        settings = MqttSettings()
        settings.load()
        self.enabled = settings.Enable
        self.mqtt_server = settings.Server
        if (settings.Subscribe != b""):
            self.topic_sub = settings.Subscribe
        else:
            self.topic_sub = b'tempMon/%s/command/#' % (self.client_id)

        if (settings.Publish != b""):
            self.topic_pub = settings.Publish
        else:
            self.topic_pub = b'tempMon/%s/status' % (self.client_id)
        
        self.temp = temp

    def settings(self, settingsVals):
        # Apply the new settings
        self.enabled = settingsVals[0]
        self.mqtt_server = settingsVals[1]

        if (settingsVals[2] != b""):
            self.topic_sub = settingsVals[2]
        else:
            self.topic_sub = b'tempMon/%s/command/#' % (self.client_id)

        if (settingsVals[3] != b""):
            self.topic_pub = settingsVals[3]
        else: 
            self.topic_pub = b'tempMon/%s/status' % (self.client_id)

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
