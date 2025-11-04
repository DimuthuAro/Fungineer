import pygame as pg
from config import *

from state_manager import StateManager
from game_state import GameState
from play_state import PlayState

pg.init()

is_running = [True]
screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pg.time.Clock()
state_manager = StateManager(is_running, PlayState())

def handle_events():
    for event in pg.event.get():
        state_manager.handle_event(event)

def update():
    dt = clock.tick(FPS) / SECOND
    state_manager.update(dt)

def render():
    screen.fill(BACKGROUND_COLOR)
    state_manager.render(screen)
    pg.display.flip()

while is_running[0]:
    handle_events()
    update()
    render()

pg.quit()