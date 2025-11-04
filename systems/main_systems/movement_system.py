import pygame as pg
from game_state import GameState
from ecs import System, PositionComponent, VelocityComponent

class MovementSystem(System):
    def __init__(self, state: GameState):
        super().__init__(state)
        self.required_components = ['PositionComponent', 'VelocityComponent']
        
        # Physics constants for more realistic movement
        self.max_velocity = 500.0  # Maximum velocity in pixels/second
        self.velocity_threshold = 0.5  # Stop moving if velocity is below this
        
    def update(self, dt):
        for entity in self.state.entities:
            if entity.has_components(self.required_components):
                
                position = self.get_position(entity)
                velocity = self.get_velocity(entity)
                
                # Get friction coefficient (0.0 = no friction, 1.0 = maximum friction)
                friction = self.get_friction(entity) if entity.get_component("FrictionComponent") else 0.1
                friction = max(0.0, min(1.0, friction))  # Clamp between 0 and 1
                
                # Apply friction using exponential decay for more realistic deceleration
                # This creates a smooth slowdown rather than linear
                friction_multiplier = pow(1.0 - friction, dt)
                vx = velocity[0] * friction_multiplier
                vy = velocity[1] * friction_multiplier
                
                # Stop completely if velocity is very small (prevent infinite sliding)
                if abs(vx) < self.velocity_threshold:
                    vx = 0.0
                if abs(vy) < self.velocity_threshold:
                    vy = 0.0
                
                # Cap velocity to maximum speed (prevents unrealistic acceleration)
                speed = (vx * vx + vy * vy) ** 0.5
                if speed > self.max_velocity:
                    scale = self.max_velocity / speed
                    vx *= scale
                    vy *= scale
                
                # Update velocity first
                self.set_velocity(entity, (vx, vy))
                
                # Update position using the new velocity (Euler integration)
                # For more accuracy, could use Verlet or RK4 integration
                x = position[0] + vx * dt
                y = position[1] + vy * dt
                
                self.set_position(entity, (x, y))