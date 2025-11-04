from turtle import back
import pygame as pg

class SpriteManager:
    def __init__(self):
        self.default_file_name = "sprites.pkl"
        self.backup_file_name = "sprites_backup.pkl"
        self.sprites : dict[str, pg.Surface] = self.get_default_saved_sprites()
        self.sprites : dict[str, pg.Surface] = self.remap_sprites(self.sprites)
        self.player_sprite_names = ["north", "south", "east", "west"]
        
        self.gui = None

    def remap_sprites(self, sprites: dict[str, pg.Surface]) -> dict[str, pg.Surface]:
        # Remapping logic (identity mapping here)
        remapped_sprites = sprites
        return remapped_sprites

    def get_default_saved_sprites(self) -> dict[str, pg.Surface]:
        sprites : dict[str, pg.Surface] = {}
        sprites = self.load_sprite_data()
        if sprites == {}:
            # If no PNGs are present, try loading from backup pickle
            sprites = self.load_backup_sprite_data()
        return sprites

    def load_sprite_data(self, file_path: str="assets/sprites/") -> dict[str, pg.Surface]:
        import os
        sprites : dict[str, pg.Surface] = {}
        if not os.path.exists(file_path):
            return sprites

        # Ensure pygame is initialized (not strictly required for loading, but safe)
        if not pg.get_init():
            pg.init()
        # convert_alpha requires a display surface; fromstring doesn't, but we'll keep it safe
        if not pg.display.get_surface():
            pg.display.set_mode((1, 1))

        for file_name in os.listdir(file_path):
            if file_name.endswith(".png"):
                sprite_name = file_name[:-4]  # Remove .png extension
                full_path = os.path.join(file_path, file_name)
                try:
                    sprite = pg.image.load(full_path).convert_alpha()
                    sprites[sprite_name] = sprite
                except Exception as e:
                    print(f"Failed to load sprite '{file_name}': {e}")
        return sprites

    def return_sprite(self, name: str) -> pg.Surface | None:
        return self.sprites.get(name, None)
    
    def load_sprite_from_file(self, name: str, file_path: str):
        # Ensure pygame is initialized with video mode
        if not pg.get_init():
            pg.init()
        if not pg.display.get_surface():
            pg.display.set_mode((1, 1))  # Minimal display for image operations
        sprite = pg.image.load(file_path).convert_alpha()
        self.sprites[name] = sprite
        
    def load_sprite_list_from_files(self, sprite_list: dict[str, str]):
        # Ensure pygame is initialized with video mode
        if not pg.get_init():
            pg.init()
        if not pg.display.get_surface():
            pg.display.set_mode((1, 1))  # Minimal display for image operations
        for name, file_path in sprite_list.items():
            sprite = pg.image.load(file_path).convert_alpha()
            self.sprites[name] = sprite
            
    def RunSpriteManagerGUI(self):
        if self.gui is None:
            import sprite_manager_gui
            self.gui = sprite_manager_gui.SpriteManagerGUI(self)

    def add_sprite(self, name: str, sprite: pg.Surface):
        self.sprites[name] = sprite

    def get_sprite(self, name: str) -> pg.Surface:
        default_sprite = pg.Surface((50, 50))
        default_sprite.fill((255, 0, 255))  # Magenta for missing sprite
        return self.sprites.get(name, default_sprite)

    def get_sprite_set(self, base_name: str) -> list[pg.Surface]:
        sprite_set = []
        for key in self.sprites.keys():
            if key.startswith(base_name):
                sprite_set.append(self.sprites[key])
        return sprite_set

    def remove_sprite(self, name: str):
        if name in self.sprites:
            del self.sprites[name]
            
    def save_sprite_data(self, file_path: str="assets/sprites/"):
        import os
        if os.path.exists(file_path) == False:
            os.makedirs(file_path)

        for sprite_name, sprite in self.sprites.items():
            self.check_for_unwanted_files()
            if isinstance(sprite_name, str) and isinstance(sprite, pg.Surface):
                check_for_existing = os.path.join(file_path, f"{sprite_name}.png")
                if os.path.exists(check_for_existing):
                    os.remove(check_for_existing)
                    print(f"Overwriting existing sprite file: {check_for_existing}")
                pg.image.save(sprite, f"{file_path}/{sprite_name}.png")  # Save individual sprite as image file
            else:
                print(f"Skipping invalid sprite entry: {sprite_name, sprite}")

    def check_for_unwanted_files(self):
        import os
        list_of_all_existing_files = os.listdir("assets/sprites/") # List all files in the sprites directory
        list_of_current_sprite_files = [f"{sprite_name}.png" for sprite_name in self.sprites.keys()] # Current sprite file names
        for existing_file in list_of_all_existing_files:
            if existing_file not in list_of_current_sprite_files:
                unwanted_path = os.path.join("assets/sprites/", existing_file)
                os.remove(unwanted_path)
                print(f"Removed outdated sprite file: {unwanted_path}")

    def save_sprite_data_as_backup(self, file_path: str="assets/sprites/"):
        import os, pickle
        # Ensure pygame is initialized (not strictly required for tostring, but safe)
        if not pg.get_init():
            pg.init()

        # Keep backups out of the PNG folder so cleanup doesn't delete them
        if os.path.exists(file_path) == False:
            os.makedirs(file_path)

        backup_file = os.path.join(file_path, "backup.pkl")

        # Serialize Surfaces into pickle-safe dict of bytes + metadata
        backup_data: dict[str, dict] = {}
        for name, surf in self.sprites.items():
            if not isinstance(name, str) or not isinstance(surf, pg.Surface):
                continue
            w, h = surf.get_size()
            # Use RGBA to preserve per-pixel alpha
            pixels = pg.image.tostring(surf, "RGBA")
            backup_data[name] = {
                "size": (w, h),
                "mode": "RGBA",
                "pixels": pixels,
                "alpha": surf.get_alpha(),      # surface alpha (if any)
                "colorkey": surf.get_colorkey() # color key (if any)
            }

        if os.path.exists(backup_file):
            os.remove(backup_file)
            print(f"Overwriting existing backup file: {backup_file}")

        with open(backup_file, "wb") as f:
            pickle.dump(backup_data, f)

        print(f"Sprite data backed up to: {backup_file}")

    def load_backup_sprite_data(self, file_path: str="assets/sprites/backup.pkl") -> dict[str, pg.Surface]:
        import os, pickle
        sprites : dict[str, pg.Surface] = {}
        if not os.path.exists(file_path):
            return sprites

        # Ensure pygame is initialized for potential format conversions
        if not pg.get_init():
            pg.init()
        # convert_alpha requires a display surface; fromstring doesn't, but we'll keep it safe
        if not pg.display.get_surface():
            pg.display.set_mode((1, 1))

        with open(file_path, "rb") as f:
            data: dict[str, dict] = pickle.load(f)

        for name, meta in data.items():
            try:
                size = tuple(meta["size"])
                mode = meta.get("mode", "RGBA")
                pixels = meta["pixels"]
                surf = pg.image.fromstring(pixels, size, mode)
                # Restore alpha/colorkey if present
                if meta.get("alpha") is not None:
                    surf.set_alpha(meta["alpha"])
                if meta.get("colorkey") is not None:
                    surf.set_colorkey(meta["colorkey"])
                sprites[name] = surf
            except Exception as e:
                print(f"Failed to restore sprite '{name}' from backup: {e}")
        return sprites
            
    def save_n_exit(self):
        if self.gui is not None:
            self.gui.save_n_exit()
            self.save_sprite_data()
            self.save_sprite_data_as_backup()
        pg.quit()


if __name__ == "__main__":
    sprite_manager = SpriteManager()
    sprite_manager.RunSpriteManagerGUI()