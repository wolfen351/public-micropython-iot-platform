from serial_log import SerialLog
import usocket as socket
import uselect as select


class Server:
    def __init__(self, poller, port, sock_type):
        # create socket with correct type: stream (TCP) or datagram (UDP)
        self.sock = socket.socket(socket.AF_INET, sock_type)

        # register to get event updates for this socket
        self.poller = poller
        self.poller.register(self.sock, select.POLLIN)

        addr = socket.getaddrinfo("0.0.0.0", port)[0][-1]
        # allow new requests while still sending last response
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(addr)

        SerialLog.log("Web Server listening on", addr)

    
    def stop(self, poller):
        poller.unregister(self.sock)
        self.sock.close()
        SerialLog.log("Web Server stopped")
 