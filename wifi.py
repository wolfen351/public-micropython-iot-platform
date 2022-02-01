from basic_module import BasicModule
import machine
from serial_log import SerialLog
import ubinascii
import network
from wifi_settings import WifiSettings
import time
import uota
from web_processor import okayHeader, unquote

class WifiHandler(BasicModule):

    def __init__(self, basicSettings):
        self.connected = False
        self.apMode = False
        self.downTimeStart = time.time() # start time of no connection
        self.sta_if = network.WLAN(network.STA_IF)
        self.ap_if = network.WLAN(network.AP_IF)
        self.client_id = ubinascii.hexlify(machine.unique_id())
        self.essid = "%s-%s" % (basicSettings['ShortName'], self.client_id.decode('ascii'))

    def start(self):
        self.station()

    def tick(self):
        if (not self.apMode):
            if (self.sta_if.isconnected() and not self.connected):
                # New connection
                self.connected = True
                SerialLog.log('Wifi Connected! Config:', self.sta_if.ifconfig())
                # Disable AP
                ap_if = network.WLAN(network.AP_IF)
                ap_if.active(False)
                # Check for update and update if needed
                if uota.check_for_updates():
                    uota.install_new_firmware()
                    machine.reset()

            if (not self.sta_if.isconnected() and self.connected):
                # Connection lost
                SerialLog.log('Wifi Connection lost, waiting to reconnect')
                pass
            
            if (not self.sta_if.isconnected() and not self.connected and self.downTimeStart + 30 < time.time()):
                # Never connected, run an AP after 30s of downtime
                self.ap()

    def getTelemetry(self):
        return { 
            "ssid": self.sta_if.config('essid'), 
            "ip": self.sta_if.ifconfig()[0],
            "rssi": self.sta_if.status('rssi')
        }

    def processTelemetry(self, telemetry):
        pass

    def getCommands(self):
        return []

    def processCommands(self, commands):
        pass

    def getRoutes(self):
        return {
            b"/network": b"./web_network.html", 
            b"/netloadsettings": self.loadnetsettings,
            b"/netsavesettings": self.savenetsettings
        }

    # internal functions

    def loadnetsettings(self, params):
        settings = WifiSettings()
        settings.load()
        headers = okayHeader
        data = b"{ \"ssid\": \"%s\", \"password\": \"%s\", \"type\": \"%s\", \"ip\": \"%s\", \"netmask\": \"%s\", \"gateway\": \"%s\" }" % (settings.Ssid, settings.Password, settings.Type, settings.Ip, settings.Netmask, settings.Gateway)
        return data, headers

    def savenetsettings(self, params):
        # Read form params
        ssid = unquote(params.get(b"Ssid", None))
        password = unquote(params.get(b"Password", None))
        type = unquote(params.get(b"Type", None))
        ip = unquote(params.get(b"Ip", None))
        netmask = unquote(params.get(b"Netmask", None))
        gateway = unquote(params.get(b"Gateway", None))
        settings = WifiSettings(ssid, password, type, ip, netmask, gateway)
        settings.write()
        headers = b"HTTP/1.1 307 Temporary Redirect\r\nLocation: /\r\n"
        # Connect using the new settings
        self.station()
        # Reboot
        machine.reset()
        return b"", headers

    def ap(self):
        # Enable AP
        SerialLog.log("Starting AP: " + self.essid)
        self.ap_if.active(True)
        self.ap_if.ifconfig(("192.168.4.1", "255.255.255.0", "192.168.4.1", "192.168.4.1"))
        self.ap_if.config(essid=self.essid, authmode=network.AUTH_OPEN)
        self.sta_if.active(False)
        self.apMode = True

    def station(self):
        SerialLog.log('\nConnecting to wifi...')
        try:
            self.ap_if.active(False)
            if (self.sta_if.isconnected()):
                self.sta_if.disconnect()
            self.sta_if.active(True)
            self.sta_if.config(dhcp_hostname=self.essid)
            netSettings = WifiSettings()
            netSettings.load()
            SerialLog.log("Network: ", netSettings.Ssid)
            self.sta_if.connect(netSettings.Ssid, netSettings.Password)
            if (netSettings.Type == b"Static"):
                self.sta_if.ifconfig((netSettings.Ip, netSettings.Netmask, netSettings.Gateway, b'8.8.8.8'))
        except KeyboardInterrupt:
            raise
        except Exception as e:
            SerialLog.log("Error connecting to wifi:", e)
            import sys
            sys.print_exception(e)
            pass


