from modules.basic.basic_module import BasicModule
import time
from modules.web.web_processor import okayHeader
from serial_log import SerialLog

class GarageDoorControl(BasicModule):

    locked = False

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

        self.openAtMs = 15 * 60 * 1000 # 15 minutes
        self.pressMs = 750

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

            if (not self.locked):
                if (self.openForMs > self.openAtMs and self.openForMs < self.openAtMs + self.pressMs):
                    self.commands.append("/relay/on/1")
                if (self.openForMs > self.openAtMs + self.pressMs):
                    self.commands.append("/relay/off/1")
                    self.lastOpenAt = time.ticks_ms()


    def getTelemetry(self): 
        # round open for ms to seconds
        openForMsRounded = int(self.openForMs / 1000) * 1000
        telemetry = { 
            "garagedoorStatus": self.doorState, 
            "openForMs": openForMsRounded,
            "garageDoorLocked": self.locked
        }
        return telemetry

    def processTelemetry(self, telemetry):
        oldSensorState = self.sensorState

        # if critical telemetry is missing, just return
        if ("averagecm" not in telemetry):
            self.sensorState = "Unknown"
            return

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
        for c in commands:
            if (c.startswith("/garagedoor/lock")):
                self.lock()
            if (c.startswith("/garagedoor/unlock")):
                self.unlock()

    def getRoutes(self):
        return { 
            b"/garagedoor/lock" : self.webLock,
            b"/garagedoor/unlock" : self.webUnlock
        }

    def getIndexFileName(self):
        return { "garagedoorcloser" : "/modules/garage_door_closer/index.html" }

    # Internal code here
    def webLock(self, params): 
        self.lock()
        headers = okayHeader
        data = b""
        return data, headers
    
    def webUnlock(self, params): 
        self.unlock()
        headers = okayHeader
        data = b""
        return data, headers
    
    def lock(self):
        self.locked = True

    def unlock(self):
        self.locked = False