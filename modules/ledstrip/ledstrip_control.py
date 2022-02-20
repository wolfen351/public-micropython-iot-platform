from modules.basic.basic_module import BasicModule
import machine, neopixel, time
from modules.ledstrip.ledstrip_settings import LedStripSettings
from modules.web.web_processor import okayHeader, unquote

class LedStripControl(BasicModule):

    ledCount = 120
    np = neopixel.NeoPixel(machine.Pin(16), ledCount)
    action = b"none"
    prevaction = b"unset"
    primary = "000000"
    secondary = "000000"
    duration = 5000

    def __init__(self, basicSettings):
        pass

    def start(self):
        ledStripSettings = LedStripSettings()
        ledStripSettings.load()
        self.action = ledStripSettings.ledAction
        self.primary = ledStripSettings.ledColorPrimary
        self.secondary = ledStripSettings.ledColorSecondary

    def tick(self):
        ms = time.ticks_ms()
        perc = (ms % self.duration) / self.duration

        if (self.action == b"none" and self.prevaction != b"none"):
            self.fullstrip(self.primary)
            self.prevaction = b"none"

        if (self.action == b"switch"):
            if (perc > 0.5):
                self.fullstrip(self.primary)
            else:
                self.fullstrip(self.secondary)

        if (self.action == b"fade"):
            p = self.hex_to_rgb(self.primary)
            s = self.hex_to_rgb(self.secondary)

            if (perc < 0.5):
                calcR = int(p[0] + (s[0] - p[0]) * perc*2)
                calcG = int(p[1] + (s[1] - p[1]) * perc*2)
                calcB = int(p[2] + (s[2] - p[2]) * perc*2)
            else:
                perc = perc - 0.5
                calcR = int(s[0] + (p[0] - s[0]) * perc*2)
                calcG = int(s[1] + (p[1] - s[1]) * perc*2)
                calcB = int(s[2] + (p[2] - s[2]) * perc*2)

            col = (calcR, calcG, calcB)
            self.fullstrip_tuple(col)

        if (self.action == b"cycle"):

            p = self.hex_to_rgb(self.primary)
            s = self.hex_to_rgb(self.secondary)

            offset = int(perc * self.ledCount)
            for j in range(self.ledCount):
                self.np[j] = s
            self.np[offset % self.ledCount] = p
            self.np.write()

        if (self.action == b"bounce"):

            p = self.hex_to_rgb(self.primary)
            s = self.hex_to_rgb(self.secondary)

            offset = int(perc * self.ledCount * 2)
            for j in range(self.ledCount):
                self.np[j] = s
            if (offset > self.ledCount):
                offset = self.ledCount - (offset - self.ledCount)
            if (offset >= self.ledCount):
                offset = self.ledCount-1
            self.np[offset % self.ledCount] = p
            self.np.write()

        if (self.action == b"rainbow"):

            offset = int(perc * self.ledCount)

            third = int(self.ledCount // 3);

            for led in range(self.ledCount):
                r=0
                b=0
                g=0

                # r 0-255 g 0 b 255-0
                if (led >= 0 and led < third):
                    inThird = led
                    b = 255 - int(inThird / third * 255)
                    r = int(inThird / third * 255)
                # r 255-0 g 0-255 b 0
                if (led >= third and led <= 2*third):
                    inThird = led - third
                    r = 255 - int(inThird / third * 255)
                    g = int(inThird / third * 255)
                # r 0 g 255-0 b 0-255
                if (led >= third*2 and led <= 3*third):
                    inThird = led - third*2
                    g = 255 - int(inThird / third * 255)
                    b = int(inThird / third * 255)

                p = (led + offset) % self.ledCount

                self.np[p] = (r,g,b)
            self.np.write()


    def getTelemetry(self):
        return { 
            "ledaction": self.action,
            "ledprimary": self.primary,
            "ledsecondary": self.secondary
        }

    def processTelemetry(self, telemetry):
        pass

    def getCommands(self):
        return []

    def processCommands(self, commands):
        pass

    def getRoutes(self):
        return { 
            b"/led/color" : self.ledcolor,
            b"/led/action" : self.ledaction,
            b"/ledstrip" : b"/modules/ledstrip/ledstrip.html"
        }

    def getIndexFileName(self):
        return { "ledstrip" : "/modules/ledstrip/ledstrip_index.html" }


    # private methods

    def hex_to_rgb(self, value):
        lv = len(value)
        t1 = tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
        return (t1[0], t1[1], t1[2])
    
    def setcolor(self, primary, secondary):
        self.primary = primary
        self.secondary = secondary
        self.prevaction = b"color"
        self.saveSettings()

    def setaction(self, action):
        self.prevaction = self.action
        self.action = action
        self.saveSettings()

    def saveSettings(self):
        settings = LedStripSettings(self.action, self.primary, self.secondary)
        settings.write()

    def fullstrip(self, color):
        for i in range(self.ledCount):
            self.np[i] = self.hex_to_rgb(color)
        self.np.write()

    def fullstrip_tuple(self, color):
        for i in range(self.ledCount):
            self.np[i] = color
        self.np.write()

    def ledcolor(self, params):
        headers = okayHeader
        primary = unquote(params.get(b"primary", None))
        secondary = unquote(params.get(b"secondary", None))
        self.setcolor(primary, secondary)
        return b"", headers

    def ledaction(self, params):
        headers = okayHeader
        action = unquote(params.get(b"action", None))
        self.setaction(action)
        return b"", headers