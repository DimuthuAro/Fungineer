from typing import cast     
from ecs import System, HealthComponent
import pygame as pg

class ToolbarSystem(System):
    def __init__(self, state):
        super().__init__(state)
        self.required_components: list[str] = []
        self.coins = 0
        self.wave = 1
        self.enemy_count = 0
        
    def update(self, dt):
        # Update toolbar data from game state
        self.coins = self.state.state_data.get('coins', 0)
        self.wave = self.state.state_data.get('wave', 1)
        
        # Get resource amounts
        self.wood = int(self.state.resource_data.get('tree', 0))
        self.stone = int(self.state.resource_data.get('stone', 0))
        self.water = int(self.state.resource_data.get('pond', 0))
        self.food = int(self.state.resource_data.get('animal', 0))

        # Count enemies
        self.enemy_count = 0
        for entity in self.state.entities:
            if entity.name.startswith("Enemy"):
                self.enemy_count += 1
        
        # Get player health
        player_entity = None
        for entity in self.state.entities:
            if entity.name == "Player":
                player_entity = entity
                break
        
        if player_entity and player_entity.has_components(['HealthComponent']):
            self.player_health = self.get_health(player_entity)
            self.player_max_health = cast(HealthComponent, player_entity.get_component("HealthComponent")).max_health
        else:
            self.player_health = 0
            self.player_max_health = 100
    
    def render(self, screen):
        # Get screen dimensions
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        
        # Create professional toolbar background with gradient effect
        toolbar_height = 70
        toolbar_rect = pg.Rect(0, 0, screen_width, toolbar_height)
        
        # Dark gradient background
        for i in range(toolbar_height):
            shade = 30 + int(i * 0.3)
            pg.draw.line(screen, (shade, shade, shade + 5), (0, i), (screen_width, i))
        
        # Top border highlight
        pg.draw.line(screen, (80, 80, 90), (0, 0), (screen_width, 0), 2)
        # Bottom border shadow
        pg.draw.line(screen, (20, 20, 25), (0, toolbar_height - 1), (screen_width, toolbar_height - 1), 3)
        
        # Fonts - using system font for emoji support
        try:
            # Try to load a system font that supports emojis
            font_emoji = pg.font.SysFont('segoeuisymbol,segoeui,arial', 28)
            font_medium = pg.font.SysFont('segoeuisymbol,segoeui,arial', 28)
            font_small = pg.font.SysFont('segoeuisymbol,segoeui,arial', 22)
        except:
            # Fallback to default font
            font_emoji = pg.font.Font(None, 32)
            font_medium = pg.font.Font(None, 28)
            font_small = pg.font.Font(None, 22)
        
        # Starting position
        current_x = 15
        spacing = 10
        
        # === LEFT SECTION: Currency ===
        self._render_stat_box(screen, current_x, 12, "💰", str(self.coins), (255, 215, 0), font_emoji, font_small)
        current_x += 120
        
        # Vertical divider
        pg.draw.line(screen, (80, 80, 90), (current_x, 15), (current_x, toolbar_height - 15), 2)
        current_x += spacing + 10
        
        # === MIDDLE LEFT: Resources ===
        resources = [
            ("🌲", self.wood, (101, 166, 77)),
            ("🪨", self.stone, (158, 158, 158)),
            ("💧", self.water, (64, 164, 223)),
            ("🍖", self.food, (235, 137, 52)),
        ]
        
        for emoji, amount, color in resources:
            self._render_stat_box(screen, current_x, 12, emoji, str(amount), color, font_emoji, font_small)
            current_x += 90
        
        # Vertical divider
        pg.draw.line(screen, (80, 80, 90), (current_x, 15), (current_x, toolbar_height - 15), 2)
        current_x += spacing + 10
        
        # === MIDDLE: Wave & Enemies ===
        self._render_stat_box(screen, current_x, 12, "🌊", str(self.wave), (100, 200, 255), font_emoji, font_small)
        current_x += 120
        
        self._render_stat_box(screen, current_x, 12, "👾", str(self.enemy_count), (255, 100, 100), font_emoji, font_small)
        current_x += 120
        
        # === RIGHT SECTION: Health Bar ===
        health_bar_x = screen_width - 270
        health_bar_y = 22
        health_bar_width = 220
        health_bar_height = 26
        
        # Health label with heart emoji
        heart_text = font_emoji.render("❤", True, (255, 100, 100))
        screen.blit(heart_text, (health_bar_x - 42, 16))
        
        # Health bar background with rounded corners effect
        health_bg_rect = pg.Rect(health_bar_x, health_bar_y, health_bar_width, health_bar_height)
        pg.draw.rect(screen, (60, 20, 20), health_bg_rect, border_radius=4)
        
        # Health bar fill
        health_percentage = self.player_health / self.player_max_health if self.player_max_health > 0 else 0
        health_width = int((health_bar_width - 4) * health_percentage)
        
        if health_percentage > 0.6:
            health_color = (76, 175, 80)  # Green
        elif health_percentage > 0.3:
            health_color = (255, 193, 7)  # Amber
        else:
            health_color = (244, 67, 54)  # Red
        
        if health_width > 0:
            health_fill_rect = pg.Rect(health_bar_x + 2, health_bar_y + 2, health_width, health_bar_height - 4)
            pg.draw.rect(screen, health_color, health_fill_rect, border_radius=3)
        
        # Health bar border
        pg.draw.rect(screen, (200, 200, 200), health_bg_rect, 2, border_radius=4)
        
        # Health text with shadow
        health_text_str = f"{int(self.player_health)}/{int(self.player_max_health)}"
        health_text = font_small.render(health_text_str, True, (0, 0, 0))
        health_text_main = font_small.render(health_text_str, True, (255, 255, 255))
        text_rect = health_text.get_rect(center=(health_bar_x + health_bar_width // 2, health_bar_y + health_bar_height // 2))
        screen.blit(health_text, (text_rect.x + 1, text_rect.y + 1))
        screen.blit(health_text_main, text_rect)
    
    def _render_stat_box(self, screen, x, y, icon, value, color, font_icon, font_small, label=None):
        """Helper method to render a stat box with icon and value"""
        # Icon
        icon_text = font_icon.render(icon, True, (200, 200, 200))
        screen.blit(icon_text, (x, y + 2))
        
        # Calculate icon width for proper spacing
        icon_width = icon_text.get_width()
        
        # Value with subtle shadow
        value_shadow = font_small.render(value, True, (0, 0, 0))
        value_text = font_small.render(value, True, color)
        screen.blit(value_shadow, (x + icon_width + 6, y + 7))
        screen.blit(value_text, (x + icon_width + 5, y + 6))
        
        # Optional label below
        if label:
            label_font = pg.font.Font(None, 16)
            label_text = label_font.render(label, True, (150, 150, 150))
            screen.blit(label_text, (x, y + 30))
