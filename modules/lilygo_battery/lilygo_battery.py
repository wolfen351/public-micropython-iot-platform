from board_system.cpu_hardware import CpuHardware
from machine import Pin, ADC, reset
from time import ticks_ms, ticks_diff

from serial_log import SerialLog

class LilyGoBattery:

    voltage = 0
    voltagePercent = 0
    lastBatteryCheck = 0
    bootTime = 0

    def __init__(self):
        pass

    def start(self):
        self.pot = ADC(Pin(2))
        self.pot.atten(ADC.ATTN_11DB)       #Full range: 3.3v
        self.bootTime = ticks_ms()
        self.lastSleepTime = 0

    def tick(self):
        currentTime = ticks_ms()

        uptimeMs = ticks_diff(currentTime, self.bootTime)
        hasBeenRunningForMoreThan2Mins = uptimeMs > 120000
        timeSinceLastSleepMs = ticks_diff(currentTime, self.lastSleepTime)

        # If it has been up for more than 1h then reboot
        if (uptimeMs > 3600000):
            reset()

        # check battery voltage every 5s
        diff = ticks_diff(currentTime, self.lastBatteryCheck)
        if (diff > 5000):
            pot_value = self.pot.read()
            self.voltage = pot_value * 2 / 1000
            self.voltagePercent = round(((pot_value * 2) / 5842) * 100)
            self.lastBatteryCheck = ticks_ms()
            SerialLog.log("Battery voltage: %s (%s%%)" % (self.voltage, self.voltagePercent))

        # stay awake for 10s every 10min
        if (timeSinceLastSleepMs > 10000 and hasBeenRunningForMoreThan2Mins and self.voltagePercent < 90):
            self.lastSleepTime = ticks_ms()
            CpuHardware.lightSleep(600000) # sleep for 10min

    def getTelemetry(self):
        return { 
            "voltage": self.voltage,
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