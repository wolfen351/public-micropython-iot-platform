from modules.basic.basic_module import BasicModule
from modules.web.web_server import WebServer
import json

#public static vars
okayHeader = b"HTTP/1.1 200 Ok\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\n"
redirectHomeHeader = b"HTTP/1.1 302 Ok\r\nLocation: /\r\n"

# public static methods
def unquote(string):
    if not string:
        return b''

    if isinstance(string, str):
        string = string.encode('utf-8')

    string = string.replace(b"+", b" ")

    # split into substrings on each escape character
    bits = string.split(b'%')
    if len(bits) == 1:
        return string  # there was no escape character
    
    res = [bits[0]]  # everything before the first escape character

    # for each escape character, get the next two digits and convert to 
    for item in bits[1:]:
        code = item[:2]
        char = bytes([int(code, 16)])  # convert to utf-8-encoded byte
        res.append(char)  # append the converted character
        res.append(item[2:])  # append anything else that occurred before the next escape character
    
    return b''.join(res)


class WebProcessor(BasicModule):
   
    def __init__(self):
        self.telemetry = {}
        self.panels = {}
        self.boardName = self.getPref("web", "name", self.basicSettings["name"])
        self.statusLedEnabled = self.getPref("web", "statusLedEnabled", True)     

    def start(self):
        BasicModule.start(self)
        self.server = WebServer()
        self.server.start()
     
    def tick(self):
        self.server.tick()
     
    def getTelemetry(self):
        return { 
            "name": self.boardName,
            "onboard/led": "Enabled" if self.statusLedEnabled else "Disabled"
        }

     
    def processTelemetry(self, telemetry):
        pass

     
    def getCommands(self):
        return []

     
    def processCommands(self, commands):
        pass

     
    def getRoutes(self):
        return {
            b"/": b"/modules/web/web_index.html",
            b"/cash.min.js": b"/modules/web/cash.min.js",
            b"/telemetry": self.webTelemetry,
            b"/reboot": self.webReboot,
            b"/panels": self.webPanels,
            b"/saveName": self.webSaveName,
            b"/switchLed": self.switchLed
        }

    # special code called from main to set ALL routes
     
    def setRoutes(self, routes):
        self.server.setRoutes(routes)

    # special code called from main to set ALL telemetry
     
    def setTelemetry(self, telemetry):
        self.telemetry = telemetry

    # special code called from main to set ALL panels
     
    def setPanels(self, panels):
        self.panels = panels

    # special code called from main to see if Led must be on
    def getLedEnabled(self):
        return self.statusLedEnabled

    # return json telemetry to ui
    def webTelemetry(self, params):
        headers = okayHeader
        data = json.dumps(self.telemetry)
        return data, headers  

    # return json panel list to ui
    def webPanels(self, params):
        headers = okayHeader
        data = json.dumps(self.panels)
        return data, headers  

    # Simple reboot
    def webReboot(self, params):
        return "", okayHeader, True
     
    def webSaveName(self, params):
        name = unquote(params.get(b"name", None))
        self.boardName = name
        self.setPref("web", "name", name)
        headers = okayHeader
        data = name
        return data, headers  

     
    def switchLed(self, params):
        headers = okayHeader
        data = "ok"
        self.statusLedEnabled = not self.statusLedEnabled
        self.setPref("web", "statusLedEnabled", self.statusLedEnabled)
        return data, headers    



    

