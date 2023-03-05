
import time
from modules.basic.basic_module import BasicModule
from modules.touchscreen.ili9341 import Display, color565
from modules.touchscreen.xglcd_font import XglcdFont
from machine import Pin, SPI
from modules.touchscreen.xpt2046 import Touch

class TouchScreen(BasicModule):

    spi = None
    display = None
    xpt = None
    robotron = XglcdFont('modules/touchscreen/ArcadePix9x11.c', 9, 11)
    lastTouch = None
    lastTouchAt = 0

    def __init__(self):
        pass

    def start(self):
        self.spi = SPI(1, baudrate=100000000, sck=Pin(7), mosi=Pin(11), miso=Pin(9))
        self.display = Display(self.spi, dc=Pin(12), cs=Pin(5), rst=Pin(0))

        # Low speed SPI for touch
        self.spi = SPI(1, baudrate=2000000, sck=Pin(7), mosi=Pin(11), miso=Pin(9))
        self.xpt = Touch(self.spi, cs=Pin(18))

        lastTouchAt = time.ticks_ms()

    
    def tick(self):
        currentTime = time.ticks_ms()
        diff = time.ticks_diff(currentTime, self.lastTouchAt)
        self.lastTouch = None
        if (diff > 200):
            # Slow down SPI for touch
            self.spi = SPI(1, baudrate=2000000, sck=Pin(7), mosi=Pin(11), miso=Pin(9))
            t = self.xpt.get_rawtouch()
            self.lastTouch = t

    def getTelemetry(self):
        telemetry = {}
        if (self.lastTouch != None):
            telemetry = { "touch", self.lastTouch }
        return telemetry

    def processTelemetry(self, telemetry):
        pass

    def getCommands(self):
        if (self.lastTouch != None):
            return [b"/touch/0/0"]
        return []

    def processCommands(self, commands):
        pass

    def getRoutes(self):
        return {
        }

    def getIndexFileName(self):
        return {  }

    # Internal code here
