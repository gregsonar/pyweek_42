# src/levelcomplete.py
"""Межуровневый экран: уровень пройден, время добега и кнопка «Дальше»."""

import pygame as pg

from . import config
from .fonts import load_font
from .i18n import tr
from .scene import Scene
from .ui import Menu, MenuItem


class LevelCompleteScene(Scene):
    """Сообщение о прохождении уровня + время + переход на следующий уровень."""

    wants_mouse_grab = False

    def __init__(self, app, level_number, time_seconds, next_index):
        super().__init__(app)
        self.level_number = level_number
        self.time_seconds = time_seconds
        self.next_index = next_index
        self.title_font = load_font(config.MENU_TITLE_SIZE)
        self.info_font = load_font(config.MENU_ITEM_SIZE)
        self.menu = Menu(
            [MenuItem(lambda: tr("level_complete_next", self.app.language), self._next)]
        )

    def _next(self):
        """Перейти на следующий уровень (с фейдом)."""
        from .main import GameplayScene

        self.app.fade_to(GameplayScene(self.app, self.next_index))

    def _time_str(self):
        secs = int(round(self.time_seconds))
        return "%d:%02d" % (secs // 60, secs % 60)

    def handle_events(self, events):
        for event in events:
            self.menu.handle_event(event)

    def draw(self, screen):
        screen.fill(config.MENU_BG_COLOR)
        w = screen.get_width()
        h = screen.get_height()

        title = tr("level_complete_title", self.app.language, n=self.level_number)
        surf = self.title_font.render(title, True, config.MENU_TITLE_COLOR)
        shadow = self.title_font.render(title, True, config.HUD_SHADOW_COLOR)
        trect = surf.get_rect(midtop=(w // 2, int(h * 0.24)))
        screen.blit(shadow, trect.move(3, 3))
        screen.blit(surf, trect)

        info = tr("level_complete_time", self.app.language, t=self._time_str())
        isurf = self.info_font.render(info, True, config.MENU_COLOR)
        irect = isurf.get_rect(midtop=(w // 2, trect.bottom + 24))
        screen.blit(isurf, irect)

        self.menu.draw(screen, w // 2, irect.bottom + 40)
