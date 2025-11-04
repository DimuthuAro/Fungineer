from turtle import st
from ecs import System, Entity, Component
from game_state import GameState
import random   
from factory.resource_factory import ResourceFactory

class RandomResourceGenerationSystem(System):
    def __init__(self, state: GameState):
        super().__init__(state)
        self.resource_factory = ResourceFactory()
        self.spawn_interval = 1.0  # seconds
        self.time_since_last_spawn = 0.0
        state.max_resource_data = {"wood": 50, "stone": 30, "water": 20, "food": 40}
        state.resource_data = {"wood": 0, "stone": 0, "water": 0, "food": 0}
        
    def update(self, dt):
        self.time_since_last_spawn += dt
        print(f"Time since last spawn: {self.time_since_last_spawn}")
        if self.time_since_last_spawn >= self.spawn_interval:
            self.spawn_resources()
            self.time_since_last_spawn = 0.0
            
    def spawn_resources(self):
        resource_types = self.state.max_resource_data.keys()
        for resource_type in resource_types:
            current_amount = self.state.resource_data.get(resource_type, 0)
            max_amount = self.state.max_resource_data.get(resource_type, 0)
            if current_amount < max_amount:
                new_entity = self.resource_factory.create_resource(resource_type)
                print(f"Spawned new resource: {resource_type}")
                if new_entity:
                    self.state.entities.append(new_entity)
        
        