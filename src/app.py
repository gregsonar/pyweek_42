import pygame as pg

from . import audio
from . import config
from . import save as save_module
from .i18n import tr

class App:

    def __init__(self):
        pg.init()
        audio.init()
        self.screen = pg.display.set_mode((config.WIN_WIDTH, config.WIN_HEIGHT))
        pg.display.set_caption(tr("game_title"))
        self.clock = pg.time.Clock()

        self.save = save_module.load()
        self.language = self.save.language or config.LANGUAGE

        self.music_on = (
            self.save.music_on
            if self.save.music_on is not None
            else config.AUDIO_MUSIC_DEFAULT
        )
        self.sfx_on = (
            self.save.sfx_on
            if self.save.sfx_on is not None
            else config.AUDIO_SFX_DEFAULT
        )
        audio.set_music_enabled(self.music_on)
        audio.set_sfx_enabled(self.sfx_on)
        self.running = True
        self._scenes = []
        self._fade = None
        self._fade_surf = None

    def set_language(self, language):
        self.language = language
        self.save.language = language
        self.persist()

    def persist(self):
        save_module.persist(self.save)

    def toggle_music(self):
        self.music_on = not self.music_on
        self.save.music_on = self.music_on
        audio.set_music_enabled(self.music_on)
        self.persist()

    def toggle_sfx(self):
        self.sfx_on = not self.sfx_on
        self.save.sfx_on = self.sfx_on
        audio.set_sfx_enabled(self.sfx_on)
        self.persist()

    @property
    def scene(self):
        return self._scenes[-1] if self._scenes else None

    def push_scene(self, scene):
        self._scenes.append(scene)
        scene.on_enter()
        self._apply_mouse_mode()

    def pop_scene(self):
        if self._scenes:
            self._scenes.pop().on_exit()
        self._apply_mouse_mode()

    def replace_scene(self, scene):
        if self._scenes:
            self._scenes.pop().on_exit()
        self._scenes.append(scene)
        scene.on_enter()
        self._apply_mouse_mode()

    def fade_to(self, new_scene):
        if self._fade is not None:
            return
        self._fade = {"phase": "out", "t": 0.0, "next": new_scene}

    def _advance_fade(self, dt):
        fade = self._fade
        fade["t"] += dt
        if fade["t"] < config.FADE_DURATION:
            return
        if fade["phase"] == "out":
            self.replace_scene(fade["next"])
            fade["phase"] = "in"
            fade["t"] = 0.0
            fade["next"] = None
        else:
            self._fade = None

    def _fade_alpha(self):
        frac = min(1.0, self._fade["t"] / config.FADE_DURATION)
        return frac if self._fade["phase"] == "out" else 1.0 - frac

    def _draw_fade(self):
        alpha = int(max(0.0, min(1.0, self._fade_alpha())) * 255)
        if alpha <= 0:
            return
        if self._fade_surf is None:
            self._fade_surf = pg.Surface((config.WIN_WIDTH, config.WIN_HEIGHT))
            self._fade_surf.fill(config.FADE_COLOR)
        self._fade_surf.set_alpha(alpha)
        self.screen.blit(self._fade_surf, (0, 0))

    def quit(self):
        self.running = False

    def _apply_mouse_mode(self):
        scene = self.scene
        grab = bool(getattr(scene, "wants_mouse_grab", False))
        pg.mouse.set_visible(not grab)
        pg.event.set_grab(grab)

        pg.mouse.get_rel()

    def run(self):
        while self.running and self._scenes:
            dt = min(self.clock.tick(config.FPS) / 1000.0, config.MAX_DT)
            events = pg.event.get()
            for event in events:
                if event.type == pg.QUIT:
                    self.running = False

            fading = self._fade is not None
            scene = self.scene
            if scene is not None and not fading:
                scene.handle_events(events)

            if self.scene is not None:
                self.scene.update(dt)
            if self._fade is not None:
                self._advance_fade(dt)
            self._draw()
            if self._fade is not None:
                self._draw_fade()
            pg.display.flip()
        pg.quit()

    def _draw(self):
        if not self._scenes:
            return
        start = len(self._scenes) - 1
        while start > 0 and getattr(self._scenes[start], "render_below", False):
            start -= 1
        for scene in self._scenes[start:]:
            scene.draw(self.screen)
