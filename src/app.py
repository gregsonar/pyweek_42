# src/app.py
"""Приложение: окно, главный цикл и стек сцен (экранов)."""

import pygame as pg

from . import config
from . import save as save_module
from .i18n import tr


class App:
    """
    Владеет pygame, окном, часами, языком и стеком сцен; крутит главный цикл.

    Каждый кадр: собрать события -> отдать верхней сцене (handle_events),
    обновить её (update) -> отрисовать стек (draw) -> flip. Обновляется только
    верхняя сцена, поэтому оверлей (пауза) сам "замораживает" сцену под собой.
    """

    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((config.WIN_WIDTH, config.WIN_HEIGHT))
        pg.display.set_caption(tr("game_title"))
        self.clock = pg.time.Clock()
        # Сохранение (портативное): язык и прогресс. Язык берём из сейва, иначе -
        # значение по умолчанию из config.
        self.save = save_module.load()
        self.language = self.save.language or config.LANGUAGE
        self.running = True
        self._scenes = []  # стек сцен, верхняя - активная
        self._fade = None  # активный переход между сценами (или None)
        self._fade_surf = None  # поверхность затемнения перехода (ленивая)

    def set_language(self, language):
        """Сменить язык интерфейса и сохранить выбор."""
        self.language = language
        self.save.language = language
        self.persist()

    def persist(self):
        """Записать текущее сохранение на диск."""
        save_module.persist(self.save)

    # --- управление стеком ---
    @property
    def scene(self):
        """Активная (верхняя) сцена или None."""
        return self._scenes[-1] if self._scenes else None

    def push_scene(self, scene):
        """Положить сцену на вершину стека."""
        self._scenes.append(scene)
        scene.on_enter()
        self._apply_mouse_mode()

    def pop_scene(self):
        """Снять верхнюю сцену со стека."""
        if self._scenes:
            self._scenes.pop().on_exit()
        self._apply_mouse_mode()

    def replace_scene(self, scene):
        """Заменить верхнюю сцену новой."""
        if self._scenes:
            self._scenes.pop().on_exit()
        self._scenes.append(scene)
        scene.on_enter()
        self._apply_mouse_mode()

    def fade_to(self, new_scene):
        """Плавно перейти к сцене: затемнение -> замена на середине -> проявление."""
        if self._fade is not None:
            return  # переход уже идёт
        self._fade = {"phase": "out", "t": 0.0, "next": new_scene}

    def _advance_fade(self, dt):
        """Продвинуть текущий переход; на середине заменить сцену."""
        fade = self._fade
        fade["t"] += dt
        if fade["t"] < config.FADE_DURATION:
            return
        if fade["phase"] == "out":
            self.replace_scene(fade["next"])  # полностью затемнено - меняем сцену
            fade["phase"] = "in"
            fade["t"] = 0.0
            fade["next"] = None
        else:
            self._fade = None  # переход завершён

    def _fade_alpha(self):
        """Прозрачность 0..1 чёрного оверлея по фазе перехода."""
        frac = min(1.0, self._fade["t"] / config.FADE_DURATION)
        return frac if self._fade["phase"] == "out" else 1.0 - frac

    def _draw_fade(self):
        """Наложить чёрный оверлей текущего перехода поверх сцены."""
        alpha = int(max(0.0, min(1.0, self._fade_alpha())) * 255)
        if alpha <= 0:
            return
        if self._fade_surf is None:
            self._fade_surf = pg.Surface((config.WIN_WIDTH, config.WIN_HEIGHT))
            self._fade_surf.fill(config.FADE_COLOR)
        self._fade_surf.set_alpha(alpha)
        self.screen.blit(self._fade_surf, (0, 0))

    def quit(self):
        """Завершить приложение."""
        self.running = False

    def _apply_mouse_mode(self):
        """Захват/видимость мыши по флагу активной сцены."""
        scene = self.scene
        grab = bool(getattr(scene, "wants_mouse_grab", False))
        pg.mouse.set_visible(not grab)
        pg.event.set_grab(grab)
        # Сбросить накопленную дельту мыши, чтобы камера не прыгнула при смене
        # режима (вход в игру/выход из паузы)
        pg.mouse.get_rel()

    # --- главный цикл ---
    def run(self):
        while self.running and self._scenes:
            dt = min(self.clock.tick(config.FPS) / 1000.0, config.MAX_DT)
            events = pg.event.get()
            for event in events:
                if event.type == pg.QUIT:
                    self.running = False
            # Во время перехода ввод сцен блокируем (чтобы не сработало дважды)
            fading = self._fade is not None
            scene = self.scene
            if scene is not None and not fading:
                scene.handle_events(events)
            # сцена могла смениться в handle_events - обновляем актуальную верхнюю
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
        """Отрисовать стек: от нижней видимой сцены (сквозь render_below) вверх."""
        if not self._scenes:
            return
        start = len(self._scenes) - 1
        while start > 0 and getattr(self._scenes[start], "render_below", False):
            start -= 1
        for scene in self._scenes[start:]:
            scene.draw(self.screen)
