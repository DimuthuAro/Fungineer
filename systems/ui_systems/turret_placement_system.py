from ecs import System, Entity, PositionComponent, SpriteComponent, SizeComponent, TowerComponent, HealthComponent
import pygame as pg

class TurretPlacementSystem(System):
    def __init__(self, state):
        super().__init__(state)
        self.required_components: list[str] = []
        self.placement_mode = False
        self.selected_turret_type = "Basic"
        self.preview_turret = None
        self.turret_costs = {
            "Basic": 50,
            "Rapid": 100,
            "Heavy": 150,
            "Sniper": 200
        }
        self.grid_size = 40  # Size of placement grid
        
    def handle_event(self, event):
        """Handle mouse and keyboard events for turret placement"""
        if event.type == pg.KEYDOWN:
            # Press '1' for Basic turret
            if event.key == pg.K_1:
                self.select_turret("Basic")
            # Press '2' for Rapid turret
            elif event.key == pg.K_2:
                self.select_turret("Rapid")
            # Press '3' for Heavy turret
            elif event.key == pg.K_3:
                self.select_turret("Heavy")
            # Press '4' for Sniper turret
            elif event.key == pg.K_4:
                self.select_turret("Sniper")
            # Press ESC to cancel placement
            elif event.key == pg.K_ESCAPE:
                self.cancel_placement()
                
        elif event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                # Check if clicking on turret selection UI buttons
                if self.check_ui_button_click(event.pos):
                    return  # Button click handled
                
                # Otherwise, try to place turret if in placement mode
                if self.placement_mode:
                    self.place_turret()
            elif event.button == 3:  # Right click
                self.cancel_placement()
    
    def check_ui_button_click(self, mouse_pos):
        """Check if mouse click is on a turret selection button and handle it"""
        screen = pg.display.get_surface()
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        # UI dimensions (must match render_turret_selection_ui)
        ui_height = 80
        ui_y = screen_height - ui_height
        button_width = 120
        button_height = 60
        padding = 10
        
        mouse_x, mouse_y = mouse_pos
        
        # Check if click is within UI area
        if mouse_y < ui_y:
            return False
        
        # Check each button
        turret_types = ["Basic", "Rapid", "Heavy", "Sniper"]
        current_coins = self.state.state_data.get("coins", 0)
        
        for i, turret_type in enumerate(turret_types):
            x = padding + i * (button_width + padding)
            y = ui_y + padding
            
            button_rect = pg.Rect(x, y, button_width, button_height)
            
            if button_rect.collidepoint(mouse_x, mouse_y):
                # Check if player can afford this turret
                cost = self.turret_costs[turret_type]
                if current_coins >= cost:
                    self.select_turret(turret_type)
                    return True
                else:
                    print(f"Not enough coins for {turret_type} turret! Need {cost}, have {current_coins}")
                    return True
        
        return False
    
    def select_turret(self, turret_type: str):
        """Enable placement mode for the selected turret type"""
        cost = self.turret_costs.get(turret_type, 0)
        current_coins = self.state.state_data.get("coins", 0)
        
        if current_coins >= cost:
            self.placement_mode = True
            self.selected_turret_type = turret_type
            print(f"Turret placement mode: {turret_type} (Cost: {cost} coins)")
        else:
            print(f"Not enough coins! Need {cost}, have {current_coins}")
    
    def cancel_placement(self):
        """Cancel turret placement mode"""
        self.placement_mode = False
        self.selected_turret_type = None
        print("Turret placement cancelled")
    
    def get_grid_position(self, mouse_x, mouse_y):
        """Snap mouse position to grid"""
        grid_x = (mouse_x // self.grid_size) * self.grid_size
        grid_y = (mouse_y // self.grid_size) * self.grid_size
        return grid_x, grid_y
    
    def is_valid_placement(self, x, y):
        """Check if the position is valid for turret placement"""
        # Check if position is below toolbar (assuming toolbar height is 60)
        if y < 60:
            return False
        
        # Check if there's already a turret at this position
        for entity in self.state.entities:
            if entity.has_components(['TowerComponent', 'PositionComponent']):
                pos = self.get_position(entity)
                size = self.get_size(entity) if entity.has_components(['SizeComponent']) else (self.grid_size, self.grid_size)
                
                # Check for overlap
                if (abs(pos[0] - x) < size[0] and abs(pos[1] - y) < size[1]):
                    return False
        
        return True
    
    def place_turret(self):
        """Place the selected turret at the current mouse position"""
        if not self.placement_mode:
            return
        
        mouse_x, mouse_y = pg.mouse.get_pos()
        grid_x, grid_y = self.get_grid_position(mouse_x, mouse_y)
        
        # Check if placement is valid
        if not self.is_valid_placement(grid_x, grid_y):
            print("Invalid turret placement location!")
            return
        
        # Check if player has enough coins
        cost = self.turret_costs[self.selected_turret_type] 
        current_coins = self.state.state_data.get("coins", 0)
        
        if current_coins < cost:
            print(f"Not enough coins! Need {cost}, have {current_coins}")
            return
        
        # Create the turret
        turret_count = sum(1 for e in self.state.entities if e.name.startswith("Turret"))
        turret = Entity(f"Turret_{self.selected_turret_type}_{turret_count}")
        
        # Create turret sprite based on type
        turret_sprite = self.create_turret_sprite(self.selected_turret_type)
        
        # Add components
        turret.add_component(PositionComponent(x=grid_x, y=grid_y))
        turret.add_component(SpriteComponent(sprite=turret_sprite))
        turret.add_component(SizeComponent(width=self.grid_size, height=self.grid_size))
        turret.add_component(TowerComponent(TowerType=self.selected_turret_type))
        turret.add_component(HealthComponent(health=100))
        
        # Add to entities
        self.state.entities.append(turret)
        
        # Deduct coins
        self.state.state_data["coins"] = current_coins - cost
        
        print(f"Placed {self.selected_turret_type} turret at ({grid_x}, {grid_y}). Coins remaining: {self.state.state_data['coins']}")
        
        # Exit placement mode
        self.cancel_placement()
    
    def create_turret_sprite(self, turret_type: str):
        """Create a sprite for the turret based on its type"""
        sprite = pg.Surface((self.grid_size, self.grid_size))
        
        # Different colors for different turret types
        if turret_type == "Basic":
            sprite.fill((100, 100, 255))  # Blue
        elif turret_type == "Rapid":
            sprite.fill((255, 165, 0))    # Orange
        elif turret_type == "Heavy":
            sprite.fill((139, 69, 19))    # Brown
        elif turret_type == "Sniper":
            sprite.fill((128, 0, 128))    # Purple
        else:
            sprite.fill((150, 150, 150))  # Gray
        
        # Draw a simple turret shape
        center = self.grid_size // 2
        pg.draw.circle(sprite, (50, 50, 50), (center, center), center - 5)
        pg.draw.rect(sprite, (30, 30, 30), (center - 3, 5, 6, center))
        
        return sprite
    
    def update(self, dt):
        """Update turret placement preview"""
        pass
    
    def render(self, screen):
        """Render placement preview and turret selection UI"""
        if self.placement_mode:
            # Draw placement preview
            mouse_x, mouse_y = pg.mouse.get_pos()
            grid_x, grid_y = self.get_grid_position(mouse_x, mouse_y)
            
            # Check if placement is valid
            is_valid = self.is_valid_placement(grid_x, grid_y)
            
            # Create preview sprite
            preview = pg.Surface((self.grid_size, self.grid_size))
            preview.set_alpha(128)  # Semi-transparent
            
            if is_valid:
                preview.fill((0, 255, 0))  # Green for valid
            else:
                preview.fill((255, 0, 0))  # Red for invalid
            
            screen.blit(preview, (grid_x, grid_y))
            
            # Draw grid lines at placement position
            pg.draw.rect(screen, (255, 255, 255) if is_valid else (255, 0, 0), 
                        (grid_x, grid_y, self.grid_size, self.grid_size), 2)
        
        # Draw turret selection UI at bottom of screen
        self.render_turret_selection_ui(screen)
    
    def render_turret_selection_ui(self, screen):
        """Render the turret selection buttons at the bottom of the screen"""
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        # UI dimensions
        ui_height = 80
        ui_y = screen_height - ui_height
        button_width = 120
        button_height = 60
        padding = 10
        
        # Draw background
        ui_rect = pg.Rect(0, ui_y, screen_width, ui_height)
        pg.draw.rect(screen, (30, 30, 30), ui_rect)
        pg.draw.rect(screen, (80, 80, 80), ui_rect, 2)
        
        # Turret types to display
        turret_types = ["Basic", "Rapid", "Heavy", "Sniper"]
        turret_keys = ["1", "2", "3", "4"]
        
        font = pg.font.Font(None, 24)
        small_font = pg.font.Font(None, 20)
        
        current_coins = self.state.state_data.get("coins", 0)
        
        # Draw each turret button
        for i, (turret_type, key) in enumerate(zip(turret_types, turret_keys)):
            x = padding + i * (button_width + padding)
            y = ui_y + padding
            
            cost = self.turret_costs[turret_type]
            can_afford = current_coins >= cost
            is_selected = self.placement_mode and self.selected_turret_type == turret_type
            
            # Button background
            if is_selected:
                button_color = (100, 200, 100)
            elif can_afford:
                button_color = (60, 60, 60)
            else:
                button_color = (40, 40, 40)
            
            button_rect = pg.Rect(x, y, button_width, button_height)
            pg.draw.rect(screen, button_color, button_rect)
            pg.draw.rect(screen, (255, 255, 255) if can_afford else (100, 100, 100), button_rect, 2)
            
            # Turret icon (small preview)
            icon_size = 30
            icon_x = x + (button_width - icon_size) // 2
            icon_y = y + 5
            icon_sprite = self.create_turret_sprite(turret_type)
            icon_sprite = pg.transform.scale(icon_sprite, (icon_size, icon_size))
            screen.blit(icon_sprite, (icon_x, icon_y))
            
            # Turret name
            name_text = font.render(turret_type, True, (255, 255, 255) if can_afford else (100, 100, 100))
            name_rect = name_text.get_rect(center=(x + button_width // 2, y + button_height - 20))
            screen.blit(name_text, name_rect)
            
            # Cost
            cost_text = small_font.render(f"{cost} 🪙", True, (255, 215, 0) if can_afford else (100, 100, 50))
            cost_rect = cost_text.get_rect(center=(x + button_width // 2, y + button_height - 5))
            screen.blit(cost_text, cost_rect)
            
            # Key hint
            key_text = small_font.render(f"[{key}]", True, (150, 150, 150))
            screen.blit(key_text, (x + 5, y + 5))
        
        # Draw instructions
        if self.placement_mode:
            instruction_text = font.render("Left Click to Place | Right Click/ESC to Cancel", True, (255, 255, 255))
        else:
            instruction_text = font.render("Press 1-4 to select turret type", True, (200, 200, 200))
        
        instruction_rect = instruction_text.get_rect(center=(screen_width // 2, ui_y - 20))
        screen.blit(instruction_text, instruction_rect)
