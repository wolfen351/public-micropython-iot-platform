from basic_module import BasicModule
import ds18x20, onewire, machine
from serial_log import SerialLog
import time
from web_processor import okayHeader
import ubinascii

class TempMonitor(BasicModule):

    lastTemp = {}
    lastConvert = 0

    def __init__(self, basicSettings):
        pass

    def start(self):
        self.ds_pin = machine.Pin(18)
        self.ds_sensor = ds18x20.DS18X20(onewire.OneWire(self.ds_pin))
        self.roms = self.ds_sensor.scan()
        SerialLog.log('Found DS devices: ', self.roms)
        self.ds_sensor.convert_temp()
        self.lastConvert = time.ticks_ms()
        for rom in self.roms:
            self.lastTemp[str(rom)] = -127

    def tick(self):
        currentTime = time.ticks_ms()
        diff = time.ticks_diff(currentTime, self.lastConvert)
        if (diff > 750): 
            for rom in self.roms:
                current = self.ds_sensor.read_temp(rom)
                if (current != self.lastTemp[str(rom)]):
                    self.lastTemp[str(rom)] = current
                    SerialLog.log("%s = %s*C" % (ubinascii.hexlify(rom).decode('ascii'), current))
            self.ds_sensor.convert_temp()
            self.lastConvert = time.ticks_ms()

    def getTelemetry(self):
        telemetry = {}
        for rom in self.roms:
            sensorName = "temperature/%s" % (ubinascii.hexlify(rom).decode('ascii'))
            current = self.lastTemp[str(rom)]
            telemetry.update({sensorName:current})
        return telemetry

    def processTelemetry(self, telemetry):
        pass

    def getCommands(self):
        return []

    def processCommands(self, commands):
        pass

    def getRoutes(self):
        return {
            b"/temp": self.gettemp,
        }

    # Internal code here
    def currentTemp(self):
        return self.lastTemp

    def gettemp(self, params):
        tempVal = self.currentTemp()
        headers = okayHeader
        data = b"{ \"temp\": %s }" % (tempVal)
        return data, headers            
