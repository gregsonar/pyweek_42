# src/menu.py
"""Главное меню игры."""

from . import config
from .confirm import ConfirmScene
from .credits import CreditsScene
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
                    # активна только при наличии сохранённого прогресса
                    enabled_fn=lambda: self.app.save.has_progress(),
                ),
                MenuItem(
                    lambda: tr("menu_new_game", self.app.language), self._new_game
                ),
                MenuItem(self._language_label, self._toggle_language),
                MenuItem(
                    lambda: tr("menu_credits", self.app.language), self._credits
                ),
                MenuItem(
                    lambda: tr("menu_quit", self.app.language), self.app.quit
                ),
            ]
        )

    def _credits(self):
        self.app.push_scene(CreditsScene(self.app))

    def _language_label(self):
        name = tr("lang_%s" % self.app.language, self.app.language)
        return "%s: %s" % (tr("menu_language", self.app.language), name)

    def _toggle_language(self):
        self.app.set_language("ru" if self.app.language == "en" else "en")

    def _new_game(self):
        """Новая игра. При наличии прогресса - подтверждение (затрёт прогресс)."""
        if self.app.save.has_progress():
            self.app.push_scene(
                ConfirmScene(self.app, "confirm_new_game", self._start_fresh)
            )
        else:
            self._start_fresh()

    def _start_fresh(self):
        """Начать с первого уровня, записав прогресс."""
        self.app.save.set_progress(1)
        self.app.persist()
        self.app.fade_to(GameplayScene(self.app, 0))

    def _continue(self):
        """Продолжить с сохранённого уровня (прогресс - номер уровня, с 1)."""
        index = (self.app.save.progress_level or 1) - 1
        index = max(0, min(index, len(config.LEVELS) - 1))
        self.app.fade_to(GameplayScene(self.app, index))

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
