import math
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
from .traps import BatteryTrap, Trap
from .utils import desaturate, load_sprite, load_texture, load_textures

class GameplayScene(Scene):

    wants_mouse_grab = True

    def __init__(self, app, level_index=0):
        super().__init__(app)
        self.level_index = level_index
        self._level = config.LEVELS[level_index]

        self.virt_surf = pg.Surface((config.VIRT_WIDTH, config.VIRT_HEIGHT))
        self.rays_surf = pg.Surface(
            (config.VIRT_WIDTH, config.VIRT_HEIGHT), pg.SRCALPHA
        )

        texture_paths = {
            1: "assets/textures/walls/wall_concrete_01.png",
            2: "assets/textures/walls/wall_wires.png",
            3: "assets/textures/walls/wall_graffiti_01.png",
            4: "assets/textures/walls/wall_poster_python.png",
            5: "assets/textures/walls/wall_poster_1.png",
            6: "assets/textures/walls/wall_graffiti_02.png",
            7: "assets/textures/walls/wall_vent.png",
            8: "assets/textures/walls/wall_terminal.png",
            9: "assets/textures/walls/wall_console_01.png",
            10: "assets/textures/walls/wall_mousehole_01.png",
            11: "assets/textures/walls/wall_graffiti_03.png",
            12: "assets/textures/walls/wall_carpet_lower.png",
            13: "assets/textures/walls/wall_carpet_upper.png",
            14: "assets/textures/walls/wall_posters.png",
            15: "assets/textures/walls/wall_bedL_1.png",
            16: "assets/textures/walls/wall_bedR_1.png",

            21: "assets/textures/walls/wall_concrete_01_up.png",
            22: "assets/textures/walls/wall_wires_up.png",
            23: "assets/textures/walls/wall_outside_window.png",
            "floor": "assets/textures/flats/floor_grate.png",
            "floor2": "assets/textures/flats/floor_grate_2.png",
            "floor_outside": "assets/textures/flats/outside-window-floor.png",
            "ceil": "assets/textures/flats/ceiling_panel.png",
            "ceil2": "assets/textures/flats/ceiling_panel-2.png",
            "sky": "assets/textures/flats/sky.png",
        }
        textures = load_textures(texture_paths)

        self._floor_overrides = {
            cell: textures[key]
            for cell, key in self._level.floor_overrides.items()
            if key in textures
        }

        self.hud = Hud(self.app.language)

        level = self._level

        self.renderer = Renderer(
            textures, level.lower_map, level.upper_map, sky_mode=level.sky_mode
        )

        self.player = level.player_start.copy()

        self.focus = config.VIGNETTE
        self.brightness = config.BASE_BRIGHTNESS
        self.rays_intensity = 0.0
        self._is_firing = False

        self.sparks = [Spark() for _ in range(config.SPARK_COUNT)]

        self.exit_door = None
        self.interactables = self._build_interactables()
        self.highlighted = None
        self.interact_pressed = False

        self.props = self._build_props()

        self.traps = self._build_traps()

        self.battery_traps = self._build_battery_traps()

        self.hp = config.PLAYER_MAX_HP
        self._trap_contact_cell = None
        self._trap_contact_ticks = 0
        self._stun_ticks = 0

        self._frame = np.zeros(
            (config.VIRT_WIDTH, config.VIRT_HEIGHT, 3), dtype=np.float32
        )

        self.timer = Timer()
        self.time_ctrl = TimeController(self.timer)

        self.level_number = level.number
        self._time_limit_ticks = round(level.time_limit * config.TICK_RATE)
        self.time_left_ticks = self._time_limit_ticks
        self.completion_time = None

        self.show_debug = False
        self._debug_font = load_font(config.HUD_TEXT_SIZE)

        self._failing = False
        self._fail_left = 0.0

        self._show_level_intro()

    def on_enter(self):
        pg.mouse.get_rel()
        self._start_music()

    def on_exit(self):
        audio.stop_loop()
        audio.stop_music(clear=True)

    def _start_music(self):
        audio.play_music(self._level.music, loop=self._level.music_loop)

    def _win(self):
        self.completion_time = self.timer.seconds
        print(
            "level %d complete in %.2f s" % (self._level.number, self.completion_time),
            flush=True,
        )
        next_index = self.level_index + 1
        if next_index < len(config.LEVELS):

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
        key = "level_%d_msg" % self.level_number
        if has(key, self.app.language):
            self.hud.set_message(key, seconds=config.LEVEL_MSG_SECONDS)

    def _build_interactables(self):
        return self._load_interactables(self._level.interactables)

    def _load_interactables(self, table):
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

        for spec in table:
            if spec.get("kind") == "button":
                if "off" in spec and "on" in spec:
                    states = [
                        InteractState(load_sprite(pref + spec["off"])),
                        InteractState(load_sprite(pref + spec["on"])),
                    ]
                else:
                    states = [InteractState(s) for s in button_states()]
                buttons[spec.get("id")] = Interactable(
                    spec["x"],
                    spec["y"],
                    states,
                    **common(spec),
                )

        for spec in table:
            kind = spec["kind"]
            if kind == "button":
                objs.append(buttons[spec.get("id")])
            elif kind == "door":
                objs.append(
                    Interactable(
                        spec["x"],
                        spec["y"],
                        [
                            InteractState(
                                load_sprite(pref + spec["closed"]), solid=True
                            ),
                            InteractState(
                                load_sprite(pref + spec["open"]), solid=False
                            ),
                        ],
                        **common(spec),
                    )
                )
            elif kind == "locked_door":
                door = Interactable(
                    spec["x"],
                    spec["y"],
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
                    spec["x"],
                    spec["y"],
                    [InteractState(load_sprite(pref + spec["closed"]), solid=True)],
                    interact_radius=config.INTERACT_RADIUS * 0.5,
                    **common(spec),
                )
                self.exit_door = obj
                objs.append(obj)
        return objs

    def _build_props(self):
        return self._load_props(self._level.props)

    def _load_props(self, table):
        props = []
        for entry in table:
            file, w, h, x, y, y_offset, solid, block_radius = entry[:8]
            angle = entry[8] if len(entry) > 8 else 0.0
            billboard = entry[9] if len(entry) > 9 else False
            spr = load_sprite("assets/textures/" + file)
            side = max(w, h)
            props.append(
                Interactable(
                    x,
                    y,
                    [InteractState(spr, solid=solid)],
                    angle=angle,
                    width=side,
                    height=side,
                    y_offset=y_offset,
                    block_radius=block_radius,
                    billboard=billboard,
                )
            )
        return props

    def _build_traps(self):
        return self._load_traps(self._level.traps)

    def _load_traps(self, table):
        tex_on = load_texture("assets/textures/flats/floor_trap_enabled.png")
        tex_off = desaturate(
            tex_on, amount=config.TRAP_OFF_DESATURATE, dim=config.TRAP_OFF_DIM
        )
        return [
            Trap(x, y, tex_on, tex_off, intervals_ms, start_active=active)
            for (x, y, intervals_ms, active) in table
        ]

    def _build_battery_traps(self):
        return self._load_battery_traps(self._level.battery_traps)

    def _load_battery_traps(self, table):
        pref = "assets/textures/sprites/"
        tex_on = load_sprite(pref + "spr_batteryTrap_on.png")
        tex_off = load_sprite(pref + "spr_batteryTrap_off.png")
        return [
            BatteryTrap(x, y, tex_on, tex_off, intervals_ms, start_active=active)
            for (x, y, intervals_ms, active) in table
        ]

    @property
    def _world_objects(self):
        return self.interactables + self.props + self.linked_doors + self.battery_traps

    def _blocked_by_object(self, nx, ny):
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
        return self.time_ctrl.player_running and self._stun_ticks <= 0

    def handle_events(self, events):

        self.interact_pressed = False
        if self._failing:
            return
        for event in events:
            if event.type != pg.KEYDOWN:
                continue
            if event.key == pg.K_ESCAPE:
                from .pause import PauseScene

                audio.stop_loop()
                self.app.push_scene(PauseScene(self.app))
            elif event.key == pg.K_e:
                self.interact_pressed = True
            elif event.key == pg.K_l:
                self.app.set_language("ru" if self.app.language == "en" else "en")
                self.hud.set_language(self.app.language)
            elif event.key == pg.K_f and self.player_can_act:

                self.time_ctrl.toggle_freeze()
            elif event.key == pg.K_F3:
                self.show_debug = not self.show_debug
            elif event.key == pg.K_F10:
                self._win()

    def _update_input(self, dt):
        is_firing = pg.mouse.get_pressed()[0]
        target_focus = 280.0 if is_firing else config.VIGNETTE
        target_bright = 15.0 if is_firing else config.BASE_BRIGHTNESS
        target_rays = 1.0 if is_firing else 0.0

        self.focus += (target_focus - self.focus) * 0.1
        self.brightness += (target_bright - self.brightness) * 0.1
        self.rays_intensity += (target_rays - self.rays_intensity) * 0.1

        rel_x, _ = pg.mouse.get_rel()
        if self.player_can_act:
            self.player["angle"] += rel_x * config.MOUSE_SENSITIVITY

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

        if not self.player_can_act:
            dx = dy = 0.0

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

        if self._failing:
            self._fail_left -= dt
            self.hud.update(dt, player_frozen=False)
            self.hud.damage_flash = 1.0
            audio.stop_loop()
            if self._fail_left <= 0.0:
                self.reset_level()
            return

        is_firing = self._update_input(dt)

        for _ in range(self.timer.update(dt)):
            if self._stun_ticks > 0:
                self._stun_ticks -= 1
            self.time_ctrl.step()
            if self.time_ctrl.world_running:
                self.world_step()

            self._apply_trap_damage()
            if self._failing:
                break

        self._play_time_events()

        self.hud.update(dt, player_frozen=not self.time_ctrl.player_running)
        self.update_interaction()
        self._update_buzz()
        self._is_firing = is_firing

    _TIME_EVENT_SOUND = {
        "world_freeze": "freeze",
        "player_freeze": "freeze",
        "world_unfreeze": "unfreeze",
        "player_unfreeze": "unfreeze",
    }

    def _play_time_events(self):
        for ev in self.time_ctrl.drain_events():
            sound = self._TIME_EVENT_SOUND.get(ev)
            if sound is not None:
                audio.play(sound)

    def _update_buzz(self):
        if config.BUZZ_MAX_DIST <= 0.0:
            audio.stop_loop()
            return
        px, py = self.player["x"], self.player["y"]
        nearest = None
        for trap in self.battery_traps:
            if not trap.active:
                continue
            dist = math.hypot(trap.x - px, trap.y - py)
            if nearest is None or dist < nearest:
                nearest = dist
        if nearest is None:
            audio.loop("buzz", 0.0)
            return
        volume = max(0.0, 1.0 - nearest / config.BUZZ_MAX_DIST)
        audio.loop("buzz", volume)

    def update_particles(self, is_firing, hit_info):

        if is_firing and hit_info and hit_info[2] < 6:
            if random.random() > 0.4:
                for spark in self.sparks:
                    if not spark.is_active():
                        spark.spawn(hit_info[0], hit_info[1], self.player["angle"])
                        break

        for spark in self.sparks:
            if spark.update():
                dx_s = spark.x - self.player["x"]
                dy_s = spark.y - self.player["y"]
                dist_s = dx_s * np.cos(self.player["angle"]) + dy_s * np.sin(
                    self.player["angle"]
                )

                if dist_s > 0.1:

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

        frame = self._frame
        frame.fill(0.0)
        self.renderer.begin_frame()

        floor_tiles = dict(self._floor_overrides)
        floor_tiles.update({trap.cell: trap.texture for trap in self.traps})
        self.renderer.render_floor_ceiling(
            frame,
            self.player["x"],
            self.player["y"],
            self.player["angle"],
            floor_tiles=floor_tiles,
        )

        hit_info = self.renderer.render_walls(
            frame, self.player["x"], self.player["y"], self.player["angle"]
        )

        self.renderer.render_sprites(
            frame,
            self.player["x"],
            self.player["y"],
            self.player["angle"],
            self._world_objects,
            self.highlighted,
        )

        final = self.renderer.apply_post_processing(
            frame, focus=self.focus, brightness=self.brightness, saturation_mult=1.0
        )
        pg.surfarray.blit_array(self.virt_surf, final)

        self.renderer.draw_god_rays(self.rays_surf, self.rays_intensity)
        self.virt_surf.blit(self.rays_surf, (0, 0))

        if self.app.scene is self:
            self.update_particles(self._is_firing, hit_info)

        screen.blit(
            pg.transform.scale(self.virt_surf, (config.WIN_WIDTH, config.WIN_HEIGHT)),
            (0, 0),
        )

        self.hud.draw(
            screen,
            time_left=self.time_left_ticks / config.TICK_RATE,
            hp=self.hp,
            max_hp=config.PLAYER_MAX_HP,
            level_number=self.level_number,
            world_frozen=not self.time_ctrl.world_running,
            budget_fraction=self.time_ctrl.budget_fraction,
        )

        if self.show_debug:
            self._draw_debug(screen)

    def _draw_debug(self, screen):
        x = self.player["x"]
        y = self.player["y"]
        angle = self.player["angle"]
        line1 = "x=%.2f  y=%.2f  angle=%.3f" % (x, y, angle)
        line2 = "cell row=%d col=%d   deg=%.1f" % (
            int(y),
            int(x),
            float(np.degrees(angle)),
        )
        m = config.HUD_MARGIN
        lh = self._debug_font.get_height() + 2
        for i, text in enumerate((line1, line2)):
            shadow = self._debug_font.render(text, True, config.HUD_SHADOW_COLOR)
            label = self._debug_font.render(text, True, config.HUD_COLOR)
            screen.blit(shadow, (m + 1, m + i * lh + 1))
            screen.blit(label, (m, m + i * lh))

    def update_interaction(self):

        for link in self.button_links:
            link.sync()

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

            self.interact_pressed = False
            if self.highlighted is self.exit_door:
                self._win()
            elif self.highlighted in self.linked_doors:

                self.highlighted.state = 2 if self.highlighted.state == 1 else 1
            else:
                self.highlighted.use()

    def world_step(self):

        self.time_left_ticks -= 1
        if self.time_left_ticks <= 0:
            self.time_left_ticks = 0
            print("time is up - fail pause", flush=True)
            self.hud.set_message("time_up", seconds=config.FAIL_PAUSE_SECONDS)
            self._begin_fail()
            return
        for trap in self.traps:
            trap.step()
        for trap in self.battery_traps:
            trap.step()

    def _active_trap_at(self, cell):
        for trap in self.traps:
            if trap.active and trap.cell == cell:
                return trap
        for trap in self.battery_traps:
            if trap.active and trap.cell == cell:
                return trap
        return None

    def _apply_trap_damage(self):
        cell = (int(self.player["y"]), int(self.player["x"]))
        if self._active_trap_at(cell) is None:

            self._trap_contact_cell = None
            self._trap_contact_ticks = 0
            return
        if self._trap_contact_cell != cell:

            self._trap_contact_cell = cell
            self._trap_contact_ticks = 0
            self._damage(1)
        else:
            self._trap_contact_ticks += 1
            if self._trap_contact_ticks >= config.TRAP_DAMAGE_PERIOD:
                self._trap_contact_ticks -= config.TRAP_DAMAGE_PERIOD
                self._damage(1)

    def _damage(self, amount):
        self.hp -= amount

        self._stun_ticks = config.PLAYER_STUN_TICKS

        self.hud.flash_damage()
        audio.play("hurt")
        print("player hit by trap, hp=%d" % self.hp, flush=True)
        if self.hp <= 0:
            print("player died - fail pause", flush=True)
            self._begin_fail()

    def _begin_fail(self):
        if self._failing:
            return
        self._failing = True
        self._fail_left = config.FAIL_PAUSE_SECONDS
        self.hud.flash_damage()
        audio.stop_music()
        audio.play("death")

    def reset_level(self):
        level = self._level
        self._failing = False
        self._fail_left = 0.0
        self.player = level.player_start.copy()
        self.hp = config.PLAYER_MAX_HP
        self._trap_contact_cell = None
        self._trap_contact_ticks = 0
        self._stun_ticks = 0
        for trap in self.traps:
            trap.reset()
        for trap in self.battery_traps:
            trap.reset()
        for obj in self.interactables:
            obj.state = 0
        for door in self.linked_doors:
            door.state = 0
        self.highlighted = None
        self.interact_pressed = False

        self.timer = Timer()
        self.time_ctrl = TimeController(self.timer)

        self.time_left_ticks = self._time_limit_ticks
        self.hud.reset()

        self._start_music()

def run_engine():

    from .splash import SplashScene

    app = App()
    app.push_scene(SplashScene(app))
    audio.play("intro")
    app.run()
