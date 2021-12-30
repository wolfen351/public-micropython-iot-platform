import gc
import network
import ubinascii as binascii
import uselect as select
import utime as time

from captive_dns import DNSServer
from captive_http import HTTPServer
from network_settings import NetSettings


class CaptivePortal:
    AP_IP = "192.168.4.1"
    MAX_CONN_ATTEMPTS = 3
    AP_WAIT = 300 #seconds

    def __init__(self, project="WOLF"):
        self.local_ip = self.AP_IP
        self.sta_if = network.WLAN(network.STA_IF)

        self.essid = b"%s-%s" % (project,  binascii.hexlify(self.sta_if.config("mac")[-3:]))

        self.creds = NetSettings()

        self.dns_server = None
        self.http_server = None

        self.conn_time_start = None
        self.waiting_for_new_creds = False

    def start_access_point(self):
        # sometimes need to turn off AP before it will come up properly

        # Only allocate ram for AP and poller if needed
        self.ap_if = network.WLAN(network.AP_IF)
        self.poller = select.poll()

        self.ap_if.active(False)
        while not self.ap_if.active():
            self.ap_if.active(True)
            time.sleep(1)
        # IP address, netmask, gateway, DNS
        self.ap_if.ifconfig(
            (self.local_ip, "255.255.255.0", self.local_ip, self.local_ip)
        )
        self.ap_if.config(essid=self.essid, authmode=network.AUTH_OPEN)
        print("AP mode configured:", self.essid, self.ap_if.ifconfig())
        self.waiting_for_new_creds = True

    def connect_to_wifi(self):
        print("Trying to connect to SSID '{:s}' with password {:s}".format(self.creds.Ssid, self.creds.Password))

        # initiate the connection
        self.sta_if.active(True)
        self.sta_if.connect(self.creds.Ssid, self.creds.Password)

        attempts = 1
        while attempts <= self.MAX_CONN_ATTEMPTS:
            if not self.sta_if.isconnected():
                print("Connection attempt {:d}/{:d} ...".format(attempts, self.MAX_CONN_ATTEMPTS))
                time.sleep(2)
                attempts += 1
            else:
                print("Connected to {:s}".format(self.creds.Ssid))
                self.local_ip = self.sta_if.ifconfig()[0]
                print("IP ", self.local_ip)
                return True

        print(
            "Failed to connect to {:s} with {:s}. WLAN status={:d}".format(
                self.creds.Ssid, self.creds.Password, self.sta_if.status()
            )
        )

        return False

    def check_valid_wifi(self):
        if not self.sta_if.isconnected():
            if self.creds.load().is_valid():
                # have credentials to connect, but not yet connected
                # return value based on whether the connection was successful
                return self.connect_to_wifi()
            # not connected, and no credentials to connect yet
            return False

        # Not connected
        return False

    def captive_portal(self):
        self.start_access_point()

        if self.http_server is None:
            self.http_server = HTTPServer(self.poller, self.local_ip, self)
        if self.dns_server is None:
            self.dns_server = DNSServer(self.poller, self.local_ip)

        t_end = time.time() + self.AP_WAIT
        while time.time() < t_end:
            gc.collect()
            # check for socket events and handle them
            for response in self.poller.ipoll(1000):
                sock, event, *others = response
                is_handled = self.handle_dns(sock, event, others)
                if not is_handled:
                    self.handle_http(sock, event, others)

            # Check if the creds we have work
            if not self.waiting_for_new_creds:
                if self.check_valid_wifi():
                    self.cleanup()
                    return
                else:
                    print("Creds provided did not work, waiting for new attempt")
                    self.waiting_for_new_creds = True

            # Check if we magically got a connection from previously configured values (like the router came up while we are in AP)
            if self.sta_if.isconnected():
                self.cleanup()
                return
                

        print("Gave up on getting new wifi credentials")
        self.cleanup()

    def handle_dns(self, sock, event, others):
        if sock is self.dns_server.sock:
            # ignore UDP socket hangups
            if event == select.POLLHUP:
                return True

            try:
                self.dns_server.handle(sock, event, others)
            except:
                pass

            return True
        return False

    def handle_http(self, sock, event, others):
        self.http_server.handle(sock, event, others)

    def cleanup(self):
        if self.http_server:
            self.http_server.stop(self.poller)
        if self.dns_server:
            self.dns_server.stop(self.poller)
        if self.ap_if != None:
            self.ap_if.active(False)
            self.ap_if = None
        gc.collect()

    def try_connect_from_file(self):
        if self.creds.load().is_valid():
            if self.connect_to_wifi():
                return True
        return False

    def start(self):
        # turn off station interface to force a reconnect
        self.sta_if.active(False)
        if not self.try_connect_from_file():
            self.captive_portal()

