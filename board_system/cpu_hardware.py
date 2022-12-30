import machine
from serial_log import SerialLog

class CpuHardware():

    def __init__(self):
        pass;

    def SetCpuMaxSpeed():
        SerialLog.log("CPU 40Mhz")
        machine.freq(40000000) 

