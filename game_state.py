from os import system
import pygame as pg
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ecs import Entity
    from ecs import System
    
class GameState:
    is_pausable = False
    shoot_interval: float = 0.2
    entities: list['Entity'] = []
    systems: dict[str, 'System'] = {}
    state_data: dict[str, float] = {}
    resource_data: dict[str, float] = {}
    max_resource_data: dict[str, float] = {}
    max_trees = 120
    def enter(self):...
    def exit(self):...

    def handle_event(self, event):
        for system in self.systems.values():
            system.handle_event(event)  

    def update(self, dt):
        for system in self.systems.values():
            system.update(dt)

    def render(self, screen):
        for system in self.systems.values():
            system.render(screen)