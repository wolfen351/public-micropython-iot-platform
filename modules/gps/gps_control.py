from machine import UART
from serial_log import SerialLog
from modules.gps.micropyGPS import MicropyGPS

class GPSControl:
    def __init__(self, basicSettings):
        self.uart = UART(1, 9600)                         # init with given baudrate
        self.uart.init(9600, bits=8, parity=None, stop=1, tx=33, rx=35) # init with given parameters
        self.myGPS = MicropyGPS()

    def start(self):
        pass

    def tick(self):
        gpsData = self.uart.readline()     # read a line
        if (gpsData != None):
            for c in gpsData.decode('ascii'): #bytes to string
                self.myGPS.update(c)
            SerialLog.log("GPS:", gpsData, self.myGPS.latitude_string() + " " + self.myGPS.longitude_string() + " " + self.myGPS.date_string('s_dmy') + " " + str(self.myGPS.satellites_in_use))

    def getTelemetry(self):
        return {}

    def processTelemetry(self, telemetry):
        pass

    def getCommands(self):
        return []

    def processCommands(self, commands):
        pass

    def getRoutes(self):
        return {}

    def getIndexFileName(self):
        return { }