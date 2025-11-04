from re import A
from shutil import move
from typing import cast
from cycler import V
import pygame as pg
from regex import E
from game_state import GameState
from sprite_manager import SpriteManager

from systems.main_systems.render_system import RenderSystem
from systems.main_systems.map_loading_system import MapLoadingSystem
from systems.main_systems.input_system import InputSystem
from systems.main_systems.movement_system import MovementSystem 
from systems.main_systems.collision_system import CollisionSystem

from systems.entity_management_systems.shooting_system import ShootingSystem
from systems.entity_management_systems.turrent_auto_firing_system import TurretAutoFiringSystem
from systems.entity_management_systems.worker_management_system import WorkerManagementSystem
from systems.entity_management_systems.random_resource_generation_system import RandomResourceGenerationSystem

from systems.ui_systems.toolbar_system import ToolbarSystem
from systems.ui_systems.tooltip_system import TooltipSystem
from systems.ui_systems.turret_placement_system import TurretPlacementSystem

from ecs import AnimatedSpriteComponent, Entity, FactoryComponent, TextComponent
from ecs import PositionComponent,SpawnerComponent, SpriteComponent, VelocityComponent
from ecs import ControllableComponent, EnemyComponent, HealthComponent, CollisionComponent, System
from ecs import SizeComponent, WorkerComponent
from factory.entity_factory import EntityFactory
import re

class PlayState(GameState):
    def enter(self):
        self.is_pausable = True
        self.main_systems_list = [
            "InputSystem",
            "MovementSystem",
            "CollisionSystem",
            "MapLoadingSystem",
            "RenderSystem"
        ]
        self.entity_management_systems_list = [
            "ShootingSystem",
            "TurretAutoFiringSystem",
            "WorkerManagementSystem",
            "RandomResourceGenerationSystem"
        ]
        self.ui_systems_list = [
            "ToolbarSystem",
            "TooltipSystem",
            "TurretPlacementSystem"
        ]
        self.systems : dict[str,System] = self.systems_initialization()
        self.sprite_manager = SpriteManager()
        self.entity_factory = EntityFactory(self)
        self.text = ""
        self.create_entities()
        self.shoot_interval = 0.2  # seconds between shot
        self.state_data["coins"] = 100
        self.state_data["wave"] = 0
        
    def systems_initialization(self) -> dict[str, System]:
        systems = {}
        # Initialize main systems
        main_systems = self.system_initialization(self.main_systems_list)
        systems.update(main_systems)
        print("Initialized Main Systems")
        
        # Initialize entity management systems
        entity_management_systems = self.system_initialization(self.entity_management_systems_list)
        systems.update(entity_management_systems)
        print("Initialized Entity Management Systems")

        # Initialize UI systems
        ui_systems = self.system_initialization(self.ui_systems_list)
        systems.update(ui_systems)
        print("Initialized UI Systems")

        return systems    
        
    def get_system_class(self, system_name: str):

        # Convert CamelCase to snake_case
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', system_name)
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

        return s2

    def create_entities(self):
        sprites = self.sprite_manager.sprites
        self.entity_factory.create_entity("player", position=(200,200), sprite_names="player_004", size=(64,64))
        self.entity_factory.create_entity("Worker", position=(100,100), sprite_names=["worker_000","worker_001","worker_002","worker_003","worker_004","worker_005",
                                                                                      "worker_006","worker_007","worker_008","worker_009","worker_010","worker_011",
                                                                                      "worker_012","worker_013","worker_014","worker_015","worker_016","worker_017",
                                                                                      "worker_018","worker_019","worker_020","worker_021","worker_022","worker_023"], size=(64,64))
        

        self.entity_factory.create_entity("Enemy", position=(300,300), sprite_names="enemy_000", size=(32,32))

    def system_initialization(self, systems_list: list[str]) -> dict[str, System]:
        systems = {}
        for system_name in systems_list:
            system_class_name = self.get_system_class(system_name)
            if system_class_name:
                system_class = globals().get(system_name)
                if system_class:
                    systems[system_name] = system_class(self)
                    print(f"Initialized system: {system_class_name}")
                else:
                    print(f"Warning: Class '{system_name}' not found in globals")
            else:
                print(f"Warning: Unknown system '{system_name}'")
        return systems    

    def exit(self):
        print("Exiting Play State")
        self.sprite_manager.save_n_exit()
    
