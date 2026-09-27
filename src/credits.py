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
    "---",
    "PyWeek 42 — Borrowed Time",
    "pyweek.org",
    "",
    "A game from the KnottyKaa team",
    "Engine core (and words of wisdom): @rikovmike",
    "https://github.com/rikovmike",
    "",
    "Graphics and design: @JunaGala",
    "https://github.com/JunaGala/",
    "",
    "Programming and bugs: Dudnikov",
    "https://github.com/gregsonar/",
    "",
    "Engine: py_raycast_project (MIT)",
    "Font: HomeVideo (CC0)",
    "Sounds: freesound.org, ccmixter.org, sfbgames.itch.io (see assets/CREDITS.txt)",
    "",
    "Made with love!",
]


class CreditsScene(Scene):
    """Полноэкранные титры: заголовок, список строк, кнопка 'Назад'."""

    wants_mouse_grab = False

    def __init__(self, app):
        super().__init__(app)
        self.title_font = load_font(config.MENU_TITLE_SIZE)
        self.line_font = load_font(config.CREDITS_LINE_SIZE)
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
        trect = title.get_rect(midtop=(w // 2, int(h * 0.08)))
        screen.blit(shadow, trect.move(3, 3))
        screen.blit(title, trect)

        # Полоса под строки: от заголовка до места кнопки "Назад" внизу. Шаг
        # (unit) подгоняется под доступную высоту, поэтому список любой длины
        # уместится. Пустые строки - разделители в половину шага.
        max_w = w - 2 * config.HUD_MARGIN
        content_top = trect.bottom + 20
        back_reserve = self.line_font.get_height() + 48  # место под кнопку снизу
        avail = max(1, (h - back_reserve) - content_top)
        weight = sum(1.0 if line else 0.45 for line in CREDITS_LINES)
        unit = avail / weight if weight else avail

        y = content_top
        for line in CREDITS_LINES:
            if line:
                surf = self.line_font.render(line, True, config.MENU_COLOR)
                sw, sh = surf.get_size()
                # ужать строку, если шире полосы или выше ячейки (устойчиво к росту)
                scale = min(1.0, max_w / sw, (unit * 0.9) / sh)
                if scale < 1.0:
                    surf = pg.transform.smoothscale(
                        surf, (max(1, int(sw * scale)), max(1, int(sh * scale)))
                    )
                screen.blit(surf, surf.get_rect(center=(w // 2, int(y + unit / 2))))
                y += unit
            else:
                y += unit * 0.45

        self.menu.draw(screen, w // 2, int(y) + 16)
