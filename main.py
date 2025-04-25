import asyncio
import random
import sys
import threading
import time
import typing

import pygame as pg
import pygame_widgets as pw  # type: ignore
import pygame_menu as pm

from pygame.locals import Rect
from pygame_widgets.button import ButtonArray # type: ignore

# Initialize
pg.init()

# ------------------------ GAME CONSTANTS ------------------------
WINDOW_TITLE: str = "some game"
FRAMES_PER_SECOND: int = 100
RESOLUTION: tuple[int, int] = (800, 600)

INPUT_KEYS: list[int] = [pg.K_f, pg.K_g, pg.K_h, pg.K_j]

# -----------------------------------------------------------------

# Basic colours
WHITE: tuple[int, ...] = (255, 255, 255)
BLACK: tuple[int, ...] = (0, 0, 0)
BLUE: tuple[int, ...] = (0, 0, 255)
GREEN: tuple[int, ...] = (0, 255, 0)
RED: tuple[int, ...] = (255, 0, 0)

DARK_GREY: tuple[int, ...] = (64, 64, 64)
DARKER_GREY: tuple[int, ...] = (32, 32, 32)

# Screen / Clock

screen: pg.Surface = pg.display.set_mode(RESOLUTION)
clock: pg.time.Clock = pg.time.Clock()

SCREEN_WIDTH: int
SCREEN_HEIGHT: int

SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()

# SCORE TEXT
SYSFONT = pg.font.get_default_font()
DEFAULT_FONT = pg.font.SysFont(SYSFONT, 24)


mytheme = pm.themes.Theme(title_bar_style=pm.widgets.MENUBAR_STYLE_UNDERLINE_TITLE,
                          title_font_color = DARK_GREY,
                          selection_color = BLACK,
                          fps = FRAMES_PER_SECOND,
                          widget_font = pm.font.FONT_MUNRO,
                          title_font = pm.font.FONT_8BIT,
                          widget_font_size = 40
                    
                          )

def quit() -> None:
    """Terminates game."""
    pg.quit()
    sys.exit()

def main() -> None:
    """Main menu for game."""
    menu = pm.Menu('Game Name', 400, 300,
                    theme=mytheme)

    menu.add.text_input('Name: ', default='John Doe', maxchar=10)
    menu.add.selector('Difficulty: ', [('Hard', 1), ('Easy', 2)])
    menu.add.button('Play', lambda: play_game())
    menu.add.button('Quit', pm.events.EXIT)

    menu.mainloop(screen) # Run


def play_game() -> None:
    dt: float = 0.0
    running: bool = True

    # Game preparation
    pg.display.set_caption(WINDOW_TITLE)

    while running:
        screen.fill(BLACK)

        # Event handling
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

        # Draw screen
        pg.display.flip()
        dt = clock.tick(FRAMES_PER_SECOND) / 1000

    quit()


if __name__ == "__main__":
    main()
