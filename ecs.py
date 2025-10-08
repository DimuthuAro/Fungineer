import pygame as pg
from typing import cast
from game_state import GameState

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
        
    def add_component(self, component: Component):
        self.components[component.name] = component
        
    def get_component(self, component_name: str):
        return self.components.get(component_name, None)
        
    def remove_component(self, component_name: str):
        if component_name in self.components:
            del self.components[component_name]

    def has_components(self, component_names: list[str]) -> bool:
        for comp_name in component_names:
            if comp_name not in self.components:
                return False
        return True

from traceback_logging import TraceBackLogging

class System:
    def __init__(self, state: GameState):
        self.state = state
        self.required_components = []
        
    # Error Handling Methods
    def _check_entity(self, entity):
        if not entity:
            TraceBackLogging.log(entity)
            raise LookupError("Entity is None")

    def _check_component(self, component: Component | None):
        if not component:
            TraceBackLogging.log(component)
            raise LookupError(f"The Component - {getattr(component, 'name', '<unknown>')} is None")

    def check_for_none(self, entity: Entity | None, components: Component | list[Component]):
        self._check_entity(entity)
        if isinstance(components, list):
            for component in components:
                self._check_component(component)
        else:
            self._check_component(components)

    # Component Accessor Methods (Getters For Components From Entity)
    def get_position(self, entity) -> tuple[float, float]:
        position_component = cast(PositionComponent, entity.get_component("PositionComponent"))
        self.check_for_none(entity, position_component)
        position = (position_component.x, position_component.y)
        return position

    def get_size(self, entity) -> tuple[float, float]:
        size_component = cast(SizeComponent, entity.get_component("SizeComponent"))
        self.check_for_none(entity, size_component)
        size = (size_component.width, size_component.height)
        return size

    def get_rect(self, entity) -> pg.Rect:
        position_component = cast(PositionComponent, entity.get_component("PositionComponent"))
        size_component = cast(SizeComponent, entity.get_component("SizeComponent"))
        self.check_for_none(entity, [position_component, size_component])
        rect = pg.Rect(position_component.x, position_component.y, size_component.width, size_component.height)
        return rect

    def get_description(self, entity) -> str | None:
        description_component = cast(DescriptionComponent, entity.get_component("DescriptionComponent"))
        if description_component:
            description_component = cast(DescriptionComponent, description_component)
            return description_component.text
        return None
    
    def get_enemy_type(self, entity) -> int:
        enemy_component = cast(EnemyComponent, entity.get_component("EnemyComponent"))
        self.check_for_none(entity, enemy_component)
        return enemy_component.enemy_type

    def get_damage(self, entity) -> int:
        damage_component = cast(DamageComponent, entity.get_component("DamageComponent"))
        self.check_for_none(entity, damage_component)
        return damage_component.damage
    
    def get_health(self, entity) -> int:
        health_component = cast(HealthComponent, entity.get_component("HealthComponent"))
        self.check_for_none(entity, health_component)
        return health_component.health
    
    def get_bullet_type(self, entity) -> str:
        bullet_component = cast(BulletComponent, entity.get_component("BulletComponent"))
        self.check_for_none(entity, bullet_component)
        return bullet_component.BulletType
    
    def get_tower_type(self, entity) -> str:
        tower_component = cast(TowerComponent, entity.get_component("TowerComponent"))
        self.check_for_none(entity, tower_component)
        return tower_component.TowerType
    
    def get_bullet_sprite(self, entity) -> pg.Surface:
        bullet_sprite_component = cast(BulletSpriteComponent, entity.get_component("BulletSpriteComponent"))
        self.check_for_none(entity, bullet_sprite_component)
        return bullet_sprite_component.sprite
    
    def get_velocity(self, entity) -> tuple[float, float]:
        velocity_component = cast(VelocityComponent, entity.get_component("VelocityComponent"))
        self.check_for_none(entity, velocity_component)
        return (velocity_component.vx, velocity_component.vy)
    
    def get_friction(self, entity) -> float:
        friction_component = cast(FrictionComponent, entity.get_component("FrictionComponent"))
        self.check_for_none(entity, friction_component)
        return friction_component.friction
    
    def get_sprite(self, entity) -> pg.Surface:
        sprite_component = cast(SpriteComponent, entity.get_component("SpriteComponent"))
        self.check_for_none(entity, sprite_component)
        return sprite_component.sprite
    
    def set_health(self, entity, new_health: int):
        health_component = cast(HealthComponent, entity.get_component("HealthComponent"))
        self.check_for_none(entity, health_component)
        health_component.health = new_health
        
    def set_position(self, entity, new_position: tuple[float, float]):
        position_component = cast(PositionComponent, entity.get_component("PositionComponent"))
        self.check_for_none(entity, position_component)
        position_component.x, position_component.y = new_position
        
    def set_velocity(self, entity, new_velocity: tuple[float, float]):
        velocity_component = cast(VelocityComponent, entity.get_component("VelocityComponent"))
        self.check_for_none(entity, velocity_component)
        velocity_component.vx, velocity_component.vy = new_velocity
        
    @property
    def entities(self):
        return self.state.entities

    def handle_event(self, event):
        pass
    
    def update(self, dt):
        pass
    
    def render(self, screen):
        pass
