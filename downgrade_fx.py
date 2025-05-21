"""
credits to chris-greening:
https://dev.to/chrisgreening/simulating-simple-crt-and-glitch-effects-in-pygame-1mf1
"""

import random
import pygame as pg
from constants import *

pg.init()

def apply_downgrade_effect(screen: pg.Surface, pixelation: int):
    _scanlines(screen)
    _pixelation(screen, pixelation)
    _flicker(screen)

def _scanlines(screen):
        scanline_surface = pg.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pg.SRCALPHA)

        for y in range(0, SCREEN_HEIGHT, 3):
            pg.draw.line(scanline_surface, (0, 0, 0, 60), (0, y), (SCREEN_WIDTH, y))

        screen.blit(scanline_surface, (0, 0))

def _pixelation(screen: pg.Surface, pixelation: int) -> None:
    small_surf = pg.transform.scale(screen, (SCREEN_WIDTH // pixelation, SCREEN_HEIGHT // pixelation))
    screen.blit(pg.transform.scale(small_surf, (SCREEN_WIDTH, SCREEN_HEIGHT)), (0, 0))

def _flicker(screen: pg.Surface):
    if random.randint(0, 25) == 0:
        flicker_surface = pg.Surface(screen.get_size(), pg.SRCALPHA)
        flicker_surface.fill((255, 255, 255, 2))
        screen.blit(flicker_surface, (0, 0))