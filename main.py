import asyncio
import math
import os
import random
import sys
import threading
import time
import typing

import pygame as pg # type: ignore
import pygame_menu as pm

from pygame import Rect
#from pygame_widgets.button import ButtonArray # type: ignore

from classes import PlayerBullet, EnemyBullet, Enemy
from constants import *

# Initialize
pg.init()

# Screen / Clock

screen: pg.Surface = pg.display.set_mode(RESOLUTION, pg.RESIZABLE | pg.SCALED, vsync=1)
clock: pg.time.Clock = pg.time.Clock()

SCREEN_WIDTH: int
SCREEN_HEIGHT: int

SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()

# Images
test_space = pg.image.load(os.path.join("./images/background","test_space.png")).convert()


# Background tiling
test_space_tiles = math.ceil(SCREEN_WIDTH / (test_space.get_width())) + 1


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
        rect (pg.Rect): The rectangle representing the player.
        left (bool): Indicates if the player is moving left.
        right (bool): Indicates if the player is moving right.
        speed (int): The speed at which the player moves.
    """
    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        self.left: bool = False
        self.right: bool = False

        self.rect: pg.Rect = pg.Rect(x, y, width, height)
        self.speed = 0

        self.direction: int = 0 # left: 0, right: 1

        self.bullets: typing.List[PlayerBullet] = []
        self.bullet_cooldown_ms: float = 100
        self.cooldown_timer: int = 0

    def move(self, dt) -> None:
        # Player input
        keys = pg.key.get_pressed()

        if keys[pg.K_a]:
            #self.rect.x -= int(300 * dt)
            self.direction = 1
            game.background_scroll += int(300 * dt)

        if keys[pg.K_d]:
            #self.rect.x += int(300 * dt)
            self.direction = 0
            game.background_scroll -= int(300 * dt)

        if keys[pg.K_w]:
            self.rect.y -= int(300 * dt)

        if keys[pg.K_s]:
            self.rect.y += int(300 * dt)
            
        print(game.offset)
        
        #print(self.rect.x, self.rect.y)
        

    def fire_bullet(self) -> None:
        """Fires a bullet."""
        # Create a bullet at the player's position
        # and set its angle and speed
        if self.cooldown_timer > self.bullet_cooldown_ms:
            self.cooldown_timer = 0
            bullet = PlayerBullet(self.rect.x, self.rect.y + (self.rect.height // 2), width=10, height=10, angle = self.direction * -180, speed=10)
            self.bullets.append(bullet)
    
    def switch_direction(self) -> None:
        """Switches the direction of the player."""
        if self.direction == 0:
            self.direction = 1
        else:
            self.direction = 0

    def draw(self) -> None:
        """Draws the player."""
        pg.draw.rect(game.surface, BLUE, self.rect)

class Game(object):

    def __init__(self) -> None:
        self.dt: float = 0.0
        self.running: bool = True
        self.surface: pg.Surface = pg.Surface(RESOLUTION)

        self.background_scroll: int = 0 # Background scroll counter
        self.current_background = test_space
        
        self.enemies: typing.List[Enemy] = []
        
        
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

    def background(self) -> None:
        # Draw the background

        surface_width = self.surface.get_width()
        surface_height = self.surface.get_height()

        background_width = self.current_background.get_width()
        background_height = self.current_background.get_height()

        # Transform background to right size
        pg.transform.scale(self.current_background, (surface_width, surface_height))


        for i in range(test_space_tiles):
            self.surface.blit(self.current_background, 
                (self.background_scroll + i * background_width, 
                surface_height // 2 - self.current_background.get_height() // 2))
            
        for enemy in self.enemies:
            enemy.update(self.background_scroll)

        # Reset scroll if background has looped
        if abs(self.background_scroll) >= background_width:
            self.background_scroll = 0

        #print(self.background_scroll)

    def play_game(self) -> None:

        # Game preparation
        pg.display.set_caption(WINDOW_TITLE)

        # Intialize game
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4, PLAYER_SIZE, PLAYER_SIZE)
<<<<<<< Updated upstream
=======
        time_since_last_enemy = 0.0
        time_since_last_bullet = 0.0
>>>>>>> Stashed changes

        self.running = True
        while self.running:
            # Update background
            screen.fill(BLACK)
            self.surface.fill(BLACK)
            self.background()

        
            # Event handling
            self.player.cooldown_timer += clock.get_time()
            self.event()

            # Draw player bullets
            for bullet in self.player.bullets:
                bullet.update()
                bullet.draw(self.surface)
<<<<<<< Updated upstream
                
=======
            
            #Draw enemies
            for enemy in self.enemy_group.enemies:
                enemy.update(int(self.offset))
                enemy.draw(self.surface)
                enemy.fire_bullet(self.player.rect.x, self.player.rect.y)
            
>>>>>>> Stashed changes
            # Draw enemy bullets
            for enemy in self.enemy_group.enemies:
                for bullet in enemy.bullets:
                    bullet.update()
                    bullet.draw(self.surface)
<<<<<<< Updated upstream
=======
            
>>>>>>> Stashed changes

            # Draw/update player
            self.player.draw()
            self.player.move(self.dt)

<<<<<<< Updated upstream
            #spawn enemies
            if random.randint(1, 100) == 1:
=======
            time_since_last_enemy += self.dt
            time_since_last_bullet += self.dt
            

            if time_since_last_enemy >= 1:
                # Spawn enemy
>>>>>>> Stashed changes
                enemy = Enemy(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT))
                self.enemies.append(enemy)
                
<<<<<<< Updated upstream
            # Draw enemies
            for enemy in self.enemies:
                #enemy.update()
                enemy.draw(self.surface)
=======
                
            # Update enemy group
            for enemy in self.enemy_group.enemies:
                enemy.angle_to_player(self.player.rect.x, self.player.rect.y)
                
            # Fire enemy bullets
            if time_since_last_bullet >= 3:
                for enemy in self.enemy_group.enemies:
                    enemy_bullet = enemy.fire_bullet(self.player.rect.x, self.player.rect.y)
                    enemy.bullets.append(enemy_bullet)  # Append to the correct enemy's bullet list
                time_since_last_bullet = 0
                    
>>>>>>> Stashed changes

            self.player.rect.clamp_ip(self.surface.get_rect())
            
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

                # Fire bullet
                elif event.key == pg.K_n:
                    self.player.fire_bullet()


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
