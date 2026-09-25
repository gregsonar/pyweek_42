# src/maze.py
"""Генератор лабиринтов (рекурсивный бэктрекинг) для карт уровней.

Классический алгоритм "recursive backtracker" (DFS с возвратом): даёт
"идеальный" лабиринт без циклов - с гарантированными тупиками и единственным
путём между любыми клетками. Сетка тайлов имеет размер (2*ch+1) x (2*cw+1):
клетки лабиринта стоят на нечётных позициях, между ними - стены, которые
алгоритм выборочно убирает (проход = 0, стена = wall_id). Внешняя рамка -
всегда стены.
"""

import math
import random


def generate_maze(cw, ch, seed=0, wall_id=1):
    """
    Сгенерировать лабиринт cw x ch клеток.

    Возвращает (grid, start_xy, start_angle, exit_xy):
    - grid: карта тайлов (список строк), 0 - проход, wall_id - стена;
      размер (2*ch+1) строк на (2*cw+1) столбцов;
    - start_xy: мировые координаты центра стартовой клетки (угол 0,0);
    - start_angle: угол взгляда игрока в открытую сторону от старта;
    - exit_xy: мировые координаты центра выходной клетки (угол cw-1, ch-1).
    """
    rng = random.Random(seed)
    cols = 2 * cw + 1
    rows = 2 * ch + 1
    grid = [[wall_id] * cols for _ in range(rows)]
    visited = [[False] * cw for _ in range(ch)]

    def carve(cx, cy):
        visited[cy][cx] = True
        grid[2 * cy + 1][2 * cx + 1] = 0  # клетка - проход
        neighbours = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        rng.shuffle(neighbours)
        for dx, dy in neighbours:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < cw and 0 <= ny < ch and not visited[ny][nx]:
                grid[2 * cy + 1 + dy][2 * cx + 1 + dx] = 0  # убрать стену между
                carve(nx, ny)

    carve(0, 0)

    start_xy = (2 * 0 + 1 + 0.5, 2 * 0 + 1 + 0.5)  # центр клетки (0,0) -> (1.5, 1.5)
    exit_xy = (2 * (cw - 1) + 1 + 0.5, 2 * (ch - 1) + 1 + 0.5)

    # Угол взгляда: в открытую сторону от старта (восток или юг)
    if grid[1][2] == 0:
        start_angle = 0.0            # проход на восток (+x)
    elif grid[2][1] == 0:
        start_angle = math.pi / 2    # проход на юг (+y)
    else:
        start_angle = 0.0

    return grid, start_xy, start_angle, exit_xy
