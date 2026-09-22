# src/placeholder_sprites.py
"""
Временные спрайты-заглушки для интерактивных объектов.

Спрайты возвращаются как numpy-массивы RGBA float32 формы (size, size, 4)
с индексацией [x, y] (согласовано с текстурами стен и рендерером).
Модуль легко удалить, заменив заглушки финальным артом.
"""

import numpy as np
from . import config


def _blank(size):
    """Прозрачный холст size x size (RGBA float32)."""
    return np.zeros((size, size, 4), dtype=np.float32)


def _fill(arr, x0, x1, y0, y1, color):
    """Залить прямоугольник [x0:x1, y0:y1] цветом RGBA."""
    arr[x0:x1, y0:y1, 0] = color[0]
    arr[x0:x1, y0:y1, 1] = color[1]
    arr[x0:x1, y0:y1, 2] = color[2]
    arr[x0:x1, y0:y1, 3] = color[3]


def button_states(size=None):
    """
    Кнопка в двух состояниях: [отжата (красная), нажата (зелёная)].
    Небольшая панель на стене с центральной клавишей.
    """
    if size is None:
        size = config.TEX_SIZE

    plate = (60, 60, 70, 255)      # металлическая панель
    released = (210, 60, 50, 255)  # красная клавиша
    pressed = (60, 200, 90, 255)   # зелёная клавиша

    a = _blank(size)
    _fill(a, 16, 48, 16, 48, plate)
    _fill(a, 22, 42, 22, 42, released)

    b = _blank(size)
    _fill(b, 16, 48, 16, 48, plate)
    # Нажатая клавиша чуть меньше и темнее - эффект "вдавлена"
    _fill(b, 25, 39, 25, 39, (int(pressed[0] * 0.7),
                              int(pressed[1] * 0.7),
                              int(pressed[2] * 0.7), 255))
    return [a, b]


def door_states(size=None):
    """
    Дверь в двух состояниях: [закрыта (сплошная), открыта (проём виден)].
    Твёрдость задаётся не спрайтом, а состоянием объекта.
    """
    if size is None:
        size = config.TEX_SIZE

    frame = (90, 70, 45, 255)   # дверная коробка
    leaf = (140, 100, 60, 255)  # полотно двери
    seam = (70, 50, 30, 255)    # шов посередине

    closed = _blank(size)
    _fill(closed, 8, 56, 0, 64, leaf)
    _fill(closed, 31, 33, 4, 60, seam)  # вертикальный шов

    opened = _blank(size)
    # Только коробка: боковые стойки и верхняя перемычка, центр прозрачен
    _fill(opened, 8, 14, 0, 64, frame)
    _fill(opened, 50, 56, 0, 64, frame)
    _fill(opened, 8, 56, 0, 6, frame)
    return [closed, opened]
