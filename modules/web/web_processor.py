import machine
from modules.basic.basic_module import BasicModule
from modules.web.web_server import WebServer
import json

#public static code
okayHeader = b"HTTP/1.1 200 Ok\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\n"
redirectHomeHeader = b"HTTP/1.1 302 Ok\r\nLocation: /\r\n"

@micropython.native 
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

    @micropython.native 
    def start(self):
        self.server = WebServer()
        self.server.start()

    @micropython.native 
    def tick(self):
        self.server.tick()

    @micropython.native 
    def getTelemetry(self):
        return {}

    @micropython.native 
    def processTelemetry(self, telemetry):
        pass

    @micropython.native 
    def getCommands(self):
        return []

    @micropython.native 
    def processCommands(self, commands):
        pass

    @micropython.native 
    def getRoutes(self):
        return {
            b"/": b"/modules/web/web_index.html",
            b"/cash.min.js": b"/cash.min.js",
            b"/telemetry": self.webTelemetry,
            b"/reboot": self.webReboot,
            b"/panels": self.webPanels,
        }

    # special code called from main to set ALL routes
    @micropython.native 
    def setRoutes(self, routes):
        self.server.setRoutes(routes)

    # special code called from main to set ALL telemetry
    @micropython.native 
    def setTelemetry(self, telemetry):
        self.telemetry = telemetry

    # special code called from main to set ALL panels
    @micropython.native 
    def setPanels(self, panels):
        self.panels = panels

    # return json telemetry to ui
    @micropython.native 
    def webTelemetry(self, params):
        headers = okayHeader
        data = json.dumps(self.telemetry)
        return data, headers  

    # return json panel list to ui
    @micropython.native 
    def webPanels(self, params):
        headers = okayHeader
        data = json.dumps(self.panels)
        return data, headers  

    # Simple reboot
    @micropython.native 
    def webReboot(self, params):
        machine.reset()


    



    

