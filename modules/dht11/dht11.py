from modules.basic.basic_module import BasicModule
import machine
import dht
import time
from serial_log import SerialLog

class Dht11Monitor(BasicModule):

    currentT = 0
    currentH = 0

    def __init__(self):
        self.lastConvert = time.ticks_ms()

     
    def start(self):
        self.ts_pin = machine.Pin(16)
        self.dht = dht.DHT11(self.ts_pin)

     
    def tick(self):
        currentTime = time.ticks_ms()
        diff = time.ticks_diff(currentTime, self.lastConvert)
        if (diff > 2500): 
            self.dht.measure()
            self.currentT = self.dht.temperature()
            self.currentH = self.dht.humidity()
            self.lastConvert = currentTime

     
    def getTelemetry(self):
        telemetry = {}
        telemetry.update({"temperature/dht11":self.currentT})
        telemetry.update({"humidity/dht11":self.currentH})
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
        return { "dht11" : "/modules/dht11/dht11_index.html" }

    # Internal code here

