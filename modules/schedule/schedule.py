from modules.basic.basic_module import BasicModule

class Schedule(BasicModule):

    def __init__(self):
        BasicModule.start(self)
        BasicModule.free(self) # release the ram

    def start(self):
        pass

    def tick(self):
        pass

    def getTelemetry(self):
        return {}

    def processTelemetry(self, telemetry):
        pass

    def getCommands(self):
        return []

    def processCommands(self, commands):
        pass

    def getRoutes(self):
        return {
            b"/schedule": b"/modules/schedule/settings.html"
        }


    def getIndexFileName(self):
        return { "schedule" : "/modules/schedule/schedule_index.html" }


    # internal code
