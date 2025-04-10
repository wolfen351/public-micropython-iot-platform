import json
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
    UTC_DST_OFFSET = 0 # seconds from utc with DST
    UTC_OFFSET = 0 # seconds from utc with DST
    UTC_DST_START = "2020-01-01T00:00:00Z" # DST start time in ISO 8601 format
    UTC_DST_END = "2020-01-01T00:00:00Z" # DST start time in ISO 8601 format

    previous = [-1,-1,-1,-1,-1,-1,-1]
    lastTimeSync = 0

    def __init__(self):
        pass

    def start(self):
        self.sta_if = network.WLAN(network.STA_IF)
        self.tzName = self.getPref("ntp", "tzIANA", "pacific/auckland")

        self.updateTimezoneCache()
        self.updateTimeZoneVars()
        self.updateDST()

    def updateTimezoneCache(self, force = False):
        # check if the file already exists, if it does, we don't need to download it again
        if (not force):
            try:
                with open("timezone.json", "r") as f:
                    return
            except OSError:
                pass
        
        # Get the timezone information from online source using the timezone: 'https://www.timeapi.io/api/timezone/zone?timeZone=Pacific/Auckland'
        # and set the UTC_OFFSET based on the timezone information
        response = None
        try:
            import urequests as requests
            response = requests.get("https://www.timeapi.io/api/timezone/zone?timeZone=%s" % self.tzName, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # save this info to a file for later use
                with open("timezone.json", "w") as f:
                    json.dump(data, f)  # Use json.dump to write valid JSON
            else:
                SerialLog.log("Error getting timezone information: %s" % response.status_code)
        except Exception as e:
            SerialLog.log("Error getting timezone information: %s" % str(e))
            if response:
                response.close()

    def updateTimeZoneVars(self):
        # read the timezone information from the file
        try:
            with open("timezone.json", "r") as f:
                rawdata = f.read()
            data = json.loads(rawdata)

            NtpSync.UTC_BASE_OFFSET = int(data["standardUtcOffset"]["seconds"]) # convert to seconds
            NtpSync.UTC_DST_OFFSET = int(data["dstInterval"]["dstOffsetToUtc"]["seconds"]) # convert to seconds
            NtpSync.UTC_DST_START = data["dstInterval"]["dstStart"]
            NtpSync.UTC_DST_END = data["dstInterval"]["dstEnd"]
            SerialLog.log("Base offset in hours: %s" % (NtpSync.UTC_BASE_OFFSET / 3600))
            SerialLog.log("DST offset in hours: %s" % (NtpSync.UTC_DST_OFFSET / 3600))
            SerialLog.log("DST start: %s" % NtpSync.UTC_DST_START)
            SerialLog.log("DST end: %s" % NtpSync.UTC_DST_END)
        except OSError:
            SerialLog.log("Error reading timezone information from file")
        
    def updateDST(self):
        # Check if DST is in effect
        localTime = time.localtime(time.time())
        SerialLog.log("Local time before UTC Offset & DST Calculation: %s" %str(localTime))
        if (NtpSync.UTC_DST_START != None and NtpSync.UTC_DST_END != None):
            # Convert local time to UTC time
            utcTime = time.mktime(localTime) - NtpSync.UTC_OFFSET
            # let utcTime be a string of the format "2023-10-01T02:00:00Z"
            utcTime = "%04d-%02d-%02dT%02d:%02d:%02dZ" % (localTime[0], localTime[1], localTime[2], localTime[3], localTime[4], localTime[5])
            SerialLog.log("UTC time: %s" % utcTime)
            SerialLog.log("DST time starts: %s" % NtpSync.UTC_DST_START)
            SerialLog.log("DST time ends: %s" % NtpSync.UTC_DST_END)

            # Check if DST is in effect
            if (NtpSync.UTC_DST_START <= utcTime <= NtpSync.UTC_DST_END):
                NtpSync.UTC_OFFSET = NtpSync.UTC_DST_OFFSET
                SerialLog.log("DST is in effect - switching to DST Offset hours: %s" % (NtpSync.UTC_DST_OFFSET / 3600))
            else:   
                NtpSync.UTC_OFFSET = NtpSync.UTC_BASE_OFFSET
                SerialLog.log("DST is not in effect - switching to Base Offset hours: %s" % (NtpSync.UTC_BASE_OFFSET / 3600))                                                

        SerialLog.log("The offset is %s seconds / %s hours" % (NtpSync.UTC_OFFSET, NtpSync.UTC_OFFSET / 3600))
        localTime = time.localtime(time.time() + NtpSync.UTC_OFFSET)
        SerialLog.log("Local time after UTC Offset & DST Calculation: %s" %str(localTime))


    def tick(self):

        if (not NtpSync.gotTime):
            if (self.sta_if.isconnected()):
                # Set up NTP
                try:
                    SerialLog.log("Local time before synchronization: %s" %str(time.localtime(time.time() + NtpSync.UTC_OFFSET)))
                    ntptime.settime()
                    NtpSync.lastTimeSync = time.time()
                    SerialLog.log("Local time after synchronization:  %s" %str(time.localtime(time.time() + NtpSync.UTC_OFFSET)))
                    self.updateDST()
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
            "ntp": "Synchronized",
            "offset": NtpSync.UTC_OFFSET,
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
        data = b"{ \"tz\": \"%s\" }" % (self.getPref("ntp", "tzIANA", "pacific/auckland"))
        return data, headers

    def saventpsettings(self, params):
        # Read form params
        tz = unquote(params.get(b"tz", None))
        self.setPref("ntp", "tzIANA", tz)

        self.updateTimezoneCache(True) # force update the timezone cache
        self.updateTimeZoneVars()
        self.updateDST()

        headers = b"HTTP/1.1 307 Temporary Redirect\r\nLocation: /\r\n"
        return b"", headers, True
