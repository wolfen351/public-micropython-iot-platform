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
    Triggers = [0, 0]

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
     
    def tick(self):
        # Main Loop
        if (self.Triggers[0] == 1):
            SerialLog.log(b"Light: Trigger 1 - " + str(self.Triggers[0]))
            self.action = 1
            self.triggeredAt = time.ticks_ms()

        if (self.Triggers[1] == 1):
            SerialLog.log(b"Light: Trigger 2 - " + str(self.Triggers[1]))
            self.action = 2
            self.triggeredAt = time.ticks_ms()

        # Reset Triggers
        self.Triggers[0] = 0
        self.Triggers[1] = 0

        newLightState = [self.lightState[0], self.lightState[1], self.lightState[2], self.lightState[3]]

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
            for num in range(4):
                if (newLightState[num] != self.lightState[num] and newLightState[num] == 0):
                    self.commands.append(b"/relay/off/" + str(num+1).encode('ascii'))
                    self.lightState[num] = 0

                if (newLightState[num] != self.lightState[num] and newLightState[num] == 1):
                    self.commands.append(b"/relay/on/" + str(num+1).encode('ascii'))
                    self.lightState[num] = 1
     
    def getTelemetry(self):
        return { 
            "light1": self.lightState[0],
            "light2": self.lightState[1],
            "light3": self.lightState[2],
            "light4": self.lightState[3]
        }
     
    def processTelemetry(self, telemetry):
        pass
     
    def getCommands(self):
        var = self.commands
        self.commands = []
        return var
     
    def processCommands(self, commands):
        for c in commands:
            if (c.startswith(b"/trigger/")):
                s = int(c.replace(b"/trigger/", b""))
                self.Triggers[s] = 1
     
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
        settings =  self.getsettings()
        headers = okayHeader
        data = b"{ \"timeOn\": %s, \"delay1\": %s, \"delay2\": %s, \"delay3\": %s, \"delay4\": %s }" % (settings[0], settings[1], settings[2], settings[3], settings[4])
        return data, headers
     
    def webSaveSettings(self, params):
        # Read form params
        TimeOn = unquote(params.get(b"TimeOn", None))
        Delay1 = unquote(params.get(b"Delay1", None))
        Delay2 = unquote(params.get(b"Delay2", None))
        Delay3 = unquote(params.get(b"Delay3", None))
        Delay4 = unquote(params.get(b"Delay4", None))
        settings = (int(TimeOn), int(Delay1), int(Delay2), int(Delay3), int(Delay4))
        self.settings(settings)
        headers = b"HTTP/1.1 307 Temporary Redirect\r\nLocation: /\r\n"
        return b"", headers

    def settings(self, settingsVals):
        self.TimeOnSetting = settingsVals[0]
        self.Delay0Setting = settingsVals[1]
        self.Delay1Setting = settingsVals[2]
        self.Delay2Setting = settingsVals[3]
        self.Delay3Setting = settingsVals[4]

        # Save the light settings to disk
        lightSettings = DionHallwayLightsSettings()
        lightSettings.TimeOnSetting = self.TimeOnSetting
        lightSettings.Delay0Setting = self.Delay0Setting
        lightSettings.Delay1Setting = self.Delay1Setting
        lightSettings.Delay2Setting = self.Delay2Setting
        lightSettings.Delay3Setting = self.Delay3Setting
        SerialLog.log(lightSettings)
        lightSettings.write()
    
     
    def getsettings(self):
        s = (self.TimeOnSetting, self.Delay0Setting, self.Delay1Setting, self.Delay2Setting, self.Delay3Setting)
        return s



