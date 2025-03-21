from modules.basic.basic_module import BasicModule
from machine import Pin
from serial_log import SerialLog
from modules.web.web_processor import okayHeader, unquote

class Relayx2(BasicModule):

    # Switch Pins
    S1 = None
    S2 = None
    Switches = []

    # Actual of the switches (0=Off, 1=On)
    States = [0, 0]

    def __init__(self):
        BasicModule.start(self)
        self.flip1command = self.basicSettings["relayx2"]["flipcommand1"]
        self.flip2command = self.basicSettings["relayx2"]["flipcommand2"]
        self.pin1number = self.basicSettings["relayx2"]["pin1"]
        self.pin2number = self.basicSettings["relayx2"]["pin2"]
        self.S1 = Pin(self.pin1number, Pin.OUT, pull=Pin.PULL_DOWN)
        self.S2 = Pin(self.pin2number, Pin.OUT, pull=Pin.PULL_DOWN)
        self.Switches.append(self.S1)
        self.Switches.append(self.S2)
        BasicModule.free(self) # release the ram

    def start(self):
        # Default the relay off, so the program matches the hw behaviour
        startState1 = self.getPref("relayx2", "S1", 0)
        if (startState1 == 1):
            self.on(1)
        else:
            self.off(1)

        startState2 = self.getPref("relayx2", "S2", 0)
        if (startState2 == 1):
            self.on(2)
        else:
            self.off(2)


    def tick(self):
        pass

    def getTelemetry(self):
        return {
            "relay/S1" : self.States[0],
            "relay/S2" : self.States[1]
        }

    def processTelemetry(self, telemetry):
        pass

    def getCommands(self):
        return []

    def processCommands(self, commands):
        for c in commands:
            if (c.startswith("/relay/on/1")):
                self.on(1)
            if (c.startswith("/relay/off/1")):
                self.off(1)
            if (c.startswith("/relay/flip/1")):
                self.flip(1)
            if (c.startswith(self.flip1command)):
                self.flip(1)

            if (c.startswith("/relay/on/2")):
                self.on(2)
            if (c.startswith("/relay/off/2")):
                self.off(2)
            if (c.startswith("/relay/flip/2")):
                self.flip(2)
            if (c.startswith(self.flip2command)):
                self.flip(2)


    def getRoutes(self):
        return { 
            b"/relay/flip/1" : self.webFlip1,
            b"/relay/flip/2" : self.webFlip2 
        }


    def getIndexFileName(self):
        return { 
            "relayx2" : "/modules/relayx2/relayx2_index.html" 
        }


    # internal code
    def webFlip1(self, params): 
        self.flip(1)
        headers = okayHeader
        data = b""
        return data, headers  

    def webFlip2(self, params): 
        self.flip(2)
        headers = okayHeader
        data = b""
        return data, headers  


    def on(self, num):
        self.States[num - 1] = 1
        self.Switches[num - 1].on()
        self.setPref("relayx1", "S" + str(num), 1)

    def off(self, num):
        self.States[num - 1] = 0
        self.Switches[num - 1].off()
        self.setPref("relayx1", "S" + str(num), 0)

    def flip(self, num): # num is 1-4, but arrays are 0-3
        if (self.States[num - 1] == 0):
            self.on(num)
        else:
            self.off(num)
