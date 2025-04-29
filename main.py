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

PLAYER_SIZE: int = 50

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

def about() -> None:
    """Shows about menu."""

    menu = pm.Menu('About', 400, 300,
                    theme=mytheme)
    menu.add.label('Game by: Jasper Wan\nPython 3.12.4 - 3.13\nCreated April 2025', font_size = 30)
    menu.add.button('Return', lambda: main())
    menu.mainloop(screen)


def main() -> None:
    """Main menu for game."""
    pg.display.set_caption(WINDOW_TITLE)
    menu = pm.Menu('Game Name', 400, 300,
                    theme=mytheme)

    menu.add.text_input('Name: ', default='John Doe', maxchar=10)
    menu.add.selector('Difficulty: ', [('Hard', 1), ('Easy', 2)])
    menu.add.button('Play', lambda: Game())
    menu.add.button('About', lambda: about())
    menu.add.button('Quit', pm.events.EXIT)

    menu.mainloop(screen) # Run

class Player(object):
    def __init__(self, x, y, width, height) -> None:
        self.left = False
        self.right = False

        self.player_rect: pg.Rect = Rect(x, y, width, height)

    def move(self, dt):
        # Player input
        keys = pg.key.get_pressed()

        if keys[pg.K_a]:
            self.player_rect.x -= int(300 * dt)

        if keys[pg.K_d]:
            self.player_rect.x += int(300 * dt)

        if keys[pg.K_w]:
            self.player_rect.y -= int(300 * dt)

        if keys[pg.K_s]:
            self.player_rect.y += int(300 * dt)

class Game(object):
    def __init__(self) -> None:
        self.dt: float = 0.0
        self.running: bool = True
        self.surface: pg.Surface = pg.Surface(RESOLUTION)

        self.window_width: int = SCREEN_WIDTH
        self.window_height: int = SCREEN_HEIGHT

        self.play_game()

    def draw(self) -> None:
        self.surface.blit(screen, (0, 0))

        transformed_screen = pg.transform.scale(screen,(self.window_width, self.window_height))
        screen.blit(transformed_screen, (0, 0))
        pg.display.update()

    def play_game(self) -> None:

        # Game preparation
        pg.display.set_caption(WINDOW_TITLE)

        player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4, PLAYER_SIZE, PLAYER_SIZE)

        while self.running:
            screen.fill(BLACK)

            # Event handling
            self.event()

            # Player movement

            player.move(self.dt)
            pg.draw.rect(self.surface, BLUE, player.player_rect)
            
            player.player_rect.clamp_ip(screen.get_rect())
            
            # Draw screen
            self.draw()
            self.dt = clock.tick(FRAMES_PER_SECOND) / 1000

        quit()

    def event(self) -> None:
        """Handles events."""
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_ESCAPE:
                    self.running = False
    


if __name__ == "__main__":
    main()
