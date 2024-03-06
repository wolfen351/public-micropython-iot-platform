from machine import Pin
from modules.basic.basic_module import BasicModule

class PIRDetect(BasicModule):

    # CommandCache
    commands = []
    valueA = 0
    valueB = 0

    def __init__(self):
        pass
     
    def start(self):
        BasicModule.start(self)

        self.pinDetectorANumber = self.basicSettings['pir']['pinA']
        self.pinDetectorA = Pin(self.pinDetectorANumber, Pin.IN, Pin.PULL_UP)

        self.pinDetectorBNumber = self.basicSettings['pir']['pinB']
        self.pinDetectorB = Pin(self.pinDetectorBNumber, Pin.IN, Pin.PULL_UP)

     
    def tick(self):

        oldValueA = self.valueA
        oldValueB = self.valueB

        self.valueA = 1 - self.pinDetectorA.value()
        self.valueB = 1 - self.pinDetectorB.value()
        
        if (oldValueA != self.valueA and self.valueA == 0):
            self.commands.append(self.basicSettings['pir']['pinACommand'])

        if (oldValueB != self.valueB and self.valueB == 0):
            self.commands.append(self.basicSettings['pir']['pinBCommand'])

    def getTelemetry(self):
        return { 
            "pirA": self.valueA,
            "pirB": self.valueB
        }
     
    def processTelemetry(self, telemetry):
        pass
     
    def getCommands(self):
        var = self.commands
        self.commands = []
        return var
     
    def processCommands(self, commands):
        pass
     
    def getRoutes(self):
        return { }
     
    def getIndexFileName(self):
        return { "pir": "/modules/pir/index.html" }

    # Internal Methods
