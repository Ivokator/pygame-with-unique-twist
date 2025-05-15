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
from pygame.math import Vector2
from pygame_widgets.button import ButtonArray # type: ignore

import map

from classes import PlayerBullet, EnemyBullet, Enemy, EnemyGroup
from constants import *

# Initialize
pg.init()

# Screen / Clock

screen: pg.Surface = pg.display.set_mode(RESOLUTION, pg.RESIZABLE | pg.SCALED, vsync=1)
clock: pg.time.Clock = pg.time.Clock()

SCREEN_WIDTH: int
SCREEN_HEIGHT: int

SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()

GAMEPLAY_WIDTH: int = SCREEN_WIDTH
GAMEPLAY_HEIGHT: int = SCREEN_HEIGHT * 9 // 10

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
    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        self.rect = pg.Rect(x, y, width, height)
        self.pos = Vector2(x, y)

        # Physics parameters
        self.velocity = Vector2(0, 0)
        self.accel_x = 0.0
        self.accel_y = 0.0

        self.max_speed = 5
        self.accel_rate = 50
        self.drag = 20

        self.direction = 0  # left:0, right:1

        self.bullets: typing.List[PlayerBullet] = []
        self.bullet_cooldown_ms: float = 100
        self.cooldown_timer: int = 0

    def move(self, dt) -> None:
        keys = pg.key.get_pressed()

        # HORIZONTAL ACCELERATION 
        if keys[pg.K_a]:
            self.accel_x = -self.accel_rate
            self.direction = 1
        elif keys[pg.K_d]:
            self.accel_x = self.accel_rate
            self.direction = 0
        else:
            # no input -> apply drag opposite to current velocity
            if self.velocity.x > 0:
                self.accel_x = -self.drag
            elif self.velocity.x < 0:
                self.accel_x = self.drag
            else:
                self.accel_x = 0

        # integrate horizontal velocity
        self.velocity.x += self.accel_x * dt
        
        # if input has flipped drag past zero, zero it out
        if abs(self.velocity.x) < (self.drag * dt):
            self.velocity.x = 0

        # clamp to max speed
        self.velocity.x = max(-self.max_speed, min(self.velocity.x, self.max_speed))

        # VERTICAL ACCELERATION
        if keys[pg.K_w]:
            self.accel_y = -self.accel_rate
        elif keys[pg.K_s]:
            self.accel_y = self.accel_rate
        else:
            if self.velocity.y > 0:
                self.accel_y = -self.drag
            elif self.velocity.y < 0:
                self.accel_y = self.drag
            else:
                self.accel_y = 0

        self.velocity.y += self.accel_y * dt

        if abs(self.velocity.y) < (self.drag * dt):
            self.velocity.y = 0

        print(self.accel_x, self.accel_y)

        self.velocity.y = max(-self.max_speed, min(self.velocity.y, self.max_speed))
        self.pos += self.velocity

        # assigns Vector2 to Tuple[int, int], but works
        self.rect.center = self.pos # type: ignore


    def fire_bullet(self) -> None:
        """Fires a bullet."""
        # Create a bullet at the player's position
        # and set its angle and speed
        if self.cooldown_timer > self.bullet_cooldown_ms:
            self.cooldown_timer = 0
            bullet = PlayerBullet(self.rect.x, self.rect.y + (self.rect.height // 2), width=10, height=10, angle = self.direction * -180, speed=30)
            self.bullets.append(bullet)
    
    def switch_direction(self) -> None:
        """Switches the direction of the player."""
        if self.direction == 0:
            self.direction = 1
        else:
            self.direction = 0

    def draw(self) -> None:
        """Draws the player."""
        pg.draw.rect(game.surface, WHITE, self.rect)

class Game(object):

    def __init__(self) -> None:
        self.dt: float = 0.0
        self.running: bool = True
        self.surface: pg.Surface = pg.Surface(RESOLUTION)

        self.offset: Vector2 = Vector2(0, 0)
        self.current_background = test_space

        self.top_widget: pg.Surface = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT // 6))
        self.text_score = DEFAULT_FONT.render("000000", True, WHITE)

        self.camera = Vector2(RESOLUTION[0] // 2, RESOLUTION[1] // 2)


    def draw(self) -> None:
        screen_height = screen.get_height()
        screen_width = screen_height * (RESOLUTION[0] / RESOLUTION[1])

        screen_surface = pg.Surface((screen_width, screen_height))

        # Calculate the offset for the camera
        heading = self.player.pos - self.camera
        self.camera += heading * 0.05
        self.offset = -self.camera + Vector2(RESOLUTION[0] // 2, RESOLUTION[1] // 2)

        # Scale up the surface to fit the screen
        pg.transform.scale(
            self.surface,
            (screen_width, screen_height),
            screen_surface)

        self.enemy_group.update(int(self.offset[0]), screen_surface)

        # Blit and center surface on the screen
        screen.blit(
            screen_surface,
            ((screen.get_width() - self.surface.get_width()) / 4, 0))

        self.render_top_widget()  

        pg.display.flip()

    def render_top_widget(self) -> None:
        # Draw the top widget
        self.top_widget.fill(DARK_GREY)
        screen.blit(self.top_widget, (0, 0))

        #self.top_widget.blit(self.text_score, (SCREEN_WIDTH // 2 - self.text_score.get_width() // 2, SCREEN_HEIGHT // 20))

    def background(self) -> None:
        # Draw the background

        surface_width = self.surface.get_width()
        surface_height = self.surface.get_height()

        background_width = self.current_background.get_width()
        background_height = self.current_background.get_height()

        # Transform background to right size
        pg.transform.scale(self.current_background, (surface_width, surface_height))

        scaled_background = pg.transform.scale(self.current_background, (background_width, surface_height))

        # Scroll background
        for i in range(-1, test_space_tiles + 1):
            self.surface.blit(scaled_background, 
            (self.offset[0] % background_width + i * background_width, 0))



    def play_game(self) -> None:

        # Game preparation
        pg.display.set_caption(WINDOW_TITLE)
        self.enemy_group = EnemyGroup()

        # Intialize player
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4, PLAYER_SIZE, PLAYER_SIZE)

        self.mountain_noise_data = map.generate_mountains()
        time_since_last_enemy = 0.0

        self.running = True
        while self.running:
            # Update background
            screen.fill(BLACK)
            self.surface.fill(BLACK)
            self.background()

            # Draw mountains
            map.draw_mountains(self.surface, self.mountain_noise_data, SCREEN_HEIGHT, self.offset[0])
        
            # Event handling
            self.player.cooldown_timer += clock.get_time()
            self.event()

            # Draw bullets
            for bullet in self.player.bullets:
                bullet.update()
                bullet.draw(self.surface)

            # Draw/update player
            self.player.draw()
            self.player.move(self.dt)

            time_since_last_enemy += self.dt

            if time_since_last_enemy >= 1:
                # Spawn enemy
                enemy = Enemy(random.randint(0, SCREEN_WIDTH), random.randint(0, SCREEN_HEIGHT))

                # Spawn no more than 5 enemies at once
                if len(self.enemy_group.enemies) < 5:
                    self.enemy_group.add_enemy(enemy)
                else:
                    # Remove the oldest enemy
                    self.enemy_group.enemies.pop(0)
                    self.enemy_group.remove(self.enemy_group.enemies[0])

                time_since_last_enemy = 0
                


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
