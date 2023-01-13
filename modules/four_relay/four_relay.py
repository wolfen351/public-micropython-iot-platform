from modules.basic.basic_module import BasicModule
from machine import Pin
from serial_log import SerialLog
from modules.web.web_processor import okayHeader, unquote

class FourRelay(BasicModule):

    # Switch Pins
    S1 = Pin(25, Pin.OUT)
    S2 = Pin(26, Pin.OUT)
    S3 = Pin(33, Pin.OUT)
    S4 = Pin(32, Pin.OUT)
    Switches = [S1, S2, S3, S4]

    # Actual of the switches (0=Off, 1=On)
    States = [0, 0, 0, 0]


    def __init__(self):
        pass

    def start(self):
        # Default all the switches to off, so the program matches the hw behaviour
        self.allOff()

    def tick(self):
        pass

    def getTelemetry(self):
        return {
            "relay/S1" : self.States[0],
            "relay/S2" : self.States[1],
            "relay/S3" : self.States[2],
            "relay/S4" : self.States[3]
        }

    def processTelemetry(self, telemetry):
        pass

    def getCommands(self):
        return []

    def processCommands(self, commands):
        for c in commands:
            if (c.startswith(b"/relay/on/")):
                s = int(c.replace(b"/relay/on/", b""))
                self.on(s)
            if (c.startswith(b"/relay/off/")):
                s = int(c.replace(b"/relay/off/", b""))
                self.off(s)
            if (c.startswith(b"/relay/flip/")):
                s = int(c.replace(b"/relay/flip/", b""))
                self.flip(s)

    def getRoutes(self):
        return { 
            b"/relay/alloff" : self.webAllOff,
            b"/relay/allon" : self.webAllOn,
            b"/relay/flip" : self.webFlip 
        }


    def getIndexFileName(self):
        return { "relay" : "/modules/four_relay/relay_index.html" }


    # internal code
    def webAllOn(self, params): 
        self.allOn()
        headers = okayHeader
        data = b""
        return data, headers        

    def webAllOff(self, params): 
        self.allOff()
        headers = okayHeader
        data = b""
        return data, headers        

    def webFlip(self, params): 
        sw = unquote(params.get(b"sw", None))
        self.flip(int(sw))
        headers = okayHeader
        data = b""
        return data, headers  

    def allOn(self): # num is 1-4, but arrays are 0-3
        for num in range(4):
            self.States[num] = 1
            self.Switches[num].on()

    def allOff(self): # num is 1-4, but arrays are 0-3
        for num in range(4):
            self.States[num] = 0
            self.Switches[num].off()
            
    def on(self, num): # num is 1-4, but arrays are 0-3
        self.States[num - 1] = 1
        self.Switches[num -1].on()

    def off(self, num): # num is 1-4, but arrays are 0-3
        self.States[num - 1] = 0
        self.Switches[num -1].off()

    def flip(self, num): # num is 1-4, but arrays are 0-3
        if (self.States[num - 1] == 0):
            self.on(num)
        else:
            self.off(num)

    def command(self, num, onOff): # num is 1-4, OnOff=0 for off and 1 for on
        if (onOff == 0): 
            self.off(num)
        if (onOff == 1): 
            self.on(num)


