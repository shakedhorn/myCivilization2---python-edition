import pygame
import socket
import json
import threading
import time
import math
from CivShared.game_defs import GameData

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
        self.camera_x = 0
        self.camera_y = 0
        self.tile_size = 32
        self.target_mode = False
        self.start_time = time.time()

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
                                self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                                self.sock.connect((ip, int(port)))
                                self.state = "LOGIN"
                                self.input_text = ""
                            except: self.input_text = "ERROR: IP:PORT"
                        elif self.state == "LOGIN":
                            self.username = self.input_text
                            self.sock.sendall(json.dumps({"type": "LOGIN", "user": self.username}).encode())
                            resp = json.loads(self.sock.recv(1024).decode())
                            if resp["status"] == "LOGIN_OK":
                                self.my_id = str(resp["id"])
                                self.state = "GAME"
                                threading.Thread(target=self.network_loop, daemon=True).start()
                    elif event.key == pygame.K_BACKSPACE: self.input_text = self.input_text[:-1]
                    else: self.input_text += event.unicode
                elif event.type == pygame.MOUSEBUTTONDOWN and self.state == "GAME":
                    mx, my = pygame.mouse.get_pos()
                    if self.selected_unit_id:
                        button_rect = pygame.Rect(10, 600, 180, 50)
                        if button_rect.collidepoint(mx, my):
                            self.send_net_msg({"type": "FOUND_CITY", "unit_id": self.selected_unit_id})
                            continue
                    # המרת קואורדינטות עכבר לאריחי מפה (כולל המצלמה)
                    grid_x = (mx + self.camera_x) // self.tile_size
                    grid_y = (my + self.camera_y) // self.tile_size
                    if event.button == 1: # קליק שמאלי - בחירת יחידה
                        if self.target_mode:
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
                                    found_unit = True
                                    print(f"Selected: {uid}")
                            if not found_unit:
                                self.selected_unit_id = None

                    elif event.button == 3 and self.selected_unit_id: # קליק ימני - פקודת תנועה/תקיפה
                        self.send_net_msg({
                            "type": "MOVE_UNIT",
                            "unit_id": self.selected_unit_id,
                            "nx": grid_x, "ny": grid_y
                        })

            if self.state == "SPLASH":
                # אפקט פעימה צבעוני לשם המשחק
                pulse = (math.sin(time.time() * 5) + 1) / 2
                color = (255, 200 + 55 * pulse, 50)
                self.draw_text_centered("MY CIVILIZATION 2", 250, self.font_title, color)
                self.draw_text_centered("Shaked Horn & Benjamin Zimerman", 400, self.font_main, (200, 200, 200))
                if time.time() - self.start_time > 3: self.state = "CONNECT"
            
            elif self.state == "CONNECT" or self.state == "LOGIN":
                # רקע דמוי משחק (כחול עמוק)
                pygame.draw.rect(self.screen, (30, 60, 100), (0, 0, 1024, 768))
                title = "SERVER CONNECTION" if self.state == "CONNECT" else "PLAYER LOGIN"
                subtitle = "Enter IP:PORT" if self.state == "CONNECT" else "Enter Username"
                
                self.draw_minecraft_box(312, 284, 400, 200, title)
                input_surf = self.font_main.render(self.input_text + "|", True, (255, 255, 255))
                self.screen.blit(input_surf, (332, 360))
                self.draw_text_centered(subtitle, 330, self.font_small, (150, 150, 150), shadow=False)

            elif self.state == "GAME" and self.game_state:
                # ציור המפה והיחידות (כפי שעשינו קודם)
                for y, row in enumerate(self.game_state["map"]):
                    for x, tile in enumerate(row):
                        screen_x = x * self.tile_size - self.camera_x
                        screen_y = y * self.tile_size - self.camera_y
                        if -self.tile_size < screen_x < 1024 and -self.tile_size < screen_y < 768:
                            color = (34, 139, 34) if tile["terrain"] == "plains" else (100, 149, 237)
                            pygame.draw.rect(self.screen, color, (screen_x, screen_y, self.tile_size, self.tile_size))
                            pygame.draw.rect(self.screen, (0, 0, 0, 30), (screen_x, screen_y, self.tile_size, self.tile_size), 1)
                
                for uid, u in self.game_state["units"].items():
                    color = (255, 255, 0) if u["owner"] == self.my_id else (255, 50, 50)
                    pos = (u["x"] * self.tile_size - self.camera_x + self.tile_size // 2, u["y"] * self.tile_size - self.camera_y + self.tile_size // 2)
                    if -32 < pos[0] < 1056 and -32 < pos[1] < 800:
                        pygame.draw.circle(self.screen, color, pos, 15)
                        # סימון יחידה נבחרת בריבוע לבן
                        if self.selected_unit_id == uid:
                            pygame.draw.rect(self.screen, (255, 255, 255), (u["x"]*self.tile_size - self.camera_x, u["y"]*self.tile_size - self.camera_y, self.tile_size, self.tile_size), 2)

                if self.selected_unit_id:
                    unit = self.game_state["units"].get(self.selected_unit_id)
                    if unit:
                        unit_info = GameData.UNITS.get(unit["type"], {})
                        if unit_info["name"] == "Settler":
                            # ציור כפתור פשוט בצד
                            rect = pygame.Rect(10, 600, 150, 40)
                            pygame.draw.rect(self.screen, (200, 200, 200), rect)
                            txt = self.font_small.render("Found City (B)", True, (0, 0, 0))
                            self.screen.blit(txt, (20, 610))
                            # בדיקה אם לחצו על המקש B
                            if pygame.key.get_pressed()[pygame.K_b] or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and rect.collidepoint(pygame.mouse.get_pos())):
                                self.send_net_msg({"type": "FOUND_CITY", "unit_id": self.selected_unit_id})
                        elif unit_info["range"] > 0:
                            btn_rect = pygame.Rect(10, 550, 150, 40)
                            pygame.draw.rect(self.screen, (200, 50, 50) if self.target_mode else (100, 100, 100), btn_rect)
                            self.screen.blit(self.font_small.render("Target (R)", True, (255,255,255)), (20, 558))
                            
                            # לחיצה על R תפעיל את מצב המטרה
                            if pygame.key.get_pressed()[pygame.K_r]:
                                self.target_mode = True

            pygame.display.flip()
        pygame.quit()

if __name__ == "__main__":
    CivClient().run()