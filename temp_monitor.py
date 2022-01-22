import ds18x20, onewire, machine
from serial_log import SerialLog
import time

class TempMonitor():

    lastTemp = 0
    lastConvert = 0

    def __init__(self):
        pass

    def start(self):
        self.ds_pin = machine.Pin(18)
        self.ds_sensor = ds18x20.DS18X20(onewire.OneWire(self.ds_pin))
        self.roms = self.ds_sensor.scan()
        SerialLog.log('Found DS devices: ', self.roms)
        self.ds_sensor.convert_temp()
        self.lastConvert = time.ticks_ms()

    def currentTemp(self):
        return self.lastTemp

    def tick(self):
        currentTime = time.ticks_ms()
        diff = time.ticks_diff(currentTime, self.lastConvert)
        if (diff > 750): 
            for rom in self.roms:
                current = self.ds_sensor.read_temp(rom)
                if (current != self.lastTemp):
                    self.lastTemp = current
                    SerialLog.log("%s*C" % current)
            self.ds_sensor.convert_temp()
            self.lastConvert = time.ticks_ms()
            
