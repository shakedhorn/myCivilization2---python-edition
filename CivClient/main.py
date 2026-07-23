import pygame
import time
from CivClient.network import Network
from CivClient.renderer import Renderer
from CivClient.ui_manager import UIManager
from CivClient.input_handler import InputHandler

class CivApp:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1024, 768))
        pygame.display.set_caption("My Civilization 2 - Python Edition")
        
        self.clock = pygame.time.Clock()
        
        # State
        self.state = "SPLASH"
        self.input_text = ""
        self.username = ""
        self.server_ip = ""
        self.games_list = []
        self.game_state = None
        self.my_id = None
        
        # Gameplay State
        self.selected_unit_id = None
        self.selected_city_id = None
        self.active_panel = "MAP"
        self.target_mode = None
        self.target_building = None
        
        # Camera
        self.camera_x = 0
        self.camera_y = 0
        self.tile_size = 32
        
        # UI Scroll state
        self.tree_scroll_y = 0
        self.tree_scroll_x = 0
        self.city_build_scroll_y = 0
        self.current_prod_list_len = 0
        
        self.start_time = time.time()
        
        self.network = Network(self)
        self.ui_manager = UIManager(self)
        self.renderer = Renderer(self)
        self.input_handler = InputHandler(self)

    def run(self):
        running = True
        while running:
            running = self.input_handler.handle_events()
            if not running:
                break
            self.input_handler.handle_keys_held()
            self.renderer.render()
            self.clock.tick(30)
        self.network.close()
        pygame.quit()

if __name__ == "__main__":
    CivApp().run()
