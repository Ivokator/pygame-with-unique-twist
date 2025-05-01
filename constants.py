import pygame as pg
import pygame_menu as pm

pg.init()

# ------------------------ GAME CONSTANTS ------------------------
WINDOW_TITLE: str = "some game"
FRAMES_PER_SECOND: int = 100
RESOLUTION: tuple[int, int] = (800, 600)

PLAYER_SIZE: int = 50

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

# Pygame Menu Themes
mytheme = pm.themes.Theme(title_bar_style=pm.widgets.MENUBAR_STYLE_UNDERLINE_TITLE,
                          title_font_color = DARK_GREY,
                          selection_color = BLACK,
                          fps = FRAMES_PER_SECOND,
                          widget_font = pm.font.FONT_MUNRO,
                          title_font = pm.font.FONT_8BIT,
                          widget_font_size = 40
                    
                          )