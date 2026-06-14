# CivServer/game_logic.py
import random
from CivShared.game_defs import GameData, CommandType

class GameState:
    def __init__(self, width=50, height=36):
        self.width = width
        self.height = height
        self.turn_count = 1
        self.players = {}  # {player_id: {gold: 100, science: 0, ...}}
        self.units = {}    # {unit_id: {type: 'warrior', x: 5, y: 5, owner: id, hp: 100}}
        self.cities = {}   # {city_id: {name: 'Jerusalem', x: 10, y: 10, owner: id}}
        self.next_unit_id = 1
        self.next_city_id = 1
        self.map = self._generate_map()

    def _generate_map(self):
        # 1. Initialize world with Ocean
        grid = [[0 for _ in range(self.width)] for _ in range(self.height)]
        
        # 2. Seed and Grow continents
        num_continents = random.randint(2, 4)
        for _ in range(num_continents):
            # Pick a seed point that is far from the poles
            cx = random.randint(5, self.width - 6)
            cy = random.randint(5, self.height - 6)
            
            target_size = random.randint(150, 300)
            
            grid[cy][cx] = 1
            added = 1
            continent_tiles = [(cx, cy)]
            attempts = 0
            
            # Keep picking a random tile in the continent and trying to expand to a neighbor
            while added < target_size and attempts < target_size * 10:
                attempts += 1
                fx, fy = random.choice(continent_tiles)
                
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dx == 0 and dy == 0: continue
                        nx, ny = (fx + dx) % self.width, fy + dy
                        
                        # Leave room for poles (y=0,1 and y=height-2,height-1)
                        if 2 <= ny < self.height - 2:
                            if grid[ny][nx] == 0:
                                grid[ny][nx] = 1
                                added += 1
                                continent_tiles.append((nx, ny))
                        
        # 2.5 Smooth the continents so they aren't spiky
        for _ in range(2):
            new_grid = [[0 for _ in range(self.width)] for _ in range(self.height)]
            for y in range(2, self.height - 2):
                for x in range(self.width):
                    land_count = 0
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            nx, ny = (x + dx) % self.width, y + dy
                            if 0 <= ny < self.height:
                                land_count += grid[ny][nx]
                    # >= 4 favors thicker continents
                    new_grid[y][x] = 1 if land_count >= 4 else 0
            for y in range(2, self.height - 2):
                for x in range(self.width):
                    grid[y][x] = new_grid[y][x]

        # 3. Build the map_data and assign biomes
        map_data = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                # Hardcode poles
                if y < 2 or y >= self.height - 2:
                    terrain = "snow" if random.random() < 0.5 else "tundra"
                elif grid[y][x] == 1:
                    rand = random.random()
                    if rand < 0.10: terrain = "mountains"
                    elif rand < 0.30: terrain = "forest"
                    elif rand < 0.60: terrain = "plains"
                    else: terrain = "grassland"
                else:
                    terrain = "ocean"
                row.append({"terrain": terrain, "improvement": None, "owner": -1})
            map_data.append(row)
            
        # 4. Generate coastlines
        for y in range(self.height):
            for x in range(self.width):
                if map_data[y][x]["terrain"] == "ocean":
                    is_coast = False
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            nx, ny = (x + dx) % self.width, y + dy
                            if 0 <= ny < self.height:
                                if map_data[ny][nx]["terrain"] not in ["ocean", "coast"]:
                                    is_coast = True
                    if is_coast:
                        map_data[y][x]["terrain"] = "coast"
                        
        return map_data

    def get_sync_data(self):
        """מחזיר את כל מצב המשחק בצורה שניתן להפוך ל-JSON"""
        return {
            "turn": self.turn_count,
            "players": self.players,
            "units": self.units,
            "cities": self.cities,
            "map": self.map
        }

    def handle_command(self, player_id, cmd_type, data):
        """ה-Router המרכזי של הפקודות"""
        if cmd_type == "MOVE_UNIT":
            return self._move_unit(player_id, data)
        elif cmd_type == "FOUND_CITY":
            return self._found_city(player_id, data)
        elif cmd_type == "END_TURN":
            return self._end_turn(player_id)
        elif cmd_type == "SKIP_UNIT_TURN":
            return self._skip_unit_turn(player_id, data)
        elif cmd_type == "CHANGE_PRODUCTION":
            return self._change_production(player_id, data)
        elif cmd_type == "BUILD_IMPROVEMENT":
            return self._build_improvement(player_id, data)
        # כאן יכנסו כל שאר הפקודות (BUILD_BUILDING, ADOPT_CIVIC וכו')
        return False

    def _build_improvement(self, p_id, data):
        u_id = str(data.get("unit_id"))
        imp_type = data.get("improvement")
        unit = self.units.get(u_id)
        if not unit or unit["owner"] != p_id or unit["type"] != "builder": return False
        
        if unit.get("charges", 0) <= 0: return False
        
        player = self.players.get(p_id)
        imp_data = GameData.IMPROVEMENTS.get(imp_type, {})
        req_tech = imp_data.get("required_tech")
        
        if req_tech and req_tech not in player.get("techs", []):
            return False
            
        x, y = unit["x"], unit["y"]
        tile = self.map[y][x]
        if tile.get("improvement"): return False
        
        tile["improvement"] = imp_type
        unit["charges"] -= 1
        unit["has_moved"] = True
        
        if unit["charges"] <= 0:
            del self.units[u_id]
            
        return True

    def _change_production(self, p_id, data):
        c_id = data.get("city_id")
        if c_id not in self.cities: return False
        city = self.cities[c_id]
        if city["owner"] != p_id: return False
        
        category = data.get("category")
        item_name = data.get("item")
        
        city["production_item"] = {"category": category, "name": item_name}
        return True

    def _skip_unit_turn(self, p_id, data):
        u_id = str(data.get("unit_id"))
        unit = self.units.get(u_id)
        if unit and unit["owner"] == p_id and not unit.get("has_moved", False):
            unit["has_moved"] = True
            return True
        return False

    def _end_turn(self, p_id):
        if p_id in self.players:
            self.players[p_id]["ended_turn"] = True
            
            # בדיקה האם כולם סיימו
            if all(p.get("ended_turn", False) for p in self.players.values()):
                self._next_turn()
            return True
        return False
        
    def _calculate_city_yields(self, city):
        food, prod, gold, science, culture = 0, 0, 0, 0, 0
        food += 2
        prod += 2
        
        # Auto-assign worked tiles based on population and yields
        # Calculate yield for each owned tile
        tile_yields = []
        for wx, wy in city.get("owned_tiles", []):
            if 0 <= wy < self.height and 0 <= wx < self.width:
                t_type = self.map[wy][wx]["terrain"]
                imp_type = self.map[wy][wx].get("improvement")
                
                t_stats = GameData.TERRAIN.get(t_type, {})
                f = t_stats.get("food_yield", 0)
                p = t_stats.get("production_yield", 0)
                g = t_stats.get("gold_yield", 0)
                
                if imp_type:
                    i_stats = GameData.IMPROVEMENTS.get(imp_type, {})
                    f += i_stats.get("food_bonus", 0)
                    p += i_stats.get("production_bonus", 0)
                    g += i_stats.get("gold_bonus", 0)
                
                total_val = f * 2 + p * 2 + g
                tile_yields.append((total_val, f, p, g, wx, wy))
                
        # Sort and pick top tiles up to population limit
        tile_yields.sort(reverse=True, key=lambda x: x[0])
        pop = city.get("population", 1)
        worked = tile_yields[:pop]
        
        city["worked_tiles"] = [(x[4], x[5]) for x in worked]
        
        for val, f, p, g, wx, wy in worked:
            food += f
            prod += p
            gold += g
                
        for b in city.get("buildings", []):
            b_stats = GameData.BUILDINGS.get(b, {})
            prod += b_stats.get("production_bonus", 0)
            science += b_stats.get("science_bonus", 0)
            culture += b_stats.get("culture_bonus", 0)
            
        return {"food": food, "production": prod, "gold": gold, "science": science, "culture": culture}

    def _next_turn(self):
        self.turn_count += 1
        for p_id, p in self.players.items():
            p["ended_turn"] = False
            p["last_gold_income"] = 0
            p["last_science_income"] = 1
            p["last_culture_income"] = 1
            
        for c_id, city in self.cities.items():
            yields = self._calculate_city_yields(city)
            city["last_production_yield"] = yields["production"]
            c_owner = city["owner"]
            if c_owner in self.players:
                self.players[c_owner]["last_gold_income"] += yields["gold"]
                self.players[c_owner]["last_science_income"] += yields["science"]
                self.players[c_owner]["last_culture_income"] += yields["culture"]
                
            city["stored_food"] = city.get("stored_food", 0) + yields["food"]
            food_needed = 15 + (city.get("population", 1) * 5)
            if city["stored_food"] >= food_needed:
                city["population"] += 1
                city["stored_food"] -= food_needed
                
            # Border Expansion Logic
            city["border_progress"] = city.get("border_progress", 0) + yields["culture"]
            if city["border_progress"] >= 25:
                # Find adjacent unowned tiles within radius 3
                cx, cy = city["x"], city["y"]
                candidates = []
                owned_set = set(city.get("owned_tiles", []))
                
                for ox, oy in owned_set:
                    for dy in [-1, 0, 1]:
                        for dx in [-1, 0, 1]:
                            nx, ny = (ox + dx) % self.width, oy + dy
                            if 0 <= ny < self.height and (nx, ny) not in owned_set:
                                # Ensure distance <= 3
                                dist_x = min((nx - cx) % self.width, (cx - nx) % self.width)
                                dist_y = abs(ny - cy)
                                if dist_x <= 3 and dist_y <= 3:
                                    if self.map[ny][nx].get("owner") == -1:
                                        candidates.append((nx, ny))
                
                if candidates:
                    chosen_x, chosen_y = random.choice(candidates)
                    city["owned_tiles"].append((chosen_x, chosen_y))
                    self.map[chosen_y][chosen_x]["owner"] = c_owner
                    city["border_progress"] -= 25
                    
            city["stored_production"] = city.get("stored_production", 0) + yields["production"]
            prod_item = city.get("production_item")
            if prod_item:
                cost = 9999
                if prod_item["category"] == "unit":
                    cost = GameData.UNITS.get(prod_item["name"], {}).get("production_cost", 9999)
                elif prod_item["category"] == "building":
                    cost = GameData.BUILDINGS.get(prod_item["name"], {}).get("production_cost", 9999)
                    
                if city["stored_production"] >= cost:
                    city["stored_production"] -= cost
                    if prod_item["category"] == "unit":
                        unit_type = prod_item["name"]
                        new_unit = {
                            "type": unit_type, "owner": c_owner,
                            "x": city["x"], "y": city["y"], "hp": 100, "has_moved": False
                        }
                        if unit_type == "builder":
                            new_unit["charges"] = 3
                        self.units[str(self.next_unit_id)] = new_unit
                        self.next_unit_id += 1
                    elif prod_item["category"] == "building":
                        if prod_item["name"] not in city.get("buildings", []):
                            city.setdefault("buildings", []).append(prod_item["name"])
                    city["production_item"] = None
                    
        for p_id, p in self.players.items():
            p["gold"] += p.get("last_gold_income", 0)
            p["science"] += p.get("last_science_income", 0)
            p["culture"] += p.get("last_culture_income", 0)
            
        for u in self.units.values():
            u["has_moved"] = False

    def _get_unit_at(self, x, y):
        for uid, unit in self.units.items():
            if unit["x"] == x and unit["y"] == y:
                return uid, unit
        return None, None

    def _move_unit(self, p_id, data):
        u_id = str(data.get("unit_id"))
        nx, ny = data.get("nx"), data.get("ny")
        
        if u_id not in self.units: return False
        unit = self.units[u_id]
        if unit["owner"] != p_id: return False
        if unit.get("has_moved", False): return False
        
        # 1. בדיקת טווח תנועה (פשוט: מרחק 1) (with horizontal wrap)
        dx = abs(unit["x"] - nx)
        if dx > self.width / 2: dx = self.width - dx
        
        if dx > 1 or abs(unit["y"] - ny) > 1: return False

        # Ensure ny is valid (just in case)
        if not (0 <= ny < self.height): return False
        target_terrain = self.map[ny][nx]["terrain"]
        stats = GameData.UNITS[unit["type"]]

        # 2. בדיקת מים/יבשה
        is_water = GameData.TERRAIN[target_terrain]["isWater"]
        if is_water and not stats["isNaval"]: return False
        if not is_water and stats["isNaval"]: return False
        if target_terrain == "mountains": return False

        # 3. בדיקה אם יש שם יחידה אחרת
        target_uid, target_unit = self._get_unit_at(nx, ny)
        
        if target_unit:
            if target_unit["owner"] == p_id: return False # אי אפשר לעמוד שניים על אותו משבצת
            
            # לוגיקת קרב / כיבוש
            target_stats = GameData.UNITS[target_unit["type"]]
            if target_stats["melee"] == 0: # יחידה אזרחית - כיבוש
                target_unit["owner"] = p_id
                return True
            else: # קרב
                return self._resolve_melee_combat(u_id, target_uid)

        # 4. בדיקת עיר
        # (כאן תוסיף בדיקה אם יש עיר ב-nx,ny ותפעיל לוגיקת מצור)

        # תנועה רגילה
        unit["x"], unit["y"] = nx, ny
        unit["has_moved"] = True
        return True

    def _found_city(self, p_id, data):
        u_id = str(data.get("unit_id"))
        unit = self.units.get(u_id)
        if unit and unit["type"] == "settler" and unit["owner"] == p_id:
            city_id = f"city_{unit['x']}_{unit['y']}"
            # Claim 3x3 starting territory
            owned_tiles = []
            cx, cy = unit["x"], unit["y"]
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    nx, ny = (cx + dx) % self.width, cy + dy
                    if 0 <= ny < self.height:
                        if self.map[ny][nx].get("owner") == -1: # Only claim unowned
                            self.map[ny][nx]["owner"] = p_id
                            owned_tiles.append((nx, ny))
            
            self.cities[city_id] = {
                "x": cx, "y": cy,
                "owner": p_id, "hp": 200, "has_walls": False,
                "name": f"City of Player {p_id}",
                "population": 1,
                "stored_food": 0,
                "stored_production": 0,
                "production_item": None,
                "buildings": ["cityCenter"],
                "owned_tiles": owned_tiles,
                "worked_tiles": [],
                "border_progress": 0
            }
            del self.units[u_id] # מחיקת המתיישב
            return True
        return False
    
    def _resolve_melee_combat(self, attacker_id, defender_id):
        att = self.units[attacker_id]
        defen = self.units[defender_id]
        
        att_stats = GameData.UNITS[att["type"]]
        def_stats = GameData.UNITS[defen["type"]]
        
        # חישוב נזק פשוט (אפשר לשכלל לפי הנוסחה של Civ)
        # נניח שכל יחידה מתחילה עם 100 HP (צריך להוסיף ל-init של היחידה)
        damage_to_def = max(10, att_stats["melee"] - (def_stats["melee"] // 2))
        damage_to_att = max(5, def_stats["melee"] - (att_stats["melee"] // 2))
        
        defen["hp"] = defen.get("hp", 100) - damage_to_def
        att["hp"] = att.get("hp", 100) - damage_to_att
        
        # בדיקת מוות
        if defen["hp"] <= 0:
            del self.units[defender_id]
            # אם המגן מת, התוקף תופס את המשבצת
            att["x"], att["y"] = defen["x"], defen["y"]
        
        if att["hp"] <= 0:
            if attacker_id in self.units: del self.units[attacker_id]
            
        return True