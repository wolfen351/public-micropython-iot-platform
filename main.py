# Main 

# Parameters
TimeOn = 6000
Delay0 = 0
Delay1 = 100
Delay2 = 300
Delay3 = 300

import gc

from d1mini_pins import PIN_D1, PIN_D3, PIN_D5, PIN_D6, PIN_D7, PIN_D8, PIN_LED

# First get and connect to the WiFi
print()
print("Starting Wifi..")
from captive_portal import CaptivePortal
portal = CaptivePortal(project="4LIGHTS")
portal.start()
del portal
gc.collect()

print()
print("Starting Web..")
from web_portal import WebPortal
web = WebPortal()
web.start();

print("Ready!")

from machine import Pin
from time import sleep

Period0 = Delay0
Period1 = Delay0 + Delay1
Period2 = Delay0 + Delay1 + Delay2
Period3 = Delay0 + Delay1 + Delay2 + Delay3
Periods = [Period0, Period1, Period2, Period3]

# Led Pin
led = Pin(PIN_LED, Pin.OUT)

# Light Pins
L1 = Pin(PIN_D5, Pin.OUT)
L2 = Pin(PIN_D6, Pin.OUT)
L3 = Pin(PIN_D7, Pin.OUT)
L4 = Pin(PIN_D8, Pin.OUT)
Lights = [L1, L2, L3, L4]

# Trigger Pins by connecting D1 or D3 to ground
T1 = Pin(PIN_D1, Pin.IN)#, Pin.PULL_UP) 
T2 = Pin(PIN_D3, Pin.IN)#, Pin.PULL_UP)

# Default all the lights to off
L1.off()
L2.off()
L3.off()
L4.off()

# When to change a light to ON
LightOnAt = [-1, -1, -1, -1]

# When to change a light to OFF
LightOffAt = [-1, -1, -1, -1]

# Prevent a number from dropping below -1
def clampTo(val):
    if (val < -1):
        return -1;
    return val;

# Make the number at most the desired value, deal with -1 
def atMost(current, desired):
    if (desired <= current):
        return desired;
    if (current == -1):
        return desired;
    return current;

# Make the number at least the desired value
def atLeast(current, desired):
    if (desired >= current):
        return desired;
    return current;

# If a timer reaches 0 then set the light on or off
def setLight(OnAt, OffAt, Light):
    if (OnAt == 0):
        Light.on()
    if (OffAt == 0):
        Light.off()

# Subtract 1 from all the timer calcs, dont let them go below -1
def subtract(OnAt, OffAt):
    return clampTo(OnAt - 1), clampTo(OffAt - 1)

while True:

    web.tick()

    # Main Loop
    Trigger1 = T1.value();
    Trigger2 = T2.value();

    for l in range(4):
        # If trigger 1 is set, then go upwards
        if (Trigger1 == 1):
            LightOnAt[l] = atMost(LightOnAt[l], Periods[l])
            LightOffAt[l] = atLeast(LightOffAt[l], Periods[3-l] + TimeOn)

        # If trigger 2 is set, then go downwards
        if (Trigger2 == 1):
            LightOnAt[l] = atMost(LightOnAt[l], Periods[3-l])
            LightOffAt[l] = atLeast(LightOffAt[l], Periods[l] + TimeOn)

        setLight(LightOnAt[l], LightOffAt[l], Lights[l])
        LightOnAt[l], LightOffAt[l] = subtract(LightOnAt[l], LightOffAt[l])

    sleep(0.1)

    # Debug output
    print("T1=", Trigger1, "T2=", Trigger2, " - (", LightOnAt[0], LightOffAt[0], ") (", LightOnAt[1], LightOffAt[1], ") (", LightOnAt[2], LightOffAt[2], ") (", LightOnAt[3], LightOffAt[3], ")")
        