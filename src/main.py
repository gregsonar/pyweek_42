# src/main.py
"""Основной цикл игры: ввод, обновление, отрисовка."""

import random

import numpy as np
import pygame as pg

from src.i18n import has, tr

from . import config
from .entities import Spark
from .hud import Hud
from .interactables import Interactable, InteractState, select_highlight
from .placeholder_sprites import button_states
from .renderer import Renderer
from .timing import TimeController, Timer
from .traps import Trap
from .utils import desaturate, load_sprite, load_texture, load_textures


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
        self.rays_surf = pg.Surface(
            (config.VIRT_WIDTH, config.VIRT_HEIGHT), pg.SRCALPHA
        )

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
            21: "assets/textures/walls/wall_concrete_01_up.png",
            22: "assets/textures/walls/wall_concrete_02_up.png",
            "floor": "assets/textures/flats/floor_grate.png",
            "floor2": "assets/textures/flats/floor_grate_2.png",  # 2-й вариант пола
            "ceil": "assets/textures/flats/ceiling_panel.png",
            "ceil2": "assets/textures/flats/ceiling_panel-2.png",  # 2-й вариант потолка
            "sky": "assets/textures/flats/sky.png",  # для режима SKY_MODE
        }
        textures = load_textures(texture_paths)

        # Локализация интерфейса и HUD (создаётся после pg.init - шрифты готовы)
        self.language = config.LANGUAGE
        self.hud = Hud(self.language)

        # Данные уровня (карты, старт, режим верха) в одном объекте
        level = config.DEFAULT_LEVEL

        # Инициализация рендерера (нижний и верхний пояс стен, режим верха)
        self.renderer = Renderer(
            textures, level.lower_map, level.upper_map, sky_mode=level.sky_mode
        )

        # Состояние игрока
        self.player = level.player_start.copy()

        # Параметры эффектов
        self.focus = config.VIGNETTE  # фокусное расстояние / виньетка
        self.brightness = config.BASE_BRIGHTNESS  # яркость
        self.rays_intensity = 0.0  # интенсивность god rays

        # Частицы
        self.sparks = [Spark() for _ in range(config.SPARK_COUNT)]

        # Интерактивные объекты (пока с заглушками-спрайтами)
        self.interactables = self._build_interactables()
        self.highlighted = None  # текущий подсвеченный объект
        self.interact_pressed = False  # флаг нажатия клавиши использования

        # Неинтерактивный декор (плоские спрайты, не участвуют в подсветке/E)
        self.props = self._build_props()

        # Ловушки (объекты мира; циклят по мировым тикам)
        self.traps = self._build_traps()

        # Здоровье игрока и состояние касания активной ловушки
        self.hp = config.PLAYER_MAX_HP
        self._trap_contact_cell = None
        self._trap_contact_ticks = 0
        self._stun_ticks = 0  # оставшийся стан игрока при уроне (тики)

        # Буфер кадра переиспользуется между кадрами (без переаллокации)
        self._frame = np.zeros(
            (config.VIRT_WIDTH, config.VIRT_HEIGHT, 3), dtype=np.float32
        )

        # Время: фиксированный шаг логики + механика заёма/возврата времени
        self.timer = Timer()
        self.time_ctrl = TimeController(self.timer)

        # Обратный отсчёт времени попытки (в тиках; идёт только при world_running,
        # то есть останавливается, когда игрок останавливает время)
        self.level_number = level.number
        self._time_limit_ticks = round(level.time_limit * config.TICK_RATE)
        self.time_left_ticks = self._time_limit_ticks

        self.clock = pg.time.Clock()
        self.running = True

        # Вводное сообщение уровня (только при первом входе)
        self._show_level_intro()

    def _show_level_intro(self):
        """Показать вводное сообщение уровня, если оно задано в i18n."""
        key = "level_%d_msg" % self.level_number
        if has(key, self.language):
            self.hud.set_message(key, seconds=config.LEVEL_MSG_SECONDS)

    def _build_interactables(self):
        """Расставляет объекты на карте по умолчанию."""
        btn = button_states()  # кнопка пока на заглушке
        door_closed = load_sprite("assets/textures/sprites/spr_door1_closed.png")
        door_open = load_sprite("assets/textures/sprites/spr_door1_open.png")
        return [
            # Кнопка на северной грани перегородки: поверхность вдоль X, приподнята
            Interactable(
                5.0,
                4.6,
                [InteractState(btn[0]), InteractState(btn[1])],
                angle=0.0,
                width=0.5,
                height=0.5,
                y_offset=0.35,
                cyclic=True,
            ),
            # Дверь в проёме перегородки: поверхность вдоль X (перекрывает проход
            # по Y), в один тайл, ровно в нижнем поясе
            Interactable(
                6.5,
                5.5,
                [
                    InteractState(door_closed, solid=True),
                    InteractState(door_open, solid=False),
                ],
                angle=0.0,
                width=1.0,
                height=1.0,
                y_offset=0.0,
                cyclic=True,
            ),
        ]

    def _build_props(self):
        """Расставляет неинтерактивный декор. Сторона квадрата = max(w, h)."""
        base = "assets/textures/sprites/"

        def prop(name, real_w, real_h, x, y, y_offset=0.0):
            side = max(real_w, real_h)
            spr = load_sprite(base + name)
            return Interactable(
                x,
                y,
                [InteractState(spr)],
                angle=0.0,
                width=side,
                height=side,
                y_offset=y_offset,
            )

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

    def _build_traps(self):
        """Демо-ловушки. Пассивная текстура - временно обесцвеченная активная."""
        tex_on = load_texture("assets/textures/flats/floor_trap_enabled.png")
        tex_off = desaturate(
            tex_on, amount=config.TRAP_OFF_DESATURATE, dim=config.TRAP_OFF_DIM
        )
        on, off = config.TRAP_ON_TICKS, config.TRAP_OFF_TICKS
        return [
            # На пути от старта на север (игрок наступит)
            Trap(6, 3, tex_on, tex_off, on, off, start_active=True),
            # Южная половина, другой ритм и противофаза
            Trap(3, 8, tex_on, tex_off, 60, 120, start_active=False),
        ]

    def _blocked_by_object(self, nx, ny):
        """Есть ли рядом с точкой (nx, ny) твёрдый объект, мешающий проходу."""
        for obj in self.interactables:
            if (
                obj.solid
                and np.hypot(obj.x - nx, obj.y - ny) < config.OBJECT_BLOCK_RADIUS
            ):
                return True
        return False

    @property
    def player_can_act(self):
        """Может ли игрок двигаться/поворачиваться/взаимодействовать/жать F."""
        return self.time_ctrl.player_running and self._stun_ticks <= 0

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
            # Переключение языка интерфейса (en/ru)
            if event.type == pg.KEYDOWN and event.key == pg.K_l:
                self.language = "ru" if self.language == "en" else "en"
                self.hud.set_language(self.language)
            # Способность заёма времени: остановка мира (тоггл)
            if event.type == pg.KEYDOWN and event.key == pg.K_f and self.player_can_act:
                self.time_ctrl.toggle_freeze()

        # Управление фокусом (ЛКМ)
        is_firing = pg.mouse.get_pressed()[0]
        target_focus = 280.0 if is_firing else config.VIGNETTE
        target_bright = 15.0 if is_firing else config.BASE_BRIGHTNESS
        target_rays = 1.0 if is_firing else 0.0

        # Плавное изменение параметров
        self.focus += (target_focus - self.focus) * 0.1
        self.brightness += (target_bright - self.brightness) * 0.1
        self.rays_intensity += (target_rays - self.rays_intensity) * 0.1

        # Поворот камеры мышью (get_rel вызываем всегда, чтобы дельта не копилась;
        # при заморозке/стане игрока поворот не применяем)
        rel_x, _ = pg.mouse.get_rel()
        if self.player_can_act:
            self.player["angle"] += rel_x * config.MOUSE_SENSITIVITY

        # Перемещение клавишами
        keys = pg.key.get_pressed()
        dx, dy = 0, 0
        sin_a, cos_a = np.sin(self.player["angle"]), np.cos(self.player["angle"])

        if keys[pg.K_w]:
            dx += cos_a
            dy += sin_a
        if keys[pg.K_s]:
            dx -= cos_a
            dy -= sin_a
        if keys[pg.K_a]:
            dx += sin_a
            dy -= cos_a
        if keys[pg.K_d]:
            dx -= sin_a
            dy += cos_a

        # При заморозке (возврат долга) или стане (урон) движение отключено
        if not self.player_can_act:
            dx = dy = 0.0

        # Коллизия с картой (упрощённая) и с твёрдыми объектами
        next_x, next_y = self.player["x"] + dx * 0.3, self.player["y"] + dy * 0.3
        if (
            0 <= int(next_y) < self.renderer.map_h
            and 0 <= int(self.player["x"] + dx * 0.3) < self.renderer.map_w
            and self.renderer.map[
                int(self.player["y"]), int(self.player["x"] + dx * 0.3)
            ]
            == 0
            and not self._blocked_by_object(next_x, self.player["y"])
        ):
            self.player["x"] += dx * config.MOVE_SPEED * dt
        if (
            0 <= int(self.player["y"] + dy * 0.3) < self.renderer.map_h
            and 0 <= int(next_x) < self.renderer.map_w
            and self.renderer.map[
                int(self.player["y"] + dy * 0.3), int(self.player["x"])
            ]
            == 0
            and not self._blocked_by_object(self.player["x"], next_y)
        ):
            self.player["y"] += dy * config.MOVE_SPEED * dt

        return is_firing

    def update_particles(self, is_firing, hit_info):
        """Обновление и отрисовка частиц."""
        # Спавн искр при "сварке"
        if is_firing and hit_info and hit_info[2] < 6:
            if random.random() > 0.4:
                for spark in self.sparks:
                    if not spark.is_active():
                        spark.spawn(hit_info[0], hit_info[1], self.player["angle"])
                        break

        # Обновление и отрисовка
        for spark in self.sparks:
            if spark.update():
                dx_s = spark.x - self.player["x"]
                dy_s = spark.y - self.player["y"]
                dist_s = dx_s * np.cos(self.player["angle"]) + dy_s * np.sin(
                    self.player["angle"]
                )

                if dist_s > 0.1:
                    # Проекция на экран
                    screen_x = int(
                        (
                            (
                                dx_s * -np.sin(self.player["angle"])
                                + dy_s * np.cos(self.player["angle"])
                            )
                            / dist_s
                            / 1.1
                            + 0.5
                        )
                        * config.VIRT_WIDTH
                    )
                    screen_y = int(
                        config.VIRT_HEIGHT / 2 + (spark.z / dist_s * config.VIRT_HEIGHT)
                    )

                    # Отрисовка, если искра ближе, чем стена
                    if (
                        0 <= screen_x < config.VIRT_WIDTH
                        and 0 <= screen_y < config.VIRT_HEIGHT
                        and dist_s < self.renderer.z_buffer[screen_x, screen_y]
                    ):
                        size = max(1, int(3 / dist_s))
                        pg.draw.rect(
                            self.virt_surf,
                            (255, 200, 50),
                            (screen_x, screen_y, size, size),
                        )

    def render(self, is_firing):
        """Полный цикл рендеринга кадра."""
        # Буферы (переиспользуем кадровый буфер, пол/потолок перезапишут всё)
        frame = self._frame
        frame.fill(0.0)
        self.renderer.begin_frame()

        # 1. Пол и потолок (с подменой тайлов под ловушками)
        floor_tiles = {trap.cell: trap.texture for trap in self.traps}
        self.renderer.render_floor_ceiling(
            frame,
            self.player["x"],
            self.player["y"],
            self.player["angle"],
            floor_tiles=floor_tiles,
        )

        # 2. Стены
        hit_info = self.renderer.render_walls(
            frame, self.player["x"], self.player["y"], self.player["angle"]
        )

        # 3. Объекты и декор (плоские спрайты) - до пост-обработки
        self.renderer.render_sprites(
            frame,
            self.player["x"],
            self.player["y"],
            self.player["angle"],
            self.interactables + self.props,
            self.highlighted,
        )

        # 4. Пост-обработка
        final = self.renderer.apply_post_processing(
            frame, focus=self.focus, brightness=self.brightness, saturation_mult=1.0
        )
        pg.surfarray.blit_array(self.virt_surf, final)

        # 5. God rays
        self.renderer.draw_god_rays(self.rays_surf, self.rays_intensity)
        self.virt_surf.blit(self.rays_surf, (0, 0))

        # 6. Частицы
        self.update_particles(is_firing, hit_info)

        # 7. Масштабирование на полный экран
        self.screen.blit(
            pg.transform.scale(self.virt_surf, (config.WIN_WIDTH, config.WIN_HEIGHT)),
            (0, 0),
        )

        # 8. HUD поверх масштабированной сцены (в разрешении окна)
        self.hud.draw(
            self.screen,
            time_left=self.time_left_ticks / config.TICK_RATE,
            hp=self.hp,
            max_hp=config.PLAYER_MAX_HP,
            level_number=self.level_number,
            world_frozen=not self.time_ctrl.world_running,
            budget_fraction=self.time_ctrl.budget_fraction,
        )

        pg.display.flip()

    def update_interaction(self):
        """Выбор подсвеченного объекта и его использование по нажатию E."""
        self.highlighted = select_highlight(
            self.interactables,
            self.player["x"],
            self.player["y"],
            self.player["angle"],
            self.renderer.map,
        )
        if (
            self.interact_pressed
            and self.highlighted is not None
            and self.player_can_act
        ):
            self.highlighted.use()

    def world_step(self):
        """Один мировой тик: обратный отсчёт и циклы ловушек.

        Вызывается только при world_running, поэтому отсчёт времени попытки и
        переключение ловушек вкл/выкл стоят, пока игрок держит мир остановленным.
        Урон от активных ловушек применяется отдельно (см. _apply_trap_damage в
        главном цикле) - каждый тик, чтобы включённая на момент остановки времени
        ловушка оставалась опасной и при замороженном мире.
        """
        # Обратный отсчёт времени попытки; при исчерпании - рестарт
        self.time_left_ticks -= 1
        if self.time_left_ticks <= 0:
            self.time_left_ticks = 0
            print("time is up - level restart", flush=True)
            self.reset_level()
            self.hud.set_message("time_up", seconds=2.0)
            return
        for trap in self.traps:
            trap.step()

    def _active_trap_at(self, cell):
        """Активная ловушка в клетке (строка, столбец) или None."""
        for trap in self.traps:
            if trap.active and trap.cell == cell:
                return trap
        return None

    def _apply_trap_damage(self):
        """Урон: 1 при касании работающей ловушки, далее 1/сек, пока стоишь."""
        cell = (int(self.player["y"]), int(self.player["x"]))
        if self._active_trap_at(cell) is None:
            # ушёл с ловушки или она выключилась - урон не копится
            self._trap_contact_cell = None
            self._trap_contact_ticks = 0
            return
        if self._trap_contact_cell != cell:
            # новое касание работающей ловушки - урон сразу
            self._trap_contact_cell = cell
            self._trap_contact_ticks = 0
            self._damage(1)
        else:
            self._trap_contact_ticks += 1
            if self._trap_contact_ticks >= config.TRAP_DAMAGE_PERIOD:
                self._trap_contact_ticks -= config.TRAP_DAMAGE_PERIOD
                self._damage(1)

    def _damage(self, amount):
        """Нанести урон игроку; при HP<=0 - проигрыш и рестарт уровня."""
        self.hp -= amount
        # Кратко станим игрока, чтобы урон ощущался (движение/ввод отключены)
        self._stun_ticks = config.PLAYER_STUN_TICKS
        # Полноэкранная вспышка урона в HUD
        self.hud.flash_damage()
        print("player hit by trap, hp=%d" % self.hp, flush=True)
        if self.hp <= 0:
            print("player died - level restart", flush=True)
            self.reset_level()

    def reset_level(self):
        """Полный мягкий сброс уровня (при проигрыше)."""
        level = config.DEFAULT_LEVEL
        self.player = level.player_start.copy()
        self.hp = config.PLAYER_MAX_HP
        self._trap_contact_cell = None
        self._trap_contact_ticks = 0
        self._stun_ticks = 0
        for trap in self.traps:
            trap.reset()
        for obj in self.interactables:
            obj.state = 0
        self.highlighted = None
        self.interact_pressed = False
        # Сброс времени (бюджет/долг/состояние)
        self.timer = Timer()
        self.time_ctrl = TimeController(self.timer)
        # Сброс обратного отсчёта попытки и состояния HUD
        self.time_left_ticks = self._time_limit_ticks
        self.hud.reset()
        # TODO: при смерти/рестарте показывать отдельное сообщение (не вводное) -
        # реализуем позже; вводное сообщение уровня здесь намеренно не повторяем

    def run(self):
        """Главный цикл игры."""
        while self.running:
            # Ограничиваем шаг кадра сверху: при лаге dt не должен позволять
            # проскочить сквозь стену (см. коллизию в handle_input)
            dt = min(self.clock.tick(config.FPS) / 1000.0, config.MAX_DT)
            is_firing = self.handle_input(dt)
            # Шаги логики времени (фиксированный тик): механика заёма/возврата и
            # мир (ловушки/урон) - при world_running
            for _ in range(self.timer.update(dt)):
                if self._stun_ticks > 0:
                    self._stun_ticks -= 1
                self.time_ctrl.step()
                if self.time_ctrl.world_running:
                    self.world_step()
                # Урон от активных ловушек - каждый тик, независимо от остановки
                # мира: включённая ловушка опасна и в замороженном состоянии
                self._apply_trap_damage()
            self.hud.update(dt, player_frozen=not self.time_ctrl.player_running)
            self.update_interaction()
            self.render(is_firing)

        pg.quit()


def run_engine():
    """Точка входа для запуска извне."""
    game = Game()
    game.run()
