class Player:
    def __init__(self, player_id, name="Unknown", color=(255, 255, 255)):
        self.id = player_id
        self.name = name
        self.color = color
        self.gold = 100
        self.science = 0
        self.culture = 0
        self.techs = []
        self.civics = []
        self.current_research = None
        self.research_progress = 0
        self.current_civic = None
        self.civic_progress = 0
        self.ended_turn = False
        self.last_gold_income = 0
        self.last_science_income = 1
        self.last_culture_income = 1
        self.eliminated = False
        self.winner = None
        self.explored_tiles = []

    def to_json(self):
        return self.__dict__.copy()

    @classmethod
    def from_json(cls, data):
        p = cls(data.get("id", -1))
        for k, v in data.items():
            setattr(p, k, v)
        return p
