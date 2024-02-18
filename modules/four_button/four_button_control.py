from modules.basic.basic_module import BasicModule
from machine import Pin

class FourButton(BasicModule):

    # Button Pins
    B1 = Pin(34, Pin.IN)
    B2 = Pin(35, Pin.IN)
    B3 = Pin(36, Pin.IN)
    B4 = Pin(39, Pin.IN)
    Buttons = [B1, B2, B3, B4]

    # State of the buttons (0=Off, 1=On)
    States = [0, 0, 0, 0]

    # CommandCache
    commands = []

    def __init__(self):
        pass
     
    def start(self):
        BasicModule.start(self)

        self.extraCommandsOn = self.basicSettings['four_button']['commandsOn']
        self.extraCommandsOff = self.basicSettings['four_button']['commandsOff']
        self.value = 0

     
    def tick(self):
        newValue = 1 - self.B1.value()
        if (self.States[0] != newValue):
            self.States[0] = newValue
            self.commands.append("/button/B1/" + str(newValue))
            if (newValue == 1):
                self.commands.append(self.extraCommandsOn[0])
            else: 
                self.commands.append(self.extraCommandsOff[0])
        newValue = 1 - self.B2.value()
        if (self.States[1] != newValue):
            self.States[1] = newValue
            self.commands.append("/button/B2/" + str(newValue))
            if (newValue == 1):
                self.commands.append(self.extraCommandsOn[1])
            else: 
                self.commands.append(self.extraCommandsOff[1])
        newValue = 1 - self.B3.value()
        if (self.States[2] != newValue):
            self.States[2] = newValue
            self.commands.append("/button/B3/" + str(newValue))
            if (newValue == 1):
                self.commands.append(self.extraCommandsOn[2])
            else: 
                self.commands.append(self.extraCommandsOff[2])
        newValue = 1 - self.B4.value()
        if (self.States[3] != newValue):
            self.States[3] = newValue
            self.commands.append("/button/B4/" + str(newValue))
            if (newValue == 1):
                self.commands.append(self.extraCommandsOn[3])
            else: 
                self.commands.append(self.extraCommandsOff[3])
     
    def getTelemetry(self):
        return {
            "button/B1" : self.States[0],
            "button/B2" : self.States[1],
            "button/B3" : self.States[2],
            "button/B4" : self.States[3]
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
        return {}

     
    def getIndexFileName(self):
        return { "four_button" : "/modules/four_button/four_button_index.html" }