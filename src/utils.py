import os
import sys
import math
import pygame as pg
import numpy as np
from . import config

def _warn(msg):
    print("[ресурсы] " + msg, file=sys.stderr)

def load_texture(path=None, size=None):
    if size is None:
        size = (config.TEX_SIZE, config.TEX_SIZE)

    if path:
        if os.path.exists(path):
            try:
                img = pg.image.load(path).convert()
                surf = pg.Surface(size)
                surf.blit(img, (0, 0))
                return pg.surfarray.array3d(surf).astype(np.float32)
            except Exception as exc:
                _warn("не удалось загрузить текстуру %s: %s -> серая заглушка"
                      % (path, exc))
        else:
            _warn("текстура не найдена: %s -> серая заглушка" % path)

    surf = pg.Surface(size)
    surf.fill((100, 100, 100))
    return pg.surfarray.array3d(surf).astype(np.float32)

def load_textures(texture_map):
    return {key: load_texture(path) for key, path in texture_map.items()}

def load_sprite(path, size=None):
    if size is None:
        size = (config.TEX_SIZE, config.TEX_SIZE)

    if path and os.path.exists(path):
        try:
            img = pg.image.load(path).convert_alpha()
            rgb = pg.surfarray.array3d(img).astype(np.float32)
            alpha = pg.surfarray.array_alpha(img).astype(np.float32)
            return np.dstack([rgb, alpha])
        except Exception as exc:
            _warn("не удалось загрузить спрайт %s: %s -> маджента-заглушка"
                  % (path, exc))
    else:
        _warn("спрайт не найден: %s -> маджента-заглушка" % path)

    w, h = size
    placeholder = np.zeros((w, h, 4), dtype=np.float32)
    placeholder[:, :, 0] = 255.0
    placeholder[:, :, 2] = 255.0
    placeholder[:, :, 3] = 255.0
    return placeholder

def clamp(value, min_val, max_val):
    return max(min_val, min(value, max_val))

def desaturate(tex, amount=0.6, dim=1.0):
    out = tex.copy()
    gray = np.dot(tex[..., :3], [0.299, 0.587, 0.114])
    gray3 = np.stack([gray] * 3, axis=-1)
    out[..., :3] = (tex[..., :3] * (1.0 - amount) + gray3 * amount) * dim
    return out

def camera_space(px, py, pa, ox, oy):
    dx = ox - px
    dy = oy - py
    dist = math.hypot(dx, dy)
    theta = math.atan2(dy, dx) - pa

    theta = (theta + math.pi) % (2 * math.pi) - math.pi
    forward = dx * math.cos(pa) + dy * math.sin(pa)
    return dist, theta, forward

def has_line_of_sight(game_map, px, py, ox, oy):
    map_h, map_w = game_map.shape
    dx = ox - px
    dy = oy - py
    dist = math.hypot(dx, dy)
    if dist < 1e-6:
        return True

    mx, my = int(px), int(py)
    tx_cell, ty_cell = int(ox), int(oy)
    if mx == tx_cell and my == ty_cell:
        return True

    rdx, rdy = dx / dist, dy / dist
    ddx = abs(1 / rdx) if rdx != 0 else 1e30
    ddy = abs(1 / rdy) if rdy != 0 else 1e30
    sx, sdx = (-1, (px - mx) * ddx) if rdx < 0 else (1, (mx + 1 - px) * ddx)
    sy, sdy = (-1, (py - my) * ddy) if rdy < 0 else (1, (my + 1 - py) * ddy)

    traveled = 0.0
    while traveled < dist - 1e-4:
        if sdx < sdy:
            traveled = sdx
            sdx += ddx
            mx += sx
        else:
            traveled = sdy
            sdy += ddy
            my += sy

        if not (0 <= my < map_h and 0 <= mx < map_w):
            return False

        if mx == tx_cell and my == ty_cell:
            return True
        if game_map[my, mx] > 0:
            return False

    return True
