from modules.basic.basic_module import BasicModule
import machine, neopixel, time
from modules.web.web_processor import okayHeader, unquote
from serial_log import SerialLog
import ujson

class LedStripControl(BasicModule):

    primaryColorHexString = b"000000"
    secondaryColorHexString = b"000000"
    primaryColorTuple = (0,0,0)
    secondaryColorTuple = (0,0,0)
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
    ACTION_BRIGHTNESS = 9

    ACTION_LOOKUP = { 
        b"none" : ACTION_NONE,
        b"white": ACTION_WHITE,
        b"clear": ACTION_CLEAR,
        b"switch": ACTION_SWITCH,
        b"fade": ACTION_FADE,
        b"cycle": ACTION_CYCLE,
        b"bounce": ACTION_BOUNCE,
        b"rainbow": ACTION_RAINBOW,
        b"color": ACTION_COLOR,
        b"brightness": ACTION_BRIGHTNESS
    }   
    ACTION_TEXT_LOOKUP = {v: k for k, v in ACTION_LOOKUP.items()}

    action = ACTION_NONE
    prevaction = ACTION_NONE
    previousAnimationPercentage = 0
    rainbow = [primaryColorTuple] * 0

    def __init__(self):
        pass

    def start(self):
        BasicModule.start(self)

        self.action = self.getPref("ledStrip", "action", self.ACTION_NONE)
        
        self.primaryColorHexString = self.getPref("ledStrip", "primary", b"000000")
        self.primaryColorTuple = self.hexStringToRgbTuple(self.primaryColorHexString)

        self.secondaryColorHexString = self.getPref("ledStrip", "secondary", b"000000")
        self.secondaryColorTuple = self.hexStringToRgbTuple(self.secondaryColorHexString)

        self.brightness = self.getPref("ledStrip", "brightness", 255)
        self.duration = self.getPref("ledStrip", "duration", 1000) 
        self.whiteOverride = False

        self.ledCount = self.basicSettings['led']['length']
        self.ledPin = self.basicSettings['led']['pin']

        self.neoPixel = neopixel.NeoPixel(machine.Pin(self.ledPin), self.ledCount)
        self.calculateRainbow()

    def tick(self):
        ms = time.ticks_ms()
        animationPercentage = (ms % self.duration) / self.duration

        if (self.whiteOverride):
            if (self.prevaction != self.ACTION_WHITE):
                self.maxwhite()
                self.prevaction = self.ACTION_WHITE
            return
        elif (self.action == self.ACTION_NONE and self.prevaction != self.ACTION_NONE):
            self.fullstrip_tuple(self.primaryColorTuple)
            self.prevaction = self.ACTION_NONE

        elif (self.action == self.ACTION_SWITCH):
            if (animationPercentage > 0.5 and self.previousAnimationPercentage < 0.5):
                self.fullstrip_tuple(self.primaryColorTuple)
            elif (animationPercentage < 0.5 and self.previousAnimationPercentage > 0.5):
                self.fullstrip_tuple(self.secondaryColorTuple)

        elif (self.action == self.ACTION_FADE):
            p = self.primaryColorTuple
            s = self.secondaryColorTuple

            if (animationPercentage < 0.5):
                calcR = int(p[0] + (s[0] - p[0]) * animationPercentage*2)
                calcG = int(p[1] + (s[1] - p[1]) * animationPercentage*2)
                calcB = int(p[2] + (s[2] - p[2]) * animationPercentage*2)
            else:
                animationPercentage = animationPercentage - 0.5
                calcR = int(s[0] + (p[0] - s[0]) * animationPercentage*2)
                calcG = int(s[1] + (p[1] - s[1]) * animationPercentage*2)
                calcB = int(s[2] + (p[2] - s[2]) * animationPercentage*2)

            col = (calcR, calcG, calcB)
            self.fullstrip_tuple(col)

        elif (self.action == self.ACTION_CYCLE):

            p = self.applybrightness(self.primaryColorTuple)
            s = self.applybrightness(self.secondaryColorTuple)

            offset = int(animationPercentage * self.ledCount)
            self.neoPixel.fill(s)
            self.neoPixel[offset % self.ledCount] = p
            self.neoPixel.write()

        elif (self.action == self.ACTION_BOUNCE):

            p = self.applybrightness(self.primaryColorTuple)
            s = self.applybrightness(self.secondaryColorTuple)

            offset = int(animationPercentage * self.ledCount * 2)
            self.neoPixel.fill(s)
            if (offset > self.ledCount):
                offset = self.ledCount - (offset - self.ledCount)
            if (offset >= self.ledCount):
                offset = self.ledCount-1
            self.neoPixel[offset % self.ledCount] = p
            self.neoPixel.write()

        elif (self.action == self.ACTION_RAINBOW):
            offset = int(animationPercentage * self.ledCount)
            
            for i in range(self.ledCount):
                self.neoPixel[i] = self.rainbow[(i + offset) % self.ledCount]
            self.neoPixel.write()

        self.previousAnimationPercentage = animationPercentage


    def getTelemetry(self):
        try:
            p = self.hexStringToRgbTuple(self.primaryColorHexString)
            s = self.hexStringToRgbTuple(self.secondaryColorHexString)
            return { 
                "ledaction": self.ACTION_TEXT_LOOKUP[self.action],
                "ledprimary": self.primaryColorHexString,
                "ledprimaryr": p[0], 
                "ledprimaryg": p[1], 
                "ledprimaryb": p[2], 
                "ledsecondary": self.secondaryColorHexString,
                "ledsecondaryr": s[0], 
                "ledsecondaryg": s[1], 
                "ledsecondaryb": s[2], 
                "ledbrightness": self.brightness,
                "ledduration": self.duration,
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
                        newSecondary = self.rgbValuesToHexString(val["r"], val["g"], val["b"])
                        self.setcolor(newSecondary, self.secondaryColorHexString)
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
                        newSecondary = self.rgbValuesToHexString(val["r"], val["g"], val["b"])
                        self.setcolor(self.primaryColorHexString, newSecondary)
                    elif (cc == "effect"):
                        self.setaction(bytes(val, 'ascii'))                    
            if (b"/button/onboard/1" in c):
                SerialLog.log("WHITE COMMAND")
                self.whiteOverride = not self.whiteOverride
                self.prevaction = self.ACTION_CLEAR

    def getRoutes(self):
        return { 
            b"/led/color" : self.webSetColours,
            b"/led/action" : self.webSetAction,
            b"/led/brightness" : self.webSetBrightness,
            b"/led/duration" : self.webSetDuration,
            b"/ledstrip" : b"/modules/ledstrip/settings.html"
        }

    def getIndexFileName(self):
        return { "ledstrip" : "/modules/ledstrip/index.html" }


    # private methods

    def calculateRainbow(self):
        # allocate space for the rainbow
        self.rainbow = [self.primaryColorTuple] * self.ledCount
        third = int(self.ledCount // 3);
        for led in range(self.ledCount):
            r=0
            b=0
            g=0
            # r 0-255 g 0 b 255-0
            if (led >= 0 and led <= third):
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
            self.rainbow[led] = self.applybrightness((r,g,b))
        self.rainbow[self.ledCount - 1] = self.applybrightness((0,0,255))

    def hexStringToRgbTuple(self, hexColorString):
        return (int(hexColorString[0:2], 16), int(hexColorString[2:4], 16), int(hexColorString[4:6], 16))

    def rgbValuesToHexString(self, r, g, b):
        return ''.join('%02x'%i for i in (r,g,b))
    
    def setcolor(self, primaryColorHexString, secondaryColorHexString):
        self.primaryColorHexString = primaryColorHexString
        self.primaryColorTuple = self.hexStringToRgbTuple(self.primaryColorHexString)
        self.secondaryColorHexString = secondaryColorHexString
        self.secondaryColorTuple = self.hexStringToRgbTuple(self.secondaryColorHexString)
        self.prevaction = self.ACTION_COLOR
        self.saveSettings()

    def setaction(self, actionText):
        newAction = self.ACTION_LOOKUP[actionText]
        self.prevaction = self.action
        self.action = newAction
        self.saveSettings()

    def setbrightness(self, brightness):
        self.brightness = brightness
        self.prevaction = self.ACTION_BRIGHTNESS
        self.saveSettings()
        self.calculateRainbow()

    def setduration(self, duration):
        if (duration <= 0):
            duration = 32
        self.duration = duration
        self.prevaction = self.ACTION_NONE
        self.saveSettings()

    def saveSettings(self):
        self.setPref("ledStrip", "action", self.action)
        self.setPref("ledStrip", "primary", self.primaryColorHexString)
        self.setPref("ledStrip", "secondary", self.secondaryColorHexString)
        self.setPref("ledStrip", "brightness", self.brightness)
        self.setPref("ledStrip", "duration", self.duration)

    def maxwhite(self):
        self.neoPixel.fill((255,255,255))
        self.neoPixel.write()

    def fullstrip(self, hexColorString):
        col = self.applybrightness(self.hexStringToRgbTuple(hexColorString))
        self.neoPixel.fill(col)
        self.neoPixel.write()

    def fullstrip_tuple(self, colourTuple):
        col = self.applybrightness(colourTuple)
        self.neoPixel.fill(col)
        self.neoPixel.write()

    def applybrightness(self, colorTuple):
        handicap = self.brightness / 255.0
        t1 = (int(colorTuple[0] * handicap), int(colorTuple[1] * handicap), int(colorTuple[2] * handicap))
        return (t1[0], t1[1], t1[2])

    def webSetColours(self, params):
        headers = okayHeader
        primary = unquote(params.get(b"primary", None))
        secondary = unquote(params.get(b"secondary", None))
        self.setcolor(primary, secondary)
        return b"", headers

    def webSetAction(self, params):
        headers = okayHeader
        action = unquote(params.get(b"action", None))
        self.setaction(action)
        return b"", headers

    def webSetBrightness(self, params):
        headers = okayHeader
        brightness = int(unquote(params.get(b"brightness", None)))
        self.prevaction = self.ACTION_BRIGHTNESS
        self.setbrightness(brightness)
        return b"", headers

    def webSetDuration(self, params):
        headers = okayHeader
        duration = int(unquote(params.get(b"duration", None)))
        self.prevaction = self.ACTION_BRIGHTNESS
        self.setduration(duration)
        return b"", headers        