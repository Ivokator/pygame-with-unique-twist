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
        self.smart_bombs: int = 3

        # Physics parameters
        self.velocity: Vector2 = Vector2(0, 0)
        self.accel_x: float = 0.0
        self.accel_y: float = 0.0
        self.max_speed_x: int = 10
        self.max_speed_y: int = 7
        self.accel_rate: int = 50

        self.draw_x = x

        # careful that drag does not exceed accel_rate
        self.drag_x: int = 1 
        self.drag_y: int = 50

        self.direction = 0  # left:0, right:1

        self.bullets: typing.List[PlayerBullet] = []
        self.bullet_cooldown_ms: float = 100
        self.cooldown_timer: int = 0
        self.bullet_speed: int = 30

        self.lookahead_compensation: float = 0.0

        # given positions are defaulted
        self.hitbox_top = pg.Rect(self.draw_x + self.rect.width // 7, self.pos.y, self.rect.width // 4, self.rect.height * 2 // 3,)
        self.hitbox_bottom = pg.Rect(self.draw_x + self.rect.width // 7, self.pos.y + self.rect.height * 2 // 3, self.rect.width * 6 // 7, self.rect.height // 4)
        
        #player states
        self.state = Player.States.IDLE

        self.idle_sprite = pg.image.load(os.path.join("images", "player", "idle.png")).convert_alpha()
        self.idle_sprite = pg.transform.scale(self.idle_sprite, (width, self.idle_sprite.get_height() / self.idle_sprite.get_width() * width))

        self.move_sprites = [pg.image.load(os.path.join("images", "player", "moving1.png")).convert_alpha(),
                             pg.image.load(os.path.join("images", "player", "moving2.png")).convert_alpha(),
                             pg.image.load(os.path.join("images", "player", "moving3.png")).convert_alpha(),
                             ]
        
        for i, sprite in enumerate(self.move_sprites):
            self.move_sprites[i] = pg.transform.scale(sprite, (width, sprite.get_height() / sprite.get_width() * width))
        
        self.move_sprites_pointer: int = 0
        self.move_sprites_timer: float = 0.0
        
        # current image!
        self.image = self.idle_sprite
        self.smart_bomb_image = pg.image.load(os.path.join("images", "player", "smart_bomb.png")).convert_alpha()

        self.smart_bomb_height: int = TOP_WIDGET_HEIGHT // 8
        self.smart_bomb_width: int = int((self.smart_bomb_image.get_width() / self.smart_bomb_image.get_height()) * self.smart_bomb_height)

        self.smart_bomb_image = pg.transform.scale(self.smart_bomb_image, (self.smart_bomb_width, self.smart_bomb_height))

        self.is_reviving: bool = False
        self._revive_timer: float = 0.0
        self.REVIVE_DURATION: float = 1.0  # seconds

        self.invulnerable: bool = False
        self.invul_timer: float = 0.0
        self.INVUL_DURATION: float = 2.0

    def health_indicator(self, offset_x: float) -> pg.sprite.Group | None:
        if self.state == Player.States.DEAD:
            return None
        
        # emit smoke/sparks based on health
        if self.health < 100:
            intensity = max(1, (100 - self.health) // 30)

            if random.randint(0, max(5, self.health // 4)) == 0:
                for _ in range(intensity):

                    # smoke/sparks
                    return misc.explosion_effect(Vector2(self.hitbox_top.x - offset_x, self.hitbox_top.y + 20),
                                        number = 7, 
                                        min_lifetime=0.2, 
                                        max_lifetime=0.7,
                                        min_angle=230,
                                        max_angle=310,
                                        base_colour=random.choice([(63, 63, 63), (207, 195, 40), (255,140,0)]))
        return None

    def move(self, dt: float, keybind: dict[str, int]) -> None:
        if self.state == Player.States.DEAD:
            return

        self.move_sprites_timer += dt

        keys = pg.key.get_pressed()

        # HORIZONTAL ACCELERATION 
        if keys[keybind["move_left"]]:
            self.accel_x = -self.accel_rate
            self.direction = 1
        elif keys[keybind["move_right"]]:
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

        # VERTICAL ACCELERATION
        if keys[keybind["move_up"]]:
            self.accel_y = -self.accel_rate
        elif keys[keybind["move_down"]]:
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

        # clamp to max y-axis speed
        self.velocity.y = max(-self.max_speed_y, min(self.velocity.y, self.max_speed_y))

        self.pos += self.velocity

        # world border clamp
        if self.pos.x < -WORLD_WIDTH // 2:
                self.pos.x = -WORLD_WIDTH // 2
                self.velocity.x = 0
        elif self.pos.x > WORLD_WIDTH // 2:
            self.pos.x = WORLD_WIDTH // 2
            self.velocity.x = 0
        self.rect.x = int(self.pos.x)


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
            bullet = PlayerBullet(self.rect.x + (self.rect.width // 2), self.rect.y + (self.rect.height // 2), width=10, height=10, angle = self.direction * -180, speed=self.bullet_speed)
            self.bullets.append(bullet)

            # sound
            random_sound = random.choice([sound.PLAYER_FIRE1, sound.PLAYER_FIRE2, sound.PLAYER_FIRE3, sound.PLAYER_FIRE4,])
            random_sound.play()
        
    def gets_hit_by(self, source) -> None:
        """Damages player according to the source of damage.
        (eg: class Enemy does 20 damage)
        """
        if self.state == Player.States.DEAD:
            return
        if self.invulnerable:
            return

        if isinstance(source, EnemyBullet):
            self.health -= 20

        elif isinstance(source, (Enemy, Mutant, Baiter)):
            self.health -= 100

        print(self.health)

    def death(self) -> pg.sprite.Group:
        self.state = Player.States.DEAD
        return misc.explosion_effect(self.pos, 70)
        
    def revive(self, offset_x: float) -> pg.sprite.Group:
        self.accel_x = 0.0
        self.accel_y = 0.0
        self.velocity = Vector2(0,0)
        self.health = 100
        return misc.explosion_effect(Vector2(self.pos.x + self.rect.width // 2, self.pos.y + self.rect.height // 2), min_lifetime=0.7, max_lifetime=1.2, min_speed=400, max_speed=500, reversed=True)
    
    def update(self, offset_x: float, dt: float, keybinds: dict[str, int]) -> None:
        self.draw_x = int(self.pos.x + offset_x)
        self.rect.x, self.rect.y = int(self.draw_x), int(self.pos.y)
        self.pos.y = max(0, min(GAMEPLAY_HEIGHT - self.rect.height, self.pos.y))

        if self.invulnerable:
            self.invul_timer += dt
            if self.invul_timer >= self.INVUL_DURATION:
                self.invulnerable = False

        # move animation / thruster sound effect
        keys = pg.key.get_pressed()
        if keys[keybinds["move_left"]] or keys[keybinds["move_right"]]:
            
            self.image = self.move_sprites[self.move_sprites_pointer]
            
            if self.move_sprites_timer > 0.1:
                self.move_sprites_timer = 0
                self.move_sprites_pointer = (self.move_sprites_pointer + 1) % (len(self.move_sprites))

            if not pg.mixer.music.get_busy():
                
                pg.mixer.music.play(loops=-1, start=random.uniform(0,7), fade_ms=50) # play thruster sound effect

        else:
            self.image = self.idle_sprite
            pg.mixer.music.fadeout(50)

    def draw(self, surface: pg.Surface) -> None:
        if self.state == Player.States.DEAD:
            return
        
        if self.invulnerable:
            period = 0.1
            if int(self.invul_timer / period) % 2 == 0:
                # draw normally
                if self.direction == 0:
                    surface.blit(self.image, (self.draw_x, self.rect.y))
                else:
                    flipped = pg.transform.flip(self.image, True, False)
                    surface.blit(flipped, (self.draw_x, self.rect.y))
            return


        if self.direction == 0:
            surface.blit(self.image, (self.draw_x, self.rect.y))
            self.hitbox_top = pg.Rect(self.draw_x + self.rect.width // 7, self.pos.y, self.rect.width // 4, self.rect.height * 2 // 3,)
            self.hitbox_bottom = pg.Rect(self.draw_x + self.rect.width // 7, self.pos.y + self.rect.height * 2 // 3, self.rect.width * 6 // 7, self.rect.height // 4)
        else:
            self.flipped = pg.transform.flip(self.image, True, False)
            surface.blit(self.flipped, (self.draw_x, self.rect.y))

            self.hitbox_top = pg.Rect(self.draw_x + self.rect.width * 6 // 7 - self.rect.width // 4, self.pos.y, self.rect.width // 4, self.rect.height * 2 // 3,)
            self.hitbox_bottom = pg.Rect(self.draw_x, self.pos.y + self.rect.height * 2 // 3, self.rect.width * 6 // 7, self.rect.height // 4)

        #pg.draw.rect(surface, WHITE, self.hitbox_top)

class PlayerGroup(pg.sprite.GroupSingle):
    """
    A sprite group that manages persistent player statistics such as points.
    Unlike the Player class (representing the player's ship, which is reloaded or reset each round),
    PlayerGroup is intended to track stats that persist across rounds, such as score, ships, or achievements.
    """
    def __init__(self) -> None:
        super().__init__()
        self.score: int = 0
        self.coins: int = 0

        self.upgrades: list = []
        
        self.ships: int = 5
        self.ships_awarded: int = 0

        self.lives_image: pg.Surface = pg.image.load(os.path.join("images", "player", "idle.png")).convert_alpha()
        self.lives_height: int = TOP_WIDGET_HEIGHT // 8
        self.lives_width: int = int((self.lives_image.get_width() / self.lives_image.get_height()) * self.lives_height)

        self.lives_image = pg.transform.scale(self.lives_image, (self.lives_width, self.lives_height))

    def update_items(self, dt: float, collision_list: list, surface: pg.Surface, offset_x: float, keybinds, particles: list[pg.sprite.Group]) -> None:
        """Updates all items in player's inventory."""
        for item in self.upgrades:
            if hasattr(item, "update"):
                item.update(player=self.sprite, 
                            dt=dt, 
                            collision_list=collision_list, 
                            surface=surface,
                            offset_x=offset_x,
                            keybinds=keybinds,
                            particles=particles,

                            )

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
       self.rect.x = int(screen_x)
       pg.draw.circle(screen, WHITE, (screen_x, self.y), self.radius)
    
    def update(self) -> None:
        self.x += self.velocity.x
        self.y += self.velocity.y

        self.rect.x, self.rect.y = int(self.x), int(self.y)

class EnemyState(Enum):
    ATTACKING = 1
    CAPTURING = 2


class Enemy(pg.sprite.Sprite):
    def __init__(self, spawn_x: int, spawn_y: int) -> None:
        super().__init__()
        self.state = EnemyState.ATTACKING
        self.spawn_x = spawn_x
        self.spawn_y = spawn_y
        self.draw_x: float | int = spawn_x
        self.pos = Vector2(spawn_x, spawn_y)
        self.width = 50
        self.height = 50
        self.rect: pg.Rect = pg.Rect(spawn_x, spawn_y, self.width, self.height)
        self.speed = 1.2
        self.max_speed = 2.0
        self.acceleration = 0.10
        self.velocity = Vector2(0, 0)
        self.chase_distance = 1000
        self.offset_x = 0
        self.bullets: typing.List[EnemyBullet] = []
        self.idle_sprite = pg.image.load(os.path.join("images", "enemies", "lander.png")).convert_alpha()
        self.image = pg.transform.scale(self.idle_sprite, (self.width, self.idle_sprite.get_height() / self.idle_sprite.get_width() * self.width))
        self.wander_angle = random.uniform(0, 360)
        self.wander_timer = 0.0
        self.chase_probability = 0.6
        self.closest_humanoid: Vector2 = Vector2(0, 0)
        self.captured_humanoid = None
        self.scanned = False

    def death(self, sound_on: bool = True) -> pg.sprite.Group:
        if self.captured_humanoid is not None:
            self.captured_humanoid.state = HumanoidState.FALLING
            self.captured_humanoid = None
        if sound_on:
            random_sound: pg.mixer.Sound = random.choice([sound.ENEMY_EXPLOSION1, sound.ENEMY_EXPLOSION2, sound.ENEMY_EXPLOSION3, sound.ENEMY_EXPLOSION4, sound.ENEMY_EXPLOSION5])
            for i in range(1,6):
                if not pg.mixer.Channel(i).get_busy():
                    print(f"Channel {i}: {random_sound}")
                    pg.mixer.Channel(i).play(random_sound, maxtime=1800)
                    break

        self.kill()
        return misc.explosion_effect(self.pos, 50, min_lifetime=0.8, max_lifetime=2.0)

    def draw(self, surface) -> None:
        surface.blit(self.image, (self.draw_x, self.rect.y))

        #pg.draw.rect(surface, GREEN, pg.Rect(self.draw_x, self.pos.y, self.width, self.height))

    def update(self, offset_x: float, player, humanoids_pos, screen) -> None:
        if hasattr(player, "state") and getattr(player, "state", None) == Player.States.DEAD:
            self.draw_x = self.pos.x + offset_x
            self.rect.x = int(self.draw_x)
            self.rect.y = int(self.pos.y)
            return
        player_pos = player.pos
        if self.state == EnemyState.ATTACKING:
            distance = self.pos.distance_to(player_pos)
            if distance < self.chase_distance and random.random() < self.chase_probability:
                direction = (player_pos - self.pos).normalize() if distance != 0 else Vector2(0, 0)
                self.wander_timer += 1
                if self.wander_timer > 30:
                    self.wander_angle = random.uniform(-10, 10)
                    self.wander_timer = 0

                # Prevent enemy from going off screen vertically
                if self.pos.y < 0:
                    self.pos.y = 0
                    self.velocity.y = abs(self.velocity.y)
                elif self.pos.y > GAMEPLAY_HEIGHT - self.height:
                    self.pos.y = GAMEPLAY_HEIGHT - self.height
                    self.velocity.y = -abs(self.velocity.y)

                angle = math.atan2(direction.y, direction.x) + math.radians(self.wander_angle)
                move_direction = Vector2(math.cos(angle), math.sin(angle))
            else:
                self.wander_timer += 1
                if self.wander_timer > 30:
                    self.wander_angle = random.uniform(0, 2 * math.pi)
                    self.wander_timer = 0
                move_direction = Vector2(math.cos(self.wander_angle), math.sin(self.wander_angle))
            desired_velocity = move_direction * self.speed
            self.velocity += (desired_velocity - self.velocity) * self.acceleration
            if self.velocity.length() > self.max_speed:
                self.velocity.scale_to_length(self.max_speed)
            self.pos += self.velocity
        elif self.state == EnemyState.CAPTURING:
            direction = (self.closest_humanoid - self.pos).normalize() if self.closest_humanoid != self.pos else Vector2(0, 0)
            angle = math.atan2(direction.y, direction.x)
            move_direction = Vector2(math.cos(angle), math.sin(angle))
            desired_velocity = move_direction * self.speed
            self.velocity += (desired_velocity - self.velocity) * self.acceleration
            if self.velocity.length() > self.max_speed:
                self.velocity.scale_to_length(self.max_speed)
            self.pos += self.velocity
            if self.pos.distance_to(self.closest_humanoid) < 10 and self.captured_humanoid is None:
                for humanoid in humanoids_pos:
                    if humanoid.pos == self.closest_humanoid and humanoid.state != HumanoidState.CAPTURED:
                        humanoid.state = HumanoidState.CAPTURED
                        self.captured_humanoid = humanoid
                        break
            if self.pos.y < CAPTURE_HEIGHT:
                if self.captured_humanoid is not None:
                    self.captured_humanoid.state = HumanoidState.FALLING
                    self.captured_humanoid.state = HumanoidState.KILLED
                    self.captured_humanoid = None

                if hasattr(self, "group") and self.group is not None:
                    print("humanoid converted to mutant!")
                    self.group.add_mutant(self.pos.x, 0)

                self.state = EnemyState.ATTACKING

        self.pos.y = max(0, min(self.pos.y, GROUND_Y + 50 - self.height)) # + 50 so landers can still reach humanoids
        
        self.draw_x = self.pos.x + offset_x
        self.rect.x = int(self.draw_x)
        self.rect.y = int(self.pos.y)

    def fire_bullet(self, player_x: float, player_y: float) -> None:
        if getattr(self, "state", None) == EnemyState.CAPTURING:
            return
        dx = player_x - self.pos.x
        dy = player_y - self.pos.y
        angle = math.degrees(math.atan2(dy, dx)) + random.randint(-2, 2)
        spawn_x = self.pos.x + self.width / 2
        spawn_y = self.pos.y + self.height / 2
        bullet = EnemyBullet(spawn_x, spawn_y, radius=5, speed=6, angle=angle)
        self.bullets.append(bullet)

class Mutant(pg.sprite.Sprite):
    def __init__(self, spawn_x: int, spawn_y: int) -> None:
        super().__init__()
        self.pos: Vector2 = Vector2(spawn_x, spawn_y)
        self.draw_x: float | int = spawn_x

        # IN PIXELS!!!
        self.speed: float = 450.0
        self.max_speed: float = 700.0

        self.velocity: Vector2 = Vector2(0, 0)
        self.acceleration: float = 0.25

        self.width: int = 40
        self.height: int = 40

        self.rect: pg.Rect = pg.Rect(spawn_x, spawn_y, self.width, self.height)

        self.idle_sprite: pg.Surface = pg.image.load(os.path.join("images", "enemies", "mutant.png")).convert_alpha() \
            if os.path.exists(os.path.join("images", "enemies", "mutant.png")) \
            else pg.Surface((self.width, self.height))
        
        self.image: pg.Surface = pg.transform.scale(self.idle_sprite, (self.width, self.idle_sprite.get_height() / self.idle_sprite.get_width() * self.width))

        # wander
        self.wander_timer: float = 0.0
        self.wander_angle: float = random.uniform(0, 2*math.pi)
        self.change_interval: float = 0.5

        # zig-zag
        self._oscillator: float = 0.0 # running time for sine oscillation
        self._zigzag_freq: float = 0.3 + random.uniform(-0.1, 0.5)# oscillations per second
        self._zigzag_amp: float = 0.7 + random.uniform(-0.4, 0.2)# how strongly to pull sideways (0-1 please don't set this to be any more i swear)

        # shooting
        self._shoot_chance_per_second: float = 0.1
        self.bullets: list[EnemyBullet] = []
    
    def draw(self, surface) -> None:
        surface.blit(self.image, (self.draw_x, self.rect.y))

    def update(self, offset_x: float, player: Player, humanoids_pos, screen: pg.Surface, dt: float) -> None:
        if player is None:
            return
        
        if hasattr(player, "state") and getattr(player, "state", None) == Player.States.DEAD:
            self.draw_x = self.pos.x + offset_x
            self.rect.x = int(self.draw_x)
            self.rect.y = int(self.pos.y)
            return
        
        print(f"Mutant: dt={dt}, pos={self.pos}")
        
        to_player = player.pos - self.pos
        distance = to_player.length()

        if distance > 0:
            base_dir = to_player.normalize()
        else:
            base_dir = Vector2(0, 0)

        # zig-zag effect
        self._oscillator += dt * self._zigzag_freq * 2 * math.pi
        perp = Vector2(-base_dir.y, base_dir.x) # perpendicular
        zig_offset = math.sin(self._oscillator) * self._zigzag_amp

        # direction of sin [-1, 1] combined with direction
        zigzag_dir = (base_dir + perp * zig_offset).normalize()

        desired_velocity = zigzag_dir * self.speed

        self.velocity += (desired_velocity - self.velocity) * self.acceleration
        
        if self.velocity.length() > self.max_speed:
            self.velocity.scale_to_length(self.max_speed)

        self.pos += self.velocity * dt

        # clamp vertically
        self.pos.y = max(0, min(GAMEPLAY_HEIGHT - self.height, self.pos.y))

        self.draw_x = self.pos.x + offset_x
        self.rect.x = int(self.draw_x)
        self.rect.y = int(self.pos.y)

        # randomly shoot at player
        if random.random() < (self._shoot_chance_per_second * dt):
            self.fire_bullet(player.pos.x, player.pos.y)

    def death(self, sound_on: bool = True) -> pg.sprite.Group:
        if sound_on:
            random_sound: pg.mixer.Sound = random.choice([sound.ENEMY_EXPLOSION1, sound.ENEMY_EXPLOSION2, sound.ENEMY_EXPLOSION3, sound.ENEMY_EXPLOSION4, sound.ENEMY_EXPLOSION5])
            for i in range(1,6):
                if not pg.mixer.Channel(i).get_busy():
                    print(f"Channel {i}: {random_sound}")
                    pg.mixer.Channel(i).play(random_sound, maxtime=1800)
                    break

        self.kill()
        return misc.explosion_effect(self.pos, 50, min_lifetime=0.8, max_lifetime=2.0)

    def fire_bullet(self, player_x: float, player_y: float) -> None:
        dx = player_x - self.pos.x
        dy = player_y - self.pos.y

        angle = math.degrees(math.atan2(dy, dx)) + random.uniform(-4, 4)
        spawn_x = self.pos.x + self.width / 2
        spawn_y = self.pos.y + self.height / 2

        bullet = EnemyBullet(spawn_x, spawn_y, radius=5, speed=7, angle=angle)
        self.bullets.append(bullet)

class Baiter(pg.sprite.Sprite):
    # similar to old mutant code
    def __init__(self, spawn_x: int, spawn_y: int) -> None:
        super().__init__()
        self.speed: float = 9.5 + random.uniform(-1, 1)
        self.max_speed: float = 13.0 + random.uniform(-1, 1)
        self.acceleration: float = 0.04 + random.uniform(-0.01, 0.05)
        self.velocity: Vector2 = Vector2(0, 0)
        self.pos = Vector2(spawn_x, spawn_y)

        self.width: int = 35
        self.height: int = 18
        self.rect: pg.Rect = pg.Rect(spawn_x, spawn_y, self.width, self.height)
        self.colour: tuple[int,int,int] = (200, 50, 50)

    def update(self, offset_x: float, player: Player) -> None:
        # first check if player is dead
        if hasattr(player, "state") and getattr(player, "state", None) == Player.States.DEAD:
            self.draw_x: float = self.pos.x + offset_x
            self.rect.x = int(self.draw_x)
            self.rect.y = int(self.pos.y)
            return
        
        # randomize pod's direction slightly
        angle_offset = random.uniform(-0.15, 0.15)  # radians
        direction_vector = (player.pos - self.pos)

        if direction_vector.length() != 0:
            direction_vector = direction_vector.normalize()

            cos_theta = math.cos(angle_offset)
            sin_theta = math.sin(angle_offset)
            x, y = direction_vector.x, direction_vector.y

            direction = Vector2(
            x * cos_theta - y * sin_theta,
            x * sin_theta + y * cos_theta
            )
        else:
            direction = Vector2(0, 0)

        desired_velocity: Vector2 = direction * self.speed
        self.velocity += (desired_velocity - self.velocity) * self.acceleration

        if self.velocity.length() > self.max_speed:
            self.velocity.scale_to_length(self.max_speed)

        self.pos += self.velocity
        self.pos.y = max(0, min(GAMEPLAY_HEIGHT - self.height, self.pos.y)) # clamp vertically

        self.draw_x = self.pos.x + offset_x
        self.rect.x = int(self.draw_x)
        self.rect.y = int(self.pos.y)

    def draw(self, screen: pg.Surface) -> None:
        pg.draw.rect(screen, self.colour, self.rect)

    def death(self, sound_on: bool = True) -> pg.sprite.Group:
        if sound_on:
            random_sound: pg.mixer.Sound = random.choice([sound.ENEMY_EXPLOSION1, sound.ENEMY_EXPLOSION2, sound.ENEMY_EXPLOSION3, sound.ENEMY_EXPLOSION4, sound.ENEMY_EXPLOSION5])
            for i in range(1,6):
                if not pg.mixer.Channel(i).get_busy():
                    print(f"Channel {i}: {random_sound}")
                    pg.mixer.Channel(i).play(random_sound, maxtime=1800)
                    break

        self.kill()
        return misc.explosion_effect(self.pos, 50, min_lifetime=0.8, max_lifetime=2.0)

class EnemyGroup(pg.sprite.Group):
    def __init__(self) -> None:
        super().__init__()
        self.bullets: typing.List[EnemyBullet] = []
        self.capturing_limit: int = 2
        self.capturing_timer: float = 0.0
        self.capturing_interval: float = 3.0

        self.baiters_active_timer: float = 0.0
        self.baiter_timer: float = 0.0
        self.time_until_baiters_spawn: float = 15.0

    def add(self, *sprites) -> None:
        super().add(*sprites)
        for sprite in sprites:
            if isinstance(sprite, (Enemy, Mutant)):
                if not hasattr(sprite, "group"):
                    sprite.group = self

    def add_mutant(self, x: float, y: float) -> None:
        mutant = Mutant(int(x), int(y))
        self.add(mutant)
    
    def spawn_pod(self, player: Player) -> None:
        min_distance = SCREEN_WIDTH
        while True:
            spawn_x = random.randint(-WORLD_WIDTH // 2, WORLD_WIDTH // 2)
            spawn_y = random.randint(TOP_WIDGET_HEIGHT, GAMEPLAY_HEIGHT)

            # make sure pod is far away enough
            if abs(spawn_x - player.pos.x) > min_distance or abs(spawn_y - player.pos.y) > min_distance:
                break

        self.add(Baiter(spawn_x, spawn_y))

    def update(self, offset_x: float, player, humanoids_pos, screen, dt: float, current_wave: int) -> None:
        
        # only spawn baiters on level 2 onwards
        if current_wave >= 2:
            if self.baiters_active_timer > self.time_until_baiters_spawn:
                self.baiter_timer += dt
                if self.baiter_timer > 10.0:
                    self.spawn_pod(player)
                    self.baiter_timer = 0
            else:
                self.baiters_active_timer += dt


        self.capturing_timer += dt

        capturing_enemies = [e for e in self.sprites() if getattr(e, "state", None) == EnemyState.CAPTURING]

        if self.capturing_timer >= self.capturing_interval:
            idle_enemies = [e for e in self.sprites() if getattr(e, "state", None) == EnemyState.ATTACKING]

            if len(capturing_enemies) < self.capturing_limit and idle_enemies and humanoids_pos:
                chosen = random.choice(idle_enemies) # YOU ARE THE CHOSEN ONE!!!
                closest_humanoid = min(humanoids_pos, key=lambda h: chosen.pos.distance_to(h.pos))

                chosen.closest_humanoid = closest_humanoid.pos
                chosen.state = EnemyState.CAPTURING # the chosen one to die...
                chosen.scanned = True

                self.capturing_timer = 0.0

        for enemy in self.sprites():
            self.bullets += getattr(enemy, "bullets", [])
            if hasattr(enemy, "bullets"):
                enemy.bullets.clear()

            if isinstance(enemy, Enemy):
                enemy.update(offset_x, player, humanoids_pos, screen)
            elif isinstance(enemy, Mutant):
                enemy.update(offset_x, player, humanoids_pos, screen, dt)
            elif isinstance(enemy, Baiter):
                enemy.update(offset_x, player) # AAAAAAAAAAAAAAAAAA

            enemy.draw(screen)

class MiniMap(pg.sprite.Group):
    def __init__(self) -> None:
        super().__init__()
        self.surface: pg.Surface = pg.Surface((SCREEN_WIDTH // 3, TOP_WIDGET_HEIGHT - TOP_WIDGET_LINE_THICKNESS // 2))

        # fast reference
        self.surface_width: int = self.surface.get_width()
        self.surface_height: int = self.surface.get_height()

        self.visible_area_width: int = self.surface_width // 12

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
            icon_x = norm_x * self.surface_width - (self.icon_size / 2) + (self.surface_width / 2) - (self.visible_area_width / 4)

            icon_y: float = (sprite.pos.y / GAMEPLAY_HEIGHT) * self.surface_height - (self.icon_size / 2)

            # avoids drawing icons that are outside of the surface and cannot be seen
            #if icon_x > self.surface_width or icon_x < -self.icon_size:
            #    continue

            # clamp inside minimap
            icon_x = max(0, min(self.surface_width  - self.icon_size, icon_x))
            icon_y = max(0, min(self.surface_height - self.icon_size, icon_y))

            if isinstance(sprite, Humanoid):
                pg.draw.rect(self.surface, DARK_GREY, pg.Rect(icon_x, icon_y, self.icon_size * 0.8, self.icon_size))
            elif isinstance(sprite, Player):
                pg.draw.rect(self.surface, WHITE, pg.Rect(icon_x, icon_y, self.icon_size, self.icon_size))
            elif isinstance(sprite, Mutant):
                pg.draw.rect(self.surface, (200, 10, 200), pg.Rect(icon_x, icon_y, self.icon_size, self.icon_size))
            elif isinstance(sprite, Enemy):
                pg.draw.rect(self.surface, GREEN, pg.Rect(icon_x, icon_y, self.icon_size, self.icon_size))
            elif isinstance(sprite, Baiter):
                pg.draw.rect(self.surface, RED, pg.Rect(icon_x, icon_y, self.icon_size * 0.6, self.icon_size * 0.6))
            

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
    KILLED = 6

class Humanoid(pg.sprite.Sprite):
    def __init__(self, x: int, y: int) -> None:
        super().__init__()
        self.width = 10
        self.height = 20
        self.draw_x: int | float = x

        self.pos: Vector2 = Vector2(x, y)

        self.state: HumanoidState = HumanoidState.IDLE
        self.speed: float = -0.5
        self.fall_speed: float = 2.0
        self.fall_time: float = 0.0

        self.walk_speed: float = 2.0
        self.walking: bool = False

    def draw(self, screen) -> None:
        self.rect = pg.Rect(self.draw_x, self.pos.y, self.width, self.height)
        pg.draw.rect(screen, DARK_GREY, self.rect)

    def update(self, offset_x: float, dt: float, particles: list[pg.sprite.Group], player_group: PlayerGroup, pop_ups: list[pg.sprite.Sprite], player=None | Player) -> None:
        self.draw_x = self.pos.x + offset_x

        if self.state == HumanoidState.IDLE:
            if not hasattr(self, "idle_direction"):
                self.idle_direction = random.choice([-1, 1])
            if not hasattr(self, "walk_velocity"):
                self.walk_velocity = Vector2(self.idle_direction * self.walk_speed, 0)

            self.pos.x += self.walk_velocity.x * dt

            if self.pos.x < -WORLD_WIDTH // 2:
                self.pos.x = 0
                self.idle_direction = 1
                self.walk_velocity.x = self.walk_speed
            elif self.pos.x > WORLD_WIDTH // 2:
                self.pos.x = WORLD_WIDTH // 2
                self.idle_direction = -1
                self.walk_velocity.x = -self.walk_speed

            # move bobbing
            self.pos.y = GROUND_Y + math.sin(pg.time.get_ticks() / 500 + id(self)) * 2
        
        elif self.state == HumanoidState.CAPTURED:
            if player is None or getattr(player, "state", None) == Player.States.DEAD:
                return
            self.pos.y += self.speed
        
        elif self.state == HumanoidState.FALLING:
            self.pos.y += self.fall_speed
            self.fall_time += dt

            # if player catches falling humanoid
            if self.rect.collidelist([player.hitbox_top, player.hitbox_bottom]) >= 0:
                self.state = HumanoidState.RESCUED
                self.fall_time = 0.0

            if self.pos.y >= GROUND_Y:
                if self.fall_time > 1.0:
                    self.death(particles)
                    return
            
                self.pos.y = GROUND_Y
                self.state = HumanoidState.IDLE
        elif self.state == HumanoidState.RESCUED:
            # after being rescued, follow player's position
            print("rescuing humanoid!")
            if player is not None:
                self.pos.x = player.pos.x + (player.rect.width /2 )
                self.pos.y = player.pos.y + player.rect.height
            
            if player is None or getattr(player, "state", None) == Player.States.DEAD:
                self.death(particles)
                return
            
            if self.pos.y >= GROUND_Y:
                self.pos.y = GROUND_Y
                self.state = HumanoidState.IDLE
                player_group.score += 500
                player_group.coins += 3
                pop_ups.append(misc.text_pop_up("500", player.pos))

                
        if self.state == HumanoidState.KILLED:
            self.death(particles)
            return
    
    def death(self, particles: list[pg.sprite.Group]) -> None:
        self.kill()
        particles.append(misc.explosion_effect(self.pos, 20, 70, 120, 1.0, 2.0, 0, 360, DARK_GREY))
        del self
        
class HumanoidGroup(pg.sprite.Group):
    def __init__(self) -> None:
        super().__init__()

    def update(self, offset_x: float, dt: float, screen: pg.Surface, particles: list[pg.sprite.Group], player_group: PlayerGroup, pop_ups, player=None) -> None:
        for sprite in self:
            sprite.update(offset_x, dt, particles, player_group, pop_ups, player)
            sprite.draw(screen)