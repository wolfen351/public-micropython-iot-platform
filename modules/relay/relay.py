from modules.basic.basic_module import BasicModule
from machine import Pin
from serial_log import SerialLog
from modules.web.web_processor import okayHeader, unquote

class Relay(BasicModule):

    # Switch Pins
    S1 = None
    Switches = []

    # Actual of the switches (0=Off, 1=On)
    States = [0]

    def __init__(self):
        BasicModule.start(self)
        self.flipcommand = self.basicSettings["relay"]["flipcommand"]
        self.pinnumber = self.basicSettings["relay"]["pin"]
        self.S1 = Pin(self.pinnumber, Pin.OUT, pull=Pin.PULL_DOWN)
        self.Switches.append(self.S1)
        BasicModule.free(self) # release the ram

    def start(self):
        # Default the relay off, so the program matches the hw behaviour
        startState = self.getPref("relay", "S1", 0)
        if (startState == 1):
            self.on()
        else:
            self.off()

    def tick(self):
        pass

    def getTelemetry(self):
        return {
            "relay/S1" : self.States[0]
        }

    def processTelemetry(self, telemetry):
        pass

    def getCommands(self):
        return []

    def processCommands(self, commands):
        for c in commands:
            if (c.startswith("/relay/on/1")):
                self.on()
            if (c.startswith("/relay/off/1")):
                self.off()
            if (c.startswith("/relay/flip/1")):
                self.flip()
            if (c.startswith(self.flipcommand)):
                self.flip()

    def getRoutes(self):
        return { 
            b"/relay/flip" : self.webFlip 
        }


    def getIndexFileName(self):
        return { "relay" : "/modules/relay/relay_index.html" }


    # internal code
    def webFlip(self, params): 
        self.flip()
        headers = okayHeader
        data = b""
        return data, headers  

    def on(self):
        self.States[0] = 1
        self.Switches[0].on()
        self.setPref("relay", "S1", 1)

    def off(self):
        self.States[0] = 0
        self.Switches[0].off()
        self.setPref("relay", "S1", 0)

    def flip(self): # num is 1-4, but arrays are 0-3
        if (self.States[0] == 0):
            self.on()
        else:
            self.off()

    def command(self, onOff): # OnOff=0 for off and 1 for on
        if (onOff == 0): 
            self.off()
        if (onOff == 1): 
            self.on()


