from serial_log import SerialLog
import uos

class MqttSettings:

    SETTINGS_FILE = "./mqtt.settings"

    def __init__(self, Enable=b"Y", Server=b"mqtt.example.com", Subscribe=b"", Publish=b"", Username=b"", Password=b""):
        self.Enable=Enable
        self.Server=Server
        self.Subscribe=Subscribe
        self.Publish=Publish
        self.Username=Username
        self.Password=Password

    def write(self):
        """Write settings to settings_file if valid input found."""
        if self.is_valid():
            with open(self.SETTINGS_FILE, "wb") as f:
                f.write(b",".join([self.Enable, self.Server, self.Subscribe, self.Publish, self.Username, self.Password]))
            SerialLog.log("Wrote settings to {:s}".format(self.SETTINGS_FILE))

    def load(self):
        try:
            with open(self.SETTINGS_FILE, "rb") as f:
                contents = f.read().split(b",")
            SerialLog.log("Loaded settings from {:s}".format(self.SETTINGS_FILE))
            if len(contents) >= 4:
                self.Enable = contents[0]
                self.Server = contents[1]
                self.Subscribe = contents[2]
                self.Publish = contents[3]
            if len(contents) == 6:
                self.Username = contents[4]
                self.Password = contents[5]

            if not self.is_valid():
                self.remove()

            SerialLog.log("Contents:", contents)

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
        self.Server = b"mqtt.example.com"
        self.Subscribe = b""
        self.Publish = b""
        self.Username = b""
        self.Password = b""

    def is_valid(self):
        # Ensure the credentials are entered as bytes
        if not isinstance(self.Enable, bytes):
            return False
        if not isinstance(self.Server, bytes):
            return False
        if not isinstance(self.Subscribe, bytes):
            return False
        if not isinstance(self.Publish, bytes):
            return False
       if not isinstance(self.Username, bytes):
            return False
       if not isinstance(self.Password, bytes):
            return False

        return True
 