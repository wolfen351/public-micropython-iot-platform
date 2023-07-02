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
    roms = []
    lastScan = 0

    def __init__(self):
        pass

    def start(self):
        BasicModule.start(self)

        self.pinNumber = self.basicSettings['ds18b20']['pin'] # default is 18
        self.readEveryMs = self.basicSettings['ds18b20']['readEveryMs'] # default is 1000
        SerialLog.log("Configured to look for ds18b20 on pin: ", self.pinNumber)
        self.ds_pin = Pin(self.pinNumber, Pin.IN, Pin.PULL_UP)
        self.ds_sensor = ds18x20.DS18X20(onewire.OneWire(self.ds_pin))
        time.sleep(0.5)
        self.roms = self.getSensors()
        self.lastScan = time.ticks_ms()

        if (len(self.roms) > 0):
            self.ds_sensor.convert_temp()
            self.lastConvert = time.ticks_ms()

    def tick(self):
        # Try every 5s to get any connected sensors
        if (len(self.roms) == 0 and self.lastScan + 5000 < time.ticks_ms()):
            self.roms = self.getSensors(1)
            self.lastScan = time.ticks_ms()

        if (len(self.roms) > 0):
            currentTime = time.ticks_ms()
            diff = time.ticks_diff(currentTime, self.lastConvert)
            if (diff > self.readEveryMs and diff > 750): 
                for rom in self.roms:
                    current = self.ds_sensor.read_temp(rom)
                    SerialLog.log("%s = %s'C" % (ubinascii.hexlify(rom).decode('ascii'), current))
                    if (current != self.lastTemp[str(rom)]):
                        self.lastTemp[str(rom)] = current
                self.ds_sensor.convert_temp()
                self.lastConvert = time.ticks_ms()

    def getTelemetry(self): 
        telemetry = {"tempReadAt": self.lastConvert}
        for rom in self.roms:
            sensorName = "temperature/%s" % (ubinascii.hexlify(rom).decode('ascii'))

            # make sure we have a last temp for this sensor
            if self.lastTemp.get(str(rom)) is None:
                self.lastTemp[str(rom)] = -127

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
    
    def getSensors(self, tries=5):
        # try again if no devices found
        attempt = 0
        while (len(self.roms) == 0 and attempt < tries):
            SerialLog.log('No devices found. Trying again...')
            self.roms = self.ds_sensor.scan()
            time.sleep(0.5)
            SerialLog.log('Found DS devices: ', self.roms)
            attempt += 1
        return self.roms
