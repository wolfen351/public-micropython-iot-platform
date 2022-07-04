
from modules.basic.basic_module import BasicModule
from modules.touchscreen.ili9341 import Display, color565
from modules.touchscreen.xglcd_font import XglcdFont
from machine import Pin, SPI
from modules.touchscreen.xpt2046 import Touch

# Screen is 320x240 px
# X is left to right on the small side (0-240)
# Y is up to down on the long side (0-320)

class AcRemote(BasicModule):

    spi = None
    display = None
    xpt = None
    font = XglcdFont('modules/touchscreen/fonts/EspressoDolce18x24.c', 18, 24)

    def __init__(self, basicSettings):
        pass

    def start(self):
        # High Speed SPI for drawing
        self.spi = SPI(1, baudrate=100000000, sck=Pin(7), mosi=Pin(11), miso=Pin(9))
        self.display = Display(self.spi, dc=Pin(12), cs=Pin(5), rst=Pin(0))
        self.display.clear(color565(0, 0, 0))
        self.display.draw_rectangle(0,0,144,60,color565(255,255,0)) # Plus Button
        self.display.fill_rectangle(0,60,144,200,color565(0,0,255)) # Temp Section
        self.display.draw_rectangle(0,260,144,60,color565(255,255,0)) # Minus Button
        self.display.draw_rectangle(144,0,96,80,color565(70,70,70)) # Power Button
        self.display.draw_rectangle(144,80,96,80,color565(80,80,80)) # Heat Button
        self.display.draw_rectangle(144,160,96,80,color565(90,90,90)) # Dry Button
        self.display.draw_rectangle(144,240,96,80,color565(100,100,100)) # Cool Button

        self.display.fill_rectangle(65,270,15,40,color565(255,255,255)) # Minus
        self.display.fill_rectangle(65,10,15,40,color565(255,255,255)) # Plus Across
        self.display.fill_rectangle(52,22,40,15,color565(255,255,255)) # Plus Down

        self.display.draw_text(20, 240, "20*C", self.font, color565(255, 255, 255), background=color565(0, 0, 0), landscape=True)


        # Low speed SPI for touch
        self.spi = SPI(1, baudrate=2000000, sck=Pin(7), mosi=Pin(11), miso=Pin(9))
        self.xpt = Touch(self.spi, cs=Pin(18))
    
    def tick(self):
        t = self.xpt.get_rawtouch()
        if (t is not None):
            self.display.fill_circle(t[0], t[1], 10, color565(255,0,0))

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
