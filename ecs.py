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

class TooltipComponent(Component):
    def __init__(self, text="Description <Not Set>"):
        super().__init__()
        self.text = text
        self.tooptip_id = id(self)
        self.is_on = False

class TextComponent(Component):
    def __init__(self, text=""):
        super().__init__()
        self.text = text

class CollisionComponent(Component):
    def __init__(self, plane=0):
        super().__init__()
        self.is_colliding = False
        self.plane = plane

class SpawnerComponent(Component):
    def __init__(self, spawn_rate: float=5.0, enemy_type: list[str]=["BasicEnemy"]):
        super().__init__()
        self.spawn_rate: float = spawn_rate  # seconds between spawns
        self.enemy_type: list[str] = enemy_type
        self.time_since_last_spawn: float = 0.0  # seconds

class TileComponent(Component):
    def __init__(self, tile_type: int):
        super().__init__()
        self.tile_type = tile_type
        
class TreeComponent(Component):
    def __init__(self, tree_type: str):
        super().__init__()
        self.tree_type = tree_type

class FactoryComponent(Component):
    def __init__(self, factory_type: str):
        super().__init__()
        self.factory_type = factory_type
        
class ResourceComponent(Component):
    def __init__(self, resource_type: str, resource_amount: float=100):
        super().__init__()
        self.resource_type: str = resource_type
        self.resource_amount: float = resource_amount
        
class WorkerComponent(Component):
    def __init__(self):
        super().__init__()
        self.carrying_capacity = 100
        self.current_load = 0
        
class AnimatedSpriteComponent(Component):
    def __init__(self, frames: list[pg.Surface], frame_duration: float):
        super().__init__()
        self.frames = frames
        self.frame_duration = frame_duration  # seconds per frame
        self.current_frame_index = 0
        self.time_since_last_frame = 0.0  # seconds   
        
