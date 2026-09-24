# src/menu.py
"""Главное меню игры."""

from . import config
from .fonts import load_font
from .i18n import tr
from .main import GameplayScene
from .scene import Scene
from .ui import Menu, MenuItem


class MainMenuScene(Scene):
    """Заголовок, пункты меню и выбор языка. Курсор виден (мышь не захвачена)."""

    wants_mouse_grab = False

    def __init__(self, app):
        super().__init__(app)
        self.title_font = load_font(config.MENU_TITLE_SIZE)
        self.menu = Menu(
            [
                MenuItem(
                    lambda: tr("menu_continue", self.app.language),
                    self._continue,
                    # неактивна до системы сохранения (шаг 5 плана)
                    enabled_fn=lambda: False,
                ),
                MenuItem(
                    lambda: tr("menu_new_game", self.app.language), self._new_game
                ),
                MenuItem(self._language_label, self._toggle_language),
                MenuItem(
                    lambda: tr("menu_quit", self.app.language), self.app.quit
                ),
            ]
        )

    def _language_label(self):
        name = tr("lang_%s" % self.app.language, self.app.language)
        return "%s: %s" % (tr("menu_language", self.app.language), name)

    def _toggle_language(self):
        self.app.language = "ru" if self.app.language == "en" else "en"

    def _new_game(self):
        self.app.replace_scene(GameplayScene(self.app))

    def _continue(self):
        pass  # шаг 5: загрузка прогресса

    def handle_events(self, events):
        for event in events:
            self.menu.handle_event(event)

    def draw(self, screen):
        screen.fill(config.MENU_BG_COLOR)
        w = screen.get_width()
        h = screen.get_height()
        text = tr("game_title", self.app.language)
        title = self.title_font.render(text, True, config.MENU_TITLE_COLOR)
        shadow = self.title_font.render(text, True, config.HUD_SHADOW_COLOR)
        trect = title.get_rect(midtop=(w // 2, int(h * 0.18)))
        screen.blit(shadow, trect.move(3, 3))
        screen.blit(title, trect)
        self.menu.draw(screen, w // 2, trect.bottom + 60)
