import ujson
from os import listdir

from serial_log import SerialLog

class BasicModule:

    # static vars
    prefs = {}
    basicSettings = {}
    loadedPrefs = False

    def __init__(self):
        pass

    def start(self):
        f = open("profile.json",'r')
        settings_string=f.read()
        f.close()
        self.basicSettings = ujson.loads(settings_string)
        self.ensurePrefsExists()
        self.loadPrefs()

    def free(self):
        self.prefs = None
        self.basicSettings = None
        self.loadedPrefs = False


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

    def loadPrefs(self):
        f = open("prefs.json",'r')
        settings_string=f.read()
        f.close()
        self.prefs = ujson.loads(settings_string)
        self.loadedPrefs = True

    # Returns the preference if possible, otherwise the default
    def getPref(self, node, setting, default):

        if (not self.loadedPrefs):
            self.ensurePrefsExists()
            self.loadPrefs()

        if (node not in self.prefs):
            return default

        pref = self.prefs[node]
        if (setting not in pref):
            return default

        if pref[setting] == None: 
            return default

        return pref[setting]

    def setPref(self, sectionName, settingName, value):

        # if the value is a byte array, convert it to a string
        if (isinstance(value, bytes)):
            value = value.decode("utf-8")

        if (self.getPref(sectionName, settingName, None) == value):
            return

        if (sectionName not in self.prefs):
            self.prefs.update({sectionName: {settingName: value}})

        section = self.prefs[sectionName]
        section.update({settingName: value})

        f = open("prefs.json", "w")
        f.write(ujson.dumps(self.prefs))
        f.close()

        SerialLog.log("Set preference %s.%s to %s" % (sectionName, settingName, value))