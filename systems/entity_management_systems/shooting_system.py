from ecs import DamageComponent, System, Entity, Component, VelocityComponent, PositionComponent, SpriteComponent, CollisionComponent, SizeComponent
from game_state import GameState
import pygame as pg

class ShootingSystem(System):
    BULLET_COUNT=0
    def __init__(self, state: GameState):
        super().__init__(state)
        self.required_components: list[str] = ['ControllableComponent', 'PositionComponent', 'SpriteComponent']
        self.is_mouse_down = False
        self.lastframe = 0.0
        self.currentframe = 0.0
        self.state = state
        
    def update(self, dt):
        self.is_mouse_down = pg.mouse.get_pressed()[0]
        for entity in self.state.entities:
            if entity.has_components(self.required_components):
                if  self.is_mouse_down:
                    self.handle_shooting(entity, dt)
                
    def handle_shooting(self, entity, dt):
        self.currentframe += dt
        if self.state.shoot_interval is None:
            return
        if self.currentframe - self.lastframe < self.state.shoot_interval:
            return
        self.lastframe = self.currentframe
        # Placeholder for shooting logic
        position = self.get_position(entity)
        mouse_x, mouse_y = pg.mouse.get_pos()
        direction_x = mouse_x - position[0]
        direction_y = mouse_y - position[1]
        direction_length = self.pythagorus(direction_x, direction_y)
        if direction_length > 0:
            direction_x /= direction_length
            direction_y /= direction_length
        
        self.shoot_a_bullet(position, direction_x, direction_y, direction_length)

    def shoot_a_bullet(self, position, dir_x, dir_y, dir_length):
        bullet = Entity(F"Bullet_{ShootingSystem.BULLET_COUNT}")
        ShootingSystem.BULLET_COUNT += 1
        bullet_speed = 500  # pixels per second
        bullet_velocity_x = dir_x * bullet_speed
        bullet_velocity_y = dir_y * bullet_speed
        
        DEBUG_BULLET_SPRITE = pg.Surface((10, 5))
        DEBUG_BULLET_SPRITE.fill((255, 255, 0))  # Yellow for bullet
        bullet.add_component(DamageComponent(damage=25))
        bullet.add_component(PositionComponent(x=position[0], y=position[1]))
        bullet.add_component(SpriteComponent(sprite=DEBUG_BULLET_SPRITE))
        bullet.add_component(SizeComponent(width=10, height=5))
        bullet.add_component(VelocityComponent(vx=bullet_velocity_x, vy=bullet_velocity_y))
        bullet.add_component(CollisionComponent(plane=0))
        self.state.entities.append(bullet)

    def pythagorus(self, a: float, b: float) -> float:
        return (a ** 2 + b ** 2) ** 0.5
        