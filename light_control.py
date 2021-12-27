from d1mini_pins import PIN_D1, PIN_D2
from light_settings import LightSettings
from machine import Pin, sleep

class LightControl:

    # Parameters (in milliseconds 1000=1s)
    TimeOnSetting = 30000
    Delay0Setting = 0
    Delay1Setting = 1000
    Delay2Setting = 3000
    Delay3Setting = 3000

    def calculateTimes(self):
        # Convert to number of loops using a timefactor
        self.TimeFactor = 16# ms per loop
        self.TimeOn = self.TimeOnSetting//self.TimeFactor
        self.Delay0 = self.Delay0Setting//self.TimeFactor
        self.Delay1 = self.Delay1Setting//self.TimeFactor
        self.Delay2 = self.Delay2Setting//self.TimeFactor
        self.Delay3 = self.Delay3Setting//self.TimeFactor

        # Periods
        self.Period0 = self.Delay0
        self.Period1 = self.Delay0 + self.Delay1
        self.Period2 = self.Delay0 + self.Delay1 + self.Delay2
        self.Period3 = self.Delay0 + self.Delay1 + self.Delay2 + self.Delay3
        self.Periods = [self.Period0, self.Period1, self.Period2, self.Period3]

    # Mode of the lights (0=Off, 1=On, 2=Auto)
    Modes = [2, 2, 2, 2]

    # Trigger Pins by connecting D1 or D3 to ground
    T1 = Pin(PIN_D1, Pin.IN) 
    T2 = Pin(PIN_D2, Pin.IN)

    # When to change a light to ON
    LightOnAt = [-1, -1, -1, -1]

    # When to change a light to OFF
    LightOffAt = [-1, -1, -1, -1]

    def __init__(self, mosfet):
        self.Mosfet = mosfet
        self.calculateTimes()

    def status(self):
        return self.Modes

    def start(self):
        # Default all the lights to off
        self.Mosfet.allOff()
        
        lightSettings = LightSettings()
        lightSettings.load()
        self.TimeOnSetting = lightSettings.TimeOnSetting
        self.Delay0Setting = lightSettings.Delay0Setting
        self.Delay1Setting = lightSettings.Delay1Setting
        self.Delay2Setting = lightSettings.Delay2Setting
        self.Delay3Setting = lightSettings.Delay3Setting

    def convert(self, value):
        if (value == b"1"):
            return 0
        if (value == b"2"):
            return 1
        if (value == b"3"):
            return 2
        if (value == b"4"):
            return 3
        return -1

    # override normal behaviour
    def command(self, function, value):
        num = self.convert(value)
        if (function == 1):
            self.Modes[num] = 1
        if (function == 0):
            self.Modes[num] = 0
        if (function == 2):
            self.Modes[num] = 2

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
        print(lightSettings)
        lightSettings.write()

    # Prevent a number from dropping below -1
    def clampTo(self, val):
        if (val < -1):
            return -1
        return val

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
            self.Mosfet.off(Light)
        if (Mode == 1): # on
            self.Mosfet.on(Light)
        if (Mode == 2): # auto
            if (OnAt == 0): # Switch the light on, and stay on at least the TimeOn
                self.Mosfet.on(Light)
                self.LightOffAt[Light-1] = self.atLeast(self.LightOffAt[Light-1], self.TimeOn)
            if (OffAt == 0):
                self.Mosfet.off(Light)

    # Subtract 1 from all the timer calcs, dont let them go below -1
    def subtract(self, OnAt, OffAt):
        return self.clampTo(OnAt - 1), self.clampTo(OffAt - 1)


    def tick(self):
        # Main Loop
        Trigger1 = self.T1.value()
        Trigger2 = self.T2.value()

        for l in range(4):
            # If trigger 1 is set, then go upwards (connected to ground)
            if (Trigger1 == 0):
                self.LightOnAt[l] = self.atMost(self.LightOnAt[l], self.Periods[l])

            # If trigger 2 is set, then go downwards (connected to ground)
            if (Trigger2 == 0):
                self.LightOnAt[l] = self.atMost(self.LightOnAt[l], self.Periods[3-l])

            self.setLight(self.LightOnAt[l], self.LightOffAt[l], l+1, self.Modes[l])
            self.LightOnAt[l], self.LightOffAt[l] = self.subtract(self.LightOnAt[l], self.LightOffAt[l])

        # Debug output
        #print("T1=", Trigger1, "T2=", Trigger2, " - (", self.LightOnAt[0], self.LightOffAt[0], ") (", self.LightOnAt[1], self.LightOffAt[1], ") (", self.LightOnAt[2], self.LightOffAt[2], ") (", self.LightOnAt[3], self.LightOffAt[3], ")")
        #sleep(100)