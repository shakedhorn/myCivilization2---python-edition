import socket
import json
import time
import hashlib
import copy

def apply_delta(state, delta):
    if not isinstance(delta, dict):
        return delta
    for k, v in delta.items():
        if v == "__DELETE__":
            if k in state:
                del state[k]
        elif isinstance(v, dict) and k in state and isinstance(state[k], dict):
            apply_delta(state[k], v)
        else:
            state[k] = v

class Network:
    def __init__(self, app):
        self.app = app
        self.sock = None

    def send_net_msg(self, msg_dict):
        if not self.sock: return
        try:
            data = json.dumps(msg_dict).encode()
            self.sock.sendall(len(data).to_bytes(4, 'big') + data)
        except Exception as e:
            print("Net send error:", e)

    def connect(self, ip, port):
        self.app.server_ip = ip
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((ip, port))

    def login(self, username):
        self.sock.sendall(json.dumps({"type": "LOGIN", "user": username}).encode())
        resp_raw = self.sock.recv(1024)
        if resp_raw:
            return json.loads(resp_raw.decode())
        return None

    def close(self):
        if self.sock:
            self.sock.close()
            self.sock = None

    def recv_json(self):
        if not self.sock: 
            return None
        try:
            resp_raw = self.sock.recv(1024)
            if resp_raw:
                return json.loads(resp_raw.decode())
        except Exception as e:
            print("Net recv error:", e)
        return None

    def recv_prefixed_json(self):
        if not self.sock: return None
        try:
            raw_len = self.sock.recv(4)
            if not raw_len: return None
            msg_len = int.from_bytes(raw_len, 'big')
            data = b""
            while len(data) < msg_len:
                packet = self.sock.recv(msg_len - len(data))
                if not packet: return None
                data += packet
            return json.loads(data.decode())
        except Exception as e:
            print("Net prefixed recv error:", e)
        return None

    def network_loop(self):
        while True:
            try:
                if self.app.game_state is None:
                    self.send_net_msg({"type": "REQUEST_FULL_STATE"})
                else:
                    self.send_net_msg({"type": "UPDATE_ALL"})
                    
                raw_len = self.sock.recv(4)
                if not raw_len: break
                msg_len = int.from_bytes(raw_len, 'big')
                data = b""
                while len(data) < msg_len:
                    data += self.sock.recv(msg_len - len(data))
                
                msg = json.loads(data.decode())
                
                if msg.get("type") == "FULL_STATE":
                    self.app.game_state = msg["data"]
                elif msg.get("type") == "DELTA":
                    if self.app.game_state is not None:
                        apply_delta(self.app.game_state, msg["data"])
                elif msg.get("type") == "CHECKSUM":
                    if self.app.game_state is not None:
                        # Client-side checksum validation
                        state_str = json.dumps(self.app.game_state, sort_keys=True)
                        my_chk = hashlib.md5(state_str.encode()).hexdigest()
                        
                        if my_chk != msg["hash"]:
                            print("Checksum MISMATCH! Requesting full state resync...")
                            self.send_net_msg({"type": "REQUEST_FULL_STATE"})
                        else:
                            print("Checksum OK!")
                
                time.sleep(0.1)
            except Exception as e:
                print("Network loop ended:", e)
                break
