import os

import pygame as pg
import pygame_menu as pm

pg.init()

# ------------------------ GAME CONSTANTS ------------------------
WINDOW_TITLE: str = "some game"
FRAMES_PER_SECOND: int = 100
RESOLUTION: tuple[int, int] = (1280, 960)

PLAYER_SIZE: int = 30

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
PRESS_START_FONT = pg.font.Font(os.path.join("fonts", "PressStart2P-Regular.ttf"), 24)

# Pygame Menu Themes
mytheme = pm.themes.Theme(title_bar_style=pm.widgets.MENUBAR_STYLE_UNDERLINE_TITLE,
                          title_font_color = DARK_GREY,
                          selection_color = BLACK,
                          fps = FRAMES_PER_SECOND,
                          widget_font = PRESS_START_FONT,
                          title_font = PRESS_START_FONT,
                          widget_font_size = RESOLUTION[0] // 10,
                          )




# ---------------------------- MISC CONSTANTS ----------------------------
# do not change unless you know what you're doing!!


TOP_WIDGET_LINE_THICKNESS: int = 20
