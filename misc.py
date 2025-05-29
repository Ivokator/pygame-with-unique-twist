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
                     min_angle: int = 0,
                     max_angle: int = 360,
                     base_colour: tuple[int, int, int] = (255, 200, 50),
                     reversed: bool = False
                     ) -> pg.sprite.Group:
    
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
        min_angle (int): Min angle to shoot particles.
        max_angle (int): Max angle to shoot particles.
        base_colour (tuple[int, int, int]): Base color of the particles.
        reversed (bool): Set to True to create reverse explosion effect
    Returns:
        pg.sprite.Group: A group of particles (sprites) representing the explosion.
    """
    particle_group: ParticleGroup = ParticleGroup()

    for _ in range(number):
        angle = random.randint(min_angle, max_angle)
        lifetime = random.uniform(min_lifetime, max_lifetime)
        speed = random.uniform(min_speed, max_speed)

        if not reversed:
            particle = Particle(pos, 
                                speed=speed,
                                lifetime=lifetime,
                                angle=angle,
                                base_colour=base_colour)
        else:
            particle = ReverseParticle(pos, 
                                speed=speed,
                                lifetime=lifetime,
                                angle=angle,
                                base_colour=base_colour)
            
        particle_group.add(particle)

    return particle_group

class Particle(pg.sprite.Sprite):

    def __init__(self, spawn_pos: Vector2, 
                 speed: float,
                 lifetime: float, 
                 angle: int,
                 base_colour: tuple[int, int, int]) -> None:
        super().__init__()
        
        self.pos: Vector2 = spawn_pos.copy()

        self.velocity: Vector2 = pg.math.Vector2()
        self.velocity.from_polar((speed, angle))
        
        self.total_time: float = lifetime
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
        # off-screen culling
        if self.pos.x + offset_x > SCREEN_WIDTH or self.pos.x + offset_x < 0:
            return
        if self.pos.y > GAMEPLAY_HEIGHT or self.pos.y < 0:
            return
        
        # particle fades from fully opaque to fully transparent in self.total_time

        # get (r,g,b,a)
        visibility_percentage: float = max(0.0, min(1.0, self.remaining_time / self.total_time))

        alpha: int = int(255 * visibility_percentage) # alpha channel
        colour: tuple[int, int, int, int] = (*self.base_colour, alpha)

        # shrink to nothing in self.total_time
        radius: float = float(self.size * visibility_percentage)
        if radius <= 0:
            return

        # creates temp surface so alpha values can render
        temp_surface: pg.Surface = pg.Surface((radius*2, radius*2), pg.SRCALPHA)
        pg.draw.circle(temp_surface, colour, (radius, radius), radius)
        
        draw_x: float = self.pos.x + offset_x
        screen.blit(temp_surface, (draw_x - radius/2, self.pos.y - radius/2))

class ReverseParticle(Particle):
    """reversed explosion effect (like sucking in to center)
        looks like the normal explosion effect but in reverse
    """
    def __init__(self, spawn_pos: Vector2, 
                 speed: float,
                 lifetime: float, 
                 angle: int,
                 base_colour: tuple[int, int, int]) -> None:
        super().__init__(spawn_pos, 
                         speed=speed,
                         lifetime=lifetime,
                         angle=angle,
                         base_colour=base_colour)

        # calculating the position of the particle if it was a normal explosion and then reversing the velocity
        self.pos: Vector2 = spawn_pos.copy() + self.velocity * self.total_time
        self.velocity = -self.velocity

    def update(self, dt: float) -> None:
        self.pos += self.velocity * dt
        self.remaining_time -= dt
        if self.remaining_time <= 0:
            self.kill()
            del self

    def draw(self, screen: pg.Surface, offset_x: float):
        # particle fades from fully transparent to fully opaque in self.total_time

        # get (r,g,b,a)
        visibility_percentage: float = max(0.0, min(1.0, (self.total_time - self.remaining_time) / self.total_time))
        alpha: int = int(255 * visibility_percentage)
        colour: tuple[int, int, int, int] = (*self.base_colour, alpha)

        radius: float = float(self.size * visibility_percentage)
        if radius >= self.size:
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


def draw_visibility_fade(surface: pg.Surface, player_x: float):
    """Fog near world borders to indicate that player shouldn't go there"""
    width, height = surface.get_size()
    zone = SCREEN_WIDTH // 4

    # Distance from edge
    dist_left  = max(0,  zone - (player_x - -WORLD_WIDTH / 2))
    dist_right = max(0,  zone - (WORLD_WIDTH / 2 - player_x))

    fade = pg.Surface((zone, height), pg.SRCALPHA)

    for x in range(int(dist_left)):
        alpha = int(200 * (1 - (x / zone)))
        fade.fill((255, 255, 255, alpha), rect=pg.Rect(x, 0, 1, height))
    surface.blit(fade, (0, 0))

    fade = pg.Surface((zone, height), pg.SRCALPHA)
    for x in range(int(dist_right)):
        alpha = int(200 * (1 - (x / zone)))
        fade.fill((255, 255, 255, alpha), rect=pg.Rect(zone - 1 - x, 0, 1, height))
    surface.blit(fade, (width - zone, 0))





























"""

  --                                                                         +-..-     
-...-+                                                                       -.....+   
-...--..+                                                                    +---..--  
-..-....-       +-..-+                                                        +-.....- 
 ---....---++  -.....-                  #    ##                               +--.....+
  +-..-......-+....--                  ##     +##                   +-...-+   +.-....-+
   -.-............--                 +#+-......-......              +.....-   --....-+ 
   ----...---....-+               .---..........++..+##+.            +-...-  -.-......-
   +---.--.......-             .++#####+........#- .######.-          +-..-+-...--....-
    +--.-........-            -#. .+####..----..#####. -##-.-+        +-.........--...-
     --.....-....-          -.######-+##-...--..++####++-------       +-..--...--..---+
     +---.....-..-         ---+#######+--+######+------+++------      ----......-----+ 
      +---.....--+        ---+--------+#############+-...--------      ---......----   
        ---....-         -.---+++--+##################-...------.-      +-.....--+     
          -----         +..----..-#####################+..------.-+       +---+        
                        -..----.-+######################-.------..-                    
                        -..---.-+########################-------..-                    
                        -.-----+##########################+---+-..-                    
                       --.-----###########################+-++--..-                    
                        -.----+##########+-----+###########------.-                    
                        -.----########+-.........-+#########-----.-                    
                        +----+#######-.............-########------+                    
                         ----######+-................+######+-----                     
                          ---#####--..................-#####+----                      
                          +--+##+----.................--+###+---                       
                          +..-----------...........-------------                       
                           -...-----------------------------...+                       
                               ----------------------------+-.-                        
                                  +---------------------+                              
                                     +--------------+                                  


"""