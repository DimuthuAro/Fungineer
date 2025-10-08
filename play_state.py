import pygame as pg
from game_state import GameState
from systems.render_system import RenderSystem
from systems.movement_system import MovementSystem
from systems.input_system import InputSystem
from ecs import Entity, Component, PositionComponent, SpriteComponent, VelocityComponent, ControllableComponent

class PlayState(GameState):
    def enter(self):
        self.is_pausable = True
        self.system_initialization()
        self.player = Entity(name="Player")
        self.player.add_component(PositionComponent(x=100, y=100))
        self.player.add_component(ControllableComponent())
        sprite = pg.Surface((50, 50))
        sprite.fill((0, 255, 0))  # Fill the sprite with green
        self.player.add_component(SpriteComponent(sprite=sprite))
        self.player.add_component(VelocityComponent(vx=10, vy=0))
        self.entities.append(self.player)
        
    def system_initialization(self):
        print("Initializing systems for Play State")
        self.render_system = RenderSystem(self)
        self.movement_system = MovementSystem(self)
        self.input_system = InputSystem(self)
    
    def exit(self):
        print("Exiting Play State")
    
    def handle_event(self, event):
        self.input_system.handle_event(event)
    
    def update(self, dt):
        self.movement_system.update(dt)

    def render(self, screen):
        self.render_system.render(screen)