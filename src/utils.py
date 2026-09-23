# src/utils.py
"""Вспомогательные функции."""

import os
import sys
import math
import pygame as pg
import numpy as np
from . import config


def _warn(msg):
    """Предупреждение в консоль (stderr) - чтобы отлавливать пропавшие ресурсы."""
    print("[ресурсы] " + msg, file=sys.stderr)


def load_texture(path=None, size=None):
    """
    Загружает текстуру и возвращает её как numpy-массив float32.
    Если путь не указан или файл не найден — возвращает серую заглушку
    и печатает предупреждение в консоль.
    """
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

    # Заглушка: серая текстура
    surf = pg.Surface(size)
    surf.fill((100, 100, 100))
    return pg.surfarray.array3d(surf).astype(np.float32)


def load_textures(texture_map):
    """
    Загружает словарь текстур.
    :param texture_map: dict {key: path_or_none}
    :return: dict {key: numpy_array}
    """
    return {key: load_texture(path) for key, path in texture_map.items()}


def load_sprite(path, size=None):
    """
    Загружает спрайт с альфа-каналом.
    :return: numpy-массив RGBA float32 формы (w, h, 4), индексация [x, y].
    Если файл не найден или не читается — возвращает заметную маджента-заглушку
    (непрозрачную) и печатает предупреждение, а не падает.
    """
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

    # Заглушка: заметный непрозрачный маджента-квадрат
    w, h = size
    placeholder = np.zeros((w, h, 4), dtype=np.float32)
    placeholder[:, :, 0] = 255.0  # R
    placeholder[:, :, 2] = 255.0  # B
    placeholder[:, :, 3] = 255.0  # непрозрачный
    return placeholder


def clamp(value, min_val, max_val):
    """Ограничивает значение диапазоном [min_val, max_val]."""
    return max(min_val, min(value, max_val))


def camera_space(px, py, pa, ox, oy):
    """
    Переводит мировую точку (ox, oy) в систему координат камеры.

    :return: (dist, theta, forward), где
             dist    - евклидово расстояние до точки,
             theta   - угловое смещение от центра взгляда (радианы),
                       согласовано с формулой лучей стен: экранный столбец =
                       (theta + FOV) / (2 * FOV) * VIRT_WIDTH,
             forward - перпендикулярная дистанция до плоскости камеры
                       (та же метрика, что в z-буфере стен).
    """
    dx = ox - px
    dy = oy - py
    dist = math.hypot(dx, dy)
    theta = math.atan2(dy, dx) - pa
    # Нормализация угла в диапазон [-pi, pi]
    theta = (theta + math.pi) % (2 * math.pi) - math.pi
    forward = dx * math.cos(pa) + dy * math.sin(pa)
    return dist, theta, forward


def has_line_of_sight(game_map, px, py, ox, oy):
    """
    Проверяет прямую видимость между точками (px, py) и (ox, oy):
    возвращает False, если между ними есть твёрдая ячейка карты (> 0).
    Обход сетки методом DDA (Amanatides-Woo).
    """
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
        # Достигли ячейки объекта - препятствий по пути не было
        if mx == tx_cell and my == ty_cell:
            return True
        if game_map[my, mx] > 0:
            return False

    return True