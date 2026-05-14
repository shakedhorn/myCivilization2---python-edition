# CivServer/game_logic.py
import random
from CivShared.game_defs import GameData, CommandType

class GameState:
    def __init__(self, width=36, height=28):
        self.width = width
        self.height = height
        self.turn_count = 1
        self.players = {}  # {player_id: {gold: 100, science: 0, ...}}
        self.units = {}    # {unit_id: {type: 'warrior', x: 5, y: 5, owner: id, hp: 100}}
        self.cities = {}   # {city_id: {name: 'Jerusalem', x: 10, y: 10, owner: id}}
        self.map = self._generate_map()
        self.unit_counter = 0

    def _generate_map(self):
        # יצירת מפה בסיסית לפי TerrainType שהגדרת
        map_data = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                # לוגיקת יצירה בסיסית (אפשר לשכלל בהמשך)
                choice = random.choices(
                    ["grassland", "plains", "forest", "mountains", "ocean"],
                    weights=[40, 30, 15, 5, 10]
                )[0]
                row.append({"terrain": choice, "improvement": None, "owner": -1})
            map_data.append(row)
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
        # כאן יכנסו כל שאר הפקודות (BUILD_BUILDING, ADOPT_CIVIC וכו')
        return False

    def _end_turn(self, p_id):
        # לוגיקה לבדיקת האם כל השחקנים סיימו תור
        # אם כן - קידום turn_count ועיבוד ייצור בערים
        pass

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
        
        # 1. בדיקת טווח תנועה (פשוט: מרחק 1)
        if abs(unit["x"] - nx) > 1 or abs(unit["y"] - ny) > 1: return False

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
        return True

    def _found_city(self, p_id, data):
        u_id = str(data.get("unit_id"))
        unit = self.units.get(u_id)
        if unit and unit["type"] == "settler" and unit["owner"] == p_id:
            city_id = f"city_{unit['x']}_{unit['y']}"
            self.cities[city_id] = {
                "x": unit["x"], "y": unit["y"],
                "owner": p_id, "hp": 200, "has_walls": False,
                "name": f"City of Player {p_id}"
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