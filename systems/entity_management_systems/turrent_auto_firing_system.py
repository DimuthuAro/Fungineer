from ecs import CollisionComponent, System, Entity, PositionComponent, SpriteComponent, VelocityComponent, SizeComponent, TowerComponent, DamageComponent
from game_state import GameState
import pygame as pg
import math

class TurretAutoFiringSystem(System):
    def __init__(self, state: GameState):
        super().__init__(state)
        self.required_components: list[str] = ['TowerComponent', 'PositionComponent']
        
        # Turret type configurations
        self.turret_configs = {
            "Basic": {
                "range": 200,
                "fire_rate": 1.0,  # seconds between shots
                "bullet_speed": 400,
                "damage": 25,
                "bullet_color": (100, 100, 255)
            },
            "Rapid": {
                "range": 150,
                "fire_rate": 0.3,
                "bullet_speed": 500,
                "damage": 15,
                "bullet_color": (255, 165, 0)
            },
            "Heavy": {
                "range": 250,
                "fire_rate": 2.0,
                "bullet_speed": 300,
                "damage": 50,
                "bullet_color": (139, 69, 19)
            },
            "Sniper": {
                "range": 400,
                "fire_rate": 1.5,
                "bullet_speed": 800,
                "damage": 75,
                "bullet_color": (128, 0, 128)
            }
        }
        
        # Track last fire time for each turret
        self.turret_cooldowns = {}
        self.bullet_count = 0
        
    def update(self, dt):
        """Update all turrets - find targets and fire"""
        for entity in self.state.entities:
            if entity.has_components(self.required_components):
                self.update_turret(entity, dt)
    
    def update_turret(self, turret_entity, dt):
        """Update a single turret - find target and fire if possible"""
        turret_type = self.get_tower_type(turret_entity)
        config = self.turret_configs.get(turret_type)
        
        if not config:
            return
        
        # Update cooldown
        turret_id = id(turret_entity)
        if turret_id not in self.turret_cooldowns:
            self.turret_cooldowns[turret_id] = 0.0
        
        self.turret_cooldowns[turret_id] -= dt
        
        # Find nearest enemy in range
        target = self.find_nearest_enemy(turret_entity, config["range"])
        
        # Fire at target if cooldown is ready
        if target and self.turret_cooldowns[turret_id] <= 0:
            self.turret_cooldowns[turret_id] = 0.0
            self.fire_at_target(turret_entity, target, config)
            self.turret_cooldowns[turret_id] = config["fire_rate"]
    
    def find_nearest_enemy(self, turret_entity, max_range):
        """Find the nearest enemy within range of the turret"""
        turret_pos = self.get_position(turret_entity)
        turret_size = self.get_size(turret_entity)
        turret_center_x = turret_pos[0] + turret_size[0] / 2
        turret_center_y = turret_pos[1] + turret_size[1] / 2
        
        nearest_enemy = None
        nearest_distance = float('inf')
        
        for entity in self.state.entities:
            # Check if entity is an enemy
            if entity.name.startswith("Enemy_") and entity.has_components(['PositionComponent', 'SizeComponent']):
                enemy_pos = self.get_position(entity)
                enemy_size = self.get_size(entity)
                enemy_center_x = enemy_pos[0] + enemy_size[0] / 2
                enemy_center_y = enemy_pos[1] + enemy_size[1] / 2
                
                # Calculate distance
                dx = enemy_center_x - turret_center_x
                dy = enemy_center_y - turret_center_y
                distance = math.sqrt(dx * dx + dy * dy)
                
                # Check if in range and closer than previous nearest
                if distance <= max_range and distance < nearest_distance:
                    nearest_enemy = entity
                    nearest_distance = distance
        
        return nearest_enemy
    
    def fire_at_target(self, turret_entity, target_entity, config):
        """Fire a bullet from turret towards the target"""
        turret_pos = self.get_position(turret_entity)
        turret_size = self.get_size(turret_entity)
        turret_center_x = turret_pos[0] + turret_size[0] / 2
        turret_center_y = turret_pos[1] + turret_size[1] / 2
        
        target_pos = self.get_position(target_entity)
        target_size = self.get_size(target_entity)
        target_center_x = target_pos[0] + target_size[0] / 2
        target_center_y = target_pos[1] + target_size[1] / 2
        
        # Calculate direction
        dx = target_center_x - turret_center_x
        dy = target_center_y - turret_center_y
        distance = math.sqrt(dx * dx + dy * dy)
        
        if distance == 0:
            return
        
        # Normalize direction
        dir_x = dx / distance
        dir_y = dy / distance
        
        # Create bullet
        self.create_turret_bullet(
            turret_center_x, 
            turret_center_y, 
            dir_x, 
            dir_y, 
            config["bullet_speed"],
            config["damage"],
            config["bullet_color"]
        )
    
    def create_turret_bullet(self, x, y, dir_x, dir_y, speed, damage, color):
        """Create a bullet entity fired from a turret"""
        bullet = Entity(f"TurretBullet_{self.bullet_count}")
        self.bullet_count += 1
        
        # Calculate velocity
        vel_x = dir_x * speed
        vel_y = dir_y * speed
        
        # Create bullet sprite
        bullet_sprite = pg.Surface((8, 8))
        bullet_sprite.fill(color)
        
        # Add components
        bullet.add_component(PositionComponent(x=x, y=y))
        bullet.add_component(SpriteComponent(sprite=bullet_sprite))
        bullet.add_component(SizeComponent(width=8, height=8))
        bullet.add_component(VelocityComponent(vx=vel_x, vy=vel_y))
        bullet.add_component(DamageComponent(damage=damage))
        bullet.add_component(CollisionComponent(plane=0))
        
        # Add to entities
        self.state.entities.append(bullet)
    
    def render(self, screen):
        """Render turret range indicators (optional debug visualization)"""
        # Optionally draw range circles for turrets
        for entity in self.state.entities:
            if entity.has_components(self.required_components):
                turret_type = self.get_tower_type(entity)
                config = self.turret_configs.get(turret_type)
                
                if config:
                    turret_pos = self.get_position(entity)
                    turret_size = self.get_size(entity)
                    center_x = int(turret_pos[0] + turret_size[0] / 2)
                    center_y = int(turret_pos[1] + turret_size[1] / 2)
                    
                    # Draw range circle (semi-transparent)
                    # Uncomment to see turret ranges
                    # pg.draw.circle(screen, (255, 255, 255), (center_x, center_y), int(config["range"]), 1)
