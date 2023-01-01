from modules.basic.basic_module import BasicModule
 
# Screen is 320x240 px
# X is left to right on the small side (0-240)
# Y is up to down on the long side (0-320)

class TempHistory(BasicModule):

    def __init__(self):
        pass


    def start(self):
        pass

    def tick(self):
        pass

    def getTelemetry(self):
        telemetry = {
        }
        return telemetry

    def processTelemetry(self, telemetry):
        pass

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

