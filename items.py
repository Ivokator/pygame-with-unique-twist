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
        self.size: int = 30

        self.name: str = "Charge Fire"
        self.desc: str = "Charge up a bigger shot by holding the shoot key and releasing."
        self.price: int = 32
        self.level: int = 1
        self.max_level: int = 4
        self.upgrade_costs: list[int] = [
            12, 26, 50
        ]

        self.stats: dict[str, int | float] = {
            "Size": self.size,
            "Charge time": self.max_charge,
            "Speed": self.speed, 
        }

        self.upgrade_amount: dict[str, int | float] = {
            "Size": 5,
            "Charge time": -0.3,
            "Speed": 8, 
        }
        
    
    def upgrade(self) -> None:
        self.size += int(self.upgrade_amount["Size"])
        self.max_charge += self.upgrade_amount["Charge time"]
        self.speed += int(self.upgrade_amount["Speed"])
        
        self.stats = {
            "Size": self.size,
            "Charge time": self.max_charge,
            "Speed": self.speed, 
        }
    
    def use(self, player=None, dt=None, particles=None, keybinds=None, **kwargs) -> None:
        pass

    def update(self, player: Player, dt: float, keybinds: dict[str,int], **kwargs) -> None:
        keys = pg.key.get_pressed()
        particles = kwargs.get("particles")

        shoot_key = keybinds.get("shoot", pg.K_SPACE)
        if keys[shoot_key]:
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
                                                        width=self.size,
                                                        height=self.size, 
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
        self.rect: pg.Rect = pg.Rect(0, 0, 20, 90)
        self.position: Vector2 = Vector2(0, 0)
        self.deployed: bool = False

        # Pulse effect
        self.max_alpha: float = 255.0           
        self.alpha: float = self.max_alpha
        self.pulse_speed: float = 200.0
        self.pulse_direction: int = -1

        self.name: str = "Shield"
        self.desc: str = "Spawns a shield which can hold off enemy fire."
        self.price: int = 25
        self.level: int = 1
        self.max_level: int = 4
        self.upgrade_costs: list[int] = [
            18, 28, 39
        ]

        self.stats: dict[str, str | int | float] = {
            "Width": self.rect.width,
            "Height": self.rect.height,
            "Health": self.max_health,
        }

        self.upgrade_amount: dict[str, int | float] = {
            "Width": 10,
            "Height": 40,
            "Health": 30,
        }

    def use(self, player: Player, **kwargs) -> None:
        if not self.deployed:
            self.deploy(player.pos)

    def deploy(self, pos: Vector2) -> None:
        if self.deployed:
            return

        self.position = pos.copy()
        self.rect.topleft = (int(self.position.x), int(self.position.y))
        self.deployed = True
        print("Shield deployed!")
    
    def reset(self) -> None:
        self.deployed = False
        self.health = self.max_health
        self.alpha = self.max_alpha
        self.pulse_direction = -1

    def upgrade(self) -> None:
        self.rect.width += int(self.upgrade_amount["Width"])
        self.rect.height += int(self.upgrade_amount["Height"])
        self.max_health += int(self.upgrade_amount["Health"])

        self.stats = {
            "Width": self.rect.width,
            "Height": self.rect.height,
            "Health": self.max_health,
        }

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


class dash(object):
    """Dash upgrade: when activated, player lunges forward quickly. How original."""

    def __init__(self) -> None:
        self.dash_distance: float = 200.0 # pixels
        self.dash_cooldown: float = 1.5
        self._cooldown_timer: float = 0.0

        self.name: str = "Dash"
        self.desc: str = "Press Left Shift to dash forward. Cooldown applies."
        self.price: int = 20
        self.level: int = 1
        self.max_level: int = 4
        self.upgrade_costs: list[int] = [
            10, 21, 33
        ]

        self.stats: dict[str, float] = {
            "Dash distance": self.dash_distance,
            "Cooldown": self.dash_cooldown,
        }

        self.upgrade_amount: dict[str, float] = {
            "Dash distance": 50.0,
            "Cooldown": -0.3,
        }

    def upgrade(self) -> None:
        if self.level < self.max_level:
            self.level += 1
            self.dash_distance += self.upgrade_amount["Dash distance"]
            self.dash_cooldown = max(0.1, self.dash_cooldown + self.upgrade_amount["Cooldown"])
            self.stats = {
                "Dash distance": self.dash_distance,
                "Cooldown": self.dash_cooldown,
            }

    def update(self, player: Player, dt: float, **kwargs) -> None:
        self._cooldown_timer += dt

    def use(self, player: Player, **kwargs) -> None:
         if self._cooldown_timer >= self.dash_cooldown:
            dir_multiplier = -1 if player.direction == 1 else 1
            
            player.pos.x += dir_multiplier * self.dash_distance
            player.pos.x = max(-WORLD_WIDTH // 2, min(WORLD_WIDTH // 2, player.pos.x))

            player.rect.centerx = int(player.pos.x)
            self._cooldown_timer = 0.0

            # Optional particle effect:
            particles = kwargs.get("particles")
            if particles is not None:
                particles.append(
                    misc.explosion_effect(
                        Vector2(player.pos.x, player.pos.y),
                        number=20,
                        min_speed=200,
                        max_speed=400,
                        min_lifetime=0.1,
                        max_lifetime=0.3,
                        base_colour=(200, 200, 255),
                        reversed=True
                    )
                )