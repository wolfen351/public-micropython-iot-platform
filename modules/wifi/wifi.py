from modules.basic.basic_module import BasicModule
from machine import unique_id, reset
from serial_log import SerialLog
import ubinascii
import network
import time
import modules.ota.ota as ota
from modules.web.web_processor import okayHeader, unquote
import gc
from os import statvfs, uname
from sys import print_exception

class WifiHandler(BasicModule):

    hostname = None
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
        self.freerambytes = -1
        self.freediskbytes = -1
        self.apModeGaveUp = False
        self.everConnected = False
        self.stationCount = 0
        self.connectionTime = 0

    # Called by the startup code as booting the board
    def preStart(self):

        self.ap_if.active(False)

        ssid = self.getPref("wifi", "ssid", self.defaultSSID)
        password = self.getPref("wifi", "password", self.defaultPassword)

        BasicModule.start(self)
        self.hostname = "%s-%s" % (self.basicSettings['shortName'], self.client_id.decode('ascii')[-4:])

        # If wifi is configured, then attempt to connect
        if (self.defaultSSID != ssid or self.defaultPassword != password):
            self.station()
            # wait up to 20s for a connection
            SerialLog.log('Waiting for wifi...')
            startTime = time.ticks_ms()
            while (time.ticks_diff(time.ticks_ms(), startTime) < 20000 and not self.sta_if.isconnected()):
                time.sleep(0.1)

            if self.sta_if.isconnected():
                # New connection
                self.connected = True
                self.everConnected = True
                self.connectionTime = time.ticks_ms()  # Store the connection time
                SerialLog.log('Wifi Connected! Config:', self.sta_if.ifconfig())

                self.ota()

            else:
                SerialLog.log('No Wifi available, skipping OTA')

        else:
            SerialLog.log('Wifi not configured, skipping connection and ota update process')


    def start(self):
        BasicModule.start(self)
        self.defaultSSID = "%s-%s" % (self.basicSettings['shortName'], self.client_id.decode('ascii')[-4:])

    def get_free_disk_space(self):
        fs_stat = statvfs('/')
        block_sz = fs_stat[0]
        free_blocks = fs_stat[3]
        freebytes = block_sz * free_blocks
        return freebytes

    def tick(self):
        if (not self.apMode):

            # Ongoing connection
            if (self.sta_if.isconnected() and self.connected):
                now = time.ticks_ms()
                diff = time.ticks_diff(now, self.lastrssitime)
                if (diff > 50000):
                    self.rssi = self.sta_if.status('rssi')
                    self.lastrssitime = now
                    self.freerambytes = gc.mem_free()
                    self.freediskbytes = self.get_free_disk_space()

                if (self.freerambytes == -1):
                    self.freerambytes = gc.mem_free()
                return

            # New connection
            if (self.sta_if.isconnected() and not self.connected):
                self.connected = True
                self.everConnected = True
                self.connectionTime = time.ticks_ms()  # Store the connection time
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
            now = time.ticks_ms()

            if (self.defaultSSID == ssid and self.defaultPassword == password):   
                # wifi is not configured, switch to AP mode
                SerialLog.log("Wifi not configured, starting AP")             
                self.ap()                
            elif (not self.sta_if.isconnected()):
                # Connection lost, but wifi is configured
                diff = time.ticks_diff(now, self.lastReconnectTime)
                if (diff > 30000):
                    SerialLog.log('Connecting to wifi ...')
                    self.lastReconnectTime = now
                    self.connected = False
                    self.station()
                diff = time.ticks_diff(now, self.downTimeStart)
                if (diff > 5400000):  # 90 minutes in milliseconds
                    SerialLog.log("Failed to connect to wifi for 90 minutes, rebooting ...")
                    reset()

            if (not self.sta_if.isconnected() and not self.everConnected and not self.apModeGaveUp):
                diff = time.ticks_diff(now, self.downTimeStart)
                if (diff > 60000):
                    SerialLog.log("Failed to connect to wifi (60s), enabling configuration AP ...")
                    self.ap()

        else:
            # we are in apmode
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
                    # AP is active and there are stations connected
                    if (self.stationCount < len(self.ap_if.status('stations'))):
                        SerialLog.log("New station connected to AP")
                    elif (self.stationCount > len(self.ap_if.status('stations'))):
                        SerialLog.log("Station disconnected from AP")
                    self.stationCount = len(self.ap_if.status('stations'))
                    
            else:
                # Wifi is disabled
                pass


    def getTelemetry(self):
        if (self.apMode):
            if (self.ap_if.active()):
                return {
                    "ssid": self.ap_if.config('essid'),
                    "ip": b"192.168.4.1",
                    "rssi": "0",
                    "version": ota.local_version(),
                    "freeram": self.freerambytes,
                    "freedisk": self.freediskbytes,
                    "osname": uname().sysname,
                    "wifiMode": b"Access Point",
                    "stations": len(self.ap_if.status('stations'))
                }
            else:
                return {
                    "wifiMode": b"Disabled",
                }
        else:
            wifiUptime = time.ticks_diff(time.ticks_ms(), self.connectionTime) // 1000  # Calculate connected time in seconds
            return {
                "ssid": self.sta_if.config('essid'),
                "ip": self.sta_if.ifconfig()[0],
                "rssi": self.rssi,
                "version": ota.local_version(),
                "freeram": self.freerambytes,
                "freedisk": self.freediskbytes,
                "osname": uname().release,
                "wifiMode": b"Station",
                "wifiUptime": wifiUptime
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
            b"/getlog": self.getlog,
            b"/forceUpdate": self.forceUpdate,
            b"/firmware": b"/modules/wifi/firmware.html",
            b'/upload': self.webUpload
        }

    def getIndexFileName(self):
        return {"wifi": "/modules/wifi/index.html"}

    # internal functions

    def forceUpdate(self, params):
        # Squash OTA exceptions
        try:
            # Check for update and update if needed
            SerialLog.log("Forcing OTA update")
            ota.force_version_number()
            ota.force_update()
            return b"Update started, rebooting...", okayHeader, True
        except Exception as e:
            SerialLog.log('OTA failed: ' + str(e))
            print_exception(e)
            return b"OTA failed exf: " + str(e).encode('utf-8'), okayHeader

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
    
    def webUpload(self, params, post_params):
        headers = okayHeader

        # in post_params array, each element has a name. The file data is in filedata and the file name is in location
        # eg: [{'name': b'location', 'filename': None, 'value': b'/k3s.yaml'}, {'name': b'file', 'filename': b'k3s.yaml', 'filedata': b'aaa'}]

        location = None
        filedata = None
        for param in post_params:
            if param.get('name', None) == b'location':
                location = param.get('value', None).decode('ascii')
            if param.get('name', None) == b'file':
                filedata = param.get('filedata', None)

        if filedata and location:
            SerialLog.log("File upload data bytes:", len(filedata))
            # save the filedata bytes to the location on disk
            with open(location, "wb") as f:
                f.write(filedata)
            data = 'FILE UPLOADED'
        else:
            data = 'NO FILE UPLOADED'
        
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
        SerialLog.log("Starting AP: %s" % (self.defaultSSID))
        self.ap_if.active(True)
        self.ap_if.ifconfig(("192.168.4.1", "255.255.255.0",
                            "192.168.4.1", "192.168.4.1"))
        self.ap_if.config(essid=self.defaultSSID, authmode=network.AUTH_OPEN)
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
                try:
                    self.sta_if.config(pm=self.sta_if.PM_NONE)                
                except Exception as e:
                    SerialLog.log("Failed to set power management mode to NONE")

            if self.basicSettings.get("suppressHostName", False) == True:
                SerialLog.log("Suppressing DHCP hostname")
            else:
                # Set The DCHP Hostname
                try:
                    SerialLog.log("Setting DHCP hostname", self.hostname)
                    time.sleep(0.1) # Sleep here to prevent issues when setting dhcp hostname
                    self.sta_if.config(dhcp_hostname=self.hostname)
                except Exception as e:
                    SerialLog.log("Failed to set DHCP hostname")
                    print_exception(e)

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
            
            # Check if wifi is up
            if not self.sta_if.isconnected():
                SerialLog.log('Failed to connect to wifi')
            else:
                SerialLog.log('Wifi Connected!')

        except KeyboardInterrupt:
            raise
        except Exception as e:
            SerialLog.log("Error connecting to wifi:", str(e))
            print_exception(e)
            self.powerCycleWifi()
        
    def powerCycleWifi(self):
        SerialLog.log('Power cycling wifi station interface...')
        self.sta_if.active(False)
        self.ap_if.active(False)
        time.sleep(2)
        self.sta_if.active(True)
        try:
            self.sta_if.config(pm=self.sta_if.PM_NONE)
        except Exception as e:
            SerialLog.log("Failed to set power management mode to NONE")

    def ota(self):

        # Squash OTA exceptions
        try:
            # Check for update and update if needed
            if ota.check_for_updates():
                ota.install_new_firmware()
                SerialLog.log('Update installed, rebooting...')
                reset()
        except Exception as e:
            SerialLog.log('OTA failed ex: ' + str(e))
            print_exception(e)

