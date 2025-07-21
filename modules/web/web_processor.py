from modules.basic.basic_module import BasicModule
from modules.web.web_server import WebServer
import json
import time

# Public static vars
okayHeader = b"HTTP/1.1 200 Ok\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\n"
okayHeaderHtml = b"HTTP/1.1 200 Ok\r\nContent-Type: text/html\r\nAccess-Control-Allow-Origin: *\r\n"
refreshDoc = b"<html><head><meta http-equiv='refresh' content='15; url=/'></head><body>Rebooting, please wait...</body></html>"
redirectHomeHeader = b"HTTP/1.1 302 Ok\r\nLocation: /\r\n"

# Public static methods
def unquote(string):
    if not string:
        return b''

    if isinstance(string, str):
        string = string.encode('utf-8')

    string = string.replace(b"+", b" ")

    # Split into substrings on each escape character
    bits = string.split(b'%')
    if len(bits) == 1:
        return string  # There was no escape character
    
    res = [bits[0]]  # Everything before the first escape character

    # For each escape character, get the next two digits and convert to 
    for item in bits[1:]:
        code = item[:2]
        char = bytes([int(code, 16)])  # Convert to utf-8-encoded byte
        res.append(char)  # Append the converted character
        res.append(item[2:])  # Append anything else that occurred before the next escape character
    
    unquoted = b''.join(res)

    # Trim all whitespace off the end, protect against unquoted being empty
    while unquoted and unquoted[-1] == 32:
        unquoted = unquoted[:-1]

    return unquoted


class WebProcessor(BasicModule):
   
    def __init__(self):
        super().__init__()
        self.telemetry = {}
        self.panels = {}
        self.boardName = ""
        self.statusLedEnabled = self.getPref("web", "statusLedEnabled", True)
        self.last_telemetry_broadcast = 0     

    def start(self):
        super().start()
        self.server = WebServer()
        self.server.start()
        self.boardName = self.getPref("web", "name", self.basicSettings["name"])
     
    def tick(self):
        self.server.tick()
        
        # Broadcast telemetry via WebSocket every second
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_telemetry_broadcast) > 1000:
            self.server.broadcast_telemetry(self.telemetry)
            self.last_telemetry_broadcast = current_time
     
    def getTelemetry(self):
        return { 
            "name": self.boardName,
            "onboard/led": "Enabled" if self.statusLedEnabled else "Disabled",
            "switch/messageled": 1 if self.statusLedEnabled else 0
        }

    def processTelemetry(self, telemetry):
        pass

    def getCommands(self):
        return []

    def processCommands(self, commands):
        for c in commands:
            if (c.startswith("/switch/on/messageled")):
                self.statusLedEnabled = True
                self.setPref("web", "statusLedEnabled", self.statusLedEnabled)
            if (c.startswith("/switch/off/messageled")):
                self.statusLedEnabled = False
                self.setPref("web", "statusLedEnabled", self.statusLedEnabled)

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

    def setRoutes(self, routes):
        self.server.setRoutes(routes)

    def setTelemetry(self, telemetry):
        self.telemetry = telemetry

    def setPanels(self, panels):
        self.panels = panels

    def getLedEnabled(self):
        return self.statusLedEnabled

    def webTelemetry(self, params):
        headers = okayHeader
        data = json.dumps(self.telemetry)
        return data, headers  

    def webPanels(self, params):
        headers = okayHeader
        data = json.dumps(self.panels)
        return data, headers  

    def webReboot(self, params):
        return refreshDoc, okayHeaderHtml, True  # True for reboot
     
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





