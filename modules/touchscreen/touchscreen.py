
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

    def __init__(self, basicSettings):
        pass

    def start(self):
        self.spi = SPI(1, baudrate=100000000, sck=Pin(7), mosi=Pin(11), miso=Pin(9))
        self.display = Display(self.spi, dc=Pin(12), cs=Pin(5), rst=Pin(0))
        self.display.clear(color565(64, 0, 255))

        # Low speed SPI for touch
        self.spi = SPI(1, baudrate=2000000, sck=Pin(7), mosi=Pin(11), miso=Pin(9))
        self.xpt = Touch(self.spi, cs=Pin(18))
    
    def tick(self):
        t = self.xpt.get_touch()
        if (t is not None):
            self.display.draw_text(40, 40, str(t), self.robotron, color565(255, 255, 255), background=color565(64, 0, 255))

    def getTelemetry(self):
        telemetry = {}
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
