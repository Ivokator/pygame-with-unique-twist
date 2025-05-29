import math
import os
import random
import sys
import typing

import pygame as pg # type: ignore
import pygame_menu as pm

from pygame.math import Vector2

import map
import misc

from classes import EnemyState, Player, PlayerBullet, PlayerGroup, EnemyBullet, Enemy, EnemyGroup, Humanoid, HumanoidGroup, HumanoidState, MiniMap
from downgrade_fx import apply_downgrade_effect

from constants import *

# Initialize
pg.mixer.pre_init(44100, -16, 16, 512)
pg.init()

# Screen / Clock

screen: pg.Surface = pg.display.set_mode(RESOLUTION, pg.RESIZABLE | pg.SCALED, vsync=1)
clock: pg.time.Clock = pg.time.Clock()

# Images
test_space = pg.image.load(os.path.join("./images/background","black_rectangle.png")).convert()

# Background tiling
test_space_tiles = math.ceil(SCREEN_WIDTH / (test_space.get_width())) + 1

# Camera look-ahead constants
MAX_LOOKAHEAD: float = SCREEN_WIDTH * 0.5 # pixels ahead of player
SMOOTHING: float = 0.03 # higher = snappier
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

        # group containing player
        self.player_group: PlayerGroup = PlayerGroup()

        # Intialize player
        self.player: Player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4, PLAYER_WIDTH, PLAYER_HEIGHT)
        self.player_group.add(self.player)

        self.enemy_group: EnemyGroup = EnemyGroup()


        self.offset: Vector2 = Vector2(0, 0)
        self.speed_threshold: float = self.player.max_speed_x * 0.7 # threshold for look-ahead
            
        self.previousoffsets: typing.List[float] = []
            
        self.current_background = test_space
        self.offset_change: float = 0.0

        self.mini_map: MiniMap = MiniMap()
        self.mini_map_clock: float = 0.0

        self.camera = Vector2(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.current_lookahead = 0.0

        self.particles: list[pg.sprite.Group] = []

        self.initial_humanoids: int = 30
        self.humanoid_group: HumanoidGroup = HumanoidGroup()

        self.game_over_text: pg.Surface = PRESS_START_FONT.render("GAME OVER", False, GREEN)
        self.game_over_text_rect: pg.Rect = self.game_over_text.get_rect()
        self.game_over_text_rect.center = (SCREEN_WIDTH // 2, GAMEPLAY_HEIGHT // 2)
        self.game_over_timer: float = 0.0


        self.smart_bomb_text: pg.Surface = PRESS_START_FONT.render("SMART BOMB!", False, WHITE)
        self.smart_bomb_text_rect: pg.Rect = self.smart_bomb_text.get_rect()
        self.smart_bomb_text_rect.center = (SCREEN_WIDTH // 2, TOP_WIDGET_HEIGHT // 2)

    def draw(self) -> None:
        
        self.enemy_group.update(self.offset.x, self.player, self.humanoid_group, self.gameplay_surface)
        self.humanoid_group.update(self.offset.x, self.gameplay_surface, self.player)
        self.player.update(self.offset.x)

        if self.player_group.ships < 0:
            self.game_over()

        # Blit and center surface on the screen
        screen.blit(
            self.gameplay_surface,
            ((screen.get_width() - self.surface.get_width()) / 4, TOP_WIDGET_HEIGHT))
             
        self.render_top_widget()

        apply_downgrade_effect(screen, 2)

        pg.display.flip()

    def _camera_look_ahead(self) -> None:
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

        # Render text
        self.text_score: pg.Surface = PRESS_START_FONT.render(str(self.player_group.score).zfill(7), False, WHITE)
        screen.blit(self.text_score, (100, TOP_WIDGET_HEIGHT - self.text_score.get_height() - 10))
        
        # Display ships
        self.display_ships()
        self.display_smart_bombs()

        self.mini_map.add(*self.enemy_group.sprites())
        self.mini_map.update(self.offset.x)
        
        screen.blit(self.mini_map.surface, ((self.surface.get_width() // 2) - (self.mini_map.surface.get_width() // 2), 0))

    def display_ships(self) -> None:
        for i in range(self.player_group.ships):
            screen.blit(self.player_group.lives_image, 
                        (self.text_score.get_width() + 100 - (i*self.player_group.lives_width), 
                         TOP_WIDGET_HEIGHT - self.text_score.get_height() - self.player_group.lives_height - self.player.smart_bomb_image.get_height() - 25))
    
    def display_smart_bombs(self) -> None:
        for i in range(self.player.smart_bombs):
            screen.blit(self.player.smart_bomb_image, 
                        (self.text_score.get_width() + 115 - (i * self.player_group.lives_width), # lives_width to align with ships
                         TOP_WIDGET_HEIGHT - self.text_score.get_height() - self.player.smart_bomb_height - 18))
    
    def background(self) -> None:
        # Draw the background

        surface_width = self.surface.get_width()
        surface_height = self.surface.get_height()

        background_width = self.current_background.get_width()
        background_height = self.current_background.get_height()

        # Transform background to right size
        scaled_background = pg.transform.scale(self.current_background, (background_width*1.5, background_height*1.5))

        # Scroll background
        for i in range(-1, test_space_tiles + 1):
            self.surface.blit(scaled_background, 
            (self.offset.x % background_width + i * background_width, 50))

    def _screen_rescale(self) -> None:
        pg.transform.scale(
            self.surface,
            (SCREEN_WIDTH, GAMEPLAY_HEIGHT),
            self.gameplay_surface)
        
    def _calculate_offset(self) -> None:
        """Calculates the camera offset based on player position and camera position.

        The offset is used to center the player on the screen and create a parallax effect.
        Changes self.offset and self.previousoffsets.
        """
        heading = self.player.pos - self.camera
        self.camera += heading * 0.05

        self.offset = Vector2(
            int(-self.camera.x + SCREEN_WIDTH//2),
            int(-self.camera.y + SCREEN_HEIGHT//2)
        )

        # Calculate change in offset (d_offset)
        self.previousoffsets.append(self.offset.x)
        if len(self.previousoffsets) > 2:
            self.previousoffsets.pop(0)
            self.offset_change = self.previousoffsets[1] - self.previousoffsets[0]

    def play_game(self) -> bool:
        # Game preparation
        pg.display.set_caption(WINDOW_TITLE)

        self.mini_map.add(self.player)

        self.peaks: list[tuple[int, int]] = map.generate_peaks(WORLD_WIDTH)
        self.mini_map.create_mountain_representation(self.peaks, WORLD_WIDTH)

        time_since_last_enemy: float = 0.0
        test_spam_enemy_fire_time: float = 0.0
        particle_timer: float = 0.0
        self.player_dead_timer: float = 0.0

        revival_particles: pg.sprite.Group | None = None
        currently_reviving: bool = False

        self.generate_humanoids()
        self.spawn_enemies(min(self.num_of_enemies, 30))

        self.running = True

        while self.running:
            self._calculate_offset()
            self._camera_look_ahead()

            # Update background
            screen.fill(BLACK)
            self.surface.fill(BLACK)
            self.background()

            # Draw mountains
            map.draw_mountains(self.surface, self.peaks, self.offset.x, WORLD_WIDTH)

            # if dead, respawn
            if self.player.state == Player.States.DEAD and not currently_reviving:
                if self.player_group.ships < 1:
                    self.player_group.ships -= 1
                else:
                    self.player_dead_timer += self.dt
                    if self.player_dead_timer >= 2.0:
                        # safe respawn logic
                        respawn_x = SCREEN_WIDTH // 2
                        respawn_y = SCREEN_HEIGHT // 4
                        temp_rect = pg.Rect(respawn_x, respawn_y, PLAYER_WIDTH, PLAYER_HEIGHT)
                        max_attempts = 20
                        attempts = 0
                        while any(temp_rect.colliderect(enemy.rect) for enemy in self.enemy_group.sprites()) and attempts < max_attempts:
                            respawn_y += PLAYER_HEIGHT + 10
                            if respawn_y > GAMEPLAY_HEIGHT - PLAYER_HEIGHT:
                                respawn_y = TOP_WIDGET_HEIGHT + 10
                            temp_rect = pg.Rect(respawn_x, respawn_y, PLAYER_WIDTH, PLAYER_HEIGHT)
                            attempts += 1
                        self.player.pos = Vector2(respawn_x, respawn_y)
                        
                        revival_particles = self.player.revive(self.offset.x)
                        self.particles.append(revival_particles)

                        currently_reviving = True
                        self.player_group.ships -= 1
                        self.player_dead_timer = 0.0

            # Event handling
            self.player.cooldown_timer += clock.get_time()
            self.event()

            # if player successfully killed all enemies, exit out of function
            if not self.enemy_group:
                return True

            # Draw player
            if self.player.health <= 0 and self.player.state != Player.States.DEAD:
                self.player.state = Player.States.DEAD
                self.screen_flash(1, [(255, 255, 255, 50)], 0.06, 0.02, False)
                self.particles.append(self.player.death())
                
            self.player.draw(self.surface)
            self.player.move(self.dt)

            # Draw player bullets
            for bullet in self.player.bullets:

                # off-screen culling
                if SCREEN_WIDTH * 1.2 < bullet.x > SCREEN_WIDTH * -0.2:
                    self.player.bullets.remove(bullet)
                    del bullet
                    continue

                bullet.update()
                bullet.draw(self.surface)

            self.update_and_draw_enemy_related()

            test_spam_enemy_fire_time += self.dt
            if test_spam_enemy_fire_time > 1.3:
                for enemy in self.enemy_group.sprites():
                    enemy.fire_bullet(self.player.pos.x, self.player.pos.y)
                    test_spam_enemy_fire_time = 0.0
            
            # Clamp player position
            self.player.rect.clamp_ip(self.surface.get_rect())

            # Rescale screen
            self._screen_rescale()

            # particles!!!
            if self.particles:
                # update each particle group
                for group in self.particles[:]:
                    group.update(self.dt, self.gameplay_surface, self.offset.x)

                    # if group is empty
                    if not group:
                        self.particles.remove(group)

                        # respawn player
                        if group is revival_particles:
                            revival_particles = None
                            currently_reviving = False

                            self.player.state = Player.States.IDLE

                        del group
            
            particle_timer += self.dt
            if particle_timer > 1.0:
                if (particle_group := self.player.health_indicator(self.offset.x)):
                    self.particles.append(particle_group)

            # Draw screen
            self.draw()
            
            # Update previous offset (move this to the end of the loop)
            self.previous_offset = self.offset

            # Update delta time
            self.dt = clock.tick(FRAMES_PER_SECOND) / 1000

        if not self.enemy_group:
            return True
        else:
            return False

    def spawn_enemies(self, num: int) -> None:
        """Spawn given number of enemies."""
        min_distance = 200
        for _ in range(num):
            while True:
                spawn_x = random.randint(-SCREEN_WIDTH, SCREEN_WIDTH*2)
                spawn_y = random.randint(TOP_WIDGET_HEIGHT, GAMEPLAY_HEIGHT)
                if abs(spawn_x - self.player.pos.x) > min_distance or abs(spawn_y - self.player.pos.y) > min_distance:
                    break
            enemy = Enemy(spawn_x, spawn_y)
            self.enemy_group.add(enemy)

    def update_and_draw_enemy_related(self) -> None:
        # Draw enemies
        for enemy in self.enemy_group.sprites():
            enemy.update(self.offset.x, self.player, self.humanoid_group.sprites(), self.surface)

            if -(SCREEN_WIDTH * 0.2) < enemy.pos.x < SCREEN_WIDTH * 1.2:
                enemy.draw(self.surface)

            # enemy collision detection w/ player
            if self.player.hitbox_top.colliderect(enemy.rect) or self.player.hitbox_bottom.colliderect(enemy.rect):
                if self.player.state != Player.States.DEAD:
                    self.player.gets_hit_by(enemy)

            # collision detection with player bullets
            if (collided_bullet := pg.sprite.spritecollideany(enemy, self.player.bullets)): # type: ignore
                # hit enemy!
                if getattr(enemy, "state", None) == EnemyState.CAPTURING:
                    self.player_group.score += 250
                else:
                    self.player_group.score += 50
                self.particles.append(enemy.death())
                self.player.bullets.remove(collided_bullet)
                del enemy

        for ebullet in self.enemy_group.bullets:
                # enemy bullet collision detection w/ player
                if self.player.hitbox_top.colliderect(ebullet.rect) or self.player.hitbox_bottom.colliderect(ebullet.rect):
                    if self.player.state != Player.States.DEAD:
                        self.player.gets_hit_by(ebullet)
                        self.particles.append(misc.explosion_effect(Vector2(ebullet.x, ebullet.y),
                                                                    number=10,
                                                                    min_lifetime=0.2,
                                                                    max_lifetime=0.35,
                                                                    min_speed=200,
                                                                    ))

                        self.enemy_group.bullets.remove(ebullet)
                        del ebullet
                        continue

                # off-screen culling
                if ebullet.x + self.offset.x < SCREEN_WIDTH * -0.2 or ebullet.x + self.offset.x > SCREEN_WIDTH * 1.2 or ebullet.y > SCREEN_HEIGHT or ebullet.y < 0:
                    self.enemy_group.bullets.remove(ebullet)
                    del ebullet
                    continue

                ebullet.update()
                ebullet.draw(self.surface, self.offset.x)
            


    def game_over(self) -> None:
        self.game_over_timer += self.dt
        self.gameplay_surface.blit(self.game_over_text, self.game_over_text_rect)

        if self.game_over_timer > 3.0:
            self.main_menu()

    def generate_humanoids(self) -> None:
        for i in range(self.initial_humanoids):
            spawn_x: int = random.randint(EDGE_SPAWN_BUFFER - (WORLD_WIDTH//2), (WORLD_WIDTH//2) - EDGE_SPAWN_BUFFER)
            spawn_y: int = GROUND_Y
            #print(f"Humanoid spawned at ({spawn_x}, {spawn_y})")
            self.humanoid_group.add(Humanoid(spawn_x, spawn_y))

        # add to mini_map
        self.mini_map.add(self.humanoid_group.sprites())

    def smart_bomb(self) -> None:
        """Uses a smart bomb, if possible.
        
        A smart bomb kills all enemies (and bullets) visible on screen.
        """
        if self.player.smart_bombs <= 0:
            return

        self.player.smart_bombs -= 1

        enemies_on_screen = [enemy for enemy in self.enemy_group.sprites() if 0 < enemy.pos.x + self.offset.x < SCREEN_WIDTH]
        bullets_on_screen = [bullet for bullet in self.enemy_group.bullets if 0 < bullet.x + self.offset.x < SCREEN_WIDTH]

        for enemy in enemies_on_screen:
            self.particles.append(enemy.death(sound_on=False))
            enemy.kill()
            del enemy
        for bullet in bullets_on_screen:
            self.enemy_group.bullets.remove(bullet)

        # flash effect
        self.screen_flash(3, [(255, 0, 0, 100), (0, 255, 0, 100), (0, 0, 255, 100)], 0.06, 0.03)
        
    def screen_flash(self, num: int, colours: list[tuple[int, int, int, int]], flash_seconds: float, blank_seconds: float, show_smart_bomb_text: bool = True) -> None:
        """Flashes the screen with colour, giving a dramatic effect.
        
        Arguments:
            num (int): Number of individual flashes to show on screen.
            colours (list[tuple[int, int, int, int]]): List of RGBA tuples to flash the screen with. Flashes colours in order.
                - If len(colours) > num, extra colours are ignored.
                - If len(colours) < num, colours are cycled through.
                - Ill-advised to pass fully opaque colours
            flash_seconds (float): Duration for each colour to flash at a time.
            blank_seconds (float): Duration between flashes of colour of no flash.
            show_smart_bomb_text (bool): Show "SMART BOMB!" on screen (only applicable for smart bomb usage).
        Example:
            Flashes the screen red, green, and blue for 0.5 seconds each, with 0.2 seconds of no flash in between.
            .. code-block:: python
                screen_flash(3, [(255, 0, 0, 255), (0, 255, 0, 255), (0, 0, 255, 255)], 0.5, 0.2)
            
        """
        
        for i in range(num):
            colour = colours[i % len(colours)]
            original_surface = self.gameplay_surface.copy()

            flash_overlay = pg.Surface((screen.get_width(), screen.get_height()-TOP_WIDGET_HEIGHT), pg.SRCALPHA)
            flash_overlay.fill(colour)

            screen.blit(original_surface, (0, TOP_WIDGET_HEIGHT))
            self.render_top_widget()
            screen.blit(flash_overlay, (0, TOP_WIDGET_HEIGHT))
            if show_smart_bomb_text:
                self.gameplay_surface.blit(self.smart_bomb_text, self.smart_bomb_text_rect)

            pg.display.flip()

            pg.time.delay(int(flash_seconds * 1000))

            screen.blit(original_surface, (0, TOP_WIDGET_HEIGHT))
            if show_smart_bomb_text:
                self.gameplay_surface.blit(self.smart_bomb_text, self.smart_bomb_text_rect)

            pg.display.flip()
            
            pg.time.delay(int(blank_seconds * 1000))

    def event(self) -> None:
        """Handles events."""
        for event in pg.event.get():
            if event.type == pg.QUIT:
                quit()
            elif event.type == pg.KEYDOWN:
                    
                # Fire bullet
                if event.key == pg.K_SPACE:
                    self.player.fire_bullet()

                elif event.key == pg.K_p:
                    self.smart_bomb()

                elif event.key == pg.K_F1: # self-destruct
                    if self.player.state != Player.States.DEAD:
                        self.particles.append(self.player.death())

    def game_loop(self) -> None:
        self.current_wave: int = 1
        self.num_of_enemies: int = 10
        while True:
            self.wave_screen()
            if self.play_game():
                self.current_wave += 1
                self.num_of_enemies += 5
    
    def wave_screen(self) -> None:
        """Displays attack wave in big text
            Starts next round
        
        """
        running: bool = True
        wait_counter: float = 0.0

        while running:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    running = False
            
            self.surface.fill(BLACK)
            wave_text: pg.Surface = PRESS_START_FONT.render(f"ATTACK WAVE {self.current_wave}", False, WHITE)
            wave_text_rect: pg.Rect = wave_text.get_rect()
            wave_text_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - (wave_text_rect.height * 2))
            self.surface.blit(wave_text, wave_text_rect)

            wait_counter += self.dt

            if wait_counter > 3.0:
                running = False
                self.enemy_group.empty()
                self.humanoid_group.empty()
                return

            screen.blit(self.surface, (0, 0))

            pg.display.flip()
            self.dt = clock.tick(FRAMES_PER_SECOND) / 1000

    def main_menu(self) -> None:
        """Returns to the main menu."""
        self.running = False
        pg.display.set_caption(WINDOW_TITLE)
        menu = pm.Menu('Defender Remake', SCREEN_WIDTH * 2 // 3, SCREEN_HEIGHT * 1 // 2,
                        theme=mytheme)
        menu.add.button('Play', lambda: self.game_loop())
        menu.add.button('Controls', lambda: self.controls())
        menu.add.button('About', lambda: self.about())
        menu.add.button('Quit', pm.events.EXIT)

        menu.mainloop(screen)

    def controls(self) -> None:
        """Shows game controls."""
        menu = pm.Menu('Controls', SCREEN_WIDTH * 2 // 3, SCREEN_HEIGHT * 2 // 3,
                        theme=mytheme)
        menu.add.label("""
Move: WASD
Shoot: Space
Smart Bomb: P
""")
        menu.add.button('Return', lambda: self.main_menu())
        menu.mainloop(screen)
    
    def about(self) -> None:
        """Shows about menu."""

        menu = pm.Menu('About', SCREEN_WIDTH * 2 // 3, SCREEN_HEIGHT * 2 // 3,
                        theme=mytheme)
        menu.add.label('\nPython 3.11.9 - 3.13\nCreated April 2025\nv. DEV\n-----------------------\nCREDITS:\nIvokator\nSkyVojager')
        menu.add.button('Return', lambda: self.main_menu())
        menu.mainloop(screen)





if __name__ == "__main__":
    game = Game()
    game.main_menu()
