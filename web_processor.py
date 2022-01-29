from network_settings import NetSettings
import machine
from web_server import WebServer
from wifi import WifiHandler

class WebProcessor():

    def __init__(self, basicSettings):
        self.okayHeader = b"HTTP/1.1 200 Ok\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\n"

    def start(self):
        self.server = WebServer()
        self.server.start(self.getRoutes())

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


    #internal code
    def unquote(self, string):
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

    def getRoutes(self):
        return {
            b"/": b"./web_index.html", 
            b"/ha": b"./web_ha.html", 
            b"/mqtt": b"./web_mqtt.html", 
            b"/network": b"./web_network.html", 
            b"/temp": self.gettemp,
            b"/tbloadsettings": self.loadtbsettings,
            b"/tbsavesettings": self.savetbsettings,
            b"/haloadsettings": self.loadhasettings,
            b"/hasavesettings": self.savehasettings,
            b"/mqttloadsettings": self.loadmqttsettings,
            b"/mqttsavesettings": self.savemqttsettings,
            b"/netloadsettings": self.loadnetsettings,
            b"/netsavesettings": self.savenetsettings
        }

    def gettemp(self, params):
        tempVal = self.temp.currentTemp()
        headers = self.okayHeader
        data = b"{ \"temp\": %s }" % (tempVal)
        return data, headers

    def loadmqttsettings(self, params):
        settings =  self.mqtt.getsettings()
        headers = self.okayHeader
        data = b"{ \"enable\": \"%s\", \"server\": \"%s\", \"subscribe\": \"%s\", \"publish\": \"%s\" }" % (settings[0], settings[1], settings[2], settings[3])
        return data, headers

    def savemqttsettings(self, params):
        # Read form params
        enable = self.unquote(params.get(b"enable", None))
        server = self.unquote(params.get(b"server", None))
        subscribe = self.unquote(params.get(b"subscribe", None))
        publish = self.unquote(params.get(b"publish", None))
        settings = (enable, server, subscribe, publish)
        self.mqtt.settings(settings)
        headers = b"HTTP/1.1 307 Temporary Redirect\r\nLocation: /\r\n"
        return b"", headers
    
    def loadhasettings(self, params):
        settings =  self.ha.getsettings()
        headers = self.okayHeader
        data = b"{ \"enable\": \"%s\", \"server\": \"%s\", \"subscribe\": \"%s\", \"publish\": \"%s\" }" % (settings[0], settings[1], settings[2], settings[3])
        return data, headers

    def savehasettings(self, params):
        # Read form params
        enable = self.unquote(params.get(b"enable", None))
        server = self.unquote(params.get(b"server", None))
        subscribe = self.unquote(params.get(b"subscribe", None))
        publish = self.unquote(params.get(b"publish", None))
        settings = (enable, server, subscribe, publish)
        self.ha.settings(settings)
        headers = b"HTTP/1.1 307 Temporary Redirect\r\nLocation: /\r\n"
        return b"", headers

    def loadtbsettings(self, params):
        settings =  self.tb.getsettings()
        headers = self.okayHeader
        data = b"{ \"enable\": \"%s\", \"server\": \"%s\", \"subscribe\": \"%s\", \"publish\": \"%s\" }" % (settings[0], settings[1], settings[2], settings[3])
        return data, headers

    def savetbsettings(self, params):
        # Read form params
        enable = self.unquote(params.get(b"enable", None))
        server = self.unquote(params.get(b"server", None))
        subscribe = self.unquote(params.get(b"subscribe", None))
        publish = self.unquote(params.get(b"publish", None))
        settings = (enable, server, subscribe, publish)
        self.tb.settings(settings)
        headers = b"HTTP/1.1 307 Temporary Redirect\r\nLocation: /\r\n"
        return b"", headers
    
    def loadnetsettings(self, params):
        settings = NetSettings()
        settings.load()
        headers = self.okayHeader
        data = b"{ \"ssid\": \"%s\", \"password\": \"%s\", \"type\": \"%s\", \"ip\": \"%s\", \"netmask\": \"%s\", \"gateway\": \"%s\" }" % (settings.Ssid, settings.Password, settings.Type, settings.Ip, settings.Netmask, settings.Gateway)
        return data, headers

    def savenetsettings(self, params):
        # Read form params
        ssid = self.unquote(params.get(b"Ssid", None))
        password = self.unquote(params.get(b"Password", None))
        type = self.unquote(params.get(b"Type", None))
        ip = self.unquote(params.get(b"Ip", None))
        netmask = self.unquote(params.get(b"Netmask", None))
        gateway = self.unquote(params.get(b"Gateway", None))
        settings = NetSettings(ssid, password, type, ip, netmask, gateway)
        settings.write()
        headers = b"HTTP/1.1 307 Temporary Redirect\r\nLocation: /\r\n"
        # Connect using the new settings
        WifiHandler().station()
        # Reboot
        machine.reset()
        return b"", headers
