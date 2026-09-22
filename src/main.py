# src/main.py
"""Основной цикл игры: ввод, обновление, отрисовка."""

import pygame as pg
import numpy as np
import random
from . import config
from .utils import load_textures, load_sprite
from .entities import Spark
from .renderer import Renderer
from .interactables import Interactable, InteractState, select_highlight
from .placeholder_sprites import button_states, door_states


class Game:
    """Основной класс игры."""

    def __init__(self):
        pg.init()
        self.screen = pg.display.set_mode((config.WIN_WIDTH, config.WIN_HEIGHT))
        pg.display.set_caption("Raycast Pygame Renderer")
        pg.mouse.set_visible(False)
        pg.event.set_grab(True)

        # Виртуальный буфер (низкое разрешение для ретро-эффекта)
        self.virt_surf = pg.Surface((config.VIRT_WIDTH, config.VIRT_HEIGHT))
        self.rays_surf = pg.Surface((config.VIRT_WIDTH, config.VIRT_HEIGHT), pg.SRCALPHA)

        # Загрузка ресурсов (id стен 1..15 -> новые тайлы)
        texture_paths = {
            1: "assets/textures/walls/wall_concrete_01.png",
            2: "assets/textures/walls/wall_concrete_02.png",
            3: "assets/textures/walls/wall_concrete_moss.png",
            4: "assets/textures/walls/wall_poster_wizard.png",
            5: "assets/textures/walls/wall_poster_halftone.png",
            6: "assets/textures/walls/wall_shelf_farm.png",
            7: "assets/textures/walls/wall_vent.png",
            8: "assets/textures/walls/wall_terminal.png",
            9: "assets/textures/walls/wall_console_0.png",
            10: "assets/textures/walls/wall_console_1.png",
            11: "assets/textures/walls/wall_window_0.png",
            12: "assets/textures/walls/wall_window_1.png",
            13: "assets/textures/walls/wall_window_2.png",
            14: "assets/textures/walls/wall_window_3.png",
            15: "assets/textures/walls/wall_window_4.png",
            16: "assets/textures/walls/wall_window_0_up.png",
            17: "assets/textures/walls/wall_window_1_up.png",
            18: "assets/textures/walls/wall_window_2_up.png",
            19: "assets/textures/walls/wall_window_3_up.png",
            20: "assets/textures/walls/wall_window_4_up.png",
            'floor': "assets/textures/flats/floor_grate.png",
            'ceil': "assets/textures/flats/ceiling_panel.png",
        }
        textures = load_textures(texture_paths)

        # Инициализация рендерера (нижний и верхний пояс стен)
        self.renderer = Renderer(textures, config.DEFAULT_MAP,
                                 config.DEFAULT_MAP_UPPER)

        # Состояние игрока
        self.player = config.PLAYER_START.copy()

        # Параметры эффектов
        self.focus = config.VIGNETTE  # фокусное расстояние / виньетка
        self.brightness = config.BASE_BRIGHTNESS  # яркость
        self.rays_intensity = 0.0  # интенсивность god rays

        # Частицы
        self.sparks = [Spark() for _ in range(config.SPARK_COUNT)]

        # Интерактивные объекты (пока с заглушками-спрайтами)
        self.interactables = self._build_interactables()
        self.highlighted = None       # текущий подсвеченный объект
        self.interact_pressed = False # флаг нажатия клавиши использования

        # Неинтерактивный декор (плоские спрайты, не участвуют в подсветке/E)
        self.props = self._build_props()

        self.clock = pg.time.Clock()
        self.running = True

    def _build_interactables(self):
        """Расставляет объекты на карте по умолчанию (заглушки для теста)."""
        btn = button_states()
        door = door_states()
        return [
            # Кнопка на северной грани перегородки: поверхность вдоль X, приподнята
            Interactable(5.0, 4.6,
                         [InteractState(btn[0]), InteractState(btn[1])],
                         angle=0.0, width=0.5,
                         height=0.5, y_offset=0.35, cyclic=True),
            # Дверь в проёме перегородки: поверхность вдоль X (перекрывает проход по Y)
            Interactable(6.5, 5.5,
                         [InteractState(door[0], solid=True),
                          InteractState(door[1], solid=False)],
                         angle=0.0, width=1.0,
                         height=1.0, y_offset=0.0, cyclic=True),
        ]

    def _build_props(self):
        """Расставляет неинтерактивный декор. Сторона квадрата = max(w, h)."""
        base = "assets/textures/sprites/"

        def prop(name, real_w, real_h, x, y, y_offset=0.0):
            side = max(real_w, real_h)
            spr = load_sprite(base + name)
            return Interactable(x, y, [InteractState(spr)],
                                angle=0.0, width=side, height=side,
                                y_offset=y_offset)

        return [
            # Северная половина
            # prop("spr_bed.png", 2.00, 0.74, 2.5, 1.6),
            # prop("spr_chair.png", 0.62, 1.00, 8.0, 1.6),
            prop("spr_plant.png", 0.62, 0.85, 10.5, 1.6),
            prop("spr_plant.png", 0.62, 0.85, 7.5, 1.6),
            # Южная половина
            prop("spr_crate_a.png", 1.20, 0.82, 3.5, 8.5),
            prop("spr_crate_b.png", 1.00, 1.05, 5.0, 8.5),
            prop("spr_shrooms.png", 0.55, 0.34, 7.0, 8.7),
            prop("spr_overlay.png", 0.85, 0.52, 9.5, 7.5, y_offset=1.0),
        ]

    def _blocked_by_object(self, nx, ny):
        """Есть ли рядом с точкой (nx, ny) твёрдый объект, мешающий проходу."""
        for obj in self.interactables:
            if obj.solid and \
                    np.hypot(obj.x - nx, obj.y - ny) < config.OBJECT_BLOCK_RADIUS:
                return True
        return False

    def handle_input(self, dt):
        """Обработка ввода: события и клавиши. dt — время кадра в секундах."""
        # Флаг использования сбрасывается каждый кадр и выставляется по нажатию
        self.interact_pressed = False
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                self.running = False
            # Использование объекта - по нажатию (одно срабатывание на нажатие)
            if event.type == pg.KEYDOWN and event.key == pg.K_e:
                self.interact_pressed = True

        # Управление фокусом (ЛКМ)
        is_firing = pg.mouse.get_pressed()[0]
        target_focus = 280.0 if is_firing else config.VIGNETTE
        target_bright = 15.0 if is_firing else config.BASE_BRIGHTNESS
        target_rays = 1.0 if is_firing else 0.0

        # Плавное изменение параметров
        self.focus += (target_focus - self.focus) * 0.1
        self.brightness += (target_bright - self.brightness) * 0.1
        self.rays_intensity += (target_rays - self.rays_intensity) * 0.1

        # Поворот камеры мышью
        rel_x, _ = pg.mouse.get_rel()
        self.player['angle'] += rel_x * config.MOUSE_SENSITIVITY

        # Перемещение клавишами
        keys = pg.key.get_pressed()
        dx, dy = 0, 0
        sin_a, cos_a = np.sin(self.player['angle']), np.cos(self.player['angle'])

        if keys[pg.K_w]: dx += cos_a; dy += sin_a
        if keys[pg.K_s]: dx -= cos_a; dy -= sin_a
        if keys[pg.K_a]: dx += sin_a; dy -= cos_a
        if keys[pg.K_d]: dx -= sin_a; dy += cos_a

        # Коллизия с картой (упрощённая) и с твёрдыми объектами
        next_x, next_y = self.player['x'] + dx * 0.3, self.player['y'] + dy * 0.3
        if 0 <= int(next_y) < self.renderer.map_h and \
                0 <= int(self.player['x'] + dx * 0.3) < self.renderer.map_w and \
                self.renderer.map[int(self.player['y']), int(self.player['x'] + dx * 0.3)] == 0 and \
                not self._blocked_by_object(next_x, self.player['y']):
            self.player['x'] += dx * config.MOVE_SPEED * dt
        if 0 <= int(self.player['y'] + dy * 0.3) < self.renderer.map_h and \
                0 <= int(next_x) < self.renderer.map_w and \
                self.renderer.map[int(self.player['y'] + dy * 0.3), int(self.player['x'])] == 0 and \
                not self._blocked_by_object(self.player['x'], next_y):
            self.player['y'] += dy * config.MOVE_SPEED * dt

        return is_firing

    def update_particles(self, is_firing, hit_info):
        """Обновление и отрисовка частиц."""
        # Спавн искр при "сварке"
        if is_firing and hit_info and hit_info[2] < 6:
            if random.random() > 0.4:
                for spark in self.sparks:
                    if not spark.is_active():
                        spark.spawn(hit_info[0], hit_info[1], self.player['angle'])
                        break

        # Обновление и отрисовка
        for spark in self.sparks:
            if spark.update():
                dx_s = spark.x - self.player['x']
                dy_s = spark.y - self.player['y']
                dist_s = dx_s * np.cos(self.player['angle']) + dy_s * np.sin(self.player['angle'])

                if dist_s > 0.1:
                    # Проекция на экран
                    screen_x = int(((dx_s * -np.sin(self.player['angle']) +
                                     dy_s * np.cos(self.player['angle'])) / dist_s / 1.1 + 0.5) * config.VIRT_WIDTH)
                    screen_y = int(config.VIRT_HEIGHT / 2 + (spark.z / dist_s * config.VIRT_HEIGHT))

                    # Отрисовка, если искра ближе, чем стена
                    if (0 <= screen_x < config.VIRT_WIDTH and
                            0 <= screen_y < config.VIRT_HEIGHT and
                            dist_s < self.renderer.z_buffer[screen_x, screen_y]):
                        size = max(1, int(3 / dist_s))
                        pg.draw.rect(self.virt_surf, (255, 200, 50),
                                     (screen_x, screen_y, size, size))

    def render(self, is_firing):
        """Полный цикл рендеринга кадра."""
        # Буферы
        frame = np.zeros((config.VIRT_WIDTH, config.VIRT_HEIGHT, 3), dtype=np.float32)
        self.renderer.begin_frame()

        # 1. Пол и потолок
        self.renderer.render_floor_ceiling(frame,
                                           self.player['x'], self.player['y'],
                                           self.player['angle'])

        # 2. Стены
        hit_info = self.renderer.render_walls(frame,
                                              self.player['x'], self.player['y'],
                                              self.player['angle'])

        # 3. Объекты и декор (плоские спрайты) - до пост-обработки
        self.renderer.render_sprites(frame,
                                     self.player['x'], self.player['y'],
                                     self.player['angle'],
                                     self.interactables + self.props,
                                     self.highlighted)

        # 4. Пост-обработка
        final = self.renderer.apply_post_processing(
            frame,
            focus=self.focus,
            brightness=self.brightness,
            saturation_mult=1.0
        )
        pg.surfarray.blit_array(self.virt_surf, final)

        # 5. God rays
        self.renderer.draw_god_rays(self.rays_surf, self.rays_intensity)
        self.virt_surf.blit(self.rays_surf, (0, 0))

        # 6. Частицы
        self.update_particles(is_firing, hit_info)

        # 7. Масштабирование на полный экран
        self.screen.blit(pg.transform.scale(self.virt_surf,
                                            (config.WIN_WIDTH, config.WIN_HEIGHT)),
                         (0, 0))
        pg.display.flip()

    def update_interaction(self):
        """Выбор подсвеченного объекта и его использование по нажатию E."""
        self.highlighted = select_highlight(
            self.interactables,
            self.player['x'], self.player['y'], self.player['angle'],
            self.renderer.map,
        )
        if self.interact_pressed and self.highlighted is not None:
            self.highlighted.use()

    def run(self):
        """Главный цикл игры."""
        while self.running:
            dt = self.clock.tick(config.FPS) / 1000.0
            is_firing = self.handle_input(dt)
            self.update_interaction()
            self.render(is_firing)

        pg.quit()


def run_engine():
    """Точка входа для запуска извне."""
    game = Game()
    game.run()