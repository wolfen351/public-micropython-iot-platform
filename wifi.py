import machine
from serial_log import SerialLog
import ubinascii
import network
from network_settings import NetSettings
import time

class WifiHandler():
    def __init__(self):
        self.connected = False
        self.apMode = False
        self.downTimeStart = time.time() # start time of no connection
        self.sta_if = network.WLAN(network.STA_IF)
        self.ap_if = network.WLAN(network.AP_IF)
        self.client_id = ubinascii.hexlify(machine.unique_id())

    def start(self):
        self.station()

    def ap(self):
        # Enable AP
        essid = "TempMon-%s" % self.client_id.decode('ascii')
        SerialLog.log("Starting AP: " + essid)
        self.ap_if.active(True)
        self.ap_if.ifconfig(("192.168.4.1", "255.255.255.0", "192.168.4.1", "192.168.4.1"))
        self.ap_if.config(essid=essid, authmode=network.AUTH_OPEN)
        self.sta_if.active(False)
        self.apMode = True

    def station(self):
        SerialLog.log('\nConnecting to wifi...')
        try:
            self.sta_if.active(True)
            netSettings = NetSettings()
            netSettings.load()
            SerialLog.log("Network: ", netSettings.Ssid)
            self.sta_if.connect(netSettings.Ssid, netSettings.Password)
            if (netSettings.Type == b"Static"):
                self.sta_if.ifconfig((netSettings.Ip, netSettings.Netmask, netSettings.Gateway, b'8.8.8.8'))
        except KeyboardInterrupt:
            raise
        except Exception as e:
            SerialLog.log("Error connecting to wifi:", e)
            pass

    def tick(self):
        if (not self.apMode):
            if (self.sta_if.isconnected() and not self.connected):
                # New connection
                self.connected = True
                SerialLog.log('Wifi Connected! Config:', self.sta_if.ifconfig())
                # Disable AP
                ap_if = network.WLAN(network.AP_IF)
                ap_if.active(False)

            if (not self.sta_if.isconnected() and self.connected):
                # Connection lost
                SerialLog.log('Wifi Connection lost, waiting to reconnect')
                pass
            
            if (not self.sta_if.isconnected() and not self.connected and self.downTimeStart + 30 < time.time()):
                # Never connected, run an AP after 30s of downtime
                self.ap()
