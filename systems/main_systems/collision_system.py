from operator import is_

from regex import E, P
from traitlets import Bool
from ecs import System, Entity, Component, PositionComponent, SizeComponent, CollisionComponent, HealthComponent, DamageComponent
import pygame as pg

class CollisionSystem(System):
    def __init__(self, state):
        super().__init__(state)
        self.required_components: list[str] = ['CollisionComponent', 'PositionComponent', 'SizeComponent']
        
    def update(self, dt):
        for entity in self.state.entities:
            if entity.has_components(self.required_components):
                self.handle_collision(entity, dt)

    def check4(self, entity, other_entity , entityname : list[str] | str, otherentityname : list[str] | str):
        if isinstance(entityname, str):
            entityname = [entityname]
        if isinstance(otherentityname, str):
            otherentityname = [otherentityname]
        if any(entity.name.startswith(name) for name in entityname) and any(other_entity.name.startswith(name) for name in otherentityname):
            return True
        if any(entity.name.startswith(name) for name in otherentityname) and any(other_entity.name.startswith(name) for name in entityname):
            return True
        return False
                
    def handle_collision(self, entity, dt):
        collision_plane = self.get_collition_plane(entity)
        position = self.get_position(entity)
        size = self.get_size(entity)
        rect = pg.Rect(position[0], position[1], size[0], size[1])
        
        for other_entity in self.state.entities:
            if other_entity == entity:  # Skip self-collision
                continue
                
            if other_entity.has_components(self.required_components):
                other_collision_plane = self.get_collition_plane(other_entity)
                
                # Only check collision if on the same plane
                if collision_plane != other_collision_plane:
                    continue
                    
                other_position = self.get_position(other_entity)
                other_size = self.get_size(other_entity)
                other_rect = pg.Rect(other_position[0], other_position[1], other_size[0], other_size[1])
                
                if rect.colliderect(other_rect):
                    self.resolve_collision(entity, other_entity)
                        
    def resolve_collision(self, entity, other_entity):
        entity_name = entity.name
        other_entity_name = other_entity.name

        # Check for bullet-enemy collision
        is_bullet_enemy_collision = (entity_name.startswith("Enemy_") and other_entity_name.startswith(("Bullet_", "TurretBullet_"))) or \
                                   (other_entity_name.startswith("Enemy_") and entity_name.startswith(("Bullet_", "TurretBullet_")))

        if is_bullet_enemy_collision:
            # Determine which is the bullet and which is the enemy
            if entity_name.startswith(("Bullet_", "TurretBullet_")):
                bullet, enemy = entity, other_entity
            else:
                bullet, enemy = other_entity, entity
            self.handle_bullet_enemy_collision(bullet, enemy)

    def handle_bullet_enemy_collision(self, bullet, enemy):
        # Check if enemy has HealthComponent
        if not enemy.has_components(['HealthComponent']):
            print(f"DEBUG: ERROR - Enemy '{enemy.name}' does NOT have HealthComponent!")
            return
        
        # Get damage from bullet's DamageComponent if it exists, otherwise use default
        damage = self.get_damage(bullet) 
        health = self.get_health(enemy)
        health -= damage
        self.set_health(enemy, health)
        
        # Remove bullet from the game
        if bullet in self.state.entities:
            self.state.entities.remove(bullet)
            self.state.state_data["coins"] += 1
