from modules.basic.basic_module import BasicModule
from machine import unique_id, reset
from serial_log import SerialLog
import ubinascii
import network
import time
import modules.ota.ota as ota
from modules.web.web_processor import okayHeader, unquote
import gc
from uos import statvfs

class WifiHandler(BasicModule):

    essid = "Wolfen-Sensor-AP"
    defaultSSID = "NOT-CONFIGURED"
    defaultPassword = "no-password-set"

    def __init__(self):
        self.connected = False
        self.apMode = False
        self.downTimeStart = time.ticks_ms()  # start time of no connection
        self.sta_if = network.WLAN(network.STA_IF)
        self.ap_if = network.WLAN(network.AP_IF)
        self.client_id = ubinascii.hexlify(unique_id())
        self.rssi = 0
        self.lastrssitime = 0
        self.lastReconnectTime = 0
        self.version = "unknown"
        self.freerambytes = -1
        self.freediskbytes = -1
        self.apModeGaveUp = False
        self.everConnected = False

    def preStart(self):

        self.ap_if.active(False)

        ssid = self.getPref("wifi", "ssid", self.defaultSSID)
        password = self.getPref("wifi", "password", self.defaultPassword)

        if (self.defaultSSID != ssid or self.defaultPassword != password):
            # Set the essid, so the dhcp hostname is set
            BasicModule.start(self)
            self.essid = "%s-%s" % (self.basicSettings['shortName'], self.client_id.decode('ascii')[-4:])

            self.station()

            self.version = ota.local_version()
            startTime = time.ticks_ms()

            # wait up to 20s for a connection
            SerialLog.log('Waiting for wifi...')
            while (time.ticks_diff(time.ticks_ms(), startTime) < 20000 and not self.sta_if.isconnected()):
                time.sleep(0.1)

            if self.sta_if.isconnected():
                # New connection
                self.connected = True
                self.everConnected = True
                SerialLog.log('Wifi Connected! Config:', self.sta_if.ifconfig())

                self.ota()

            else:
                SerialLog.log('No Wifi available, skipping OTA')

        else:
            SerialLog.log('Wifi not configured, skipping connection and ota update process')


    def start(self):
        BasicModule.start(self)
        self.essid = "%s-%s" % (self.basicSettings['shortName'], self.client_id.decode('ascii')[-4:])

    def get_free_disk_space(self):
        fs_stat = statvfs('/')
        block_sz = fs_stat[0]
        free_blocks = fs_stat[3]
        freebytes = block_sz * free_blocks / 1024
        return freebytes

    def tick(self):
        if (not self.apMode):

            if (self.sta_if.isconnected() and self.connected):
                # Ongoing connection
                now = time.ticks_ms()
                diff = time.ticks_diff(now, self.lastrssitime)
                if (diff > 50000):
                    self.rssi = self.sta_if.status('rssi')
                    self.lastrssitime = now
                    self.freerambytes = gc.mem_free()
                    self.freediskbytes = get_free_disk_space()

                if (self.freerambytes == -1):
                    self.freerambytes = gc.mem_free()
                return

            if (self.sta_if.isconnected() and not self.connected):
                # New connection
                self.connected = True
                self.everConnected = True
                SerialLog.log('Wifi Connected! Config:', self.sta_if.ifconfig())
                # Disable AP on station mode successful connection
                ap_if = network.WLAN(network.AP_IF)
                ap_if.active(False)

                self.ota()

                return

            if (not self.sta_if.isconnected() and self.connected):
                self.downTimeStart = time.ticks_ms()
                self.connected = False
                SerialLog.log('Wifi Connection lost')

            # Check that the wifi is actually configured, start AP if not
            ssid = self.getPref("wifi", "ssid", self.defaultSSID)
            password = self.getPref("wifi", "password", self.defaultPassword)
            if (self.defaultSSID == ssid and self.defaultPassword == password):   
                SerialLog.log("Wifi not configured, starting AP")             
                self.ap()                

            if (not self.sta_if.isconnected()):
                # Connection lost
                now = time.ticks_ms()
                diff = time.ticks_diff(now, self.lastReconnectTime)
                if (diff > 30000):
                    SerialLog.log('No wifi for 30s, attempting to reconnect ...')
                    self.lastReconnectTime = now
                    self.connected = False
                    self.station()
                diff = time.ticks_diff(now, self.downTimeStart)
                if (diff > 86400000):
                    SerialLog.log("Failed to connect to wifi for 24h, rebooting ...")
                    reset()

            if (not self.sta_if.isconnected() and not self.everConnected and not self.apModeGaveUp):
                diff = time.ticks_diff(now, self.downTimeStart)
                if (diff > 60000):
                    SerialLog.log("Failed to connect to wifi, enabling configuration AP ...")
                    self.ap()

        else:
            if (self.ap_if.active()):
                if (len(self.ap_if.status('stations')) == 0):
                    now = time.ticks_ms()
                    diff = time.ticks_diff(now, self.lastReconnectTime)
                    # Turn off AP after 3 mins if no one connects
                    if (diff > 180000): 
                        SerialLog.log("No stations connected to AP, shutting down AP")
                        self.apModeGaveUp = True # this prevents a second AP mode if wifi drops later
                        self.ap_if.active(False)

                        # Check that the wifi is actually configured, switch to station, if it is
                        ssid = self.getPref("wifi", "ssid", self.defaultSSID)
                        password = self.getPref("wifi", "password", self.defaultPassword)
                        if (self.defaultSSID != ssid or self.defaultPassword != password):   
                            # switch back to Station mode
                            self.lastReconnectTime = now
                            self.downTimeStart = now
                            self.apMode = False
                            self.connected = False
                            self.station()
                        else:
                            SerialLog.log("Wifi is not configured, AP timed out, disabling all wifi")
                            if (self.sta_if.active()):
                                self.sta_if.active(False)
            else:
                # Wifi is disabled
                pass


    def getTelemetry(self):
        if (self.apMode):
            if (self.ap_if.active()):
                return {
                    "ssid": self.essid,
                    "ip": b"192.168.4.1",
                    "rssi": "0",
                    "version": self.version,
                    "freeram": self.freerambytes,
                    "freedisk": self.freediskbytes,
                    "wifiMode": b"Access Point",
                    "stations": len(self.ap_if.status('stations'))
                }
            else:
                return {
                    "wifiMode": b"Disabled",
                }
        return {
            "ssid": self.sta_if.config('essid'),
            "ip": self.sta_if.ifconfig()[0],
            "rssi": self.rssi,
            "version": self.version,
            "freeram": self.freerambytes,
            "freedisk": self.freediskbytes,
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

        ssid = self.getPref("wifi", "ssid", self.defaultSSID)
        password = self.getPref("wifi", "password", self.defaultPassword)
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
        SerialLog.log("Starting AP: %s" % (self.essid))
        self.ap_if.active(True)
        self.ap_if.ifconfig(("192.168.4.1", "255.255.255.0",
                            "192.168.4.1", "192.168.4.1"))
        self.ap_if.config(essid=self.essid, authmode=network.AUTH_OPEN)
        self.apMode = True

    def station(self):
        ssid = self.getPref("wifi", "ssid", self.defaultSSID)

        if (ssid == self.defaultSSID):
            SerialLog.log("Wifi not configured, skipping connection")
            self.sta_if.active(False)
            return

        SerialLog.log('\nConnecting to wifi...', ssid)
        try:
            # Make sure the interface is active
            if (not self.sta_if.active()):
                self.sta_if.active(True)
                time.sleep(0.1) # Sleep here to prevent issues when setting dhcp hostname

            # Set The DCHP Hostname
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
            password = self.getPref("wifi", "password", self.defaultPassword)
            self.sta_if.connect(ssid, password)

            # wait up to 20s for a connection
            SerialLog.log('Waiting for wifi...')
            startTime = time.ticks_ms()
            while (time.ticks_diff(time.ticks_ms(), startTime) < 20000 and not self.sta_if.isconnected()):
                time.sleep(0.1)

        except KeyboardInterrupt:
            raise
        except Exception as e:
            SerialLog.log("Error connecting to wifi:", e)
            from sys import print_exception
            print_exception(e)
            self.powerCycleWifi()
        
    def powerCycleWifi(self):
        SerialLog.log('Power cycling wifi station interface...')
        self.sta_if.active(False)
        self.ap_if.active(False)
        time.sleep(2)
        self.sta_if.active(True)

    def ota(self):
        # Squash OTA exceptions
        try:
            # Check for update and update if needed
            if ota.check_for_updates():
                ota.install_new_firmware()
                SerialLog.log('Update installed, rebooting...')
                reset()
        except Exception as e:
            SerialLog.log('OTA failed: ' + str(e))

