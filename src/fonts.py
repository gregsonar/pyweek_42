# src/fonts.py
"""Загрузка игрового шрифта (HomeVideo) с фолбэком на системный.

Единый шрифт для HUD и экранов меню. Покрывает цифры, латиницу, кириллицу и
символы ♥/♡, поэтому отдельный символьный шрифт не нужен.
"""

import pygame as pg

from . import config


def load_font(size):
    """Игровой шрифт нужного кегля. При сбое загрузки файла - системный фолбэк."""
    try:
        return pg.font.Font(config.FONT_PATH, size)
    except (FileNotFoundError, OSError, pg.error):
        return pg.font.SysFont(config.HUD_FONT_FALLBACK, size)
