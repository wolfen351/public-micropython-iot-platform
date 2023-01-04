from board_system.cpu_hardware import CpuHardware
from machine import Pin, ADC
import machine
from serial_log import SerialLog
import network

class LilyGoBattery:

    loopcount = 0
    voltagePercent = 100

    def __init__(self):
        pass

    def start(self):
        self.pot = ADC(Pin(2))
        self.pot.atten(ADC.ATTN_11DB)       #Full range: 3.3v
        self.sta_if = network.WLAN(network.STA_IF)

    def tick(self):
        if (not self.sta_if.isconnected() or self.voltagePercent < 95): # no wifi, or battery is discharging, so enable sleep
            self.loopcount += 1
            if (self.loopcount > 400 and (self.loopcount % 100) == 0):
                CpuHardware.lightSleep(600000) # sleep for 10min
                #machine.deepsleep(60000)

    def getTelemetry(self):

        pot_value = self.pot.read()
        self.voltagePercent = round(((pot_value * 2) / 5842) * 100)

        return { 
            "voltage": pot_value * 2 / 1000,
            "voltagePercent": self.voltagePercent
        }

    def processTelemetry(self, telemetry):
        pass

    def getCommands(self):
        return []

    def processCommands(self, commands):
        pass

    def getRoutes(self):
        return { }


    def getIndexFileName(self):
        return {  }