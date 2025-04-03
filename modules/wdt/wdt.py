from modules.basic.basic_module import BasicModule
from machine import WDT
from serial_log import SerialLog

class WDTControl(BasicModule):

    def __init__(self):
        pass
     
    def start(self):
        self.wdt = WDT(timeout=900000) # 15 min
        self.wdt.feed()
        SerialLog.log("WDT started")
     
    def tick(self):
        self.wdt.feed()
     
    def getTelemetry(self):
        return {}
     
    def processTelemetry(self, telemetry):
        pass
     
    def getCommands(self):
        return []
     
    def processCommands(self, commands):
        pass
     
    def getRoutes(self):
        return {}
     
    def getIndexFileName(self):
        return {}

    # Internal code here

