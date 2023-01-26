from modules.basic.basic_module import BasicModule
from machine import unique_id, reset
from serial_log import SerialLog
import ubinascii
import network
import time
import modules.ota.ota as ota
from modules.web.web_processor import okayHeader, unquote
import gc


class WifiHandler(BasicModule):

    essid = "ElectronicAP"

    def __init__(self):
        self.connected = False
        self.apMode = False
        self.downTimeStart = time.time()  # start time of no connection
        self.sta_if = network.WLAN(network.STA_IF)
        self.ap_if = network.WLAN(network.AP_IF)
        self.client_id = ubinascii.hexlify(unique_id())
        self.rssi = 0
        self.lastrssitime = 0
        self.lastReconnectTime = 0
        self.version = "unknown"
        self.freeram = -1
        self.apModeGaveUp = False

    def preStart(self):

        self.ap_if.active(False)
        self.station()

        self.version = ota.local_version()
        startTime = time.ticks_ms()

        SerialLog.log('Waiting for wifi...')
        while (time.ticks_diff(time.ticks_ms(), startTime) < 5000 and not self.sta_if.isconnected()):
            time.sleep(0.1)

        # wait up to 5s for a connection
        if self.sta_if.isconnected():
            # New connection
            self.connected = True
            SerialLog.log('Wifi Connected! Config:', self.sta_if.ifconfig())
            # Check for update and update if needed
            if ota.check_for_updates():
                ota.install_new_firmware()
                reset()
        else:
            SerialLog.log('No Wifi available, skipping OTA')



    def start(self):
        BasicModule.start(self)
        self.essid = "%s-%s" % (self.basicSettings['shortName'], self.client_id.decode('ascii')[-4:])

    def tick(self):
        if (not self.apMode):

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
                return

            if (self.sta_if.isconnected() and not self.connected):
                # New connection
                self.connected = True
                SerialLog.log('Wifi Connected! Config:', self.sta_if.ifconfig())
                # Disable AP on station mode successful connection
                ap_if = network.WLAN(network.AP_IF)
                ap_if.active(False)
                return

            if (not self.sta_if.isconnected() and self.connected):
                self.downTimeStart = time.ticks_ms()
                self.connected = False
                SerialLog.log('Wifi Connection lost')

            if (not self.sta_if.isconnected()):
                # Connection lost
                now = time.ticks_ms()
                diff = time.ticks_diff(now, self.lastReconnectTime)
                if (diff > 10000):
                    SerialLog.log('Reconnecting..')
                    self.lastReconnectTime = now
                    self.connected = False
                    self.station()

                diff = time.ticks_diff(now, self.downTimeStart)
                if (diff > 30000 and not self.apModeGaveUp):
                    SerialLog.log("Failed to connect to wifi, enabling configuration AP ...")
                    self.ap()

        else:
            if (len(self.ap_if.status('stations')) == 0):
                now = time.ticks_ms()
                diff = time.ticks_diff(now, self.lastReconnectTime)
                if (diff > 300000):
                    SerialLog.log("No stations connected to AP, shutting down AP")
                    self.ap_if.active(False)

                    # switch back to Station mode
                    self.lastReconnectTime = now
                    self.downTimeStart = now
                    self.apMode = False
                    self.connected = False
                    self.apModeGaveUp = True # this prevents a second AP mode if wifi drops later
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
            b"/network": b"/modules/wifi/settings.html",
            b"/log": b"/modules/wifi/log.html",
            b"/netloadsettings": self.loadnetsettings,
            b"/netsavesettings": self.savenetsettings,
            b"/getlog": self.getlog
        }

    def getIndexFileName(self):
        return {"wifi": "/modules/wifi/index.html"}

    # internal functions

    def loadnetsettings(self, params):

        ssid = self.getPref("wifi", "ssid", "NETWORK")
        password = self.getPref("wifi", "password", "password")
        type = self.getPref("wifi", "type", "DHCP")
        ip = self.getPref("wifi", "ip", "")
        netmask = self.getPref("wifi", "netmask", "")
        gateway = self.getPref("wifi", "gateway", "")

        headers = okayHeader
        data = b"{ \"ssid\": \"%s\", \"password\": \"%s\", \"type\": \"%s\", \"ip\": \"%s\", \"netmask\": \"%s\", \"gateway\": \"%s\" }" % (
            ssid, password, type, ip, netmask, gateway)
        return data, headers

    def getlog(self, params):
        headers = okayHeader
        data = SerialLog.logHistory()
        return data, headers

    def savenetsettings(self, params):
        # Read form params
        self.setPref("wifi", "ssid", unquote(params.get(b"Ssid", None)))
        self.setPref("wifi", "password", unquote(params.get(b"Password", None)))
        self.setPref("wifi", "type", unquote(params.get(b"Type", None)))
        self.setPref("wifi", "ip", unquote(params.get(b"Ip", None)))
        self.setPref("wifi", "netmask", unquote(params.get(b"Netmask", None)))
        self.setPref("wifi", "gateway", unquote(params.get(b"Gateway", None)))

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
        self.apMode = True

    def station(self):
        ssid = self.getPref("wifi", "ssid", "NETWORK")
        SerialLog.log('\nConnecting to wifi...', ssid)
        try:
            if (self.sta_if.isconnected()):
                self.sta_if.disconnect()
            self.sta_if.active(True)
            self.sta_if.config(dhcp_hostname=self.essid)

            # set static ip
            type = self.getPref("wifi", "type", "DHCP")
            if (type == "Static"):
                ip = self.getPref("wifi", "ip", "")
                SerialLog.log('Assigning Static IP:', ip)
                netmask = self.getPref("wifi", "netmask", "")
                gateway = self.getPref("wifi", "gateway", "")
                self.sta_if.ifconfig((ip, netmask, gateway, '8.8.8.8'))

            # actually connect
            password = self.getPref("wifi", "password", "password")
            self.sta_if.connect(ssid, password)

        except KeyboardInterrupt:
            raise
        except Exception as e:
            SerialLog.log("Error connecting to wifi:", e)
            from sys import print_exception
            print_exception(e)
        
