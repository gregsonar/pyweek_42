import numpy as np
from . import config

def _blank(size):
    return np.zeros((size, size, 4), dtype=np.float32)

def _fill(arr, x0, x1, y0, y1, color):
    arr[x0:x1, y0:y1, 0] = color[0]
    arr[x0:x1, y0:y1, 1] = color[1]
    arr[x0:x1, y0:y1, 2] = color[2]
    arr[x0:x1, y0:y1, 3] = color[3]

def button_states(size=None):
    if size is None:
        size = config.TEX_SIZE

    plate = (60, 60, 70, 255)
    released = (210, 60, 50, 255)
    pressed = (60, 200, 90, 255)

    a = _blank(size)
    _fill(a, 16, 48, 16, 48, plate)
    _fill(a, 22, 42, 22, 42, released)

    b = _blank(size)
    _fill(b, 16, 48, 16, 48, plate)

    _fill(b, 25, 39, 25, 39, (int(pressed[0] * 0.7),
                              int(pressed[1] * 0.7),
                              int(pressed[2] * 0.7), 255))
    return [a, b]
