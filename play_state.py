import pygame as pg
from state_manager import GameState

class PlayState(GameState):
    def enter(self):
        self.is_pausable = True
        self.fps = 0.0
        self.ups = 0.0
        self.paused = False
        self.text = "Play State - Press 'P' to Pause"
        print("Entering Play State")
    
    def exit(self):
        print("Exiting Play State")
    
    def handle_event(self, event):
        pass
    
    def update(self, dt):
        self.ups += dt
        self.text = f"Play State - FPS: {self.fps % 1} UPS: {self.ups % 1} - Press 'P' to Pause"
    
    def render(self, screen):
        pg.draw.rect(screen, (0, 128, 255), (50, 50, 700, 500))
        font = pg.font.Font(None, 36)
        text_surf = font.render(self.text, True, (255, 255, 255))
        screen.blit(text_surf, (60, 60))