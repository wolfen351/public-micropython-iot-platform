import hashlib
import ubinascii
import uselect as select
import usocket as socket
import ustruct as struct
from serial_log import SerialLog
import json
import gc

class WebSocketServer:
    def __init__(self, poller, port=81):
        self.poller = poller
        self.clients = {}
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_sock.bind(('0.0.0.0', port))
        self.server_sock.listen(2)
        self.server_sock.setblocking(False)
        self.poller.register(self.server_sock, select.POLLIN)
        SerialLog.log("WebSocket server listening on port", port)

    def handle(self, sock, event):
        if sock is self.server_sock:
            self._accept_connection()
        elif event & select.POLLIN:
            self._handle_client_data(sock)
        elif event & select.POLLHUP or event & select.POLLERR:
            self._close_client(sock)

    def _accept_connection(self):
        try:
            client_sock, addr = self.server_sock.accept()
            client_sock.setblocking(False)
            self.poller.register(client_sock, select.POLLIN)
            self.clients[id(client_sock)] = {
                'sock': client_sock,
                'addr': addr,
                'handshake_done': False
            }
            SerialLog.log("WebSocket client connected:", addr)
        except OSError:
            pass

    def _handle_client_data(self, sock):
        client_id = id(sock)
        if client_id not in self.clients:
            return
            
        client = self.clients[client_id]
        
        try:
            data = sock.recv(1024)
            if not data:
                self._close_client(sock)
                return

            if not client['handshake_done']:
                self._handle_handshake(sock, data)
            else:
                self._handle_websocket_frame(sock, data)
                
        except OSError:
            self._close_client(sock)

    def _handle_handshake(self, sock, data):
        client_id = id(sock)
        try:
            # Parse HTTP headers
            headers = {}
            lines = data.decode('utf-8').split('\r\n')
            
            for line in lines[1:]:
                if ':' in line:
                    key, value = line.split(':', 1)
                    headers[key.strip().lower()] = value.strip()

            if 'sec-websocket-key' in headers:
                # Generate WebSocket accept key
                ws_key = headers['sec-websocket-key']
                accept_key = self._generate_accept_key(ws_key)
                
                # Send handshake response
                response = (
                    "HTTP/1.1 101 Switching Protocols\r\n"
                    "Upgrade: websocket\r\n"
                    "Connection: Upgrade\r\n"
                    f"Sec-WebSocket-Accept: {accept_key}\r\n"
                    "\r\n"
                )
                
                sock.send(response.encode('utf-8'))
                self.clients[client_id]['handshake_done'] = True
                SerialLog.log("WebSocket handshake completed for client", client_id, "- Total clients:", len(self.clients))
            else:
                SerialLog.log("WebSocket handshake failed: missing sec-websocket-key")
                self._close_client(sock)
                
        except Exception as e:
            SerialLog.log("WebSocket handshake error:", e)
            self._close_client(sock)

    def _generate_accept_key(self, ws_key):
        # WebSocket magic string
        magic = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
        combined = ws_key + magic
        
        # Create SHA1 hash
        sha1 = hashlib.sha1()
        sha1.update(combined.encode('utf-8'))
        digest = sha1.digest()
        
        # Encode to base64
        return ubinascii.b2a_base64(digest).decode('utf-8').strip()

    def _handle_websocket_frame(self, sock, data):
        if len(data) < 2:
            return
            
        # Simple frame parsing - assumes small frames for telemetry
        # In a full implementation, you'd handle fragmentation, masking, etc.
        opcode = data[0] & 0x0F
        
        if opcode == 0x8:  # Close frame
            self._close_client(sock)
        elif opcode == 0x9:  # Ping frame
            # Send pong
            pong_frame = bytes([0x8A, 0x00])
            sock.send(pong_frame)

    def _close_client(self, sock):
        client_id = id(sock)
        if client_id in self.clients:
            SerialLog.log("WebSocket client disconnected:", self.clients[client_id]['addr'])
            try:
                self.poller.unregister(sock)
            except:
                pass
            try:
                sock.close()
            except:
                pass
            del self.clients[client_id]
            SerialLog.log("WebSocket clients remaining:", len(self.clients))

    def broadcast_telemetry(self, telemetry_data):
        """Send telemetry data to all connected WebSocket clients"""
        if not self.clients:
            return
            
        try:
            # Convert telemetry to JSON
            json_data = json.dumps(telemetry_data)
            message_bytes = json_data.encode('utf-8')
            
            # Create WebSocket frame
            frame = self._create_frame(message_bytes)
            
            # Send to all connected clients
            clients_to_remove = []
            for client_id, client in self.clients.items():
                if client['handshake_done']:
                    try:
                        client['sock'].send(frame)
                    except OSError as e:
                        SerialLog.log("WebSocket send error for client", client_id, ":", e)
                        clients_to_remove.append(client['sock'])
                    except Exception as e:
                        SerialLog.log("WebSocket unexpected error for client", client_id, ":", e)
                        clients_to_remove.append(client['sock'])
            
            # Remove disconnected clients
            for sock in clients_to_remove:
                self._close_client(sock)
                
            gc.collect()
            
        except Exception as e:
            SerialLog.log("Error broadcasting telemetry:", e)

    def _create_frame(self, payload):
        """Create a WebSocket frame for sending data"""
        payload_len = len(payload)
        
        # Text frame (opcode 0x1), final frame (FIN=1)
        frame = bytearray([0x81])
        
        if payload_len < 126:
            frame.append(payload_len)
        elif payload_len < 65536:
            frame.append(126)
            frame.extend(struct.pack('!H', payload_len))
        else:
            frame.append(127)
            frame.extend(struct.pack('!Q', payload_len))
            
        frame.extend(payload)
        return bytes(frame)

    def stop(self):
        """Stop the WebSocket server"""
        # Close all client connections
        for client_id, client in list(self.clients.items()):
            self._close_client(client['sock'])
        
        # Close server socket
        try:
            self.poller.unregister(self.server_sock)
        except:
            pass
        try:
            self.server_sock.close()
        except:
            pass
        
        SerialLog.log("WebSocket server stopped")

    def tick(self):
        """Process WebSocket events - called from main event loop"""
        # This is handled by the main poller in web_server.py
        pass
