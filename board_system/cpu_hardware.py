import sys
import ujson
import machine
from serial_log import SerialLog
from machine import Pin
from time import sleep

class CpuHardware():

    statusPin = None

    def __init__(self):
        pass

    @staticmethod
    def StatusLedOn():
        if (CpuHardware.statusPin == None):
            f = open("profile.json",'r')
            settings_string=f.read()
            f.close()
            settings_dict = ujson.loads(settings_string)
            CpuHardware.statusPin = Pin(settings_dict["statusLedPin"], Pin.OUT)
        CpuHardware.statusPin.on()

    @staticmethod
    def StatusLedOff():
        CpuHardware.statusPin.off()

    @staticmethod
    def SetCpuMaxSpeed():
        f = open("profile.json",'r')
        settings_string=f.read()
        f.close()
        settings_dict = ujson.loads(settings_string)

        try: 
            SerialLog.log("CPU ", machine.freq() / 1000000, "Mhz (nominal)")
            SerialLog.log("CPU ", settings_dict["cpuSpeed"] / 1000000, "Mhz (accel)")
            machine.freq(settings_dict["cpuSpeed"]) 
        except Exception as e:
            sys.print_exception(e)
            SerialLog.log("Error! Failed to set cpu speed")

    @staticmethod
    def SetCpuLowSpeed():
        try: 
            SerialLog.log("CPU ", machine.freq() / 1000000, "Mhz (nominal)")
            SerialLog.log("CPU 40 Mhz (low)")
            machine.freq(40000000) 
        except Exception as e:
            sys.print_exception(e)
            SerialLog.log("Error! Failed to set cpu speed")

    @staticmethod
    def lightSleep(timeToNapInMs):
        SerialLog.log("Going to sleep for", timeToNapInMs, "ms...")
        # lights out
        led = Pin(3, Pin.OUT)
        led.off()
        SerialLog.log("Zzz")
        sleep(0.2)
        if (timeToNapInMs-200 > 0):
            machine.lightsleep(timeToNapInMs-200) # Sleep to save power 
        SerialLog.log("Woke up..")
    
    @staticmethod
    def printResetCause():
        resetCause = machine.reset_cause()
        if resetCause == 0:
            SerialLog.log("Boot: Power on")
        elif resetCause == 1:
            SerialLog.log("Boot: External reset")
        elif resetCause == 2:
            SerialLog.log("Boot: Watchdog reset")
        elif resetCause == 3:
            SerialLog.log("Boot: Exception reset")
        elif resetCause == 4:
            SerialLog.log("Boot: Deep sleep wakeup")
        elif resetCause == 5:
            SerialLog.log("Boot: Software reset")
        elif resetCause == 6:
            SerialLog.log("Boot: RTC wakeup")
        elif resetCause == 7:
            SerialLog.log("Boot: Timer wakeup")
        elif resetCause == 8:
            SerialLog.log("Boot: Unknown")
        else:
            SerialLog.log("Boot: Unknown (%d)" % resetCause)


    def printVersion():
        import os
        # Get the version of the board
        board = os.uname().machine
        SerialLog.log(board)
        version = os.uname().version
        SerialLog.log("Micropython:", version)
        # Get the version of the micropython
        with open('version', 'r') as f:
            local_version = f.read().strip() 
            SerialLog("App Version:", local_version)
