import ujson

class BasicModule:

    def __init__(self):
        self.basicSettings = {}

    def start(self):
        f = open("profile.json",'r')
        settings_string=f.read()
        f.close()
        self.basicSettings = ujson.loads(settings_string)

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
        return {}

    def getIndexFileName(self):
        return { }