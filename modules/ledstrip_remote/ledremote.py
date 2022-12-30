
from math import floor
from time import sleep
from modules.basic.basic_module import BasicModule
from modules.touchscreen.ili9341 import Display, color565
from modules.touchscreen.xglcd_font import XglcdFont
from machine import Pin, SPI
from modules.touchscreen.xpt2046 import Touch
from serial_log import SerialLog

# Screen is 320x240 px
# X is left to right on the small side (0-240)
# Y is up to down on the long side (0-320)

class LedRemote(BasicModule):

    spi = None
    display = None
    xpt = None

    color = color565(0,0,0)
    colorRGB = "000000"
    brightness = 50
    commands = []

    def __init__(self):
        pass

    def start(self):
        # High Speed SPI for drawing
        self.spi = SPI(1, baudrate=40000000, sck=Pin(7), mosi=Pin(11), miso=Pin(9))
        self.display = Display(self.spi, dc=Pin(12), cs=Pin(5), rst=Pin(0))
        self.display.draw_image('modules/ledstrip_remote/backgroundsmall.raw',0,0,240,320)

        # Low speed SPI for touch
        self.spi = SPI(1, baudrate=2000000, sck=Pin(7), mosi=Pin(11), miso=Pin(9))
        self.xpt = Touch(self.spi, cs=Pin(18))

    def tick(self):
        t = self.xpt.get_rawtouch()
        if (t is not None):
            column = floor(t[0] / 60) + 1
            row = floor(t[1] / 53) + 1

            if (row == 1):
                if (column == 1):   # brighter
                    self.brightness = self.brightness + 1
                    if (self.brightness > 100):
                        self.brightness = 100
                elif (column == 2): # dimmer
                    self.brightness = self.brightness - 1
                    if (self.brightness < 0):
                        self.brightness = 0
                elif (column == 3): # off
                    self.brightness = 0
                elif (column == 4): # on
                    self.brightness = 100
            elif (row == 2):
                if (column == 1):   # red
                    self.color = self.setcolor(255,0,0)
                elif (column == 2): # green
                    self.color = self.setcolor(0,255,0)
                elif (column == 3): # blue
                    self.color = self.setcolor(0,0,255)
                elif (column == 4): # white
                    self.color = self.setcolor(255,255,255)
            elif (row == 3):
                if (column == 1):   # brightorange
                    self.color = self.setcolor(255,127,80)
                elif (column == 2): # brightgreen
                    self.color = self.setcolor(144,238,144)
                elif (column == 3): # brightblue
                    self.color = self.setcolor(30,144,255)
                elif (column == 4): # white
                    self.color = self.setcolor(255,255,255)
            elif (row == 4):
                if (column == 1):   # darkorange
                    self.color = self.setcolor(255,140,0)
                elif (column == 2): # lightblue
                    self.color = self.setcolor(135,206,250)
                elif (column == 3): # darkpurple
                    self.color = self.setcolor(75,0,130)
                elif (column == 4): # strobe
                    pass
            elif (row == 5):
                if (column == 1):   # orange
                    self.color = self.setcolor(255,165,0)
                elif (column == 2): # lightblue
                    self.color = self.setcolor(0,191,255)
                elif (column == 3): # purple
                    self.color = self.setcolor(138,43,226)
                elif (column == 4): # fade
                    pass
            elif (row == 6):
                if (column == 1):   # yellow
                    self.color = self.setcolor(255,255,0)
                elif (column == 2): # blue
                    self.color = self.setcolor(65,105,225)
                elif (column == 3): # pink
                    self.color = self.setcolor(255,20,147)
                elif (column == 4): # smooth
                    pass

    def getTelemetry(self):
        telemetry = {
            "colorRGB": self.colorRGB,
            "brightness": self.brightness,
        }
        return telemetry

    def processTelemetry(self, telemetry):
        pass

    def getCommands(self):
        c = self.commands
        self.commands = []
        return c

    def processCommands(self, commands):
        pass
    
    def getRoutes(self):
        return {
        }

    def getIndexFileName(self):
        return {  }

    # Internal code here

    def setcolor(self, r,g,b):
        self.colorRGB = str(r)+","+str(g)+","+str(b)
        return color565(r,g,b)

