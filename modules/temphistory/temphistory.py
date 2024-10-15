import json
from modules.basic.basic_module import BasicModule
from modules.web.web_processor import okayHeader
from serial_log import SerialLog
import ujson

class TempHistory(BasicModule):

    def __init__(self):
        pass

    def start(self):
        self.historyYesterday = [None for i in range(24)]
        self.historyToday = [None for i in range(24)]
        self.historyMonth = [None for i in range(32)]
        self.min = 200
        self.max = -200
        self.count = 0
        self.sum = 0
        self.daymin = 200
        self.daymax = -200
        self.daycount = 0
        self.daysum = 0
        self.currentHour = -1
        self.currentDay = -1
        self.currentMonth = -1
        self.lastRead = 0 # last time we got fresh temp data

        self.loadHistoryFromDisk()

    def tick(self):
        pass

    def getTelemetry(self):
        if (self.count == 0):
            return {}
        
        telemetry = {
            'tempmin': self.min,
            'tempmax': self.max,
            'tempavg': (self.sum / self.count) if self.count > 0 else 0,
            'tempcount': self.count,

            'daymin': self.daymin,
            'daymax': self.daymax,
            'dayavg': (self.daysum / self.daycount) if self.daycount > 0 else 0,
            'daycount': self.daycount
        }
        return telemetry

    def processTelemetry(self, telemetry):

        # skip if we dont have time
        if (not "time" in telemetry):
            return

        if (telemetry["time"][0] == 2000): # exclude when we dont have ntp time (year 2000)
            return

        if (not "tempReadAt" in telemetry): # quit if we havent read a temp
            return

        if (telemetry["tempReadAt"] == self.lastRead): # only cycle if we have freesh data
            return

        self.lastRead = telemetry["tempReadAt"]

        for attr, value in telemetry.items():
            if (attr.startswith('temperature')):
                if (value != -127): # exclude unknown value
                    self.count +=1
                    self.daycount += 1
                    self.sum += value
                    self.daysum += value
                    if (self.min > value): 
                        self.min = value
                    if (self.max < value):
                        self.max = value
                    if (self.daymin > value): 
                        self.daymin = value
                    if (self.daymax < value):
                        self.daymax = value

            if (attr == "time"):
                hour = value[3]
                day = value[2]
                month = value[1]

                # reset counters every month
                if (self.currentMonth != month):
                    self.historyMonth = [None for i in range(32)]
                    self.currentMonth = month

                # reset counters every day
                if (self.currentDay != day):
                    self.historyYesterday = self.historyToday
                    self.historyToday = [None for i in range(24)]
                    self.daymin = 200
                    self.daymax = -200
                    self.daycount = 0
                    self.daysum = 0
                    self.currentDay = day

                # reset counters every hour
                if (self.currentHour != hour):
                    self.saveHistoryToDisk()
                    self.min = 200
                    self.max = -200
                    self.count = 0
                    self.sum = 0
                    self.currentHour = hour

                # update current hour
                if (self.count > 0):
                    self.historyToday[self.currentHour] = {
                        "min": self.min,
                        "max": self.max,
                        "count": self.count,
                        "sum": self.sum
                    }

                # update current day
                if (self.daycount > 0):
                    self.historyMonth[self.currentDay] = {
                        "min": self.daymin,
                        "max": self.daymax,
                        "count": self.daycount,
                        "sum": self.daysum
                    }

    def getCommands(self):
        return []

    def processCommands(self, commands):
        pass

    def getRoutes(self):
        return {
            b"/temphistory": b"/modules/temphistory/history.html",
            b"/temphistorydetailtoday": self.tempHistoryDetailToday,
            b"/temphistorydetailyesterday": self.tempHistoryDetailYesterday,
            b"/temphistorydetailmonth": self.tempHistoryDetailMonth
        }

    def tempHistoryDetailToday(self, params):
        headers = okayHeader
        data = json.dumps(self.historyToday)
        return data, headers  

    def tempHistoryDetailYesterday(self, params):
        headers = okayHeader
        data = json.dumps(self.historyYesterday)
        return data, headers  

    def tempHistoryDetailMonth(self, params):
        headers = okayHeader
        data = json.dumps(self.historyMonth)
        return data, headers  

    def getIndexFileName(self):
        return {"temphistory": "/modules/temphistory/index.html"}
               
    # Internal code here
    def loadHistoryFromDisk(self):
        try:
            f = open("temphistory.json",'r')
            self.historyYesterday = ujson.loads(f.readline())
            self.historyToday = ujson.loads(f.readline())
            self.historyMonth = ujson.loads(f.readline())
            self.currentHour = ujson.loads(f.readline())
            self.currentDay = ujson.loads(f.readline())
            self.currentMonth = ujson.loads(f.readline())
            self.min = ujson.loads(f.readline())
            self.max = ujson.loads(f.readline())
            self.count = ujson.loads(f.readline())
            self.sum = ujson.loads(f.readline())
            self.daymin = ujson.loads(f.readline())
            self.daymax = ujson.loads(f.readline())
            self.daycount = ujson.loads(f.readline())
            self.daysum = ujson.loads(f.readline())
            f.close()
            SerialLog.log("Temp history loaded from disk")
        except Exception as e:
            SerialLog.log("Error: Unable to load history from disk.", e)

    def saveHistoryToDisk(self):
        f = open("temphistory.json", "w")
        f.write(ujson.dumps(self.historyYesterday))        
        f.write('\n')
        f.write(ujson.dumps(self.historyToday))
        f.write('\n')
        f.write(ujson.dumps(self.historyMonth))
        f.write('\n')
        f.write(ujson.dumps(self.currentHour))
        f.write('\n')
        f.write(ujson.dumps(self.currentDay))
        f.write('\n')
        f.write(ujson.dumps(self.currentMonth))
        f.write('\n')
        f.write(ujson.dumps(self.min))
        f.write('\n')
        f.write(ujson.dumps(self.max))
        f.write('\n')
        f.write(ujson.dumps(self.count))
        f.write('\n')
        f.write(ujson.dumps(self.sum))
        f.write('\n')
        f.write(ujson.dumps(self.daymin))
        f.write('\n')
        f.write(ujson.dumps(self.daymax))
        f.write('\n')
        f.write(ujson.dumps(self.daycount))
        f.write('\n')
        f.write(ujson.dumps(self.daysum))
        f.write('\n')
        f.close()

