import pygame
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
        self.target_mode = False
        self.start_time = time.time()
        self.games_list = []
        self.city_build_scroll_y = 0
        self.server_ip = ""

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
                                    self.sock.sendall(json.dumps({"type": "LOGIN", "user": self.username}).encode())
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
                    elif event.key == pygame.K_SPACE and self.state == "GAME":
                        if self.selected_unit_id:
                            self.send_net_msg({"type": "SKIP_UNIT_TURN", "unit_id": self.selected_unit_id})
                    else: self.input_text += event.unicode
                elif event.type == pygame.MOUSEMOTION and self.state == "GAME":
                    if event.buttons[0] or event.buttons[1] or event.buttons[2]: # Any mouse button held
                        self.camera_x -= event.rel[0]
                        self.camera_y -= event.rel[1]
                        
                        # Clamp camera to map bounds
                        if self.game_state and "map" in self.game_state:
                            map_width = len(self.game_state["map"][0]) * self.tile_size
                            map_height = len(self.game_state["map"]) * self.tile_size
                            max_x = max(0, map_width - 1024)
                            max_y = max(0, map_height - 560) # Game area is 560px tall (600 bottom - 40 top)
                            
                            self.camera_x = max(0, min(self.camera_x, max_x))
                            self.camera_y = max(0, min(self.camera_y, max_y))
                            
                elif event.type == pygame.MOUSEBUTTONDOWN and self.state == "GAME":
                    mx, my = pygame.mouse.get_pos()
                    
                    if my < 40:
                        continue # Ignore clicks on the top UI
                    
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
                                            self.target_mode = not self.target_mode
                                    elif unit_info.get("name") == "Builder":
                                        ux, uy = unit["x"], unit["y"]
                                        tile = self.game_state["map"][uy][ux]
                                        t_type = tile["terrain"]
                                        has_imp = tile.get("improvement") is not None
                                        charges = unit.get("charges", 0)
                                        
                                        if not has_imp and charges > 0:
                                            possible = []
                                            if t_type in ["grassland", "plains"]: possible.append(("Farm", "farm"))
                                            elif t_type in ["hills"]: possible.append(("Mine", "mine"))
                                            elif t_type in ["coast"]: possible.append(("Fishing Boats", "fishingBoats"))
                                            
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
                                    end_btn_rect = pygame.Rect(800, 620, 180, 50)
                                    if end_btn_rect.collidepoint(mx, my):
                                        self.send_net_msg({"type": "END_TURN"})
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
                            base_options = [
                                ("Warrior", "unit", "warrior"),
                                ("Slinger", "unit", "slinger"),
                                ("Settler", "unit", "settler"),
                                ("Builder", "unit", "builder"),
                                ("Monument", "building", "monument"),
                                ("Granary", "building", "granary")
                            ]
                            city = self.game_state.get("cities", {}).get(self.selected_city_id, {})
                            options = [o for o in base_options if o[1] != "building" or o[2] not in city.get("buildings", [])]
                            
                            for i, (label, cat, internal_name) in enumerate(options):
                                bx = 834
                                by = 90 + i * 50 + self.city_build_scroll_y
                                brect = pygame.Rect(bx, by, 180, 40)
                                if brect.collidepoint(mx, my):
                                    self.send_net_msg({
                                        "type": "CHANGE_PRODUCTION",
                                        "city_id": self.selected_city_id,
                                        "category": cat,
                                        "item": internal_name
                                    })
                        continue
                        
                    # המרת קואורדינטות עכבר לאריחי מפה (כולל המצלמה)
                    grid_x = (mx + self.camera_x) // self.tile_size
                    grid_y = (my - 40 + self.camera_y) // self.tile_size
                    if event.button == 1: # קליק שמאלי - בחירה
                        if self.target_mode and self.selected_unit_id:
                            # אנחנו במצב מטרה - שולחים פקודת התקפה במקום תנועה
                            self.send_net_msg({
                                "type": "RANGED_ATTACK",
                                "unit_id": self.selected_unit_id,
                                "tx": grid_x, "ty": grid_y
                            })
                            self.target_mode = False
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
                    if self.selected_city_id:
                        mx, my = pygame.mouse.get_pos()
                        if mx >= 824 and 40 <= my <= 600:
                            self.city_build_scroll_y += event.y * 20
                            self.city_build_scroll_y = min(0, self.city_build_scroll_y)
                            # Maximum scroll: 6 items * 50px = 300px + 20px padding = 320px height
                            # Container height is 560px. So we don't actually need to limit scrolling
                            # negatively unless there are many items. Let's make it robust:
                            num_items = 6
                            content_height = num_items * 50 + 20
                            max_scroll = max(0, content_height - 560)
                            self.city_build_scroll_y = max(-max_scroll, self.city_build_scroll_y)

            if self.state == "SPLASH":
                # אפקט פעימה צבעוני לשם המשחק
                pulse = (math.sin(time.time() * 5) + 1) / 2
                color = (255, 200 + 55 * pulse, 50)
                self.draw_text_centered("MY CIVILIZATION 2", 250, self.font_title, color)
                self.draw_text_centered("Shaked Horn & Benjamin Zimerman", 400, self.font_main, (200, 200, 200))
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
                # ציור המפה והיחידות (כפי שעשינו קודם)
                for y, row in enumerate(self.game_state["map"]):
                    for x, tile in enumerate(row):
                        screen_x = x * self.tile_size - self.camera_x
                        screen_y = y * self.tile_size - self.camera_y + 40
                        if -self.tile_size < screen_x < 1024 and -self.tile_size < screen_y < 600:
                            color = TERRAIN_COLORS.get(tile["terrain"], (255, 0, 255))
                            pygame.draw.rect(self.screen, color, (screen_x, screen_y, self.tile_size, self.tile_size))
                            
                            imp = tile.get("improvement")
                            if imp:
                                imp_color = (50, 200, 50) if imp == "farm" else (100, 100, 100) if imp in ["mine", "quarry"] else (200, 200, 50) if imp == "pasture" else (0, 150, 200) if imp == "fishingBoats" else (200, 100, 50)
                                pygame.draw.rect(self.screen, imp_color, (screen_x + 8, screen_y + 8, 16, 16))
                                pygame.draw.rect(self.screen, (0, 0, 0), (screen_x + 8, screen_y + 8, 16, 16), 1)
                                
                            pygame.draw.rect(self.screen, (0, 0, 0, 30), (screen_x, screen_y, self.tile_size, self.tile_size), 1)
                
                # ציור ערים
                for cid, city in self.game_state.get("cities", {}).items():
                    screen_x = city["x"] * self.tile_size - self.camera_x
                    screen_y = city["y"] * self.tile_size - self.camera_y + 40
                    if -self.tile_size < screen_x < 1024 and -self.tile_size < screen_y < 600:
                        color = (150, 150, 150)
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

                for uid, u in self.game_state["units"].items():
                    color = (255, 255, 0) if u["owner"] == self.my_id else (255, 50, 50)
                    if u["owner"] == self.my_id and u.get("has_moved", False):
                        color = (150, 150, 0) # Darker yellow if moved
                    pos = (u["x"] * self.tile_size - self.camera_x + self.tile_size // 2, u["y"] * self.tile_size - self.camera_y + self.tile_size // 2 + 40)
                    if -32 < pos[0] < 1056 and -32 < pos[1] < 600:
                        pygame.draw.circle(self.screen, color, pos, 15)
                        
                        u_type = u.get("type", "?")
                        char_surf = self.font_small.render(u_type[0].upper(), True, (0, 0, 0))
                        char_rect = char_surf.get_rect(center=pos)
                        self.screen.blit(char_surf, char_rect)
                        
                        # סימון יחידה נבחרת בריבוע לבן
                        if self.selected_unit_id == uid:
                            pygame.draw.rect(self.screen, (255, 255, 255), (u["x"]*self.tile_size - self.camera_x, u["y"]*self.tile_size - self.camera_y + 40, self.tile_size, self.tile_size), 2)
                            
                # ציור Top UI
                top_rect = pygame.Rect(0, 0, 1024, 40)
                pygame.draw.rect(self.screen, (20, 20, 30), top_rect)
                me = self.game_state.get("players", {}).get(self.my_id, {})
                turn = self.game_state.get("turn", 1)
                
                top_text = f"Turn: {turn}   |   Gold: {me.get('gold',0)} (+{me.get('last_gold_income',0)})   |   Science: {me.get('science',0)} (+{me.get('last_science_income',0)})   |   Culture: {me.get('culture',0)} (+{me.get('last_culture_income',0)})"
                top_surf = self.font_main.render(top_text, True, (255, 255, 255))
                self.screen.blit(top_surf, (20, 5))

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
                                    self.target_mode = True
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
                        
                        base_options = [
                            ("Warrior", "unit", "warrior"),
                            ("Slinger", "unit", "slinger"),
                            ("Settler", "unit", "settler"),
                            ("Builder", "unit", "builder"),
                            ("Monument", "building", "monument"),
                            ("Granary", "building", "granary")
                        ]
                        options = [o for o in base_options if o[1] != "building" or o[2] not in city.get("buildings", [])]
                        
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
                    else:
                        end_btn_rect = pygame.Rect(800, 620, 180, 50)
                        pygame.draw.rect(self.screen, (50, 200, 50), end_btn_rect)
                        self.screen.blit(self.font_main.render("END TURN ->", True, (0, 0, 0)), (810, 625))
                else:
                    self.draw_text_centered("Waiting for everyone to end their turn...", 650, self.font_main, (200, 200, 200), shadow=True)

            pygame.display.flip()
        pygame.quit()

if __name__ == "__main__":
    CivClient().run()