import pygame as pg

from . import config

def load_font(size):
    try:
        return pg.font.Font(config.FONT_PATH, size)
    except (FileNotFoundError, OSError, pg.error):
        return pg.font.SysFont(config.HUD_FONT_FALLBACK, size)
