from modules.basic.basic_module import BasicModule
from modules.us_range.hcsr04 import HCSR04
import time

class USRangeSensor(BasicModule):

    distance_cm = -1
    average_cm = -1
    average_over = 30
    bucket = []

    def __init__(self):
        pass

    def start(self):
        BasicModule.start(self)
        self.sensor = HCSR04(trigger_pin=18, echo_pin=16)
        self.lastPulseTime = time.ticks_ms()
        self.lastDetectTime = time.ticks_ms()

    def tick(self):

        currentTime = time.ticks_ms()
        diff = time.ticks_diff(currentTime, self.lastPulseTime)
        if (diff > 200):
            self.lastPulseTime = currentTime
            reading = self.sensor.distance_cm()
            if (reading != 250):
                self.lastDetectTime = currentTime
                self.bucket.append(reading)
                self.distance_cm = sum(self.bucket) / len(self.bucket)
                if (len(self.bucket) >= self.average_over):
                    self.average_cm = sum(self.bucket) / len(self.bucket)
                    self.bucket.pop(0)


    def getTelemetry(self): 

        if (self.distance_cm == -1 or self.average_cm == -1):
            return {}
        
        # only send data if we've detected something in the last 5 seconds, and there is at least 5 values in the bucket
        currentTime = time.ticks_ms()
        diff = time.ticks_diff(currentTime, self.lastDetectTime)
        if (diff > 5000 or len(self.bucket) < 5):
            return {}
        
        telemetry = { 
            "averagecm": self.average_cm
        }
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
