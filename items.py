import pygame as pg

from pygame.math import Vector2

import misc

from classes import Player, PlayerBullet, EnemyBullet
from constants import *
from sound import CHARGE_FIRE_SOUND, CHARGED_SOUND

pg.init()

class ChargedBullet(PlayerBullet):
    def __init__(self, x: float, y: float, width: int, height: int, angle, speed: int) -> None:
        super().__init__(x, y, width, height, angle, speed)

class big_shot(object):
    """NOW'S YOUR CHANCE TO BE A- what?
    
    Player can charge up a bigger shot by holding
    shoot key and releasing.
    """

    def __init__(self) -> None:
        self.charge: float = 0.0
        self.max_charge: float = 1.2
        self.charged: bool = False
        self.charging: bool = False
        self.color: tuple[int, int, int] = RED

        self.speed: int = 50

    def update(self, player: Player, dt: float, **kwargs) -> None:
                
        keys = pg.key.get_pressed()
        particles = kwargs.get("particles")

        if keys[pg.K_SPACE]:
            self.charge += dt

            if not self.charged and self.charge >= self.max_charge:
                self.charged = True
                if particles is not None:
                    particles.append(
                        misc.explosion_effect(
                            player.pos, 
                            number=30,
                            min_speed=300,
                            max_speed=500,
                            min_lifetime=0.2,
                            max_lifetime=0.5,
                            base_colour=(255,255,255),
                        )
                    )
                pg.mixer.Channel(6).play(CHARGED_SOUND, maxtime=1800)
        else:
            if self.charge >= self.max_charge:
                    print("BIGSHOT!")
                    player.bullets.append(ChargedBullet(player.rect.x + (player.rect.width // 2), 
                                                        player.rect.y + (player.rect.height // 2), 
                                                        width=30,
                                                        height=30, 
                                                        angle = player.direction * -180, 
                                                        speed=self.speed))
                    pg.mixer.Channel(6).play(CHARGE_FIRE_SOUND, maxtime=1800)
            self.charge = 0
            self.charged = False
    

class deployable_shield(object):
    """Shield consumable that player can deploy to block bullets."""

    def __init__(self) -> None:
        self.max_health: int = 200
        self.health: int = self.max_health
        self.rect: pg.Rect = pg.Rect(0, 0, 20, 60)
        self.position: Vector2 = Vector2(0, 0)
        self.deployed: bool = False

        # Pulse effect
        self.max_alpha: float = 255.0           
        self.alpha: float = self.max_alpha
        self.pulse_speed: float = 200.0
        self.pulse_direction: int = -1

    def deploy(self, pos: Vector2) -> None:
        if self.deployed:
            return

        self.position = pos.copy()
        self.rect.topleft = (int(self.position.x), int(self.position.y))
        self.deployed = True
        print("Shield deployed!")

    def update(self, **kwargs) -> None:
        if not self.deployed:
            return

        offset_x = kwargs.get("offset_x", 0)
        self.rect.x = int(self.position.x + offset_x)
        self.rect.y = int(self.position.y)

        dt: float = kwargs.get("dt", 0)

        self.max_alpha = max(0, (self.health / self.max_health) * 255)

        self.alpha += self.pulse_direction * self.pulse_speed * dt
        if self.alpha <= 0:
            self.alpha = 0
            self.pulse_direction = 1
        elif self.alpha >= self.max_alpha:
            self.alpha = self.max_alpha
            self.pulse_direction = -1

        if "surface" in kwargs:
            self.draw(kwargs["surface"])

    def draw(self, surface: pg.Surface) -> None:
        shield_surface: pg.Surface = pg.Surface((self.rect.width, self.rect.height), pg.SRCALPHA)
        shield_surface.fill((255, 255, 255, int(self.alpha)))
        surface.blit(shield_surface, (self.rect.x, self.rect.y))
