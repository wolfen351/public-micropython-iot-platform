from modules.basic.basic_module import BasicModule
import time

from serial_log import SerialLog

class GarageDoorControl(BasicModule):

    def __init__(self):
        pass

    def start(self):
        BasicModule.start(self)
        self.doorState = "Closed"
        self.lastOpenAt = 0
        self.openForMs = 0
        self.commands = []

    def tick(self):
        # reset timer
        if (self.doorState == "Closed" and self.lastOpenAt != 0):
            self.lastOpenAt = 0
            self.openForMs = 0

        if (self.doorState == "Open"):
            # start timer
            if (self.lastOpenAt == 0):
                self.lastOpenAt = time.ticks_ms()

            currentTime = time.ticks_ms()
            self.openForMs = time.ticks_diff(currentTime, self.lastOpenAt)

            if (self.openForMs > 600000 and self.openForMs < 602000):
                self.commands.append("/mosfet/allon")
            if (self.openForMs > 602000):
                self.commands.append("/mosfet/alloff")
                self.lastOpenAt = time.ticks_ms()


    def getTelemetry(self): 
        telemetry = { "garagedoorStatus": self.doorState, "openForMs": self.openForMs }
        return telemetry

    def processTelemetry(self, telemetry):
        if (telemetry["distancecm"] > 90):
          self.doorState = "Closed"
        else:
          self.doorState = "Open"

    def getCommands(self):
        toSend = self.commands
        self.commands = []
        return toSend

    def processCommands(self, commands):
        pass

    def getRoutes(self):
        return {}

    def getIndexFileName(self):
        return { "garagedoorcloser" : "/modules/garage_door_closer/index.html" }

    # Internal code here
