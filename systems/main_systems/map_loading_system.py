from sympy import false
from ecs import Entity, PositionComponent, SizeComponent, SpriteComponent, System, TileComponent, TooltipComponent
import sprite_manager
import os

class MapLoadingSystem(System):
    def __init__(self, state):
        self.state = state
        self.position = 0, 0
        super().__init__(state)
        self.load_map()
        self.required_components: list[str] = ['TileComponent', 'PositionComponent', 'SizeComponent', 'SpriteComponent']    
        self.map_data = [[0 for _ in range(100)] for _ in range(100)]  # Placeholder for map data
        self.sprite_manager = sprite_manager.SpriteManager()
        for i, map_slice in enumerate(self.map_data):
            for j, tile_value in enumerate(map_slice):
                index = tile_value + (i * len(map_slice)) + j
                tile = Entity(f"Tile_{index}")
                HTileCount = 25  # Placeholder for horizontal tile count
                tile_x = index % HTileCount
                tile_y = index // HTileCount
                tile_sprite = self.sprite_manager.get_sprite(f"GRASS")
                tile.add_component(PositionComponent(x=tile_x * 32, y=tile_y * 32))
                tile.add_component(SpriteComponent(sprite=tile_sprite))
                tile.add_component(TileComponent(tile_type=tile_value))
                tile.add_component(SizeComponent(width=32, height=32))
                self.state.entities.append(tile)
                
    def load_map(self): 
    #Check for save map file exists?
        try:
            with open("assets/maps/map.txt", "r") as f:
                lines = f.readlines()
                self.map_data = [list(map(int, line.strip().split(','))) for line in lines]    
        except Exception as e:
            if e.__class__ == FileNotFoundError:
                #Write default map data to file
                default_map_data = [[0 for _ in range(100)] for _ in range(100)]
                # Create the directory if it doesn't exist
                os.makedirs("assets/maps", exist_ok=True)
                with open("assets/maps/map.txt", "w") as f:
                    for row in default_map_data:
                        f.write(','.join(map(str, row)) + '\n')
                self.map_data = default_map_data    
                print("Map loaded successfully.")
            else:
                print(f"Error loading map: {e}")
          