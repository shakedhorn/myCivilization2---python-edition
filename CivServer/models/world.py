class World:
    def __init__(self, width, height, map_data=None):
        self.width = width
        self.height = height
        self.map_data = map_data if map_data else []
        # O(1) Spatial Hashing grid: {(x, y): {"unit": uid, "city": cid}}
        self.occupants = {}

    def get_tile(self, x, y):
        if 0 <= y < self.height and 0 <= x < self.width:
            return self.map_data[y][x]
        return None

    def get_occupant(self, x, y):
        return self.occupants.get((x, y), {"unit": None, "city": None})

    def set_unit(self, x, y, uid):
        if (x, y) not in self.occupants:
            self.occupants[(x, y)] = {"unit": None, "city": None}
        self.occupants[(x, y)]["unit"] = str(uid) if uid is not None else None

    def remove_unit(self, x, y):
        if (x, y) in self.occupants:
            self.occupants[(x, y)]["unit"] = None

    def set_city(self, x, y, cid):
        if (x, y) not in self.occupants:
            self.occupants[(x, y)] = {"unit": None, "city": None}
        self.occupants[(x, y)]["city"] = str(cid) if cid is not None else None

    def remove_city(self, x, y):
        if (x, y) in self.occupants:
            self.occupants[(x, y)]["city"] = None

    def to_json(self):
        return {
            "width": self.width,
            "height": self.height,
            "map_data": self.map_data
        }

    @classmethod
    def from_json(cls, data):
        w = cls(data.get("width"), data.get("height"), data.get("map_data"))
        return w
