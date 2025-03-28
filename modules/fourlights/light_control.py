from modules.basic.basic_module import BasicModule
from modules.fourlights.light_settings import LightSettings
from machine import Pin
import time
from serial_log import SerialLog
from modules.web.web_processor import okayHeader, unquote

class LightControl(BasicModule):

    # Parameters (in milliseconds 1000=1s)
    TimeOnSetting = 30000
    Delay0Setting = 0
    Delay1Setting = 1000
    Delay2Setting = 3000
    Delay3Setting = 3000
    lastrun = time.ticks_ms()

    # CommandCache
    commands = []

    # Mode of the lights (0=Off, 1=On, 2=Auto)
    Modes = [2, 2, 2, 2]

    # Actual Light State
    Lights = [0, 0, 0, 0]

    # Trigger Pins by connecting D1 or D2 to ground
    T1 = Pin(35, Pin.IN)
    T2 = Pin(33, Pin.IN)
    SoftT1 = 0
    SoftT2 = 0

    # When to change a light to ON
    LightOnAt = [-1, -1, -1, -1]

    # When to change a light to OFF
    LightOffAt = [-1, -1, -1, -1]

    # State of the triggers (1=off)
    Triggers = [1, 1]

    def __init__(self):
        self.calculateTimes()

     
    def start(self):
        # Default all the lights to off
        self.commands.append("/mosfet/alloff")
        
        lightSettings = LightSettings()
        lightSettings.load()
        self.TimeOnSetting = lightSettings.TimeOnSetting
        self.Delay0Setting = lightSettings.Delay0Setting
        self.Delay1Setting = lightSettings.Delay1Setting
        self.Delay2Setting = lightSettings.Delay2Setting
        self.Delay3Setting = lightSettings.Delay3Setting

        self.lastrun = time.ticks_ms()
        self.calculateTimes()

     
    def tick(self):
        # Main Loop
        Trigger1 = self.T1.value()
        Trigger2 = self.T2.value()

        if (self.SoftT1 == 1):
            Trigger1 = 0
            self.SoftT1 = 0

        if (self.SoftT2 == 1):
            Trigger2 = 0
            self.SoftT2 = 0

        if (self.Triggers[0] != Trigger1):
            self.Triggers[0] = Trigger1
            SerialLog.log(b"Light: Trigger 1 - " + str(1 - Trigger1))

        if (self.Triggers[1] != Trigger2):
            self.Triggers[1] = Trigger2
            SerialLog.log(b"Light: Trigger 2 - " + str(1 - Trigger2))

        diff = time.ticks_diff(time.ticks_ms(), self.lastrun)
        self.lastrun = time.ticks_ms()

        for l in range(4):
            # If trigger 1 is set, then go upwards (connected to ground)
            if (Trigger1 == 0):
                self.LightOnAt[l] = self.atMost(self.LightOnAt[l], self.Periods[l])

            # If trigger 2 is set, then go downwards (connected to ground)
            if (Trigger2 == 0):
                self.LightOnAt[l] = self.atMost(self.LightOnAt[l], self.Periods[3-l])

            self.setLight(self.LightOnAt[l], self.LightOffAt[l], l+1, self.Modes[l])
            self.LightOnAt[l], self.LightOffAt[l] = self.subtract(self.LightOnAt[l], self.LightOffAt[l], diff)

        # Debug output
        #print("T1=", Trigger1, "T2=", Trigger2, " - (", self.LightOnAt[0], self.LightOffAt[0], ") (", self.LightOnAt[1], self.LightOffAt[1], ") (", self.LightOnAt[2], self.LightOffAt[2], ") (", self.LightOnAt[3], self.LightOffAt[3], ")")
        #sleep(100)

     
    def getTelemetry(self):
        return { 
            "light1" : self.Modes[0], 
            "light2" : self.Modes[1], 
            "light3" : self.Modes[2], 
            "light4" : self.Modes[3], 
            "trigger1" : 1-self.Triggers[0], 
            "trigger2" : 1-self.Triggers[1], 
            }

     
    def processTelemetry(self, telemetry):
        pass

     
    def getCommands(self):
        var = self.commands
        self.commands = []
        return var

     
    def processCommands(self, commands):
        for command in commands:
            if (command == "/button/onboard/1"):
                self.SoftT1 = 1
            if (command == "/trigger/on/1"):
                self.SoftT1 = 1
            if (command == "/trigger/on/2"):
                self.SoftT2 = 1
     
    def getRoutes(self):
        return {
            b"/4light/on": self.webCommandOn,
            b"/4light/off": self.webCommandOff,
            b"/4light/auto": self.webCommandAuto,
            b"/light": b"/modules/fourlights/web_light.html",
            b"/lightsavesettings": self.webSaveSettings,
            b"/lightloadsettings": self.webLoadSettings,
            b"/4light/trigger/1": self.webtrigger1,
            b"/4light/trigger/2": self.webtrigger2
        }

     
    def getIndexFileName(self):
        return { "lights4": "/modules/fourlights/light_index.html" }

    # Internal Methods
    def webtrigger1(self, params):
        headers = okayHeader
        data = b""
        self.SoftT1 = 1
        return data, headers
    
    def webtrigger2(self, params):
        headers = okayHeader
        data = b""
        self.SoftT2 = 1
        return data, headers
    
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


     
    def webCommandOn(self, params):
        headers = okayHeader
        data = b""
        val = int(unquote(params.get(b"sw", None))) - 1
        self.command(1, val)
        return data, headers  

     
    def webCommandOff(self, params):
        headers = okayHeader
        data = b""
        val = int(unquote(params.get(b"sw", None))) - 1
        self.command(0, val)
        return data, headers  

     
    def webCommandAuto(self, params):
        headers = okayHeader
        data = b""
        val = int(unquote(params.get(b"sw", None))) - 1
        self.command(2, val)
        return data, headers  

     
    def calculateTimes(self):
        # Convert to number of loops using a timefactor
        self.TimeOn = self.TimeOnSetting
        self.Delay0 = self.Delay0Setting
        self.Delay1 = self.Delay1Setting
        self.Delay2 = self.Delay2Setting
        self.Delay3 = self.Delay3Setting

        # Periods
        self.Period0 = self.Delay0
        self.Period1 = self.Delay0 + self.Delay1
        self.Period2 = self.Delay0 + self.Delay1 + self.Delay2
        self.Period3 = self.Delay0 + self.Delay1 + self.Delay2 + self.Delay3
        self.Periods = [self.Period0, self.Period1, self.Period2, self.Period3]

     
    def status(self):
        return self.Modes

     
    def triggers(self):
        return self.Triggers

    # override normal behaviour Function=0-Off 1-On 2-Auto; Num  is 0-3
     
    def command(self, function, num):
        if (function == 0):
            self.Modes[num] = 0 #off
            if (self.Lights[num] != 0):
                self.commands.append("/mosfet/off/" + str(num+1))
                self.Lights[num] = 0
        if (function == 1):
            self.Modes[num] = 1 #on
            if (self.Lights[num] != 1):
                self.commands.append("/mosfet/on/" + str(num+1))
                self.Lights[num] = 1
        if (function == 2):
            self.Modes[num] = 2 #auto

     
    def settings(self, settingsVals):
        self.TimeOnSetting = settingsVals[0]
        self.Delay0Setting = settingsVals[1]
        self.Delay1Setting = settingsVals[2]
        self.Delay2Setting = settingsVals[3]
        self.Delay3Setting = settingsVals[4]
        self.calculateTimes()

        # Save the light settings to disk
        lightSettings = LightSettings()
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

    # Prevent a number from dropping below -1
     
    def clampTo(self, old, new):
        if (old > 0 and new < 0):
            return 0
        if (old < 0 and new < 0):
            return -1
        return new

    # Make the number at most the desired value, deal with -1 
     
    def atMost(self, current, desired):
        if (desired <= current):
            return desired
        if (current == -1):
            return desired
        return current

    # Make the number at least the desired value
     
    def atLeast(self, current, desired):
        if (desired >= current):
            return desired
        return current

    # If a timer reaches 0 then set the light on or off
     
    def setLight(self, OnAt, OffAt, Light, Mode):
        if (Mode == 0): # off
            if (self.Lights[Light-1] != 0):
                self.commands.append("/mosfet/off/" + str(Light))
                self.Lights[Light-1] = 0
        if (Mode == 1): # on
            if (self.Lights[Light-1] != 1):
                self.commands.append("/mosfet/on/" + str(Light))
                self.Lights[Light-1] = 1
        if (Mode == 2): # auto
            if (OnAt == 0): # Switch the light on, and stay on at least the TimeOn
                if (self.Lights[Light-1] != 1):
                    self.commands.append("/mosfet/on/" + str(Light))
                    self.Lights[Light-1] = 1
                self.LightOffAt[Light-1] = self.atLeast(self.LightOffAt[Light-1], self.TimeOn)
            if (OffAt == 0):
                self.commands.append("/mosfet/off/" + str(Light))
                self.Lights[Light-1] = 0

    # Subtract 1 from all the timer calcs, dont let them go below -1
     
    def subtract(self, OnAt, OffAt, diff):
        return self.clampTo(OnAt, OnAt - diff), self.clampTo(OffAt, OffAt - diff)


