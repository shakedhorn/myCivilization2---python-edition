class City:
    def __init__(self, city_id, name, x, y, owner_id):
        self.id = str(city_id)
        self.name = name
        self.x = x
        self.y = y
        self.owner = owner_id
        self.hp = 200
        self.has_walls = False
        self.population = 1
        self.stored_food = 0
        self.stored_production = 0
        self.production_item = None
        self.buildings = ["cityCenter"]
        self.owned_tiles = []
        self.worked_tiles = []
        self.border_progress = 0
        self.last_production_yield = 0

    def to_json(self):
        return self.__dict__.copy()

    @classmethod
    def from_json(cls, data):
        c = cls(data.get("id"), data.get("name"), data.get("x"), data.get("y"), data.get("owner"))
        for k, v in data.items():
            if k == "owned_tiles" or k == "worked_tiles":
                setattr(c, k, [tuple(t) if isinstance(t, list) else t for t in v])
            else:
                setattr(c, k, v)
        return c
