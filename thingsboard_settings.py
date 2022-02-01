from serial_log import SerialLog
import uos

class ThingsboardSettings:

    SETTINGS_FILE = "./tb.settings"

    def __init__(self, Enable=b"Y", Server=b"mqtt.wolfen.za.net", Subscribe=b"", Publish=b"", Port=1883, AccessToken=b""):
        self.Enable=Enable
        self.Server=Server
        self.Subscribe=Subscribe
        self.Publish=Publish
        self.Port = Port
        self.AccessToken = AccessToken

    def write(self):
        """Write settings to settings_file if valid input found."""
        if self.is_valid():
            with open(self.SETTINGS_FILE, "wb") as f:
                f.write(",".join([self.Enable, self.Server, self.Subscribe, self.Publish, str(self.Port), self.AccessToken]))
            SerialLog.log("Wrote settings to {:s}".format(self.SETTINGS_FILE))

    def load(self):
        try:
            with open(self.SETTINGS_FILE, "rb") as f:
                contents = f.read().split(b",")
            SerialLog.log("Loaded settings from {:s}".format(self.SETTINGS_FILE))
            if len(contents) == 4:
                self.Enable = contents[0]
                self.Server = contents[1]
                self.Subscribe = contents[2]
                self.Publish = contents[3]
                self.Port = int(contents[4])
                self.AccessToken = contents[5]

            if not self.is_valid():
                self.remove()

            SerialLog.log(contents)

        except OSError:
            pass

        return self

    def remove(self):
        """
        1. Delete settings file from disk.
        2. Reset to defaults
        """
        SerialLog.log("Attempting to remove {}".format(self.SETTINGS_FILE))
        try:
            uos.remove(self.SETTINGS_FILE)
        except OSError:
            pass
        self.Enable = b"Y"
        self.Server = b"mqtt.wolfen.za.net"
        self.Subscribe = b""
        self.Publish = b""
        self.Port = 1883
        self.AccessToken = b""

    def is_valid(self):
        # Ensure the credentials are entered as bytes
        if not isinstance(self.Enable, str):
            return False
        if not isinstance(self.Server, str):
            return False
        if not isinstance(self.Subscribe, str):
            return False
        if not isinstance(self.Publish, str):
            return False
        if not isinstance(self.Port, int):
            return False
        if not isinstance(self.AccessToken, str):
            return False

        return True
 