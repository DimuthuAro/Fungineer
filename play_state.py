import pygame as pg
from state_manager import GameState

class PlayState(GameState):
    def enter(self):
        self.is_pausable = True
    
    def exit(self):
        print("Exiting Play State")
    
    def handle_event(self, event):
        pass
    
    def update(self, dt):
        pass
    
    def render(self, screen):
        pass