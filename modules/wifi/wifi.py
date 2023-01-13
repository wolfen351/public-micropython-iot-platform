from modules.basic.basic_module import BasicModule
import machine
from serial_log import SerialLog
import ubinascii
import network
from modules.wifi.wifi_settings import WifiSettings
import time
import modules.ota.ota as ota
from modules.web.web_processor import okayHeader, unquote
import gc


class WifiHandler(BasicModule):

    def __init__(self):
        self.connected = False
        self.apMode = False
        self.downTimeStart = time.time()  # start time of no connection
        self.sta_if = network.WLAN(network.STA_IF)
        self.ap_if = network.WLAN(network.AP_IF)
        self.client_id = ubinascii.hexlify(machine.unique_id())
        self.rssi = 0
        self.lastrssitime = 0
        self.lastReconnectTime = 0
        self.version = "unknown"
        self.freeram = -1

    def start(self):
        BasicModule.start(self)
        self.essid = "%s-%s" % (self.basicSettings['shortName'], self.client_id.decode('ascii')[-4:])

        self.station()
        self.version = ota.local_version()

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
                if ota.check_for_updates():
                    ota.install_new_firmware()
                    machine.reset()

            if (not self.sta_if.isconnected() and self.connected):
                # Connection lost
                now = time.ticks_ms()
                diff = time.ticks_diff(now, self.lastReconnectTime)
                if (diff > 10000):
                    SerialLog.log('Wifi Connection lost, reconnecting..')
                    self.lastReconnectTime = now
                    self.station()

            if (not self.sta_if.isconnected() and not self.connected and self.downTimeStart + 30 < time.time()):
                # Never connected, run an AP after 30s of downtime
                SerialLog.log("Failed to connect to wifi, switching to AP mode...")
                self.ap()

            if (self.sta_if.isconnected() and self.connected):
                # Ongoing connection
                now = time.ticks_ms()
                diff = time.ticks_diff(now, self.lastrssitime)
                if (diff > 50000):
                    self.rssi = self.sta_if.status('rssi')
                    self.lastrssitime = now
                    self.freeram = gc.mem_free()

            if (self.freeram == -1):
                self.freeram = gc.mem_free()

        else:
            if (len(self.ap_if.status('stations')) == 0):
                now = time.ticks_ms()
                diff = time.ticks_diff(now, self.lastReconnectTime)
                if (diff > 60000):
                    SerialLog.log("No stations connected to AP, switching back to station mode")
                    self.lastReconnectTime = now
                    self.apMode = False
                    self.station()

    def getTelemetry(self):
        if (self.apMode):
            return {
                "ssid": self.essid,
                "ip": b"192.168.4.1",
                "rssi": "0",
                "version": self.version,
                "freeram": self.freeram,
                "wifiMode": b"Access Point",
                "stations": len(self.ap_if.status('stations'))
            }
        return {
            "ssid": self.sta_if.config('essid'),
            "ip": self.sta_if.ifconfig()[0],
            "rssi": self.rssi,
            "version": self.version,
            "freeram": self.freeram,
            "wifiMode": b"Station"
        }
    

    def processTelemetry(self, telemetry):
        pass

    def getCommands(self):
        return []

    def processCommands(self, commands):
        pass

    def getRoutes(self):
        return {
            b"/network": b"/modules/wifi/web_network.hctml",
            b"/log": b"/modules/wifi/web_log.html",
            b"/netloadsettings": self.loadnetsettings,
            b"/netsavesettings": self.savenetsettings,
            b"/getlog": self.getlog
        }

    def getIndexFileName(self):
        return {"wifi": "/modules/wifi/wifi_index.html"}

    # internal functions

    def loadnetsettings(self, params):
        settings = WifiSettings()
        settings.load()
        headers = okayHeader
        data = b"{ \"ssid\": \"%s\", \"password\": \"%s\", \"type\": \"%s\", \"ip\": \"%s\", \"netmask\": \"%s\", \"gateway\": \"%s\" }" % (
            settings.Ssid, settings.Password, settings.Type, settings.Ip, settings.Netmask, settings.Gateway)
        return data, headers

    def getlog(self, params):
        headers = okayHeader
        data = SerialLog.logHistory()
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
        return b"", headers, True

    def ap(self):
        # Enable AP
        SerialLog.log("Starting AP: " + self.essid)
        self.ap_if.active(True)
        self.ap_if.ifconfig(("192.168.4.1", "255.255.255.0",
                            "192.168.4.1", "192.168.4.1"))
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
            self.sta_if.connect(netSettings.Ssid, netSettings.Password)
            if (netSettings.Type == b"Static"):
                self.sta_if.ifconfig(
                    (netSettings.Ip, netSettings.Netmask, netSettings.Gateway, b'8.8.8.8'))
            SerialLog.log("Wifi connection starting..")
        except KeyboardInterrupt:
            raise
        except Exception as e:
            SerialLog.log("Error connecting to wifi:", e)
            import sys
            sys.print_exception(e)
            pass
