# src/victory.py
"""Экран завершения уровня/игры."""

import pygame as pg

from . import config
from .fonts import load_font
from .i18n import tr
from .scene import Scene
from .ui import Menu, MenuItem


class VictoryScene(Scene):
    """Поздравление с прохождением + переход в меню или к титрам."""

    wants_mouse_grab = False

    def __init__(self, app):
        super().__init__(app)
        self.title_font = load_font(config.MENU_TITLE_SIZE)
        self.menu = Menu(
            [
                MenuItem(
                    lambda: tr("victory_menu", self.app.language), self._to_menu
                ),
                MenuItem(
                    lambda: tr("victory_credits", self.app.language), self._credits
                ),
            ]
        )

    def _to_menu(self):
        from .menu import MainMenuScene

        self.app.fade_to(MainMenuScene(self.app))

    def _credits(self):
        from .credits import CreditsScene

        self.app.push_scene(CreditsScene(self.app))

    def handle_events(self, events):
        for event in events:
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                self._to_menu()
            else:
                self.menu.handle_event(event)

    def draw(self, screen):
        screen.fill(config.MENU_BG_COLOR)
        w = screen.get_width()
        h = screen.get_height()
        text = tr("victory_title", self.app.language)
        title = self.title_font.render(text, True, config.MENU_TITLE_COLOR)
        shadow = self.title_font.render(text, True, config.HUD_SHADOW_COLOR)
        trect = title.get_rect(midtop=(w // 2, int(h * 0.22)))
        screen.blit(shadow, trect.move(3, 3))
        screen.blit(title, trect)
        self.menu.draw(screen, w // 2, trect.bottom + 60)
