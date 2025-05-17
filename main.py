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

# Images
test_space = pg.image.load(os.path.join("./images/background","test_space.png")).convert()

# Background tiling
test_space_tiles = math.ceil(SCREEN_WIDTH / (test_space.get_width())) + 1

# Camera look-ahead constants
MAX_LOOKAHEAD: float = SCREEN_WIDTH * 0.6 # pixels ahead of player
SMOOTHING: float = 0.04 # 0–1 (higher = snappier)
EDGE_MARGIN = SCREEN_WIDTH * 0.4 # pixels from left/right edge

def quit() -> None:
    """Terminates game."""
    pg.quit()
    sys.exit()

class Player(object):
    """Player character class.

    Attributes:
        rect (pg.Rect): The rectangle representing the player's position and size.
        pos (pg.Vector2): The player's position as a 2D vector.

        velocity (pg.Vector2): The player's velocity as a 2D vector.

        accel_x (float): The player's acceleration in the x direction.
        accel_y (float): The player's acceleration in the y direction.

        max_speed_x (int): The maximum speed of the player in the x direction.
        max_speed_y (int): The maximum speed of the player in the y direction.
        accel_rate (int): The rate of acceleration for the player.
        drag (int): The drag applied to the player's movement.
            - low values give icy movement, high values give sharp and responsive movement 

        direction (int): The direction the player is facing (0 for left, 1 for right).
            - yes i know this is crap
        
        bullets (typing.List[PlayerBullet]): List of bullets fired by the player.
        bullet_cooldown_ms (float): Cooldown time in milliseconds between firing bullets.
        cooldown_timer (int): Timer to track bullet cooldown.
    """
    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        self.rect: pg.Rect = pg.Rect(x, y, width, height)
        self.pos: Vector2 = Vector2(x, y)

        # Physics parameters
        self.velocity: Vector2 = Vector2(0, 0)
        self.accel_x: float = 0.0
        self.accel_y: float = 0.0
        self.max_speed_x: int = 10
        self.max_speed_y: int = 8
        self.accel_rate: int = 30

        # careful that drag does not exceed accel_rate
        self.drag_x: int = 3 
        self.drag_y: int = 20

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
                self.accel_x = -self.drag_x
            elif self.velocity.x < 0:
                self.accel_x = self.drag_x
            else:
                self.accel_x = 0

        # integrate horizontal velocity
        self.velocity.x += self.accel_x * dt
        
        # if input has flipped drag past zero, zero it out
        if abs(self.velocity.x) < (self.drag_x * dt):
            self.velocity.x = 0

        # clamp to max x-axis speed
        self.velocity.x = max(-self.max_speed_x, min(self.velocity.x, self.max_speed_x))

        # VERTICAL ACCELERATION
        if keys[pg.K_w]:
            self.accel_y = -self.accel_rate
        elif keys[pg.K_s]:
            self.accel_y = self.accel_rate
        else:
            if self.velocity.y > 0:
                self.accel_y = -self.drag_y
            elif self.velocity.y < 0:
                self.accel_y = self.drag_y
            else:
                self.accel_y = 0

        self.velocity.y += self.accel_y * dt

        if abs(self.velocity.y) < (self.drag_y * dt):
            self.velocity.y = 0

        # clamp to max y-axis speed
        self.velocity.y = max(-self.max_speed_y, min(self.velocity.y, self.max_speed_y))

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
    
    def update(self, offset_x) -> None:
        """Update the player's position based on the offset."""
        self.rect.x = self.pos.x + offset_x

    def draw(self) -> None:
        """Draws the player."""
        pg.draw.rect(game.surface, WHITE, self.rect)

