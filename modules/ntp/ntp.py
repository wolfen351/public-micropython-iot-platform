from modules.basic.basic_module import BasicModule
from modules.web.web_processor import okayHeader, unquote
from serial_log import SerialLog
import ntptime
import time
import network
 
class NtpSync(BasicModule):

    gotTime = False
    ntptime.host = "0.nz.pool.ntp.org"
    UTC_BASE_OFFSET = 0 # seconds from utc without DST
    UTC_OFFSET = 0 # seconds from utc with DST
    previous = [-1,-1,-1,-1,-1,-1,-1]
    lastTimeSync = 0

    def __init__(self):
        pass

    def start(self):
        self.sta_if = network.WLAN(network.STA_IF)
        NtpSync.UTC_BASE_OFFSET = self.getPref("ntp", "defaultOffset", 43200) # default is 12 hours
        self.tzName = self.getPref("ntp", "tzIANA", "pacific/auckland")

        # Implement DST here
        NtpSync.UTC_OFFSET = NtpSync.UTC_BASE_OFFSET
        if (self.tzName == "pacific/auckland"):
            NtpSync.UTC_OFFSET += 3600

    def tick(self):

        if (not NtpSync.gotTime):
            if (self.sta_if.isconnected()):
                # Set up NTP
                try:
                    SerialLog.log("Local time before synchronization: %s" %str(time.localtime()))
                    ntptime.settime()
                    NtpSync.lastTimeSync = time.time()
                    SerialLog.log("Local time after synchronization: %s" %str(time.localtime(time.time())))
                    SerialLog.log("The offset is %s seconds" %str(NtpSync.UTC_OFFSET))
                    localTime = time.localtime(time.time() + NtpSync.UTC_OFFSET)
                    SerialLog.log("Local time after UTC Offset & DST Calculation: %s" %str(localTime))
                    NtpSync.gotTime = True
                except Exception as e:
                    SerialLog.log("Error syncing time: ", e)
                    import sys
                    sys.print_exception(e)

        if (not self.sta_if.isconnected()):
            NtpSync.gotTime = False # resync time when wifi comes back

        if (NtpSync.lastTimeSync != 0):
            if (time.time() - NtpSync.lastTimeSync > 3 * 3600):
                NtpSync.gotTime = False # resync time every 3 hours

    def getTelemetry(self):
        
        if (not NtpSync.gotTime):
            return { "ntp": "Waiting" }
        
        localTime = time.localtime(time.time() + NtpSync.UTC_OFFSET)
        # format localTime as a ISO 8601 string
        localTime = "%04d-%02d-%02dT%02d:%02d:%02d" % (localTime[0], localTime[1], localTime[2], localTime[3], localTime[4], localTime[5])
        telemetry = {
            "time" : localTime,
            "timeZone": self.tzName,
            "ntp": "Synchronized"
        }
        return telemetry

    def processTelemetry(self, telemetry):
        pass

    def getCommands(self):
        return []

    def processCommands(self, commands):
        pass

    def getRoutes(self):
        return {
            b"/ntp": b"/modules/ntp/ntp_settings.html",
            b"/spacetime.min.js": b"/modules/ntp/spacetime.min.js",
            b"/timezones.js": b"/modules/ntp/timezones.js",
            b"/ntploadsettings": self.loadntpsettings,
            b"/ntpsavesettings": self.saventpsettings,
        }

    def getIndexFileName(self):
        return {"ntp": "/modules/ntp/ntp_index.html"}

    # Internal code here

    def loadntpsettings(self, params):
        headers = okayHeader
        data = b"{ \"tz\": \"%s\", \"defaultOffset\": \"%s\" }" % (self.getPref("ntp", "tzIANA", "pacific/auckland"), self.getPref("ntp", "defaultOffset", 0))
        return data, headers

    def saventpsettings(self, params):
        # Read form params
        tz = unquote(params.get(b"tz", None))
        defaultOffset = int(unquote(params.get(b"defaultOffset", None)))

        self.setPref("ntp", "tzIANA", tz)
        self.setPref("ntp", "defaultOffset", defaultOffset)

        headers = b"HTTP/1.1 307 Temporary Redirect\r\nLocation: /\r\n"
        return b"", headers, True
