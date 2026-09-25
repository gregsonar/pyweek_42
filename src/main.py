# src/main.py
"""Игровая сцена: ввод, обновление и отрисовка игрового процесса."""

import random

import numpy as np
import pygame as pg

from . import audio, config
from .app import App
from .entities import Spark
from .fonts import load_font
from .hud import Hud
from .i18n import has
from .interactables import (
    ButtonLink,
    Interactable,
    InteractState,
    select_highlight,
)
from .placeholder_sprites import button_states
from .renderer import Renderer
from .scene import Scene
from .timing import TimeController, Timer
from .traps import Trap
from .utils import desaturate, load_sprite, load_texture, load_textures


class GameplayScene(Scene):
    """Игровой процесс: рендер сцены, движение игрока, время, ловушки, HUD."""

    wants_mouse_grab = True  # игра захватывает мышь и прячет курсор

    def __init__(self, app, level_index=0):
        super().__init__(app)
        self.level_index = level_index
        self._level = config.LEVELS[level_index]  # данные текущего уровня

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
            23: "assets/textures/walls/wall-outside-window.png",
            "floor": "assets/textures/flats/floor_grate.png",
            "floor2": "assets/textures/flats/floor_grate_2.png",  # 2-й вариант пола
            "floor_outside": "assets/textures/flats/outside-window-floor.png",
            "ceil": "assets/textures/flats/ceiling_panel.png",
            "ceil2": "assets/textures/flats/ceiling_panel-2.png",  # 2-й вариант потолка
            "sky": "assets/textures/flats/sky.png",  # для режима SKY_MODE
        }
        textures = load_textures(texture_paths)

        # Кастомные тайлы пола по клеткам: (строка, столбец) -> текстура.
        # Строятся из floor_overrides уровня (ключ текстуры -> массив). Клетки
        # с неизвестным ключом пропускаем.
        self._floor_overrides = {
            cell: textures[key]
            for cell, key in self._level.floor_overrides.items()
            if key in textures
        }

        # HUD (шрифты готовы - pygame инициализирован в App). Язык хранит App.
        self.hud = Hud(self.app.language)

        # Данные уровня (карты, старт, режим верха) в одном объекте
        level = self._level

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
        self._is_firing = False  # зажата ли ЛКМ (для god rays/искр в draw)

        # Частицы
        self.sparks = [Spark() for _ in range(config.SPARK_COUNT)]

        # Интерактивные объекты из дата-таблицы уровня (кнопки/двери/выход).
        # _load_interactables выставляет self.exit_door, linked_doors, button_links.
        self.exit_door = None
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
        self.completion_time = None  # время добега до двери (сек), ставится в _win

        # Дебаг-оверлей позиции/поворота игрока (F3) - для расстановки спрайтов
        # и правки уровня. По умолчанию выключен.
        self.show_debug = False
        self._debug_font = load_font(config.HUD_TEXT_SIZE)

        # Вводное сообщение уровня (только при первом входе)
        self._show_level_intro()

    def on_enter(self):
        """Сброс накопленной дельты мыши, чтобы камера не прыгнула при входе."""
        pg.mouse.get_rel()

    def _win(self):
        """Завершение уровня. Не последний -> межуровневый экран и следующий
        уровень; последний -> экран победы. Оба перехода с фейдом.

        Основной триггер - дверь-выход (E, см. update_interaction). F10 оставлен
        временно как дев-шорткат (потом убрать или вынести в чит-режим).
        Фиксируем время добега до двери от старта уровня.
        """
        self.completion_time = self.timer.seconds
        print(
            "level %d complete in %.2f s"
            % (self._level.number, self.completion_time),
            flush=True,
        )
        next_index = self.level_index + 1
        if next_index < len(config.LEVELS):
            # разблокировать следующий уровень (для «Продолжить») и показать экран
            self.app.save.set_progress(config.LEVELS[next_index].number)
            self.app.persist()
            from .levelcomplete import LevelCompleteScene

            self.app.fade_to(
                LevelCompleteScene(
                    self.app, self._level.number, self.completion_time, next_index
                )
            )
        else:
            from .victory import VictoryScene

            self.app.fade_to(VictoryScene(self.app))

    def _show_level_intro(self):
        """Показать вводное сообщение уровня, если оно задано в i18n."""
        key = "level_%d_msg" % self.level_number
        if has(key, self.app.language):
            self.hud.set_message(key, seconds=config.LEVEL_MSG_SECONDS)

    def _build_interactables(self):
        """Интерактивные объекты уровня из дата-таблицы (совместимо с дизайнером).

        _load_interactables строит кнопки/двери/выход, заполняет self.exit_door,
        self.linked_doors и self.button_links. Возвращает список E-объектов.
        """
        return self._load_interactables(self._level.interactables)

    def _load_interactables(self, table):
        """Строит интерактивные объекты из дата-таблицы.

        Виды (kind):
          "button" (id для ссылок) - кнопка, E циклит состояния (0 красн., 1 зел.);
          "locked_door" (button=id управляющей кнопки; файлы locked/closed/open) -
            запираемая дверь: кнопка разблокирует, E у двери открывает. Идёт в
            self.linked_doors + связь self.button_links;
          "door" (closed/open) - простая дверь, E переключает;
          "exit" (closed) - по E завершает уровень (self.exit_door), радиус
            срабатывания вдвое меньше.
        Пути к спрайтам - относительно assets/textures/. Возвращает E-объекты
        (кнопки, простые двери, выход); запираемые двери - в self.linked_doors.
        """
        pref = "assets/textures/"
        objs = []
        self.linked_doors = []
        self.button_links = []
        buttons = {}

        def common(spec):
            return dict(
                angle=spec.get("angle", 0.0),
                width=spec.get("width", 1.0),
                height=spec.get("height", 1.0),
                y_offset=spec.get("y_offset", 0.0),
                cyclic=spec.get("cyclic", True),
                billboard=spec.get("billboard", False),
            )

        # Кнопки - первым проходом (двери ссылаются на них по id)
        for spec in table:
            if spec.get("kind") == "button":
                buttons[spec.get("id")] = Interactable(
                    spec["x"], spec["y"],
                    [InteractState(s) for s in button_states()],
                    **common(spec),
                )

        for spec in table:
            kind = spec["kind"]
            if kind == "button":
                objs.append(buttons[spec.get("id")])
            elif kind == "door":
                objs.append(Interactable(
                    spec["x"], spec["y"],
                    [
                        InteractState(load_sprite(pref + spec["closed"]), solid=True),
                        InteractState(load_sprite(pref + spec["open"]), solid=False),
                    ],
                    **common(spec),
                ))
            elif kind == "locked_door":
                door = Interactable(
                    spec["x"], spec["y"],
                    [
                        InteractState(load_sprite(pref + spec["locked"]), solid=True),
                        InteractState(load_sprite(pref + spec["closed"]), solid=True),
                        InteractState(load_sprite(pref + spec["open"]), solid=False),
                    ],
                    block_radius=spec.get("block_radius"),
                    **common(spec),
                )
                self.linked_doors.append(door)
                self.button_links.append(
                    ButtonLink(buttons[spec["button"]], [door], open_state=1)
                )
            elif kind == "exit":
                obj = Interactable(
                    spec["x"], spec["y"],
                    [InteractState(load_sprite(pref + spec["closed"]), solid=True)],
                    interact_radius=config.INTERACT_RADIUS * 0.5,
                    **common(spec),
                )
                self.exit_door = obj
                objs.append(obj)
        return objs

    def _build_props(self):
        """Декор из дата-таблицы уровня (совместимо с дизайнером уровней)."""
        return self._load_props(self._level.props)

    def _load_props(self, table):
        """Строит декор-пропсы из таблицы.

        Запись: (file, w, h, x, y, y_offset, solid, block_radius[, billboard]).
        file - путь относительно assets/textures/. Сторона квадрата = max(w, h).
        block_radius=None -> дефолт config.OBJECT_BLOCK_RADIUS. billboard
        (опционально, по умолч. False) -> спрайт всегда лицом к игроку.
        """
        props = []
        for entry in table:
            file, w, h, x, y, y_offset, solid, block_radius = entry[:8]
            billboard = entry[8] if len(entry) > 8 else False
            spr = load_sprite("assets/textures/" + file)
            side = max(w, h)
            props.append(
                Interactable(
                    x,
                    y,
                    [InteractState(spr, solid=solid)],
                    angle=0.0,
                    width=side,
                    height=side,
                    y_offset=y_offset,
                    block_radius=block_radius,
                    billboard=billboard,
                )
            )
        return props

    def _build_traps(self):
        """Ловушки из дата-таблицы уровня (совместимо с дизайнером уровней)."""
        return self._load_traps(self._level.traps)

    def _load_traps(self, table):
        """Строит ловушки из таблицы: (x, y, intervals_ms, start_active).

        intervals_ms - список длительностей фаз в мс (чередуются вкл/выкл от
        start_active, зациклено). Текстуры ловушки (активная + обесцвеченная
        пассивная) - на стороне игры.
        """
        tex_on = load_texture("assets/textures/flats/floor_trap_enabled.png")
        tex_off = desaturate(
            tex_on, amount=config.TRAP_OFF_DESATURATE, dim=config.TRAP_OFF_DIM
        )
        return [
            Trap(x, y, tex_on, tex_off, intervals_ms, start_active=active)
            for (x, y, intervals_ms, active) in table
        ]

    @property
    def _world_objects(self):
        """Все спрайтовые объекты сцены: интерактивные, декор, управляемые двери."""
        return self.interactables + self.props + self.linked_doors

    def _blocked_by_object(self, nx, ny):
        """Есть ли рядом с точкой (nx, ny) твёрдый объект, мешающий проходу.

        Проверяются интерактивные объекты, декор (пропсы) и управляемые двери:
        непроходимость задаётся флагом solid у состояния. Радиус блокировки -
        block_radius объекта, иначе общий config.OBJECT_BLOCK_RADIUS.
        """
        for obj in self._world_objects:
            if not obj.solid:
                continue
            radius = (
                obj.block_radius
                if obj.block_radius is not None
                else config.OBJECT_BLOCK_RADIUS
            )
            if np.hypot(obj.x - nx, obj.y - ny) < radius:
                return True
        return False

    @property
    def player_can_act(self):
        """Может ли игрок двигаться/поворачиваться/взаимодействовать/жать F."""
        return self.time_ctrl.player_running and self._stun_ticks <= 0

    def handle_events(self, events):
        """Дискретные события кадра: E (использовать), L (язык), F (заём), Esc,
        F3 (дебаг-оверлей позиции/поворота), F10 (дев-победа)."""
        # Флаг использования сбрасывается каждый кадр и выставляется по нажатию
        self.interact_pressed = False
        for event in events:
            if event.type != pg.KEYDOWN:
                continue
            if event.key == pg.K_ESCAPE:
                from .pause import PauseScene  # ленивый импорт - разрыв цикла

                self.app.push_scene(PauseScene(self.app))
            elif event.key == pg.K_e:
                self.interact_pressed = True
            elif event.key == pg.K_l:
                self.app.set_language("ru" if self.app.language == "en" else "en")
                self.hud.set_language(self.app.language)
            elif event.key == pg.K_f and self.player_can_act:
                self.time_ctrl.toggle_freeze()
                audio.play("freeze" if not self.time_ctrl.world_running else "unfreeze")
            elif event.key == pg.K_F3:
                self.show_debug = not self.show_debug  # оверлей позиции/поворота
            elif event.key == pg.K_F10:
                self._win()  # ВРЕМЕННО: имитация победы (пока нет цели уровня)

    def _update_input(self, dt):
        """Непрерывный ввод: ЛКМ (фокус), поворот мышью, движение. -> is_firing."""
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

    def update(self, dt):
        """Кадр логики: ввод, фиксированные тики (время/мир/урон), HUD, выбор."""
        is_firing = self._update_input(dt)

        # Шаги логики времени (фиксированный тик): механика заёма/возврата и
        # мир (ловушки) - при world_running; урон - каждый тик
        for _ in range(self.timer.update(dt)):
            if self._stun_ticks > 0:
                self._stun_ticks -= 1
            self.time_ctrl.step()
            if self.time_ctrl.world_running:
                self.world_step()
            # Урон от активных ловушек - каждый тик, независимо от остановки мира:
            # включённая ловушка опасна и в замороженном состоянии
            self._apply_trap_damage()

        self.hud.update(dt, player_frozen=not self.time_ctrl.player_running)
        self.update_interaction()
        self._is_firing = is_firing

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

    def draw(self, screen):
        """Полный цикл рендеринга кадра на screen (без flip - им занят App)."""
        # Буферы (переиспользуем кадровый буфер, пол/потолок перезапишут всё)
        frame = self._frame
        frame.fill(0.0)
        self.renderer.begin_frame()

        # 1. Пол и потолок (кастомные тайлы пола по клеткам + подмена под ловушками)
        floor_tiles = dict(self._floor_overrides)
        floor_tiles.update({trap.cell: trap.texture for trap in self.traps})
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
            self._world_objects,
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

        # 6. Частицы (только когда игра активна - под паузой заморожены)
        if self.app.scene is self:
            self.update_particles(self._is_firing, hit_info)

        # 7. Масштабирование на полный экран
        screen.blit(
            pg.transform.scale(self.virt_surf, (config.WIN_WIDTH, config.WIN_HEIGHT)),
            (0, 0),
        )

        # 8. HUD поверх масштабированной сцены (в разрешении окна)
        self.hud.draw(
            screen,
            time_left=self.time_left_ticks / config.TICK_RATE,
            hp=self.hp,
            max_hp=config.PLAYER_MAX_HP,
            level_number=self.level_number,
            world_frozen=not self.time_ctrl.world_running,
            budget_fraction=self.time_ctrl.budget_fraction,
        )

        # 9. Дебаг-оверлей позиции/поворота (F3)
        if self.show_debug:
            self._draw_debug(screen)

    def _draw_debug(self, screen):
        """Оверлей текущей позиции/поворота игрока (для расстановки объектов).

        Показывает x/y и angle (радианы - как в данных уровня, PROPS/
        INTERACTABLES/player_start), клетку карты (row=int y, col=int x) и угол
        в градусах. Рисуется в левом верхнем углу.
        """
        x = self.player["x"]
        y = self.player["y"]
        angle = self.player["angle"]
        line1 = "x=%.2f  y=%.2f  angle=%.3f" % (x, y, angle)
        line2 = "cell row=%d col=%d   deg=%.1f" % (
            int(y), int(x), float(np.degrees(angle))
        )
        m = config.HUD_MARGIN
        lh = self._debug_font.get_height() + 2
        for i, text in enumerate((line1, line2)):
            shadow = self._debug_font.render(text, True, config.HUD_SHADOW_COLOR)
            label = self._debug_font.render(text, True, config.HUD_COLOR)
            screen.blit(shadow, (m + 1, m + i * lh + 1))
            screen.blit(label, (m, m + i * lh))

    def update_interaction(self):
        """Выбор подсвеченного объекта и его использование по нажатию E."""
        # Блокировка управляемых дверей следует за кнопками (до выбора подсветки)
        for link in self.button_links:
            link.sync()

        # Кандидаты на подсветку: обычные E-объекты + РАЗБЛОКИРОВАННЫЕ двери
        # (заперта = state 0 -> не подсвечивается, по E не используется)
        candidates = self.interactables + [
            door for door in self.linked_doors if door.state != 0
        ]
        self.highlighted = select_highlight(
            candidates,
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
            # Одноразовое срабатывание: гасим флаг сразу, чтобы использование не
            # повторялось на следующих кадрах (например, во время фейда, когда
            # handle_events не вызывается и не сбрасывает флаг сам).
            self.interact_pressed = False
            if self.highlighted is self.exit_door:
                self._win()  # дверь-выход завершает уровень
            elif self.highlighted in self.linked_doors:
                # разблокированная дверь: E переключает закрыта(1) <-> открыта(2)
                self.highlighted.state = 2 if self.highlighted.state == 1 else 1
            else:
                self.highlighted.use()

    def world_step(self):
        """Один мировой тик: обратный отсчёт и циклы ловушек.

        Вызывается только при world_running, поэтому отсчёт времени попытки и
        переключение ловушек вкл/выкл стоят, пока игрок держит мир остановленным.
        Урон от активных ловушек применяется отдельно (см. _apply_trap_damage в
        update) - каждый тик, чтобы включённая на момент остановки времени
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
        # Полноэкранная вспышка урона в HUD + звук
        self.hud.flash_damage()
        audio.play("hurt")
        print("player hit by trap, hp=%d" % self.hp, flush=True)
        if self.hp <= 0:
            print("player died - level restart", flush=True)
            self.reset_level()

    def reset_level(self):
        """Полный мягкий сброс уровня (при проигрыше)."""
        level = self._level
        self.player = level.player_start.copy()
        self.hp = config.PLAYER_MAX_HP
        self._trap_contact_cell = None
        self._trap_contact_ticks = 0
        self._stun_ticks = 0
        for trap in self.traps:
            trap.reset()
        for obj in self.interactables:
            obj.state = 0
        for door in self.linked_doors:
            door.state = 0  # управляемые двери - закрыты (кнопки сброшены выше)
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


def run_engine():
    """Точка входа: запустить приложение со сплеш-заставки."""
    # Ленивый импорт разрывает цикл main <-> splash/menu (импортируют GameplayScene)
    from .splash import SplashScene

    app = App()
    app.push_scene(SplashScene(app))
    app.run()
