from modules.basic.basic_module import BasicModule
from web.web_processor import okayHeader, unquote

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
            b"/schedule": b"/modules/schedule/settings.html",
            b"/scheduleloadsettings": self.loadschedulesettings,
            b"/schedulesavesettings": self.saveschedulesettings
        }

    def getIndexFileName(self):
        return { "schedule" : "/modules/schedule/schedule_index.html" }


    # internal code
    def loadschedulesettings(self, params):

        bootcommand = self.getPref("schedule", "bootcommand", "/somecommand")
        delaycommand = self.getPref("schedule", "delaycommand", "/somecommand")
        delayseconds = self.getPref("schedule", "delayseconds", "300")

        headers = okayHeader
        data = b"{ \"bootcommand\": \"%s\", \"delaycommand\": \"%s\", \"delayseconds\": \"%s\" }" % (bootcommand, delaycommand, delayseconds)
        return data, headers
    
    def saveschedulesettings(self, params):
        # Read form params
        self.setPref("schedule", "bootcommand", unquote(params.get(b"bootcommand", None)))
        self.setPref("schedule", "delaycommand", unquote(params.get(b"delaycommand", None)))
        self.setPref("schedule", "delayseconds", unquote(params.get(b"delayseconds", None)))

        headers = b"HTTP/1.1 307 Temporary Redirect\r\nLocation: /\r\n"

        return b"", headers, True