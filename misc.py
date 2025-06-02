import math
import random
import typing

import pygame as pg
import pygame_widgets as pw # type: ignore

from pygame.math import Vector2
from pygame_widgets.button import Button # type: ignore

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



class text_pop_up(pg.sprite.Sprite):
    def __init__(self, text: str, pos: Vector2, colour: tuple[int, int, int] = (255,255,255), lifetime: float = 1.0, rise_speed: float = 40.0) -> None:
        super().__init__()
        self.text = text
        self.pos = pos.copy()
        self.colour = colour
        self.lifetime = lifetime
        self.remaining_time = lifetime
        self.rise_speed = rise_speed

        self.image = PRESS_START_FONT.render(self.text, True, self.colour)
        self.rect = self.image.get_rect(center=(self.pos.x, self.pos.y))

    def update(self, dt: float) -> None:
        self.remaining_time -= dt
        
        # text rises up the screen
        self.pos.y -= self.rise_speed * dt
        self.rect.center = int(self.pos.x), int(self.pos.y)

        # fade out over time
        alpha = int(255 * (self.remaining_time / self.lifetime))
        self.image.set_alpha(alpha)

    def draw(self, screen: pg.Surface, offset_x: float = 0):
        draw_x = self.pos.x + offset_x
        screen.blit(self.image, (draw_x - self.rect.width // 2, self.pos.y - self.rect.height // 2))


def keybind_menu(screen: pg.Surface, font: pg.font.Font, keybinds: dict[str, int]) -> None:
    """
    Keybind menu.
    
    Arguments:
        screen (pg.Surface): your main display surface
        font (pg.font.Font): a pygame.font.Font instance for drawing text
        keybinds (dict[str, int]): a dict mapping action names (str) → pygame key constants
    """
    # yes i tried using pygame_menu, it seems near impossible for this task so i have to do it manually
    # no im not putting the keybinds in JSON yet...
    # ok i'll comment step by step so future me does not get confused




    # First value in tuple are the strings visible to player
    # Second value is internal strings used to represent the keys
    actions = [
        ("Move Left",    "move_left"),
        ("Move Right",   "move_right"),
        ("Move Up",      "move_up"),
        ("Move Down",    "move_down"),
        ("Shoot",        "shoot"),
        ("Smart Bomb",   "smart_bomb"),
        ("Use Item 1",   "use_item_1"),
        ("Use Item 2",   "use_item_2"),
        ("Use Item 3",   "use_item_3"),
        ("Use Item 4",   "use_item_4"),
    ]

    rebinding_key: str | None = None # if str, then it represents the key to rebind
    running: bool = True

    def on_back() -> None:
        """Back button to exit `keybind_menu`."""
        nonlocal running, rebinding_key

        # make sure player isn't in the middle of rebinding a key when back is pressed
        if rebinding_key is not None: 
            rebinding_key = None
            for (label, act_key), action_button in action_buttons.items():
                action_button.setText(f"{label}: {pg.key.name(keybinds[act_key]).upper()}") # simply reset text if that happens
        else:
            running = False

    back_button: Button = Button(
        screen,
        100, 90, 130, 50,
        text="Back",
        font=font,
        radius=5,
        textColour=WHITE,
        inactiveColour=(80, 80, 80),
        hoverColour=(100, 100, 100),
        pressedColour=(60, 60, 60),
        onClick=on_back
    )

    # one action button per keybind
    action_buttons: dict[tuple[str, str], Button] = {}

    # we define `label` as the user-friendly label name of the keys,
    # `act_key`` is the actual stored key used by the code

    for i, (label, act_key) in enumerate(actions): # for every action (with index)
        row_y = 150 + i *  55
        current_keyname: str = pg.key.name(keybinds[act_key]).upper() # user-friendly name

        # create a button for the keybind, with action and currently binded key
        action_button: Button = Button(
            screen,
            100, row_y, 400,  50, # there's a bug where clicking "Keybinds" in main menu would automatically click the action button behind it
                                  # so we just leave this at the side to prevent that :P
            text=f"{label}: {current_keyname}",
            font=font,
            textColour=WHITE,
            radius=5,
            inactiveColour=(50, 50, 50),
            hoverColour=(70, 70, 70),
            pressedColour=(90, 90, 90),
            # callback via closure to capture this action’s key
            onClick=(lambda a=act_key, l=label: start_rebind(a, l))
        )

        action_buttons[(label, act_key)] = action_button # add button to dictionary of action buttons

    def start_rebind(action_key: str, display_label: str) -> None:
        """
        Initiates the key rebinding process for a given action.

        Sets the `rebinding_key` variable to the specified action key.
        Updates the corresponding action button's text to prompt the user to press a new key.

        Args:
            action_key (str): The identifier for the action whose key binding is to be changed.
            display_label (str): The user-friendly label for the action to display during rebinding.
            
        """
        nonlocal rebinding_key
        rebinding_key = action_key

        for (label, act_k), action_button in action_buttons.items():
            if act_k == action_key:
                action_button.setText(f"{display_label}: PRESS KEY…")
                break

    clock: pg.time.Clock = pg.time.Clock()
    title_surface: pg.Surface = font.render("KEYBINDS", True, pg.Color('white'))


    # keybind menu loop
    while running:
        dt: float = clock.tick(FRAMES_PER_SECOND) / 1000.0

        events = pg.event.get()
        for event in events:
            if event.type == pg.QUIT:
                pg.quit()
                return

            # listen for next key
            if event.type == pg.KEYDOWN:
                # ESC to quit
                if event.key == pg.K_ESCAPE and rebinding_key is None:
                    running = False
                
                # REBIND!
                elif rebinding_key is not None and event.key != pg.K_ESCAPE:
                    keybinds[rebinding_key] = event.key # assign pressed key

                    
                    for (label, act_key), action_button in action_buttons.items():
                        if act_key == rebinding_key:
                            new_name = pg.key.name(event.key).upper() # make everything uppercase because yes
                            action_button.setText(f"{label}: {new_name}") # change button label
                            break
                    rebinding_key = None

        screen.fill((0, 0, 0))

        computer_back: pg.Rect = pg.Rect(SCREEN_WIDTH // 20, SCREEN_HEIGHT // 20, SCREEN_WIDTH * 0.9, SCREEN_HEIGHT * 0.9)
        pg.draw.rect(screen, (20, 20, 20), computer_back, width=10, border_radius=20)

        screen.blit(title_surface, ((screen.get_width() - title_surface.get_width()) // 2, 80))

        # draw all buttons
        for action_button in action_buttons.values():
            action_button.listen(events)
        back_button.listen(events)

        # important!
        pw.update(events)

        pg.display.flip()


















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