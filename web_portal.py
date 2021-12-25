import gc
import network
import uselect as select

from web_http import WebHTTPServer


class WebPortal:
    def __init__(self):

        self.sta_if = network.WLAN(network.STA_IF)

        self.http_server = None
        self.poller = select.poll()

        self.conn_time_start = None

    def start(self):
        print("Starting web portal")

        if self.http_server is None:
            self.http_server = WebHTTPServer(self.poller)
            print("Configured HTTP server")

    def handle_http(self, sock, event, others):
        self.http_server.handle(sock, event, others)

    def tick(self):
        try:
            gc.collect()
            # check for socket events and handle them
            for response in self.poller.ipoll(0):
                sock, event, *others = response
                self.handle_http(sock, event, others)
        except KeyboardInterrupt:
            print("Captive portal stopped")
