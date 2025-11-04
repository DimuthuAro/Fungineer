import pygame as pg
from turtle import position
from ecs import CollisionComponent, Entity, HealthComponent, PositionComponent, ResourceComponent, SizeComponent, SpriteComponent, TreeComponent
import sprite_manager
import random
import pygame



class ResourceFactory:
    COUNT = {"tree": 0, "stone": 0, "pond": 0, "animal": 0}
    def __init__(self):
        self.sprite_manager = sprite_manager.SpriteManager()
        self.tree_sprite1 = self.sprite_manager.get_sprite("TREE_001")
        self.tree_sprite1 = pygame.transform.scale(self.tree_sprite1, (32, 32))
        self.tree_sprite2 = self.sprite_manager.get_sprite("TREE_002")
        self.tree_sprite2 = pygame.transform.scale(self.tree_sprite2, (32, 32))
        self.tree_sprite3 = self.sprite_manager.get_sprite("TREE_003")
        self.tree_sprite3 = pygame.transform.scale(self.tree_sprite3, (32, 32))
        self.tree_sprite4 = self.sprite_manager.get_sprite("TREE_004")
        self.tree_sprite4 = pygame.transform.scale(self.tree_sprite4, (32, 32))
        self.tree_sprite = {
            "Oak": self.tree_sprite1,
            "Pine": self.tree_sprite2,
            "Birch": self.tree_sprite3,
            "Maple": self.tree_sprite4
        }

    def create_resource(self, resource_type:str) -> Entity | None:
        spawn_area: pg.Rect = pg.Rect(0, 0, 800, 600)  # x, y, width, height
        spawn_area.inflate_ip(-64, -64)  # Avoid spawning too close to edges
        position_x = random.randint(spawn_area.left, spawn_area.right)
        position_y = random.randint(spawn_area.top, spawn_area.bottom)
        position_component = PositionComponent(x=position_x, y=position_y)
        width = 32
        height = 32
        size_component = SizeComponent(width=width, height=height)
        resource_component = ResourceComponent(resource_type=resource_type, resource_amount=100)
        collision_component = CollisionComponent(plane=0)
        health_component = HealthComponent(100)
        entity_count = ResourceFactory.COUNT.get(resource_type, 0)
        ResourceFactory.COUNT[resource_type] = entity_count + 1
        resource_name = f"{resource_type.capitalize()}_{entity_count + 1}"
        
        entity = Entity(resource_name)
        entity.add_component(position_component)
        entity.add_component(size_component)
        entity.add_component(resource_component)
        entity.add_component(collision_component)
        entity.add_component(health_component)

        if resource_type == "tree":
            tree_types = list(self.tree_sprite.keys())
            chosen_tree_type = random.choice(tree_types)
            sprite = self.tree_sprite[chosen_tree_type]
            sprite_component = SpriteComponent(sprite=sprite)
            tree_component = TreeComponent(tree_type=chosen_tree_type)
            entity.add_component(sprite_component)
            entity.add_component(tree_component)
        else:
            sprite_name = resource_type.upper() + "_001"
            sprite = self.sprite_manager.get_sprite(f"{sprite_name}")
            if not sprite:
                sprite = pygame.Surface((32, 32))
                sprite.fill((255, 0, 255))  # Magenta for missing sprite
                
            sprite_component = SpriteComponent(sprite=sprite)
            entity.add_component(sprite_component)    
        return entity

            