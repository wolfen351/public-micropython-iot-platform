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
        self.ensurePrefsExists()

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
    def ensurePrefsExists(self):
        if not "prefs.json" in listdir(): 
            SerialLog.log("No prefs.json file found. Making a new one")
            f = open("prefs.json", "w")
            f.write("{}")
            f.close()


    # Returns the preference if possible, otherwise the default
    def getPref(self, node, setting, default):
        self.ensurePrefsExists()

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

    def setPref(self, sectionName, settingName, value):
        self.ensurePrefsExists()

        f = open("prefs.json",'r')
        settings_string=f.read()
        f.close()
        fullDoc = ujson.loads(settings_string)

        if (sectionName not in fullDoc):
            fullDoc.update({sectionName: {settingName: value}})

        section = fullDoc[sectionName]
        section.update({settingName: value})

        data = ujson.dumps(fullDoc)
        SerialLog.log("New prefs.json: ", data)

        f = open("prefs.json", "w")
        f.write(data)
        f.close()