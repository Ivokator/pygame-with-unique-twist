import asyncio
import random
import sys
import threading
import time
import typing

import pygame as pg
import pygame_widgets as pw  # type: ignore

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

def quit() -> None:
    """Terminates game and stops code."""
    pg.quit()
    sys.exit()

def main() -> None:
    """Main menu for game."""
    dt: float = 0.0
    running: bool = True

    # Game preparation
    pg.display.set_caption(WINDOW_TITLE)

    while running:
        screen.fill(BLACK)

        # Menu title
        title_text: pg.Surface = DEFAULT_FONT.render("Main Menu", True, WHITE)
        title_rect: pg.Rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))


        # Menu options
        menu_options: list[str] = ["Play", "Settings", "Quit"]
        buttonArray = ButtonArray(
            screen,
            SCREEN_WIDTH // 2 - 100,  # X-coordinate
            SCREEN_HEIGHT // 2 - 100,  # Y-coordinate
            200,  # Width
            300,  # Height
            (1, 3),  # grid shape
            border=10,  # Distance between buttons and edge of array
            texts=("Play", "Settings", "Quit"),  # Sets the texts of each button (counts left to right then top to bottom)
            onClicks=(lambda: play_game(), lambda: print('2'), lambda: quit()),
            font=DEFAULT_FONT,
            fontSize=40
        )
        
        # Input events
        for event in (events := pg.event.get()):
            if event.type == pg.QUIT:
                running = False

        # Draw screen
        screen.blit(title_text, title_rect)

        pw.update(events)
        pg.display.flip()
        dt = clock.tick(FRAMES_PER_SECOND) / 1000

    quit()


def play_game() -> None:
    dt: float = 0.0
    running: bool = True

    # Game preparation
    pg.display.set_caption(WINDOW_TITLE)

    while running:
        screen.fill(BLACK)

        # Quit game
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

        # Draw screen
        pg.display.flip()
        dt = clock.tick(FRAMES_PER_SECOND) / 1000

    pg.quit()


if __name__ == "__main__":
    main()
