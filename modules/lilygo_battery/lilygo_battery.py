from board_system.cpu_hardware import CpuHardware
from machine import Pin, ADC
import network
import time

from serial_log import SerialLog

class LilyGoBattery:

    loopcount = 0
    voltage = 0
    voltagePercent = 0
    lastBatteryCheck = 0
    bootTime = 0

    def __init__(self):
        pass

    def start(self):
        self.pot = ADC(Pin(2))
        self.pot.atten(ADC.ATTN_11DB)       #Full range: 3.3v
        self.sta_if = network.WLAN(network.STA_IF)
        self.ap_if = network.WLAN(network.AP_IF)
        self.bootTime = time.ticks_ms()
        self.lastSleepTime = 0

    def tick(self):
        currentTime = time.ticks_ms()
        self.loopcount += 1

        uptimeMs = time.ticks_diff(currentTime, self.bootTime)
        hasBeenRunningForMoreThan2Mins = uptimeMs > 120000
        wifiConnected = self.sta_if.isconnected()
        timeSinceLastSleepMs = time.ticks_diff(currentTime, self.lastSleepTime)
        apRunning = self.ap_if.active()

        # stay awake for 10s every 10min
        if (timeSinceLastSleepMs > 10000 and not wifiConnected and not apRunning and hasBeenRunningForMoreThan2Mins):
            CpuHardware.lightSleep(600000) # sleep for 10min

        # check battery voltage every 5s
        diff = time.ticks_diff(currentTime, self.lastBatteryCheck)
        if (diff > 5000):
            pot_value = self.pot.read()
            self.voltage = pot_value * 2 / 1000
            self.voltagePercent = round(((pot_value * 2) / 5842) * 100)
            self.lastBatteryCheck = time.ticks_ms()

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