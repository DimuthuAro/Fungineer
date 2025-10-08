from re import T
from typing import cast
from numpy import size
import pygame as pg
from regex import D

class Component():
    def __init__(self):
        self.name = self.__class__.__name__
        
class SizeComponent(Component):
    def __init__(self, width=0.0, height=0.0):
        super().__init__()
        self.width: float = width
        self.height: float = height        
        
class PositionComponent(Component):
    def __init__(self, x=0.0, y=0.0):
        super().__init__()
        self.x: float = x
        self.y: float = y

class VelocityComponent(Component):
    def __init__(self, vx:float=0, vy:float=0):
        super().__init__()
        self.vx: float = vx
        self.vy: float = vy
        
class SpriteComponent(Component):
    def __init__(self, sprite : pg.Surface):
        super().__init__()
        self.sprite = sprite
        
class FrictionComponent(Component):
    def __init__(self, friction=0.1):
        super().__init__()
        self.friction = friction
        
class ControllableComponent(Component):
    def __init__(self):
        super().__init__()
        
class HealthComponent(Component):
    def __init__(self, health=100):
        super().__init__()
        self.health = health
        self.max_health = health
        
class DamageComponent(Component):
    def __init__(self, damage=10):
        super().__init__()
        self.damage = damage
        
class BulletComponent(Component):
    def __init__(self, BulletType="Basic"):
        super().__init__()
        self.BulletType = BulletType
        
class TowerComponent(Component):
    def __init__(self, TowerType: str="Basic"):
        super().__init__()
        self.TowerType: str = TowerType
        
class BulletSpriteComponent(Component):
    def __init__(self, sprite: pg.Surface):
        super().__init__()
        self.sprite = sprite
        
class EnemyComponent(Component):
    def __init__(self, enemy_type: int):
        super().__init__()
        self.enemy_type = enemy_type
        
class EffectComponent(Component):
    def __init__(self, effect_type: str):
        super().__init__()
        self.effect_type = effect_type
        self.duration = 0.5  # seconds
        self.rotation = 0.0  # degrees
        self.size = 1.0  # scale factor
        self.speed = 50.0  # pixels per second
        self.rotation_speed = 90.0  # degrees per second
        self.direction = 1.0  # 1.0 for up-right, -1.0 for down-left
        self.size_growth = 2.5  # scale factor per second

class GridComponent(Component):
    def __init__(self, grid_x=0, grid_y=0):
        super().__init__()
        self.grid_x = grid_x
        self.grid_y = grid_y

class DescriptionComponent(Component):
    def __init__(self, text="Description <Not Set>"):
        super().__init__()
        self.text = text       
 
class Entity:
    def __init__(self, name):
        self.name = name
        self.components = {}
        self.required_components = []
        
    def add_component(self, component: Component):
        self.components[component.name] = component
        
    def get_component(self, component_name: str):
        return self.components.get(component_name, None)
        
    def remove_component(self, component_name: str):
        if component_name in self.components:
            del self.components[component_name]

    def add_required_component(self, component: Component):
        self.required_components.append(component.name)

    def get_required_components(self):
        return self.required_components

    def has_required_components(self):
        for comp_name in self.required_components:
            if comp_name not in self.components:
                return False
        return True