from . import config
from .confirm import ConfirmScene
from .credits import CreditsScene
from .fonts import load_font
from .i18n import has, tr
from .main import GameplayScene
from .scene import Scene
from .ui import Menu, MenuItem, audio_toggle_items

_HOWTO_KEYS = ("menu_howto_1", "menu_howto_2", "menu_howto_3")

class MainMenuScene(Scene):

    wants_mouse_grab = False

    def __init__(self, app):
        super().__init__(app)
        self.title_font = load_font(config.MENU_TITLE_SIZE)
        self.help_font = load_font(config.MENU_HELP_SIZE)
        self.menu = Menu(
            [
                MenuItem(
                    lambda: tr("menu_continue", self.app.language),
                    self._continue,

                    enabled_fn=lambda: self.app.save.has_progress(),
                ),
                MenuItem(
                    lambda: tr("menu_new_game", self.app.language), self._new_game
                ),
                MenuItem(self._language_label, self._toggle_language),
                *audio_toggle_items(self.app),
                MenuItem(
                    lambda: tr("menu_credits", self.app.language), self._credits
                ),
                MenuItem(
                    lambda: tr("menu_quit", self.app.language), self.app.quit
                ),
            ],

            spacing=config.MENU_ITEM_SPACING_COMPACT,
        )

    def _credits(self):
        self.app.push_scene(CreditsScene(self.app))

    def _language_label(self):
        name = tr("lang_%s" % self.app.language, self.app.language)
        return "%s: %s" % (tr("menu_language", self.app.language), name)

    def _toggle_language(self):
        self.app.set_language("ru" if self.app.language == "en" else "en")

    def _new_game(self):
        if self.app.save.has_progress():
            self.app.push_scene(
                ConfirmScene(self.app, "confirm_new_game", self._start_fresh)
            )
        else:
            self._start_fresh()

    def _start_fresh(self):
        self.app.save.set_progress(1)
        self.app.persist()
        self.app.fade_to(GameplayScene(self.app, 0))

    def _continue(self):
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
        trect = title.get_rect(midtop=(w // 2, int(h * 0.13)))
        screen.blit(shadow, trect.move(3, 3))
        screen.blit(title, trect)
        self.menu.draw(screen, w // 2, trect.bottom + 40)
        self._draw_howto(screen, w, h)

    def _draw_howto(self, screen, w, h):
        lines = [
            tr(key, self.app.language) for key in _HOWTO_KEYS
            if has(key, self.app.language)
        ]
        if not lines:
            return
        line_h = self.help_font.get_height() + config.MENU_HELP_LINE_SPACING

        bottom = h - config.MENU_HELP_BOTTOM_MARGIN
        for i, text in enumerate(reversed(lines)):
            label = self.help_font.render(text, True, config.MENU_HELP_COLOR)
            shadow = self.help_font.render(text, True, config.HUD_SHADOW_COLOR)
            rect = label.get_rect(midbottom=(w // 2, bottom - i * line_h))
            screen.blit(shadow, rect.move(2, 2))
            screen.blit(label, rect)
