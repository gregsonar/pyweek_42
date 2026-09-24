# src/ui.py
"""Простое меню: вертикальный список пунктов с навигацией клавиатурой и мышью."""

import pygame as pg

from . import audio
from . import config
from .fonts import load_font


class MenuItem:
    """Пункт меню: подпись (функция -> строка), действие и признак активности.

    Подпись - функция, чтобы текст пересобирался каждый кадр (например, при смене
    языка). enabled_fn - функция, чтобы активность зависела от состояния игры.
    """

    def __init__(self, text_fn, action, enabled_fn=None):
        self.text_fn = text_fn
        self.action = action
        self.enabled_fn = enabled_fn or (lambda: True)
        self.rect = None  # прямоугольник последней отрисовки (для мыши)

    @property
    def enabled(self):
        return bool(self.enabled_fn())


class Menu:
    """Вертикальное меню. Стрелки/WASD + Enter/Space, наведение и клик мышью."""

    def __init__(self, items, item_size=None, spacing=None):
        self.items = items
        self.font = load_font(item_size or config.MENU_ITEM_SIZE)
        self.spacing = spacing if spacing is not None else config.MENU_ITEM_SPACING
        self.selected = self._first_enabled()

    def _first_enabled(self):
        for i, item in enumerate(self.items):
            if item.enabled:
                return i
        return 0

    def move(self, delta):
        """Сдвинуть выбор на активный пункт в направлении delta (+1/-1)."""
        n = len(self.items)
        if n == 0:
            return
        old = self.selected
        i = self.selected
        for _ in range(n):
            i = (i + delta) % n
            if self.items[i].enabled:
                self.selected = i
                if i != old:
                    audio.play("ui_move")
                return

    def activate(self):
        """Выполнить действие выбранного пункта (если он активен)."""
        if 0 <= self.selected < len(self.items):
            item = self.items[self.selected]
            if item.enabled:
                audio.play("ui_select")
                item.action()

    def handle_event(self, event):
        """Навигация: клавиатура (стрелки/WASD/Enter) и мышь (наведение/клик)."""
        if event.type == pg.KEYDOWN:
            if event.key in (pg.K_UP, pg.K_w):
                self.move(-1)
            elif event.key in (pg.K_DOWN, pg.K_s):
                self.move(1)
            elif event.key in (pg.K_RETURN, pg.K_KP_ENTER, pg.K_SPACE):
                self.activate()
        elif event.type == pg.MOUSEMOTION:
            self._hover(event.pos)
        elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self._hover(event.pos):
                self.activate()

    def _hover(self, pos):
        """Навести выбор на пункт под курсором. -> True, если попали в активный."""
        for idx, item in enumerate(self.items):
            if item.rect and item.rect.collidepoint(pos) and item.enabled:
                if idx != self.selected:
                    audio.play("ui_move")
                self.selected = idx
                return True
        return False

    def draw(self, screen, center_x, top_y):
        """Отрисовать пункты по центру от center_x, начиная с top_y. -> нижний y."""
        y = top_y
        line_h = self.font.get_height() + self.spacing
        for idx, item in enumerate(self.items):
            if not item.enabled:
                color = config.MENU_COLOR_DISABLED
            elif idx == self.selected:
                color = config.MENU_COLOR_SELECTED
            else:
                color = config.MENU_COLOR
            text = item.text_fn()
            label = self.font.render(text, True, color)
            shadow = self.font.render(text, True, config.HUD_SHADOW_COLOR)
            rect = label.get_rect(midtop=(center_x, y))
            screen.blit(shadow, rect.move(2, 2))
            screen.blit(label, rect)
            item.rect = rect
            y += line_h
        return y
