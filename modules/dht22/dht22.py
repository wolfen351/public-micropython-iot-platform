from modules.basic.basic_module import BasicModule
import machine
import dht
import time
from serial_log import SerialLog

class Dht22Monitor(BasicModule):

    currentT = 0
    currentH = 0

    def __init__(self):
        self.lastConvert = time.ticks_ms()

     
    def start(self):
        BasicModule.start(self)
        self.pin = self.basicSettings['dht22']['pin'] # default is 1000
        self.readEveryMs = self.basicSettings['dht22']['readEveryMs'] # default is 1000
        self.ts_pin = machine.Pin(self.pin)
        self.dht = dht.DHT22(self.ts_pin)

     
    def tick(self):
        currentTime = time.ticks_ms()
        diff = time.ticks_diff(currentTime, self.lastConvert)
        if (diff > self.readEveryMs and diff > 2500): 
            self.dht.measure()
            self.currentT = self.dht.temperature()
            self.currentH = self.dht.humidity()
            self.lastConvert = currentTime
            SerialLog.log("%s = %s'C %s %RH" % ("DHT22", self.currentT, self.currentH))
     
    def getTelemetry(self):
        # only return telemetry if we got readings
        if (self.currentT != 0 or self.currentH != 0):
            telemetry = {
                "temperature/dht22" : self.currentT,
                "humidity/dht22" : self.currentH,
                "tempReadAt": self.lastConvert
            }
            return telemetry
        else:
            return {} 

     
    def processTelemetry(self, telemetry):
        pass

     
    def getCommands(self):
        return []

     
    def processCommands(self, commands):
        pass

     
    def getRoutes(self):
        return {
        }

     
    def getIndexFileName(self):
        return { "dht22" : "/modules/dht22/dht22_index.html" }

    # Internal code here

