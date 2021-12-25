# This file is executed on every boot (including wake-boot from deepsleep)

from time import sleep

from d1mini_pins import PIN_LED
from machine import Pin

ledPin = Pin(PIN_LED)
for r in range(5):
    ledPin.on()
    sleep(0.2)
    ledPin.off()


