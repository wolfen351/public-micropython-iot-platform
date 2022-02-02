from basic_module import BasicModule
from web_server import WebServer
import json

#public static code
okayHeader = b"HTTP/1.1 200 Ok\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\n"

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

    def start(self):
        self.server = WebServer()
        self.server.start()

    def tick(self):
        self.server.tick()

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
            b"/": b"./web_index.html",
            b"/telemetry": self.webTelemetry
        }

    # special code called from main to set ALL routes
    def setRoutes(self, routes):
        self.server.setRoutes(routes)

    # special code called from main to set ALL telemetry
    def setTelemetry(self, telemetry):
        self.telemetry = telemetry

    # return json telemetry to ui
    def webTelemetry(self, params):
        headers = okayHeader
        data = json.dumps(self.telemetry)
        return data, headers  



    



    

