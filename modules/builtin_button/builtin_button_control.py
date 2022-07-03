from modules.basic.basic_module import BasicModule
from machine import Pin

class BuiltinButtonControl(BasicModule):

    # CommandCache
    commands = []

    def __init__(self, basicSettings):
        self.buttonPin = Pin(0, Pin.IN)
        self.value = 0

    @micropython.native 
    def start(self):
        self.value = 0

    @micropython.native 
    def tick(self):
        newValue = 1 - self.buttonPin.value()
        if (self.value != newValue):
            self.value = newValue
            self.commands.append(b"/button/onboard/" + str(self.value))

    @micropython.native 
    def getTelemetry(self):
        return { 'button/onboard': self.value }

    @micropython.native 
    def processTelemetry(self, telemetry):
        pass

    @micropython.native 
    def getCommands(self):
        var = self.commands
        self.commands = []
        return var

    @micropython.native 
    def processCommands(self, commands):
        pass

    @micropython.native 
    def getRoutes(self):
        return {}

    @micropython.native 
    def getIndexFileName(self):
        return { "builtinbutton" : "/modules/builtin_button/builtin_button_index.html" }