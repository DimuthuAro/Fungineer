import pygame as pg

from ecs import System
from game_state import GameState

class RenderSystem(System):
    def __init__(self, state: GameState):
        super().__init__(state)
        self.rendering_components = [ 'PositionComponent', 'SpriteComponent' ]
        
    def render(self, screen):
        for entity in self.entities:
            if entity.has_components(self.rendering_components):
                position = self.get_position(entity)
                sprite = self.get_sprite(entity)
                screen.blit(sprite, position)