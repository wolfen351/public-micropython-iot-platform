import ujson
from os import listdir

from serial_log import SerialLog

class BasicModule:

    def __init__(self):
        self.basicSettings = {}

    def start(self):
        f = open("profile.json",'r')
        settings_string=f.read()
        f.close()
        self.basicSettings = ujson.loads(settings_string)

        if not "prefs.json" in listdir(): 
            SerialLog.log("No prefs.json file found. Making a new one")
            f = open("prefs.json", "w")
            f.write("{}")
            f.close()

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

    #internal code

    # Returns the preference if possible, otherwise the default
    def getPref(self, node, setting, default):
        f = open("prefs.json",'r')
        settings_string=f.read()
        f.close()
        prefs = ujson.loads(settings_string)

        if (node not in prefs):
            return default

        pref = prefs[node]
        if (setting not in pref):
            return default

        return pref[setting]

    def setPref(self, node, setting, value):
        f = open("prefs.json",'r')
        settings_string=f.read()
        f.close()
        prefs = ujson.loads(settings_string)

        if (node not in prefs):
            prefs.update({node: {setting: value}})

        pref = prefs[node]
        if (setting not in pref):
            pref.update({setting: value})

        data = ujson.dumps(prefs)
        SerialLog.log("New prefs.json: ", data)

        f = open("prefs.json", "w")
        f.write(data)
        f.close()