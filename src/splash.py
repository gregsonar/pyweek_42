# src/splash.py
"""Сплеш-заставка при запуске: лого/заголовок с фейдами, затем главное меню."""

import pygame as pg

from . import config
from .fonts import load_font
from .i18n import tr
from .menu import MainMenuScene
from .scene import Scene


class SplashScene(Scene):
    """Заставка: появление -> показ -> угасание -> меню. Скип любой клавишей/кликом."""

    wants_mouse_grab = False

    def __init__(self, app):
        super().__init__(app)
        self._t = 0.0
        self._done = False
        self._logo = self._load_logo()
        self.title_font = None if self._logo else load_font(config.SPLASH_TITLE_SIZE)
        self._total = (
            config.SPLASH_FADE_IN + config.SPLASH_HOLD + config.SPLASH_FADE_OUT
        )

    def _load_logo(self):
        """Загрузить лого, если файл есть; иначе None (покажем текст-заглушку)."""
        try:
            return pg.image.load(config.SPLASH_LOGO_PATH).convert_alpha()
        except (pg.error, FileNotFoundError, OSError):
            return None

    def _alpha(self):
        """Прозрачность 0..1 по фазе фейдов."""
        fi, hold, fo = (
            config.SPLASH_FADE_IN,
            config.SPLASH_HOLD,
            config.SPLASH_FADE_OUT,
        )
        t = self._t
        if t < fi:
            return t / fi
        if t < fi + hold:
            return 1.0
        if t < fi + hold + fo:
            return 1.0 - (t - fi - hold) / fo
        return 0.0

    def _to_menu(self):
        if self._done:
            return
        self._done = True
        self.app.replace_scene(MainMenuScene(self.app))

    def handle_events(self, events):
        for event in events:
            if event.type == pg.KEYDOWN or event.type == pg.MOUSEBUTTONDOWN:
                self._to_menu()
                return

    def update(self, dt):
        self._t += dt
        if self._t >= self._total:
            self._to_menu()

    def draw(self, screen):
        screen.fill(config.MENU_BG_COLOR)
        alpha = int(max(0.0, min(1.0, self._alpha())) * 255)
        w = screen.get_width()
        h = screen.get_height()
        if self._logo is not None:
            img = self._logo.copy()
            img.set_alpha(alpha)
            screen.blit(img, img.get_rect(center=(w // 2, h // 2)))
        else:
            text = tr("game_title", self.app.language)
            surf = self.title_font.render(text, True, config.MENU_TITLE_COLOR)
            surf.set_alpha(alpha)
            screen.blit(surf, surf.get_rect(center=(w // 2, h // 2)))
