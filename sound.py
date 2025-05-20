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
    sound.set_volume(0.3)


if __name__ == "__main__":
    pg.mixer.quit()