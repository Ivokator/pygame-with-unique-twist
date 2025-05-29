import pygame as pg
import pygame_widgets as pw  # type: ignore

from pygame_widgets.button import ButtonArray # type: ignore

from classes import Player
from constants import *

pg.init()

def roguelite_background(surface: pg.Surface) -> None:
    """Roguelite map background
    
    this is supposed to resemble a futuristic ship on-board screen
    """
    surface.fill((40,40,40))

    computer_back: pg.Rect = pg.Rect(SCREEN_WIDTH // 20, SCREEN_HEIGHT // 20, SCREEN_WIDTH * 0.9, SCREEN_HEIGHT * 0.9)
    pg.draw.rect(surface, (20, 20, 20), computer_back, border_radius=30)

    computer_screen: pg.Rect = pg.Rect(0, 0, SCREEN_WIDTH * 0.8, SCREEN_HEIGHT * 0.75)
    computer_screen.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    pg.draw.rect(surface, (5, 5, 5), computer_screen, border_radius=5)

def three_choice_buttons(surface: pg.Surface) -> ButtonArray:
    return ButtonArray(
    # Mandatory Parameters
    surface,  # Surface to place button array on
    SCREEN_WIDTH // 2 - (SCREEN_WIDTH * 0.8 // 2),  # X-coordinate
    SCREEN_HEIGHT // 2,  # Y-coordinate
    SCREEN_WIDTH * 0.8,  # Width
    SCREEN_HEIGHT * 0.3,  # Height
    (3, 1),  # Shape: 2 buttons wide, 2 buttons tall
    border=100,  # Distance between buttons and edge of array
    fonts=[PRESS_START_FONT, PRESS_START_FONT, PRESS_START_FONT],
    fontSizes=[15, 15, 15],
    texts=('Pick', 'Pick', 'Pick'),  
    onClicks=(lambda: print('1'), lambda: print('2'), lambda: print('3'), lambda: print('4')),
    colour=(5, 5, 5),
)

if __name__ == "__main__":
    # test game loop

    screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pg.display.set_caption("The Roguelite Part")
    clock = pg.time.Clock()
    running = True

    _ = three_choice_buttons(screen)

    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False

        screen.fill(BLACK)

        roguelite_background(screen)

        events = pg.event.get()
        pw.update(events)

        pg.display.flip()
        clock.tick(FRAMES_PER_SECOND)