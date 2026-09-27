import math
import random

def generate_maze(cw, ch, seed=0, wall_id=1):
    rng = random.Random(seed)
    cols = 2 * cw + 1
    rows = 2 * ch + 1
    grid = [[wall_id] * cols for _ in range(rows)]
    visited = [[False] * cw for _ in range(ch)]

    def carve(cx, cy):
        visited[cy][cx] = True
        grid[2 * cy + 1][2 * cx + 1] = 0
        neighbours = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        rng.shuffle(neighbours)
        for dx, dy in neighbours:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < cw and 0 <= ny < ch and not visited[ny][nx]:
                grid[2 * cy + 1 + dy][2 * cx + 1 + dx] = 0
                carve(nx, ny)

    carve(0, 0)

    start_xy = (2 * 0 + 1 + 0.5, 2 * 0 + 1 + 0.5)
    exit_xy = (2 * (cw - 1) + 1 + 0.5, 2 * (ch - 1) + 1 + 0.5)

    if grid[1][2] == 0:
        start_angle = 0.0
    elif grid[2][1] == 0:
        start_angle = math.pi / 2
    else:
        start_angle = 0.0

    return grid, start_xy, start_angle, exit_xy
