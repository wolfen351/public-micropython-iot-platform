import machine
from serial_log import SerialLog
import uerrno
import uio
import uselect as select
import usocket as socket
from collections import namedtuple
import ussl
import gc

WriteConn = namedtuple("WriteConn", ["body", "buff", "buffmv", "write_range"])
ReqInfo = namedtuple("ReqInfo", ["type", "path", "params", "host"])

from modules.web.server import Server

class WebServer():
    def __init__(self):

        self.poller = select.poll()

        self.httpServer = Server(self.poller, 80, socket.SOCK_STREAM, "WebHTTP Server")

        self.request = dict()
        self.conns = dict()

        # queue up to 5 connection requests before refusing
        self.httpServer.sock.listen(2)
        self.httpServer.sock.setblocking(False)

        self.shouldReboot = False

    
    def handle(self, sock, event, others):
        if sock is self.httpServer.sock:
            # client connecting on port 80, so spawn off a new
            # socket to handle this connection
            self.accept(sock)
        elif event & select.POLLIN:
            # socket has data to read in
            self.read(sock)
        elif event & select.POLLOUT:
            # existing connection has space to send more data
            self.write_to(sock)

    def accept(self, server_sock):
        try:
            connection, addr = server_sock.accept()
            connection.setblocking(False)
            connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.poller.register(connection, select.POLLIN)
        except OSError as e:
            if e.args[0] == uerrno.EAGAIN:
                return

    def parse_request(self, req):
        req_lines = req.split(b"\r\n")
        req_type, full_path, http_ver = req_lines[0].split(b" ")
        path = full_path.split(b"?")
        SerialLog.log("Web:", path)
        base_path = path[0]
        query = path[1] if len(path) > 1 else None
        query_params = (
            {
                key: val
                for key, val in [param.split(b"=") for param in query.split(b"&")]
            }
            if query
            else {}
        )
        host = [line.split(b": ")[1] for line in req_lines if b"Host:" in line][0]

        return ReqInfo(req_type, base_path, query_params, host)

    def get_response(self, req):
        """generate a response body and headers, given a route"""

        headers = "HTTP/1.1 200 Ok\r\nCache-Control: max-age=300\r\n"
        route = self.routes.get(req.path, None)

        if (route == None):
            # assume misses are a file
            try:
                if (req.path.endswith(b".js")):
                    headers += "content-type: application/javascript\r\n"
                return open(req.path, "rb"), headers, False
            except OSError: #open failed
                headers = b"HTTP/1.1 404 Not Found\r\n"
                return uio.BytesIO(b""), headers, False

        if type(route) is bytes:
            # expect a filename, so return contents of file
            SerialLog.log("Returning file:", route)
            return open(route, "rb"), headers, False

        if callable(route):
            # call a function, which may or may not return a response
            try:
                response = route(req.params)
                body = response[0] or b""
                headers = response[1]
                shouldReboot = False
                if len(response) == 3:
                    shouldReboot = headers[2]
                return uio.BytesIO(body), headers, shouldReboot
            except KeyboardInterrupt:
                raise
            except Exception as e:
                import sys
                sys.print_exception(e)
                headers = b"HTTP/1.1 500 Function failed\r\n"
                return uio.BytesIO(b""), headers, False

        headers = b"HTTP/1.1 404 Not Found\r\n"
        return uio.BytesIO(b""), headers, False

    def read(self, s):
        try:
            data = s.read()
            if not data:
                # no data in the TCP stream, so close the socket
                SerialLog.log("Closed socket, no more data")
                self.close(s)
                return

            # add new data to the full request
            sid = id(s)
            self.request[sid] = self.request.get(sid, b"") + data
            if (len(self.request[sid]) > 1000):
                SerialLog.log("Stream closed")
                self.close(s)
                return

            # check if additional data expected
            if data[-4:] != b"\r\n\r\n":
                # HTTP request is not finished if no blank line at the end
                # wait for next read event on this socket instead
                SerialLog.log("Waiting for more data...", data)
                return

            # get the completed request
            req = self.parse_request(self.request.pop(sid))
            body, headers, shouldReboot = self.get_response(req)
            self.shouldReboot = shouldReboot
            self.prepare_write(s, body, headers)
        except Exception as e:
            SerialLog.log("Error reading from socket", e)
            self.close(s)
        

    def prepare_write(self, s, body, headers):
        # add newline to headers to signify transition to body
        headers += "\r\n"

        # force strings to have utf-8 encoding so they have a defined length
        if type(headers) is str:
            headers = headers.encode("utf-8")

        # TCP/IP MSS is 536 bytes, so create buffer of this size and
        # initially populate with header data
        buff = bytearray(headers + "\x00" * (536 - len(headers)))
        # use memoryview to read directly into the buffer without copying
        buffmv = memoryview(buff)
        # start reading body data into the memoryview starting after
        # the headers, and writing at most the remaining space of the buffer
        # return the number of bytes written into the memoryview from the body
        bw = body.readinto(buffmv[len(headers) :], 536 - len(headers))
        # save place for next write event
        c = WriteConn(body, buff, buffmv, [0, len(headers) + bw])
        self.conns[id(s)] = c
        # let the poller know we want to know when it's OK to write
        self.poller.modify(s, select.POLLOUT)

    def write_to(self, sock):
        # get the data that needs to be written to this socket
        c = self.conns[id(sock)]
        if c:
            # write next 536 bytes (max) into the socket
            try:
                bytes_written = sock.write(c.buffmv[c.write_range[0] : c.write_range[1]])
            except OSError as e:
                if (e.errno == 128): # Not connected anymore
                    self.close(sock)
                if (e.errno == 104): # Connection Reset
                    self.close(sock)
                return
            if not bytes_written or c.write_range[1] < 536:
                # either we wrote no bytes, or we wrote < TCP MSS of bytes
                # so we're done with this connection
                self.close(sock)
                gc.collect()
            else:
                # more to write, so read the next portion of the data into
                # the memoryview for the next send event
                self.buff_advance(c, bytes_written)

    def buff_advance(self, c, bytes_written):
        if bytes_written == c.write_range[1] - c.write_range[0]:
            # wrote all the bytes we had buffered into the memoryview
            # set next write start on the memoryview to the beginning
            c.write_range[0] = 0
            # set next write end on the memoryview to length of bytes
            # read in from remainder of the body, up to TCP MSS
            c.write_range[1] = c.body.readinto(c.buff, 536)
        else:
            # didn't read in all the bytes that were in the memoryview
            # so just set next write start to where we ended the write
            c.write_range[0] += bytes_written

    def close(self, s):
        s.close()
        self.poller.unregister(s)
        sid = id(s)
        if sid in self.request:
            del self.request[sid]
        if sid in self.conns:
            del self.conns[sid]
        if (self.shouldReboot):
            machine.reset()

    def start(self):
        SerialLog.log("Web server started")

    def setRoutes(self, routes):
        self.routes = routes

    def tick(self):
        # check for socket events and handle them
        for response in self.poller.ipoll(0):
            sock, event, *others = response
            self.handle(sock, event, others)