class Entity:
    EntityRegistry: dict[str, 'Entity'] = {}

    def __init__(self, name):
        self.name = name
        self.tooltip_component = TooltipComponent(name)
        self.components = {}
        self.state_data = {}
        self.add_component(self.tooltip_component)
        Entity.EntityRegistry[name] = self
        
    def set_name(self, new_name: str):
        del Entity.EntityRegistry[self.name]
        self.name = new_name
        Entity.EntityRegistry[new_name] = self

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

    def get_direction_for_sprite(self, entity) -> str:
        velocity = self.get_velocity(entity)
        vx, vy = velocity
        if abs(vx) > abs(vy):
            if vx > 0:
                return "right"
            else:
                return "left"
        else:
            if vy > 0:
                return "down"
            else:
                return "up"
    
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

    def get_tooltip(self, entity) -> str | None:
        description_component = cast(TooltipComponent, entity.get_component("TooltipComponent"))
        if description_component:
            description_component = cast(TooltipComponent, description_component)
            return description_component.text
        return None
    
    def set_tooltip(self, entity, new_tooltip: str):
        tooltip_component = cast(TooltipComponent, entity.get_component("TooltipComponent"))
        self.check_for_none(entity, tooltip_component)
        tooltip_component.text = new_tooltip
    
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
    
    def get_text(self, entity) -> str:
        text_component = cast(TextComponent, entity.get_component("TextComponent"))
        self.check_for_none(entity, text_component)
        return text_component.text
    
    def get_collition_plane(self, entity) -> int:
        collision_component = cast(CollisionComponent, entity.get_component("CollisionComponent"))
        self.check_for_none(entity, collision_component)
        return collision_component.plane
    
    def get_collition_status(self, entity) -> bool:
        collision_component = cast(CollisionComponent, entity.get_component("CollisionComponent"))
        self.check_for_none(entity, collision_component)
        return collision_component.is_colliding
    
    def get_tile_type(self, entity) -> int:
        tile_component = cast(TileComponent, entity.get_component("TileComponent"))
        self.check_for_none(entity, tile_component)
        return tile_component.tile_type
    
    def get_tile_grid_position(self, entity) -> tuple[int, int]:
        grid_component = cast(GridComponent, entity.get_component("GridComponent"))
        self.check_for_none(entity, grid_component)
        return (grid_component.grid_x, grid_component.grid_y)
    
    def get_tree_type(self, entity) -> str:
        tree_component = cast(TreeComponent, entity.get_component("TreeComponent"))
        self.check_for_none(entity, tree_component)
        return tree_component.tree_type

    def get_tooltip_status(self, entity) -> bool:
        tooltip_component = cast(TooltipComponent, entity.get_component("TooltipComponent"))
        self.check_for_none(entity, tooltip_component)
        return tooltip_component.is_on
    
    def get_factory_type(self, entity) -> str:
        factory_component = cast(FactoryComponent, entity.get_component("FactoryComponent"))
        self.check_for_none(entity, factory_component)
        return factory_component.factory_type
    
    def get_resource_type(self, entity) -> str:
        resource_component = cast(ResourceComponent, entity.get_component("ResourceComponent"))
        self.check_for_none(entity, resource_component)
        return resource_component.resource_type
    
    def get_worker_type(self, entity) -> int | None:
        worker_component = cast(WorkerComponent, entity.get_component("WorkerComponent"))
        if worker_component:
            return 1  # Assuming only one type of worker for now
        return 1
    
    def get_sprite_frames(self, entity) -> list[pg.Surface]:
        animated_sprite_component = cast(AnimatedSpriteComponent, entity.get_component("AnimatedSpriteComponent"))
        self.check_for_none(entity, animated_sprite_component)
        return animated_sprite_component.frames
    
    def get_sprite_frame_duration(self, entity) -> float:
        animated_sprite_component = cast(AnimatedSpriteComponent, entity.get_component("AnimatedSpriteComponent"))
        self.check_for_none(entity, animated_sprite_component)
        return animated_sprite_component.frame_duration
    
    def get_sprite_current_frame_index(self, entity) -> int:
        animated_sprite_component = cast(AnimatedSpriteComponent, entity.get_component("AnimatedSpriteComponent"))
        self.check_for_none(entity, animated_sprite_component)
        return animated_sprite_component.current_frame_index
    
    def get_sprite_time_since_last_frame(self, entity) -> float:
        animated_sprite_component = cast(AnimatedSpriteComponent, entity.get_component("AnimatedSpriteComponent"))
        self.check_for_none(entity, animated_sprite_component)
        return animated_sprite_component.time_since_last_frame
    
    def get_sprite_current_frame(self, entity) -> pg.Surface:
        animated_sprite_component = cast(AnimatedSpriteComponent, entity.get_component("AnimatedSpriteComponent"))
        self.check_for_none(entity, animated_sprite_component)
        return animated_sprite_component.frames[animated_sprite_component.current_frame_index]
    
    def set_sprite_current_frame_index(self, entity, new_index: int):
        animated_sprite_component = cast(AnimatedSpriteComponent, entity.get_component("AnimatedSpriteComponent"))
        self.check_for_none(entity, animated_sprite_component)
        animated_sprite_component.current_frame_index = new_index
        
    def set_sprite_time_since_last_frame(self, entity, new_time: float):
        animated_sprite_component = cast(AnimatedSpriteComponent, entity.get_component("AnimatedSpriteComponent"))
        self.check_for_none(entity, animated_sprite_component)
        animated_sprite_component.time_since_last_frame = new_time
        
    def set_sprite_frames(self, entity, new_frames: list[pg.Surface]):
        animated_sprite_component = cast(AnimatedSpriteComponent, entity.get_component("AnimatedSpriteComponent"))
        self.check_for_none(entity, animated_sprite_component)
        animated_sprite_component.frames = new_frames
        
    def set_sprite_frame_duration(self, entity, new_duration: float):
        animated_sprite_component = cast(AnimatedSpriteComponent, entity.get_component("AnimatedSpriteComponent"))
        self.check_for_none(entity, animated_sprite_component)
        animated_sprite_component.frame_duration = new_duration     
        
    def set_worker_type(self, entity, new_worker_type: int):
        worker_component = cast(WorkerComponent, entity.get_component("WorkerComponent"))
        self.check_for_none(entity, worker_component)
        # Currently only one type of worker, so no action needed
        pass
    
    def set_resource_type(self, entity, new_resource_type: str):
        resource_component = cast(ResourceComponent, entity.get_component("ResourceComponent"))
        self.check_for_none(entity, resource_component)
        resource_component.resource_type = new_resource_type
    
    def set_factory_type(self, entity, new_factory_type: str):
        factory_component = cast(FactoryComponent, entity.get_component("FactoryComponent"))
        self.check_for_none(entity, factory_component)
        factory_component.factory_type = new_factory_type
    
    def set_tooltip_status(self, entity, is_on: bool):
        tooltip_component = cast(TooltipComponent, entity.get_component("TooltipComponent"))
        self.check_for_none(entity, tooltip_component)
        tooltip_component.is_on = is_on

    def set_tree_type(self, entity, new_tree_type: str):
        tree_component = cast(TreeComponent, entity.get_component("TreeComponent"))
        self.check_for_none(entity, tree_component)
        tree_component.tree_type = new_tree_type

    def set_tile_type(self, entity, new_tile_type: int):
        tile_component = cast(TileComponent, entity.get_component("TileComponent"))
        self.check_for_none(entity, tile_component)
        tile_component.tile_type = new_tile_type
        
    def set_tile_grid_position(self, entity, new_grid_position: tuple[int, int]):   
        grid_component = cast(GridComponent, entity.get_component("GridComponent"))
        self.check_for_none(entity, grid_component)
        grid_component.grid_x, grid_component.grid_y = new_grid_position
    
    def set_text(self, entity, new_text: str):
        text_component = cast(TextComponent, entity.get_component("TextComponent"))
        self.check_for_none(entity, text_component)
        text_component.text = new_text
    
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
