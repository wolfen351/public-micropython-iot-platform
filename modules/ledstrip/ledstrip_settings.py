from serial_log import SerialLog
import uos


class LedStripSettings:

    SETTINGS_FILE = "./ledstrip.settings"

    def __init__(self, ledAction = b"rainbow", ledColorPrimary = b"000000", ledColorSecondary = b"000000"):
        self.ledAction = ledAction
        self.ledColorPrimary = ledColorPrimary
        self.ledColorSecondary = ledColorSecondary

    def write(self):
        """Write settings to settings_file if valid input found."""
        if self.is_valid():
            with open(self.SETTINGS_FILE, "wb") as f:
                f.write(b",".join([self.ledAction, self.ledColorPrimary, self.ledColorSecondary]))
            SerialLog.log("Wrote settings to {:s}".format(self.SETTINGS_FILE))

    def load(self):

        try:
            with open(self.SETTINGS_FILE, "rb") as f:
                contents = f.read().split(b",")
            SerialLog.log("Loaded LedStrip Settings from {:s}".format(self.SETTINGS_FILE))
            if len(contents) == 3:
                self.ledAction = contents[0]
                self.ledColorPrimary = contents[1]
                self.ledColorSecondary = contents[2]

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
        self.ledAction = b"rainbow"
        self.ledColorPrimary = b"000000"
        self.ledColorSecondary = b"000000"


    def is_valid(self):
        # Ensure the credentials are entered as bytes
        if not isinstance(self.ledAction, bytes):
            return False
        if not isinstance(self.ledColorPrimary, bytes):
            return False
        if not isinstance(self.ledColorSecondary, bytes):
            return False
        return True
 