import socket
import json
import threading
import random
from CivShared.game_defs import *
from CivServer.game_logic import GameState

class GameServer:
    def __init__(self, port=54321):
        self.port = port
        self.clients = {}
        self.game = GameState(width=50, height=36)
        self.game_started = False
        self.lock = threading.RLock()

    def _check_start_game(self):
        with self.lock:
            if not self.game_started and len(self.game.players) >= 2:
                self.game_started = True
                for p_id in self.game.players:
                    # Find a valid land tile for starting spawn
                    spawn_x, spawn_y = 5, 5
                    for _ in range(100):
                        sx, sy = random.randint(2, self.game.width - 3), random.randint(2, self.game.height - 3)
                        if self.game.map[sy][sx]["terrain"] not in ["ocean", "coast", "mountains"]:
                            spawn_x, spawn_y = sx, sy
                            break
                            
                    # יצירת Settler התחלתי לשחקן
                    self.game.units[str(self.game.next_unit_id)] = {
                        "type": "settler", "owner": p_id, "x": spawn_x, 
                        "y": spawn_y, "hp": 100, "has_moved": False
                    }
                    self.game.next_unit_id += 1

    def handle_client(self, conn, addr):
        player_id = None
        try:
            # שלב 1: LOGIN
            raw_len = conn.recv(4)
            if not raw_len: return
            msg_len = int.from_bytes(raw_len, byteorder='big')
            data = b""
            while len(data) < msg_len:
                packet = conn.recv(msg_len - len(data))
                if not packet: return
                data += packet
            login_msg = json.loads(data.decode())
            
            if login_msg.get("type") == "LOGIN":
                username = login_msg.get("user", "Unknown")
                # המרה ל-string כדי למנוע בלבול במפתחות של JSON
                player_id = str(abs(hash(username)) % 1000)
                
                with self.lock:
                    if player_id not in self.game.players:
                        available_colors = [
                            (255, 50, 50),   # Red
                            (50, 50, 255),   # Blue
                            (50, 255, 50),   # Green
                            (255, 255, 50),  # Yellow
                            (255, 50, 255),  # Purple
                            (50, 255, 255),  # Cyan
                            (255, 150, 50),  # Orange
                            (255, 255, 255), # White
                        ]
                        assigned_color = available_colors[len(self.game.players) % len(available_colors)]
                        
                        self.game.players[player_id] = {
                            "name": username, "gold": 50, "science": 0, "culture": 0, "production": 0,
                            "techs": [], "civics": [], "ended_turn": False,
                            "current_research": None, "research_progress": 0,
                            "current_civic": None, "civic_progress": 0,
                            "color": assigned_color
                        }

                
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
                        self._check_start_game()
                        sync_data = self.game.get_sync_data()
                        sync_data["game_started"] = getattr(self, "game_started", False)
                        resp = json.dumps(sync_data).encode()
                        conn.sendall(len(resp).to_bytes(4, 'big') + resp)
                    
                    elif cmd == "MOVE_UNIT":
                        self.game.handle_command(player_id, "MOVE_UNIT", msg)

                    elif cmd == "FOUND_CITY":
                        success = self.game.handle_command(player_id, "FOUND_CITY", msg)
                        if success:
                            print(f"City built successfully for {player_id}")
                            
                    elif cmd in ["END_TURN", "SKIP_UNIT_TURN", "FORTIFY_HEAL", "RANGED_ATTACK", "CHANGE_PRODUCTION", "BUILD_IMPROVEMENT", "CHOOSE_RESEARCH", "CHOOSE_CIVIC"]:
                        self.game.handle_command(player_id, cmd, msg)

        except Exception as e:
            print(f"Error with player {player_id}: {e}")
        finally:
            conn.close()

    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(('0.0.0.0', self.port))
        server.listen()
        print(f"Game Server started on port {self.port}")
        while True:
            conn, addr = server.accept()
            threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True).start()

if __name__ == "__main__":
    GameServer().start()