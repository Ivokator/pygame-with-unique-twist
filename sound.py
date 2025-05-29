"""
Sound channels:

0: Player fire
1-5: Enemy explosion
6: big_shot



"""

import os
import pygame as pg

# ---------------------------- SOUND CONSTANTS ----------------------------
pg.mixer.init()

# TODO: replace these sounds with BETTER ONES!!!!!
PLAYER_FIRE1 = pg.mixer.Sound(os.path.join("sound_fx", "player", "fire1.wav"))
PLAYER_FIRE2 = pg.mixer.Sound(os.path.join("sound_fx", "player", "fire2.wav"))
PLAYER_FIRE3 = pg.mixer.Sound(os.path.join("sound_fx", "player", "fire3.wav"))
PLAYER_FIRE4 = pg.mixer.Sound(os.path.join("sound_fx", "player", "fire4.wav"))

for sound in [PLAYER_FIRE1, PLAYER_FIRE2, PLAYER_FIRE3, PLAYER_FIRE4]:
    sound.set_volume(0.12)

# thruster. music to my ears!
pg.mixer.music.load(os.path.join("sound_fx", "player", "thruster.mp3"))
pg.mixer.music.set_volume(0.22)


ENEMY_EXPLOSION1 = pg.mixer.Sound(os.path.join("sound_fx", "enemy", "explosion1.wav"))
ENEMY_EXPLOSION2 = pg.mixer.Sound(os.path.join("sound_fx", "enemy", "explosion2.wav"))
ENEMY_EXPLOSION3 = pg.mixer.Sound(os.path.join("sound_fx", "enemy", "explosion3.wav"))
ENEMY_EXPLOSION4 = pg.mixer.Sound(os.path.join("sound_fx", "enemy", "explosion4.wav"))
ENEMY_EXPLOSION5 = pg.mixer.Sound(os.path.join("sound_fx", "enemy", "explosion5.wav"))

for sound in [ENEMY_EXPLOSION1, ENEMY_EXPLOSION2, ENEMY_EXPLOSION3, ENEMY_EXPLOSION4, ENEMY_EXPLOSION5]:
    sound.set_volume(0.38)




# ITEM SPECIFIC
CHARGE_FIRE_SOUND = pg.mixer.Sound(os.path.join("sound_fx", "item_specific", "big_shot", "charge-fire.wav"))
CHARGE_FIRE_SOUND.set_volume(0.13)

CHARGED_SOUND = pg.mixer.Sound(os.path.join("sound_fx", "item_specific", "big_shot", "charged.wav"))
CHARGED_SOUND.set_volume(0.18)


if __name__ == "__main__":
    pg.mixer.quit()