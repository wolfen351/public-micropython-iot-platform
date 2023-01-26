from modules.basic.basic_module import BasicModule
from machine import Pin
import ds18x20, onewire
from serial_log import SerialLog
import time
from modules.web.web_processor import okayHeader
import ubinascii
from json import dumps

class DS18B20Temp(BasicModule):

    lastTemp = {}
    lastConvert = 0

    def __init__(self):
        pass

    def start(self):
        BasicModule.start(self)

        self.pinNumber = self.basicSettings['ds18b20']['pin'] # default is 18
        self.readEveryMs = self.basicSettings['ds18b20']['readEveryMs'] # default is 1000
        SerialLog.log("Configured to look for ds18b20 on pin: ", self.pinNumber)
        self.ds_pin = Pin(self.pinNumber, Pin.IN, Pin.PULL_UP)
        self.ds_sensor = ds18x20.DS18X20(onewire.OneWire(self.ds_pin))
        self.roms = self.ds_sensor.scan()
        SerialLog.log('Found DS devices: ', self.roms)
        if (len(self.roms) > 0):
            self.ds_sensor.convert_temp()
            self.lastConvert = time.ticks_ms()
            for rom in self.roms:
                self.lastTemp[str(rom)] = -127

    def tick(self):
        if (len(self.roms) > 0):
            currentTime = time.ticks_ms()
            diff = time.ticks_diff(currentTime, self.lastConvert)
            if (diff > self.readEveryMs and diff > 750): 
                for rom in self.roms:
                    current = self.ds_sensor.read_temp(rom)
                    if (current != self.lastTemp[str(rom)]):
                        self.lastTemp[str(rom)] = current
                        SerialLog.log("%s = %s'C" % (ubinascii.hexlify(rom).decode('ascii'), current))
                self.ds_sensor.convert_temp()
                self.lastConvert = time.ticks_ms()

    def getTelemetry(self): 
        telemetry = {"tempReadAt": self.lastConvert}
        for rom in self.roms:
            sensorName = "temperature/%s" % (ubinascii.hexlify(rom).decode('ascii'))
            current = self.lastTemp[str(rom)]
            if (current != -127):
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

    def getIndexFileName(self):
        return { "temp" : "/modules/ds18b20temp/ds18b20_temp_index.html" }

    # Internal code here
    def currentTemp(self):
        return self.lastTemp

    def gettemp(self, params):
        telemetry = self.getTelemetry()
        del telemetry['tempReadAt']
        headers = okayHeader
        data = dumps(telemetry)
        return data, headers            
