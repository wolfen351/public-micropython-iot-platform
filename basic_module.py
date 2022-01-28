class BasicModule:
    def __init__(self):
        pass

    def start(self):
        pass

    def tick(self):
        pass

    def getTelemetry(self):
        return {}

    def getCommands(self):
        return []

    def processCommands(self, command, parameters):
        pass

    def processTelemetry(self, telemetry):
        pass

