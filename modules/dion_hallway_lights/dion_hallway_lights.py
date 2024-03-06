from modules.basic.basic_module import BasicModule
from modules.dion_hallway_lights.dion_hallway_lights_settings import DionHallwayLightsSettings
import time
from serial_log import SerialLog
from modules.web.web_processor import okayHeader, unquote

class DionHallwayLightsControl(BasicModule):

    # CommandCache
    commands = []

    # Actual Light State
    lightState = [0, 0, 0, 0]

    # State of the triggers (0=off)
    triggerState = [0, 0]

    # Action says which way we are going
    action = 0 # 0=none 1=up 2=down

    # Time the trigger fired
    triggeredAt = 0

    # Delay in ms betwen lights activating
    delayBetweenLights = 400

    # How long each light stays on
    stayOnFor = 10000

    def __init__(self):
        pass
     
    def start(self):
        # Default all the lights to off, so the software matches the HW behaviour
        self.lightState = [0, 0, 0, 0]

        # Load the light settings
        lightSettings = DionHallwayLightsSettings()
        lightSettings.load()
        self.stayOnFor = lightSettings.TimeOnSetting
        self.delayBetweenLights = lightSettings.DelaySetting
     
    def tick(self):
        # Main Loop
        if (self.triggerState[0] == 1):
            SerialLog.log("Light: Trigger 1")
            self.action = 1
            self.triggeredAt = time.ticks_ms()

        if (self.triggerState[1] == 1):
            SerialLog.log("Light: Trigger 2")
            self.action = 2
            self.triggeredAt = time.ticks_ms()

        # Reset Triggers
        self.triggerState[0] = 0
        self.triggerState[1] = 0

        newLightState = self.lightState.copy()

        if (self.action > 0):
            diff = time.ticks_diff(time.ticks_ms(), self.triggeredAt)
           
            if (self.action == 1): # going up
                if diff > 0:
                    newLightState[0] = 1
                if diff > self.delayBetweenLights:
                    newLightState[1] = 1
                if diff > self.delayBetweenLights * 2:
                    newLightState[2] = 1
                if diff > self.delayBetweenLights * 3:
                    newLightState[3] = 1
                if diff > self.stayOnFor:
                    newLightState[0] = 0
                if diff > self.delayBetweenLights + self.stayOnFor:
                    newLightState[1] = 0
                if diff > self.delayBetweenLights * 2  + self.stayOnFor:
                    newLightState[2] = 0
                if diff > self.delayBetweenLights * 3  + self.stayOnFor:
                    newLightState[3] = 0
                    self.action = 0

            if (self.action == 2): # going down
                if diff > 0:
                    newLightState[3] = 1
                if diff > self.delayBetweenLights:
                    newLightState[2] = 1
                if diff > self.delayBetweenLights * 2:
                    newLightState[1] = 1
                if diff > self.delayBetweenLights * 3:
                    newLightState[0] = 1
                if diff > self.stayOnFor:
                    newLightState[3] = 0
                if diff > self.delayBetweenLights + self.stayOnFor:
                    newLightState[2] = 0
                if diff > self.delayBetweenLights * 2  + self.stayOnFor:
                    newLightState[1] = 0
                if diff > self.delayBetweenLights * 3  + self.stayOnFor:
                    newLightState[0] = 0
                    self.action = 0


            # send changes as commands
            for num, val in enumerate(newLightState):
                if (val != self.lightState[num] and val == 0):
                    self.commands.append("/relay/off/%s" % (num+1))
                    self.lightState[num] = 0

                if (val != self.lightState[num] and val == 1):
                    self.commands.append("/relay/on/%s" % (num+1))
                    self.lightState[num] = 1
     
    def getTelemetry(self):
        return { 
            "light1": self.lightState[0],
            "light2": self.lightState[1],
            "light3": self.lightState[2],
            "light4": self.lightState[3],
            "trigger/1": self.triggerState[0],
            "trigger/2": self.triggerState[1]
        }
     
    def processTelemetry(self, telemetry):
        pass
     
    def getCommands(self):
        var = self.commands
        self.commands = []
        return var
     
    def processCommands(self, commands):
        for c in commands:
            if (c.startswith("/trigger/")):
                s = int(c[-1])
                self.triggerState[s-1] = 1
     
    def getRoutes(self):
        return {
            b"/light": b"/modules/dion_hallway_lights/settings.html",
            b"/lightsavesettings": self.webSaveSettings,
            b"/lightloadsettings": self.webLoadSettings
        }
     
    def getIndexFileName(self):
        return { "dion_hallway_lights": "/modules/dion_hallway_lights/index.html" }

    # Internal Methods
    def webLoadSettings(self, params):
        headers = okayHeader
        data = b"{ \"timeOn\": %s, \"delay\": %s }" % (self.stayOnFor, self.delayBetweenLights)
        return data, headers
     
    def webSaveSettings(self, params):
        # Read form params
        self.stayOnFor = int(unquote(params.get(b"TimeOn", None)))
        self.delayBetweenLights = int(unquote(params.get(b"Delay", None)))

        # Save the light settings to disk
        lightSettings = DionHallwayLightsSettings()
        lightSettings.TimeOnSetting = self.stayOnFor
        lightSettings.DelaySetting = self.delayBetweenLights
        SerialLog.log(lightSettings)
        lightSettings.write()

        headers = b"HTTP/1.1 307 Temporary Redirect\r\nLocation: /\r\n"
        return b"", headers

