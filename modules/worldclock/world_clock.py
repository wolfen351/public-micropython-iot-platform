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
    font = XglcdFont('modules/touchscreen/font25x57.c', 25, 57, 32, 97, 228)
    gotTime = False
    time = [0,0,0] #hms
    previous = [0,0,0] # hms
    hideDecimal = False
    bitdata = {}

    def __init__(self):
        pass


    def start(self):
        # High Speed SPI for drawing
        self.spi = SPI(1, baudrate=60000000, sck=Pin(7), mosi=Pin(11), miso=Pin(9))
        self.display = Display(self.spi, dc=Pin(12), cs=Pin(5), rst=Pin(0))
        self.display.clear(color565(0, 0, 0))

    def tick(self):
        if self.gotTime and (self.previous[0] != self.time[0] or self.previous[1] != self.time[1] or self.previous[2] != self.time[2]):
            self.displayTime()

    def displayTime(self, full = False):
        # Speed up SPI for drawing
        self.spi = SPI(1, baudrate=60000000, sck=Pin(7), mosi=Pin(11), miso=Pin(9))
        
        if (self.gotTime):
            # convert the string in self.time from ISO format to a list of integers
            localTime = list(map(int, self.time.split("T")[1].split(":")))
            spacing = 65
            leftspacing = 60
            if (self.previous[2] != localTime[2] or full == True):
                if (not self.hideDecimal):
                    self.drawNumber(localTime[2], 200, leftspacing, False) # seconds
            if (self.previous[1] != localTime[1] or full == True):
                if (not self.hideDecimal):
                    self.drawNumber(localTime[1], 200, leftspacing+spacing) # mins
            if (self.previous[0] != localTime[0] or full == True):
                if (not self.hideDecimal):
                    self.drawNumber(localTime[0], 200, leftspacing+spacing*2) # hours
            self.previous = localTime

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
