import network
from network_settings import NetSettings
import time

class WifiHandler():
    def __init__(self):
        self.connected = False
        self.apMode = False
        self.downTimeStart = time.time() # start time of no connection

    def start(self):
        self.station()

    def ap(self):
        # Enable AP
        print("Starting AP..")
        ap_if = network.WLAN(network.AP_IF)
        sta_if = network.WLAN(network.STA_IF)
        ap_if.active(True)
        ap_if.ifconfig(("192.168.4.1", "255.255.255.0", "192.168.4.1", "192.168.4.1"))
        ap_if.config(essid="4Lights", authmode=network.AUTH_OPEN)
        sta_if.active(False)
        self.apMode = True

    def station(self):
        print('\nConnecting to wifi...')
        sta_if = network.WLAN(network.STA_IF)
        sta_if.active(True)
        netSettings = NetSettings()
        netSettings.load()
        sta_if.connect(netSettings.Ssid, netSettings.Password)
        if (netSettings.Type == b"Static"):
            sta_if.ifconfig((netSettings.Ip, netSettings.Netmask, netSettings.Gateway, b'8.8.8.8'))
    
    def tick(self):
        if (not self.apMode):
            sta_if = network.WLAN(network.STA_IF)
            if (sta_if.isconnected() and not self.connected):
                # New connection
                self.connected = True
                print('Wifi Connected! Config:', sta_if.ifconfig())
                # Disable AP
                ap_if = network.WLAN(network.AP_IF)
                ap_if.active(False)

            if (not sta_if.isconnected() and self.connected):
                # Connection lost
                print('Wifi Connection lost, waiting to reconnect')

            if (not sta_if.isconnected() and not self.connected and self.downTimeStart + 30 < time.time()):
                # Never connected, run an AP after 30s of downtime
                self.ap()
