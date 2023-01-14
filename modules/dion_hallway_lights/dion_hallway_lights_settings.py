from serial_log import SerialLog
import uos


class DionHallwayLightsSettings:

    SETTINGS_FILE = "./light.settings"

    def __init__(self, TimeOnSetting=30000, DelaySetting=400):
        self.TimeOnSetting = TimeOnSetting
        self.DelaySetting = DelaySetting

    def write(self):
        """Write settings to settings_file if valid input found."""
        if self.is_valid():
            with open(self.SETTINGS_FILE, "wb") as f:
                f.write(",".join([str(self.TimeOnSetting),str(self.DelaySetting)]))
            SerialLog.log("Wrote settings to {:s}".format(self.SETTINGS_FILE))

    def load(self):

        try:
            with open(self.SETTINGS_FILE, "rb") as f:
                contents = f.read().split(b",")
            SerialLog.log("Loaded Light Settings from {:s}".format(self.SETTINGS_FILE))
            if len(contents) == 2:
                self.TimeOnSetting = int(contents[0])
                self.DelaySetting = int(contents[1])

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
        self.TimeOnSetting = 30000
        self.DelaySetting = 400

    def is_valid(self):
        # Ensure the credentials are entered as bytes
        if not isinstance(self.TimeOnSetting, int):
            return False
        if not isinstance(self.DelaySetting, int):
            return False
 
        return True
 