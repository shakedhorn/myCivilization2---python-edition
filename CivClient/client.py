import pygame
import socket
import json
import threading
import time
import math
from CivShared.game_defs import GameData

TERRAIN_COLORS = {
    "grassland": (106, 186, 76),
    "plains": (200, 180, 100),
    "desert": (240, 230, 140),
    "tundra": (180, 200, 200),
    "snow": (250, 250, 250),
    "hills": (139, 137, 137),
    "mountains": (100, 100, 100),
    "coast": (100, 200, 250),
    "ocean": (20, 100, 180),
    "forest": (34, 100, 34)
}

class CivClient:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1024, 768))
        pygame.display.set_caption("My Civilization 2 - Python Edition")
        
        # טעינת גופנים
        self.font_title = pygame.font.SysFont("Impact", 100)
        self.font_main = pygame.font.SysFont("Arial", 32, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 20)
        
        self.sock = None
        self.game_state = None
        self.my_id = None
        self.state = "SPLASH"
        self.input_text = ""
        self.username = ""
        self.selected_unit_id = None
        self.selected_city_id = None
        self.camera_x = 0
        self.camera_y = 0
        self.tile_size = 32
        self.target_mode = None
        self.start_time = time.time()
        self.games_list = []
        self.city_build_scroll_y = 0
        self.active_panel = "MAP"
        self.tree_scroll_y = 0
        self.tree_scroll_x = 0
        self.server_ip = ""
        self.clock = pygame.time.Clock()


    def get_tree_layout(self, items_dict, is_tech):
        import math
        layout = {}
        tiers = {}
        req_key = "required_techs" if is_tech else "required_civics"
        
        def get_tier(k):
            if k in tiers: return tiers[k]
            reqs = items_dict[k].get(req_key, [])
            if not reqs:
                tiers[k] = 0
                return 0
            t = max(get_tier(r) for r in reqs if r in items_dict) + 1
            tiers[k] = t
            return t

        for key in items_dict: get_tier(key)
        
        tier_groups = {}
        for k, t in tiers.items():
            tier_groups.setdefault(t, []).append(k)
            
        card_w, card_h = 240, 140
        margin_x, margin_y = 60, 20
        
        current_x = 50
        for t in sorted(tier_groups.keys()):
            items_in_tier = tier_groups[t]
            if t > 0:
                def avg_parent_y(node):
                    reqs = items_dict[node].get(req_key, [])
                    valid_reqs = [r for r in reqs if r in layout]
                    if not valid_reqs: return 0
                    return sum(layout[r][1] for r in valid_reqs) / len(valid_reqs)
                items_in_tier.sort(key=avg_parent_y)
                
            max_per_col = 3
            num_items = len(items_in_tier)
            
            for idx, key in enumerate(items_in_tier):
                col_offset = idx // max_per_col
                row_idx = idx % max_per_col
                
                cx = current_x + (col_offset * (card_w + 20))
                cy = 120 + row_idx * (card_h + margin_y)
                layout[key] = (cx, cy)
                
            cols_needed = math.ceil(num_items / max_per_col) if num_items > 0 else 1
            current_x += cols_needed * (card_w + margin_x)
                
        return layout

    def send_net_msg(self, msg_dict):
        if not self.sock: return
        data = json.dumps(msg_dict).encode()
        self.sock.sendall(len(data).to_bytes(4, 'big') + data)

    def network_loop(self):
        while True:
            try:
                self.send_net_msg({"type": "UPDATE_ALL"})
                raw_len = self.sock.recv(4)
                if not raw_len: break
                msg_len = int.from_bytes(raw_len, 'big')
                data = b""
                while len(data) < msg_len:
                    data += self.sock.recv(msg_len - len(data))
                self.game_state = json.loads(data.decode())
                time.sleep(0.1)
            except: break

    def draw_text_centered(self, text, y, font, color, shadow=True):
        if shadow:
            shadow_surf = font.render(text, True, (20, 20, 20))
            self.screen.blit(shadow_surf, (512 - shadow_surf.get_width()//2 + 4, y + 4))
        surf = font.render(text, True, color)
        self.screen.blit(surf, (512 - surf.get_width()//2, y))

    def draw_minecraft_box(self, x, y, w, h, title):
        # תיבה מרחפת עם שקיפות
        box_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        box_surf.fill((0, 0, 0, 180)) 
        self.screen.blit(box_surf, (x, y))
        pygame.draw.rect(self.screen, (255, 255, 255), (x, y, w, h), 2)
        
        t_surf = self.font_small.render(title, True, (255, 215, 0))
        self.screen.blit(t_surf, (x + 20, y + 20))

    def run(self):
        running = True
        while running:
            # צבע רקע בסיסי
            self.screen.fill((20, 20, 40))
            
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT: running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if self.state == "CONNECT":
                            try:
                                ip, port = self.input_text.split(":")
                                self.server_ip = ip
                                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                self.sock.connect((ip, int(port)))
                                self.state = "LOGIN"
                                self.input_text = ""
                            except: self.input_text = "ERROR: IP:PORT"
                        elif self.state == "LOGIN":
                            self.username = self.input_text
                            # שולחים לוגין לשרת הבסיס
                            self.sock.sendall(json.dumps({"type": "LOGIN", "user": self.username}).encode())
                            
                            resp_raw = self.sock.recv(1024)
                            if resp_raw:
                                resp = json.loads(resp_raw.decode())
                                if resp["status"] == "LOGIN_OK":
                                    self.games_list = resp.get("games", [])
                                    self.state = "LOBBY"
                                    self.input_text = ""
                                    self.sock.close() 
                            else:
                                self.input_text = "ERROR: SERVER DISCONNECTED"
                        elif self.state == "LOBBY":
                            game_name = self.input_text
                            
                            try:
                                # 1. פתיחת סוקט חדש מול שרת הבסיס כי הקודם נסגר
                                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                self.sock.connect((self.server_ip, 54321)) # תמיד להתחבר לפורט הראשי של השרת בסיס
                                
                                # 2. שליחת הבקשה (יצירה או הצטרפות)
                                if game_name in self.games_list:
                                    self.sock.sendall(json.dumps({"type": "JOIN_GAME", "name": game_name}).encode())
                                else:
                                    self.sock.sendall(json.dumps({"type": "CREATE_GAME", "name": game_name}).encode())
                                
                                # 3. קבלת הפורט של שרת המשחק הייעודי
                                resp = json.loads(self.sock.recv(1024).decode())
                                
                                if resp.get("status") == "JOIN_SUCCESS":
                                    port = resp["port"]
                                    self.sock.close()  # סוגרים את החיבור לשרת הבסיס, סיימנו איתו
                                    
                                    # 4. מתחברים לשרת המשחק האמיתי שנוצר (הפורט החדש שקיבלנו)
                                    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                    self.sock.connect((self.server_ip, port))
                                    
                                    # 5. התחברות (Login) לשרת המשחק
                                    self.send_net_msg({"type": "LOGIN", "user": self.username})
                                    game_resp = json.loads(self.sock.recv(1024).decode())
                                    
                                    if game_resp.get("status") == "LOGIN_OK":
                                        self.my_id = str(game_resp["id"])
                                        self.state = "GAME"
                                        # מעכשיו הסוקט נשאר פתוח קבוע והרשת רצה ברקע
                                        threading.Thread(target=self.network_loop, daemon=True).start()
                                else:
                                    self.input_text = "ERROR: " + resp.get("message", "FAILED")
                                    self.sock.close()
                                    
                            except Exception as e:
                                self.input_text = f"CONN ERROR: {e}"
                        else:
                            self.input_text = "ERROR: " + resp.get("message", "FAILED")
                    elif event.key == pygame.K_BACKSPACE: self.input_text = self.input_text[:-1]
                    elif event.key == pygame.K_SPACE and self.state == "GAME" and self.game_state and self.game_state.get("game_started", False):
                        if self.selected_unit_id:
                            self.send_net_msg({"type": "SKIP_UNIT_TURN", "unit_id": self.selected_unit_id})
                    else: self.input_text += event.unicode
                elif event.type == pygame.MOUSEMOTION and self.state == "GAME" and self.game_state and self.game_state.get("game_started", False):
                    if event.buttons[0] or event.buttons[1] or event.buttons[2]: # Any mouse button held
                        self.camera_x -= event.rel[0]
                        self.camera_y -= event.rel[1]
                        
                        # Clamp camera to map bounds (only Y axis, X wraps infinitely!)
                        if self.game_state and "map" in self.game_state:
                            map_pixel_w = len(self.game_state["map"][0]) * self.tile_size
                            map_height = len(self.game_state["map"]) * self.tile_size
                            max_y = max(0, map_height - 560) # Game area is 560px tall (600 bottom - 40 top)
                            
                            self.camera_x %= map_pixel_w
                            self.camera_y = max(0, min(self.camera_y, max_y))
                            
                elif event.type == pygame.MOUSEBUTTONDOWN and self.state == "GAME" and self.game_state and self.game_state.get("game_started", False):
                    mx, my = pygame.mouse.get_pos()
                    
                    if my < 40:
                        if event.button == 1:
                            if 600 <= mx <= 700:
                                self.active_panel = "MAP"
                            elif 720 <= mx <= 860:
                                self.active_panel = "TECH"
                            elif 880 <= mx <= 1020:
                                self.active_panel = "CIVIC"
                        continue
                        
                    if self.active_panel in ["TECH", "CIVIC"] and 40 <= my < 600:
                        mods = pygame.key.get_mods()
                        if event.button == 4:
                            if mods & pygame.KMOD_SHIFT:
                                self.tree_scroll_y = min(0, self.tree_scroll_y + 40)
                            else:
                                self.tree_scroll_x = min(0, self.tree_scroll_x + 40)
                        elif event.button == 5:
                            if mods & pygame.KMOD_SHIFT:
                                self.tree_scroll_y -= 40
                            else:
                                self.tree_scroll_x -= 40
                        elif event.button == 1:
                            is_tech = (self.active_panel == "TECH")
                            items = GameData.TECHS if is_tech else GameData.CIVICS
                            layout = self.get_tree_layout(items, is_tech)
                            
                            for key, (cx, cy) in layout.items():
                                rect = pygame.Rect(cx + self.tree_scroll_x, cy + self.tree_scroll_y, 240, 140)
                                if rect.collidepoint(mx, my):
                                    if is_tech:
                                        self.send_net_msg({"type": "CHOOSE_RESEARCH", "tech": key})
                                    else:
                                        self.send_net_msg({"type": "CHOOSE_CIVIC", "civic": key})
                        continue
                    
                    if my >= 600:
                        # לחיצה על ה-UI
                        if event.button == 1:
                            if self.selected_unit_id:
                                unit = self.game_state["units"].get(self.selected_unit_id)
                                if unit and not unit.get("has_moved"):
                                    unit_info = GameData.UNITS.get(unit["type"], {})
                                    if unit_info.get("name") == "Settler":
                                        btn_rect = pygame.Rect(250, 620, 150, 40)
                                        if btn_rect.collidepoint(mx, my):
                                            self.send_net_msg({"type": "FOUND_CITY", "unit_id": self.selected_unit_id})
                                    elif unit_info.get("range", 0) > 0:
                                        btn_rect = pygame.Rect(250, 620, 150, 40)
                                        if btn_rect.collidepoint(mx, my):
                                            self.target_mode = None if self.target_mode == "ATTACK" else "ATTACK"
                                    elif unit_info.get("name") == "Builder":
                                        ux, uy = unit["x"], unit["y"]
                                        tile = self.game_state["map"][uy][ux]
                                        t_type = tile["terrain"]
                                        has_imp = tile.get("improvement") is not None
                                        charges = unit.get("charges", 0)
                                        
                                        if not has_imp and charges > 0:
                                            possible = []
                                            me = self.game_state.get("players", {}).get(self.my_id, {})
                                            my_techs = me.get("techs", [])
                                            if tile.get("owner") == self.my_id:
                                                for imp_id, imp_data in GameData.IMPROVEMENTS.items():
                                                    if t_type in imp_data.get("valid_terrains", []) and (not imp_data.get("required_tech") or imp_data["required_tech"] in my_techs):
                                                        possible.append((imp_data["name"], imp_id))
                                            
                                            for idx, (label, imp_id) in enumerate(possible):
                                                bx = 250 + idx * 150
                                                btn_rect = pygame.Rect(bx, 620, 140, 40)
                                                if btn_rect.collidepoint(mx, my):
                                                    self.send_net_msg({"type": "BUILD_IMPROVEMENT", "unit_id": self.selected_unit_id, "improvement": imp_id})
                                            
                            # End Turn Button logic
                            me = self.game_state.get("players", {}).get(self.my_id, {})
                            if not me.get("ended_turn", False):
                                my_units = [u for u in self.game_state["units"].values() if u["owner"] == self.my_id]
                                all_moved = all(u.get("has_moved", False) for u in my_units)
                                
                                my_cities = [c for c in self.game_state.get("cities", {}).values() if c["owner"] == self.my_id]
                                all_producing = all(c.get("production_item") is not None for c in my_cities)
                                
                                if all_moved and all_producing:
                                    if me.get("current_research") is None:
                                        end_btn_rect = pygame.Rect(750, 620, 260, 50)
                                        if end_btn_rect.collidepoint(mx, my):
                                            self.active_panel = "TECH"
                                    elif me.get("current_civic") is None:
                                        end_btn_rect = pygame.Rect(750, 620, 260, 50)
                                        if end_btn_rect.collidepoint(mx, my):
                                            self.active_panel = "CIVIC"
                                    else:
                                        end_btn_rect = pygame.Rect(800, 620, 180, 50)
                                        if end_btn_rect.collidepoint(mx, my):
                                            self.send_net_msg({"type": "END_TURN"})
                                            self.active_panel = "MAP"
                                elif not all_producing:
                                    end_btn_rect = pygame.Rect(750, 620, 260, 50)
                                    if end_btn_rect.collidepoint(mx, my):
                                        for cid, city in self.game_state.get("cities", {}).items():
                                            if city["owner"] == self.my_id and city.get("production_item") is None:
                                                self.selected_city_id = cid
                                                self.selected_unit_id = None
                                                break
                        continue
                        
                    if self.selected_city_id and mx >= 824 and 40 <= my <= 600:
                        if event.button == 1:
                            me = self.game_state.get("players", {}).get(self.my_id, {})
                            my_techs = me.get("techs", [])
                            my_civics = me.get("civics", [])
                            city = self.game_state.get("cities", {}).get(self.selected_city_id, {})
                            options = []
                            
                            for uid, u_stats in GameData.UNITS.items():
                                if u_stats["requiredTech"] and u_stats["requiredTech"] not in my_techs: continue
                                if u_stats["UpgradeTo"]:
                                    upg_tech = GameData.UNITS[u_stats["UpgradeTo"]]["requiredTech"]
                                    if upg_tech and upg_tech in my_techs: continue
                                options.append((u_stats["name"], "unit", uid))
                                
                            for bid, b_stats in GameData.BUILDINGS.items():
                                if bid in city.get("buildings", []): continue
                                if b_stats["requiredTech"] and b_stats["requiredTech"] not in my_techs: continue
                                if b_stats["requiredCivic"] and b_stats["requiredCivic"] not in my_civics: continue
                                if b_stats["requiredBefore"] and b_stats["requiredBefore"] not in city.get("buildings", []): continue
                                options.append((b_stats["name"], "building", bid))
                            
                            for i, (label, cat, internal_name) in enumerate(options):
                                bx = 834
                                by = 90 + i * 50 + self.city_build_scroll_y
                                brect = pygame.Rect(bx, by, 180, 40)
                                if brect.collidepoint(mx, my):
                                    if cat == "building" and GameData.BUILDINGS.get(internal_name, {}).get("requiresTile", False):
                                        self.target_mode = "DISTRICT"
                                        self.target_building = internal_name
                                    else:
                                        self.send_net_msg({
                                            "type": "CHANGE_PRODUCTION",
                                            "city_id": self.selected_city_id,
                                            "category": cat,
                                            "item": internal_name
                                        })
                        continue
                        
                    # המרת קואורדינטות עכבר לאריחי מפה (כולל המצלמה)
                    map_w = len(self.game_state["map"][0]) if self.game_state.get("map") else 1
                    grid_x = ((mx + self.camera_x) // self.tile_size) % map_w
                    grid_y = (my - 40 + self.camera_y) // self.tile_size
                    if event.button == 1: # קליק שמאלי - בחירה
                        if self.target_mode and self.selected_unit_id:
                            # אנחנו במצב מטרה - שולחים פקודת התקפה במקום תנועה
                            self.send_net_msg({
                                "type": "RANGED_ATTACK",
                                "unit_id": self.selected_unit_id,
                                "tx": grid_x, "ty": grid_y
                            })
                            self.target_mode = None
                        else:
                            found_unit = False
                            for uid, unit in self.game_state["units"].items():
                                if unit["x"] == grid_x and unit["y"] == grid_y and unit["owner"] == self.my_id:
                                    self.selected_unit_id = uid
                                    self.selected_city_id = None
                                    found_unit = True
                                    print(f"Selected: {uid}")
                            if not found_unit:
                                self.selected_unit_id = None
                                found_city = False
                                for cid, city in self.game_state.get("cities", {}).items():
                                    if city["x"] == grid_x and city["y"] == grid_y and city["owner"] == self.my_id:
                                        self.selected_city_id = cid
                                        found_city = True
                                        print(f"Selected City: {cid}")
                                if not found_city:
                                    self.selected_city_id = None

                    elif event.button == 3 and self.selected_unit_id: # קליק ימני - פקודת תנועה/תקיפה
                        unit = self.game_state["units"].get(self.selected_unit_id)
                        if unit and not unit.get("has_moved", False):
                            self.send_net_msg({
                                "type": "MOVE_UNIT",
                                "unit_id": self.selected_unit_id,
                                "nx": grid_x, "ny": grid_y
                            })
                            
                elif event.type == pygame.MOUSEWHEEL and self.state == "GAME":
                    mx, my = pygame.mouse.get_pos()
                    if self.selected_city_id and mx >= 824 and 40 <= my <= 600:
                        self.city_build_scroll_y += event.y * 20
                        self.city_build_scroll_y = min(0, self.city_build_scroll_y)
                        num_items = 6
                        content_height = num_items * 50 + 20
                        max_scroll = max(0, content_height - 560)
                        self.city_build_scroll_y = max(-max_scroll, self.city_build_scroll_y)
                    elif 40 <= my < 600 and (mx < 824 if self.selected_city_id else True):
                        if self.game_state and "map" in self.game_state:
                            old_tile_size = self.tile_size
                            
                            zoom_amount = event.y * 4
                            new_tile_size = self.tile_size + zoom_amount
                            
                            map_height_tiles = len(self.game_state["map"])
                            # Min zoom: entire map height fits in 560px
                            min_tile_size = (560 + map_height_tiles - 1) // map_height_tiles
                            # Max zoom: about 8 tiles fit in 560px
                            max_tile_size = 560 // 8
                            
                            new_tile_size = max(min_tile_size, min(max_tile_size, new_tile_size))
                            
                            if new_tile_size != old_tile_size:
                                # Keep the map perfectly centered on the mouse cursor while zooming
                                grid_x_exact = (mx + self.camera_x) / old_tile_size
                                grid_y_exact = (my - 40 + self.camera_y) / old_tile_size
                                
                                self.tile_size = new_tile_size
                                
                                self.camera_x = int(grid_x_exact * self.tile_size - mx)
                                self.camera_y = int(grid_y_exact * self.tile_size - (my - 40))

            if self.state == "SPLASH":
                # אפקט פעימה צבעוני לשם המשחק
                pulse = (math.sin(time.time() * 5) + 1) / 2
                color = (255, 200 + 55 * pulse, 50)
                self.draw_text_centered("MY CIVILIZATION 2", 250, self.font_title, color)
                self.draw_text_centered("Shaked Horn", 400, self.font_main, (200, 200, 200))
                if time.time() - self.start_time > 3: self.state = "CONNECT"
            
            elif self.state in ["CONNECT", "LOGIN", "LOBBY"]:
                # רקע דמוי משחק (כחול עמוק)
                pygame.draw.rect(self.screen, (30, 60, 100), (0, 0, 1024, 768))
                
                if self.state == "CONNECT":
                    title = "SERVER CONNECTION"
                    subtitle = "Enter IP:PORT"
                elif self.state == "LOGIN":
                    title = "PLAYER LOGIN"
                    subtitle = "Enter Username"
                else:
                    title = "GAME LOBBY"
                    subtitle = "Enter Game Name (Join/Create)"
                
                self.draw_minecraft_box(312, 284, 400, 200, title)
                input_surf = self.font_main.render(self.input_text + "|", True, (255, 255, 255))
                self.screen.blit(input_surf, (332, 360))
                self.draw_text_centered(subtitle, 330, self.font_small, (150, 150, 150), shadow=False)
                
                if self.state == "LOBBY":
                    # Show active games
                    y_offset = 500
                    self.draw_text_centered("Active Games:", y_offset, self.font_small, (255, 255, 0))
                    for g in self.games_list:
                        y_offset += 30
                        self.draw_text_centered(g, y_offset, self.font_small, (200, 200, 200))

            elif self.state == "GAME" and self.game_state:
                if not self.game_state.get("game_started", False):
                    pygame.draw.rect(self.screen, (30, 60, 100), (0, 0, 1024, 768))
                    self.draw_minecraft_box(312, 284, 400, 200, "WAITING FOR PLAYERS")
                    self.draw_text_centered(f"Connected: {len(self.game_state.get('players', {}))} / 2+", 360, self.font_small, (200, 200, 200), shadow=False)
                    self.draw_text_centered("The game will start automatically.", 400, self.font_small, (150, 150, 150), shadow=False)
                    pygame.display.flip()
                    self.clock.tick(30)
                    continue
                
                if self.active_panel == "MAP":
                    # ציור המפה והיחידות (כפי שעשינו קודם)
                    for y, row in enumerate(self.game_state["map"]):
                        map_w = len(row)
                        map_pixel_w = map_w * self.tile_size
                        for x, tile in enumerate(row):
                            screen_x = (x * self.tile_size - self.camera_x) % map_pixel_w
                            if screen_x > map_pixel_w - self.tile_size: screen_x -= map_pixel_w
                        
                            screen_y = y * self.tile_size - self.camera_y + 40
                            if -self.tile_size < screen_x < 1024 and -self.tile_size < screen_y < 600:
                                color = TERRAIN_COLORS.get(tile["terrain"], (255, 0, 255))
                                pygame.draw.rect(self.screen, color, (screen_x, screen_y, self.tile_size, self.tile_size))
                            
                                imp = tile.get("improvement")
                                if imp:
                                    imp_color = (50, 200, 50) if imp == "farm" else (100, 100, 100) if imp in ["mine", "quarry"] else (200, 200, 50) if imp == "pasture" else (0, 150, 200) if imp == "fishingBoats" else (200, 100, 50)
                                    pygame.draw.rect(self.screen, imp_color, (screen_x + 8, screen_y + 8, 16, 16))
                                    pygame.draw.rect(self.screen, (0, 0, 0), (screen_x + 8, screen_y + 8, 16, 16), 1)
                                
                                owner = tile.get("owner", -1)
                                if owner != -1:
                                    p_color = self.game_state.get("players", {}).get(owner, {}).get("color", (255, 255, 255))
                                    border_thick = max(2, self.tile_size // 12)
                                
                                    # Check Top
                                    if y == 0 or self.game_state["map"][y-1][x].get("owner", -1) != owner:
                                        pygame.draw.rect(self.screen, p_color, (screen_x, screen_y, self.tile_size, border_thick))
                                    # Check Bottom
                                    if y == len(self.game_state["map"]) - 1 or self.game_state["map"][y+1][x].get("owner", -1) != owner:
                                        pygame.draw.rect(self.screen, p_color, (screen_x, screen_y + self.tile_size - border_thick, self.tile_size, border_thick))
                                    # Check Left (wrap)
                                    lx = (x - 1) % map_w
                                    if self.game_state["map"][y][lx].get("owner", -1) != owner:
                                        pygame.draw.rect(self.screen, p_color, (screen_x, screen_y, border_thick, self.tile_size))
                                    # Check Right (wrap)
                                    rx = (x + 1) % map_w
                                    if self.game_state["map"][y][rx].get("owner", -1) != owner:
                                        pygame.draw.rect(self.screen, p_color, (screen_x + self.tile_size - border_thick, screen_y, border_thick, self.tile_size))
                                
                                pygame.draw.rect(self.screen, (40, 40, 40), (screen_x, screen_y, self.tile_size, self.tile_size), 1)
                
                    # ציור ערים
                    map_w = len(self.game_state["map"][0]) if self.game_state.get("map") else 1
                    map_pixel_w = map_w * self.tile_size
                    for cid, city in self.game_state.get("cities", {}).items():
                        screen_x = (city["x"] * self.tile_size - self.camera_x) % map_pixel_w
                        if screen_x > map_pixel_w - self.tile_size: screen_x -= map_pixel_w
                    
                        screen_y = city["y"] * self.tile_size - self.camera_y + 40
                        if -self.tile_size < screen_x < 1024 and -self.tile_size < screen_y < 600:
                            owner_color = self.game_state.get("players", {}).get(city.get("owner", ""), {}).get("color", (150, 150, 150))
                            color = owner_color
                            pygame.draw.rect(self.screen, color, (screen_x, screen_y, self.tile_size, self.tile_size))
                            pygame.draw.rect(self.screen, (0, 0, 0), (screen_x, screen_y, self.tile_size, self.tile_size), 2)
                        
                            b_colors = {
                                "monument": (100, 100, 255),
                                "granary": (255, 200, 0),
                                "library": (0, 255, 255),
                                "waterMill": (50, 50, 200)
                            }
                            buildings = city.get("buildings", [])
                            b_idx = 0
                            for b in buildings:
                                if b == "cityCenter": continue
                                bc = b_colors.get(b, (200, 200, 200))
                                bx = screen_x + 2 + (b_idx * 8) % (self.tile_size - 8)
                                by = screen_y + self.tile_size - 8
                                pygame.draw.rect(self.screen, bc, (bx, by, 6, 6))
                                pygame.draw.rect(self.screen, (0, 0, 0), (bx, by, 6, 6), 1)
                                b_idx += 1
                            
                            if self.selected_city_id == cid:
                                pygame.draw.rect(self.screen, (255, 255, 255), (screen_x, screen_y, self.tile_size, self.tile_size), 3)
                                
                            hp = city.get("hp", 200)
                            max_hp = 200
                            if hp < max_hp:
                                hp_ratio = max(0, hp / max_hp)
                                pygame.draw.rect(self.screen, (200, 0, 0), (screen_x, screen_y - 6, self.tile_size, 4))
                                pygame.draw.rect(self.screen, (0, 200, 0), (screen_x, screen_y - 6, int(self.tile_size * hp_ratio), 4))


                    for uid, u in self.game_state["units"].items():
                        base_color = self.game_state.get("players", {}).get(u.get("owner", ""), {}).get("color", (255, 255, 255))
                        color = base_color
                        if u["owner"] == self.my_id and u.get("has_moved", False):
                            color = (max(0, base_color[0] - 100), max(0, base_color[1] - 100), max(0, base_color[2] - 100)) # Darker if moved
                        
                        ux_screen = (u["x"] * self.tile_size - self.camera_x) % map_pixel_w
                        if ux_screen > map_pixel_w - self.tile_size: ux_screen -= map_pixel_w
                    
                        pos = (ux_screen + self.tile_size // 2, u["y"] * self.tile_size - self.camera_y + self.tile_size // 2 + 40)
                        if -32 < pos[0] < 1056 and -32 < pos[1] < 600:
                            pygame.draw.circle(self.screen, color, pos, 15)
                        
                            u_type = u.get("type", "?")
                            char_surf = self.font_small.render(u_type[0].upper(), True, (0, 0, 0))
                            char_rect = char_surf.get_rect(center=pos)
                            self.screen.blit(char_surf, char_rect)
                        
                            # סימון יחידה נבחרת בריבוע לבן
                            if self.selected_unit_id == uid:
                                pygame.draw.rect(self.screen, (255, 255, 255), (ux_screen, u["y"]*self.tile_size - self.camera_y + 40, self.tile_size, self.tile_size), 2)
                                
                            hp = u.get("hp", 100)
                            max_hp = 100
                            if hp < max_hp:
                                hp_ratio = max(0, hp / max_hp)
                                pygame.draw.rect(self.screen, (200, 0, 0), (ux_screen, u["y"]*self.tile_size - self.camera_y + 40 - 6, self.tile_size, 4))
                                pygame.draw.rect(self.screen, (0, 200, 0), (ux_screen, u["y"]*self.tile_size - self.camera_y + 40 - 6, int(self.tile_size * hp_ratio), 4))
                            

                elif self.active_panel in ["TECH", "CIVIC"]:
                    self.screen.set_clip(pygame.Rect(0, 40, 1024 if not self.selected_city_id else 824, 560))
                    pygame.draw.rect(self.screen, (20, 20, 30), (0, 40, 1024, 560))
                    title = "Science Tree" if self.active_panel == "TECH" else "Civic Tree"
                    self.draw_text_centered(title, 60, self.font_main, (255, 255, 255))
                    
                    me = self.game_state.get("players", {}).get(self.my_id, {})
                    my_techs = me.get("techs", [])
                    my_civics = me.get("civics", [])
                    current_res = me.get("current_research") if self.active_panel == "TECH" else me.get("current_civic")
                    res_prog = me.get("research_progress", 0) if self.active_panel == "TECH" else me.get("civic_progress", 0)
                    
                    is_tech = self.active_panel == "TECH"
                    source_dict = GameData.TECHS if is_tech else GameData.CIVICS
                    
                    layout = self.get_tree_layout(source_dict, is_tech)
                    card_width, card_height = 240, 140
                    
                    # Draw connecting lines first
                    for key, (cx, cy) in layout.items():
                        reqs = source_dict[key].get("required_techs", []) if is_tech else source_dict[key].get("required_civics", [])
                        for req in reqs:
                            if req in layout:
                                rx, ry = layout[req]
                                start_pos = (rx + card_width + self.tree_scroll_x, ry + card_height // 2 + self.tree_scroll_y)
                                end_pos = (cx + self.tree_scroll_x, cy + card_height // 2 + self.tree_scroll_y)
                                pygame.draw.line(self.screen, (100, 100, 100), start_pos, end_pos, 3)
                    
                    # Draw cards
                    for key, (cx, cy) in layout.items():
                        data = source_dict[key]
                        draw_x = cx + self.tree_scroll_x
                        draw_y = cy + self.tree_scroll_y
                        rect = pygame.Rect(draw_x, draw_y, card_width, card_height)
                        
                        # Only draw if on screen
                        if draw_x > 1024 or draw_x + card_width < 0 or draw_y > 600 or draw_y + card_height < 40:
                            continue
                            
                        is_unlocked = key in my_techs or key in my_civics
                        is_researching = current_res == key
                        reqs = data.get("required_techs", []) if is_tech else data.get("required_civics", [])
                        can_research = all(r in (my_techs if is_tech else my_civics) for r in reqs) and not is_unlocked
                        
                        bg_color = (40, 40, 50)
                        border_color = (100, 100, 100)
                        if is_unlocked:
                            bg_color = (50, 100, 50)
                            border_color = (100, 255, 100)
                        elif is_researching:
                            bg_color = (50, 50, 150) if is_tech else (120, 50, 150)
                            border_color = (100, 100, 255) if is_tech else (220, 100, 255)
                        elif can_research:
                            bg_color = (80, 80, 80)
                            border_color = (200, 200, 200)
                            
                        pygame.draw.rect(self.screen, bg_color, rect)
                        pygame.draw.rect(self.screen, border_color, rect, 2)
                        
                        self.screen.blit(self.font_small.render(data["name"], True, (255, 255, 255)), (draw_x + 10, draw_y + 10))
                        cost = data.get("science_cost", 0) if is_tech else data.get("culture_cost", 0)
                        
                        if is_researching:
                            self.screen.blit(self.font_small.render(f"Progress: {int(res_prog)}/{cost}", True, (200, 200, 255)), (draw_x + 10, draw_y + 40))
                        elif not is_unlocked:
                            self.screen.blit(self.font_small.render(f"Cost: {cost}", True, (200, 200, 200)), (draw_x + 10, draw_y + 40))
                        else:
                            self.screen.blit(self.font_small.render("Unlocked", True, (150, 255, 150)), (draw_x + 10, draw_y + 40))
                            
                        # Draw Turns left and Unlocks
                        if not is_unlocked and can_research:
                            income = me.get("last_science_income", 1) if is_tech else me.get("last_culture_income", 1)
                            progress_val = res_prog if is_researching else 0
                            turns_left = math.ceil((cost - progress_val) / max(1, income))
                            self.screen.blit(self.font_small.render(f"Turns: {turns_left}", True, (200, 200, 255)), (draw_x + 120, draw_y + 40))
                            
                        unlock_text_y = draw_y + 65
                        for unit in data.get("unlocked_units", []):
                            self.screen.blit(self.font_small.render(f"+ Unit: {unit.capitalize()}", True, (200, 255, 200)), (draw_x + 10, unlock_text_y))
                            unlock_text_y += 22
                        for bldg in data.get("unlocked_buildings", []):
                            self.screen.blit(self.font_small.render(f"+ Bldg: {bldg.capitalize()}", True, (200, 200, 255)), (draw_x + 10, unlock_text_y))
                            unlock_text_y += 22
                            
                        if not is_tech:
                            for policy in data.get("unlocked_policy_cards", []):
                                self.screen.blit(self.font_small.render(f"+ Policy: {policy.capitalize()}", True, (255, 200, 200)), (draw_x + 10, unlock_text_y))
                                unlock_text_y += 22
                            gov = data.get("unlocked_government")
                            if gov:
                                self.screen.blit(self.font_small.render(f"+ Gov: {gov.capitalize()}", True, (255, 255, 100)), (draw_x + 10, unlock_text_y))
                                unlock_text_y += 22

                    self.screen.set_clip(None)  # Reset clipping area


                # ציור Top UI
                me = self.game_state.get("players", {}).get(self.my_id, {})
                my_color = me.get("color", (40, 40, 60))
                # Make the top bar background a darker version of the player's color
                bg_color = (max(0, my_color[0] // 2 - 20), max(0, my_color[1] // 2 - 20), max(0, my_color[2] // 2 - 20))
                
                top_rect = pygame.Rect(0, 0, 1024, 40)
                pygame.draw.rect(self.screen, bg_color, top_rect)
                turn = self.game_state.get("turn", 1)
                
                top_text = f"Turn: {turn}  |  Gold: {int(me.get('gold',0))}  |  Science: +{me.get('last_science_income',0)}  |  Culture: +{me.get('last_culture_income',0)}"
                top_surf = self.font_small.render(top_text, True, (255, 255, 255))
                self.screen.blit(top_surf, (10, 10))
                
                # Top Bar Buttons
                pygame.draw.rect(self.screen, (100, 100, 100) if self.active_panel == "MAP" else (50, 50, 50), (600, 5, 100, 30))
                self.screen.blit(self.font_small.render("MAP", True, (255, 255, 255)), (630, 10))
                
                pygame.draw.rect(self.screen, (100, 100, 200) if self.active_panel == "TECH" else (50, 50, 100), (720, 5, 140, 30))
                self.screen.blit(self.font_small.render("TECH TREE", True, (255, 255, 255)), (740, 10))
                
                pygame.draw.rect(self.screen, (200, 100, 200) if self.active_panel == "CIVIC" else (100, 50, 100), (880, 5, 140, 30))
                self.screen.blit(self.font_small.render("CIVIC TREE", True, (255, 255, 255)), (900, 10))

                # ציור ה-UI התחתון
                ui_rect = pygame.Rect(0, 600, 1024, 168)
                pygame.draw.rect(self.screen, (40, 40, 50), ui_rect)
                pygame.draw.rect(self.screen, (100, 100, 120), ui_rect, 4)

                if self.selected_unit_id:
                    unit = self.game_state["units"].get(self.selected_unit_id)
                    if unit:
                        unit_info = GameData.UNITS.get(unit["type"], {})
                        name = unit_info.get("name", "Unknown Unit")
                        hp = unit.get("hp", 100)
                        self.screen.blit(self.font_main.render(name, True, (255, 255, 255)), (20, 620))
                        self.screen.blit(self.font_small.render(f"HP: {hp}/100", True, (200, 200, 200)), (20, 660))
                        
                        if not unit.get("has_moved", False):
                            self.screen.blit(self.font_small.render("Press SPACE to Skip Turn", True, (200, 200, 200)), (20, 690))
                            
                            if unit_info.get("name") == "Settler":
                                btn_rect = pygame.Rect(250, 620, 150, 40)
                                pygame.draw.rect(self.screen, (200, 200, 200), btn_rect)
                                self.screen.blit(self.font_small.render("Found City (B)", True, (0, 0, 0)), (260, 630))
                                if pygame.key.get_pressed()[pygame.K_b]:
                                    self.send_net_msg({"type": "FOUND_CITY", "unit_id": self.selected_unit_id})
                            elif unit_info.get("range", 0) > 0:
                                btn_rect = pygame.Rect(250, 620, 150, 40)
                                pygame.draw.rect(self.screen, (200, 50, 50) if self.target_mode else (100, 100, 100), btn_rect)
                                self.screen.blit(self.font_small.render("Target (R)", True, (255,255,255)), (260, 630))
                                if pygame.key.get_pressed()[pygame.K_r]:
                                    self.target_mode = "ATTACK"
                            elif unit_info.get("name") == "Builder":
                                ux, uy = unit["x"], unit["y"]
                                tile = self.game_state["map"][uy][ux]
                                t_type = tile["terrain"]
                                has_imp = tile.get("improvement") is not None
                                charges = unit.get("charges", 0)
                                
                                self.screen.blit(self.font_small.render(f"Charges: {charges}", True, (200, 200, 200)), (150, 660))
                                
                                if not has_imp and charges > 0:
                                    possible = []
                                    if t_type in ["grassland", "plains"]: possible.append(("Farm", "farm"))
                                    elif t_type in ["hills"]: possible.append(("Mine", "mine"))
                                    elif t_type in ["coast"]: possible.append(("Fishing Boats", "fishingBoats"))
                                    
                                    for idx, (label, imp_id) in enumerate(possible):
                                        bx = 250 + idx * 150
                                        btn_rect = pygame.Rect(bx, 620, 140, 40)
                                        pygame.draw.rect(self.screen, (200, 200, 200), btn_rect)
                                        self.screen.blit(self.font_small.render(f"Build {label}", True, (0, 0, 0)), (bx+5, 630))

                elif self.selected_city_id:
                    city = self.game_state.get("cities", {}).get(self.selected_city_id)
                    if city:
                        name = city.get("name", "City")
                        hp = city.get("hp", 200)
                        pop = city.get("population", 1)
                        food = city.get("stored_food", 0)
                        food_needed = 15 + (pop * 5)
                        prod = city.get("stored_production", 0)
                        
                        self.screen.blit(self.font_main.render(f"{name} (Pop {pop})", True, (255, 255, 255)), (20, 610))
                        self.screen.blit(self.font_small.render(f"HP: {hp}/200  |  Food: {food}/{food_needed}  |  Prod: {prod}", True, (200, 200, 200)), (20, 640))
                        
                        prod_item = city.get("production_item")
                        if prod_item:
                            item_name = prod_item["name"].capitalize()
                            cost = 999
                            if prod_item["category"] == "unit":
                                cost = GameData.UNITS.get(prod_item["name"], {}).get("production_cost", 999)
                            elif prod_item["category"] == "building":
                                cost = GameData.BUILDINGS.get(prod_item["name"], {}).get("production_cost", 999)
                            city_prod_yield = max(1, city.get("last_production_yield", 1))
                            turns_left = max(1, math.ceil((cost - prod) / city_prod_yield))
                            self.screen.blit(self.font_small.render(f"Building: {item_name} ({turns_left} Turns)", True, (150, 255, 150)), (20, 670))
                        else:
                            self.screen.blit(self.font_small.render(f"Building: Nothing", True, (255, 150, 150)), (20, 670))
                            
                        # Build Menu buttons on the right side
                        right_rect = pygame.Rect(824, 40, 200, 560)
                        pygame.draw.rect(self.screen, (40, 40, 50), right_rect)
                        pygame.draw.rect(self.screen, (100, 100, 120), right_rect, 2)
                        
                        my_techs = me.get("techs", [])
                        my_civics = me.get("civics", [])
                        options = []
                        for uid, u_stats in GameData.UNITS.items():
                            if u_stats["requiredTech"] and u_stats["requiredTech"] not in my_techs: continue
                            if u_stats["UpgradeTo"]:
                                upg_tech = GameData.UNITS[u_stats["UpgradeTo"]]["requiredTech"]
                                if upg_tech and upg_tech in my_techs: continue
                            options.append((u_stats["name"], "unit", uid))
                            
                        for bid, b_stats in GameData.BUILDINGS.items():
                            if bid in city.get("buildings", []): continue
                            if b_stats["requiredTech"] and b_stats["requiredTech"] not in my_techs: continue
                            if b_stats["requiredCivic"] and b_stats["requiredCivic"] not in my_civics: continue
                            if b_stats["requiredBefore"] and b_stats["requiredBefore"] not in city.get("buildings", []): continue
                            options.append((b_stats["name"], "building", bid))
                        
                        old_clip = self.screen.get_clip()
                        self.screen.set_clip(right_rect)
                        
                        self.screen.blit(self.font_main.render("Production", True, (255, 255, 255)), (834, 45 + self.city_build_scroll_y))
                        
                        for i, (label, cat, internal_name) in enumerate(options):
                            bx = 834
                            by = 90 + i * 50 + self.city_build_scroll_y
                            brect = pygame.Rect(bx, by, 180, 40)
                            
                            item_cost = 999
                            if cat == "unit":
                                item_cost = GameData.UNITS.get(internal_name, {}).get("production_cost", 999)
                            elif cat == "building":
                                item_cost = GameData.BUILDINGS.get(internal_name, {}).get("production_cost", 999)
                            city_prod_yield = max(1, city.get("last_production_yield", 1))
                            t_left = max(1, math.ceil(item_cost / city_prod_yield))
                            
                            color = (50, 150, 50) if prod_item and prod_item["name"] == internal_name else (80, 80, 80)
                            pygame.draw.rect(self.screen, color, brect)
                            pygame.draw.rect(self.screen, (200, 200, 200), brect, 1)
                            self.screen.blit(self.font_small.render(f"{label} ({t_left}T)", True, (255, 255, 255)), (bx + 10, by + 10))
                            
                        self.screen.set_clip(old_clip)
                        
                # Draw End Turn button if ready
                if not me.get("ended_turn", False):
                    my_units = [u for u in self.game_state["units"].values() if u["owner"] == self.my_id]
                    units_needing_orders = sum(1 for u in my_units if not u.get("has_moved", False))
                    
                    my_cities = [c for c in self.game_state.get("cities", {}).values() if c["owner"] == self.my_id]
                    cities_needing_orders = sum(1 for c in my_cities if c.get("production_item") is None)
                    
                    if cities_needing_orders > 0:
                        end_btn_rect = pygame.Rect(750, 620, 260, 50)
                        pygame.draw.rect(self.screen, (200, 150, 50), end_btn_rect)
                        pygame.draw.rect(self.screen, (255, 200, 100), end_btn_rect, 2)
                        self.screen.blit(self.font_small.render("CHOOSE PRODUCTION", True, (0, 0, 0)), (780, 635))
                    elif units_needing_orders > 0:
                        end_btn_rect = pygame.Rect(750, 620, 260, 50)
                        pygame.draw.rect(self.screen, (80, 80, 80), end_btn_rect)
                        pygame.draw.rect(self.screen, (150, 150, 150), end_btn_rect, 2)
                        self.screen.blit(self.font_small.render(f"Unit needs orders ({units_needing_orders})", True, (200, 200, 200)), (770, 635))
                    elif me.get("current_research") is None:
                        end_btn_rect = pygame.Rect(750, 620, 260, 50)
                        pygame.draw.rect(self.screen, (50, 150, 200), end_btn_rect)
                        pygame.draw.rect(self.screen, (100, 200, 255), end_btn_rect, 2)
                        self.screen.blit(self.font_small.render("CHOOSE RESEARCH", True, (0, 0, 0)), (790, 635))
                    elif me.get("current_civic") is None:
                        end_btn_rect = pygame.Rect(750, 620, 260, 50)
                        pygame.draw.rect(self.screen, (200, 100, 200), end_btn_rect)
                        pygame.draw.rect(self.screen, (255, 150, 255), end_btn_rect, 2)
                        self.screen.blit(self.font_small.render("CHOOSE CIVIC", True, (0, 0, 0)), (810, 635))
                    else:
                        end_btn_rect = pygame.Rect(800, 620, 180, 50)
                        pygame.draw.rect(self.screen, (50, 200, 50), end_btn_rect)
                        self.screen.blit(self.font_main.render("END TURN ->", True, (0, 0, 0)), (810, 625))
                else:
                    self.draw_text_centered("Waiting for everyone to end their turn...", 650, self.font_main, (200, 200, 200), shadow=True)

            if self.state == "GAME" and self.game_state and "map" in self.game_state:
                keys = pygame.key.get_pressed()
                scroll_speed = 20
                if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                    self.camera_x -= scroll_speed
                if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                    self.camera_x += scroll_speed
                if keys[pygame.K_UP] or keys[pygame.K_w]:
                    self.camera_y -= scroll_speed
                if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                    self.camera_y += scroll_speed
                    
                map_pixel_w = len(self.game_state["map"][0]) * self.tile_size
                map_height = len(self.game_state["map"]) * self.tile_size
                max_y = max(0, map_height - 560)
                
                self.camera_x %= map_pixel_w
                self.camera_y = max(0, min(self.camera_y, max_y))

            if self.state == "GAME" and self.game_state:
                me = self.game_state.get("players", {}).get(self.my_id, {})
                if me.get("eliminated"):
                    s = pygame.Surface((1024, 768), pygame.SRCALPHA)
                    s.fill((100, 0, 0, 200))
                    self.screen.blit(s, (0, 0))
                    self.draw_text_centered("DEFEAT", 300, self.font_title, (255, 50, 50))
                    self.draw_text_centered("Your civilization has been destroyed.", 400, self.font_main, (200, 200, 200))
                elif me.get("winner"):
                    s = pygame.Surface((1024, 768), pygame.SRCALPHA)
                    s.fill((0, 100, 0, 200))
                    self.screen.blit(s, (0, 0))
                    self.draw_text_centered("VICTORY", 300, self.font_title, (50, 255, 50))
                    self.draw_text_centered(f"You achieved a {me.get('winner')} Victory!", 400, self.font_main, (200, 200, 200))

            pygame.display.flip()
            self.clock.tick(30)
        pygame.quit()

if __name__ == "__main__":
    CivClient().run()