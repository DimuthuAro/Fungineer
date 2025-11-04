from typing import cast

from ecs import System, Entity, Component, PositionComponent, SizeComponent, TooltipComponent
import pygame as pg

class TooltipSystem(System):
    def __init__(self, state):
        super().__init__(state)
        self.state = state
        self.required_components: list[str] = ['TooltipComponent', 'PositionComponent', 'SizeComponent']
        
    def get_displacement_from_mouse(self, entity: Entity) -> float:
        mouse_pos = pg.mouse.get_pos()
        position = self.get_position(entity)
        size = self.get_size(entity)
        rect = pg.Rect(position,size)
        rect_center = rect.center
        distance = ((mouse_pos[0] - rect_center[0]) ** 2 + (mouse_pos[1] - rect_center[1]) ** 2) ** 0.5
        return distance

    def check_for_nearest_entity_to_mouse(self):
        entities_with_tooltips = [entity for entity in self.state.entities if entity.has_components(self.required_components)]
        if not entities_with_tooltips:
            return
        
        entities_without_tiles = [entity for entity in entities_with_tooltips if not entity.name.startswith("Tile_")]
        if not entities_without_tiles:
            return

        nearest_entity = self.find_minimum(entities_without_tiles)
        
        for entity in self.state.entities:
            if not entity.has_components(self.required_components):
                continue
            if entity == nearest_entity:
                self.set_tooltip_status(entity, True)
            else:
                self.set_tooltip_status(entity, False)


    def find_minimum(self, array) -> Entity | None:
        min_value = float('inf')
        min_entity = None
        for entity in array:
            distance = self.get_displacement_from_mouse(entity)
            if distance < min_value:
                min_value = distance
                min_entity = entity
        return min_entity
        

    def update(self, dt):
        self.check_for_nearest_entity_to_mouse()

    def render(self, screen: pg.Surface):
        for entity in self.state.entities:
            if not (
                entity and
                entity.has_components(self.required_components)
            ):  return
            
            if not self.get_tooltip_status(entity):
                continue
            tooltip_is_on = self.get_tooltip_status(entity)
            if not tooltip_is_on:
                continue
            if not self.get_tooltip(entity):
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
            
                    