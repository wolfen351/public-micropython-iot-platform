from serial_log import SerialLog
import uos

class NtpSettings:

    SETTINGS_FILE = "./ntp.settings"

    def __init__(self, tzIANACode=b"", DefaultOffset=0 ):
        self.tzIANACode = tzIANACode
        self.defaultOffset = DefaultOffset

    def write(self):
        """Write settings to settings_file if valid input found."""
        if self.is_valid():
            with open(self.SETTINGS_FILE, "wb") as f:
                f.write(b",".join([self.tzIANACode, str(self.defaultOffset).encode('ascii')]))
            SerialLog.log("Wrote settings to {:s}".format(self.SETTINGS_FILE))

    def load(self):
        try:
            with open(self.SETTINGS_FILE, "rb") as f:
                contents = f.read().split(b",")
            SerialLog.log("Loaded settings from {:s}".format(self.SETTINGS_FILE))
            if len(contents) == 2:
                self.tzIANACode = contents[0]
                self.defaultOffset = int(contents[1])

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
        self.tzIANACode = b"Pacific/Auckland"
        self.defaultOffset = 12

    def is_valid(self):
        # Ensure the credentials are entered as bytes
        if not isinstance(self.tzIANACode, bytes):
            return False
        if not isinstance(self.defaultOffset, int):
            return False

        return True
 