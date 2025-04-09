from modules.basic.basic_module import BasicModule
from modules.touchscreen.ili9341 import Display, color565
from modules.touchscreen.xglcd_font import XglcdFont
from machine import Pin, SPI
from serial_log import SerialLog

# Screen is 320x240 px
# X is left to right on the small side (0-240)
# Y is up to down on the long side (0-320)

class WorldClock(BasicModule):

    spi = None
    display = None
    xpt = None
    # path, width, height, start_letter=32, letter_count=96, bytes_per_letter=0
    #font = XglcdFont('modules/touchscreen/font25x57.c', 25, 57, 32, 97, 228)
    font = XglcdFont('modules/touchscreen/Roboto_18x22.c', 18, 22)
    gotTime = False
    time = [0,0,0] #hms
    previous = [0,0,0] # hms
    hideDecimal = False
    offsetData = {}
    timeData = { "US": [0,0,0], "IN": [0,0,0], "SA": [0,0,0], "NZ": [0,0,0] }

    def __init__(self):
        pass


    def start(self):
        # High Speed SPI for drawing
        self.spi = SPI(1, baudrate=60000000, sck=Pin(7), mosi=Pin(11), miso=Pin(9))
        self.display = Display(self.spi, dc=Pin(12), cs=Pin(5), rst=Pin(0))
        self.display.clear(color565(0, 0, 0))

        # Get TZ offset for all 4 locations
        self.GetTzOffset("NZ", "Pacific/Auckland") # New Zealand
        self.GetTzOffset("EST", "America/New_York") # US Eastern
        self.GetTzOffset("IN", "Asia/Kolkata") # India
        self.GetTzOffset("SA", "Africa/Johannesburg") # South Africa

    def GetTzOffset(self, name, tz):
        # Get the timezone information from online source using the timezone: 'https://www.timeapi.io/api/timezone/zone?timeZone=Pacific/Auckland'
        # and set the UTC_OFFSET based on the timezone information
        response = None
        try:
            import urequests as requests
            response = requests.get("https://www.timeapi.io/api/timezone/zone?timeZone=%s" % tz)
            if response.status_code == 200:
                data = response.json()
                # save this info to a file for later use
                self.offsetData[name] = data["currentUtcOffset"]["seconds"]
            else:
                SerialLog.log("Error getting timezone information: %s" % response.status_code)
        except Exception as e:
            SerialLog.log("Error getting timezone information: %s" % str(e))
            if response:
                response.close()

    def tick(self):
        if self.gotTime and (self.previous[0] != self.time[0] or self.previous[1] != self.time[1] or self.previous[2] != self.time[2]):
            self.displayTime()

    def displayTime(self, full = False):
        # Speed up SPI for drawing
        self.spi = SPI(1, baudrate=60000000, sck=Pin(7), mosi=Pin(11), miso=Pin(9))
        
        if (self.gotTime):
            # convert the string in self.time from ISO format to a list of integers
            timeNZ = list(map(int, self.time.split("T")[1].split(":")))

            secondsTimeUTC = timeNZ[0] * 3600 + timeNZ[1] * 60 + timeNZ[2] - self.offset # convert to utc seconds
            secondsTimeEST = secondsTimeUTC + self.offsetData["EST"] # convert to est seconds
            secondsTimeIN = secondsTimeUTC + self.offsetData["IN"] # convert to in seconds
            secondsTimeSA = secondsTimeUTC + self.offsetData["SA"] # convert to sa seconds

            # convert the seconds to list of hms format and wrap hours using modulo 24
            timeEST = [(secondsTimeEST // 3600) % 24, (secondsTimeEST % 3600) // 60, secondsTimeEST % 60]
            timeIN = [(secondsTimeIN // 3600) % 24, (secondsTimeIN % 3600) // 60, secondsTimeIN % 60]
            timeSA = [(secondsTimeSA // 3600) % 24, (secondsTimeSA % 3600) // 60, secondsTimeSA % 60]
            timeNZ = [(secondsTimeUTC // 3600) % 24, (secondsTimeUTC % 3600) // 60, secondsTimeUTC % 60]
            
            self.drawTime("US", timeEST, top=5, left=40)
            self.drawTime("IN", timeIN, top=70, left=40)
            self.drawTime("SA", timeSA, top=135, left=40)
            self.drawTime("NZ", timeNZ, top=200, left=40)
            self.display.draw_text(0, 260, "US", self.font, color565(255, 255, 255), color565(0, 0, 0), landscape=True)
            self.display.draw_text(65, 260, "IN", self.font, color565(255, 255, 255), color565(0, 0, 0), landscape=True)
            self.display.draw_text(130, 260, "SA", self.font, color565(255, 255, 255), color565(0, 0, 0), landscape=True)
            self.display.draw_text(195, 260, "NZ", self.font, color565(255, 255, 255), color565(0, 0, 0), landscape=True)

    def drawTime(self, name, time, top, left):
        spacing = 65
        if self.timeData[name][0] != time[0]:
            self.drawNumber(time[0], top, left+spacing*2) # hours

        if self.timeData[name][1] != time[1]:
            self.drawNumber(time[1], top, left+spacing) # mins

        if self.timeData[name][2] != time[2]:
            self.drawNumber(time[2], top, left, False) # seconds

        # store the current time for this location
        self.timeData[name] = time

    # draws a decimal number
    def drawNumber(self, number, x, y, showColon = True):
        tens = (round(number) // 10) % 10 
        ones = round(number) % 10 
        if showColon:
            self.display.draw_image('modules/worldclock/colon.raw',x,y-10,36,7)
        self.display.draw_image('modules/worldclock/small'+str(tens)+'.raw',x,y+25,36,24)
        self.display.draw_image('modules/worldclock/small'+str(ones)+'.raw',x,y,36,24)

    def getTelemetry(self):
        telemetry = {
        }
        return telemetry

    def processTelemetry(self, telemetry):
        if "offset" in telemetry:
            self.offset = telemetry["offset"]
        if ("time" in telemetry):
            self.time = telemetry["time"]
            if not self.gotTime:
                self.gotTime = True
                self.displayTime(True)

    def getCommands(self):
        return []

    def processCommands(self, commands):
        for c in commands:
            if ("/touch" in c):
                self.display.clear(color565(0, 0, 0))                
                self.hideDecimal = not self.hideDecimal
                self.displayTime(True)

    def getRoutes(self):
        return {
        }

    def getIndexFileName(self):
        return {  }

    # Internal code here
