import pygame
import math
import time
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

class Renderer:
    def __init__(self, app):
        self.app = app
        self.screen = app.screen
        self.font_title = pygame.font.SysFont("Impact", 100)
        self.font_main = pygame.font.SysFont("Arial", 32, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 20)
        self.surface_cache = {}
        self.fonts_cache = {}

    def get_dynamic_font(self, size):
        if size not in self.fonts_cache:
            self.fonts_cache[size] = pygame.font.SysFont("Arial", size, bold=True)
        return self.fonts_cache[size]

    def get_cached_text(self, text, font, color, shadow=True):
        key = (text, font, color, shadow)
        if key not in self.surface_cache:
            if shadow:
                shadow_surf = font.render(text, True, (20, 20, 20))
                surf = font.render(text, True, color)
                self.surface_cache[key] = (shadow_surf, surf)
            else:
                surf = font.render(text, True, color)
                self.surface_cache[key] = (None, surf)
        return self.surface_cache[key]

    def draw_text_centered(self, text, y, font, color, shadow=True):
        shadow_surf, surf = self.get_cached_text(text, font, color, shadow)
        if shadow and shadow_surf:
            self.screen.blit(shadow_surf, (512 - shadow_surf.get_width()//2 + 4, y + 4))
        self.screen.blit(surf, (512 - surf.get_width()//2, y))
        
    def draw_minecraft_box(self, x, y, w, h, title):
        box_surf = pygame.Surface((w, h), pygame.SRCALPHA)
        box_surf.fill((0, 0, 0, 180)) 
        self.screen.blit(box_surf, (x, y))
        pygame.draw.rect(self.screen, (255, 255, 255), (x, y, w, h), 2)
        
        _, t_surf = self.get_cached_text(title, self.font_small, (255, 215, 0), shadow=False)
        self.screen.blit(t_surf, (x + 20, y + 20))

    def render(self):
        self.screen.fill((20, 20, 40))
        app = self.app
        state = app.state

        if state == "SPLASH":
            pulse = (math.sin(time.time() * 5) + 1) / 2
            color = (255, 200 + int(55 * pulse), 50)
            self.draw_text_centered("MY CIVILIZATION 2", 250, self.font_title, color)
            self.draw_text_centered("Shaked Horn", 400, self.font_main, (200, 200, 200))
            if time.time() - app.start_time > 3: app.state = "CONNECT"

        elif state in ["CONNECT", "LOGIN", "LOBBY"]:
            pygame.draw.rect(self.screen, (30, 60, 100), (0, 0, 1024, 768))
            if state == "CONNECT":
                title, subtitle = "SERVER CONNECTION", "Enter IP:PORT"
            elif state == "LOGIN":
                title, subtitle = "PLAYER LOGIN", "Enter Username"
            else:
                title, subtitle = "GAME LOBBY", "Enter Game Name (Join/Create)"
            
            self.draw_minecraft_box(312, 284, 400, 200, title)
            _, input_surf = self.get_cached_text(app.input_text + "|", self.font_main, (255, 255, 255), shadow=False)
            self.screen.blit(input_surf, (332, 360))
            self.draw_text_centered(subtitle, 330, self.font_small, (150, 150, 150), shadow=False)
            
            if state == "LOBBY":
                y_offset = 500
                self.draw_text_centered("Active Games:", y_offset, self.font_small, (255, 255, 0))
                for g in app.games_list:
                    y_offset += 30
                    self.draw_text_centered(g, y_offset, self.font_small, (200, 200, 200))

        elif state == "GAME" and app.game_state:
            if not app.game_state.get("game_started", False):
                pygame.draw.rect(self.screen, (30, 60, 100), (0, 0, 1024, 768))
                self.draw_minecraft_box(312, 284, 400, 200, "WAITING FOR PLAYERS")
                self.draw_text_centered(f"Connected: {len(app.game_state.get('players', {}))} / 2+", 360, self.font_small, (200, 200, 200), shadow=False)
                self.draw_text_centered("The game will start automatically.", 400, self.font_small, (150, 150, 150), shadow=False)
                pygame.display.flip()
                return

            if app.active_panel == "MAP":
                self.render_map()
            elif app.active_panel in ["TECH", "CIVIC"]:
                app.ui_manager.render_tree(self)

            app.ui_manager.render_top_ui(self)
            app.ui_manager.render_bottom_ui(self)
            
            me = app.game_state.get("players", {}).get(app.my_id, {})
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

    def render_map(self):
        app = self.app
        map_data = app.game_state.get("world", {}).get("map_data", app.game_state.get("map", []))
        map_h = len(map_data)
        if map_h == 0: return
        map_w = len(map_data[0])
        map_pixel_w = map_w * app.tile_size
        
        if not getattr(app, "camera_initialized", False) and app.game_state.get("units"):
            for uid, u in app.game_state["units"].items():
                if u.get("owner") == app.my_id:
                    app.camera_x = u["x"] * app.tile_size - 1024 // 2
                    app.camera_y = max(0, min(u["y"] * app.tile_size - 600 // 2, map_h * app.tile_size - 560))
                    app.camera_initialized = True
                    break

        # CAMERA CULLING for terrain
        start_y = max(0, int((app.camera_y - 40) // app.tile_size))
        end_y = min(map_h, int((app.camera_y + 600 - 40) // app.tile_size) + 2)

        start_x_tiles = int(app.camera_x // app.tile_size)
        tiles_on_screen_x = int(1024 // app.tile_size) + 2

        for y in range(start_y, end_y):
            for i in range(tiles_on_screen_x):
                x = (start_x_tiles + i) % map_w
                tile = map_data[y][x]
                
                screen_x = (x * app.tile_size - app.camera_x) % map_pixel_w
                if screen_x > map_pixel_w - app.tile_size: screen_x -= map_pixel_w
                screen_y = y * app.tile_size - app.camera_y + 40
                
                vis = tile.get("visibility", "visible")
                
                if vis == "unexplored":
                    pygame.draw.rect(self.screen, (0, 0, 0), (screen_x, screen_y, app.tile_size, app.tile_size))
                    continue
                    
                color = TERRAIN_COLORS.get(tile["terrain"], (255, 0, 255))
                pygame.draw.rect(self.screen, color, (screen_x, screen_y, app.tile_size, app.tile_size))
                
                if vis == "fog":
                    fog_surf = pygame.Surface((app.tile_size, app.tile_size), pygame.SRCALPHA)
                    fog_surf.fill((0, 0, 0, 150))
                    self.screen.blit(fog_surf, (screen_x, screen_y))
                
                imp = tile.get("improvement")
                if imp:
                    imp_color = (50, 200, 50) if imp == "farm" else (100, 100, 100) if imp in ["mine", "quarry"] else (200, 200, 50) if imp == "pasture" else (0, 150, 200) if imp == "fishingBoats" else (200, 100, 50)
                    pygame.draw.rect(self.screen, imp_color, (screen_x + 8, screen_y + 8, 16, 16))
                    pygame.draw.rect(self.screen, (0, 0, 0), (screen_x + 8, screen_y + 8, 16, 16), 1)
                
                district = tile.get("district")
                if district:
                    d_colors = {
                        "campus": (100, 200, 255), "holySite": (220, 200, 255), "encampment": (200, 100, 50),
                        "commercialHub": (255, 215, 0), "industrialZone": (210, 130, 40), "theaterSquare": (200, 50, 200)
                    }
                    dc = d_colors.get(district, (150, 150, 150))
                    pygame.draw.rect(self.screen, dc, (screen_x + 4, screen_y + 4, app.tile_size - 8, app.tile_size - 8))
                    pygame.draw.rect(self.screen, (0, 0, 0), (screen_x + 4, screen_y + 4, app.tile_size - 8, app.tile_size - 8), 2)
                
                owner = tile.get("owner", -1)
                if owner != -1:
                    p_color = app.game_state.get("players", {}).get(owner, {}).get("color", (255, 255, 255))
                    border_thick = max(2, app.tile_size // 12)
                
                    if y == 0 or map_data[y-1][x].get("owner", -1) != owner:
                        pygame.draw.rect(self.screen, p_color, (screen_x, screen_y, app.tile_size, border_thick))
                    if y == map_h - 1 or map_data[y+1][x].get("owner", -1) != owner:
                        pygame.draw.rect(self.screen, p_color, (screen_x, screen_y + app.tile_size - border_thick, app.tile_size, border_thick))
                    lx = (x - 1) % map_w
                    if map_data[y][lx].get("owner", -1) != owner:
                        pygame.draw.rect(self.screen, p_color, (screen_x, screen_y, border_thick, app.tile_size))
                    rx = (x + 1) % map_w
                    if map_data[y][rx].get("owner", -1) != owner:
                        pygame.draw.rect(self.screen, p_color, (screen_x + app.tile_size - border_thick, screen_y, border_thick, app.tile_size))
                
                pygame.draw.rect(self.screen, (40, 40, 40), (screen_x, screen_y, app.tile_size, app.tile_size), 1)

        # Draw city lines
        for cid, city in app.game_state.get("cities", {}).items():
            prod_item = city.get("production_item")
            if prod_item and prod_item.get("tx") is not None and prod_item.get("ty") is not None:
                tx, ty = prod_item["tx"], prod_item["ty"]
                screen_tx = (tx * app.tile_size - app.camera_x) % map_pixel_w
                if screen_tx > map_pixel_w - app.tile_size: screen_tx -= map_pixel_w
                screen_ty = ty * app.tile_size - app.camera_y + 40
                if -app.tile_size < screen_tx < 1024 and -app.tile_size < screen_ty < 600:
                    for i in range(0, app.tile_size, 8):
                        pygame.draw.line(self.screen, (255, 255, 0), (screen_tx + i, screen_ty), (screen_tx, screen_ty + i), 2)
                        pygame.draw.line(self.screen, (0, 0, 0), (screen_tx + i + 2, screen_ty), (screen_tx, screen_ty + i + 2), 2)
                    pygame.draw.rect(self.screen, (255, 255, 0), (screen_tx, screen_ty, app.tile_size, app.tile_size), 3)

        # Target mode DISTRICT overlay
        if app.target_mode == "DISTRICT" and app.selected_city_id:
            city = app.game_state.get("cities", {}).get(app.selected_city_id)
            if city:
                target_b = getattr(app, "target_building", "")
                for dx in range(-3, 4):
                    for dy in range(-3, 4):
                        tx, ty = (city["x"] + dx) % map_w, city["y"] + dy
                        if 0 <= ty < map_h:
                            tile = map_data[ty][tx]
                            if tile.get("owner") == app.my_id and not tile.get("district") and not (tx == city["x"] and ty == city["y"]):
                                t_type = tile.get("terrain")
                                is_water = GameData.TERRAIN.get(t_type, {}).get("isWater", False)
                                if target_b == "harbor":
                                    if t_type != "coast": continue
                                else:
                                    if is_water or t_type == "mountains": continue
                                
                                screen_tx = (tx * app.tile_size - app.camera_x) % map_pixel_w
                                if screen_tx > map_pixel_w - app.tile_size: screen_tx -= map_pixel_w
                                screen_ty = ty * app.tile_size - app.camera_y + 40
                                if -app.tile_size < screen_tx < 1024 and -app.tile_size < screen_ty < 600:
                                    s = pygame.Surface((app.tile_size, app.tile_size), pygame.SRCALPHA)
                                    s.fill((100, 200, 255, 120))
                                    self.screen.blit(s, (screen_tx, screen_ty))
                                    pygame.draw.rect(self.screen, (255, 255, 255), (screen_tx, screen_ty, app.tile_size, app.tile_size), 2)

        # Draw cities
        for cid, city in app.game_state.get("cities", {}).items():
            screen_x = (city["x"] * app.tile_size - app.camera_x) % map_pixel_w
            if screen_x > map_pixel_w - app.tile_size: screen_x -= map_pixel_w
        
            screen_y = city["y"] * app.tile_size - app.camera_y + 40
            if -app.tile_size < screen_x < 1024 and -app.tile_size < screen_y < 600:
                owner_color = app.game_state.get("players", {}).get(city.get("owner", ""), {}).get("color", (150, 150, 150))
                pygame.draw.rect(self.screen, owner_color, (screen_x, screen_y, app.tile_size, app.tile_size))
                pygame.draw.rect(self.screen, (0, 0, 0), (screen_x, screen_y, app.tile_size, app.tile_size), 2)
            
                b_colors = {
                    "monument": (100, 100, 255), "granary": (255, 200, 0), "library": (0, 100, 200),
                    "university": (0, 50, 150), "shrine": (150, 100, 200), "temple": (100, 50, 150),
                    "waterMill": (50, 50, 200), "barracks": (150, 50, 25), "market": (200, 180, 0),
                    "workshop": (150, 80, 20), "amphitheater": (150, 30, 150)
                }
                buildings = city.get("buildings", [])
                b_placements = {(city["x"], city["y"]): []}
                for b in buildings:
                    if b == "cityCenter": continue
                    b_stats = GameData.BUILDINGS.get(b, {})
                    req = b_stats.get("requiredBefore")
                    placed = False
                    if req:
                        for ox, oy in city.get("owned_tiles", []):
                            if map_data[oy][ox].get("district") == req:
                                b_placements.setdefault((ox, oy), []).append(b)
                                placed = True
                                break
                    if not placed:
                        b_placements[(city["x"], city["y"])].append(b)
                        
                for (bx_tile, by_tile), b_list in b_placements.items():
                    bx_screen = (bx_tile * app.tile_size - app.camera_x) % map_pixel_w
                    if bx_screen > map_pixel_w - app.tile_size: bx_screen -= map_pixel_w
                    by_screen = by_tile * app.tile_size - app.camera_y + 40
                    
                    b_idx = 0
                    for b in b_list:
                        bc = b_colors.get(b, (200, 200, 200))
                        bx = bx_screen + 2 + (b_idx * 8) % (app.tile_size - 8)
                        by = by_screen + app.tile_size - 8
                        pygame.draw.rect(self.screen, bc, (bx, by, 6, 6))
                        pygame.draw.rect(self.screen, (0, 0, 0), (bx, by, 6, 6), 1)
                        b_idx += 1
                
                if app.selected_city_id == cid:
                    pygame.draw.rect(self.screen, (255, 255, 255), (screen_x, screen_y, app.tile_size, app.tile_size), 3)
                    
                hp = city.get("hp", 200)
                if hp < 200:
                    hp_ratio = max(0, hp / 200)
                    pygame.draw.rect(self.screen, (200, 0, 0), (screen_x, screen_y - 6, app.tile_size, 4))
                    pygame.draw.rect(self.screen, (0, 200, 0), (screen_x, screen_y - 6, int(app.tile_size * hp_ratio), 4))

        # Draw units
        unit_counts = {}
        for uid, u in app.game_state["units"].items():
            coord = (u["x"], u["y"])
            unit_counts[coord] = unit_counts.get(coord, 0) + 1
        
        drawn_units = {}
        for uid, u in app.game_state["units"].items():
            base_color = app.game_state.get("players", {}).get(u.get("owner", ""), {}).get("color", (255, 255, 255))
            color = base_color
            if u["owner"] == app.my_id and u.get("has_moved", False):
                color = (max(0, base_color[0] - 100), max(0, base_color[1] - 100), max(0, base_color[2] - 100))
            
            coord = (u["x"], u["y"])
            idx = drawn_units.get(coord, 0)
            drawn_units[coord] = idx + 1
            
            offset_x = (idx * (app.tile_size // 6)) if unit_counts[coord] > 1 else 0
            offset_y = (idx * (app.tile_size // 6)) if unit_counts[coord] > 1 else 0
            
            ux_screen = (u["x"] * app.tile_size - app.camera_x) % map_pixel_w
            if ux_screen > map_pixel_w - app.tile_size: ux_screen -= map_pixel_w
        
            pos = (ux_screen + app.tile_size // 2 + offset_x, u["y"] * app.tile_size - app.camera_y + app.tile_size // 2 + 40 + offset_y)
            if -app.tile_size < pos[0] < 1024 + app.tile_size and -app.tile_size < pos[1] < 600 + app.tile_size:
                radius = max(4, app.tile_size // 3)
                pygame.draw.circle(self.screen, color, pos, radius)
            
                u_type = u.get("type", "?")
                # Can use surface caching for unit types if we want, but creating a dynamic font every frame is slow
                # So let's memoize it here using font sizes
                font_size = max(8, app.tile_size // 2)
                font_key = ("Arial", font_size, bold:=False)
                dynamic_font = self.get_dynamic_font(font_size)
                _, char_surf = self.get_cached_text(u_type[0].upper(), dynamic_font, (0, 0, 0), shadow=False)
                char_rect = char_surf.get_rect(center=pos)
                self.screen.blit(char_surf, char_rect)
            
                if app.selected_unit_id == uid:
                    pygame.draw.rect(self.screen, (255, 255, 255), (ux_screen + offset_x, u["y"]*app.tile_size - app.camera_y + 40 + offset_y, app.tile_size, app.tile_size), 2)
                    
                hp = u.get("hp", 100)
                if hp < 100:
                    hp_ratio = max(0, hp / 100)
                    hp_y = u["y"]*app.tile_size - app.camera_y + 40 - 12 + offset_y
                    pygame.draw.rect(self.screen, (200, 0, 0), (ux_screen + offset_x, hp_y, app.tile_size, 4))
                    pygame.draw.rect(self.screen, (0, 200, 0), (ux_screen + offset_x, hp_y, int(app.tile_size * hp_ratio), 4))
