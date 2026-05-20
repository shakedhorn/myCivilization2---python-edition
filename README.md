# My Civilization 2 — Python Multiplayer Edition

An asynchronous, multiplayer turn-based 4X strategy game engine written in Python using **Pygame** for the graphical client interface and **Python Sockets** for the client-server network architecture. 

This project transitions the core mechanics of a traditional Civilization clone into a centralized server/distributed client model, where game logic, combat systems, and world maps are simulated entirely on the server side and synchronized via structured JSON network packets.

## Features

- **Client-Server Architecture:** Centralized `GameServer` handling state validation, combat math, and multi-client threading synchronization using thread locks.
- **Realistic Map Generation Scripts:** Procedural map generator utilizing Earth-like geographic probabilities (~71% water topology), explicit coastal borders, and latitudinal climate poles (guaranteed Tundra/Snow biomes at the top and bottom rows).
- **Socket Networking & Serialization:** Custom network protocol built over TCP sockets utilizing big-endian 4-byte headers for message length framing to eliminate TCP stream fragmentation.
- **Complete Combat & Unit Engines:** Handles movement management, Fog of War constraints, unit actions (such as Settlers founding cities), and dynamic melee calculation modifiers.
- **Extensive Data Dictionary Schema:** Unified reference tables for historical Eras (Ancient through Future), specific unit branches (Melee, Ranged, Mounted, Naval), and physical infrastructure extensions (Farms, Mines, Lumber Mills).

### Module Breakdown

- `CivShared/game_defs.py`: Contains unified game definitions (`GameData`). Defines resource yields (Food, Production, Gold), tech tree dependencies, unit statistics (melee strength, movement points, build configurations), and the `CommandType` enumeration set.
- `CivServer/game_logic.py`: Governs the `GameState` class. Tracks active entities, executes combat loops using safe delta thresholds, and handles atomic actions like tile expansion, structure queues, and unit lifecycle states.
- `CivServer/server.py`: Powers the network connection listener. Listens on a dedicated interface (`0.0.0.0`), boots independent connection-handler client threads, manages shared states securely using `threading.Lock`, and builds geographical biome maps.
- `client.py`: Drives the interactive interface via Pygame. Spawns an internal background daemon thread to consistently poll binary TCP server payloads, handles local mouse/keyboard input triggers, and renders the operational command map.

## Network Protocol Details

Communication relies on structured stringified JSON dictionaries framed over TCP streams. To guarantee message boundary delivery, packets use a 4-byte length prefix:

1. **Header Phase:** The sender transmits exactly `4 bytes` using big-endian byte-order mapping (`'big'`) denoting the size of the payload.
2. **Payload Phase:** The recipient reads the designated length from the socket buffer and parses it directly into an active JSON object.

### Sample Command Packet Schema (`MOVE_UNIT`)
```json
{
  "type": "MOVE_UNIT",
  "unit_id": "unit_12",
  "x": 14,
  "y": 8
}