class Game(object):

    def __init__(self) -> None:
        self.dt: float = 0.0
        self.running: bool = True
        self.top_widget: pg.Surface = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT // 6))
        self.surface: pg.Surface = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - self.top_widget.get_height()))

        self.offset: Vector2 = Vector2(0, 0)
        self.focus_offset: Vector2 = Vector2(0, 0)
        self.current_background = test_space

        self.text_score = PRESS_START_FONT.render("000000", True, WHITE)
        self.mini_map: pg.Surface = pg.Surface((SCREEN_WIDTH // 3, self.top_widget.get_height() - TOP_WIDGET_LINE_THICKNESS // 2))


        self.camera = Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.current_lookahead = 0.0

    def draw(self) -> None:
        screen_height = screen.get_height()
        screen_width = (screen_height * (SCREEN_WIDTH / SCREEN_HEIGHT))

        screen_surface = pg.Surface((screen_width, screen_height - self.top_widget.get_height()))

        # Calculate the offset for the camera
        heading = self.player.pos - self.camera
        self.camera += heading * 0.05

        self.camera_look_ahead()

        self.offset = Vector2(
            -self.camera.x + SCREEN_WIDTH//2,
            -self.camera.y + SCREEN_HEIGHT//2
        )

        pg.transform.scale(
            self.surface,
            (screen_width, screen_height - self.top_widget.get_height()),
            screen_surface)

        self.player.update(int(self.offset.x))
        self.enemy_group.update(int(self.offset.x), screen_surface)

        # Blit and center surface on the screen
        screen.blit(
            screen_surface,
            ((screen.get_width() - self.surface.get_width()) / 4, self.top_widget.get_height()))

        self.render_top_widget()  
        pg.display.flip()

    def camera_look_ahead(self) -> None:
        """
        Smoothly moves the camera towards the player with a look-ahead effect.
        Locks player within an edge margin by locking the camera to the player when necessary.
        """
        desired: float = 0.0

        # If player is moving, set desired look-ahead
        if abs(self.player.velocity.x) > self.speed_threshold:
            desired = math.copysign(MAX_LOOKAHEAD, self.player.velocity.x)

        self.current_lookahead += (desired - self.current_lookahead) * SMOOTHING * 0.5

        # compute player’s x in screen space
        player_screen_x: float = self.player.pos.x + self.offset.x

        violation: float = 0.0
        print(self.player.velocity.x)
        if player_screen_x < EDGE_MARGIN:
            violation = EDGE_MARGIN - player_screen_x
        elif player_screen_x > SCREEN_WIDTH - EDGE_MARGIN:
            violation = (SCREEN_WIDTH - EDGE_MARGIN) - player_screen_x

        # Compute a desired camera X that would correct the violation
        desired_cam_x: float = self.camera.x - violation

        # Smoothly interpolate camera.x toward that desired value
        self.camera.x += (desired_cam_x - self.camera.x) * SMOOTHING

        # Build target camera x with smoothed look-ahead
        target_cam_x: float = self.camera.x + self.current_lookahead
        
        # formula: a = a + (b - a) * t, where a is the current value, b is the desired value, and t is the smoothing factor
        self.camera.x += (target_cam_x - self.camera.x) * SMOOTHING


    def render_top_widget(self) -> None:
        # Draw the top widget
        self.top_widget.fill(DARK_GREY)
        self.mini_map.fill(BLACK)

        pg.draw.line(self.top_widget, WHITE, 
            (0, self.top_widget.get_height()), 
            (self.top_widget.get_width(), self.top_widget.get_height()), TOP_WIDGET_LINE_THICKNESS)


        screen.blit(self.top_widget, (0, 0))
        
        screen.blit(self.text_score, (100, self.top_widget.get_height() - self.text_score.get_height() - 10))

        # Draw elements on mini map
        for enemy in self.enemy_group.enemies:
            # Get position of actual enemy, and scale it down to the mini map
            ...
        screen.blit(self.mini_map, ((self.surface.get_width() // 2) - (self.mini_map.get_width() // 2), 0))

        

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
            (self.offset.x % background_width + i * background_width, 0))



    def play_game(self) -> None:

        # Game preparation
        pg.display.set_caption(WINDOW_TITLE)
        self.enemy_group = EnemyGroup()

        # Intialize player
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4, PLAYER_SIZE, PLAYER_SIZE)
        self.speed_threshold = self.player.max_speed_x * 0.7 # threshold for look-ahead

        self.peaks = map.generate_peaks(SCREEN_WIDTH * 5)
        time_since_last_enemy = 0.0

        self.running = True
        while self.running:
            # Update background
            screen.fill(BLACK)
            self.surface.fill(BLACK)
            self.background()

            # Draw mountains
            map.draw_mountains(self.surface, self.peaks, int(self.offset.x), SCREEN_WIDTH * 5)
        
            # Event handling
            self.player.cooldown_timer += clock.get_time()
            self.event()

            # Draw bullets
            for bullet in self.player.bullets:
                # Delete bullet if it goes off screen
                if bullet.x + SCREEN_WIDTH // 2 < 0 or bullet.x > SCREEN_WIDTH*4:
                    self.player.bullets.remove(bullet)
                    del bullet
                    continue

                bullet.update()
                bullet.draw(self.surface)

            # Draw/update player
            self.player.draw()
            self.player.move(self.dt)

            time_since_last_enemy += self.dt

            if time_since_last_enemy >= 1:
                # Spawn enemy
                enemy = Enemy(random.randint(0, SCREEN_WIDTH), random.randint(0, self.surface.get_height()))

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
        menu.add.label('\nPython 3.12.4 - 3.13\nCreated April 2025\nv. DEV\n-----------------------\nCREDITS:\nIvokator\nSkyVojager')
        menu.add.button('Return', lambda: self.main_menu())
        menu.mainloop(screen)

    


if __name__ == "__main__":

    game = Game()
    game.main_menu()
