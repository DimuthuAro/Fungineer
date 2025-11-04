import pygame as pg
from game_state import GameState
from ecs import Component, ControllableComponent, VelocityComponent, System

class InputSystem(System):
    KEY_DICT = {
        pg.K_UP: 'UP',
        pg.K_DOWN: 'DOWN',
        pg.K_LEFT: 'LEFT',
        pg.K_RIGHT: 'RIGHT',
        pg.K_w: 'UP',
        pg.K_s: 'DOWN',
        pg.K_a: 'LEFT',
        pg.K_d: 'RIGHT',
    }
    
    DIRECTION_DICT = {
        'UP': (0, -1),
        'DOWN': (0, 1),
        'LEFT': (-1, 0),
        'RIGHT': (1, 0),
    }
    
    def __init__(self, state: GameState, speed: float = 200.0):
        super().__init__(state)
        self.state = state
        self.required_components = ['ControllableComponent', 'VelocityComponent']
        self.pressed_keys = set()
        self.movement_speed = speed  # Movement speed in pixels per second
        

    def handle_event(self, event):
        for entity in self.state.entities:
            if entity.has_components(self.required_components):
                self.process_event(entity, event)

    def process_event(self, entity, event):
        if event.type == pg.KEYDOWN:
            if event.key in self.KEY_DICT:
                self.pressed_keys.add(event.key)
                self.update_velocity(entity)
                
        elif event.type == pg.KEYUP:
            if event.key in self.KEY_DICT:
                if event.key in self.pressed_keys:
                    self.pressed_keys.remove(event.key)
                self.update_velocity(entity)

    def update_velocity(self, entity):
        """Update entity velocity based on currently pressed keys"""
        # Calculate the net direction from all pressed keys
        total_dx = 0
        total_dy = 0
        
        for key in self.pressed_keys:
            if key in self.KEY_DICT:
                direction = self.KEY_DICT[key]
                dx, dy = self.DIRECTION_DICT[direction]
                total_dx += dx
                total_dy += dy
        
        # Normalize diagonal movement to prevent faster diagonal speed
        if total_dx != 0 and total_dy != 0:
            # Diagonal movement: divide by sqrt(2) to maintain consistent speed
            length = (total_dx * total_dx + total_dy * total_dy) ** 0.5
            total_dx = total_dx / length
            total_dy = total_dy / length
        
        # Apply movement speed
        vx = total_dx * self.movement_speed
        vy = total_dy * self.movement_speed
        
        self.set_velocity(entity, (vx, vy))