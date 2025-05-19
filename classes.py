import typing

import pygame as pg
from pygame.math import Vector2
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
    def __init__(self, x: int, y: int, width: int, height: int) -> None:
        super().__init__()
        self.rect: pg.Rect = pg.Rect(x, y, width, height)
        self.pos: Vector2 = Vector2(x, y)

        # Physics parameters
        self.velocity: Vector2 = Vector2(0, 0)
        self.accel_x: float = 0.0
        self.accel_y: float = 0.0
        self.max_speed_x: int = 10
        self.max_speed_y: int = 8
        self.accel_rate: int = 50

        # careful that drag does not exceed accel_rate
        self.drag_x: int = 1 
        self.drag_y: int = 20

        self.direction = 0  # left:0, right:1

        self.bullets: typing.List[PlayerBullet] = []
        self.bullet_cooldown_ms: float = 100
        self.cooldown_timer: int = 0

        self.lookahead_compensation: float = 0.0


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

    def draw(self, surface: pg.Surface) -> None:
        """Draws the player."""
        pg.draw.rect(surface, WHITE, self.rect)


class PlayerBullet(object):
    def __init__(self, x: float, y: float, width: int, height: int, angle, speed: int) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self.speed = speed
        self.angle = angle
        self.velocity = pg.math.Vector2()
        self.velocity.from_polar((self.speed, self.angle)) # polar coordinates

    def draw(self, screen) -> None:
        pg.draw.rect(screen, WHITE, pg.Rect(self.x, self.y, self.width, self.height))

    def update(self) -> None:
        self.x += self.velocity.x
        self.y += self.velocity.y


class EnemyBullet(object):
    def __init__(self, x: int, y: int, speed: int, angle, radius) -> None:
        self.x = x
        self.y = y
        self.radius = radius

        self.speed = speed
        self.angle = angle
        self.velocity = pg.math.Vector2()
        self.velocity.from_polar((self.speed, self.angle)) # polar coordinates

    def draw(self, screen):
       pg.draw.circle(screen, RED, (self.x,self.y), self.radius)
    
    def update(self):
        self.x += self.velocity.x
        self.y += self.velocity.y

class Enemy(pg.sprite.Sprite):
    def __init__(self, spawn_x: int, spawn_y: int) -> None:
        super().__init__()
        self.spawn_x = spawn_x
        self.spawn_y = spawn_y
        self.pos = Vector2(spawn_x, spawn_y)
        self.width = 30
        self.height = 30
        self.speed = 5

        print(f"Enemy created at ({self.pos.x}, {self.pos.y})")
        
    def draw(self, screen) -> None:
        pg.draw.rect(screen, GREEN, pg.Rect(self.draw_x, self.pos.y, self.width, self.height))

    def update(self, offset_x: int) -> None:
        self.draw_x = self.pos.x + offset_x

class EnemyGroup(pg.sprite.Group):
    def __init__(self) -> None:
        super().__init__()

    def update(self, offset_x: int, screen) -> None:
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
            #icon_y = max(0, min(self.surface_height - self.icon_size, icon_y))


            if isinstance(sprite, Player):
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

if __name__ == "__main__":
    # Test the classes
    pg.init()

    screen = pg.display.set_mode(RESOLUTION)
    clock = pg.time.Clock()

    player_bullet = PlayerBullet(100, 100, 10, 5, speed=5, angle=0, )
    enemy_bullet = EnemyBullet(200, 200, radius=5, speed=5, angle=45, )

    running: bool = True
    dt = 0.0
    while running:
        dt = clock.tick(FRAMES_PER_SECOND) / 1000.0
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

        screen.fill(BLACK)

        player_bullet.update()
        enemy_bullet.update()

        enemy_bullet.draw(screen)
        player_bullet.draw(screen)

        pg.display.flip()
        dt = clock.tick(FRAMES_PER_SECOND) / 1000
        
    pg.quit()