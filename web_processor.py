from network_settings import NetSettings

class WebProcessor():
    def __init__(self):
        self.okayHeader = b"HTTP/1.1 200 Ok\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\n"
        self.lights = None
        self.mqtt = None

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

    def loadlightsettings(self, params):
        settings =  self.lights.getsettings()
        headers = self.okayHeader
        data = b"{ \"timeOn\": %s, \"delay1\": %s, \"delay2\": %s, \"delay3\": %s, \"delay4\": %s }" % (settings[0], settings[1], settings[2], settings[3], settings[4])
        return data, headers

    def savelightsettings(self, params):
        # Read form params
        TimeOn = self.unquote(params.get(b"TimeOn", None))
        Delay1 = self.unquote(params.get(b"Delay1", None))
        Delay2 = self.unquote(params.get(b"Delay2", None))
        Delay3 = self.unquote(params.get(b"Delay3", None))
        Delay4 = self.unquote(params.get(b"Delay4", None))
        settings = (int(TimeOn), int(Delay1), int(Delay2), int(Delay3), int(Delay4))
        self.lights.settings(settings)
        headers = b"HTTP/1.1 307 Temporary Redirect\r\nLocation: /\r\n"
        return b"", headers

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
        return b"", headers

    def lightstatus(self, params):
        status = self.lights.status()
        headers = b"HTTP/1.1 200 Ok\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\n"
        data = b"{ \"l1\": %s, \"l2\": %s, \"l3\": %s, \"l4\": %s }" % (status[0], status[1], status[2], status[3])
        return data, headers

    def mosfetstatus(self, params):
        status = self.lights.mosfetstatus()
        headers = b"HTTP/1.1 200 Ok\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\n"
        data = b"{ \"l1\": %s, \"l2\": %s, \"l3\": %s, \"l4\": %s }" % (status[0], status[1], status[2], status[3])
        return data, headers

    def command(self, params):
        on = self.unquote(params.get(b"on", None))
        off = self.unquote(params.get(b"off", None))
        auto = self.unquote(params.get(b"auto", None))
        if (on != b""):
            self.lights.command(1, on)
        if (off != b""):
            self.lights.command(0, off)
        if (auto != b""):
            self.lights.command(2, auto)
        headers = b"HTTP/1.1 307 Temporary Redirect\r\nLocation: /\r\n"
        return b"", headers

    def start(self, lights, mqtt):
        self.lights = lights
        self.mqtt = mqtt
