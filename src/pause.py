# src/pause.py
"""Экран паузы (оверлей поверх игры)."""

import pygame as pg

from . import config
from .fonts import load_font
from .i18n import tr
from .scene import Scene
from .ui import Menu, MenuItem


class PauseScene(Scene):
    """Пауза: затемняет игру и предлагает продолжить / в меню / выйти.

    render_below=True - под паузой отрисовывается замороженный кадр игры (App
    обновляет только верхнюю сцену, поэтому мир и таймер стоят).
    """

    render_below = True
    wants_mouse_grab = False

    def __init__(self, app):
        super().__init__(app)
        self.title_font = load_font(config.PAUSE_TITLE_SIZE)
        self._overlay = pg.Surface((config.WIN_WIDTH, config.WIN_HEIGHT))
        self._overlay.fill(config.PAUSE_DIM_COLOR)
        self._overlay.set_alpha(config.PAUSE_DIM_ALPHA)
        self.menu = Menu(
            [
                MenuItem(
                    lambda: tr("pause_resume", self.app.language), self._resume
                ),
                MenuItem(
                    lambda: tr("pause_main_menu", self.app.language), self._to_menu
                ),
                MenuItem(
                    lambda: tr("pause_quit", self.app.language), self.app.quit
                ),
            ]
        )

    def _resume(self):
        """Снять паузу - вернуться в игру."""
        self.app.pop_scene()

    def _to_menu(self):
        """Выйти в главное меню (снять паузу и заменить игру меню)."""
        from .menu import MainMenuScene

        self.app.pop_scene()  # снять паузу
        self.app.replace_scene(MainMenuScene(self.app))  # игра -> меню

    def handle_events(self, events):
        for event in events:
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                self._resume()
            else:
                self.menu.handle_event(event)

    def draw(self, screen):
        screen.blit(self._overlay, (0, 0))
        w = screen.get_width()
        h = screen.get_height()
        text = tr("pause_title", self.app.language)
        title = self.title_font.render(text, True, config.MENU_TITLE_COLOR)
        shadow = self.title_font.render(text, True, config.HUD_SHADOW_COLOR)
        trect = title.get_rect(midtop=(w // 2, int(h * 0.22)))
        screen.blit(shadow, trect.move(3, 3))
        screen.blit(title, trect)
        self.menu.draw(screen, w // 2, trect.bottom + 50)
