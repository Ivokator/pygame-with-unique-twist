import math
import random
import typing

import pygame as pg
from pygame.math import Vector2

from constants import *

MIN_SIZE: int = 2
MAX_SIZE: int = 6

class Particle(pg.sprite.Sprite):
    def __init__(self, spawn_pos: Vector2, 
                 min_speed: float, max_speed: float,
                 min_lifetime: float, max_lifetime: float,
                 base_colour: tuple[int, int, int]=(255, 255, 255)) -> None:
        super().__init__()
        self.pos: Vector2 = spawn_pos.copy()

        angle: int = random.randint(0, 360)
        speed: float = random.uniform(min_speed, max_speed)

        self.velocity: Vector2 = pg.math.Vector2()
        self.velocity.from_polar((speed, angle))
        
        self.total_time: float = random.uniform(min_lifetime, max_lifetime)
        self.remaining_time: float = self.total_time
        self.base_colour = base_colour

        self.size = random.uniform(MIN_SIZE, MAX_SIZE)

    def update(self, dt: float) -> None:
        self.pos += self.velocity * dt

        self.remaining_time -= dt

        if self.remaining_time <= 0:
            self.kill()
            del self # <--- does this work? if memory leak this may be culprit
        
    def draw(self, screen: pg.Surface, offset_x: float):
        # get (r,g,b,a)
        frac = max(0.0, min(1.0, self.remaining_time / self.remaining_time))
        alpha = 255 * int(frac)
        colour = (*self.base_colour, alpha)
        radius = int(self.size * frac)
        if radius <= 0:
            return

        # creates temp surface so alpha values can render
        temp_surface = pg.Surface((radius*2, self.size*2), pg.SRCALPHA)
        pg.draw.circle(temp_surface, colour, (radius, radius), radius)
        
        draw_x = self.pos.x + offset_x
        screen.blit(temp_surface, (draw_x - radius/2, self.pos.y - self.size/2))


class ParticleGroup(pg.sprite.Group):
    def __init__(self) -> None:
        super().__init__()

    def update(self, dt: float, screen: pg.Surface, offset_x: float) -> None:
        for sprite in self.sprites():
            sprite.update(dt)
            sprite.draw(screen, offset_x)