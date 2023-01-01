from modules.basic.basic_module import BasicModule
from serial_log import SerialLog
import ntptime
import time
import network


# Screen is 320x240 px
# X is left to right on the small side (0-240)
# Y is up to down on the long side (0-320)

class NtpSync(BasicModule):

    gotTime = False
    ntptime.host = "0.nz.pool.ntp.org"
    UTC_BASE_OFFSET = 12 * 60 * 60
    UTC_OFFSET = 12 * 60 * 60
    previous = [-1,-1,-1,-1,-1,-1,-1]

    def __init__(self):
        pass


    def start(self):
        self.sta_if = network.WLAN(network.STA_IF)

    def tick(self):

        if (not self.gotTime):
            if (self.sta_if.isconnected()):
                # Set up NTP
                try:
                    SerialLog.log("Local time before synchronization: %s" %str(time.localtime()))
                    #make sure to have internet connection
                    ntptime.settime()
                    SerialLog.log("Local time after synchronization: %s" %str(time.localtime(time.time())))
                    localTime = time.localtime(time.time() + self.UTC_OFFSET)
                    SerialLog.log("Local time after UTC Offet & DST Calculation: %s" %str(localTime))
                    self.gotTime = True
                except Exception as e:
                    SerialLog.log("Error syncing time: ", e)

        doy = time.localtime()[-1]
        if (doy < 92 or doy > 268): # 2 April, 25 Sept
            self.UTC_OFFSET = self.UTC_BASE_OFFSET + 3600

    def getTelemetry(self):
        localTime = time.localtime(time.time() + self.UTC_OFFSET)
        telemetry = {
            "time" : localTime
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
        }

    def getIndexFileName(self):
        return {  }

    # Internal code here
