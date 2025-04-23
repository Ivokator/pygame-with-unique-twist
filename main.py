import asyncio
import pygame
import random
import threading
import time
import typing

from pygame.locals import Rect

# Initialize
pygame.init()

# ------------------------ GAME CONSTANTS ------------------------
WINDOW_TITLE: str = "some game"
FRAMES_PER_SECOND: int = 100
RESOLUTION: tuple[int, int] = (800, 600)

INPUT_KEYS: list[int] = [pygame.K_f, pygame.K_g, pygame.K_h, pygame.K_j]

# -----------------------------------------------------------------

# Basic colours
WHITE: tuple[int, ...] = (255, 255, 255)
BLACK: tuple[int, ...] = (0, 0, 0)
BLUE: tuple[int, ...] = (0, 0, 255)
GREEN: tuple[int, ...] = (0, 255, 0)
RED: tuple[int, ...] = (255, 0, 0)

DARK_GREY: tuple[int, ...] = (64, 64, 64)
DARKER_GREY: tuple[int, ...] = (32, 32, 32)

# Screen / Clock

screen: pygame.Surface = pygame.display.set_mode(RESOLUTION)
clock: pygame.time.Clock = pygame.time.Clock()

SCREEN_WIDTH: int
SCREEN_HEIGHT: int

SCREEN_WIDTH, SCREEN_HEIGHT = screen.get_size()

# SCORE TEXT
SYSFONT = pygame.font.get_default_font()
DEFAULT_FONT = pygame.font.SysFont(SYSFONT, 24)

def main() -> None:
    """Main menu for game."""
    dt: float = 0.0
    running: bool = True

    # Game preparation
    pygame.display.set_caption(WINDOW_TITLE)

    while running:
        screen.fill(BLACK)

        

        # Menu title
        title_text: pygame.Surface = DEFAULT_FONT.render("Main Menu", True, WHITE)
        title_rect: pygame.Rect = title_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4))


        # Menu options
        menu_options: list[str] = ["Play", "Settings", "Quit"]
        menu_texts: list[pygame.Surface] = []
        for option in menu_options: # Render every option
            text: pygame.Surface = DEFAULT_FONT.render(option, True, WHITE)
            menu_texts.append(text)
        menu_rects: list[pygame.Rect] = []

        for i, text in enumerate(menu_texts): # Rect options
            rect: pygame.Rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + i * 40))
            menu_rects.append(rect)

        # Input events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONUP:
                mouse_pos: tuple[int, int] = pygame.mouse.get_pos()
    
        # Draw screen
        screen.blit(title_text, title_rect)

        for i, text in enumerate(menu_texts):
            screen.blit(text, menu_rects[i])
        

        pygame.display.flip()
        dt = clock.tick(FRAMES_PER_SECOND) / 1000


    pygame.quit()



def play_game() -> None:
    dt: float = 0.0
    running: bool = True

    # Game preparation
    pygame.display.set_caption(WINDOW_TITLE)

    while running:
        screen.fill(BLACK)

        # Quit game
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Draw screen
        pygame.display.flip()
        dt = clock.tick(FRAMES_PER_SECOND) / 1000

    pygame.quit()




if __name__ == "__main__":
    main()