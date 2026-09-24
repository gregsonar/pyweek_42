# src/app.py
"""Приложение: окно, главный цикл и стек сцен (экранов)."""

import pygame as pg

from . import config


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
        pg.display.set_caption("Borrowed Time")
        self.clock = pg.time.Clock()
        self.language = config.LANGUAGE
        self.running = True
        self._scenes = []  # стек сцен, верхняя - активная

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
            scene = self.scene
            if scene is not None:
                scene.handle_events(events)
            # сцена могла смениться в handle_events - обновляем актуальную верхнюю
            if self.scene is not None:
                self.scene.update(dt)
            self._draw()
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
