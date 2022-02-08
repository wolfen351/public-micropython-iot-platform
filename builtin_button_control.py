from basic_module import BasicModule
from machine import Pin

class BuiltinButtonControl(BasicModule):
    def __init__(self, basicSettings):
        self.buttonPin = Pin(0, Pin.IN)

    def start(self):
        self.value = 1 - self.buttonPin.value()

    def tick(self):
        self.value = 1 - self.buttonPin.value()

    def getTelemetry(self):
        return { 'button/onboard': self.value }

    def processTelemetry(self, telemetry):
        pass

    def getCommands(self):
        return []

    def processCommands(self, commands):
        pass

    def getRoutes(self):
        return {}

    def getIndexFileName(self):
        return { "builtinbutton" : "builtin_button_index.html" }