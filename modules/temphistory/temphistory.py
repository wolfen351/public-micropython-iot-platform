from modules.basic.basic_module import BasicModule

class TempHistory(BasicModule):

    historyData = [None for i in range(24)]
    min = 200
    max = -200
    count = 0
    sum = 0
    currentHour = -1

    def __init__(self):
        pass


    def start(self):
        pass

    def tick(self):
        pass

    def getTelemetry(self):
        telemetry = {
            'tempmin': self.min,
            'tempmax': self.max,
            'tempavg': (self.sum / self.count) if self.count > 0 else 0,
            'tempcount': self.count,
            'temphistory': self.historyData
        }
        return telemetry

    def processTelemetry(self, telemetry):
        # make sure these is a node for each sensor
        for attr, value in telemetry.items():
            if (attr.startswith('temperature')):
                if (value != -127): # exclude unknown value
                    self.count +=1
                    self.sum += value
                    if (self.min > value): 
                        self.min = value
                    if (self.max < value):
                        self.max = value
            if (attr == "time"):
                hour = value[3]
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
            b"/temphistory": b"/modules/temphistory/temphistory_display.html"
        }

    def getIndexFileName(self):
        return {"temphistory": "/modules/temphistory/temphistory_index.html"}
               
    # Internal code here

