import math
import random
import typing

import pygame as pg
from pygame.math import Vector2

from constants import *

MIN_SIZE: int = 2
MAX_SIZE: int = 6

def explosion_effect(pos: Vector2, 
                     number: int = 70, 
                     min_speed: float = 120.0, 
                     max_speed: float =300.0,
                     min_lifetime: float = 1.2,
                     max_lifetime: float = 3.0,
                     angle: int = random.randint(0, 360), 
                     base_colour: tuple[int, int, int] = (255, 200, 50)) -> pg.sprite.Group:
    
    """Creates a particle explosion effect by generating 
    a group of particles.

    The particles are created with random speed, lifetime,
    and color. Each particle fades to transparent for the
    duration of its chosen lifetime.

    Arguments:
        pos (Vector2): (x, y) position of the center of explosion.
        number (int): Initial number of particles.
        min_speed (float): Minimum speed of the particles.
        max_speed (float): Maximum speed of the particles.
        min_lifetime (float): Minimum lifetime of the particles.
        max_lifetime (float): Maximum lifetime of the particles.
        angle (int): Angle (in degrees) to shoot the particle.
        base_colour (tuple[int, int, int]): Base color of the particles.
    Returns:
        pg.sprite.Group: A group of particles (sprites) representing the explosion.
    """
    particle_group: ParticleGroup = ParticleGroup()

    for _ in range(number):
        angle = random.randint(0, 360)
        particle = Particle(pos, 
                            min_speed=min_speed, 
                            max_speed=max_speed, 
                            min_lifetime=min_lifetime, 
                            max_lifetime=max_lifetime, 
                            angle=angle,
                            base_colour=base_colour)
        particle_group.add(particle)

    return particle_group

class Particle(pg.sprite.Sprite):
    def __init__(self, spawn_pos: Vector2, 
                 min_speed: float, max_speed: float,
                 min_lifetime: float, max_lifetime: float, 
                 angle: int,
                 base_colour: tuple[int, int, int]) -> None:
        super().__init__()
        self.pos: Vector2 = spawn_pos.copy()

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
        if self.pos.x + offset_x > SCREEN_WIDTH or self.pos.x + offset_x < 0:
            return
        if self.pos.y > GAMEPLAY_HEIGHT or self.pos.y < 0:
            return
        
        # get (r,g,b,a)
        visibility_percentage: float = max(0.0, min(1.0, self.remaining_time / self.total_time))

        alpha: int = int(255 * visibility_percentage)
        colour: tuple[int, int, int, int] = (*self.base_colour, alpha)

        radius: float = float(self.size * visibility_percentage)
        if radius <= 0:
            return

        # creates temp surface so alpha values can render
        temp_surface: pg.Surface = pg.Surface((radius*2, radius*2), pg.SRCALPHA)
        pg.draw.circle(temp_surface, colour, (radius, radius), radius)
        
        draw_x: float = self.pos.x + offset_x
        screen.blit(temp_surface, (draw_x - radius/2, self.pos.y - radius/2))

class ParticleGroup(pg.sprite.Group):
    def __init__(self) -> None:
        super().__init__()

    def update(self, dt: float, screen: pg.Surface, offset_x: float) -> None:
        for sprite in self.sprites():
            sprite.update(dt)
            sprite.draw(screen, offset_x)