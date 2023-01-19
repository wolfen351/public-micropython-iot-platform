from modules.basic.basic_module import BasicModule
import machine, neopixel, time
from modules.ledstrip.ledstrip_settings import LedStripSettings
from modules.web.web_processor import okayHeader, unquote
from serial_log import SerialLog
import ujson

class LedStripControl(BasicModule):

    primary = "000000"
    secondary = "000000"
    duration = 1000
    brightness = 255

    ACTION_NONE = 0
    ACTION_WHITE = 1
    ACTION_CLEAR = 2
    ACTION_SWITCH = 3
    ACTION_FADE = 4
    ACTION_CYCLE = 5
    ACTION_BOUNCE = 6
    ACTION_RAINBOW = 7
    ACTION_COLOR = 8

    ACTION_LOOKUP = { 
        b"none" : ACTION_NONE,
        b"white": ACTION_WHITE,
        b"clear": ACTION_CLEAR,
        b"switch": ACTION_SWITCH,
        b"fade": ACTION_FADE,
        b"cycle": ACTION_CYCLE,
        b"bounce": ACTION_BOUNCE,
        b"rainbow": ACTION_RAINBOW,
        b"color": ACTION_COLOR
    }   
    ACTION_TEXT_LOOKUP = {
        ACTION_NONE : b"none",
        ACTION_WHITE : b"white",
        ACTION_CLEAR : b"clear",
        ACTION_SWITCH : b"switch",
        ACTION_FADE : b"fade",
        ACTION_CYCLE : b"cycle",
        ACTION_BOUNCE : b"bounce",
        ACTION_RAINBOW : b"rainbow",
        ACTION_COLOR: b"color"
    }

    action = ACTION_NONE
    prevaction = ACTION_NONE

    def __init__(self):
        pass

    def start(self):
        BasicModule.start(self)

        ledStripSettings = LedStripSettings()
        ledStripSettings.load()
        self.action = ledStripSettings.ledAction
        self.primary = ledStripSettings.ledColorPrimary
        self.secondary = ledStripSettings.ledColorSecondary
        self.brightness = ledStripSettings.ledBrightness
        self.whiteOverride = False

        self.ledCount = self.basicSettings['led']['length']
        self.ledPin = self.basicSettings['led']['pin']

        self.np = neopixel.NeoPixel(machine.Pin(self.ledPin), self.ledCount)


    def tick(self):
        ms = time.ticks_ms()
        perc = (ms % self.duration) / self.duration

        if (self.whiteOverride):
            if (self.prevaction != self.ACTION_WHITE):
                self.maxwhite()
                self.prevaction = self.ACTION_WHITE
            return

        elif (self.action == self.ACTION_NONE and self.prevaction != self.ACTION_NONE):
            self.fullstrip(self.primary)
            self.prevaction = self.ACTION_NONE

        elif (self.action == self.ACTION_SWITCH):
            if (perc > 0.5):
                self.fullstrip(self.primary)
            else:
                self.fullstrip(self.secondary)

        elif (self.action == self.ACTION_FADE):
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

        elif (self.action == self.ACTION_CYCLE):

            p = self.applybrightness(self.hex_to_rgb(self.primary))
            s = self.applybrightness(self.hex_to_rgb(self.secondary))

            offset = int(perc * self.ledCount)
            for j in range(self.ledCount):
                self.np[j] = s
            self.np[offset % self.ledCount] = p
            self.np.write()

        elif (self.action == self.ACTION_BOUNCE):

            p = self.applybrightness(self.hex_to_rgb(self.primary))
            s = self.applybrightness(self.hex_to_rgb(self.secondary))

            offset = int(perc * self.ledCount * 2)
            for j in range(self.ledCount):
                self.np[j] = s
            if (offset > self.ledCount):
                offset = self.ledCount - (offset - self.ledCount)
            if (offset >= self.ledCount):
                offset = self.ledCount-1
            self.np[offset % self.ledCount] = p
            self.np.write()

        elif (self.action == self.ACTION_RAINBOW):

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
        try:
            p = self.hex_to_rgb(self.primary)
            s = self.hex_to_rgb(self.secondary)
            return { 
                "ledaction": self.ACTION_TEXT_LOOKUP[self.action],
                "ledprimary": self.primary,
                "ledprimaryr": p[0], 
                "ledprimaryg": p[1], 
                "ledprimaryb": p[2], 
                "ledsecondary": self.secondary,
                "ledsecondaryr": s[0], 
                "ledsecondaryg": s[1], 
                "ledsecondaryb": s[2], 
                "ledbrightness": self.brightness,
                "ledcolormode": "rgb",
                "ledstate": "ON" if self.brightness > 0 else "OFF"
            }
        except:
            return {}

    def processTelemetry(self, telemetry):
        pass

    def getCommands(self):
        return []

    def processCommands(self, commands):
        for c in commands:
            # this decodes and executes home assistant comands
            if (b"/ledprimary/" in c):
                command = c.rsplit(b'/', 1)[-1]
                bits = ujson.loads(command)
                for cc in bits:
                    val = bits[cc]
                    if (cc=="state"):
                        if (val == "OFF"):
                            self.setbrightness(0)
                    elif (cc == "brightness"):
                        self.setbrightness(int(val))
                    elif (cc == "color"):
                        newSecondary = self.rgb_to_hex(val["r"], val["g"], val["b"])
                        self.setcolor(newSecondary, self.secondary)
                    elif (cc == "effect"):
                        self.setaction(bytes(val, 'ascii'))
            if (b"/ledsecondary/" in c):
                command = c.rsplit(b'/', 1)[-1]
                bits = ujson.loads(command)
                for cc in bits:
                    val = bits[cc]
                    if (cc=="state"):
                        if (val == "OFF"):
                            self.setbrightness(0)
                    elif (cc == "brightness"):
                        self.setbrightness(int(val))
                    elif (cc == "color"):
                        newSecondary = self.rgb_to_hex(val["r"], val["g"], val["b"])
                        self.setcolor(self.primary, newSecondary)
                    elif (cc == "effect"):
                        self.setaction(bytes(val, 'ascii'))                    
            if (b"/button/onboard/1" in c):
                SerialLog.log("WHITE COMMAND")
                self.whiteOverride = not self.whiteOverride
                self.prevaction = self.ACTION_CLEAR

    def getRoutes(self):
        return { 
            b"/led/color" : self.ledcolor,
            b"/led/action" : self.ledaction,
            b"/led/brightness" : self.ledbrightness,
            b"/ledstrip" : b"/modules/ledstrip/ledstrip.html"
        }

    def getIndexFileName(self):
        return { "ledstrip" : "/modules/ledstrip/ledstrip_index.html" }


    # private methods

    def hex_to_rgb(self, value):
        lv = len(value)
        t1 = tuple(int(value[i:i + lv // 3], 16) for i in range(0, lv, lv // 3))
        return (t1[0], t1[1], t1[2])

    def rgb_to_hex(self, r, g, b):
        return ''.join('%02x'%i for i in (r,g,b))
    
    def setcolor(self, primary, secondary):
        self.primary = primary
        self.secondary = secondary
        self.prevaction = self.ACTION_COLOR
        self.saveSettings()

    def setaction(self, actionText):

        newAction = self.ACTION_LOOKUP[actionText]
        
        self.prevaction = self.action
        self.action = newAction

        self.saveSettings()

    def setbrightness(self, brightness):
        self.brightness = brightness
        self.prevaction = b"brightness"
        self.saveSettings()

    def saveSettings(self):
        settings = LedStripSettings(self.action, self.primary, self.secondary, self.brightness)
        settings.write()

    def maxwhite(self):
        for i in range(self.ledCount):
            self.np[i] = self.hex_to_rgb("ffffff")
        self.np.write()

    def fullstrip(self, color):
        col = self.applybrightness(self.hex_to_rgb(color))
        for i in range(self.ledCount):
            self.np[i] = col
        self.np.write()

    def fullstrip_tuple(self, color):
        col = self.applybrightness(color)
        for i in range(self.ledCount):
            self.np[i] = col
        self.np.write()

    def applybrightness(self, color):
        handicap = self.brightness / 255.0
        t1 = (int(color[0] * handicap), int(color[1] * handicap), int(color[2] * handicap))
        return (t1[0], t1[1], t1[2])

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

    def ledbrightness(self, params):
        headers = okayHeader
        brightness = int(unquote(params.get(b"brightness", None)))
        self.prevaction = b'brightness'
        self.setbrightness(brightness)
        return b"", headers