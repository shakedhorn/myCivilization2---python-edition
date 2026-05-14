import socket
import json
import threading
import random
from CivShared.game_defs import *
from CivServer.game_logic import GameState

class GameServer:
    def __init__(self):
        self.clients = {}
        self.game = GameState(width=20, height=20)
        self.lock = threading.Lock()
        self.next_unit_id = 1
        self.create_initial_map(20, 20)

    def create_initial_map(self, w, h):
        self.game.map = []
        for y in range(h):
            row = []
            for x in range(w):
                is_polar = (y <= 1 or y >= h - 2)
                # Earth probability: ~71% water, 29% land
                if random.random() < 0.71:
                    terrain = random.choices(["ocean", "coast"], weights=[80, 20])[0]
                else:
                    if is_polar:
                        terrain = random.choices(["snow", "tundra"], weights=[50, 50])[0]
                    else:
                        terrain = random.choices(
                            ["desert", "forest", "grassland", "plains", "hills", "mountains"],
                            weights=[33, 31, 10, 10, 10, 6]
                        )[0]
                row.append({"terrain": terrain, "owner": -1, "improvement": None})
            self.game.map.append(row)

    def handle_client(self, conn, addr):
        player_id = None
        try:
            # שלב 1: LOGIN
            raw_login = conn.recv(1024).decode()
            if not raw_login: return
            login_msg = json.loads(raw_login)
            
            if login_msg.get("type") == "LOGIN":
                username = login_msg.get("user", "Unknown")
                # המרה ל-string כדי למנוע בלבול במפתחות של JSON
                player_id = str(abs(hash(username)) % 1000)
                
                with self.lock:
                    if player_id not in self.game.players:
                        self.game.players[player_id] = {
                            "name": username, "gold": 50, "techs": [], "civics": []
                        }
                        # יצירת Settler התחלתי לשחקן חדש
                        self.game.units[str(self.next_unit_id)] = {
                            "type": "settler", "owner": player_id, "x": random.randint(2, 17), 
                            "y": random.randint(2, 17), "hp": 100
                        }
                        self.next_unit_id += 1
                
                conn.sendall(json.dumps({"status": "LOGIN_OK", "id": player_id}).encode())
            else:
                conn.sendall(json.dumps({"status": "ERROR"}).encode())
                return

            # שלב 2: לולאת המשחק
            while True:
                raw_len = conn.recv(4)
                if not raw_len: break
                msg_len = int.from_bytes(raw_len, byteorder='big')
                data = b""
                while len(data) < msg_len:
                    data += conn.recv(msg_len - len(data))
                
                msg = json.loads(data.decode())
                cmd = msg.get("type")
                with self.lock:
                    if cmd == "UPDATE_ALL":
                        sync_data = self.game.get_sync_data()
                        resp = json.dumps(sync_data).encode()
                        conn.sendall(len(resp).to_bytes(4, 'big') + resp)
                    
                    elif cmd == "MOVE_UNIT":
                        self.game.handle_command(player_id, "MOVE_UNIT", msg)

                    elif cmd == "FOUND_CITY":
                        success = self.game.handle_command(player_id, "FOUND_CITY", msg)
                        if success:
                            print(f"City built successfully for {player_id}")

        except Exception as e:
            print(f"Error with player {player_id}: {e}")
        finally:
            conn.close()

    def start(self, port=54321):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', port))
        server.listen()
        print(f"Server started on port {port}")
        while True:
            conn, addr = server.accept()
            threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    GameServer().start()