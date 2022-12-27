
from time import sleep
from modules.basic.basic_module import BasicModule
from modules.touchscreen.ili9341 import Display, color565
from modules.touchscreen.xglcd_font import XglcdFont
from machine import Pin, SPI
from modules.touchscreen.xpt2046 import Touch
from serial_log import SerialLog
import ntptime
import time

#if needed, overwrite default time server
ntptime.host = "0.nz.pool.ntp.org"

# Screen is 320x240 px
# X is left to right on the small side (0-240)
# Y is up to down on the long side (0-320)

class BinaryClock(BasicModule):

    spi = None
    display = None
    xpt = None
    font = XglcdFont('modules/touchscreen/fonts/font25x57.c', 25, 57, 32, 97, 228)
    mode = "OFF"
    detectedTemp = 23
    setpoint = 23

    #84f703d7c4b2 

    def __init__(self, basicSettings):
        pass


    def start(self):
        # High Speed SPI for drawing
        self.spi = SPI(1, baudrate=40000000, sck=Pin(7), mosi=Pin(11), miso=Pin(9))
        self.display = Display(self.spi, dc=Pin(12), cs=Pin(5), rst=Pin(0))
        self.display.clear(color565(0, 0, 0))

        # Low speed SPI for touch
        self.spi = SPI(1, baudrate=2000000, sck=Pin(7), mosi=Pin(11), miso=Pin(9))
        self.xpt = Touch(self.spi, cs=Pin(18))

        # Set up NTP
        try:
            SerialLog.log("Local time before synchronization：%s" %str(time.localtime()))
            #make sure to have internet connection
            ntptime.settime()
            SerialLog.log("Local time after synchronization：%s" %str(time.localtime()))
        except:
            SerialLog.log("Error syncing time")

    def tick(self):
        pass

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
