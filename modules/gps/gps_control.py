from machine import UART
from modules.basic.basic_module import BasicModule
from serial_log import SerialLog
from modules.gps.micropyGPS import MicropyGPS

class GPSControl(BasicModule):
    def __init__(self):
        pass

    def start(self):
        BasicModule.start(self)
        self.rxPinNumber = self.basicSettings['gps']['rxPin'] # default is 18
        self.txPinNumber = self.basicSettings['gps']['txPin'] # default is 18
        self.uart = UART(1, 9600)                         # init with given baudrate
        self.uart.init(9600, bits=8, parity=None, stop=1, tx=self.txPinNumber, rx=self.rxPinNumber) # init with given parameters
        self.myGPS = MicropyGPS()

    def tick(self):
        gpsData = self.uart.readline()     # read a line
        if (gpsData != None and len(gpsData) > 0):
            for c in gpsData.decode('ascii'): #bytes to string
                self.myGPS.update(c)
            #SerialLog.log("GPS:", gpsData, self.myGPS.latitude_string() + " " + self.myGPS.longitude_string() + " " + self.myGPS.date_string('s_dmy') + " " + str(self.myGPS.satellites_in_use))

    def getTelemetry(self):
        latdd = self.myGPS.latitude[0] + (self.myGPS.latitude[1] / 60.0)
        londd = self.myGPS.longitude[0] + (self.myGPS.longitude[1] / 60.0)
        if (self.myGPS.latitude[2] == "S"): 
            latdd = -latdd
        if (self.myGPS.longitude[2] == "W"): 
            londd = -londd

        if (latdd == 0 and londd == 0):
            return {
                "gpsdate": "%s/%s/%s" % (str(self.myGPS.date[0]),str(self.myGPS.date[1]),str(self.myGPS.date[2])),
                "gpstime": "%s:%s:%s" % (str(self.myGPS.timestamp[0]),str(self.myGPS.timestamp[1]),str(self.myGPS.timestamp[2])),
                "satellites": self.myGPS.satellites_in_use,
                "gpsaccuracy": self.myGPS.pdop
            }
        
        return { 
            "latitude": latdd,
            "longitude": londd,
            "altitude": self.myGPS.altitude,
            "gpsdate": "%s/%s/%s" % (str(self.myGPS.date[0]),str(self.myGPS.date[1]),str(self.myGPS.date[2])),
            "gpstime": "%s:%s:%s" % (str(self.myGPS.timestamp[0]),str(self.myGPS.timestamp[1]),str(self.myGPS.timestamp[2])),
            "satellites": self.myGPS.satellites_in_use,
            "course": self.myGPS.course,
            "speed": self.myGPS.speed[2],
            "gpsaccuracy": self.myGPS.pdop
        }

    def processTelemetry(self, telemetry):
        pass

    def getCommands(self):
        return []

    def processCommands(self, commands):
        pass

    def getRoutes(self):
        return { 
            b"/map" : b"/modules/gps/map.html"
        }


    def getIndexFileName(self):
        return { "gps" : "/modules/gps/gps_index.html" }