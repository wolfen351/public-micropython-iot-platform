import machine
from modules.basic.basic_module import BasicModule
from modules.web.web_server import WebServer
import json

from modules.web.web_settings import WebSettings

#public static code
okayHeader = b"HTTP/1.1 200 Ok\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\n"
redirectHomeHeader = b"HTTP/1.1 302 Ok\r\nLocation: /\r\n"

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
   
    def __init__(self, basicSettings):
        self.telemetry = {}
        self.panels = {}

    #@micropython.native 
    def start(self):
        self.server = WebServer()
        self.server.start()
        self.webSettings = WebSettings()
        self.webSettings.load()

    #@micropython.native 
    def tick(self):
        self.server.tick()

    #@micropython.native 
    def getTelemetry(self):
        return { 
            "name": self.webSettings.Name,
            "onboard/led": self.webSettings.Led
        }

    #@micropython.native 
    def processTelemetry(self, telemetry):
        pass

    #@micropython.native 
    def getCommands(self):
        return []

    #@micropython.native 
    def processCommands(self, commands):
        pass

    #@micropython.native 
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
    #@micropython.native 
    def setRoutes(self, routes):
        self.server.setRoutes(routes)

    # special code called from main to set ALL telemetry
    #@micropython.native 
    def setTelemetry(self, telemetry):
        self.telemetry = telemetry

    # special code called from main to set ALL panels
    #@micropython.native 
    def setPanels(self, panels):
        self.panels = panels

    # special code called from main to see if Led must be on
    #@micropython.native 
    def getLedEnabled(self):
        return self.webSettings.Led != b"Disabled"

    # return json telemetry to ui
    #@micropython.native 
    def webTelemetry(self, params):
        headers = okayHeader
        data = json.dumps(self.telemetry)
        return data, headers  

    # return json panel list to ui
    #@micropython.native 
    def webPanels(self, params):
        headers = okayHeader
        data = json.dumps(self.panels)
        return data, headers  

    # Simple reboot
    #@micropython.native 
    def webReboot(self, params):
        machine.reset()

    def webSaveName(self, params):
        name = unquote(params.get(b"name", None))
        self.webSettings.Name = name
        self.webSettings.write()
        headers = okayHeader
        data = name
        return data, headers  

    def switchLed(self, params):
        headers = okayHeader
        data = "ok"
        if (self.webSettings.Led == b"Enabled"):
            self.webSettings.Led = b"Disabled"
        else:
            self.webSettings.Led = b"Enabled"
        self.webSettings.write()
        return data, headers    



    

