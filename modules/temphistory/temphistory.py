import json
from modules.basic.basic_module import BasicModule
from modules.web.web_processor import okayHeader

class TempHistory(BasicModule):

    def __init__(self):
        pass


    def start(self):
        self.historyData = [None for i in range(24)]
        self.historyDataDay = [None for i in range(31)]
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

    def tick(self):
        pass

    def getTelemetry(self):
        telemetry = {
            'tempmin': self.min,
            'tempmax': self.max,
            'tempavg': (self.sum / self.count) if self.count > 0 else 0,
            'tempcount': self.count,

            'daymin': self.daymin,
            'daymax': self.daymax,
            'dayavg': (self.daysum / self.daycount) if self.daycount > 0 else 0,
            'daycount': self.daycount,
        }
        return telemetry

    def processTelemetry(self, telemetry):
        # make sure these is a node for each sensor
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
                # reset counters every day
                if (self.currentDay != day):
                    self.historyDataDay[self.currentDay] = {
                        "min": self.daymin,
                        "max": self.daymax,
                        "count": self.daycount,
                        "sum": self.daysum
                    }

                    self.daymin = 200
                    self.daymax = -200
                    self.daycount = 0
                    self.daysum = 0
                    self.currentDay = day

                # reset counters every hour
                if (self.currentHour != hour):

                    self.historyData[self.currentHour] = {
                        "min": self.min,
                        "max": self.max,
                        "count": self.count,
                        "sum": self.sum
                    }
                    self.min = 200
                    self.max = -200
                    self.count = 0
                    self.sum = 0
                    self.currentHour = hour


    def getCommands(self):
        return []

    def processCommands(self, commands):
        pass

    def getRoutes(self):
        return {
            b"/temphistory": b"/modules/temphistory/temphistory_display.html",
            b"/temphistorydetail": self.tempHistoryDetail
        }

    def tempHistoryDetail(self, params):
        headers = okayHeader
        data = b""

        telemetry = {
            'tempmin': self.min,
            'tempmax': self.max,
            'tempavg': (self.sum / self.count) if self.count > 0 else 0,
            'tempcount': self.count,
            'temphistory': self.historyData,
            'temphistoryMonth': self.historyDataDay
        }

        data = json.dumps(telemetry)
        return data, headers  

    def getIndexFileName(self):
        return {"temphistory": "/modules/temphistory/temphistory_index.html"}
               
    # Internal code here

