# CivShared/game_defs.py
from enum import Enum, auto

class CommandType(Enum):
    MOVE_UNIT = auto()
    BUILD_UNIT = auto()
    RESEARCH_TECH = auto()
    END_TURN = auto()
    UPDATE_ALL = auto()
    FOUND_CITY = auto()
    BUILD_BUILDING = auto()
    ADOPT_CIVIC = auto()
    ADOPT_POLICY = auto()
    BUILD_IMPROVEMENT = auto()

class GameData:
    UNITS = {
        # ===== MELEE =====
        "warrior": { "gold_cost": 0, "production_cost": 40, "movement": 2, "melee": 20, "sight": 2, "name": "Warrior", "type": "Melee", "range": 0, "UpgradeTo": "swordsman", "requiredTech": None, "isNaval": False },
        "swordsman": { "gold_cost": 0, "production_cost": 90, "movement": 2, "melee": 36, "sight": 2, "name": "Swordsman", "type": "Melee", "range": 0, "UpgradeTo": "musketman", "requiredTech": "ironWorking", "isNaval": False },
        "musketman": { "gold_cost": 0, "production_cost": 240, "movement": 2, "melee": 55, "sight": 2, "name": "Musketman", "type": "Melee", "range": 0, "UpgradeTo": "infantry", "requiredTech": "gunpowder", "isNaval": False },
        "infantry": { "gold_cost": 0, "production_cost": 430, "movement": 2, "melee": 70, "sight": 2, "name": "Infantry", "type": "Melee", "range": 0, "UpgradeTo": "mechanizedInfantry", "requiredTech": "replaceableParts", "isNaval": False },
        "mechanizedInfantry": { "gold_cost": 0, "production_cost": 680, "movement": 3, "melee": 85, "sight": 3, "name": "Mechanized Infantry", "type": "Melee", "range": 0, "UpgradeTo": None, "requiredTech": None, "isNaval": False },
        # ===== RANGED =====
        "slinger": { "gold_cost": 0, "production_cost": 35, "movement": 2, "melee": 5, "sight": 2, "name": "Slinger", "type": "Ranged", "range": 1, "UpgradeTo": "archer", "requiredTech": None, "isNaval": False },
        "archer": { "gold_cost": 0, "production_cost": 60, "movement": 2, "melee": 15, "sight": 2, "name": "Archer", "type": "Ranged", "range": 2, "UpgradeTo": "crossbowman", "requiredTech": "archery", "isNaval": False },
        "crossbowman": { "gold_cost": 0, "production_cost": 180, "movement": 2, "melee": 30, "sight": 2, "name": "Crossbowman", "type": "Ranged", "range": 2, "UpgradeTo": "fieldCannon", "requiredTech": "machinery", "isNaval": False },
        "fieldCannon": { "gold_cost": 0, "production_cost": 330, "movement": 2, "melee": 60, "sight": 2, "name": "Field Cannon", "type": "Ranged", "range": 2, "UpgradeTo": "machineGun", "requiredTech": "ballistics", "isNaval": False },
        "machineGun": { "gold_cost": 0, "production_cost": 600, "movement": 2, "melee": 75, "sight": 2, "name": "Machine Gun", "type": "Ranged", "range": 2, "UpgradeTo": None, "requiredTech": "advancedBallistics", "isNaval": False },
        # ===== CAVALRY =====
        "horseman": { "gold_cost": 0, "production_cost": 80, "movement": 4, "melee": 36, "sight": 2, "name": "Horseman", "type": "Cavalry", "range": 0, "UpgradeTo": "knight", "requiredTech": "horsebackRiding", "isNaval": False },
        "knight": { "gold_cost": 0, "production_cost": 180, "movement": 4, "melee": 48, "sight": 2, "name": "Knight", "type": "Cavalry", "range": 0, "UpgradeTo": "cavalry", "requiredTech": "stirrups", "isNaval": False },
        "cavalry": { "gold_cost": 0, "production_cost": 330, "movement": 5, "melee": 62, "sight": 3, "name": "Cavalry", "type": "Cavalry", "range": 0, "UpgradeTo": "helicopter", "requiredTech": "militaryScience", "isNaval": False },
        "helicopter": { "gold_cost": 0, "production_cost": 650, "movement": 6, "melee": 86, "sight": 3, "name": "Helicopter", "type": "Cavalry", "range": 0, "UpgradeTo": None, "requiredTech": "advancedFlight", "isNaval": False },
        # ===== SIEGE =====
        "catapult": { "gold_cost": 0, "production_cost": 120, "movement": 2, "melee": 25, "sight": 2, "name": "Catapult", "type": "Siege", "range": 2, "UpgradeTo": "trebuchet", "requiredTech": "engineering", "isNaval": False },
        "trebuchet": { "gold_cost": 0, "production_cost": 200, "movement": 2, "melee": 35, "sight": 2, "name": "Trebuchet", "type": "Siege", "range": 2, "UpgradeTo": "bombard", "requiredTech": "militaryEngineering", "isNaval": False },
        "bombard": { "gold_cost": 0, "production_cost": 330, "movement": 2, "melee": 55, "sight": 2, "name": "Bombard", "type": "Siege", "range": 2, "UpgradeTo": "artillery", "requiredTech": "gunpowder", "isNaval": False },
        "artillery": { "gold_cost": 0, "production_cost": 480, "movement": 2, "melee": 70, "sight": 2, "name": "Artillery", "type": "Siege", "range": 3, "UpgradeTo": "rocketArtillery", "requiredTech": "steel", "isNaval": False },
        "rocketArtillery": { "gold_cost": 0, "production_cost": 680, "movement": 3, "melee": 85, "sight": 3, "name": "Rocket Artillery", "type": "Siege", "range": 3, "UpgradeTo": None, "requiredTech": "rocketry", "isNaval": False },
        # ===== ANTI-CAV =====
        "spearman": { "gold_cost": 0, "production_cost": 65, "movement": 2, "melee": 25, "sight": 2, "name": "Spearman", "type": "AntiCav", "range": 0, "UpgradeTo": "pikeman", "requiredTech": "bronzeWorking", "isNaval": False },
        "pikeman": { "gold_cost": 0, "production_cost": 180, "movement": 2, "melee": 41, "sight": 2, "name": "Pikeman", "type": "AntiCav", "range": 0, "UpgradeTo": "pikeAndShot", "requiredTech": "militaryTactics", "isNaval": False },
        "pikeAndShot": { "gold_cost": 0, "production_cost": 250, "movement": 2, "melee": 55, "sight": 2, "name": "Pike and Shot", "type": "AntiCav", "range": 0, "UpgradeTo": "ATcrew", "requiredTech": "gunpowder", "isNaval": False },
        "ATcrew": { "gold_cost": 0, "production_cost": 430, "movement": 2, "melee": 70, "sight": 2, "name": "AT Crew", "type": "AntiCav", "range": 0, "UpgradeTo": "modernAT", "requiredTech": "replaceableParts", "isNaval": False },
        "modernAT": { "gold_cost": 0, "production_cost": 650, "movement": 3, "melee": 85, "sight": 3, "name": "Modern AT", "type": "AntiCav", "range": 0, "UpgradeTo": None, "requiredTech": "composites", "isNaval": False },
        # ===== NAVAL MELEE =====
        "galley": { "gold_cost": 0, "production_cost": 65, "movement": 3, "melee": 25, "sight": 2, "name": "Galley", "type": "Naval", "range": 0, "UpgradeTo": "quadrireme", "requiredTech": "sailing", "isNaval": True },
        "quadrireme": { "gold_cost": 0, "production_cost": 120, "movement": 3, "melee": 30, "sight": 2, "name": "Quadrireme", "type": "Naval", "range": 0, "UpgradeTo": "caravel", "requiredTech": "shipBuilding", "isNaval": True },
        "caravel": { "gold_cost": 0, "production_cost": 240, "movement": 4, "melee": 50, "sight": 3, "name": "Caravel", "type": "Naval", "range": 0, "UpgradeTo": "ironclad", "requiredTech": "cartography", "isNaval": True },
        "ironclad": { "gold_cost": 0, "production_cost": 430, "movement": 5, "melee": 65, "sight": 3, "name": "Ironclad", "type": "Naval", "range": 0, "UpgradeTo": "destroyer", "requiredTech": "steamPower", "isNaval": True },
        "destroyer": { "gold_cost": 0, "production_cost": 680, "movement": 6, "melee": 85, "sight": 3, "name": "Destroyer", "type": "Naval", "range": 0, "UpgradeTo": None, "requiredTech": "radio", "isNaval": True },
        # ===== NAVAL RANGED =====
        "frigate": { "gold_cost": 0, "production_cost": 280, "movement": 4, "melee": 55, "sight": 3, "name": "Frigate", "type": "Naval", "range": 2, "UpgradeTo": "battleship", "requiredTech": "squareRigging", "isNaval": True },
        "battleship": { "gold_cost": 0, "production_cost": 430, "movement": 5, "melee": 70, "sight": 3, "name": "Battleship", "type": "Naval", "range": 2, "UpgradeTo": "missileCruiser", "requiredTech": "steel", "isNaval": True },
        "missileCruiser": { "gold_cost": 0, "production_cost": 680, "movement": 6, "melee": 85, "sight": 3, "name": "Missile Cruiser", "type": "Naval", "range": 2, "UpgradeTo": None, "requiredTech": "guidanceSystems", "isNaval": True },
        # ===== SUPPORT / CIVILIAN =====
        "settler": { "gold_cost": 0, "production_cost": 80, "movement": 2, "melee": 0, "sight": 2, "name": "Settler", "type": "Civilian", "range": 0, "UpgradeTo": None, "requiredTech": None, "isNaval": False },
        "builder": { "gold_cost": 0, "production_cost": 50, "movement": 2, "melee": 0, "sight": 2, "name": "Builder", "type": "Civilian", "range": 0, "UpgradeTo": None, "requiredTech": None, "isNaval": False },
        "scout": { "gold_cost": 0, "production_cost": 30, "movement": 3, "melee": 10, "sight": 3, "name": "Scout", "type": "Recon", "range": 0, "UpgradeTo": "skirmisher", "requiredTech": None, "isNaval": False },
        "skirmisher": { "gold_cost": 0, "production_cost": 150, "movement": 3, "melee": 20, "sight": 3, "name": "Skirmisher", "type": "Recon", "range": 0, "UpgradeTo": "ranger", "requiredTech": "machinery", "isNaval": False },
        "ranger": { "gold_cost": 0, "production_cost": 300, "movement": 3, "melee": 40, "sight": 3, "name": "Ranger", "type": "Recon", "range": 0, "UpgradeTo": "specOps", "requiredTech": "rifling", "isNaval": False },
        "specOps": { "gold_cost": 0, "production_cost": 500, "movement": 4, "melee": 60, "sight": 3, "name": "Spec Ops", "type": "Recon", "range": 0, "UpgradeTo": None, "requiredTech": "syntheticMaterials", "isNaval": False },
        # ===== HEAVY =====
        "tank": { "gold_cost": 0, "production_cost": 480, "movement": 4, "melee": 80, "sight": 3, "name": "Tank", "type": "Armor", "range": 0, "UpgradeTo": "modernArmor", "requiredTech": "combustion", "isNaval": False },
        "modernArmor": { "gold_cost": 0, "production_cost": 680, "movement": 5, "melee": 95, "sight": 3, "name": "Modern Armor", "type": "Armor", "range": 0, "UpgradeTo": None, "requiredTech": "composites", "isNaval": False }
    }

    BUILDINGS = {
        # ===== CITY CENTER =====
        "monument": { "name": "Monument", "production_cost": 60, "requiredTech": None, "requiredCivic": None, "science_bonus": 0, "culture_bonus": 2, "production_bonus": 0, "requiresTile": False, "requiredBefore": "cityCenter"},
        "granary": { "name": "Granary", "production_cost": 65, "requiredTech": "pottery", "requiredCivic": None, "science_bonus": 0, "culture_bonus": 0, "production_bonus": 0, "requiresTile": False, "requiredBefore": None},
        "waterMill": { "name": "Water Mill", "production_cost": 80, "requiredTech": "wheel", "requiredCivic": None, "science_bonus": 0, "culture_bonus": 0, "production_bonus": 1, "requiresTile": True, "requiredBefore": None},
        "walls": { "name": "Walls", "production_cost": 150, "requiredTech": "masonry", "requiredCivic": None, "science_bonus": 0, "culture_bonus": 1, "production_bonus": 0, "requiresTile": False, "requiredBefore": None},
        # ===== CAMPUS =====
        "library": { "name": "Library", "production_cost": 80, "requiredTech": "writing", "requiredCivic": None, "science_bonus": 2, "culture_bonus": 0, "production_bonus": 0, "requiresTile": False, "requiredBefore": "campus" },
        "university": { "name": "University", "production_cost": 200, "requiredTech": "education", "requiredCivic": None, "science_bonus": 4, "culture_bonus": 0, "production_bonus": 0, "requiresTile": False, "requiredBefore": "library" },
        "researchLab": { "name": "Research Lab", "production_cost": 300, "requiredTech": "chemistry", "requiredCivic": None, "science_bonus": 5, "culture_bonus": 0, "production_bonus": 0, "requiresTile": False, "requiredBefore": "university" },
        # ===== COMMERCIAL HUB =====
        "market": { "name": "Market", "production_cost": 120, "requiredTech": "currency", "requiredCivic": None, "science_bonus": 0, "culture_bonus": 0, "production_bonus": 0, "requiresTile": False, "requiredBefore": "commercialHub" },
        "bank": { "name": "Bank", "production_cost": 220, "requiredTech": "banking", "requiredCivic": None, "science_bonus": 0, "culture_bonus": 0, "production_bonus": 0, "requiresTile": False, "requiredBefore": "market" },
        "stockExchange": { "name": "Stock Exchange", "production_cost": 350, "requiredTech": "economics", "requiredCivic": None, "science_bonus": 0, "culture_bonus": 0, "production_bonus": 0, "requiresTile": False, "requiredBefore": "bank" },
        # ===== INDUSTRIAL ZONE =====
        "workshop": { "name": "Workshop", "production_cost": 195, "requiredTech": "apprenticeship", "requiredCivic": None, "science_bonus": 0, "culture_bonus": 0, "production_bonus": 2, "requiresTile": False, "requiredBefore": "industrialZone" },
        "factory": { "name": "Factory", "production_cost": 330, "requiredTech": "industrialization", "requiredCivic": None, "science_bonus": 0, "culture_bonus": 0, "production_bonus": 3, "requiresTile": False, "requiredBefore": "workshop" },
        "powerPlant": { "name": "Power Plant", "production_cost": 480, "requiredTech": "electricity", "requiredCivic": None, "science_bonus": 0, "culture_bonus": 0, "production_bonus": 4, "requiresTile": False, "requiredBefore": "factory" },
        # ===== HOLY SITE =====
        "shrine": { "name": "Shrine", "production_cost": 70, "requiredTech": "astrology", "requiredCivic": None, "science_bonus": 0, "culture_bonus": 2, "production_bonus": 0, "requiresTile": False, "requiredBefore": "holySite" },
        "temple": { "name": "Temple", "production_cost": 120, "requiredTech": None, "requiredCivic": "theology", "science_bonus": 0, "culture_bonus": 4, "production_bonus": 0, "requiresTile": False, "requiredBefore": "shrine" },
        # ===== THEATER SQUARE =====
        "amphitheater": { "name": "Amphitheater", "production_cost": 150, "requiredTech": None, "requiredCivic": "dramaAndPoetry", "science_bonus": 0, "culture_bonus": 2, "production_bonus": 0, "requiresTile": False, "requiredBefore": "theaterSquare" },
        "museumArt": { "name": "Art Museum", "production_cost": 220, "requiredTech": None, "requiredCivic": "humanism", "science_bonus": 0, "culture_bonus": 3, "production_bonus": 0, "requiresTile": False, "requiredBefore": "amphitheater" },
        "museumArtifact": { "name": "Archaeological Museum", "production_cost": 220, "requiredTech": None, "requiredCivic": "humanism", "science_bonus": 0, "culture_bonus": 3, "production_bonus": 0, "requiresTile": False, "requiredBefore": "amphitheater" },
        "broadcastCenter": { "name": "Broadcast Center", "production_cost": 300, "requiredTech": "radio", "requiredCivic": None, "science_bonus": 0, "culture_bonus": 4, "production_bonus": 0, "requiresTile": False, "requiredBefore": "amphitheater" },
        # ===== ENTERTAINMENT =====
        "arena": { "name": "Arena", "production_cost": 150, "requiredTech": None, "requiredCivic": "gamesAndRecreation", "science_bonus": 0, "culture_bonus": 1, "production_bonus": 0, "requiresTile": False, "requiredBefore": "entertainmentComplex" },
        "zoo": { "name": "Zoo", "production_cost": 250, "requiredTech": None, "requiredCivic": "naturalHistory", "science_bonus": 0, "culture_bonus": 2, "production_bonus": 0, "requiresTile": False, "requiredBefore": "arena" },
        "stadium": { "name": "Stadium", "production_cost": 400, "requiredTech": None, "requiredCivic": "professionalSports", "science_bonus": 0, "culture_bonus": 3, "production_bonus": 0, "requiresTile": False, "requiredBefore": "zoo" },
        # ===== ENCAMPMENT =====
        "barracks": { "name": "Barracks", "production_cost": 80, "requiredTech": "bronzeWorking", "requiredCivic": None, "science_bonus": 0, "culture_bonus": 0, "production_bonus": 1, "requiresTile": False, "requiredBefore": "encampment" },
        "stable": { "name": "Stable", "production_cost": 80, "requiredTech": "horsebackRiding", "requiredCivic": None, "science_bonus": 0, "culture_bonus": 0, "production_bonus": 1, "requiresTile": False, "requiredBefore": "encampment" },
        "armory": { "name": "Armory", "production_cost": 195, "requiredTech": "militaryEngineering", "requiredCivic": None, "science_bonus": 0, "culture_bonus": 0, "production_bonus": 2, "requiresTile": False, "requiredBefore": "barracks" },
        "militaryAcademy": { "name": "Military Academy", "production_cost": 330, "requiredTech": "militaryScience", "requiredCivic": None, "science_bonus": 0, "culture_bonus": 0, "production_bonus": 3, "requiresTile": False, "requiredBefore": "armory" },
        # ===== HARBOR =====
        "lighthouse": { "name": "Lighthouse", "production_cost": 120, "requiredTech": "celestialNavigation", "requiredCivic": None, "science_bonus": 0, "culture_bonus": 0, "production_bonus": 1, "requiresTile": False, "requiredBefore": "harbor" },
        "shipyard": { "name": "Shipyard", "production_cost": 290, "requiredTech": "massProduction", "requiredCivic": None, "science_bonus": 0, "culture_bonus": 0, "production_bonus": 3, "requiresTile": False, "requiredBefore": "lighthouse" },
        "seaport": { "name": "Seaport", "production_cost": 400, "requiredTech": "steamPower", "requiredCivic": None, "science_bonus": 0, "culture_bonus": 0, "production_bonus": 4, "requiresTile": False, "requiredBefore": "shipyard" },
        # ===== DISTRICTS =====
        "cityCenter": { "name": "City Center", "production_cost": 0, "requiredTech": None, "requiredCivic": None, "science_bonus": 0, "culture_bonus": 0, "production_bonus": 0, "requiresTile": False, "requiredBefore": None },
        "campus": { "name": "Campus", "production_cost": 60, "requiredTech": "writing", "requiredCivic": None, "science_bonus": 1, "culture_bonus": 0, "production_bonus": 0, "requiresTile": False, "requiredBefore": None },
        "commercialHub": { "name": "Commercial Hub", "production_cost": 60, "requiredTech": "currency", "requiredCivic": None, "science_bonus": 0, "culture_bonus": 0, "production_bonus": 0, "requiresTile": False, "requiredBefore": None },
        "industrialZone": { "name": "Industrial Zone", "production_cost": 60, "requiredTech": "apprenticeship", "requiredCivic": None, "science_bonus": 0, "culture_bonus": 0, "production_bonus": 1, "requiresTile": False, "requiredBefore": None },
        "holySite": { "name": "Holy Site", "production_cost": 60, "requiredTech": "astrology", "requiredCivic": None, "science_bonus": 0, "culture_bonus": 1, "production_bonus": 0, "requiresTile": False, "requiredBefore": None },
        "theaterSquare": { "name": "Theater Square", "production_cost": 60, "requiredTech": None, "requiredCivic": "dramaAndPoetry", "science_bonus": 0, "culture_bonus": 1, "production_bonus": 0, "requiresTile": False, "requiredBefore": None },
        "encampment": { "name": "Encampment", "production_cost": 60, "requiredTech": "bronzeWorking", "requiredCivic": None, "science_bonus": 0, "culture_bonus": 0, "production_bonus": 1, "requiresTile": False, "requiredBefore": None },
        "harbor": { "name": "Harbor", "production_cost": 60, "requiredTech": "sailing", "requiredCivic": None, "science_bonus": 0, "culture_bonus": 0, "production_bonus": 1, "requiresTile": False, "requiredBefore": None },
        "entertainmentComplex": { "name": "Entertainment Complex", "production_cost": 60, "requiredTech": None, "requiredCivic": "gamesAndRecreation", "science_bonus": 0, "culture_bonus": 1, "production_bonus": 0, "requiresTile": False, "requiredBefore": None },
        "neighborhood": { "name": "Neighborhood", "production_cost": 120, "requiredTech": None, "requiredCivic": "urbanization", "science_bonus": 0, "culture_bonus": 0, "production_bonus": 0, "requiresTile": False, "requiredBefore": None }
    }

    GOVERNMENTS = {
        "chiefdom": { "name": "Chiefdom", "science_bonus": 0, "culture_bonus": 0, "production_bonus": 0, "military_slot": 1, "economic_slot": 1, "diplomatic_slot": 0, "wildcard_slot": 0, "requiredCivic": "codeOfLaws" },
        "autocracy": { "name": "Autocracy", "science_bonus": 10, "culture_bonus": 0, "production_bonus": 10, "military_slot": 2, "economic_slot": 1, "diplomatic_slot": 0, "wildcard_slot": 0, "requiredCivic": "politicalPhilosophy" },
        "oligarchy": { "name": "Oligarchy", "science_bonus": 0, "culture_bonus": 0, "production_bonus": 10, "military_slot": 2, "economic_slot": 1, "diplomatic_slot": 0, "wildcard_slot": 0, "requiredCivic": "politicalPhilosophy" },
        "classicalRepublic": { "name": "Classical Republic", "science_bonus": 0, "culture_bonus": 10, "production_bonus": 0, "military_slot": 0, "economic_slot": 2, "diplomatic_slot": 1, "wildcard_slot": 0, "requiredCivic": "politicalPhilosophy" },
        "monarchy": { "name": "Monarchy", "science_bonus": 0, "culture_bonus": 0, "production_bonus": 10, "military_slot": 3, "economic_slot": 1, "diplomatic_slot": 1, "wildcard_slot": 0, "requiredCivic": "divineRight" },
        "theocracy": { "name": "Theocracy", "science_bonus": 0, "culture_bonus": 10, "production_bonus": 0, "military_slot": 2, "economic_slot": 2, "diplomatic_slot": 0, "wildcard_slot": 0, "requiredCivic": "reformedChurch" },
        "merchantRepublic": { "name": "Merchant Republic", "science_bonus": 10, "culture_bonus": 10, "production_bonus": 0, "military_slot": 1, "economic_slot": 2, "diplomatic_slot": 1, "wildcard_slot": 1, "requiredCivic": "exploration" },
        "democracy": { "name": "Democracy", "science_bonus": 10, "culture_bonus": 10, "production_bonus": 0, "military_slot": 1, "economic_slot": 3, "diplomatic_slot": 2, "wildcard_slot": 1, "requiredCivic": "suffrage" },
        "fascism": { "name": "Fascism", "science_bonus": 0, "culture_bonus": 0, "production_bonus": 20, "military_slot": 4, "economic_slot": 1, "diplomatic_slot": 0, "wildcard_slot": 1, "requiredCivic": "totalitarianism" },
        "communism": { "name": "Communism", "science_bonus": 10, "culture_bonus": 0, "production_bonus": 10, "military_slot": 3, "economic_slot": 3, "diplomatic_slot": 0, "wildcard_slot": 1, "requiredCivic": "classStruggle" }
    }
    
    TECHS = {
        # ===== ANCIENT =====
        "pottery": { "name": "Pottery", "science_cost": 25, "required_techs": [], "unloced_units": [], "unlocked_buildings": ["granary"] },
        "animalHusbandry": { "name": "Animal Husbandry", "science_cost": 25, "required_techs": [], "unloced_units": [], "unlocked_buildings": [] },
        "mining": { "name": "Mining", "science_cost": 25, "required_techs": [], "unloced_units": [], "unlocked_buildings": [] },
        "sailing": { "name": "Sailing", "science_cost": 25, "required_techs": [], "unloced_units": ["galley"], "unlocked_buildings": [] },
        "astrology": { "name": "Astrology", "science_cost": 50, "required_techs": [], "unloced_units": [], "unlocked_buildings": ["shrine"] },
        "irrigation": { "name": "Irrigation", "science_cost": 50, "required_techs": ["pottery"], "unloced_units": [], "unlocked_buildings": [] },
        "writing": { "name": "Writing", "science_cost": 50, "required_techs": ["pottery"], "unloced_units": [], "unlocked_buildings": ["library"] },
        "archery": { "name": "Archery", "science_cost": 50, "required_techs": ["animalHusbandry"], "unloced_units": ["archer"], "unlocked_buildings": [] },
        "masonry": { "name": "Masonry", "science_cost": 80, "required_techs": ["mining"], "unloced_units": [], "unlocked_buildings": ["walls"] },
        "bronzeWorking": { "name": "Bronze Working", "science_cost": 80, "required_techs": ["mining"], "unloced_units": ["spearman"], "unlocked_buildings": ["barracks"] },
        "wheel": { "name": "Wheel", "science_cost": 80, "required_techs": ["mining"], "unloced_units": [], "unlocked_buildings": ["waterMill"] },
        # ===== CLASSICAL =====
        "celestialNavigation": { "name": "Celestial Navigation", "science_cost": 120, "required_techs": ["sailing"], "unloced_units": [], "unlocked_buildings": ["lighthouse"] },
        "currency": { "name": "Currency", "science_cost": 120, "required_techs": ["writing"], "unloced_units": [], "unlocked_buildings": ["market"] },
        "horsebackRiding": { "name": "Horseback Riding", "science_cost": 120, "required_techs": ["animalHusbandry"], "unloced_units": ["horseman"], "unlocked_buildings": ["stable"] },
        "ironWorking": { "name": "Iron Working", "science_cost": 120, "required_techs": ["bronzeWorking"], "unloced_units": ["swordsman"], "unlocked_buildings": [] },
        "shipBuilding": { "name": "Shipbuilding", "science_cost": 120, "required_techs": ["sailing"], "unloced_units": [], "unlocked_buildings": [] },
        "mathematics": { "name": "Mathematics", "science_cost": 200, "required_techs": ["currency"], "unloced_units": [], "unlocked_buildings": [] },
        "engineering": { "name": "Engineering", "science_cost": 200, "required_techs": ["wheel"], "unloced_units": ["catapult"], "unlocked_buildings": [] },
        "construction": { "name": "Construction", "science_cost": 200, "required_techs": ["masonry"], "unloced_units": [], "unlocked_buildings": [] },
        # ===== MEDIEVAL =====
        "militaryTactics": { "name": "Military Tactics", "science_cost": 275, "required_techs": ["construction"], "unloced_units": ["pikeman"], "unlocked_buildings": [] },
        "apprenticeship": { "name": "Apprenticeship", "science_cost": 275, "required_techs": ["mining"], "unloced_units": [], "unlocked_buildings": ["workshop"] },
        "machinery": { "name": "Machinery", "science_cost": 275, "required_techs": ["engineering"], "unloced_units": ["crossbowman"], "unlocked_buildings": [] },
        "stirrups": { "name": "Stirrups", "science_cost": 275, "required_techs": ["horsebackRiding"], "unloced_units": ["knight"], "unlocked_buildings": [] },
        "education": { "name": "Education", "science_cost": 335, "required_techs": ["apprenticeship"], "unloced_units": [], "unlocked_buildings": ["university"] },
        "militaryEngineering": { "name": "Military Engineering", "science_cost": 335, "required_techs": ["construction"], "unloced_units": [], "unlocked_buildings": ["armory"] },
        "castles": { "name": "Castles", "science_cost": 335, "required_techs": ["engineering"], "unloced_units": [], "unlocked_buildings": [] },
        # ===== RENAISSANCE =====
        "cartography": { "name": "Cartography", "science_cost": 400, "required_techs": ["shipBuilding"], "unloced_units": ["caravel"], "unlocked_buildings": [] },
        "gunpowder": { "name": "Gunpowder", "science_cost": 400, "required_techs": ["militaryEngineering"], "unloced_units": ["musketman"], "unlocked_buildings": [] },
        "massProduction": { "name": "Mass Production", "science_cost": 400, "required_techs": ["shipBuilding"], "unloced_units": [], "unlocked_buildings": ["shipyard"] },
        "banking": { "name": "Banking", "science_cost": 400, "required_techs": ["education"], "unloced_units": [], "unlocked_buildings": ["bank"] },
        "printing": { "name": "Printing", "science_cost": 400, "required_techs": ["education"], "unloced_units": [], "unlocked_buildings": [] },
        "squareRigging": { "name": "Square Rigging", "science_cost": 400, "required_techs": ["cartography"], "unloced_units": ["frigate"], "unlocked_buildings": [] },
        "astronomy": { "name": "Astronomy", "science_cost": 400, "required_techs": ["education"], "unloced_units": [], "unlocked_buildings": [] },
        "metalCasting": { "name": "Metal Casting", "science_cost": 400, "required_techs": ["apprenticeship"], "unloced_units": [], "unlocked_buildings": [] },
        "siegeTactics": { "name": "Siege Tactics", "science_cost": 400, "required_techs": ["castles"], "unloced_units": ["bombard"], "unlocked_buildings": [] },
        # ===== INDUSTRIAL =====
        "industrialization": { "name": "Industrialization", "science_cost": 490, "required_techs": ["apprenticeship"], "unloced_units": [], "unlocked_buildings": ["factory"] },
        "scientificTheory": { "name": "Scientific Theory", "science_cost": 490, "required_techs": ["education"], "unloced_units": [], "unlocked_buildings": [] },
        "ballistics": { "name": "Ballistics", "science_cost": 490, "required_techs": ["gunpowder"], "unloced_units": ["fieldCannon"], "unlocked_buildings": [] },
        "militaryScience": { "name": "Military Science", "science_cost": 490, "required_techs": ["stirrups"], "unloced_units": ["cavalry"], "unlocked_buildings": ["militaryAcademy"] },
        "steamPower": { "name": "Steam Power", "science_cost": 490, "required_techs": ["industrialization"], "unloced_units": [], "unlocked_buildings": ["seaport"] },
        "sanitation": { "name": "Sanitation", "science_cost": 490, "required_techs": ["scientificTheory"], "unloced_units": [], "unlocked_buildings": [] },
        "economics": { "name": "Economics", "science_cost": 490, "required_techs": ["banking"], "unloced_units": [], "unlocked_buildings": ["stockExchange"] },
        "rifling": { "name": "Rifling", "science_cost": 490, "required_techs": ["ballistics"], "unloced_units": ["ranger"], "unlocked_buildings": [] },
        # ===== MODERN =====
        "flight": { "name": "Flight", "science_cost": 600, "required_techs": ["steamPower"], "unloced_units": ["advancedFlight"], "unlocked_buildings": [] },
        "replaceableParts": { "name": "Replaceable Parts", "science_cost": 600, "required_techs": ["rifling"], "unloced_units": ["modernArmor"], "unlocked_buildings": [] },
        "steel": { "name": "Steel", "science_cost": 600, "required_techs": ["rifling"], "unloced_units": ["tank"], "unlocked_buildings": [] },
        "electricity": { "name": "Electricity", "science_cost": 600, "required_techs": ["steamPower"], "unloced_units": [], "unlocked_buildings": ["powerPlant"] },
        "radio": { "name": "Radio", "science_cost": 600, "required_techs": ["electricity"], "unloced_units": [], "unlocked_buildings": ["broadcastCenter"] },
        "chemistry": { "name": "Chemistry", "science_cost": 600, "required_techs": ["scientificTheory"], "unloced_units": [], "unlocked_buildings": ["researchLab"] },
        "combustion": { "name": "Combustion", "science_cost": 600, "required_techs": ["steel"], "unloced_units": ["tank"], "unlocked_buildings": [] },
        # ===== LATE GAME =====
        "refining": { "name": "Refining", "science_cost": 700, "required_techs": ["combustion"], "unloced_units": [], "unlocked_buildings": [] },
        "advancedFlight": { "name": "Advanced Flight", "science_cost": 700, "required_techs": ["flight"], "unloced_units": ["helicopter"], "unlocked_buildings": [] },
        "rocketry": { "name": "Rocketry", "science_cost": 700, "required_techs": ["radio"], "unloced_units": ["rocketArtillery"], "unlocked_buildings": [] },
        "guidanceSystems": { "name": "Guidance Systems", "science_cost": 700, "required_techs": ["rocketry"], "unloced_units": ["missileCruiser"],"unlocked_buildings": [] },
        "composites": { "name": "Composites", "science_cost": 700, "required_techs": ["replaceableParts"],"unloced_units": ["modernArmor"], "unlocked_buildings": [] },
        "syntheticMaterials": { "name": "Synthetic Materials", "science_cost": 700, "required_techs": ["composites"],"unloced_units": ["specOps"], "unlocked_buildings": [] },
        "advancedBallistics": { "name": "Advanced Ballistics", "science_cost": 700, "required_techs": ["ballistics"],"unloced_units": ["machineGun"], "unlocked_buildings": [] }
    }

    CIVICS = {
        # ===== ANCIENT =====
        "codeOfLaws": { "name": "Code Of Laws", "culture_cost": 20, "required_civics": [], "unlocked_policy_cards": ["discipline", "urbanPlanning", "godKing"], "unlocked_government": "chiefdom" },
        "craftsmanship": { "name": "Craftsmanship", "culture_cost": 40, "required_civics": ["codeOfLaws"], "unlocked_policy_cards": ["ilkum"], "unlocked_government": None },
        "foreignTrade": { "name": "Foreign Trade", "culture_cost": 40, "required_civics": ["codeOfLaws"], "unlocked_policy_cards": ["caravansaries", "maritimeIndustries"], "unlocked_government": None },
        "militaryTradition": { "name": "Military Tradition", "culture_cost": 50, "required_civics": ["craftsmanship"], "unlocked_policy_cards": ["maneuver"], "unlocked_government": None },
        "stateWorkforce": { "name": "State Workforce", "culture_cost": 70, "required_civics": ["craftsmanship"], "unlocked_policy_cards": ["charismaticLeader", "diplomaticLeague"], "unlocked_government": None },
        "earlyEmpire": { "name": "Early Empire", "culture_cost": 70, "required_civics": ["foreignTrade"], "unlocked_policy_cards": ["colonization"], "unlocked_government": None },
        "mysticism": { "name": "Mysticism", "culture_cost": 50, "required_civics": ["foreignTrade"], "unlocked_policy_cards": ["inspiration"], "unlocked_government": None },
        # ===== CLASSICAL =====
        "gamesAndRecreation": { "name": "Games and Recreation", "culture_cost": 110, "required_civics": ["stateWorkforce"], "unlocked_policy_cards": [], "unlocked_government": None },
        "politicalPhilosophy": { "name": "Political Philosophy", "culture_cost": 110, "required_civics": ["stateWorkforce", "earlyEmpire"], "unlocked_policy_cards": [], "unlocked_government": None },
        "dramaAndPoetry": { "name": "Drama and Poetry", "culture_cost": 110, "required_civics": ["earlyEmpire"], "unlocked_policy_cards": ["literaryTradition"], "unlocked_government": None },
        "theology": { "name": "Theology", "culture_cost": 110, "required_civics": ["mysticism"], "unlocked_policy_cards": [], "unlocked_government": None },
        "militaryTraining": { "name": "Military Training", "culture_cost": 110, "required_civics": ["militaryTradition"], "unlocked_policy_cards": [], "unlocked_government": None },
        # ===== MEDIEVAL =====
        "feudalism": { "name": "Feudalism", "culture_cost": 275, "required_civics": ["militaryTraining"], "unlocked_policy_cards": [], "unlocked_government": None },
        "civilService": { "name": "Civil Service", "culture_cost": 275, "required_civics": ["feudalism"], "unlocked_policy_cards": [], "unlocked_government": None },
        "divineRight": { "name": "Divine Right", "culture_cost": 275, "required_civics": ["theology"], "unlocked_policy_cards": [], "unlocked_government": "monarchy" },
        "mercenaries": { "name": "Mercenaries", "culture_cost": 275, "required_civics": ["feudalism"], "unlocked_policy_cards": [], "unlocked_government": None },
        "guilds": { "name": "Guilds", "culture_cost": 275, "required_civics": ["feudalism"], "unlocked_policy_cards": [], "unlocked_government": None },
        "medievalFaires": { "name": "Medieval Faires", "culture_cost": 275, "required_civics": ["guilds"], "unlocked_policy_cards": [], "unlocked_government": None },
        # ===== RENAISSANCE =====
        "humanism": { "name": "Humanism", "culture_cost": 400, "required_civics": ["guilds"], "unlocked_policy_cards": [], "unlocked_government": None },
        "diplomaticService": { "name": "Diplomatic Service", "culture_cost": 400, "required_civics": ["civilService"], "unlocked_policy_cards": [], "unlocked_government": None },
        "reformedChurch": { "name": "Reformed Church", "culture_cost": 400, "required_civics": ["divineRight"], "unlocked_policy_cards": [], "unlocked_government": "theocracy" },
        "mercantilism": { "name": "Mercantilism", "culture_cost": 400, "required_civics": ["guilds"], "unlocked_policy_cards": [], "unlocked_government": None },
        "enlightenment": { "name": "Enlightenment", "culture_cost": 400, "required_civics": ["humanism"], "unlocked_policy_cards": [], "unlocked_government": None },
        "exploration": { "name": "Exploration", "culture_cost": 400, "required_civics": ["mercantilism"], "unlocked_policy_cards": ["survey"], "unlocked_government": "merchantRepublic" },
        # ===== INDUSTRIAL =====
        "nationalism": { "name": "Nationalism", "culture_cost": 600, "required_civics": ["enlightenment"], "unlocked_policy_cards": [], "unlocked_government": None },
        "operaAndBallet": { "name": "Opera and Ballet", "culture_cost": 600, "required_civics": ["humanism"], "unlocked_policy_cards": [], "unlocked_government": None },
        "colonialism": { "name": "Colonialism", "culture_cost": 600, "required_civics": ["mercantilism"], "unlocked_policy_cards": [], "unlocked_government": None },
        "naturalHistory": { "name": "Natural History", "culture_cost": 600, "required_civics": ["colonialism"], "unlocked_policy_cards": [], "unlocked_government": None },
        "scorchedEarth": { "name": "Scorched Earth", "culture_cost": 600, "required_civics": ["nationalism"], "unlocked_policy_cards": [], "unlocked_government": None },
        # ===== MODERN =====
        "conservation": { "name": "Conservation", "culture_cost": 800, "required_civics": ["naturalHistory"], "unlocked_policy_cards": [], "unlocked_government": None },
        "mobilization": { "name": "Mobilization", "culture_cost": 800, "required_civics": ["nationalism"], "unlocked_policy_cards": [], "unlocked_government": None },
        "massMedia": { "name": "Mass Media", "culture_cost": 800, "required_civics": ["operaAndBallet"], "unlocked_policy_cards": [], "unlocked_government": None },
        "ideology": { "name": "Ideology", "culture_cost": 800, "required_civics": ["mobilization"], "unlocked_policy_cards": [], "unlocked_government": None },
        "suffrage": { "name": "Suffrage", "culture_cost": 800, "required_civics": ["ideology"], "unlocked_policy_cards": [], "unlocked_government": "democracy" },
        "totalitarianism": { "name": "Totalitarianism", "culture_cost": 800, "required_civics": ["ideology"], "unlocked_policy_cards": [], "unlocked_government": "fascism" },
        "classStruggle": { "name": "Class Struggle", "culture_cost": 800, "required_civics": ["ideology"], "unlocked_policy_cards": [], "unlocked_government": "communism" },
        # ===== LATE GAME =====
        "professionalSports": { "name": "Professional Sports", "culture_cost": 1000, "required_civics": ["naturalHistory"], "unlocked_policy_cards": [], "unlocked_government": None },
        "urbanization": { "name": "Urbanization", "culture_cost": 1000, "required_civics": ["civilService"], "unlocked_policy_cards": [], "unlocked_government": None }
    }

    POLICIES = {
        "discipline": { "name": "Discipline", "required_civic": "codeOfLaws", "military_bonus": 5, "economic_bonus": 0, "science_bonus": 0, "culture_bonus": 0 },
        "urbanPlanning": { "name": "Urban Planning", "required_civic": "codeOfLaws", "military_bonus": 0, "economic_bonus": 1, "science_bonus": 0, "culture_bonus": 0 },
        "godKing": { "name": "God King", "required_civic": "codeOfLaws", "military_bonus": 0, "economic_bonus": 0, "science_bonus": 0, "culture_bonus": 1 },
        "ilkum": { "name": "Ilkum", "required_civic": "craftsmanship", "military_bonus": 0, "economic_bonus": 1, "science_bonus": 0, "culture_bonus": 0 },
        "colonization": { "name": "Colonization", "required_civic": "earlyEmpire", "military_bonus": 0, "economic_bonus": 2, "science_bonus": 0, "culture_bonus": 0 },
        "caravansaries": { "name": "Caravansaries", "required_civic": "foreignTrade", "military_bonus": 0, "economic_bonus": 2, "science_bonus": 0, "culture_bonus": 0 },
        "maritimeIndustries": { "name": "Maritime Industries", "required_civic": "foreignTrade", "military_bonus": 2, "economic_bonus": 0, "science_bonus": 0, "culture_bonus": 0 },
        "maneuver": { "name": "Maneuver", "required_civic": "militaryTradition", "military_bonus": 2, "economic_bonus": 0, "science_bonus": 0, "culture_bonus": 0 },
        "survey": { "name": "Survey", "required_civic": "exploration", "military_bonus": 1, "economic_bonus": 0, "science_bonus": 0, "culture_bonus": 0 },
        "charismaticLeader": { "name": "Charismatic Leader", "required_civic": "stateWorkforce", "military_bonus": 0, "economic_bonus": 1, "science_bonus": 0, "culture_bonus": 0 },
        "diplomaticLeague": { "name": "Diplomatic League", "required_civic": "stateWorkforce", "military_bonus": 0, "economic_bonus": 1, "science_bonus": 0, "culture_bonus": 0 },
        "literaryTradition": { "name": "Literary Tradition", "required_civic": "dramaAndPoetry", "military_bonus": 0, "economic_bonus": 0, "science_bonus": 0, "culture_bonus": 2 },
        "inspiration": { "name": "Inspiration", "required_civic": "mysticism", "military_bonus": 0, "economic_bonus": 0, "science_bonus": 0, "culture_bonus": 1 },
    }

    IMPROVEMENTS = {
        "farm": { "name": "Farm", "required_tech": "pottery", "food_bonus": 1, "production_bonus": 0, "gold_bonus": 0 },
        "mine": { "name": "Mine", "required_tech": "mining", "food_bonus": 0, "production_bonus": 1, "gold_bonus": 0 },
        "quarry": { "name": "Quarry", "required_tech": "mining", "food_bonus": 0, "production_bonus": 1, "gold_bonus": 0 },
        "pasture": { "name": "Pasture", "required_tech": "animalHusbandry", "food_bonus": 1, "production_bonus": 1, "gold_bonus": 0 },
        "plantation": { "name": "Plantation", "required_tech": "irrigation", "food_bonus": 1, "production_bonus": 0, "gold_bonus": 2 },
        "camp": { "name": "Camp", "required_tech": "animalHusbandry", "food_bonus": 1, "production_bonus": 0, "gold_bonus": 1 },
        "fishingBoats": { "name": "Fishing Boats", "required_tech": "sailing", "food_bonus": 1, "production_bonus": 0, "gold_bonus": 1 },
        "lumberMill": { "name": "Lumber Mill", "required_tech": "construction", "food_bonus": 0, "production_bonus": 1, "gold_bonus": 0 }
    }

    TERRAIN = {
        "grassland": { "name": "Grassland", "food_yield": 2, "production_yield": 0, "gold_yield": 0, "isWater": False },
        "plains": { "name": "Plains", "food_yield": 1, "production_yield": 1, "gold_yield": 0, "isWater": False },
        "desert": { "name": "Desert", "food_yield": 0, "production_yield": 0, "gold_yield": 0, "isWater": False },
        "tundra": { "name": "Tundra", "food_yield": 1, "production_yield": 0, "gold_yield": 0, "isWater": False },
        "snow": { "name": "Snow", "food_yield": 0, "production_yield": 0, "gold_yield": 0, "isWater": False },
        "hills": { "name": "Hills", "food_yield": 0, "production_yield": 2, "gold_yield": 0, "isWater": False },
        "mountains": { "name": "Mountains", "food_yield": 0, "production_yield": 0, "gold_yield": 0, "isWater": False },
        "coast": { "name": "Coast", "food_yield": 1, "production_yield": 0, "gold_yield": 1, "isWater": True },
        "ocean": { "name": "Ocean", "food_yield": 1, "production_yield": 0, "gold_yield": 0, "isWater": True },
        "forest": { "name": "Forest", "food_yield": 1, "production_yield": 1, "gold_yield": 0, "isWater": False }
    }

    @staticmethod
    def get_unit_stats(u_type):
        return GameData.UNITS.get(u_type, {})