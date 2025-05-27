import os

import pygame as pg
import pygame_menu as pm

pg.init()

# ------------------------ GAME CONSTANTS ------------------------
WINDOW_TITLE: str = "some game"
FRAMES_PER_SECOND: int = 100
RESOLUTION: tuple[int, int] = (1280, 960)

PLAYER_WIDTH: int = 100
PLAYER_HEIGHT: int = 34

SCREEN_WIDTH: int = RESOLUTION[0]
SCREEN_HEIGHT: int = RESOLUTION[1]

WORLD_WIDTH: int= SCREEN_WIDTH * 5

# -----------------------------------------------------------------

# Basic colours
WHITE: tuple[int, ...] = (255, 255, 255)
BLACK: tuple[int, ...] = (0, 0, 0)
BLUE: tuple[int, ...] = (0, 0, 255)
GREEN: tuple[int, ...] = (0, 255, 0)
RED: tuple[int, ...] = (255, 0, 0)

DARK_GREY: tuple[int, ...] = (64, 64, 64)
DARKER_GREY: tuple[int, ...] = (32, 32, 32)


# SCORE TEXT
SYSFONT = pg.font.get_default_font()
DEFAULT_FONT = pg.font.SysFont(SYSFONT, 24)
PRESS_START_FONT = pg.font.Font(os.path.join("fonts", "PressStart2P-Regular.ttf"), 28)

# Pygame Menu Themes
mytheme = pm.themes.Theme(title_bar_style=pm.widgets.MENUBAR_STYLE_NONE,
                          title_font_color = DARK_GREY,
                          title_font = PRESS_START_FONT,
                          title_font_size = 50,
                          title = True,
                          title_offset=(25,25),

                          selection_color = DARKER_GREY,
                          background_color = (160,160,160,255),
                          fps = FRAMES_PER_SECOND,
                          widget_font = PRESS_START_FONT,
                          widget_font_size = RESOLUTION[0] // 30,
                          )

# ---------------------------- MISC CONSTANTS ----------------------------
# do not change unless you know what you're doing!!

TOP_WIDGET_HEIGHT = SCREEN_HEIGHT // 6
TOP_WIDGET_LINE_THICKNESS: int = 20
GAMEPLAY_HEIGHT = SCREEN_HEIGHT - TOP_WIDGET_HEIGHT

EDGE_SPAWN_BUFFER: int = SCREEN_WIDTH // 2
GROUND_Y: int = GAMEPLAY_HEIGHT * 7 // 8