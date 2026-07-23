class Unit:
    def __init__(self, unit_id, unit_type, x, y, owner_id, hp=100):
        self.id = str(unit_id)
        self.type = unit_type
        self.x = x
        self.y = y
        self.owner = owner_id
        self.hp = hp
        self.has_moved = False
        self.charges = 3 if unit_type == "builder" else 0

    def to_json(self):
        return self.__dict__.copy()

    @classmethod
    def from_json(cls, data):
        u = cls(data.get("id"), data.get("type"), data.get("x"), data.get("y"), data.get("owner"), data.get("hp", 100))
        for k, v in data.items():
            setattr(u, k, v)
        return u
