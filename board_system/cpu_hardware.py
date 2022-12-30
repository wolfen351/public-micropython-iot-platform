import sys
import ujson
import machine
from serial_log import SerialLog

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
            SerialLog.log("CPU ", settings_dict["cpu_speed"] / 1000000, "Mhz")
            machine.freq(settings_dict["cpu_speed"]) 
        except Exception as e:
            sys.print_exception(e)
            SerialLog.log("Error! Failed to set cpu speed")


