import time
import pygame as pg

from ecs import AnimatedSpriteComponent, System
from game_state import GameState


class RenderSystem(System):
    def __init__(self, state: GameState):
        super().__init__(state)
        self.rendering_components = [ 'PositionComponent', 'SpriteComponent' ]
        
    def update(self, dt):
        for entity in self.entities:
            if entity.has_components(['AnimatedSpriteComponent']):
                time_since_last_frame = self.get_sprite_time_since_last_frame(entity)
                time_since_last_frame += dt
                self.set_sprite_time_since_last_frame(entity, time_since_last_frame)
                
    def render(self, screen):
        for entity in self.entities:
            if entity.has_components(self.rendering_components):
                position = self.get_position(entity)
                sprite = self.get_sprite(entity)
                screen.blit(sprite, (int(position[0]), int(position[1])))
                
            if entity.has_components(['TextComponent']):
                text = self.get_text(entity)
                position = self.get_position(entity)
                font = pg.font.Font(None, 16)
                text_surface = font.render(text, True, (255, 255, 255))
                text_rect = text_surface.get_rect(center=(position[0] + text_surface.get_width(), position[1] + 20))
                screen.blit(text_surface, text_rect)
                
            # Draw health bars for both static and animated sprites
            if entity.has_components(['HealthComponent', 'PositionComponent']) and (
                entity.has_components(['SpriteComponent']) or entity.has_components(['AnimatedSpriteComponent'])
            ):
                health = self.get_health(entity)
                position = self.get_position(entity)
                # Determine width from sprite or current animation frame
                if entity.has_components(['SpriteComponent']):
                    base_surface = self.get_sprite(entity)
                else:
                    frames = self.get_sprite_frames(entity)
                    # Fallback safely if frames are empty
                    base_surface = frames[0] if frames else pg.Surface((20, 20))
                health_bar_width = base_surface.get_width()
                health_bar_height = 5
                health_percentage = max(0, min(health / 100, 1))
                health_bar_current_width = int(health_bar_width * health_percentage)
                x = int(position[0])
                y = int(position[1])
                health_bar_bg_rect = pg.Rect(x, y - 10, health_bar_width, health_bar_height)
                health_bar_fg_rect = pg.Rect(x, y - 10, health_bar_current_width, health_bar_height)
                pg.draw.rect(screen, (255, 0, 0), health_bar_bg_rect)
                pg.draw.rect(screen, (0, 255, 0), health_bar_fg_rect)
                

            if entity.has_components(['HealthComponent', 'PositionComponent', 'AnimatedSpriteComponent']):
                position = self.get_position(entity)
                current_frame_index = self.get_sprite_current_frame_index(entity)
                time_since_last_frame = self.get_sprite_time_since_last_frame(entity)
                sprite_duration = self.get_sprite_frame_duration(entity)
                frames = self.get_sprite_frames(entity)
                current_frame_count = len(frames) // 4
                direction = self.get_direction_for_sprite(entity)
                directions = {'up': 0, 'down': 1, 'left': 2, 'right': 3}
                if not direction in directions:
                    continue
                
                direction_index = directions[direction]
                start_index = direction_index * current_frame_count
                # Ensure we cycle within the current direction's frames
                local_frame_index = current_frame_index % max(1, current_frame_count)
                frame_index = start_index + local_frame_index
                current_frame = frames[frame_index]
                screen.blit(current_frame, (int(position[0]), int(position[1])))

                # Advance animation when enough time has passed
                if time_since_last_frame >= sprite_duration:
                    new_index = (local_frame_index + 1) % max(1, current_frame_count)
                    self.set_sprite_current_frame_index(entity, new_index)
                    self.set_sprite_time_since_last_frame(entity, 0)
                
            if entity.has_components(['TooltipComponent', 'PositionComponent', 'SizeComponent']):
                is_off = not self.get_tooltip_status(entity)
                if is_off:
                    continue
                tooltip_text = self.get_tooltip(entity)
                position = self.get_position(entity)
                
                if tooltip_text:
                    font = pg.font.SysFont('Arial', 16)
                    text_surface = font.render(tooltip_text, True, (255, 255, 255))
                    text_rect = text_surface.get_rect()
                    text_rect.topleft = (int(position[0]), int(position[1] - text_rect.height - 5))  # Position above the entity
                    
                    # Draw background rectangle
                    bg_rect = pg.Rect(text_rect.left - 2, text_rect.top - 2, text_rect.width + 4, text_rect.height + 4)
                    pg.draw.rect(screen, (0, 0, 0), bg_rect)
                    
                    # Draw the text
                    screen.blit(text_surface, text_rect)
                        
                
                    