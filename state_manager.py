import pygame as pg
from ecs import Entity
from config import *
from game_state import GameState
    
class StateManager:
    def __init__(self, is_running: list[bool], initial_state: GameState):
        self.is_running = is_running
        self.is_paused = False
        self.paused_screen = None
        self.previously_paused = False
        self.current_state: GameState = initial_state
        self.states: list[GameState] = [initial_state]
        self.current_state.enter()
        self.is_quit_message_shown = False
        self.font_small = self.init_font(24)
        self.font_medium = self.init_font(36)
        self.font_large = self.init_font(72)
        self.yes_button = pg.Rect(100, 130, 80, 40)
        self.no_button = pg.Rect(220, 130, 80, 40)

    def init_font(self, size: int):
        try:
            return pg.font.Font("Arial.ttf", size)
        except FileNotFoundError:
            return pg.font.Font(None, size)

    def add_state(self, new_state: GameState):
        self.states.append(new_state)
        
    def set_current_state(self, new_state: GameState):
        self.current_state.exit()
        self.current_state = new_state
        self.current_state.enter()
        
    def add_and_set_current_state(self, new_state: GameState):
        self.add_state(new_state)
        self.set_current_state(new_state)
    
    def handle_event(self, event):
        if self.is_quit_message_shown:
            if self.confirmed_quit(event) is True:
                self.is_running[0] = False
            elif self.confirmed_quit(event) is False:
                self.is_quit_message_shown = False
                if not self.previously_paused:
                    self.is_paused = False
            return
        
        if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
            if self.current_state.is_pausable:
                if self.is_paused:
                    self.previously_paused = True
                else:
                    self.previously_paused = False
                self.is_paused = True
                self.handle_quit()
            else:
                self.is_running[0] = False
        
        if self.current_state.is_pausable and event.type == pg.KEYDOWN and event.key == pg.K_p:
            self.is_paused = not self.is_paused
            
        if not self.is_paused:
            self.paused_screen = None
            self.current_state.handle_event(event)
        
    def update(self, dt):
        if not self.is_paused:
            self.current_state.update(dt)
    
    def handle_quit(self):
        if not self.is_quit_message_shown:
            self.is_quit_message_shown = True
    
    def render_quit_message(self, screen):
        message_box = pg.Surface((400, 200), pg.SRCALPHA)
        message_box_background_color = (127, 127, 127, 170)
        message_box_foreground_color = (0, 0, 0)
        pg.draw.rect(message_box, message_box_background_color, (0, 0, 400, 200), border_radius=10)
        pg.draw.rect(message_box, message_box_foreground_color, (0, 0, 400, 200), border_radius=10, width = 3)

        text_surf = self.font_small.render("Are you sure you want to quit?", True, message_box_foreground_color)
        text_rect = text_surf.get_rect(center=(message_box.get_width() // 2, 80))
        message_box.blit(text_surf, text_rect)

        yes_button_color = (27, 100, 27) if self.yes_button.collidepoint(pg.mouse.get_pos()[0] - (SCREEN_WIDTH // 2 - 200), pg.mouse.get_pos()[1] - (SCREEN_HEIGHT // 2 - 100)) else (27, 150, 27)
        no_button_color = (100, 27, 27) if self.no_button.collidepoint(pg.mouse.get_pos()[0] - (SCREEN_WIDTH // 2 - 200), pg.mouse.get_pos()[1] - (SCREEN_HEIGHT // 2 - 100)) else (150, 27, 27)

        pg.draw.rect(message_box, yes_button_color, self.yes_button, border_radius=5)
        pg.draw.rect(message_box, no_button_color, self.no_button, border_radius=5)

        yes_text = self.font_medium.render("Yes", True, message_box_foreground_color)
        no_text = self.font_medium.render("No", True, message_box_foreground_color)
        self.yes_button.center = (self.yes_button.x + self.yes_button.width // 2, self.yes_button.y + self.yes_button.height // 2)
        self.no_button.center = (self.no_button.x + self.no_button.width // 2, self.no_button.y + self.no_button.height // 2)
        yes_text_rect = yes_text.get_rect(center=self.yes_button.center)
        no_text_rect = no_text.get_rect(center=self.no_button.center)
        message_box.blit(yes_text, yes_text_rect)
        message_box.blit(no_text, no_text_rect)

        screen.blit(message_box, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 - 100))

    def confirmed_quit(self, event):
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            yes_button_screen_pos = pg.Rect(
                self.yes_button.x + (SCREEN_WIDTH // 2 - 200), 
                self.yes_button.y + (SCREEN_HEIGHT // 2 - 100), 
                self.yes_button.width, self.yes_button.height)
            no_button_screen_pos = pg.Rect(
                self.no_button.x + (SCREEN_WIDTH // 2 - 200), 
                self.no_button.y + (SCREEN_HEIGHT // 2 - 100), 
                self.no_button.width, self.no_button.height)
            mouse_pos = pg.mouse.get_pos()
            print(mouse_pos, yes_button_screen_pos, no_button_screen_pos)
            if yes_button_screen_pos.collidepoint(mouse_pos):
                return True
            if no_button_screen_pos.collidepoint(mouse_pos):
                return False
            
        if event.type == pg.QUIT :
            return True
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_y:
                return True
            elif event.key == pg.K_n or event.key == pg.K_ESCAPE:
                return False
        return None

    def _set_paused_overlay(self, screen):
        self.paused_screen = screen.copy()
        self.current_state.render(self.paused_screen)
        overlay = pg.Surface((screen.get_width(), screen.get_height()), pg.SRCALPHA)
        overlay.fill(PAUSED_BACKGROUND)  # Semi-transparent
        self.paused_screen.blit(overlay, (0, 0))

    def _render_paused_screen(self, screen):
        screen.blit(self.paused_screen, (0, 0))

    def _render_paused_text(self):
        if self.paused_screen:
            text = self.font_large.render("Paused", True, (255, 255, 255))
            text_rect = text.get_rect(center=(self.paused_screen.get_width() // 2, self.paused_screen.get_height() // 2))
            self.paused_screen.blit(text, text_rect)   
        
    def render(self, screen):
        if not self.is_paused:
            self.current_state.render(screen)
        else:
            if self.paused_screen is None:
                self._set_paused_overlay(screen)

            self._render_paused_screen(screen)

            if self.is_quit_message_shown:
                self.render_quit_message(screen)
            else:
                self._render_paused_text()
      
    def next_state(self):
        current_index = self.states.index(self.current_state)
        next_index = (current_index + 1) % len(self.states)
        self.set_current_state(self.states[next_index])
        
    def previous_state(self):
        current_index = self.states.index(self.current_state)
        previous_index = (current_index - 1) % len(self.states)
        self.set_current_state(self.states[previous_index])