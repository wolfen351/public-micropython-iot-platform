from serial_log import SerialLog
import uos

class ThingsboardSettings:

    SETTINGS_FILE = "./tb.settings"

    def __init__(self, Enable=b"Y", Server=b"mqtt.wolfen.za.net", Publish=b"", Port=1883, AccessToken=b""):
        self.Enable=Enable
        self.Server=Server
        self.Publish=Publish
        self.Port = Port
        self.AccessToken = AccessToken

    def write(self):
        """Write settings to settings_file if valid input found."""
        if self.is_valid():
            with open(self.SETTINGS_FILE, "wb") as f:
                f.write(b",".join([self.Enable, self.Server, self.Publish, str(self.Port).encode('ascii'), self.AccessToken]))
            SerialLog.log("Wrote settings to {:s}".format(self.SETTINGS_FILE))
        else:
            SerialLog.log("Invalid!")

    def load(self):
        try:
            with open(self.SETTINGS_FILE, "rb") as f:
                contents = f.read().split(b",")
            SerialLog.log("Loaded settings from {:s}".format(self.SETTINGS_FILE))
            if len(contents) == 5:
                self.Enable = contents[0]
                self.Server = contents[1]
                self.Publish = contents[2]
                self.Port = int(contents[3])
                self.AccessToken = contents[4]

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
        self.Publish = b""
        self.Port = 1883
        self.AccessToken = b""

    def is_valid(self):
        # Ensure the credentials are entered as bytes
        if not isinstance(self.Enable, bytes):
            return False
        if not isinstance(self.Server, bytes):
            return False
        if not isinstance(self.Publish, bytes):
            return False
        if not isinstance(self.Port, int):
            return False
        if not isinstance(self.AccessToken, bytes):
            return False

        return True
 