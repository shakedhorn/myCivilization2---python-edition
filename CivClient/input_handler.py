import pygame
import threading
from CivShared.game_defs import GameData

class InputHandler:
    def __init__(self, app):
        self.app = app

    def handle_events(self):
        app = self.app
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
                
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if app.state == "CONNECT":
                        try:
                            ip, port = app.input_text.split(":")
                            app.network.connect(ip, int(port))
                            app.state = "LOGIN"
                            app.input_text = ""
                        except:
                            app.input_text = "ERROR: IP:PORT"
                    elif app.state == "LOGIN":
                        app.username = app.input_text
                        resp = app.network.login(app.username)
                        if resp and resp["status"] == "LOGIN_OK":
                            app.games_list = resp.get("games", [])
                            app.state = "LOBBY"
                            app.input_text = ""
                            app.network.close() 
                        else:
                            app.input_text = "ERROR: SERVER DISCONNECTED"
                    elif app.state == "LOBBY":
                        game_name = app.input_text
                        try:
                            app.network.connect(app.server_ip, 54321)
                            import json
                            # Let the server decide whether to join or create
                            msg_dict = {"type": "JOIN_OR_CREATE", "name": game_name}
                            app.network.sock.sendall(json.dumps(msg_dict).encode())
                            
                            resp = app.network.recv_json()
                            if resp and resp.get("status") == "JOIN_SUCCESS":
                                port = resp["port"]
                                app.network.close()
                                app.network.connect(app.server_ip, port)
                                app.network.send_net_msg({"type": "LOGIN", "user": app.username})
                                game_resp = app.network.recv_prefixed_json()
                                
                                if game_resp and game_resp.get("status") == "LOGIN_OK":
                                    app.my_id = str(game_resp["id"])
                                    app.state = "GAME"
                                    threading.Thread(target=app.network.network_loop, daemon=True).start()
                            else:
                                err_msg = resp.get("message", "SERVER DISCONNECTED") if resp else "SERVER DISCONNECTED"
                                app.input_text = f"ERROR: {err_msg}"
                                app.network.close()
                        except Exception as e:
                            app.input_text = f"CONN ERROR: {e}"
                elif event.key == pygame.K_BACKSPACE:
                    app.input_text = app.input_text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    app.target_mode = None
                    app.target_building = None
                elif event.key == pygame.K_SPACE and app.state == "GAME" and app.game_state and app.game_state.get("game_started", False):
                    if app.selected_unit_id:
                        app.network.send_net_msg({"type": "SKIP_UNIT_TURN", "unit_id": app.selected_unit_id})
                else:
                    app.input_text += event.unicode
                    
            elif event.type == pygame.MOUSEMOTION and app.state == "GAME" and app.game_state and app.game_state.get("game_started", False):
                if event.buttons[0] or event.buttons[1] or event.buttons[2]:
                    app.camera_x -= event.rel[0]
                    app.camera_y -= event.rel[1]
                    
                    if "map" in app.game_state:
                        map_pixel_w = len(app.game_state["map"][0]) * app.tile_size
                        map_height = len(app.game_state["map"]) * app.tile_size
                        max_y = max(0, map_height - 560)
                        app.camera_x %= map_pixel_w
                        app.camera_y = max(0, min(app.camera_y, max_y))
                        
            elif event.type == pygame.MOUSEBUTTONDOWN and app.state == "GAME" and app.game_state and app.game_state.get("game_started", False):
                mx, my = pygame.mouse.get_pos()
                if my < 40:
                    if event.button == 1:
                        if 600 <= mx <= 700: app.active_panel = "MAP"
                        elif 720 <= mx <= 860: app.active_panel = "TECH"
                        elif 880 <= mx <= 1020: app.active_panel = "CIVIC"
                    continue
                    
                if app.active_panel in ["TECH", "CIVIC"] and 40 <= my < 600:
                    mods = pygame.key.get_mods()
                    if event.button == 4:
                        if mods & pygame.KMOD_SHIFT: app.tree_scroll_y = min(0, app.tree_scroll_y + 40)
                        else: app.tree_scroll_x = min(0, app.tree_scroll_x + 40)
                    elif event.button == 5:
                        if mods & pygame.KMOD_SHIFT: app.tree_scroll_y -= 40
                        else: app.tree_scroll_x -= 40
                    
                    if event.button in [4, 5]:
                        is_tech = (app.active_panel == "TECH")
                        items = GameData.TECHS if is_tech else GameData.CIVICS
                        layout = app.ui_manager.get_tree_layout(items, is_tech)
                        max_x = max([pos[0] for pos in layout.values()]) if layout else 0
                        scroll_limit = -max(0, max_x - 700)
                        app.tree_scroll_y = max(-3000, min(0, app.tree_scroll_y))
                        app.tree_scroll_x = max(scroll_limit, min(0, app.tree_scroll_x))
                        
                    elif event.button == 1:
                        is_tech = (app.active_panel == "TECH")
                        items = GameData.TECHS if is_tech else GameData.CIVICS
                        layout = app.ui_manager.get_tree_layout(items, is_tech)
                        for key, (cx, cy) in layout.items():
                            rect = pygame.Rect(cx + app.tree_scroll_x, cy + app.tree_scroll_y, 200, 115)
                            if rect.collidepoint(mx, my):
                                if is_tech: app.network.send_net_msg({"type": "CHOOSE_RESEARCH", "tech": key})
                                else: app.network.send_net_msg({"type": "CHOOSE_CIVIC", "civic": key})
                    continue
                
                if my >= 600:
                    if event.button == 1:
                        if app.selected_unit_id:
                            unit = app.game_state["units"].get(app.selected_unit_id)
                            if unit and not unit.get("has_moved"):
                                unit_info = GameData.UNITS.get(unit["type"], {})
                                if unit_info.get("name") == "Settler":
                                    btn_rect = pygame.Rect(250, 620, 150, 40)
                                    if btn_rect.collidepoint(mx, my):
                                        app.network.send_net_msg({"type": "FOUND_CITY", "unit_id": app.selected_unit_id})
                                elif unit_info.get("range", 0) > 0:
                                    btn_rect = pygame.Rect(250, 620, 150, 40)
                                    if btn_rect.collidepoint(mx, my):
                                        app.target_mode = None if app.target_mode == "ATTACK" else "ATTACK"
                                elif unit_info.get("name") == "Builder":
                                    ux, uy = unit["x"], unit["y"]
                                    tile = app.game_state["map"][uy][ux]
                                    t_type = tile["terrain"]
                                    has_imp = tile.get("improvement") is not None
                                    charges = unit.get("charges", 0)
                                    if not has_imp and charges > 0:
                                        possible = []
                                        me = app.game_state.get("players", {}).get(app.my_id, {})
                                        my_techs = me.get("techs", [])
                                        if tile.get("owner") == app.my_id:
                                            for imp_id, imp_data in GameData.IMPROVEMENTS.items():
                                                if t_type in imp_data.get("valid_terrains", []) and (not imp_data.get("required_tech") or imp_data["required_tech"] in my_techs):
                                                    possible.append((imp_data["name"], imp_id))
                                        for idx, (label, imp_id) in enumerate(possible):
                                            bx = 250 + idx * 150
                                            btn_rect = pygame.Rect(bx, 620, 140, 40)
                                            if btn_rect.collidepoint(mx, my):
                                                app.network.send_net_msg({"type": "BUILD_IMPROVEMENT", "unit_id": app.selected_unit_id, "improvement": imp_id})
                        
                        me = app.game_state.get("players", {}).get(app.my_id, {})
                        if not me.get("ended_turn", False):
                            my_units = [u for u in app.game_state["units"].values() if u["owner"] == app.my_id]
                            all_moved = all(u.get("has_moved", False) for u in my_units)
                            my_cities = [c for c in app.game_state.get("cities", {}).values() if c["owner"] == app.my_id]
                            all_producing = all(c.get("production_item") is not None for c in my_cities)
                            
                            if all_moved and all_producing:
                                if me.get("current_research") is None:
                                    end_btn_rect = pygame.Rect(750, 620, 260, 50)
                                    if end_btn_rect.collidepoint(mx, my): app.active_panel = "TECH"
                                elif me.get("current_civic") is None:
                                    end_btn_rect = pygame.Rect(750, 620, 260, 50)
                                    if end_btn_rect.collidepoint(mx, my): app.active_panel = "CIVIC"
                                else:
                                    end_btn_rect = pygame.Rect(800, 620, 180, 50)
                                    if end_btn_rect.collidepoint(mx, my):
                                        app.network.send_net_msg({"type": "END_TURN"})
                                        app.active_panel = "MAP"
                            elif not all_producing:
                                end_btn_rect = pygame.Rect(750, 620, 260, 50)
                                if end_btn_rect.collidepoint(mx, my):
                                    for cid, city in app.game_state.get("cities", {}).items():
                                        if city["owner"] == app.my_id and city.get("production_item") is None:
                                            app.selected_city_id = cid
                                            app.selected_unit_id = None
                                            break
                    continue
                    
                if app.selected_city_id and mx >= 824 and 40 <= my <= 600:
                    if event.button == 1:
                        me = app.game_state.get("players", {}).get(app.my_id, {})
                        my_techs = me.get("techs", [])
                        my_civics = me.get("civics", [])
                        city = app.game_state.get("cities", {}).get(app.selected_city_id, {})
                        options = []
                        
                        for uid, u_stats in GameData.UNITS.items():
                            if u_stats["requiredTech"] and u_stats["requiredTech"] not in my_techs: continue
                            if u_stats["UpgradeTo"]:
                                upg_tech = GameData.UNITS[u_stats["UpgradeTo"]]["requiredTech"]
                                if upg_tech and upg_tech in my_techs: continue
                            if u_stats.get("isNaval", False):
                                has_water = False
                                if "harbor" in city.get("buildings", []):
                                    has_water = True
                                else:
                                    for ox, oy in city.get("owned_tiles", []):
                                        if 0 <= oy < len(app.game_state["map"]):
                                            tt = app.game_state["map"][oy][ox]["terrain"]
                                            if GameData.TERRAIN.get(tt, {}).get("isWater", False):
                                                has_water = True
                                                break
                                if not has_water: continue
                            options.append((u_stats["name"], "unit", uid))
                            
                        for bid, b_stats in GameData.BUILDINGS.items():
                            if bid in city.get("buildings", []): continue
                            if b_stats["requiredTech"] and b_stats["requiredTech"] not in my_techs: continue
                            if b_stats["requiredCivic"] and b_stats["requiredCivic"] not in my_civics: continue
                            if b_stats["requiredBefore"] and b_stats["requiredBefore"] not in city.get("buildings", []): continue
                            options.append((b_stats["name"], "building", bid))
                        
                        app.current_prod_list_len = len(options)
                        
                        for i, (label, cat, internal_name) in enumerate(options):
                            bx = 834
                            by = 90 + i * 50 + app.city_build_scroll_y
                            brect = pygame.Rect(bx, by, 180, 40)
                            if brect.collidepoint(mx, my):
                                if cat == "building" and GameData.BUILDINGS.get(internal_name, {}).get("requiresTile", False):
                                    app.target_mode = "DISTRICT"
                                    app.target_building = internal_name
                                else:
                                    app.network.send_net_msg({
                                        "type": "CHANGE_PRODUCTION",
                                        "city_id": app.selected_city_id,
                                        "category": cat,
                                        "item": internal_name
                                    })
                    continue
                    
                map_w = len(app.game_state["map"][0]) if app.game_state.get("map") else 1
                grid_x = ((mx + app.camera_x) // app.tile_size) % map_w
                grid_y = (my - 40 + app.camera_y) // app.tile_size
                
                if event.button == 1:
                    if app.target_mode == "ATTACK" and app.selected_unit_id:
                        app.network.send_net_msg({
                            "type": "RANGED_ATTACK",
                            "unit_id": app.selected_unit_id,
                            "tx": grid_x, "ty": grid_y
                        })
                        app.target_mode = None
                    elif app.target_mode == "DISTRICT" and app.selected_city_id:
                        app.network.send_net_msg({
                            "type": "CHANGE_PRODUCTION",
                            "city_id": app.selected_city_id,
                            "category": "building",
                            "item": getattr(app, "target_building", None),
                            "tx": grid_x, "ty": grid_y
                        })
                        app.target_mode = None
                    else:
                        found_unit = False
                        for uid, unit in app.game_state["units"].items():
                            if unit["x"] == grid_x and unit["y"] == grid_y and unit["owner"] == app.my_id:
                                app.selected_unit_id = uid
                                app.selected_city_id = None
                                found_unit = True
                        if not found_unit:
                            app.selected_unit_id = None
                            found_city = False
                            for cid, city in app.game_state.get("cities", {}).items():
                                if city["x"] == grid_x and city["y"] == grid_y and city["owner"] == app.my_id:
                                    app.selected_city_id = cid
                                    found_city = True
                            if not found_city:
                                app.selected_city_id = None

                elif event.button == 3:
                    if app.target_mode:
                        app.target_mode = None
                        app.target_building = None
                    elif app.selected_unit_id:
                        unit = app.game_state["units"].get(app.selected_unit_id)
                        if unit and not unit.get("has_moved", False):
                            app.network.send_net_msg({
                                "type": "MOVE_UNIT",
                                "unit_id": app.selected_unit_id,
                                "nx": grid_x, "ny": grid_y
                            })
                            
            elif event.type == pygame.MOUSEWHEEL and app.state == "GAME":
                mx, my = pygame.mouse.get_pos()
                if app.selected_city_id and mx >= 824 and 40 <= my <= 600:
                    app.city_build_scroll_y += event.y * 20
                    app.city_build_scroll_y = min(0, app.city_build_scroll_y)
                    num_items = max(6, getattr(app, 'current_prod_list_len', 6))
                    content_height = num_items * 50 + 20
                    max_scroll = max(0, content_height - 560)
                    app.city_build_scroll_y = max(-max_scroll, app.city_build_scroll_y)
                elif 40 <= my < 600 and (mx < 824 if app.selected_city_id else True):
                    if app.game_state and "map" in app.game_state:
                        old_tile_size = app.tile_size
                        zoom_amount = event.y * 4
                        new_tile_size = app.tile_size + zoom_amount
                        
                        map_height_tiles = len(app.game_state["map"])
                        min_tile_size = (560 + map_height_tiles - 1) // map_height_tiles
                        max_tile_size = 560 // 8
                        
                        new_tile_size = max(min_tile_size, min(max_tile_size, new_tile_size))
                        
                        if new_tile_size != old_tile_size:
                            grid_x_exact = (mx + app.camera_x) / old_tile_size
                            grid_y_exact = (my - 40 + app.camera_y) / old_tile_size
                            
                            app.tile_size = new_tile_size
                            app.camera_x = int(grid_x_exact * app.tile_size - mx)
                            app.camera_y = int(grid_y_exact * app.tile_size - (my - 40))

        return True

    def handle_keys_held(self):
        app = self.app
        if app.state == "GAME" and app.game_state and "map" in app.game_state:
            keys = pygame.key.get_pressed()
            scroll_speed = 20
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                app.camera_x -= scroll_speed
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                app.camera_x += scroll_speed
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                app.camera_y -= scroll_speed
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                app.camera_y += scroll_speed
                
            map_pixel_w = len(app.game_state["map"][0]) * app.tile_size
            map_height = len(app.game_state["map"]) * app.tile_size
            max_y = max(0, map_height - 560)
            
            app.camera_x %= map_pixel_w
            app.camera_y = max(0, min(app.camera_y, max_y))
