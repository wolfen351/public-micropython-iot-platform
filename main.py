# Main 

import gc
from time import sleep
from d1mini_pins import PIN_LED
from machine import Pin

# First get and connect to the WiFi
print()
print("Starting Wifi..")
from captive_portal import CaptivePortal
portal = CaptivePortal(project="4LIGHTS")
portal.start()
del portal
gc.collect()

print()
print("Starting LightControl..")
from light_control import LightControl
lights = LightControl()
lights.start();

print()
print("Starting Web..")
from web_portal import WebPortal
web = WebPortal()
web.start(lights);

print("Ready!")

led = Pin(PIN_LED, Pin.OUT)

while True:
    web.tick()
    lights.tick();

    led.on()
    sleep(0.1)
    led.off()
