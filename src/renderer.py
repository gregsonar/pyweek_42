import numpy as np
import pygame as pg
import math
import random
from . import config
from .utils import clamp

class Renderer:

    def __init__(self, textures, game_map, upper_map=None, sky_mode=False):
        self.textures = textures
        self.map = np.array(game_map, dtype=int)
        self.map_h, self.map_w = self.map.shape
        self.sky_mode = sky_mode

        if upper_map is not None:
            self.upper_map = np.array(upper_map, dtype=int)
        else:
            self.upper_map = self.map.copy()

        self._floor_texes = [
            self.textures['floor'],
            self.textures.get('floor2', self.textures['floor']),
        ]
        self._ceil_texes = [
            self.textures['ceil'],
            self.textures.get('ceil2', self.textures['ceil']),
        ]
        self._floor_variant = self._build_variant_map(config.FLOOR_VARIANT_SECOND)
        self._ceil_variant = self._build_variant_map(config.CEIL_VARIANT_SECOND)

        self.z_buffer = np.full((config.VIRT_WIDTH, config.VIRT_HEIGHT),
                                99.0, dtype=np.float32)

        _xs = np.linspace(-0.5, 0.5, config.VIRT_WIDTH)
        _ys = np.linspace(-0.5, 0.5, config.VIRT_HEIGHT)
        xm, ym = np.meshgrid(_xs, _ys, indexing='ij')
        self._r2 = (xm ** 2 + ym ** 2).astype(np.float32)

        self._init_god_rays()

    def _init_god_rays(self):
        self.ray_angles = [random.uniform(0, math.pi * 2)
                           for _ in range(config.GOD_RAY_COUNT)]
        self.ray_phases = [random.uniform(0, math.pi * 2)
                           for _ in range(config.GOD_RAY_COUNT)]
        self.ray_mults = [random.uniform(0.5, 1.0)
                          for _ in range(config.GOD_RAY_COUNT)]

    def _build_variant_map(self, second_share):
        rnd = np.random.random((self.map_h, self.map_w))
        return (rnd < second_share).astype(np.int8)

    def begin_frame(self):
        self.z_buffer.fill(99.0)

    def render_floor_ceiling(self, frame, px, py, pa, floor_tiles=None):
        H = config.VIRT_HEIGHT
        mid = H // 2
        eye = config.EYE_HEIGHT
        ceil_gap = config.CEILING_HEIGHT - eye
        tex_n = config.TEX_SIZE
        mh, mw = self.map_h, self.map_w

        xs = np.arange(config.VIRT_WIDTH) / config.VIRT_WIDTH
        theta = pa - config.FOV + xs * (2.0 * config.FOV)
        dirx = np.cos(theta)
        diry = np.sin(theta)
        inv_cos = 1.0 / np.cos(theta - pa)

        floor_a, floor_b = self._floor_texes
        floor_variant = self._floor_variant
        for y in range(mid, H):
            perp = (eye * H) / (y - mid + 0.0001)
            r = perp * inv_cos
            cx = px + r * dirx
            cy = py + r * diry
            ix = cx.astype(int)
            iy = cy.astype(int)
            tx = np.clip(((cx - ix) * tex_n).astype(int), 0, tex_n - 1)
            ty = np.clip(((cy - iy) * tex_n).astype(int), 0, tex_n - 1)

            sel = floor_variant[np.clip(iy, 0, mh - 1), np.clip(ix, 0, mw - 1)]
            frame[:, y] = np.where(
                sel[:, None].astype(bool), floor_b[tx, ty], floor_a[tx, ty]
            )
            self.z_buffer[:, y] = perp

            if floor_tiles:
                for (cell_r, cell_c), tile_tex in floor_tiles.items():
                    mask = (iy == cell_r) & (ix == cell_c)
                    if mask.any():
                        frame[mask, y] = tile_tex[tx[mask], ty[mask]]

        if self.sky_mode and 'sky' in self.textures:
            self._render_sky(frame, pa)
        else:

            ceil_a, ceil_b = self._ceil_texes
            ceil_variant = self._ceil_variant
            for y in range(0, mid):
                perp = (ceil_gap * H) / (mid - y + 0.0001)
                r = perp * inv_cos
                cx = px + r * dirx
                cy = py + r * diry
                tx = (cx * 63).astype(int) % tex_n
                ty = (cy * 63).astype(int) % tex_n
                sel = ceil_variant[
                    np.clip(cy.astype(int), 0, mh - 1),
                    np.clip(cx.astype(int), 0, mw - 1),
                ]
                frame[:, y] = np.where(
                    sel[:, None].astype(bool), ceil_b[tx, ty], ceil_a[tx, ty]
                )
                self.z_buffer[:, y] = perp

    def _render_sky(self, frame, pa):
        sky = self.textures['sky']
        tw, th = sky.shape[0], sky.shape[1]
        H = config.VIRT_HEIGHT
        mid = H // 2

        cols = np.arange(config.VIRT_WIDTH)
        ray_ang = pa - config.FOV + (cols / config.VIRT_WIDTH) * 2 * config.FOV

        frac = (ray_ang / (2 * math.pi) * config.SKY_TILES) % 1.0
        su = (frac * tw).astype(int) % tw

        for y in range(0, mid):
            sv = int((y / mid) * th) % th
            frame[:, y] = sky[su, sv]
            self.z_buffer[:, y] = 99.0

    def cast_ray_dda(self, px, py, ray_angle, player_angle):
        rdx, rdy = math.cos(ray_angle), math.sin(ray_angle)
        mx, my = int(px), int(py)

        ddx = abs(1 / rdx) if rdx != 0 else 1e30
        ddy = abs(1 / rdy) if rdy != 0 else 1e30

        sx, step_x = (-1, (px - mx) * ddx) if rdx < 0 else (1, (mx + 1 - px) * ddx)
        sy, step_y = (-1, (py - my) * ddy) if rdy < 0 else (1, (my + 1 - py) * ddy)

        side = 0
        while True:
            if step_x < step_y:
                step_x += ddx
                mx += sx
                side = 0
            else:
                step_y += ddy
                my += sy
                side = 1

            if not (0 <= my < self.map_h and 0 <= mx < self.map_w):
                return None

            if self.map[my, mx] > 0:
                raw_dist = step_x - ddx if side == 0 else step_y - ddy

                dist = raw_dist * math.cos(ray_angle - player_angle)
                return mx, my, dist, raw_dist, side

    def _draw_wall_band(self, frame, x, top_ideal, bot_ideal, texture, tx, dist):
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
        rdx, rdy = math.cos(ray_angle), math.sin(ray_angle)
        mx, my = int(px), int(py)
        ddx = abs(1 / rdx) if rdx != 0 else 1e30
        ddy = abs(1 / rdy) if rdy != 0 else 1e30
        sx, step_x = (-1, (px - mx) * ddx) if rdx < 0 else (1, (mx + 1 - px) * ddx)
        sy, step_y = (-1, (py - my) * ddy) if rdy < 0 else (1, (my + 1 - py) * ddy)
        cos_corr = math.cos(ray_angle - player_angle)

        segments = []
        pending = None
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

            if pending is not None:
                pending["perp_far"] = raw * cos_corr
                pending = None

            lower = int(self.map[my, mx])
            upper = int(self.upper_map[my, mx])
            if lower <= 0 and upper <= 0:
                continue

            perp = raw * cos_corr
            if side == 0:
                wall_hit = py + raw * rdy
            else:
                wall_hit = px + raw * rdx
            tx = int((wall_hit % 1) * config.TEX_SIZE)

            if lower > 0:
                segments.append({
                    "perp": perp, "raw": raw, "tx": tx, "full": True,
                    "lower_id": lower, "upper_id": upper if upper > 0 else lower,
                    "perp_far": perp,
                })
                break

            seg = {"perp": perp, "raw": raw, "tx": tx, "full": False,
                   "upper_id": upper, "perp_far": perp}
            segments.append(seg)
            pending = seg

        return segments

    def render_walls(self, frame, px, py, pa):
        mid = config.VIRT_HEIGHT // 2
        eye = config.EYE_HEIGHT
        hit_info = None

        for x in range(config.VIRT_WIDTH):
            ray_angle = pa - config.FOV + (x / config.VIRT_WIDTH) * 2 * config.FOV
            rdx, rdy = math.cos(ray_angle), math.sin(ray_angle)
            segments = self._march_column(px, py, ray_angle, pa)

            for seg in reversed(segments):
                d = seg["perp"]
                unit = config.VIRT_HEIGHT / (d + 0.0001)
                y_floor = mid + (eye - 0.0) * unit
                y_seam = mid + (eye - 1.0) * unit
                y_ceil = mid + (eye - 2.0) * unit
                upper_tex = self.textures.get(seg["upper_id"])

                self._draw_wall_band(frame, x, y_ceil, y_seam, upper_tex,
                                     seg["tx"], d)

                if seg["full"]:

                    self._draw_wall_band(frame, x, y_seam, y_floor,
                                         self.textures.get(seg["lower_id"]),
                                         seg["tx"], d)
                else:

                    d_far = seg["perp_far"]
                    if d_far > d:
                        unit_far = config.VIRT_HEIGHT / (d_far + 0.0001)
                        y_seam_far = mid + (eye - 1.0) * unit_far
                        self._draw_wall_band(frame, x, y_seam, y_seam_far,
                                             self.textures.get('ceil'),
                                             seg["tx"], d_far)

            if x == config.VIRT_WIDTH // 2 and segments and segments[-1]["full"]:
                seg = segments[-1]
                hit_info = (px + seg["raw"] * rdx, py + seg["raw"] * rdy,
                            seg["perp"])

        return hit_info

    def render_sprites(self, frame, px, py, pa, objects, highlighted=None):
        mid = config.VIRT_HEIGHT // 2

        cols = np.arange(config.VIRT_WIDTH)
        ray_ang = pa - config.FOV + (cols / config.VIRT_WIDTH) * 2 * config.FOV
        rdx = np.cos(ray_ang)
        rdy = np.sin(ray_ang)
        cos_corr = np.cos(ray_ang - pa)

        for obj in objects:
            is_high = obj is highlighted
            if is_high and obj.highlight_sprite is not None:
                sprite = obj.highlight_sprite
                mult = 1.0
            else:
                sprite = obj.sprite
                mult = config.HIGHLIGHT_BRIGHTNESS if is_high else 1.0
            tex_w, tex_h = sprite.shape[0], sprite.shape[1]

            half = obj.width / 2.0
            if getattr(obj, "billboard", False):
                tx, ty = -math.sin(pa), math.cos(pa)
            else:
                tx, ty = math.cos(obj.angle), math.sin(obj.angle)
            ax, ay = obj.x - half * tx, obj.y - half * ty
            ex, ey = obj.width * tx, obj.width * ty

            apx, apy = ax - px, ay - py
            det = ex * rdy - ey * rdx
            safe = np.abs(det) > 1e-9
            det_safe = np.where(safe, det, 1.0)
            t = (-apx * ey + ex * apy) / det_safe
            s = (rdx * apy - rdy * apx) / det_safe
            hit = safe & (t > 0) & (s >= 0.0) & (s <= 1.0)

            perp_all = t * cos_corr
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
                texel = sprite[u, v_idx]

                z_col = self.z_buffer[col, y0:y1]
                alpha = texel[:, 3] / 255.0

                vis = (alpha > 0.03) & (perp < z_col)
                if not vis.any():
                    continue

                rgb = texel[:, :3].astype(np.float32)
                if mult != 1.0:
                    rgb = np.clip(rgb * mult, 0, 255)

                frame_col = frame[col, y0:y1, :]
                a = alpha[vis][:, np.newaxis]
                frame_col[vis] = rgb[vis] * a + frame_col[vis] * (1.0 - a)

                opaque = vis & (alpha > 0.5)
                z_col[opaque] = perp

    def apply_post_processing(self, frame, focus, brightness, saturation_mult):

        r2 = self._r2

        radial = np.exp(-focus * r2)
        depth_mask = np.exp(-config.DEPTH_FALLOFF * self.z_buffer)
        light_mask = radial * depth_mask * brightness

        sat_map = np.clip(
            np.exp(-(focus / 15.0) * r2) + (1.0 - (focus - 12) / 250.0),
            0, 1
        )[..., np.newaxis]

        if sat_map.min() >= 0.999:
            blended = frame
        else:
            gray = np.stack([np.dot(frame, [0.299, 0.587, 0.114])] * 3, axis=-1)
            blended = frame * sat_map + gray * (1 - sat_map)

        result = (blended * (light_mask[..., np.newaxis] + config.AMBIENT_FLOOR)).clip(0, 255)

        return result.astype(np.uint8)

    def draw_god_rays(self, surface, rays_intensity, center=None):
        if rays_intensity < 0.05:

            surface.fill((0, 0, 0, 0))
            return

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
