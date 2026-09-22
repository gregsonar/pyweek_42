# src/renderer.py
"""Логика рендеринга: геометрия, пост-обработка, эффекты."""

import numpy as np
import pygame as pg
import math
import random
from . import config
from .utils import clamp


class Renderer:
    """Основной класс рендерера."""

    def __init__(self, textures, game_map, upper_map=None):
        self.textures = textures
        self.map = np.array(game_map, dtype=int)
        self.map_h, self.map_w = self.map.shape
        # Верхний пояс стен (z 1..2). Если не задан - совпадает с нижним.
        if upper_map is not None:
            self.upper_map = np.array(upper_map, dtype=int)
        else:
            self.upper_map = self.map.copy()

        # Буферы
        self.z_buffer = np.full((config.VIRT_WIDTH, config.VIRT_HEIGHT),
                                99.0, dtype=np.float32)

        # God rays параметры
        self._init_god_rays()

    def _init_god_rays(self):
        """Инициализация параметров лучей."""
        self.ray_angles = [random.uniform(0, math.pi * 2)
                           for _ in range(config.GOD_RAY_COUNT)]
        self.ray_phases = [random.uniform(0, math.pi * 2)
                           for _ in range(config.GOD_RAY_COUNT)]
        self.ray_mults = [random.uniform(0.5, 1.0)
                          for _ in range(config.GOD_RAY_COUNT)]

    def begin_frame(self):
        """Сброс z-буфера перед рендерингом нового кадра."""
        self.z_buffer.fill(99.0)

    def render_floor_ceiling(self, frame, px, py, pa):
        """
        Отрисовка пола и потолка методом проекции.

        Глаз на высоте EYE_HEIGHT над полом, потолок на CEILING_HEIGHT. Так как
        глаз не в центре, пол и потолок несимметричны и считаются раздельно:
        пол - на глубину eye/(y-горизонт), потолок - (CEILING-eye)/(горизонт-y).
        """
        rx0 = math.cos(pa - config.FOV)
        ry0 = math.sin(pa - config.FOV)
        rx1 = math.cos(pa + config.FOV)
        ry1 = math.sin(pa + config.FOV)

        H = config.VIRT_HEIGHT
        mid = H // 2
        xs = np.linspace(0, 1, config.VIRT_WIDTH)
        eye = config.EYE_HEIGHT
        ceil_gap = config.CEILING_HEIGHT - eye  # высота потолка над глазом

        def sample(dist):
            cx = px + dist * (rx0 + xs * (rx1 - rx0))
            cy = py + dist * (ry0 + xs * (ry1 - ry0))
            tx = (cx * 63).astype(int) % config.TEX_SIZE
            ty = (cy * 63).astype(int) % config.TEX_SIZE
            return tx, ty

        # Пол (ниже горизонта)
        for y in range(mid, H):
            dist = (eye * H) / (y - mid + 0.0001)
            tx, ty = sample(dist)
            frame[:, y] = self.textures['floor'][tx, ty]
            self.z_buffer[:, y] = dist

        # Потолок (выше горизонта)
        for y in range(0, mid):
            dist = (ceil_gap * H) / (mid - y)
            tx, ty = sample(dist)
            frame[:, y] = self.textures['ceil'][tx, ty]
            self.z_buffer[:, y] = dist

    def cast_ray_dda(self, px, py, ray_angle, player_angle):
        """
        DDA-алгоритм трассировки луча.
        :return: (hit_x, hit_y, distance, raw_distance, side) или None
                 при выходе за границы. distance скорректировано от
                 "рыбьего глаза" (для высоты стен и z-буфера),
                 raw_distance — истинное расстояние вдоль луча
                 (для вычисления точки попадания).
        """
        rdx, rdy = math.cos(ray_angle), math.sin(ray_angle)
        mx, my = int(px), int(py)

        # Дельты для DDA
        ddx = abs(1 / rdx) if rdx != 0 else 1e30
        ddy = abs(1 / rdy) if rdy != 0 else 1e30

        # Направление шага и начальное расстояние до следующей границы
        sx, step_x = (-1, (px - mx) * ddx) if rdx < 0 else (1, (mx + 1 - px) * ddx)
        sy, step_y = (-1, (py - my) * ddy) if rdy < 0 else (1, (my + 1 - py) * ddy)

        side = 0  # 0 = вертикальная стена, 1 = горизонтальная
        while True:
            if step_x < step_y:
                step_x += ddx
                mx += sx
                side = 0
            else:
                step_y += ddy
                my += sy
                side = 1

            # Выход за границы карты
            if not (0 <= my < self.map_h and 0 <= mx < self.map_w):
                return None

            # Попадание в стену
            if self.map[my, mx] > 0:
                raw_dist = step_x - ddx if side == 0 else step_y - ddy
                # Коррекция "рыбьего глаза"
                dist = raw_dist * math.cos(ray_angle - player_angle)
                return mx, my, dist, raw_dist, side

    def _draw_wall_band(self, frame, x, top_ideal, bot_ideal, texture, tx, dist):
        """
        Рисует один вертикальный пояс стены (тайл 64x64) в столбце x между
        экранными координатами top_ideal..bot_ideal (float, могут выходить за
        экран) с попиксельной выборкой текстуры и записью в z-буфер.
        """
        if texture is None:
            return
        band = bot_ideal - top_ideal
        if band <= 0:
            return
        y0 = max(0, int(math.floor(top_ideal)))
        y1 = min(config.VIRT_HEIGHT, int(math.ceil(bot_ideal)))
        if y1 <= y0:
            return
        rows = np.arange(y0, y1)
        v = np.clip(((rows - top_ideal) / band * config.TEX_SIZE).astype(int),
                    0, config.TEX_SIZE - 1)
        frame[x, y0:y1] = texture[tx % config.TEX_SIZE, v]
        self.z_buffer[x, y0:y1] = dist

    def _march_column(self, px, py, ray_angle, player_angle):
        """
        Проход лучом по клеткам карты для одного столбца.

        Возвращает список сегментов от ближних к дальним. Сегмент:
        {perp, raw, tx, full, upper_id, perp_far, [lower_id]}.
        full=True - сплошная клетка (нижний пояс > 0): рисуется на всю высоту и
        останавливает луч. full=False - только верхний пояс (перемычка/висящий
        блок над проходом): рисуется как блок z 1..2 глубиной до perp_far, луч
        идёт дальше - поэтому дальняя стена сверху остаётся видна ниже блока.
        """
        rdx, rdy = math.cos(ray_angle), math.sin(ray_angle)
        mx, my = int(px), int(py)
        ddx = abs(1 / rdx) if rdx != 0 else 1e30
        ddy = abs(1 / rdy) if rdy != 0 else 1e30
        sx, step_x = (-1, (px - mx) * ddx) if rdx < 0 else (1, (mx + 1 - px) * ddx)
        sy, step_y = (-1, (py - my) * ddy) if rdy < 0 else (1, (my + 1 - py) * ddy)
        cos_corr = math.cos(ray_angle - player_angle)

        segments = []
        pending = None  # сегмент-блок, которому ещё нужна дистанция выхода
        while True:
            if step_x < step_y:
                raw = step_x
                step_x += ddx
                mx += sx
                side = 0
            else:
                raw = step_y
                step_y += ddy
                my += sy
                side = 1

            if not (0 <= my < self.map_h and 0 <= mx < self.map_w):
                break

            # Текущая граница = выход из предыдущей клетки-блока
            if pending is not None:
                pending["perp_far"] = raw * cos_corr
                pending = None

            lower = int(self.map[my, mx])
            upper = int(self.upper_map[my, mx])
            if lower <= 0 and upper <= 0:
                continue  # полностью открытая клетка - луч идёт дальше

            perp = raw * cos_corr  # перпендикулярная дистанция (как в z-буфере)
            if side == 0:
                wall_hit = py + raw * rdy
            else:
                wall_hit = px + raw * rdx
            tx = int((wall_hit % 1) * config.TEX_SIZE)

            if lower > 0:  # сплошная стена на всю высоту - останавливает луч
                segments.append({
                    "perp": perp, "raw": raw, "tx": tx, "full": True,
                    "lower_id": lower, "upper_id": upper if upper > 0 else lower,
                    "perp_far": perp,
                })
                break

            # только верхний пояс (перемычка/висящий блок) - луч идёт дальше
            seg = {"perp": perp, "raw": raw, "tx": tx, "full": False,
                   "upper_id": upper, "perp_far": perp}
            segments.append(seg)
            pending = seg

        return segments

    def render_walls(self, frame, px, py, pa):
        """
        Отрисовка стен рейкастингом в два пояса по высоте.

        Для каждого столбца _march_column собирает сегменты (перемычки/блоки
        верхнего пояса + завершающая сплошная стена). Сегменты рисуются от
        дальних к ближним (алгоритм художника): сплошная стена - оба пояса;
        перемычка/блок - верхний пояс как блок z 1..2 глубиной до perp_far
        (передняя грань + низ), поэтому снизу он не просвечивает, а дальняя
        стена сверху остаётся видна ниже блока. Экранная координата мировой
        высоты z: mid + (EYE_HEIGHT - z) * L, где L - пикселей на юнит.
        """
        mid = config.VIRT_HEIGHT // 2
        eye = config.EYE_HEIGHT
        hit_info = None

        for x in range(config.VIRT_WIDTH):
            ray_angle = pa - config.FOV + (x / config.VIRT_WIDTH) * 2 * config.FOV
            rdx, rdy = math.cos(ray_angle), math.sin(ray_angle)
            segments = self._march_column(px, py, ray_angle, pa)

            for seg in reversed(segments):  # дальние -> ближние
                d = seg["perp"]
                unit = config.VIRT_HEIGHT / (d + 0.0001)
                y_floor = mid + (eye - 0.0) * unit
                y_seam = mid + (eye - 1.0) * unit
                y_ceil = mid + (eye - 2.0) * unit
                upper_tex = self.textures.get(seg["upper_id"])

                # верхний пояс (z 1..2), передняя грань на ближней дистанции
                self._draw_wall_band(frame, x, y_ceil, y_seam, upper_tex,
                                     seg["tx"], d)

                if seg["full"]:
                    # нижний пояс (z 0..1)
                    self._draw_wall_band(frame, x, y_seam, y_floor,
                                         self.textures.get(seg["lower_id"]),
                                         seg["tx"], d)
                else:
                    # низ блока: до z=1 у дальней грани клетки (не просвечивает).
                    # Рисуется текстурой потолка - низ блока это "потолок" прохода
                    d_far = seg["perp_far"]
                    if d_far > d:
                        unit_far = config.VIRT_HEIGHT / (d_far + 0.0001)
                        y_seam_far = mid + (eye - 1.0) * unit_far
                        self._draw_wall_band(frame, x, y_seam, y_seam_far,
                                             self.textures.get('ceil'),
                                             seg["tx"], d_far)

            # Точка попадания в центр экрана (для искр) - ближайшая сплошная стена
            if x == config.VIRT_WIDTH // 2 and segments and segments[-1]["full"]:
                seg = segments[-1]
                hit_info = (px + seg["raw"] * rdx, py + seg["raw"] * rdy,
                            seg["perp"])

        return hit_info

    def render_sprites(self, frame, px, py, pa, objects, highlighted=None):
        """
        Отрисовка интерактивных объектов как плоских ориентированных
        поверхностей (не билбордов), неподвижных в пространстве.

        Для каждого экранного столбца луч (тот же, что у стен) пересекается
        с отрезком объекта - это даёт корректную перспективу и перекрытие
        через общий z-буфер. Вызывается между стенами и пост-обработкой,
        чтобы объекты попадали под те же эффекты, что и мир. Отрисованные
        пиксели пишутся в z-буфер, поэтому объекты и частицы за ними
        корректно отсекаются (в т. ч. один объект за другим).
        """
        mid = config.VIRT_HEIGHT // 2

        # Лучи столбцов (совпадают с рейкастингом стен), считаются один раз
        cols = np.arange(config.VIRT_WIDTH)
        ray_ang = pa - config.FOV + (cols / config.VIRT_WIDTH) * 2 * config.FOV
        rdx = np.cos(ray_ang)
        rdy = np.sin(ray_ang)
        cos_corr = np.cos(ray_ang - pa)  # поправка "рыбьего глаза"

        for obj in objects:
            is_high = obj is highlighted
            if is_high and obj.highlight_sprite is not None:
                sprite = obj.highlight_sprite
                mult = 1.0
            else:
                sprite = obj.sprite
                mult = config.HIGHLIGHT_BRIGHTNESS if is_high else 1.0
            tex_w, tex_h = sprite.shape[0], sprite.shape[1]

            # Концы отрезка поверхности в мировых координатах
            half = obj.width / 2.0
            tx, ty = math.cos(obj.angle), math.sin(obj.angle)
            ax, ay = obj.x - half * tx, obj.y - half * ty  # точка A
            ex, ey = obj.width * tx, obj.width * ty          # вектор A->B

            # Пересечение луча (P + t*R) с отрезком (A + s*E) сразу для всех столбцов
            apx, apy = ax - px, ay - py
            det = ex * rdy - ey * rdx
            safe = np.abs(det) > 1e-9
            det_safe = np.where(safe, det, 1.0)
            t = (-apx * ey + ex * apy) / det_safe          # дистанция вдоль луча
            s = (rdx * apy - rdy * apx) / det_safe          # параметр вдоль отрезка
            hit = safe & (t > 0) & (s >= 0.0) & (s <= 1.0)

            perp_all = t * cos_corr  # перпендикулярная дистанция (как в z-буфере)
            hit &= perp_all > config.SPRITE_NEAR_CLIP

            for col in np.nonzero(hit)[0]:
                perp = perp_all[col]
                scale = config.VIRT_HEIGHT / perp
                pixel_h = obj.height * scale
                base_y = mid + (config.EYE_HEIGHT - obj.y_offset) * scale
                top = base_y - pixel_h

                y0 = max(0, int(math.floor(top)))
                y1 = min(config.VIRT_HEIGHT, int(math.ceil(base_y)))
                if y1 <= y0:
                    continue

                u = min(tex_w - 1, max(0, int(s[col] * tex_w)))
                rows = np.arange(y0, y1)
                v_idx = np.clip(((rows - top) / pixel_h * tex_h).astype(int),
                                0, tex_h - 1)
                texel = sprite[u, v_idx]  # (bh, 4)

                z_col = self.z_buffer[col, y0:y1]
                alpha = texel[:, 3] / 255.0
                # рисуем там, где есть непрозрачность и объект ближе стены
                vis = (alpha > 0.03) & (perp < z_col)
                if not vis.any():
                    continue

                rgb = texel[:, :3].astype(np.float32)
                if mult != 1.0:
                    rgb = np.clip(rgb * mult, 0, 255)

                # Альфа-смешивание с уже отрисованным фоном (полупрозрачность)
                frame_col = frame[col, y0:y1, :]
                a = alpha[vis][:, np.newaxis]
                frame_col[vis] = rgb[vis] * a + frame_col[vis] * (1.0 - a)

                # В z-буфер пишем только достаточно непрозрачные пиксели, чтобы
                # полупрозрачные (свечение) не перекрывали глубину за собой
                opaque = vis & (alpha > 0.5)
                z_col[opaque] = perp

    def apply_post_processing(self, frame, focus, brightness, saturation_mult):
        """
        Пост-обработка: виньетка, глубина резкости, насыщенность.
        :return: frame как uint8 для отрисовки
        """
        # Координатные сетки
        xs = np.linspace(-0.5, 0.5, config.VIRT_WIDTH)
        ys = np.linspace(-0.5, 0.5, config.VIRT_HEIGHT)
        xm, ym = np.meshgrid(xs, ys, indexing='ij')

        # Виньетка + затенение по глубине
        radial = np.exp(-focus * (xm ** 2 + ym ** 2))
        depth_mask = np.exp(-config.DEPTH_FALLOFF * self.z_buffer)
        light_mask = radial * depth_mask * brightness

        # Насыщенность: центр — цветной, края — ч/б
        gray = np.stack([np.dot(frame, [0.299, 0.587, 0.114])] * 3, axis=-1)
        sat_map = np.clip(
            np.exp(-(focus / 15.0) * (xm ** 2 + ym ** 2)) +
            (1.0 - (focus - 12) / 250.0),
            0, 1
        )[..., np.newaxis]

        # Финальная композиция
        blended = frame * sat_map + gray * (1 - sat_map)
        result = (blended * (light_mask[..., np.newaxis] + config.AMBIENT_FLOOR)).clip(0, 255)

        return result.astype(np.uint8)

    def draw_god_rays(self, surface, rays_intensity, center=None):
        """Отрисовка процедурных god rays на поверхности с альфа-каналом."""
        if rays_intensity < 0.05:
            # Когда интенсивность падает, поверхность всё равно нужно очищать
            surface.fill((0, 0, 0, 0))
            return

        # ВАЖНО: очищаем слой каждый кадр, иначе лучи остаются навсегда
        surface.fill((0, 0, 0, 0))

        if center is None:
            center = (config.VIRT_WIDTH // 2, config.VIRT_HEIGHT // 2)
        cx, cy = center

        t = pg.time.get_ticks() * 0.005
        for i in range(config.GOD_RAY_COUNT):
            length = (5 + math.sin(t + self.ray_phases[i]) * 30) * self.ray_mults[i] * rays_intensity
            ex = cx + math.cos(self.ray_angles[i]) * length
            ey = cy + math.sin(self.ray_angles[i]) * length
            alpha = int(35 * rays_intensity)
            pg.draw.line(surface, (255, 210, 160, alpha),
                         (cx, cy), (int(ex), int(ey)), 1)