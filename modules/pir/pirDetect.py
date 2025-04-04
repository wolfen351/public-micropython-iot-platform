from machine import Pin
from modules.basic.basic_module import BasicModule
from serial_log import SerialLog

class PIRDetect(BasicModule):

    # CommandCache
    commands = []
    valueA = 0
    valueB = 0
    pinDetectorA = None
    pinDetectorB = None

    def __init__(self):
        pass
     
    def start(self):
        BasicModule.start(self)

        try:
            self.pinDetectorANumber = self.basicSettings['pir']['pinA']
            SerialLog.log("PIR Pin A: ", self.pinDetectorANumber)
            self.pinDetectorA = Pin(self.pinDetectorANumber, Pin.IN, Pin.PULL_UP)
        except:
            SerialLog.log("Error: PIR Pin A not found")

        try:
            self.pinDetectorBNumber = self.basicSettings['pir']['pinB']
            SerialLog.log("PIR Pin B: ", self.pinDetectorBNumber)
            self.pinDetectorB = Pin(self.pinDetectorBNumber, Pin.IN, Pin.PULL_UP)
        except:
            SerialLog.log("Error: PIR Pin B not found")

     
    def tick(self):

        oldValueA = self.valueA
        oldValueB = self.valueB

        try:
            self.valueA = 1 - self.pinDetectorA.value()
        except:
            pass
    
        try:
            self.valueB = 1 - self.pinDetectorB.value()
        except:
            pass
        
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
