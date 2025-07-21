import machine
from serial_log import SerialLog
import uerrno
import uio
import uselect as select
import usocket as socket
from collections import namedtuple
import gc

WriteConn = namedtuple("WriteConn", ["body", "buff", "buffmv", "write_range"])
ReqInfo = namedtuple("ReqInfo", ["type", "path", "params", "host", "post_params"])

from modules.web.server import Server
from modules.web.websocket_server import WebSocketServer

class WebServer():
    def __init__(self):
        self.poller = select.poll()
        self.httpServer = Server(self.poller, 80, socket.SOCK_STREAM)
        self.websocketServer = WebSocketServer(self.poller, 81)
        self.request = dict()
        self.conns = dict()

        # queue up to 2 connection requests before refusing
        self.httpServer.sock.listen(2)
        self.httpServer.sock.setblocking(False)

        self.shouldReboot = False

    def handle(self, sock, event, others):
        if sock is self.httpServer.sock:
            self.accept(sock)
        elif sock is self.websocketServer.server_sock:
            self.websocketServer.handle(sock, event)
        elif sock in [client['sock'] for client in self.websocketServer.clients.values()]:
            self.websocketServer.handle(sock, event)
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
        allDataLines = req.split(b"\r\n")
        httpVerb, reqUrl, httpVersion = allDataLines[0].split(b" ")
        reqPath = reqUrl.split(b"?")
        SerialLog.log("Web:", httpVerb, reqPath)
        basePath = reqPath[0]
        queryString = reqPath[1] if len(reqPath) > 1 else None
        query_params = (
            {
                key: val
                for key, val in [param.split(b"=") for param in queryString.split(b"&")]
            }
            if queryString
            else {}
        )

        host = [line.split(b": ")[1] for line in allDataLines if b"Host:" in line][0]

        # Initialize post_params as an empty array
        post_params = []

        # If the request method is POST, parse the body
        if httpVerb == b"POST":
            # Get the content length
            contentLength = int([line.split(b": ")[1] for line in allDataLines if b"Content-Length:" in line][0])

            # Get the content type
            contentType = [line.split(b": ")[1] for line in allDataLines if b"Content-Type:" in line][0]

            # Get the boundary
            multipartBoundary = contentType.split(b"boundary=")[1]

            # extract each part
            rawparts = req.split(b"--" + multipartBoundary)
            for part in rawparts:

                if part == b"" or part == b"--\r\n":
                    continue

                # Get the headers and the body
                bits = part.split(b"\r\n\r\n")
                headers = bits[0]
                body = b"\r\n\r\n".join(bits[1:])

                headers = headers.split(b"\r\n")

                # If the body is empty or just 2 chars long, skip
                if len(body) <= 2:
                    continue

                # Remove the last two characters from the body
                body = body[:-2]

                # Trim whitespace from the body
                body = body.strip()

                # Get the name of the field
                name = [line.split(b"; ")[1] for line in headers if b"name=" in line][0].split(b'"')[1]

                # Get the filename of the field
                filename = None
                # if any header contains filename, get the filename
                for line in headers:
                    if b"filename=" in line:
                        filename = line.split(b"; ")[2].split(b'"')[1]
                        post_params.append({ "name": name, "filename": filename, "filedata": body })
                        break

                # If the filename is None, it is a regular field
                if filename is None:
                    post_params.append({ "name": name, "value": body })

        return ReqInfo(httpVerb, basePath, query_params, host, post_params)

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
                if (req.type == b"POST"):
                    response = route(req.params, req.post_params)
                else:
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

            # log the data
            # SerialLog.log("Data received", data)

            sid = id(s)
            self.request[sid] = self.request.get(sid, b"") + data
            if len(self.request[sid]) > 10000:
                SerialLog.log("Stream closed (too much data)")
                self.close(s)
                return

            if data[-4:] != b"\r\n\r\n" and data[-4:] != b"--\r\n":
                SerialLog.log("Waiting for more data...", len(data), "bytes received")
                return

            SerialLog.log("Request received, id:", sid, " Length:", len(self.request[sid]))
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

    def stop(self):
        """Stop the web server and WebSocket server"""
        self.websocketServer.stop()
        self.httpServer.stop(self.poller)

    def start(self):
        SerialLog.log("Web server started")

    def setRoutes(self, routes):
        self.routes = routes

    def tick(self):
        for response in self.poller.ipoll(0):
            sock, event, *others = response
            self.handle(sock, event, others)

    def broadcast_telemetry(self, telemetry_data):
        """Broadcast telemetry data to WebSocket clients"""
        self.websocketServer.broadcast_telemetry(telemetry_data)
