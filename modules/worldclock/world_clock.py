from modules.basic.basic_module import BasicModule
from modules.touchscreen.ili9341 import Display, color565
from modules.touchscreen.xglcd_font import XglcdFont
from machine import Pin, SPI
from serial_log import SerialLog
import time

# Screen is 320x240 px
# X is left to right on the small side (0-240)
# Y is up to down on the long side (0-320)

class WorldClock(BasicModule):

    spi = SPI(1, baudrate=60000000, sck=Pin(7), mosi=Pin(11), miso=Pin(9))
    display = Display(spi, dc=Pin(12), cs=Pin(5), rst=Pin(0))
    display.clear(color565(0, 0, 0))
    xpt = None
    # path, width, height, start_letter=32, letter_count=96, bytes_per_letter=0
    #font = XglcdFont('modules/touchscreen/font25x57.c', 25, 57, 32, 97, 228)
    font = XglcdFont('modules/touchscreen/Roboto_18x22.c', 18, 22)
    display.draw_text(100, 200, "Loading...", font, color565(255, 255, 255), color565(0, 0, 0), landscape=True)
    gotTime = False
    time = [0,0,0] #hms
    offsetUpdatedAt = 0
    offsetData = { "US": 0, "IN": 0, "SA": 0, "NZ": 0 }
    timeData = { "US": [-1,-1,-1], "IN": [-1,-1,-1], "SA": [-1,-1,-1], "NZ": [-1,-1,-1] }

    def __init__(self):
        pass


    def start(self):
        # High Speed SPI for drawing
        self.spi = SPI(1, baudrate=60000000, sck=Pin(7), mosi=Pin(11), miso=Pin(9))
        self.display = Display(self.spi, dc=Pin(12), cs=Pin(5), rst=Pin(0))
        self.display.clear(color565(0, 0, 0))
        self.display.draw_text(100, 200, "NTP Sync...", self.font, color565(255, 255, 255), color565(0, 0, 0), landscape=True)
        # load all the offsets from the prefs file
        self.loadOffsets()

    def loadOffsets(self):
        # load all the offsets from the prefs file
        self.offsetData["US"] = self.getPref("worldclock", "offset_US", 0)
        self.offsetData["IN"] = self.getPref("worldclock", "offset_IN", 0)
        self.offsetData["SA"] = self.getPref("worldclock", "offset_SA", 0)
        self.offsetData["NZ"] = self.getPref("worldclock", "offset_NZ", 0)

    def updateOffsets(self):
        # Get TZ offset for all 4 locations
        self.GetTzOffset("NZ", "Pacific/Auckland") # New Zealand
        self.GetTzOffset("US", "America/New_York") # US Eastern
        self.GetTzOffset("IN", "Asia/Kolkata") # India
        self.GetTzOffset("SA", "Africa/Johannesburg") # South Africa

    def GetTzOffset(self, name, tz):
        # Get the timezone information from online source using the timezone: 'https://www.timeapi.io/api/timezone/zone?timeZone=Pacific/Auckland'
        # and set the UTC_OFFSET based on the timezone information
        SerialLog.log("Getting timezone information for %s i.e. %s" % (name, tz))
        response = None
        try:
            import urequests as requests
            response = requests.get("https://www.timeapi.io/api/timezone/zone?timeZone=%s" % tz)
            if response.status_code == 200:
                data = response.json()
                # save this info to a file for later use
                self.offsetData[name] = data["currentUtcOffset"]["seconds"]
                self.setPref("worldclock", "offset_" + name, self.offsetData[name])
                SerialLog.log("Timezone information for %s: Current offset is %s seconds" % (name, data["currentUtcOffset"]["seconds"]))
            else:
                SerialLog.log("Error getting timezone information: %s" % response.status_code)
        except Exception as e:
            SerialLog.log("Error getting timezone information: %s" % str(e))
            if response:
                response.close()

    def tick(self):
        self.displayTime()

        # every 6 hours, update offsets
        if self.offsetUpdatedAt == 0 or time.ticks_diff(time.ticks_ms(), self.offsetUpdatedAt) > 21600000:
            self.offsetUpdatedAt = time.ticks_ms()
            self.updateOffsets()

    def displayTime(self, full = False):
        # Speed up SPI for drawing
        self.spi = SPI(1, baudrate=60000000, sck=Pin(7), mosi=Pin(11), miso=Pin(9))
        
        if (self.gotTime):
            # convert the string in self.time from ISO format to a list of integers
            timeNZ = list(map(int, self.time.split("T")[1].split(":")))

            secondsTimeUTC = timeNZ[0] * 3600 + timeNZ[1] * 60 + timeNZ[2] - self.offset # convert to utc seconds
            secondsTimeEST = secondsTimeUTC + self.offsetData["US"] # convert to est seconds
            secondsTimeIN = secondsTimeUTC + self.offsetData["IN"] # convert to in seconds
            secondsTimeSA = secondsTimeUTC + self.offsetData["SA"] # convert to sa seconds

            # convert the seconds to list of hms format and wrap hours using modulo 24
            timeEST = [(secondsTimeEST // 3600) % 24, (secondsTimeEST % 3600) // 60, secondsTimeEST % 60]
            timeIN = [(secondsTimeIN // 3600) % 24, (secondsTimeIN % 3600) // 60, secondsTimeIN % 60]
            timeSA = [(secondsTimeSA // 3600) % 24, (secondsTimeSA % 3600) // 60, secondsTimeSA % 60]
            
            self.drawTime("US", timeEST, top=5, left=40)
            self.drawTime("IN", timeIN, top=70, left=40)
            self.drawTime("SA", timeSA, top=135, left=40)
            self.drawTime("NZ", timeNZ, top=200, left=40)

    def drawTime(self, name, time, top, left):
        spacing = 65
        if self.timeData[name][0] != time[0]:
            self.drawNumber(time[0], top, left+spacing*2, self.timeData[name][0]) # hours

        if self.timeData[name][1] != time[1]:
            self.drawNumber(time[1], top, left+spacing, self.timeData[name][1]) # mins

        if self.timeData[name][2] != time[2]:
            self.drawNumber(time[2], top, left, self.timeData[name][2]) # seconds

        if self.timeData[name][0] == -1:
            self.display.draw_text(top-5, 260, name, self.font, color565(255, 255, 255), color565(0, 0, 0), landscape=True)
            self.display.draw_image('modules/worldclock/colon.raw',top,left+spacing*2-10,36,7)
            self.display.draw_image('modules/worldclock/colon.raw',top,left+spacing-10,36,7)

        # store the current time for this location
        self.timeData[name] = time

    # draws a decimal number
    def drawNumber(self, number, x, y, prevNumber):
        prevTens = (round(prevNumber) // 10) % 10
        tens = (round(number) // 10) % 10 
        prevOnes = round(prevNumber) % 10
        ones = round(number) % 10 

        if prevTens != tens or prevNumber == -1:
            self.display.draw_image('modules/worldclock/small'+str(tens)+'.raw',x,y+25,36,24)
        if prevOnes != ones or prevNumber == -1:
            self.display.draw_image('modules/worldclock/small'+str(ones)+'.raw',x,y,36,24)

    def getTelemetry(self):
        telemetry = {
        }
        return telemetry

    def processTelemetry(self, telemetry):
        if "offset" in telemetry:
            self.offset = telemetry["offset"]
        if "time" in telemetry:
            self.time = telemetry["time"]
            if not self.gotTime:
                self.display.clear(color565(0, 0, 0))
                self.gotTime = True
                self.displayTime(True)

    def getCommands(self):
        return []

    def processCommands(self, commands):
        for c in commands:
            if ("/touch" in c):
                self.displayTime(True)

    def getRoutes(self):
        return {
        }

    def getIndexFileName(self):
        return {  }

    # Internal code here
