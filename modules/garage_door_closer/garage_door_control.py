from modules.basic.basic_module import BasicModule
import time

from serial_log import SerialLog

class GarageDoorControl(BasicModule):

    def __init__(self):
        pass

    def start(self):
        BasicModule.start(self)
        self.sensorState = "Closed"
        self.sensorChangedAt = 0

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
        # round open for ms to seconds
        openForMsRounded = int(self.openForMs / 1000) * 1000
        telemetry = { "garagedoorStatus": self.doorState, "openForMs": openForMsRounded }
        return telemetry

    def processTelemetry(self, telemetry):
        oldSensorState = self.sensorState

        # See if the sensor is open or closed
        if (telemetry["averagecm"] == -1):
          self.sensorState = "Unknown"
        elif (telemetry["averagecm"] > 90):
          self.sensorState = "Closed"
        else:
          self.sensorState = "Open"

        # Detect Sensor Changes
        if (oldSensorState != self.sensorState):
          self.sensorChangedAt = time.ticks_ms()

        # Check if 3 seconds have passed since last sensor change
        if (self.sensorChangedAt != 0 and self.doorState != self.sensorState):
            currentTime = time.ticks_ms()
            diff = time.ticks_diff(currentTime, self.sensorChangedAt)
            if (diff > 3000):
                self.doorState = self.sensorState

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
