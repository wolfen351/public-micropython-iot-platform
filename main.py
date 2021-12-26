# Main 
import gc
import micropython
import time

print('\nConnecting to wifi...')
import network
sta_if = network.WLAN(network.STA_IF)
t_end = time.time() + 15
sta_if.active(True)
while not sta_if.isconnected() and time.time() < t_end:
    pass
if (sta_if.isconnected()):
    print('network config:', sta_if.ifconfig())
else:
    print("No Wifi, starting portal to configure wifi")
    from captive_portal import CaptivePortal
    portal = CaptivePortal(project="4LIGHTS")
    portal.start()
    import machine
    machine.reset() # Reboot to save RAM
del t_end
del sta_if

# Import other modules needed
from d1mini_pins import PIN_LED
from machine import Pin
from light_control import LightControl
from mqtt_control import MQTTControl
from web_portal import WebPortal

print()
print("Starting LightControl..")
lights = LightControl()
lights.start();
gc.collect()

print()
print("Starting MQTT..")
mqtt = MQTTControl()
mqtt.start(lights)
gc.collect()

print()
print("Starting Web..")
web = WebPortal()
web.start(lights);
gc.collect()

print("Ready!")

led = Pin(PIN_LED, Pin.OUT)
ledOn = True

while True:
    # tick all the modules
    web.tick()
    mqtt.tick()
    lights.tick()

    # blink blue 
    ledOn = not ledOn;
    if (ledOn):
        led.on()
    else:
        led.off()

    #clean up
    gc.collect()
