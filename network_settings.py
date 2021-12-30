import uos

class NetSettings:

    SETTINGS_FILE = "./net.settings"

    def __init__(self, Ssid=b"SSID", Password=b"password", Type=b"DHCP", Ip=b"", Netmask=b"", Gateway=b""):
        self.Ssid=Ssid
        self.Password=Password
        self.Type=Type
        self.Ip=Ip
        self.Netmask=Netmask
        self.Gateway=Gateway

    def write(self):
        """Write settings to settings_file if valid input found."""
        if self.is_valid():
            with open(self.SETTINGS_FILE, "wb") as f:
                f.write(",".join([self.Ssid, self.Password, self.Type, self.Ip, self.Netmask, self.Gateway]))
            print("Wrote settings to {:s}".format(self.SETTINGS_FILE))

    def load(self):
        try:
            with open(self.SETTINGS_FILE, "rb") as f:
                contents = f.read().split(b",")
            print("Loaded settings from {:s}".format(self.SETTINGS_FILE))
            if len(contents) == 6:
                self.Ssid = contents[0]
                self.Password = contents[1]
                self.Type = contents[2]
                self.Ip = contents[3]
                self.Netmask = contents[4]
                self.Gateway = contents[5]

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
        self.Ssid = b"SSID"
        self.Password = b"password"
        self.Type = b"DHCP"
        self.Ip = b""
        self.Netmask = b""
        self.Gateway = b""

    def is_valid(self):
        # Ensure the credentials are entered as bytes
        if not isinstance(self.Ssid, bytes):
            return False
        if not isinstance(self.Password, bytes):
            return False
        if not isinstance(self.Type, bytes):
            return False
        if not isinstance(self.Ip, bytes):
            return False
        if not isinstance(self.Netmask, bytes):
            return False
        if not isinstance(self.Gateway, bytes):
            return False

        return True
 