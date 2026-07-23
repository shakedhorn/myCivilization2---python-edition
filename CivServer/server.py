import socket
import json
import threading
import random
import hashlib
import copy
from CivShared.game_defs import *
from CivServer.game_logic import GameLogic

def dict_diff(old, new):
    if not isinstance(old, dict) or not isinstance(new, dict):
        return new if old != new else None
    diff = {}
    for k, v in new.items():
        if k not in old:
            diff[k] = v
        else:
            if isinstance(v, dict) and isinstance(old[k], dict):
                d = dict_diff(old[k], v)
                if d is not None:
                    diff[k] = d
            else:
                if old[k] != v:
                    diff[k] = v
    for k in old:
        if k not in new:
            diff[k] = "__DELETE__"
    return diff if diff else None

class GameServer:
    def __init__(self, port=54321):
        self.port = port
        self.clients = {}
        self.game = GameLogic(width=50, height=36)
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
                        sx, sy = random.randint(2, self.game.world.width - 3), random.randint(2, self.game.world.height - 3)
                        tile = self.game.world.map_data[sy][sx]
                        if tile.get("terrain") not in ["ocean", "coast", "mountains"]:
                            spawn_x, spawn_y = sx, sy
                            break
                            
                    # Spawn initial settler
                    unit_id = str(self.game.next_unit_id)
                    from CivServer.models.unit import Unit
                    self.game.units[unit_id] = Unit(unit_id, "settler", spawn_x, spawn_y, p_id)
                    self.game.next_unit_id += 1
                    
                    # 7x7 Starting Vision
                    p = self.game.players[p_id]
                    if not hasattr(p, 'explored_tiles'): p.explored_tiles = []
                    explored_set = set(tuple(x) for x in p.explored_tiles)
                    
                    sight = 3
                    for dy in range(-sight, sight + 1):
                        for dx in range(-sight, sight + 1):
                            if dx*dx + dy*dy <= 12: # rough 7x7 circle
                                nx = (spawn_x + dx) % self.game.world.width
                                ny = spawn_y + dy
                                if 0 <= ny < self.game.world.height:
                                    explored_set.add((nx, ny))
                    p.explored_tiles = list(explored_set)

    def filter_fow(self, state, player_id):
        if not getattr(self, "game_started", False):
            return state

        visible_tiles = self.game.get_visible_tiles(player_id)
        
        p = self.game.players.get(player_id)
        explored_tiles = set(tuple(x) for x in getattr(p, 'explored_tiles', [])) if p else set()
        
        for y, row in enumerate(state.get("world", {}).get("map_data", [])):
            for x, tile in enumerate(row):
                coord = (x, y)
                if coord in visible_tiles:
                    tile["visibility"] = "visible"
                elif coord in explored_tiles:
                    tile["visibility"] = "fog"
                else:
                    tile["visibility"] = "unexplored"
                    tile["terrain"] = "unknown"
                    tile["owner"] = -1
                    tile["improvement"] = None
                    tile["district"] = None
                    
        visible_units = {}
        for uid, u in state.get("units", {}).items():
            if (u["x"], u["y"]) in visible_tiles:
                visible_units[uid] = u
        state["units"] = visible_units
        
        visible_cities = {}
        for cid, c in state.get("cities", {}).items():
            if (c["x"], c["y"]) in visible_tiles or (c["x"], c["y"]) in explored_tiles:
                visible_cities[cid] = c
        state["cities"] = visible_cities
        
        return state

    def handle_client(self, conn, addr):
        player_id = None
        last_state = {}
        last_turn = -1

        try:
            # Login
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
                player_id = str(abs(hash(username)) % 1000)
                
                with self.lock:
                    if player_id not in self.game.players:
                        available_colors = [
                            (255, 50, 50),   (50, 50, 255),   (50, 255, 50),
                            (255, 255, 50),  (255, 50, 255),  (50, 255, 255),
                            (255, 150, 50),  (255, 255, 255),
                        ]
                        assigned_color = available_colors[len(self.game.players) % len(available_colors)]
                        
                        from CivServer.models.player import Player
                        new_player = Player(player_id, username, assigned_color)
                        new_player.gold = 50
                        self.game.players[player_id] = new_player
                
                resp = json.dumps({"status": "LOGIN_OK", "id": player_id}).encode()
                conn.sendall(len(resp).to_bytes(4, 'big') + resp)
            else:
                conn.sendall(json.dumps({"status": "ERROR"}).encode())
                return

            # Game Loop
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
                        current_state = self.game.to_json()
                        current_state["game_started"] = getattr(self, "game_started", False)
                        
                        # Apply FoW
                        current_state = self.filter_fow(current_state, player_id)
                        
                        if current_state["turn"] > last_turn:
                            # Send Checksum
                            state_str = json.dumps(current_state, sort_keys=True)
                            chk = hashlib.md5(state_str.encode()).hexdigest()
                            resp = json.dumps({"type": "CHECKSUM", "turn": current_state["turn"], "hash": chk}).encode()
                            last_turn = current_state["turn"]
                            last_state = copy.deepcopy(current_state)
                        else:
                            # Send Delta
                            delta = dict_diff(last_state, current_state)
                            if delta is None: delta = {}
                            resp = json.dumps({"type": "DELTA", "data": delta}).encode()
                            last_state = copy.deepcopy(current_state)
                            
                        conn.sendall(len(resp).to_bytes(4, 'big') + resp)

                    elif cmd == "REQUEST_FULL_STATE":
                        with self.lock:
                            current_state = self.game.to_json()
                            current_state["game_started"] = getattr(self, "game_started", False)
                            current_state = self.filter_fow(current_state, player_id)
                            resp = json.dumps({"type": "FULL_STATE", "data": current_state}).encode()
                            last_state = copy.deepcopy(current_state)
                            last_turn = current_state["turn"]
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
            if player_id and player_id in self.game.players:
                if not getattr(self, "game_started", False):
                    # Only delete from lobby if the game hasn't started yet
                    del self.game.players[player_id]
                elif self.game.turn_count > 1:
                    self.game.players[player_id].eliminated = True
                    active_players = [p_id for p_id, p in self.game.players.items() if not p.eliminated]
                    if len(active_players) == 1:
                        self.game.players[active_players[0]].winner = "Domination"
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
