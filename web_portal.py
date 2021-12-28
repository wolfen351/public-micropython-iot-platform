import uerrno
import uio
import uselect as select
import usocket as socket

from collections import namedtuple

WriteConn = namedtuple("WriteConn", ["body", "buff", "buffmv", "write_range"])
ReqInfo = namedtuple("ReqInfo", ["type", "path", "params", "host"])

from server import Server

import gc


def unquote(string):
    """stripped down implementation of urllib.parse unquote_to_bytes"""

    if not string:
        return b''

    if isinstance(string, str):
        string = string.encode('utf-8')

    # split into substrings on each escape character
    bits = string.split(b'%')
    if len(bits) == 1:
        return string  # there was no escape character
    
    res = [bits[0]]  # everything before the first escape character

    # for each escape character, get the next two digits and convert to 
    for item in bits[1:]:
        code = item[:2]
        char = bytes([int(code, 16)])  # convert to utf-8-encoded byte
        res.append(char)  # append the converted character
        res.append(item[2:])  # append anything else that occurred before the next escape character
    
    return b''.join(res)


class WebPortal(Server):
    def __init__(self):

        self.poller = select.poll()

        super().__init__(self.poller, 80, socket.SOCK_STREAM, "WebHTTP Server")

        self.request = dict()
        self.conns = dict()
        self.routes = {
            b"/": b"./web_index.html", 
            b"/command": self.command, 
            b"/settings": self.settings,
            b"/lightstatus": self.lightstatus,
            b"/mosfetstatus": self.mosfetstatus,
            b"/loadsettings": self.loadsettings,
        }

        self.ssid = None
        self.lights = None

        # queue up to 5 connection requests before refusing
        self.sock.listen(5)
        self.sock.setblocking(False)

    #@micropython.native
    def handle(self, sock, event, others):
        if sock is self.sock:
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
        """accept a new client request socket and register it for polling"""

        try:
            client_sock, addr = server_sock.accept()
        except OSError as e:
            if e.args[0] == uerrno.EAGAIN:
                return

        client_sock.setblocking(False)
        client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.poller.register(client_sock, select.POLLIN)

    def parse_request(self, req):
        """parse a raw HTTP request to get items of interest"""

        req_lines = req.split(b"\r\n")
        req_type, full_path, http_ver = req_lines[0].split(b" ")
        path = full_path.split(b"?")
        print("Web:", path)
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

    def command(self, params):
        # Read form params
        on = unquote(params.get(b"on", None))
        off = unquote(params.get(b"off", None))
        auto = unquote(params.get(b"auto", None))

        if (on != b""):
            self.lights.command(1, on)

        if (off != b""):
            self.lights.command(0, off)

        if (auto != b""):
            self.lights.command(2, auto)

        headers = (
            b"HTTP/1.1 307 Temporary Redirect\r\n"
            b"Location: /\r\n"
        )

        gc.collect()

        return b"", headers

    def loadsettings(self, params):
        # Read form params
        settings =  self.lights.getsettings()

        headers = b"HTTP/1.1 200 Ok\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\n"
        data = b"{ \"timeOn\": %s, \"delay1\": %s, \"delay2\": %s, \"delay3\": %s, \"delay4\": %s }" % (settings[0], settings[1], settings[2], settings[3], settings[4])

        gc.collect()
        return data, headers

    def settings(self, params):
        # Read form params
        TimeOn = unquote(params.get(b"TimeOn", None))
        Delay1 = unquote(params.get(b"Delay1", None))
        Delay2 = unquote(params.get(b"Delay2", None))
        Delay3 = unquote(params.get(b"Delay3", None))
        Delay4 = unquote(params.get(b"Delay4", None))

        settings = (int(TimeOn), int(Delay1), int(Delay2), int(Delay3), int(Delay4))
        self.lights.settings(settings)

        headers = (
            b"HTTP/1.1 307 Temporary Redirect\r\n"
            b"Location: /\r\n"
        )

        gc.collect()

        return b"", headers
   
    def lightstatus(self, params):
        status = self.lights.status()
        headers = b"HTTP/1.1 200 Ok\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\n"
       
        gc.collect()
        data = b"{ \"l1\": %s, \"l2\": %s, \"l3\": %s, \"l4\": %s }" % (status[0], status[1], status[2], status[3])
        return data, headers

    def mosfetstatus(self, params):
        status = self.lights.mosfetstatus()
        headers = b"HTTP/1.1 200 Ok\r\nContent-Type: application/json\r\nAccess-Control-Allow-Origin: *\r\n"
       
        gc.collect()
        data = b"{ \"l1\": %s, \"l2\": %s, \"l3\": %s, \"l4\": %s }" % (status[0], status[1], status[2], status[3])
        return data, headers

    def get_response(self, req):
        """generate a response body and headers, given a route"""

        headers = b"HTTP/1.1 200 OK\r\n"
        route = self.routes.get(req.path, None)

        if type(route) is bytes:
            # expect a filename, so return contents of file
            return open(route, "rb"), headers

        if callable(route):
            # call a function, which may or may not return a response
            response = route(req.params)
            body = response[0] or b""
            headers = response[1] or headers
            return uio.BytesIO(body), headers

        headers = b"HTTP/1.1 404 Not Found\r\n"
        return uio.BytesIO(b""), headers

    def read(self, s):
        """read in client request from socket"""

        data = s.read()
        if not data:
            # no data in the TCP stream, so close the socket
            self.close(s)
            return

        # add new data to the full request
        sid = id(s)
        self.request[sid] = self.request.get(sid, b"") + data

        # check if additional data expected
        if data[-4:] != b"\r\n\r\n":
            # HTTP request is not finished if no blank line at the end
            # wait for next read event on this socket instead
            return

        # get the completed request
        req = self.parse_request(self.request.pop(sid))
        body, headers = self.get_response(req)
        self.prepare_write(s, body, headers)

    def prepare_write(self, s, body, headers):
        # add newline to headers to signify transition to body
        headers += "\r\n"
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
        """write the next message to an open socket"""

        # get the data that needs to be written to this socket
        c = self.conns[id(sock)]
        if c:
            # write next 536 bytes (max) into the socket
            try:
                bytes_written = sock.write(c.buffmv[c.write_range[0] : c.write_range[1]])
            except OSError:
                return
            if not bytes_written or c.write_range[1] < 536:
                # either we wrote no bytes, or we wrote < TCP MSS of bytes
                # so we're done with this connection
                self.close(sock)
            else:
                # more to write, so read the next portion of the data into
                # the memoryview for the next send event
                self.buff_advance(c, bytes_written)

    def buff_advance(self, c, bytes_written):
        """advance the writer buffer for this connection to next outgoing bytes"""

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
        """close the socket, unregister from poller, and delete connection"""
        s.close()
        self.poller.unregister(s)
        sid = id(s)
        if sid in self.request:
            del self.request[sid]
        if sid in self.conns:
            del self.conns[sid]
        gc.collect()

    def start(self, lights):
        print("Web server started")
        self.lights = lights

    def tick(self):
        # check for socket events and handle them
        for response in self.poller.ipoll(0):
            sock, event, *others = response
            self.handle(sock, event, others)
