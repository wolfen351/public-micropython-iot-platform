from time import sleep
from modules.basic.basic_module import BasicModule
from modules.touchscreen.ili9341 import Display, color565
from modules.touchscreen.xglcd_font import XglcdFont
from machine import Pin, SPI
from modules.touchscreen.xpt2046 import Touch
from serial_log import SerialLog
import ntptime
import time
import network

# Screen is 320x240 px
# X is left to right on the small side (0-240)
# Y is up to down on the long side (0-320)

class BinaryClock(BasicModule):

    spi = None
    display = None
    xpt = None
    font = XglcdFont('modules/touchscreen/fonts/font25x57.c', 25, 57, 32, 97, 228)
    gotTime = False
    ntptime.host = "0.nz.pool.ntp.org"
    UTC_BASE_OFFSET = 12 * 60 * 60
    UTC_OFFSET = 12 * 60 * 60
    previous = [-1,-1,-1,-1,-1,-1,-1]

    def __init__(self, basicSettings):
        pass


    def start(self):
        # High Speed SPI for drawing
        self.spi = SPI(1, baudrate=40000000, sck=Pin(7), mosi=Pin(11), miso=Pin(9))
        self.display = Display(self.spi, dc=Pin(12), cs=Pin(5), rst=Pin(0))
        self.display.clear(color565(0, 0, 0))
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

        self.displayTime()

    def displayTime(self):
        localTime = time.localtime(time.time() + self.UTC_OFFSET)
        spacing = 65
        leftspacing = 60
        if (self.previous[5] != localTime[5]):
            self.drawNumber(localTime[5], 200, leftspacing, False) # seconds
            self.drawBinary(localTime[5], 0, 10)
        if (self.previous[4] != localTime[4]):
            self.drawNumber(localTime[4], 200, leftspacing+spacing) # mins
        if (self.previous[3] != localTime[3]):
            self.drawNumber(localTime[3], 200, leftspacing+spacing*2) # hours
        self.previous = localTime

    def drawNumber(self, number, x, y, showColon = True):
        tens = (round(number) // 10) % 10 
        ones = round(number) % 10 
        if showColon:
            self.display.draw_image('modules/binary_clock/colon.raw',x,y-10,36,7)
        self.display.draw_image('modules/binary_clock/small'+str(tens)+'.raw',x,y+25,36,24)
        self.display.draw_image('modules/binary_clock/small'+str(ones)+'.raw',x,y,36,24)

    def drawBinary(self, number, x, y):
        ones = round(number) % 2 
        twos = round(number) % 4 
        fours = round(number) % 8 
        eights = round(number) % 16
        self.drawBit(eights, x+10, y)
        self.drawBit(fours, x+50, y)
        self.drawBit(twos, x+90, y) 
        self.drawBit(ones, x+130, y)

    def drawBit(self, bitValue, x, y):
        if (bitValue == 1):
            self.display.draw_image('modules/binary_clock/on.raw', x, y, 49, 46)
        else:
            self.display.draw_image('modules/binary_clock/off.raw', x, y, 49, 46)


    def getTelemetry(self):
        telemetry = {
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
