from networkx import has_bridges
from torch import ne
from zmq import has
from ecs import System, Entity, Component
from game_state import GameState
import random

class WorkerManagementSystem(System):
    def __init__(self, state: GameState):
        super().__init__(state)
        self.required_components: list[str] = ['WorkerComponent', 'HealthComponent', 'PositionComponent']
        self.worker_chopping_radius = 50
        self.hold_resources = { }
    def update(self, dt):
        for entity in self.state.entities:
            if entity.has_components(self.required_components):
                self.manage_worker(entity, dt)

    def manage_worker(self, entity, dt):
        worker_type = self.get_worker_type(entity)
        health = self.get_health(entity)
        position = self.get_position(entity)
        if worker_type is None:
            return
        elif worker_type == 1:
            new_position = self.move_towards_resource_and_mine_resource(entity, position, dt)
        elif worker_type == 0:
            pass

        if health <= 0:
            self.state.entities.remove(entity)
            print(f"Worker of type {worker_type} has been removed from the game.")
            
    def random_movement(self, entity, position, dt):
        random_x1 = random.uniform(-100, 100)
        random_y1 = random.uniform(-1, 1)
        random_x2 = random.uniform(-10, 10)
        random_y2 = random.uniform(-10, 10)

        new_x = position[0] + random_x1 * dt * 5 + random_x2 * dt * 0.1
        new_y = position[1] + random_y1 * dt * 5 + random_y2 * dt * 0.1
        self.set_position(entity, (new_x, new_y))

    def random_movement_towards_the_player_if_present(self, entity, position, dt):
        random_x1 = random.uniform(-1, 1)
        random_y1 = random.uniform(-1, 1)
        random_x2 = random.uniform(-10, 10)
        random_y2 = random.uniform(-10, 10)

        if Entity.EntityRegistry.get("Player"):
            player_entity = Entity.EntityRegistry["Player"]
            player_position = self.get_position(player_entity)
            direction_x = player_position[0] - position[0]
            direction_y = player_position[1] - position[1]
            length = (direction_x ** 2 + direction_y ** 2) ** 0.5
            if length != 0:
                direction_x /= length
                direction_y /= length
            
            # Calculate velocity for sprite direction detection
            velocity_x = direction_x * 30 + random_x1 * 5 + random_x2 * 0.1
            velocity_y = direction_y * 30 + random_y1 * 5 + random_y2 * 0.1
            self.set_velocity(entity, (velocity_x, velocity_y))
            
            new_x = position[0] + direction_x * 30 * dt + random_x1 * dt * 5 + random_x2 * dt * 0.1
            new_y = position[1] + direction_y * 30 * dt + random_y1 * dt * 5 + random_y2 * dt * 0.1
            self.set_position(entity, (new_x, new_y))
        else:
            print(f"No player entity found. Enemy remains at position {position}.")
        return self.get_position(entity)
    
    def move_towards_resource_and_mine_resource(self, entity, position, dt):
        resource_entity = self.find_nearest_resource(entity, position, dt)
        self.move_towards_resource(entity, resource_entity, dt)

    def find_nearest_resource(self, entity, position, dt):
        resources = [e for e in self.state.entities if e.has_components(['ResourceComponent', 'PositionComponent'])]
        nearest_resource = None
        min_distance = float('inf')
        for resource in resources:
            resource_position = self.get_position(resource)
            distance = ((resource_position[0] - position[0]) ** 2 + (resource_position[1] - position[1]) ** 2) ** 0.5
            if distance < min_distance:
                min_distance = distance
                nearest_resource = resource
        return nearest_resource

    def move_towards_resource(self, entity, resource_entity, dt):
        if resource_entity is None:
            self.random_movement_towards_the_player_if_present(entity, self.get_position(entity), dt)
            return self.get_position(entity)
        
        position = self.get_position(entity)
        resource_position = self.get_position(resource_entity)
        direction_x = resource_position[0] - position[0]
        direction_y = resource_position[1] - position[1]
        length = (direction_x ** 2 + direction_y ** 2) ** 0.5
        if length != 0:
            direction_x /= length
            direction_y /= length
        
        distance_to_tree = length
        speed = 50  # Units per second
        if distance_to_tree > self.worker_chopping_radius:
            # Set velocity for sprite direction detection
            velocity_x = direction_x * speed
            velocity_y = direction_y * speed
            self.set_velocity(entity, (velocity_x, velocity_y))
            
            new_x = position[0] + direction_x * speed * dt
            new_y = position[1] + direction_y * speed * dt
            self.set_position(entity, (new_x, new_y))
        else:
            # Stop moving when mining
            self.set_velocity(entity, (0, 0))
            self.mine_resource(entity, resource_entity, dt)
        return self.get_position(entity)

    def mine_resource(self, entity, resource_entity, dt):
        resource_health = self.get_health(resource_entity)
        damage_per_mine = 30  # Damage per mine
        mine_damage = damage_per_mine * dt
        resource_health -= mine_damage
        resource_type = self.get_resource_type(resource_entity)
        self.state.resource_data[resource_type] = self.state.resource_data.get(resource_type, 0) + mine_damage

        self.set_health(resource_entity, resource_health)
        if resource_health <= 0:
            self.state.entities.remove(resource_entity)
            entity.state_data[resource_type] = entity.state_data.get(resource_type, 0) + 100
            print(f"Resource {resource_type} has been depleted and removed from the game.")
        