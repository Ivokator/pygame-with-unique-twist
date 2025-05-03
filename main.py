import asyncio
import random
import sys
import threading
import time
import typing

import pygame as pg # type: ignore
import pygame_menu as pm

from pygame import Rect
from pygame_widgets.button import ButtonArray # type: ignore

from classes import PlayerBullet
from constants import *

# Initialize
pg.init()

# Screen / Clock

screen: pg.Surface = pg.display.set_mode(RESOLUTION, pg.RESIZABLE | pg.SCALED, vsync=1)
clock: pg.time.Clock = pg.time.Clock()

SCREEN_WIDTH: int
SCREEN_HEIGHT: int

SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()


def quit() -> None:
    """Terminates game."""
    pg.quit()
    sys.exit()

def about() -> None:
    """Shows about menu."""

    menu = pm.Menu('About', 400, 300,
                    theme=mytheme)
    menu.add.label('Game by: Jasper Wan\nPython 3.12.4 - 3.13\nCreated April 2025\nv. DEV', font_size = 30)
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
    """Player class.

    Args:
        x (int): The x-coordinate of the player.
        y (int): The y-coordinate of the player.
        width (int): The width of the player.
        height (int): The height of the player.
    
    Attributes:
        player_rect (pg.Rect): The rectangle representing the player.
        left (bool): Indicates if the player is moving left.
        right (bool): Indicates if the player is moving right.
        speed (int): The speed at which the player moves.
    """
    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        self.left: bool = False
        self.right: bool = False

        self.player_rect: pg.Rect = pg.Rect(x, y, width, height)
        self.speed = 0

    def move(self, dt) -> None:
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
        
        if keys[pg.K_n]:
            # Shoot bullet
            bullet = PlayerBullet(self.player_rect.x, self.player_rect.y, width=10, height=10, direction=1)
            pg.draw.rect(screen, BLUE, bullet.player_bullet_rect)



    def draw(self) -> None:
        """Draws the player."""
        pg.draw.rect(game.surface, BLUE, self.player_rect)

    def draw(self) -> None:
        """Draws the player."""
        pg.draw.rect(game.surface, BLUE, self.player_rect)

class Game(object):
    def __init__(self) -> None:
        self.dt: float = 0.0
        self.running: bool = True
        self.surface: pg.Surface = pg.Surface(RESOLUTION)

    def draw(self) -> None:
        screen_height = screen.get_height()
        screen_width = screen_height * (RESOLUTION[0] / RESOLUTION[1])

        screen_surface = pg.Surface((screen_width, screen_height))

        # Scale up the surface to fit the screen
        pg.transform.scale(
            self.surface,
            (screen_width, screen_height),
            screen_surface)

        # Blit and center surface on the screen
        screen.blit(
            screen_surface,
            ((screen.get_width() - self.surface.get_width()) / 4, 0))

        pg.display.flip()

    def play_game(self) -> None:

        # Game preparation
        pg.display.set_caption(WINDOW_TITLE)

        # Intialize player
        player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4, PLAYER_SIZE, PLAYER_SIZE)




        self.running = True
        while self.running:
            screen.fill(BLACK)
            self.surface.fill(BLACK)

            # Event handling
            self.event()

            # Player movement

            player.move(self.dt)
            player.draw()
            player.player_rect.clamp_ip(self.surface.get_rect())
            
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

    def main_menu(self) -> None:
        """Returns to the main menu."""
        self.running = False
        pg.display.set_caption(WINDOW_TITLE)
        menu = pm.Menu('Game Name', SCREEN_WIDTH * 2 // 3, SCREEN_HEIGHT * 2 // 3,
                        theme=mytheme)

        menu.add.text_input('Name: ', default='John Doe', maxchar=10)
        menu.add.selector('Difficulty: ', [('Hard', 1), ('Easy', 2)])
        menu.add.button('Play', lambda: self.play_game())
        menu.add.button('About', lambda: self.about())
        menu.add.button('Quit', pm.events.EXIT)

        menu.mainloop(screen)
    
    def about(self) -> None:
        """Shows about menu."""

        menu = pm.Menu('About', SCREEN_WIDTH * 2 // 3, SCREEN_HEIGHT * 2 // 3,
                        theme=mytheme)
        menu.add.label('Game by: Jasper Wan\nPython 3.12.4 - 3.13\nCreated April 2025')
        menu.add.button('Return', lambda: self.main_menu())
        menu.mainloop(screen)

    


if __name__ == "__main__":
    game = Game()
    game.main_menu()
