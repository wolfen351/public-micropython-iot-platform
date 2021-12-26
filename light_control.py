from d1mini_pins import PIN_D1, PIN_D3, PIN_D5, PIN_D6, PIN_D7, PIN_D8
from machine import Pin

class LightControl:
    # Parameters
    TimeOn = 6000
    Delay0 = 0
    Delay1 = 100
    Delay2 = 300
    Delay3 = 300

    # Periods
    Period0 = Delay0
    Period1 = Delay0 + Delay1
    Period2 = Delay0 + Delay1 + Delay2
    Period3 = Delay0 + Delay1 + Delay2 + Delay3
    Periods = [Period0, Period1, Period2, Period3]

    # Light Pins
    L1 = Pin(PIN_D5, Pin.OUT)
    L2 = Pin(PIN_D6, Pin.OUT)
    L3 = Pin(PIN_D7, Pin.OUT)
    L4 = Pin(PIN_D8, Pin.OUT)
    Lights = [L1, L2, L3, L4]

    # Trigger Pins by connecting D1 or D3 to ground
    T1 = Pin(PIN_D1, Pin.IN)#, Pin.PULL_UP) 
    T2 = Pin(PIN_D3, Pin.IN)#, Pin.PULL_UP)

    # When to change a light to ON
    LightOnAt = [-1, -1, -1, -1]

    # When to change a light to OFF
    LightOffAt = [-1, -1, -1, -1]

    def __init__(self):
        print("Setting up light control")

    def start(self):
        # Default all the lights to off
        self.L1.off()
        self.L2.off()
        self.L3.off()
        self.L4.off()
        print("LightControl ready!")

    def command(self, name, value):
        if (name == "switchLight"):
            self.L1.off()

    # Prevent a number from dropping below -1
    def clampTo(self, val):
        if (val < -1):
            return -1;
        return val;

    # Make the number at most the desired value, deal with -1 
    def atMost(self, current, desired):
        if (desired <= current):
            return desired;
        if (current == -1):
            return desired;
        return current;

    # Make the number at least the desired value
    def atLeast(self, current, desired):
        if (desired >= current):
            return desired;
        return current;

    # If a timer reaches 0 then set the light on or off
    def setLight(self, OnAt, OffAt, Light):
        if (OnAt == 0):
            Light.on()
        if (OffAt == 0):
            Light.off()

    # Subtract 1 from all the timer calcs, dont let them go below -1
    def subtract(self, OnAt, OffAt):
        return self.clampTo(OnAt - 1), self.clampTo(OffAt - 1)


    def tick(self):
        # Main Loop
        Trigger1 = self.T1.value();
        Trigger2 = self.T2.value();

        for l in range(4):
            # If trigger 1 is set, then go upwards
            if (Trigger1 == 1):
                self.LightOnAt[l] = self.atMost(self.LightOnAt[l], self.Periods[l])
                self.LightOffAt[l] = self.atLeast(self.LightOffAt[l], self.Periods[3-l] + self.TimeOn)

            # If trigger 2 is set, then go downwards
            if (Trigger2 == 1):
                self.LightOnAt[l] = self.atMost(self.LightOnAt[l], self.Periods[3-l])
                self.LightOffAt[l] = self.atLeast(self.LightOffAt[l], self.Periods[l] + self.TimeOn)

            self.setLight(self.LightOnAt[l], self.LightOffAt[l], self.Lights[l])
            self.LightOnAt[l], self.LightOffAt[l] = self.subtract(self.LightOnAt[l], self.LightOffAt[l])

        # Debug output
        print("T1=", Trigger1, "T2=", Trigger2, " - (", self.LightOnAt[0], self.LightOffAt[0], ") (", self.LightOnAt[1], self.LightOffAt[1], ") (", self.LightOnAt[2], self.LightOffAt[2], ") (", self.LightOnAt[3], self.LightOffAt[3], ")")
