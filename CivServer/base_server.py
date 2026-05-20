import socket
import json
import threading
import sys
import os

# Ensure the parent directory is in sys.path so we can import CivServer.server
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from CivServer.server import GameServer

class BaseServer:
    def __init__(self, host='0.0.0.0', port=54321):
        self.host = host
        self.port = port
        self.games = {}  # "game_name": port
        self.game_threads = {}
        self.next_port = 54322
        self.lock = threading.Lock()

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen()
        print(f"Base Server started on {self.host}:{self.port}")
        
        while True:
            try:
                conn, addr = server.accept()
                threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()
            except Exception as e:
                print(f"Base Server accept error: {e}")

    def handle_client(self, conn, addr):
        try:
            raw_msg = conn.recv(1024).decode()
            if not raw_msg: return
            msg = json.loads(raw_msg)
            
            cmd = msg.get("type")
            
            if cmd == "LOGIN":
                # Just acknowledge login and send game list
                self.send_response(conn, {"status": "LOGIN_OK", "games": list(self.games.keys())})
            
            elif cmd == "CREATE_GAME":
                game_name = msg.get("name")
                if not game_name:
                    self.send_response(conn, {"status": "ERROR", "message": "Game name required"})
                    return
                
                with self.lock:
                    if game_name in self.games:
                        self.send_response(conn, {"status": "ERROR", "message": "Game already exists"})
                    else:
                        port = self.next_port
                        self.next_port += 1
                        
                        # Start game server
                        gs = GameServer(port=port)
                        t = threading.Thread(target=gs.start, daemon=True)
                        t.start()
                        
                        self.games[game_name] = port
                        self.game_threads[game_name] = t
                        
                        self.send_response(conn, {"status": "JOIN_SUCCESS", "port": port})
            
            elif cmd == "JOIN_GAME":
                game_name = msg.get("name")
                with self.lock:
                    if game_name in self.games:
                        port = self.games[game_name]
                        self.send_response(conn, {"status": "JOIN_SUCCESS", "port": port})
                    else:
                        self.send_response(conn, {"status": "ERROR", "message": "Game not found"})
            else:
                self.send_response(conn, {"status": "ERROR", "message": "Unknown command"})
                
        except Exception as e:
            print(f"Error handling client {addr}: {e}")
        finally:
            conn.close()

    def send_response(self, conn, data):
        conn.sendall(json.dumps(data).encode())

if __name__ == "__main__":
    BaseServer().start()
