import machine
from serial_log import SerialLog
import uerrno
import uio
import uselect as select
import usocket as socket
from collections import namedtuple
import gc

WriteConn = namedtuple("WriteConn", ["body", "buff", "buffmv", "write_range"])
ReqInfo = namedtuple("ReqInfo", ["type", "path", "params", "host"])

from modules.web.server import Server

class WebServer():
    def __init__(self):
        self.poller = select.poll()
        self.httpServer = Server(self.poller, 80, socket.SOCK_STREAM)
        self.request = dict()
        self.conns = dict()

        # queue up to 2 connection requests before refusing
        self.httpServer.sock.listen(2)
        self.httpServer.sock.setblocking(False)

        self.shouldReboot = False

    def handle(self, sock, event, others):
        if sock is self.httpServer.sock:
            self.accept(sock)
        elif event & select.POLLIN:
            self.read(sock)
        elif event & select.POLLOUT:
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
        headers = "HTTP/1.1 200 Ok\r\nCache-Control: max-age=300\r\n"
        route = self.routes.get(req.path, None)

        if route is None:
            try:
                if req.path.endswith(b".js"):
                    headers += "content-type: application/javascript\r\n"
                return open(req.path, "rb"), headers, False
            except OSError:
                headers = b"HTTP/1.1 404 Not Found\r\n"
                return uio.BytesIO(b""), headers, False

        if isinstance(route, bytes):
            SerialLog.log("Returning file:", route)
            return open(route, "rb"), headers, False

        if callable(route):
            try:
                response = route(req.params)
                gc.collect()
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
                SerialLog.log("Closed socket, no more data")
                self.close(s)
                return

            sid = id(s)
            self.request[sid] = self.request.get(sid, b"") + data
            if len(self.request[sid]) > 1000:
                SerialLog.log("Stream closed")
                self.close(s)
                return

            if data[-4:] != b"\r\n\r\n":
                SerialLog.log("Waiting for more data...", data)
                return

            req = self.parse_request(self.request.pop(sid))
            body, headers, shouldReboot = self.get_response(req)
            self.shouldReboot = shouldReboot
            self.prepare_write(s, body, headers)
        except Exception as e:
            SerialLog.log("Error reading from socket", e)
            self.close(s)

    def prepare_write(self, s, body, headers):
        headers += "\r\n"
        if isinstance(headers, str):
            headers = headers.encode("utf-8")

        gc.collect()
        buff = bytearray(536)  
        buffmv = memoryview(buff) 
        buff[:len(headers)] = headers
        bw = body.readinto(buffmv[len(headers):], 536 - len(headers))
        c = WriteConn(body, buff, buffmv, [0, len(headers) + bw])
        self.conns[id(s)] = c
        self.poller.modify(s, select.POLLOUT)

    def write_to(self, sock):
        c = self.conns[id(sock)]
        if c:
            try:
                bytes_written = sock.write(c.buffmv[c.write_range[0] : c.write_range[1]])
            except OSError as e:
                if e.errno == 128:
                    self.close(sock)
                if e.errno == 104:
                    self.close(sock)
                return
            if not bytes_written or c.write_range[1] < 536:
                self.close(sock)
                gc.collect()
            else:
                self.buff_advance(c, bytes_written)

    def buff_advance(self, c, bytes_written):
        if bytes_written == c.write_range[1] - c.write_range[0]:
            c.write_range[0] = 0
            c.write_range[1] = c.body.readinto(c.buff, 536)
        else:
            c.write_range[0] += bytes_written

    def close(self, s):
        s.close()
        self.poller.unregister(s)
        sid = id(s)
        if sid in self.request:
            del self.request[sid]
        if sid in self.conns:
            del self.conns[sid]
        if self.shouldReboot:
            machine.reset()

    def start(self):
        SerialLog.log("Web server started")

    def setRoutes(self, routes):
        self.routes = routes

    def tick(self):
        for response in self.poller.ipoll(0):
            sock, event, *others = response
            self.handle(sock, event, others)
