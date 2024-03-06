# Main 

import neopixel, machine
from time import sleep_ms

firstpin = 16
secondPin = 17
ledCount = 120
r = 64
g = 64
b = 64
multiplier = 10

neoPixel = neopixel.NeoPixel(machine.Pin(firstpin), ledCount)

while True:

    for i in range(1,5):
        neoPixel.fill((i*multiplier,0,0))
        neoPixel.write()

    neoPixel.fill((0,0,0))
    neoPixel.write()
    sleep_ms(150)

    for i in range(1,5):
        neoPixel.fill((i*multiplier,0,0))
        neoPixel.write()

    for i in range(5,1):
        neoPixel.fill((i*multiplier,0,0))
        neoPixel.write()

    neoPixel.fill((0,0,0))
    neoPixel.write()

    sleep_ms(750)




