import sys
import ujson
import machine
from serial_log import SerialLog
from machine import Pin

class CpuHardware():

    def __init__(self):
        pass

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
        SerialLog.log("Going to sleep..")
        # lights out
        led = Pin(3, Pin.OUT)
        led.off()
        machine.lightsleep(timeToNapInMs) # Sleep for 10 min to save power 
        SerialLog.log("Woke up..")

