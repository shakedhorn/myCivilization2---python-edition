import pygame
import math
from CivShared.game_defs import GameData

class UIManager:
    def __init__(self, app):
        self.app = app
        self.screen = app.screen

    def get_tree_layout(self, items_dict, is_tech):
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
            
        card_w, card_h = 200, 115
        margin_x, margin_y = 100, 20
        
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
                
            max_per_col = 4
            num_items = len(items_in_tier)
            
            for idx, key in enumerate(items_in_tier):
                col_offset = idx // max_per_col
                row_idx = idx % max_per_col
                
                cx = current_x + (col_offset * (card_w + 20))
                cy = 80 + row_idx * (card_h + margin_y)
                layout[key] = (cx, cy)
                
            cols_needed = math.ceil(num_items / max_per_col) if num_items > 0 else 1
            current_x += cols_needed * (card_w + margin_x)
                
        return layout

    def render_tree(self, renderer):
        app = self.app
        is_tech = app.active_panel == "TECH"
        title = "Science Tree" if is_tech else "Civic Tree"
        source_dict = GameData.TECHS if is_tech else GameData.CIVICS
        
        self.screen.set_clip(pygame.Rect(0, 40, 1024 if not app.selected_city_id else 824, 560))
        pygame.draw.rect(self.screen, (20, 20, 30), (0, 40, 1024, 560))
        renderer.draw_text_centered(title, 60, renderer.font_main, (255, 255, 255))
        
        me = app.game_state.get("players", {}).get(app.my_id, {})
        my_techs = me.get("techs", [])
        my_civics = me.get("civics", [])
        current_res = me.get("current_research") if is_tech else me.get("current_civic")
        res_prog = me.get("research_progress", 0) if is_tech else me.get("civic_progress", 0)
        
        layout = self.get_tree_layout(source_dict, is_tech)
        card_width, card_height = 200, 115
        
        # Draw connecting lines
        for key, (cx, cy) in layout.items():
            reqs = source_dict[key].get("required_techs", []) if is_tech else source_dict[key].get("required_civics", [])
            for req in reqs:
                if req in layout:
                    rx, ry = layout[req]
                    start_pos = (rx + card_width + app.tree_scroll_x, ry + card_height // 2 + app.tree_scroll_y)
                    end_pos = (cx + app.tree_scroll_x, cy + card_height // 2 + app.tree_scroll_y)
                    start_x, start_y = start_pos
                    end_x, end_y = end_pos
                    mid_x = start_x + 30
                    pygame.draw.line(self.screen, (100, 100, 100), (start_x, start_y), (mid_x, start_y), 3)
                    pygame.draw.line(self.screen, (100, 100, 100), (mid_x, start_y), (mid_x, end_y), 3)
                    pygame.draw.line(self.screen, (100, 100, 100), (mid_x, end_y), (end_x, end_y), 3)
        
        # Draw cards
        for key, (cx, cy) in layout.items():
            data = source_dict[key]
            draw_x = cx + app.tree_scroll_x
            draw_y = cy + app.tree_scroll_y
            rect = pygame.Rect(draw_x, draw_y, card_width, card_height)
            
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
            
            # Using renderer cache for text
            _, n_surf = renderer.get_cached_text(data["name"], renderer.font_small, (255, 255, 255), shadow=False)
            self.screen.blit(n_surf, (draw_x + 10, draw_y + 10))
            
            cost = data.get("science_cost", 0) if is_tech else data.get("culture_cost", 0)
            
            if is_researching:
                _, p_surf = renderer.get_cached_text(f"Progress: {int(res_prog)}/{cost}", renderer.font_small, (200, 200, 255), shadow=False)
                self.screen.blit(p_surf, (draw_x + 10, draw_y + 40))
            elif not is_unlocked:
                _, p_surf = renderer.get_cached_text(f"Cost: {cost}", renderer.font_small, (200, 200, 200), shadow=False)
                self.screen.blit(p_surf, (draw_x + 10, draw_y + 40))
            else:
                _, p_surf = renderer.get_cached_text("Unlocked", renderer.font_small, (150, 255, 150), shadow=False)
                self.screen.blit(p_surf, (draw_x + 10, draw_y + 40))
                
            if not is_unlocked and can_research:
                income = me.get("last_science_income", 1) if is_tech else me.get("last_culture_income", 1)
                progress_val = res_prog if is_researching else 0
                turns_left = math.ceil((cost - progress_val) / max(1, income))
                _, t_surf = renderer.get_cached_text(f"Turns: {turns_left}", renderer.font_small, (200, 200, 255), shadow=False)
                self.screen.blit(t_surf, (draw_x + 120, draw_y + 40))
                
            unlock_text_y = draw_y + 65
            for unit in data.get("unlocked_units", []):
                _, u_surf = renderer.get_cached_text(f"+ Unit: {unit.capitalize()}", renderer.font_small, (200, 255, 200), shadow=False)
                self.screen.blit(u_surf, (draw_x + 10, unlock_text_y))
                unlock_text_y += 22
            for bldg in data.get("unlocked_buildings", []):
                _, b_surf = renderer.get_cached_text(f"+ Bldg: {bldg.capitalize()}", renderer.font_small, (200, 200, 255), shadow=False)
                self.screen.blit(b_surf, (draw_x + 10, unlock_text_y))
                unlock_text_y += 22
                
            if not is_tech:
                for policy in data.get("unlocked_policy_cards", []):
                    _, p_surf = renderer.get_cached_text(f"+ Policy: {policy.capitalize()}", renderer.font_small, (255, 200, 200), shadow=False)
                    self.screen.blit(p_surf, (draw_x + 10, unlock_text_y))
                    unlock_text_y += 22
                gov = data.get("unlocked_government")
                if gov:
                    _, g_surf = renderer.get_cached_text(f"+ Gov: {gov.capitalize()}", renderer.font_small, (255, 255, 100), shadow=False)
                    self.screen.blit(g_surf, (draw_x + 10, unlock_text_y))
                    unlock_text_y += 22

        self.screen.set_clip(None)

    def render_top_ui(self, renderer):
        app = self.app
        me = app.game_state.get("players", {}).get(app.my_id, {})
        my_color = me.get("color", (40, 40, 60))
        bg_color = (max(0, my_color[0] // 2 - 20), max(0, my_color[1] // 2 - 20), max(0, my_color[2] // 2 - 20))
        
        pygame.draw.rect(self.screen, bg_color, (0, 0, 1024, 40))
        turn = app.game_state.get("turn", 1)
        
        top_text = f"Turn: {turn}  |  Gold: {int(me.get('gold',0))}  |  Science: +{me.get('last_science_income',0)}  |  Culture: +{me.get('last_culture_income',0)}"
        _, top_surf = renderer.get_cached_text(top_text, renderer.font_small, (255, 255, 255), shadow=False)
        self.screen.blit(top_surf, (10, 10))
        
        pygame.draw.rect(self.screen, (100, 100, 100) if app.active_panel == "MAP" else (50, 50, 50), (600, 5, 100, 30))
        _, map_surf = renderer.get_cached_text("MAP", renderer.font_small, (255, 255, 255), shadow=False)
        self.screen.blit(map_surf, (630, 10))
        
        pygame.draw.rect(self.screen, (100, 100, 200) if app.active_panel == "TECH" else (50, 50, 100), (720, 5, 140, 30))
        _, t_surf = renderer.get_cached_text("TECH TREE", renderer.font_small, (255, 255, 255), shadow=False)
        self.screen.blit(t_surf, (740, 10))
        
        pygame.draw.rect(self.screen, (200, 100, 200) if app.active_panel == "CIVIC" else (100, 50, 100), (880, 5, 140, 30))
        _, c_surf = renderer.get_cached_text("CIVIC TREE", renderer.font_small, (255, 255, 255), shadow=False)
        self.screen.blit(c_surf, (900, 10))

    def render_bottom_ui(self, renderer):
        app = self.app
        ui_rect = pygame.Rect(0, 600, 1024, 168)
        pygame.draw.rect(self.screen, (40, 40, 50), ui_rect)
        pygame.draw.rect(self.screen, (100, 100, 120), ui_rect, 4)

        me = app.game_state.get("players", {}).get(app.my_id, {})

        if app.selected_unit_id:
            unit = app.game_state["units"].get(app.selected_unit_id)
            if unit:
                unit_info = GameData.UNITS.get(unit["type"], {})
                name = unit_info.get("name", "Unknown Unit")
                hp = unit.get("hp", 100)
                _, n_surf = renderer.get_cached_text(name, renderer.font_main, (255, 255, 255), shadow=False)
                self.screen.blit(n_surf, (20, 620))
                _, h_surf = renderer.get_cached_text(f"HP: {hp}/100", renderer.font_small, (200, 200, 200), shadow=False)
                self.screen.blit(h_surf, (20, 660))
                
                if not unit.get("has_moved", False):
                    _, s_surf = renderer.get_cached_text("Press SPACE to Skip Turn", renderer.font_small, (200, 200, 200), shadow=False)
                    self.screen.blit(s_surf, (20, 690))
                    
                    if unit_info.get("name") == "Settler":
                        btn_rect = pygame.Rect(250, 620, 150, 40)
                        pygame.draw.rect(self.screen, (200, 200, 200), btn_rect)
                        _, b_surf = renderer.get_cached_text("Found City (B)", renderer.font_small, (0, 0, 0), shadow=False)
                        self.screen.blit(b_surf, (260, 630))
                    elif unit_info.get("range", 0) > 0:
                        btn_rect = pygame.Rect(250, 620, 150, 40)
                        pygame.draw.rect(self.screen, (200, 50, 50) if app.target_mode else (100, 100, 100), btn_rect)
                        _, b_surf = renderer.get_cached_text("Target (R)", renderer.font_small, (255, 255, 255), shadow=False)
                        self.screen.blit(b_surf, (260, 630))
                    elif unit_info.get("name") == "Builder":
                        ux, uy = unit["x"], unit["y"]
                        tile = app.game_state["map"][uy][ux]
                        t_type = tile["terrain"]
                        has_imp = tile.get("improvement") is not None
                        charges = unit.get("charges", 0)
                        
                        _, c_surf = renderer.get_cached_text(f"Charges: {charges}", renderer.font_small, (200, 200, 200), shadow=False)
                        self.screen.blit(c_surf, (150, 660))
                        
                        if not has_imp and not tile.get("district") and charges > 0:
                            possible = []
                            my_techs = me.get("techs", [])
                            if tile.get("owner") == app.my_id:
                                for imp_id, imp_data in GameData.IMPROVEMENTS.items():
                                    if t_type in imp_data.get("valid_terrains", []) and (not imp_data.get("required_tech") or imp_data["required_tech"] in my_techs):
                                        possible.append((imp_data["name"], imp_id))
                            
                            for idx, (label, imp_id) in enumerate(possible):
                                bx = 250 + idx * 150
                                btn_rect = pygame.Rect(bx, 620, 140, 40)
                                pygame.draw.rect(self.screen, (200, 200, 200), btn_rect)
                                _, l_surf = renderer.get_cached_text(f"Build {label}", renderer.font_small, (0, 0, 0), shadow=False)
                                self.screen.blit(l_surf, (bx+5, 630))

        elif app.selected_city_id:
            city = app.game_state.get("cities", {}).get(app.selected_city_id)
            if city:
                name = city.get("name", "City")
                hp = city.get("hp", 200)
                pop = city.get("population", 1)
                food = city.get("stored_food", 0)
                food_needed = 15 + (pop * 5)
                prod = city.get("stored_production", 0)
                
                _, n_surf = renderer.get_cached_text(f"{name} (Pop {pop})", renderer.font_main, (255, 255, 255), shadow=False)
                self.screen.blit(n_surf, (20, 610))
                
                info = f"HP: {hp}/200  |  Food: {food}/{food_needed}  |  Prod: {prod}"
                _, i_surf = renderer.get_cached_text(info, renderer.font_small, (200, 200, 200), shadow=False)
                self.screen.blit(i_surf, (20, 640))
                
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
                    
                    _, p_surf = renderer.get_cached_text(f"Building: {item_name} ({turns_left} Turns)", renderer.font_small, (150, 255, 150), shadow=False)
                    self.screen.blit(p_surf, (20, 670))
                else:
                    _, p_surf = renderer.get_cached_text("Building: Nothing", renderer.font_small, (255, 150, 150), shadow=False)
                    self.screen.blit(p_surf, (20, 670))
                    
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

                old_clip = self.screen.get_clip()
                self.screen.set_clip(right_rect)
                
                _, t_surf = renderer.get_cached_text("Production", renderer.font_main, (255, 255, 255), shadow=False)
                self.screen.blit(t_surf, (834, 45 + app.city_build_scroll_y))
                
                for i, (label, cat, internal_name) in enumerate(options):
                    bx = 834
                    by = 90 + i * 50 + app.city_build_scroll_y
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
                    _, l_surf = renderer.get_cached_text(f"{label} ({t_left}T)", renderer.font_small, (255, 255, 255), shadow=False)
                    self.screen.blit(l_surf, (bx + 10, by + 10))
                    
                self.screen.set_clip(old_clip)

        if not me.get("ended_turn", False):
            my_units = [u for u in app.game_state["units"].values() if u["owner"] == app.my_id]
            units_needing_orders = sum(1 for u in my_units if not u.get("has_moved", False))
            
            my_cities = [c for c in app.game_state.get("cities", {}).values() if c["owner"] == app.my_id]
            cities_needing_orders = sum(1 for c in my_cities if c.get("production_item") is None)
            
            if cities_needing_orders > 0:
                end_btn_rect = pygame.Rect(750, 620, 260, 50)
                pygame.draw.rect(self.screen, (200, 150, 50), end_btn_rect)
                pygame.draw.rect(self.screen, (255, 200, 100), end_btn_rect, 2)
                _, b_surf = renderer.get_cached_text("CHOOSE PRODUCTION", renderer.font_small, (0, 0, 0), shadow=False)
                self.screen.blit(b_surf, (780, 635))
            elif units_needing_orders > 0:
                end_btn_rect = pygame.Rect(750, 620, 260, 50)
                pygame.draw.rect(self.screen, (80, 80, 80), end_btn_rect)
                pygame.draw.rect(self.screen, (150, 150, 150), end_btn_rect, 2)
                _, b_surf = renderer.get_cached_text(f"Unit needs orders ({units_needing_orders})", renderer.font_small, (200, 200, 200), shadow=False)
                self.screen.blit(b_surf, (770, 635))
            elif me.get("current_research") is None:
                end_btn_rect = pygame.Rect(750, 620, 260, 50)
                pygame.draw.rect(self.screen, (50, 150, 200), end_btn_rect)
                pygame.draw.rect(self.screen, (100, 200, 255), end_btn_rect, 2)
                _, b_surf = renderer.get_cached_text("CHOOSE RESEARCH", renderer.font_small, (0, 0, 0), shadow=False)
                self.screen.blit(b_surf, (790, 635))
            elif me.get("current_civic") is None:
                end_btn_rect = pygame.Rect(750, 620, 260, 50)
                pygame.draw.rect(self.screen, (200, 100, 200), end_btn_rect)
                pygame.draw.rect(self.screen, (255, 150, 255), end_btn_rect, 2)
                _, b_surf = renderer.get_cached_text("CHOOSE CIVIC", renderer.font_small, (0, 0, 0), shadow=False)
                self.screen.blit(b_surf, (810, 635))
            else:
                end_btn_rect = pygame.Rect(800, 620, 180, 50)
                pygame.draw.rect(self.screen, (50, 200, 50), end_btn_rect)
                _, b_surf = renderer.get_cached_text("END TURN ->", renderer.font_main, (0, 0, 0), shadow=False)
                self.screen.blit(b_surf, (810, 625))
        else:
            renderer.draw_text_centered("Waiting for everyone to end their turn...", 650, renderer.font_main, (200, 200, 200), shadow=True)
