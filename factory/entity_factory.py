from ecs import ControllableComponent, EnemyComponent, Entity, FactoryComponent, PositionComponent, AnimatedSpriteComponent, SizeComponent, SpawnerComponent, SpriteComponent, VelocityComponent, HealthComponent, CollisionComponent
import pygame as pg
from ecs import WorkerComponent
from sprite_manager import SpriteManager

class EntityFactory:
    
    def __init__(self, game_state):
        self.state = game_state
        self.sprite_manager = SpriteManager()
        self.DEBUG_SPRITE = pg.Surface((32, 32))
        self.DEBUG_SPRITE.fill((255, 0, 255))

    def create_entity(self, entity_type: str, position: tuple[int, int]=(0,0), sprite_names: str | list[str] ="player_004", velocity: tuple[int, int]=(0,0), size: tuple[int, int]=(64,64)):
        same_type_entity_count = sum(1 for e in self.state.entities if e.name.startswith(entity_type))
        sprites = []
        if isinstance(sprite_names, str):
            sprite_names = [sprite_names]
        for sprite_name in sprite_names:
            sprite = self.sprite_manager.get_sprite(sprite_name)
            sprite = pg.transform.scale(sprite, size)
            if sprite:
                sprites.append(sprite)
            
        entity = Entity(f"{entity_type}_{same_type_entity_count}")    
            
        if sprites and len(sprites) > 0:
            if len(sprites) == 1:
                sprite = sprites[0]
                entity.add_component(SpriteComponent(sprite=sprite))
            else:
                sprite = sprites
                entity.add_component(AnimatedSpriteComponent(frames=sprite, frame_duration=0.2))
        else:
            entity.add_component(SpriteComponent(sprite=self.DEBUG_SPRITE))

        entity.add_component(PositionComponent(x=position[0], y=position[1]))
        entity.add_component(SizeComponent(width=size[0], height=size[1]))
        entity.add_component(VelocityComponent(vx=velocity[0], vy=velocity[1]))
        entity.add_component(HealthComponent(health=100))
        entity.add_component(CollisionComponent(plane=0))
            
        if entity_type == "Enemy":
            entity.add_component(EnemyComponent(enemy_type=0))
        elif entity_type == "Worker":
            entity.add_component(WorkerComponent())
        elif entity_type == "Villager":
            entity.add_component(WorkerComponent())
        elif entity_type == "Factory":
            entity.add_component(FactoryComponent(factory_type="GenericFactory"))
        elif entity_type == "Spawner":
            entity.add_component(SpawnerComponent(spawn_rate=5.0, enemy_type=["BasicEnemy"]))
        elif entity_type == "Player":
            entity.add_component(ControllableComponent())

        self.state.entities.append(entity)