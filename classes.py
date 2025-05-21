import math
import random
import typing

from enum import Enum, auto

import pygame as pg
from pygame.math import Vector2

import misc
import sound

from constants import *

class Player(pg.sprite.Sprite):
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
    class States(Enum):
        IDLE = auto() # default
        MOVING = auto()
        DEAD = auto()

    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        super().__init__()
        self.rect: pg.Rect = pg.Rect(x, y, width, height)
        self.pos: Vector2 = Vector2(x, y)

        self.health: int = 100

        # Physics parameters
        self.velocity: Vector2 = Vector2(0, 0)
        self.accel_x: float = 0.0
        self.accel_y: float = 0.0
        self.max_speed_x: int = 10
        self.max_speed_y: int = 8
        self.accel_rate: int = 50

        self.draw_x = x

        # careful that drag does not exceed accel_rate
        self.drag_x: int = 1 
        self.drag_y: int = 20

        self.direction = 0  # left:0, right:1

        self.bullets: typing.List[PlayerBullet] = []
        self.bullet_cooldown_ms: float = 50
        self.cooldown_timer: int = 0

        self.lookahead_compensation: float = 0.0

        #player states
        self.state = Player.States.IDLE

        self.idle_sprite = pg.image.load(os.path.join("images", "player", "idle.png")).convert_alpha()

        self.move_sprites = [pg.image.load(os.path.join("images", "player", "moving1.png")).convert_alpha(),
                             pg.image.load(os.path.join("images", "player", "moving2.png")).convert_alpha(),
                             pg.image.load(os.path.join("images", "player", "moving3.png")).convert_alpha(),
                             ]
        
        # current image!
        self.image = pg.transform.scale(self.idle_sprite, (width, self.idle_sprite.get_height() / self.idle_sprite.get_width() * width))
        self.mask = pg.mask.from_surface(self.image)

    def _health_indicator(self) -> pg.sprite.Group | None:
        """"""
        # non-traditional health indicator: emit smoke/sparks based on health

        if self.health < 100:
            intensity = max(1, (100 - self.health) // 15)
            for _ in range(intensity):

                # randomize position near the player
                offset = Vector2(random.uniform(-self.rect.width // 2, self.rect.width // 2),
                                 random.uniform(self.rect.height // 2, self.rect.height))
                
                # smoke/sparks
                return misc.explosion_effect(self.pos,
                                      number = 7, 
                                      min_lifetime=0.2, 
                                      max_lifetime=0.7, 
                                      base_colour=random.choice([(120,120,120), (200,200,50), (255,140,0)]))
        return None

    def move(self, dt) -> None:
        if self.state == Player.States.DEAD:
            return

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

        # y-axis screen border collision detection

        if (self.pos.y >= GAMEPLAY_HEIGHT and self.accel_y > 0) or (self.pos.y < 0 and self.accel_y < 0):
            self.velocity.y = 0
            self.accel_y = 0
            print("crash!")
            return

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
        if self.state == Player.States.DEAD:
            return
        # Create a bullet at the player's position
        # and set its angle and speed
        if self.cooldown_timer > self.bullet_cooldown_ms:
            self.cooldown_timer = 0
            bullet = PlayerBullet(self.rect.x + (self.rect.width // 2), self.rect.y + (self.rect.height // 2), width=10, height=10, angle = self.direction * -180, speed=30)
            self.bullets.append(bullet)

            # sound
            random_sound = random.choice([sound.PLAYER_FIRE1, sound.PLAYER_FIRE2, sound.PLAYER_FIRE3, sound.PLAYER_FIRE4,])
            random_sound.play()

    def death(self) -> pg.sprite.Group:
        self.state = Player.States.DEAD
        return misc.explosion_effect(self.pos, 70)
            
    def update(self, offset_x) -> None:
        if self.state == Player.States.DEAD:
            return
        self.draw_x = int(self.pos.x + offset_x)
        self.rect.x, self.rect.y = int(self.draw_x), int(self.pos.y)
        self.pos.y = max(0, min(GAMEPLAY_HEIGHT - self.rect.height, self.pos.y))

    def draw(self, surface: pg.Surface) -> None:
        if self.state == Player.States.DEAD:
            return
        if self.direction == 0:
            surface.blit(self.image, (self.draw_x, self.rect.y))
        else:
            self.flipped = pg.transform.flip(self.image, True, False)
            surface.blit(self.flipped, (self.draw_x, self.rect.y))

        #pg.draw.rect(surface, WHITE, self.rect)

class PlayerGroup(pg.sprite.GroupSingle):
    """
    A sprite group that manages persistent player statistics such as points.
    Unlike the Player class (representing the player's ship, which is reloaded or reset each round),
    PlayerGroup is intended to track stats that persist across rounds, such as score, lives, or achievements.
    """
    def __init__(self) -> None:
        super().__init__()
        self.score: int = 0
        self.lives: int = 5



class PlayerBullet(object):
    def __init__(self, x: float, y: float, width: int, height: int, angle, speed: int) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect: pg.Rect = pg.Rect(x, y, width, height)

        self.speed = speed
        self.angle = angle
        self.velocity = pg.math.Vector2()
        self.velocity.from_polar((self.speed, self.angle)) # polar coordinates

    def draw(self, screen) -> None:
        pg.draw.rect(screen, WHITE, pg.Rect(self.x, self.y, self.width, self.height))

    def update(self) -> None:
        self.x += self.velocity.x
        self.y += self.velocity.y

        self.rect.x, self.rect.y = int(self.x), int(self.y)

class EnemyBullet(object):
    def __init__(self, x: float | int, y: float | int, speed: int, angle, radius) -> None:
        self.x = x
        self.y = y
        self.radius = radius
        self.rect: pg.Rect = pg.Rect(x, y, radius, radius)

        self.speed = speed
        self.angle = angle
        self.velocity = pg.math.Vector2()
        self.velocity.from_polar((self.speed, self.angle)) # polar coordinates

    def draw(self, screen: pg.Surface, offset_x: float):
       screen_x = self.x + offset_x
       pg.draw.circle(screen, WHITE, (screen_x, self.y), self.radius)
    
    def update(self) -> None:
        self.x += self.velocity.x
        self.y += self.velocity.y

        self.rect.x, self.rect.y = int(self.x), int(self.y)


class Enemy(pg.sprite.Sprite):
    def __init__(self, spawn_x: int, spawn_y: int) -> None:
        super().__init__()
        self.spawn_x = spawn_x
        self.spawn_y = spawn_y
        self.pos = Vector2(spawn_x, spawn_y)
        self.width = 30
        self.height = 30
        self.rect: pg.Rect = pg.Rect(spawn_x, spawn_y, self.width, self.height)
        self.speed = 5
        
        self.offset_x = 0
        
        self.bullets: typing.List[EnemyBullet] = []

        #print(f"Enemy created at ({self.x}, {self.y})")
        self.idle_sprite = pg.image.load(os.path.join("images", "enemies", "mutant.png")).convert_alpha()

        self.image = pg.transform.scale(self.idle_sprite, (self.width, self.idle_sprite.get_height() / self.idle_sprite.get_width() * self.width))
        self.mask = pg.mask.from_surface(self.image)
    
    def death(self) -> pg.sprite.Group:
        self.kill()
        return misc.explosion_effect(self.pos, 50, min_lifetime=0.8, max_lifetime=2.0)
        
    def draw(self, screen) -> None:
        pg.draw.rect(screen, GREEN, pg.Rect(self.draw_x, self.pos.y, self.width, self.height))

    def update(self, offset_x: float) -> None:
        self.draw_x = self.pos.x + offset_x
        self.rect.x = int(self.draw_x)
    
    def fire_bullet(self, player_x: float, player_y: float) -> None:
        dx = player_x - self.pos.x
        dy = player_y - self.pos.y
        angle = math.degrees(math.atan2(dy, dx)) + random.randint(-2, 2) # randomize angle

        # spawn at the enemy’s center
        spawn_x = self.pos.x + self.width / 2
        spawn_y = self.pos.y + self.height / 2
        bullet = EnemyBullet(spawn_x, spawn_y, radius=5, speed=6, angle=angle)
        self.bullets.append(bullet)

class EnemyGroup(pg.sprite.Group):
    def __init__(self) -> None:
        super().__init__()

    def update(self, offset_x: float, screen) -> None:
        for enemy in self.sprites():
            enemy.update(offset_x)
            enemy.draw(screen)

class MiniMap(pg.sprite.Group):
    def __init__(self) -> None:
        super().__init__()
        self.surface: pg.Surface = pg.Surface((SCREEN_WIDTH // 3, TOP_WIDGET_HEIGHT - TOP_WIDGET_LINE_THICKNESS // 2))

        # fast reference
        self.surface_width: int = self.surface.get_width()
        self.surface_height: int = self.surface.get_height()

        self.visible_area_width: int = self.surface_width // 8

        self.icon_size: int = self.surface_width // 60

        # visible area visual brackets
        self.lower_bracket: list[tuple[float, float]] = [
            (self.surface_width / 2 - self.visible_area_width / 2, self.surface_height * 9 // 10),
            (self.surface_width / 2 - self.visible_area_width / 2, self.surface_height - TOP_WIDGET_LINE_THICKNESS // 4),
            (self.surface_width / 2 + self.visible_area_width / 2, self.surface_height - TOP_WIDGET_LINE_THICKNESS // 4),
            (self.surface_width / 2 + self.visible_area_width / 2, self.surface_height * 9 // 10)]
        
        self.upper_bracket: list[tuple[float, float]] = [
            (self.surface_width / 2 - self.visible_area_width / 2, self.surface_height // 10),
            (self.surface_width / 2 - self.visible_area_width / 2, TOP_WIDGET_LINE_THICKNESS // 4),
            (self.surface_width / 2 + self.visible_area_width / 2, TOP_WIDGET_LINE_THICKNESS // 4),
            (self.surface_width / 2 + self.visible_area_width / 2, self.surface_height // 10)]
        

    def update(self, offset_x: float) -> None:
        self.surface.fill(BLACK)
        self.draw_mountain_outline(offset_x)

        for sprite in self.sprites():
            norm_x = (sprite.pos.x + offset_x) / self.world_width
            icon_x = norm_x * self.surface_width - (self.icon_size / 2) + ((self.surface_width - self.visible_area_width) / 2)

            icon_y: float = (sprite.pos.y / GAMEPLAY_HEIGHT) * self.surface_height - (self.icon_size / 2)

            # avoids drawing icons that are outside of the surface and cannot be seen
            if icon_x > self.surface_width or icon_x < -self.icon_size:
                continue

            # clamp inside minimap
            #icon_x = max(0, min(self.surface_width  - self.icon_size, icon_x))
            icon_y = max(0, min(self.surface_height - self.icon_size, icon_y))

            if isinstance(sprite, Humanoid):
                pg.draw.rect(self.surface, DARK_GREY, pg.Rect(icon_x, icon_y, self.icon_size * 0.8, self.icon_size))
            elif isinstance(sprite, Player):
                pg.draw.rect(self.surface, WHITE, pg.Rect(icon_x, icon_y, self.icon_size, self.icon_size))
            elif isinstance(sprite, Enemy):
                pg.draw.rect(self.surface, GREEN, pg.Rect(icon_x, icon_y, self.icon_size, self.icon_size))

        # ui visuals
        pg.draw.lines(self.surface, RED, False, self.lower_bracket, width = 2)
        pg.draw.lines(self.surface, RED, False, self.upper_bracket, width = 2)

    def create_mountain_representation(self, peaks: list[tuple[int, int]], world_width: int) -> None:
        self.mountain_representation: list[tuple[int, int]] = peaks[::4] # get every nth point
        self.world_width: int = world_width

    def draw_mountain_outline(self, offset_x: float) -> None:
        points_to_draw: list[tuple[float, float]] = []
        for x, y in self.mountain_representation:
            norm_x = (x + offset_x) / self.world_width
            norm_y = y / GAMEPLAY_HEIGHT

            point_x = norm_x * self.surface_width
            point_y = norm_y * self.surface_height

            if point_x > self.surface_width or point_x < 0:
                continue
            points_to_draw.append((point_x, point_y))
        
        if len(points_to_draw) >= 2:
            pg.draw.lines(self.surface, BLUE, False, points_to_draw, width = 2)

class HumanoidState(Enum):
    IDLE = 0
    WALKING = 1
    CAPTURED = 2
    RESCUED = 3
    FALLING = 4
    PANICKING = 5

class Humanoid(pg.sprite.Sprite):
    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self.width = 10
        self.height = 20
        self.draw_x: int | float = x

        self.pos: Vector2 = Vector2(x, y)

        self.state: HumanoidState = HumanoidState.IDLE
        self.speed: int = 5

    def draw(self, screen) -> None:
        pg.draw.rect(screen, DARK_GREY, pg.Rect(self.draw_x, self.pos.y, self.width, self.height))

    def update(self, offset_x: float) -> None:
        self.draw_x = self.pos.x + offset_x

class HumanoidGroup(pg.sprite.Group):
    def __init__(self) -> None:
        super().__init__()

    def update(self, offset_x: float, screen: pg.Surface) -> None:
        # placeholder function until humanoids have image sprites
        for sprite in self:
            sprite.update(offset_x)
            sprite.draw(screen)

if __name__ == "__main__":
    # Test the classes
    pg.init()

    screen = pg.display.set_mode(RESOLUTION)
    clock = pg.time.Clock()

    running: bool = True
    dt = 0.0
    while running:
        dt = clock.tick(FRAMES_PER_SECOND) / 1000.0
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

        screen.fill(BLACK)

        pg.display.flip()
        dt = clock.tick(FRAMES_PER_SECOND) / 1000
        
    pg.quit()