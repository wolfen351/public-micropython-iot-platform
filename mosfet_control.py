from machine import Pin

class MosfetControl:
    # Switch Pins
    S1 = Pin(12, Pin.OUT)
    S2 = Pin(11, Pin.OUT)
    S3 = Pin(9, Pin.OUT)
    S4 = Pin(7, Pin.OUT)
    Switches = [S1, S2, S3, S4]

    # Actual of the lights (0=Off, 1=On)
    States = [0, 0, 0, 0]

    def status(self):
        return self.States

    def start(self):
        # Default all the switches to off
        self.S1.off()
        self.S2.off()
        self.S3.off()
        self.S4.off()

    def allOn(self): # num is 1-4, but arrays are 0-3
        for num in range(4):
            self.States[num] = 1
            self.Switches[num].on()

    def allOff(self): # num is 1-4, but arrays are 0-3
        for num in range(4):
            self.States[num] = 0
            self.Switches[num].off()
            
    def on(self, num): # num is 1-4, but arrays are 0-3
        self.States[num - 1] = 1
        self.Switches[num -1].on()

    def off(self, num): # num is 1-4, but arrays are 0-3
        self.States[num - 1] = 0
        self.Switches[num -1].off()

    def flip(self, num): # num is 1-4, but arrays are 0-3
        if (self.States[num - 1] == 0):
            self.on(self.num)
        else:
            self.off(self.num)

    def command(self, num, onOff): # num is 1-4, OnOff=0 for off and 1 for on
        if (onOff == 0): 
            self.off(num)
        if (onOff == 1): 
            self.on(num)

    def tick(self):
        # Do what is needed each tick
        pass
