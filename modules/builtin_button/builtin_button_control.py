from modules.basic.basic_module import BasicModule
from machine import Pin

class BuiltinButtonControl(BasicModule):

    # CommandCache
    commands = []

    def __init__(self):
        self.pinNumber = self.basicSettings['builtinButton']['pin']
        self.buttonPin = Pin(self.pinNumber, Pin.IN)
        self.value = 0
     
    def start(self):
        self.value = 0

     
    def tick(self):
        newValue = 1 - self.buttonPin.value()
        if (self.value != newValue):
            self.value = newValue
            self.commands.append(b"/button/onboard/%s" % (str(self.value)))

     
    def getTelemetry(self):
        return { 'button/onboard': self.value }

     
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
        return { "builtinbutton" : "/modules/builtin_button/builtin_button_index.html" }