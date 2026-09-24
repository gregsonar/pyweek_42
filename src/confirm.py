# src/confirm.py
"""Универсальный диалог подтверждения (да/нет) как оверлей."""

import pygame as pg

from . import config
from .fonts import load_font
from .i18n import tr
from .scene import Scene
from .ui import Menu, MenuItem


class ConfirmScene(Scene):
    """Оверлей с вопросом и выбором Нет/Да. По умолчанию выбран Нет (безопасно).

    on_yes вызывается после снятия диалога, если игрок подтвердил.
    """

    render_below = True
    wants_mouse_grab = False

    def __init__(self, app, question_key, on_yes):
        super().__init__(app)
        self._question_key = question_key
        self._on_yes = on_yes
        self.font = load_font(config.MENU_ITEM_SIZE)
        self._overlay = pg.Surface((config.WIN_WIDTH, config.WIN_HEIGHT))
        self._overlay.fill(config.PAUSE_DIM_COLOR)
        self._overlay.set_alpha(config.PAUSE_DIM_ALPHA)
        self.menu = Menu(
            [
                MenuItem(lambda: tr("confirm_no", self.app.language), self._no),
                MenuItem(lambda: tr("confirm_yes", self.app.language), self._yes),
            ]
        )

    def _no(self):
        self.app.pop_scene()

    def _yes(self):
        self.app.pop_scene()  # снять диалог
        self._on_yes()

    def handle_events(self, events):
        for event in events:
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                self._no()
            else:
                self.menu.handle_event(event)

    def draw(self, screen):
        screen.blit(self._overlay, (0, 0))
        w = screen.get_width()
        h = screen.get_height()
        text = tr(self._question_key, self.app.language)
        q = self.font.render(text, True, config.MENU_COLOR)
        shadow = self.font.render(text, True, config.HUD_SHADOW_COLOR)
        qrect = q.get_rect(midtop=(w // 2, int(h * 0.32)))
        screen.blit(shadow, qrect.move(2, 2))
        screen.blit(q, qrect)
        self.menu.draw(screen, w // 2, qrect.bottom + 40)
