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
        self.ts_pin = machine.Pin(8)
        self.dht = dht.DHT22(self.ts_pin)

     
    def tick(self):
        currentTime = time.ticks_ms()
        diff = time.ticks_diff(currentTime, self.lastConvert)
        if (diff > 2500): 
            self.dht.measure()
            self.currentT = self.dht.temperature()
            self.currentH = self.dht.humidity()
            self.lastConvert = currentTime

     
    def getTelemetry(self):
        telemetry = {
            "temperature/dht22" : self.currentT,
            "humidity/dht22" : self.currentH
        }
        return telemetry

     
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

