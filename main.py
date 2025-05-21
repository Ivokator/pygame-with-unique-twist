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
#from pygame_widgets.button import ButtonArray # type: ignore

import map
import misc

from classes import Player, PlayerBullet, EnemyBullet, Enemy, EnemyGroup, Humanoid, HumanoidGroup, HumanoidState, MiniMap

from constants import *

# Initialize
pg.init()

# Screen / Clock

screen: pg.Surface = pg.display.set_mode(RESOLUTION, pg.RESIZABLE | pg.SCALED, vsync=1)
clock: pg.time.Clock = pg.time.Clock()

# Images
test_space = pg.image.load(os.path.join("./images/background","test_space.png")).convert()

# Background tiling
test_space_tiles = math.ceil(SCREEN_WIDTH / (test_space.get_width())) + 1

# Camera look-ahead constants
MAX_LOOKAHEAD: float = SCREEN_WIDTH * 0.5 # pixels ahead of player
SMOOTHING: float = 0.03 # 0–1 (higher = snappier)
EDGE_MARGIN = SCREEN_WIDTH * 0.3 # pixels from left/right edge

def quit() -> None:
    """Terminates game."""
    pg.quit()
    sys.exit()


class Game(object):
    def __init__(self) -> None:
        self.dt: float = 0.0
        self.running: bool = True
        self.top_widget: pg.Surface = pg.Surface((SCREEN_WIDTH, TOP_WIDGET_HEIGHT))
        self.surface: pg.Surface = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT - TOP_WIDGET_HEIGHT))
        self.gameplay_surface = pg.Surface((SCREEN_WIDTH, GAMEPLAY_HEIGHT))

        self.offset: Vector2 = Vector2(0, 0)
            
        self.background_scroll: float | int = 0  # Background scroll counter
        self.previousoffsets: typing.List[float] = []
            
        self.current_background = test_space
        self.offset_change: float = 0.0

        self.text_score = PRESS_START_FONT.render("000000", True, WHITE)
        self.mini_map: MiniMap = MiniMap()
        self.mini_map_clock: float = 0.0

        self.camera = Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.current_lookahead = 0.0

        self.particles: list[pg.sprite.Group] = []

        self.initial_humanoids: int = 30

    def draw(self) -> None:
        
        self.enemy_group.update(self.offset.x, self.player.pos, self.gameplay_surface)
        self.humanoid_group.update(self.offset.x, self.gameplay_surface)
        self.player.update(self.offset.x)

        # Blit and center surface on the screen
        screen.blit(
            self.gameplay_surface,
            ((screen.get_width() - self.surface.get_width()) / 4, TOP_WIDGET_HEIGHT))
             
        self.render_top_widget()

        pg.display.flip()

    def camera_look_ahead(self) -> None:
        """
        Smoothly moves the camera towards the player with a look-ahead effect.
        Locks player within an edge margin by locking the camera to the player when necessary.
        """
        desired: float = 0.0

        # if player is moving, set desired look-ahead
        if abs(self.player.velocity.x) > self.speed_threshold:
            desired = math.copysign(MAX_LOOKAHEAD, self.player.velocity.x)

        self.current_lookahead += (desired - self.current_lookahead) * SMOOTHING * 0.5

        # compute player’s x in screen space
        player_screen_x: float = self.player.pos.x + self.offset.x

        # detect how much the player is over the edge margins
        violation: float = 0.0
        if player_screen_x < EDGE_MARGIN:
            violation = EDGE_MARGIN - player_screen_x
        elif player_screen_x > SCREEN_WIDTH - EDGE_MARGIN:
            violation = (SCREEN_WIDTH - EDGE_MARGIN) - player_screen_x

        # correct the violation with a desired value
        desired_cam_x: float = self.camera.x - violation

        # smoothly interpolate camera.x toward that desired value
        self.camera.x += (desired_cam_x - self.camera.x) * SMOOTHING

        # build target camera x with smoothed look-ahead
        target_cam_x: float = self.camera.x + self.current_lookahead

        # formula: a = a + (b - a) * t, where a is the current value, b is the desired value, and t is the smoothing factor
        self.player.lookahead_compensation = (target_cam_x - self.camera.x) * SMOOTHING
        self.camera.x += (target_cam_x - self.camera.x) * SMOOTHING

    def render_top_widget(self) -> None:
        # Draw the top widget
        self.top_widget.fill(DARKER_GREY)

        pg.draw.line(self.top_widget, WHITE, 
            (0, TOP_WIDGET_HEIGHT), 
            (self.top_widget.get_width(), TOP_WIDGET_HEIGHT), TOP_WIDGET_LINE_THICKNESS)

        screen.blit(self.top_widget, (0, 0))
        screen.blit(self.text_score, (100, TOP_WIDGET_HEIGHT - self.text_score.get_height() - 10))

        
        self.mini_map.add(*self.enemy_group.sprites())
        self.mini_map.update(self.offset.x)
        
        screen.blit(self.mini_map.surface, ((self.surface.get_width() // 2) - (self.mini_map.surface.get_width() // 2), 0))

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

    def screen_rescale(self) -> None:
        pg.transform.scale(
            self.surface,
            (SCREEN_WIDTH, GAMEPLAY_HEIGHT),
            self.gameplay_surface)
        
    def calculate_offset(self) -> None:
        """Calculates the camera offset based on player position and camera position.

        The offset is used to center the player on the screen and create a parallax effect.
        Changes self.offset and self.previousoffsets.
        """
        heading = self.player.pos - self.camera
        self.camera += heading * 0.05

        self.offset = Vector2(
            -self.camera.x + SCREEN_WIDTH//2,
            -self.camera.y + SCREEN_HEIGHT//2
        )

        # Calculate change in offset (d_offset)
        self.previousoffsets.append(self.offset.x)
        if len(self.previousoffsets) > 2:
            self.previousoffsets.pop(0)
            self.offset_change = self.previousoffsets[1] - self.previousoffsets[0]

    def play_game(self) -> None:
        # Game preparation
        pg.display.set_caption(WINDOW_TITLE)
        self.enemy_group: EnemyGroup = EnemyGroup()

        # Intialize player
        self.player: Player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4, PLAYER_SIZE, PLAYER_SIZE)
        self.speed_threshold: float = self.player.max_speed_x * 0.7 # threshold for look-ahead
        self.mini_map.add(self.player)

        self.peaks: list[tuple[int, int]] = map.generate_peaks(WORLD_WIDTH)
        self.mini_map.create_mountain_representation(self.peaks, WORLD_WIDTH)
        time_since_last_enemy: float = 0.0
        test_spam_enemy_fire_time: float = 0.0

        self.humanoid_group: HumanoidGroup = HumanoidGroup()
        self.generate_humanoids()

        self.running = True

        while self.running:
            self.calculate_offset()
            self.camera_look_ahead()

            # Update background
            screen.fill(BLACK)
            self.surface.fill(BLACK)
            self.background()

            # Draw mountains
            map.draw_mountains(self.surface, self.peaks, self.offset.x, WORLD_WIDTH)

            # Event handling
            self.player.cooldown_timer += clock.get_time()
            self.event()

            # Draw player bullets
            for bullet in self.player.bullets:
                # off-screen culling
                if bullet.x < SCREEN_WIDTH * -2 or bullet.x > SCREEN_WIDTH * 2:
                    self.player.bullets.remove(bullet)
                    del bullet
                    continue

                bullet.update()
                bullet.draw(self.surface)

            # Spawn enemies
            time_since_last_enemy += self.dt

            if time_since_last_enemy >= 2:
                # Spawn enemy
                enemy = Enemy(random.randint(-SCREEN_WIDTH, SCREEN_WIDTH*2), random.randint(0, self.surface.get_height()))

                # Spawn no more than 5 enemies at once
                if len(self.enemy_group.sprites()) < 5:
                    self.enemy_group.add(enemy)
                else:
                    # Remove the oldest enemy
                    old: pg.sprite.Sprite = self.enemy_group.sprites()[0]
                    old.kill()
                    del old

                time_since_last_enemy = 0

            # Draw enemies
            for enemy in self.enemy_group.sprites():
                enemy.update(self.offset.x, self.player.pos)

                # off-screen culling
                if enemy.pos.x < SCREEN_WIDTH * 1.2 and enemy.pos.x > 0 - SCREEN_WIDTH * 0.2:
                    enemy.draw(self.surface)

                for ebullet in enemy.bullets:
                    # off-screen culling
                    if ebullet.x + self.offset.x < SCREEN_WIDTH * -0.2 or ebullet.x + self.offset.x > SCREEN_WIDTH * 1.2 or ebullet.y > SCREEN_HEIGHT or ebullet.y < 0:
                        enemy.bullets.remove(ebullet)
                        del ebullet
                        continue
        
                    ebullet.update()
                    ebullet.draw(self.surface, self.offset.x)
                    
            test_spam_enemy_fire_time += self.dt
            if test_spam_enemy_fire_time > 1.3:
                for enemy in self.enemy_group.sprites():
                    enemy.fire_bullet(self.player.pos.x, self.player.pos.y)
                    test_spam_enemy_fire_time = 0.0

            # Draw/update player
            self.player.draw(self.surface)
            self.player.move(self.dt)
            
            # Clamp player position
            self.player.rect.clamp_ip(self.surface.get_rect())

            # Rescale screen
            self.screen_rescale()

            # particles!!!
            if self.particles:
                # update each particle group
                for group in self.particles[:]:
                    group.update(self.dt, self.gameplay_surface, self.offset.x)

                    # if group is empty
                    if not group:
                        self.particles.remove(group)
                        del group

            # Draw screen
            self.draw()
            

            # Update previous offset (move this to the end of the loop)
            self.previous_offset = self.offset

            # Update delta time
            self.dt = clock.tick(FRAMES_PER_SECOND) / 1000

        quit()

    def generate_humanoids(self) -> None:
        for i in range(self.initial_humanoids):
            spawn_x: int = random.randint(EDGE_SPAWN_BUFFER - (WORLD_WIDTH//2), (WORLD_WIDTH//2) - EDGE_SPAWN_BUFFER)
            spawn_y: int = GROUND_Y
            print(f"Humanoid spawned at ({spawn_x}, {spawn_y})")
            self.humanoid_group.add(Humanoid(spawn_x, spawn_y))

        # add to mini_map
        self.mini_map.add(self.humanoid_group.sprites())

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
                    print(self.player.pos.x)

                elif event.key == pg.K_f: # temp explosion key
                    if self.player.state != Player.States.DEAD:
                        self.particles.append(self.player.death())

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
