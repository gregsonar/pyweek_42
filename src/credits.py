# src/credits.py
"""Экран титров/атрибуций."""

import pygame as pg

from . import config
from .fonts import load_font
from .i18n import tr
from .scene import Scene
from .ui import Menu, MenuItem

# Строки титров. Проприетарные имена не локализуем. Дополнить реальными
# авторами графики/звука перед релизом (см. TODO по атрибуциям в notes.md).
CREDITS_LINES = [
    "ChronoKhryshch",
    "PyWeek 42 — Borrowed Time",
    "",
    "Engine: py_raycast_project (MIT)",
    "Font: HomeVideo (CC0)",
]


class CreditsScene(Scene):
    """Полноэкранные титры: заголовок, список строк, кнопка 'Назад'."""

    wants_mouse_grab = False

    def __init__(self, app):
        super().__init__(app)
        self.title_font = load_font(config.MENU_TITLE_SIZE)
        self.line_font = load_font(config.MENU_ITEM_SIZE)
        self.menu = Menu(
            [MenuItem(lambda: tr("credits_back", self.app.language), self._back)]
        )

    def _back(self):
        self.app.pop_scene()

    def handle_events(self, events):
        for event in events:
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                self._back()
            else:
                self.menu.handle_event(event)

    def draw(self, screen):
        screen.fill(config.MENU_BG_COLOR)
        w = screen.get_width()
        h = screen.get_height()
        text = tr("credits_title", self.app.language)
        title = self.title_font.render(text, True, config.MENU_TITLE_COLOR)
        shadow = self.title_font.render(text, True, config.HUD_SHADOW_COLOR)
        trect = title.get_rect(midtop=(w // 2, int(h * 0.12)))
        screen.blit(shadow, trect.move(3, 3))
        screen.blit(title, trect)

        y = trect.bottom + 40
        line_h = self.line_font.get_height() + 8
        for line in CREDITS_LINES:
            if line:
                surf = self.line_font.render(line, True, config.MENU_COLOR)
                screen.blit(surf, surf.get_rect(midtop=(w // 2, y)))
            y += line_h

        self.menu.draw(screen, w // 2, y + 30)
