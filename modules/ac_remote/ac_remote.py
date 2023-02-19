
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

class AcRemote(BasicModule):

    spi = None
    display = None
    xpt = None
    font = XglcdFont('modules/touchscreen/font25x57.c', 25, 57, 32, 97, 228)
    mode = "OFF"
    detectedTemp = 23
    setpoint = 23

    #84f703d7c4b2 

    def __init__(self):
        pass

    def start(self):
        # High Speed SPI for drawing
        self.spi = SPI(1, baudrate=40000000, sck=Pin(7), mosi=Pin(11), miso=Pin(9))
        self.display = Display(self.spi, dc=Pin(12), cs=Pin(5), rst=Pin(0))
        self.display.clear(color565(0, 0, 0))
        self.display.draw_image('modules/ac_remote/backgroundsmall.raw',0,0,240,320)

        # Low speed SPI for touch
        self.spi = SPI(1, baudrate=2000000, sck=Pin(7), mosi=Pin(11), miso=Pin(9))
        self.xpt = Touch(self.spi, cs=Pin(18))

        self.draw_setpoint()
        self.draw_detectedTemp()

    def tick(self):
        t = self.xpt.get_rawtouch()
        if (t is not None):
            mul = 0
            #self.display.fill_circle(t[0], t[1], 10, color565(255,0,0))
            if t[0] > 144:
                if t[1] <= 80: # power
                    self.mode = "OFF"
                if t[1] > 80 and t[1] <= 160: # heat
                    self.mode = "HEAT"
                if t[1] > 160 and t[1] <= 240: # dry
                    self.mode = "DRY"
                if t[1] > 240: # cool
                    self.mode = "COOL"
                self.draw_mode()
            else:
                if t[1] < 60: # Temp -
                    self.setpoint = self.setpoint - 1
                    if self.setpoint < 10:
                        self.setpoint = 10
                if t[1] > 260: # Temp +
                    self.setpoint = self.setpoint + 1
                    if self.setpoint > 45:
                      self.setpoint = 45
                self.draw_setpoint()

    def getTelemetry(self):
        telemetry = {
            "ac_mode": self.mode,
            "ac_setpoint": self.setpoint
        }
        return telemetry

    def processTelemetry(self, telemetry):
        pass

    def getCommands(self):
        return []

    def processCommands(self, commands):
         for c in commands:
            # this decodes and executes home assistant/mqtt comands
            if (b"/current_temp/" in c):
                temp = float(c.rsplit(b'/', 1)[-1])
                self.detectedTemp = temp
                self.draw_detectedTemp()
            if (b"/ac_mode/" in c):
                mode = c.rsplit(b'/', 1)[-1]
                self.mode = mode
                self.draw_mode()
            if (b"/ac_setpoint/" in c):
                ac_setpoint = c.rsplit(b'/', 1)[-1]
                self.setpoint = ac_setpoint
                self.draw_setpoint()
    
    def getRoutes(self):
        return {
        }

    def getIndexFileName(self):
        return {  }

    # Internal code here

    def draw_mode(self):

        if self.mode == "OFF":
            mul = 0
        if self.mode == "HEAT":
            mul = 1
        if self.mode == "DRY":
            mul = 2
        if self.mode == "COOL":
            mul = 3

        # Clear existing
        self.display.draw_line(238,0,238,319,color565(0,0,0))
        self.display.draw_line(239,0,239,319,color565(0,0,0))
        # draw New
        self.display.draw_line(238,80*mul,238,79+80*mul,color565(0,255,0))
        self.display.draw_line(239,80*mul,239,79+80*mul,color565(0,255,0))

    def draw_setpoint(self):
        tens = (self.setpoint // 10) % 10 
        ones = self.setpoint % 10 
        self.spi = SPI(1, baudrate=40000000, sck=Pin(7), mosi=Pin(11), miso=Pin(9))
        self.display.draw_image('modules/ac_remote/small'+str(tens)+'.raw',105,170,36,24)
        self.display.draw_image('modules/ac_remote/small'+str(ones)+'.raw',105,145,36,24)
        self.spi = SPI(1, baudrate=2000000, sck=Pin(7), mosi=Pin(11), miso=Pin(9))

    def draw_detectedTemp(self):
        tens = (round(self.detectedTemp) // 10) % 10 
        ones = round(self.detectedTemp) % 10 
        self.spi = SPI(1, baudrate=40000000, sck=Pin(7), mosi=Pin(11), miso=Pin(9))
        self.display.draw_image('modules/ac_remote/big'+str(tens)+'.raw',20,200,72,47)
        self.display.draw_image('modules/ac_remote/big'+str(ones)+'.raw',20,153,72,47)
        self.spi = SPI(1, baudrate=2000000, sck=Pin(7), mosi=Pin(11), miso=Pin(9))
