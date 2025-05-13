<<<<<<< Updated upstream
=======
import typing
import math

>>>>>>> Stashed changes
import pygame as pg
from constants import *
import math
import random


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
<<<<<<< Updated upstream
    def __init__(self, spawn_x: int, spawn_y: int, speed: int, angle, radius) -> None:
<<<<<<< Updated upstream
        self.x = x
        self.y = y
=======
        self.x = spawn_x
        self.y = spawn_y
        self.offset_x = 0
>>>>>>> Stashed changes
=======
    def __init__(self, x: int, y: int, speed: int, angle, radius) -> None:
        self.rect = pg.Rect(x, y, radius * 2, radius * 2)
>>>>>>> Stashed changes
        self.radius = radius
        self.speed = speed
        self.angle = angle

        self.velocity_x = math.cos(math.radians(self.angle)) * self.speed
        self.velocity_y = math.sin(math.radians(self.angle)) * self.speed
        
    def draw(self, screen):
       pg.draw.rect(screen, RED, self.rect)
    
    def update(self):
<<<<<<< Updated upstream
        # using tanangle
        self.x += self.velocity.x + self.offset_x
        self.y += self.velocity.y
=======
        #print(f"Enemy bullet at ({self.x}, {self.y})")
        self.rect.x += self.velocity_x
        self.rect.y += self.velocity_y
>>>>>>> Stashed changes


class Enemy(object):
    def __init__(self, spawn_x: int, spawn_y: int) -> None:
        self.spawn_x = spawn_x
        self.spawn_y = spawn_y
        self.x = spawn_x
        self.y = spawn_y
        self.width = 50
        self.height = 50
        self.speed = 5
<<<<<<< Updated upstream
=======
        self.bullets: typing.List[EnemyBullet] = []

        self.offset_x = 0
<<<<<<< Updated upstream
        #print(f"Enemy created at ({self.x}, {self.y})")
>>>>>>> Stashed changes
=======
        
        self.bullets: typing.List[EnemyBullet] = []
>>>>>>> Stashed changes
        
    def draw(self, screen) -> None:
        pg.draw.rect(screen, GREEN, pg.Rect(self.x, self.y, self.width, self.height))

<<<<<<< Updated upstream
    def update(self, background_scroll: int) -> None:
        self.x = self.spawn_x + background_scroll
    
=======
    def update(self, offset_x: int) -> None:
        self.x = self.spawn_x + offset_x
        
<<<<<<< Updated upstream
    def angle_to_player(self, player_x: int, player_y: int) -> float:
        dx = player_x - self.x
        dy = player_y - self.y
        #cant divide by 0 lol
        if dx == 0:
            dx = 0.1
        tanangle = dy / dx
        angle = math.degrees(math.atan(tanangle))
        return angle
    
    def fire_bullet(self, player_x: int, player_y: int) -> EnemyBullet:
        angle = self.angle_to_player(player_x, player_y)
        bullet = EnemyBullet(self.x, self.y, speed=2, angle=angle, radius=5)
        return bullet
        
=======
    
    def fire_bullet(self, player_x: int, player_y: int) -> None:
        self.dx = player_x - self.x
        self.dy = player_y - self.y
        angle = math.degrees(math.atan2(self.dy, self.dx)) + random.randint(-2, 2) # randomize angle
        i = random.randint(0, 1000)
        if i < 5:
            bullet = EnemyBullet(self.x, self.y, radius=5, speed=2, angle=angle)
            self.bullets.append(bullet)
>>>>>>> Stashed changes

class EnemyGroup(pg.sprite.Group):
    def __init__(self) -> None:
        super().__init__()
        self.enemies: typing.List[Enemy] = []

    def add_enemy(self, enemy: Enemy) -> None:
        self.enemies.append(enemy)
        self.add(enemy)

    def update(self, offset_x: int, screen) -> None:
        for enemy in self.enemies:
            enemy.update(offset_x)
            enemy.draw(screen)
>>>>>>> Stashed changes

if __name__ == "__main__":
    # Test the classes
    pg.init()

    screen = pg.display.set_mode(RESOLUTION)
    clock = pg.time.Clock()

    player_bullet = PlayerBullet(100, 100, 10, 5, speed=5, angle=0,)
    enemy_bullet = EnemyBullet(200, 200, radius=5, speed=5, angle=45,)

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