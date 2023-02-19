from modules.basic.basic_module import BasicModule
from modules.us_range.hcsr04 import HCSR04
import time

class USRangeSensor(BasicModule):

    distance_cm = -1

    def __init__(self):
        pass

    def start(self):
        BasicModule.start(self)
        self.sensor = HCSR04(trigger_pin=18, echo_pin=16)
        self.lastDetectTime = time.ticks_ms()

    def tick(self):

        currentTime = time.ticks_ms()
        diff = time.ticks_diff(currentTime, self.lastDetectTime)
        if (diff > 2000):
            self.distance_cm = self.sensor.distance_cm()
            self.lastDetectTime = currentTime

    def getTelemetry(self): 
        telemetry = { "distancecm": self.distance_cm }
        return telemetry

    def processTelemetry(self, telemetry):
        pass

    def getCommands(self):
        return []

    def processCommands(self, commands):
        pass

    def getRoutes(self):
        return {}

    def getIndexFileName(self):
        return { "us_range" : "/modules/us_range/index.html" }

    # Internal code here
