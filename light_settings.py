import uos


class LightSettings:

    SETTINGS_FILE = "./light.settings"

    def __init__(self, TimeOnSetting=30000, Delay0Setting=0, Delay1Setting=1000, Delay2Setting=3000, Delay3Setting=3000):
        self.TimeOnSetting = TimeOnSetting
        self.Delay0Setting = Delay0Setting
        self.Delay1Setting = Delay1Setting
        self.Delay2Setting = Delay2Setting
        self.Delay3Setting = Delay3Setting

    def write(self):
        """Write settings to settings_file if valid input found."""
        if self.is_valid():
            with open(self.SETTINGS_FILE, "wb") as f:
                f.write(",".join([str(self.TimeOnSetting),str(self.Delay0Setting),str(self.Delay1Setting),str(self.Delay2Setting),str(self.Delay3Setting)]))
            print("Wrote settings to {:s}".format(self.SETTINGS_FILE))

    def load(self):

        try:
            with open(self.SETTINGS_FILE, "rb") as f:
                contents = f.read().split(b",")
            print("Loaded Light Settings from {:s}".format(self.SETTINGS_FILE))
            if len(contents) == 5:
                self.TimeOnSetting = int(contents[0])
                self.Delay0Setting = int(contents[1])
                self.Delay1Setting = int(contents[2])
                self.Delay2Setting = int(contents[3])
                self.Delay3Setting = int(contents[4])

            if not self.is_valid():
                self.remove()

            print(contents)

        except OSError:
            pass

        return self

    def remove(self):
        """
        1. Delete settings file from disk.
        2. Reset to defaults
        """
        print("Attempting to remove {}".format(self.SETTINGS_FILE))
        try:
            uos.remove(self.SETTINGS_FILE)
        except OSError:
            pass
        self.TimeOnSetting = 30000
        self.Delay0Setting = 0
        self.Delay1Setting = 1000
        self.Delay2Setting = 3000
        self.Delay3Setting = 3000

    def is_valid(self):
        # Ensure the credentials are entered as bytes
        if not isinstance(self.TimeOnSetting, int):
            return False
        if not isinstance(self.Delay0Setting, int):
            return False
        if not isinstance(self.Delay1Setting, int):
            return False
        if not isinstance(self.Delay2Setting, int):
            return False
        if not isinstance(self.Delay3Setting, int):
            return False

        return True
 