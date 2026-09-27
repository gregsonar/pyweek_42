import math

from .level import Level
from .maze import generate_maze

VIRT_WIDTH = 320
VIRT_HEIGHT = 200
WIN_WIDTH = 960
WIN_HEIGHT = 600

TEX_SIZE = 64
FOV = 0.6
FPS = 30

CEILING_HEIGHT = 2.0
EYE_HEIGHT = 0.5

SKY_TILES = 3.0

FLOOR_VARIANT_SECOND = 0.4
CEIL_VARIANT_SECOND = 0.2

BASE_BRIGHTNESS = 2.6
DEPTH_FALLOFF = 0.15
AMBIENT_FLOOR = 0.16
VIGNETTE = 7.0

MOUSE_SENSITIVITY = 0.003
MOVE_SPEED = 2.1
MAX_DT = 0.05

TICK_RATE = 60
MAX_TICKS_PER_FRAME = 5
FREEZE_BUDGET_TICKS = 180
REPAY_INTERVAL_MIN = 210
REPAY_INTERVAL_MAX = 720

PLAYER_MAX_HP = 3
TRAP_ON_TICKS = 90
TRAP_OFF_TICKS = 90
TRAP_DAMAGE_PERIOD = TICK_RATE
TRAP_OFF_DESATURATE = 0.65
TRAP_OFF_DIM = 0.85
PLAYER_STUN_TICKS = round(0.3 * TICK_RATE)

LANGUAGE = "en"

AUDIO_MUSIC_DEFAULT = True
AUDIO_SFX_DEFAULT = True

MUSIC_VOLUME = 0.4
SFX_VOLUME = 1.0

LEVEL_TIME_LIMIT = 90.0

FONT_PATH = "assets/fonts/HomeVideo-Regular.ttf"
HUD_FONT_FALLBACK = "segoeui,dejavusans,arial"

HUD_SYMBOL_FONT_NAME = "segoeuisymbol,dejavusans,arial"

HUD_TIMER_SIZE = 40
HUD_TEXT_SIZE = 24
HUD_HP_SIZE = 34
HUD_MARGIN = 12
HUD_COLOR = (230, 230, 230)
HUD_TIMER_FROZEN_COLOR = (120, 210, 255)
HUD_HP_FULL_COLOR = (235, 80, 80)
HUD_HP_LOST_COLOR = (110, 110, 110)
HUD_SHADOW_COLOR = (0, 0, 0)

DAMAGE_FLASH_COLOR = (200, 0, 0)
DAMAGE_FLASH_MAX_ALPHA = 140
DAMAGE_FLASH_FADE = 2.5

FAIL_PAUSE_SECONDS = 2.0

BUZZ_MAX_DIST = 6.0

FREEZE_MASK_COLOR = (30, 90, 220)
FREEZE_MASK_MIN_ALPHA = 35
FREEZE_MASK_MAX_ALPHA = 105
FREEZE_MASK_PULSE_HZ = 1.1
FREEZE_MASK_FADE = 6.0

LEVEL_MSG_SECONDS = 3.0

BUDGET_BAR_WIDTH = 140
BUDGET_BAR_MIN_WIDTH = 3
BUDGET_BAR_HEIGHT = 6
BUDGET_BAR_GAP = 6
BUDGET_BAR_COLOR = HUD_TIMER_FROZEN_COLOR

MENU_BG_COLOR = (12, 14, 20)
MENU_TITLE_SIZE = 64
MENU_TITLE_COLOR = (235, 240, 250)
MENU_ITEM_SIZE = 32
MENU_ITEM_SPACING = 16
MENU_ITEM_SPACING_COMPACT = 12
MENU_COLOR = (200, 205, 215)
MENU_COLOR_SELECTED = (120, 210, 255)
MENU_COLOR_DISABLED = (90, 95, 105)

CREDITS_LINE_SIZE = 22

MENU_HELP_SIZE = 20
MENU_HELP_COLOR = (150, 158, 172)
MENU_HELP_LINE_SPACING = 6
MENU_HELP_BOTTOM_MARGIN = 24
PAUSE_TITLE_SIZE = 52
PAUSE_DIM_COLOR = (0, 0, 0)
PAUSE_DIM_ALPHA = 170

FADE_DURATION = 0.25
FADE_COLOR = (0, 0, 0)

SPLASH_LOGO_PATH = "assets/logo.png"
SPLASH_TITLE_SIZE = 72
SPLASH_FADE_IN = 0.7
SPLASH_HOLD = 1.6
SPLASH_FADE_OUT = 0.7

INTERACT_RADIUS = 2.5
OBJECT_BLOCK_RADIUS = 0.35
HIGHLIGHT_BRIGHTNESS = 1.3
SPRITE_NEAR_CLIP = 0.1

DEFAULT_MAP = [
    [1, 1, 15, 16, 1, 1, 1, 1, 9, 8, 10, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 12],
    [7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 3],
    [11, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 1, 0, 2],
    [2, 1, 1, 1, 1, 1, 0, 1, 1, 14, 1, 1, 1, 3],
    [3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 3],
    [3, 0, 5, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 2],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 3],
    [1, 4, 5, 1, 10, 1, 7, 1, 3, 1, 23, 23, 23, 1],
]

PLAYER_START = {"x": 9.5, "y": 3, "angle": -math.pi / 2}

UPPER_DEFAULT = 21
UPPER_BY_LOWER = {
    1: 21,
    2: 22,
    11: 21,
    12: 13,

}

UPPER_OVERRIDES = {
    (5, 6): 21,
    (3, 5): 21,
    (8, 11): 21,

}

FLOOR_OVERRIDES = {
    (9, 10): "floor_outside",
    (9, 11): "floor_outside",
    (9, 12): "floor_outside",
}

def _build_upper_map(lower, upper_overrides={}):
    upper = [
        [UPPER_BY_LOWER.get(v, UPPER_DEFAULT) if v > 0 else 0 for v in row]
        for row in lower
    ]
    for (row, col), tile in upper_overrides.items():
        upper[row][col] = tile
    return upper

DEFAULT_MAP_UPPER = _build_upper_map(DEFAULT_MAP, UPPER_OVERRIDES)

PROPS = [
    ("sprites/spr_plant.png", 0.62, 0.85, 10.5, 1.6, 0.0, True, None, None, True),
    ("sprites/spr_plant.png", 0.62, 0.85, 7.5, 1.6, 0.0, True, None, None, True),
    ("sprites/spr_bottles_1.png", 1.20, 0.82, 3.5, 8.5, 0.0, False, None),
    ("sprites/spr_garbage_1.png", 1.00, 1.05, 5.0, 9.5, 0.0, True, None),
    ("sprites/spr_garbage_1.png", 0.55, 0.34, 7.0, 7.7, 0.0, True, None),
    ("sprites/spr_wires_1.png", 0.85, 0.52, 9.5, 7.5, 1.0, False, None),

    (
        "sprites/spr_wires_1.png",
        0.85,
        0.52,
        10.5,
        6.5,
        1.0,
        False,
        None,
        math.radians(90),
    ),
    (
        "sprites/spr_wires_1.png",
        0.85,
        0.52,
        10.5,
        9.5,
        1.0,
        False,
        None,
        False,
        math.radians(45),
    ),
    ("sprites/spr_window.png", 1, 1, 11.5, 8.5, 0.0, True, 0.4),
    ("sprites/spr_window.png", 1, 1, 11.5, 0.5, 0.0, True, 0.6),
]

INTERACTABLES = [
    {
        "kind": "button",
        "id": "b1",
        "x": 5.0,
        "y": 4.99,
        "angle": 0.0,
        "width": 0.5,
        "height": 0.5,
        "y_offset": 0.35,
        "cyclic": True,
        "off": "sprites/spr_button1_off.png",
        "on": "sprites/spr_button1_on.png",
    },
    {
        "kind": "locked_door",
        "button": "b1",
        "x": 6.5,
        "y": 5.5,
        "angle": 0.0,
        "width": 1,
        "height": 1,
        "y_offset": 0.0,
        "block_radius": 0.55,
        "locked": "sprites/spr_door1_closed_off.png",
        "closed": "sprites/spr_door1_closed.png",
        "open": "sprites/spr_door1_open.png",
    },
    {
        "kind": "exit",
        "x": 8.5,
        "y": 9.99,
        "angle": math.pi,
        "width": 1,
        "height": 1,
        "y_offset": 0.0,
        "cyclic": False,
        "closed": "sprites/spr_door2_closed-exit.png",
    },
]

TRAPS = [
    (6, 3, [1500, 1500], True),
    (6, 4, [1500, 1500, 2000, 500], True),
    (7, 9, [1000, 1000, 500, 3000], False),
    (8, 9, [2000, 1000, 500, 3000], False),
]

BATTERY_TRAPS = [
    (4, 4, [1800, 1200], True),
]

LEVEL1 = Level(
    lower_map=DEFAULT_MAP,
    upper_map=DEFAULT_MAP_UPPER,
    player_start=PLAYER_START,
    sky_mode=False,
    time_limit=LEVEL_TIME_LIMIT,
    number=1,
    props=PROPS,
    interactables=INTERACTABLES,
    traps=TRAPS,
    battery_traps=BATTERY_TRAPS,
    floor_overrides=FLOOR_OVERRIDES,
    music="sonic_drive_slow.wav",
    music_loop=True,
)

_MAZE_GRID, _MAZE_START, _MAZE_ANGLE, _MAZE_EXIT = generate_maze(
    cw=9, ch=7, seed=42, wall_id=1
)

_MAZE_GRID[14][2] = 9
_MAZE_GRID[7][10] = 2
_MAZE_GRID[10][17] = 7
_MAZE_GRID[6][15] = 7

LEVEL2_PROPS = [
    ("sprites/spr_plant.png", 0.62, 0.85, 10.5, 1.6, 0.0, True, None, None, True),
    ("sprites/spr_plant.png", 0.62, 0.85, 7, 1.6, 0.0, True, None, None, True),
    ("sprites/spr_bottles_1.png", 1.20, 0.82, 3.5, 8.5, 0.0, False, None),

    ("sprites/spr_garbage_1.png", 0.80, 0.85, 3.3, 9.5, 0.0, True, 0.4, 0, True),
    ("sprites/spr_garbage_1.png", 0.55, 0.34, 7.0, 7.2, 0.0, False, True),
    ("sprites/spr_wires_1.png", 0.85, 0.52, 7.5, 10.5, 1.0, False, None),
]

LEVEL2 = Level(
    lower_map=_MAZE_GRID,
    upper_map=_build_upper_map(_MAZE_GRID),
    player_start={"x": _MAZE_START[0], "y": _MAZE_START[1], "angle": _MAZE_ANGLE},
    sky_mode=False,
    time_limit=50.0,
    number=2,
    props=LEVEL2_PROPS,
    interactables=[

        {
            "kind": "exit",
            "x": _MAZE_EXIT[0],
            "y": _MAZE_EXIT[1],
            "billboard": True,
            "width": 1,
            "height": 1,
            "y_offset": 0.0,
            "cyclic": False,
            "closed": "sprites/spr_door2_closed-exit.png",
        },
    ],
    traps=[
        (5, 3, [1500, 1500], True),
        (6, 3, [1000, 1500, 2000, 500], True),
        (1, 11, [1000, 500, 2000, 500], True),
        (11, 1, [1000, 500, 2000, 500], True),
    ],
    floor_overrides={},
    music="sonic_drive_slow.wav",
    music_loop=False,
)

_MAZE_GRID_2, _MAZE_START_2, _MAZE_ANGLE_2, _MAZE_EXIT_2 = generate_maze(
    cw=3, ch=40, seed=42, wall_id=2
)

_MAZE_GRID_2[80][5] = 1

LEVEL4 = Level(
    lower_map=_MAZE_GRID_2,
    upper_map=_build_upper_map(_MAZE_GRID_2),
    player_start={"x": _MAZE_START_2[0], "y": _MAZE_START_2[1], "angle": _MAZE_ANGLE_2},
    sky_mode=True,
    time_limit=70.0,
    number=4,
    props=[
        ("walls/wall_concrete_01_up.png", 1, 1, 1.5, 5.5, 1, False, 0, 0),
        ("sprites/spr_plant.png", 0.62, 0.85, 1.8, 7, 0, True, 0.35, 0, True),
        ("sprites/spr_plant.png", 0.50, 0.80, 1.4, 9, 0, True, 0.3, 0, True),
        ("sprites/spr_plant.png", 0.50, 0.80, 1.7, 11, 0, True, 0.3, 0, True),
        ("sprites/spr_bottles_1.png", 1, 1, 1.6, 48, 0, True, 0.3, 0, True),
        ("sprites/spr_bottles_1.png", 4, 4, 1.9, 59, 0, False, 0, 0, False),
    ],
    interactables=[
        {
            "kind": "door",
            "x": 1.5,
            "y": 5.5,
            "angle": 0.0,
            "width": 1,
            "height": 1,
            "y_offset": 0.0,
            "block_radius": 0.55,
            "locked": "sprites/spr_door1_closed_off.png",
            "closed": "sprites/spr_door1_closed.png",
            "open": "sprites/spr_door1_open.png",
        },
        {
            "kind": "exit",
            "x": _MAZE_EXIT_2[0],
            "y": _MAZE_EXIT_2[1] + 0.49,
            "billboard": False,
            "width": 1,
            "height": 1,
            "y_offset": 0.0,
            "cyclic": False,
            "closed": "sprites/spr_door2_closed-exit.png",
        },
    ],
    traps=[
        (2, 15, [1000, 1500], True),
        (3, 15, [1500, 1500], True),
        (4, 15, [2000, 1500], True),
        (4, 21, [1000, 500, 1000, 1000], True),
        (5, 3, [1500, 1500], True),
        (3, 28, [1500, 1000], True),
        (3, 29, [1000, 900], True),
    ],
    floor_overrides={},
    music="sonic_drive_fast.wav",
    music_loop=True,
)

LEVEL3_MAP = [
    [1, 1, 2, 1, 1, 1, 1, 10, 7, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 9],
    [1, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 15],
    [1, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 16],
    [1, 8, 1, 0, 1, 1, 1, 1, 1, 1, 1, 12, 1, 1],
    [1, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 0, 0, 1, 0, 0, 10, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 14],
    [1, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1],
    [1, 1, 7, 1, 4, 1, 10, 1, 1, 1, 1, 1, 1, 1],
]

LEVEL3_UPPER_OVERRIDES = {
    (6, 0): 23,
    (2, 3): 21,
    (3, 3): 21,
    (3, 5): 21,
    (5, 3): 21,
    (5, 8): 21,
    (5, 11): 13,
    (7, 3): 23,
    (2, 10): 21,
}

LEVEL3_FLOOR_OVERRIDES = {}

LEVEL3_START = {"x": 1.5, "y": 1.2, "angle": 0}

LEVEL3_PROPS = [
    ("sprites/spr_bottles_1.png", 1, 1, 10.5, 4.5, 0.0, False, None),
    ("sprites/spr_bottles_1.png", 0.8, 0.8, 10.5, 6.1, 0.0, False, None),
    ("sprites/spr_garbage_1.png", 0.80, 0.85, 7.3, 9.5, 0.0, True, 0.4, 0, True),
]

LEVEL3_BATTERY_TRAPS = [
    (3, 4, [1800, 1200], True),
]

LEVEL3_INTERACTABLES = [
    {
        "kind": "door",
        "x": 3.5,
        "y": 5.5,
        "angle": 0.0,
        "width": 1,
        "height": 1,
        "y_offset": 0.0,
        "block_radius": 0.55,
        "locked": "sprites/spr_door1_closed_off.png",
        "closed": "sprites/spr_door1_closed.png",
        "open": "sprites/spr_door1_open.png",
    },
    {
        "kind": "door",
        "x": 5.5,
        "y": 3.5,
        "angle": math.pi / 2,
        "width": 1,
        "height": 1,
        "y_offset": 0.0,
        "block_radius": 0.55,
        "locked": "sprites/spr_door1_closed_off.png",
        "closed": "sprites/spr_door1_closed.png",
        "open": "sprites/spr_door1_open.png",
    },
    {
        "kind": "door",
        "x": 10.5,
        "y": 2.5,
        "angle": 0,
        "width": 1,
        "height": 1,
        "y_offset": 0.0,
        "block_radius": 0.45,
        "locked": "sprites/spr_door1_closed_off.png",
        "closed": "sprites/spr_door1_closed.png",
        "open": "sprites/spr_door1_open.png",
    },
    {
        "kind": "button",
        "id": "b1l3",
        "x": 9.01,
        "y": 3.5,
        "angle": math.pi / 2,
        "width": 0.5,
        "height": 0.5,
        "y_offset": 0.35,
        "cyclic": True,
        "off": "sprites/spr_button1_off.png",
        "on": "sprites/spr_button1_on.png",
    },
    {
        "kind": "button",
        "id": "b2l3",
        "x": 1.01,
        "y": 1.5,
        "angle": math.pi / 2,
        "width": 0.5,
        "height": 0.5,
        "y_offset": 0.35,
        "cyclic": True,
        "off": "sprites/spr_button1_off.png",
        "on": "sprites/spr_button1_on.png",
    },
    {
        "kind": "locked_door",
        "button": "b1l3",
        "x": 5,
        "y": 8.5,
        "angle": math.pi / 2,
        "width": 1,
        "height": 1,
        "y_offset": 0.0,
        "block_radius": 0.55,
        "locked": "sprites/spr_door1_closed_off.png",
        "closed": "sprites/spr_door1_closed.png",
        "open": "sprites/spr_door1_open.png",
    },
    {
        "kind": "locked_door",
        "button": "b2l3",
        "x": 9,
        "y": 10.5,
        "angle": math.pi / 2,
        "width": 1,
        "height": 1,
        "y_offset": 0.0,
        "block_radius": 0.55,
        "locked": "sprites/spr_door1_closed_off.png",
        "closed": "sprites/spr_door1_closed.png",
        "open": "sprites/spr_door1_open.png",
    },
    {
        "kind": "exit",
        "x": 9.01,
        "y": 9.5,
        "billboard": False,
        "angle": math.pi / 2,
        "width": 1,
        "height": 1,
        "y_offset": 0.0,
        "cyclic": False,
        "closed": "sprites/spr_door2_closed-exit.png",
    },
]

LEVEL3_TRAPS = [
    (6, 3, [1000, 1000, 1000, 900], True),
    (6, 4, [1000, 1200, 1200, 800], True),
    (8, 1, [1300, 800], True),
    (6, 8, [1300, 800], True),
    (6, 7, [1000, 800], True),
    (2, 6, [1000, 1000, 1000, 600, 1000, 200], True),
    (3, 6, [1000, 1000, 1000, 600, 1000, 200], True),
    (4, 6, [1000, 1000, 1000, 600, 1000, 200], True),
]

LEVEL3 = Level(
    lower_map=LEVEL3_MAP,
    upper_map=_build_upper_map(LEVEL3_MAP, LEVEL3_UPPER_OVERRIDES),
    player_start=LEVEL3_START,
    sky_mode=True,
    time_limit=45,
    number=3,
    props=LEVEL3_PROPS,
    interactables=LEVEL3_INTERACTABLES,
    traps=LEVEL3_TRAPS,
    battery_traps=LEVEL3_BATTERY_TRAPS,
    floor_overrides=LEVEL3_FLOOR_OVERRIDES,
    music="sonic_drive_slow.wav",
    music_loop=True,
)

LEVEL5_MAP = [
    [1, 9, 1, 1],
    [1, 0, 0, 1],
    [1, 0, 0, 1],
    [1, 0, 0, 1],
    [1, 0, 0, 1],
    [1, 0, 0, 1],
    [1, 0, 0, 0],
    [2, 0, 0, 1],
    [1, 0, 0, 1],
    [1, 0, 0, 1],
    [1, 0, 0, 1],
    [1, 0, 0, 1],
    [1, 0, 0, 1],
    [1, 0, 0, 1],
    [1, 0, 0, 1],
    [1, 0, 0, 1],
    [0, 0, 0, 1],
    [1, 0, 0, 1],
    [1, 0, 0, 1],
    [8, 0, 0, 1],
    [1, 0, 0, 1],
    [1, 0, 0, 1],
    [1, 0, 0, 1],
    [1, 0, 0, 1],
    [1, 1, 1, 1],
]

LEVEL5_UPPER_OVERRIDES = {
    (6, 3): 21,
    (16, 0): 21,
}

LEVEL5_FLOOR_OVERRIDES = {
    (1, 1): "floor2",
    (4, 2): "floor2",
    (5, 2): "floor2",
    (6, 2): "floor2",
    (9, 1): "floor2",
    (10, 1): "floor2",
    (11, 2): "floor2",
    (12, 1): "floor2",
    (14, 2): "floor2",
    (18, 1): "floor2",
    (19, 2): "floor2",
    (22, 1): "floor2",
    (23, 2): "floor2",
}

LEVEL5_START = {"x": 1.5, "y": 1.5, "angle": 90}

LEVEL5_PROPS = [
    ("sprites/spr_window.png", 1, 1, 3, 6.5, 0, True, 0.4, math.radians(90)),
    ("walls/wall_concrete_01_up.png", 1, 1, 3, 6.5, 1, True, 0.4, math.radians(90)),
    ("sprites/spr_window.png", 1, 1, 1, 16.5, 0, True, 0.4, math.radians(90)),
    ("walls/wall_concrete_01_up.png", 1, 1, 1, 16.5, 1, True, 0.4, math.radians(90)),
]

LEVEL5_INTERACTABLES = [
    {
        "kind": "exit",
        "x": 1.5,
        "y": 23.5,
        "angle": 0,
        "width": 1,
        "height": 1,
        "y_offset": 0,
        "cyclic": False,
        "closed": "sprites/spr_door2_closed-exit.png",
    },
]

LEVEL5_TRAPS = [
    (2, 4, [90, 90], True),
    (1, 4, [90, 90], True),
    (1, 6, [90, 1000], True),
    (2, 6, [90, 90], True),
    (1, 11, [90, 100], True),
    (2, 11, [90, 60], True),
    (1, 12, [1000, 300], True),
    (2, 12, [500, 50], True),
    (1, 13, [500, 500], True),
    (2, 13, [1000, 100], True),
    (1, 18, [90, 90], True),
    (2, 18, [1000, 500], True),
    (1, 19, [1000, 200], True),
    (2, 21, [3000, 500], True),
    (2, 22, [90, 90], True),
    (2, 23, [3000, 40], True),
    (1, 22, [3000, 45], True),
    (2, 17, [3000, 48], True),
    (1, 15, [3000, 52], True),
]

LEVEL5_BATTERY_TRAPS = [
    (1, 5, [1800, 1000], True),
    (2, 5, [1500, 1500], True),
    (1, 9, [1000, 1500], True),
    (2, 9, [1000, 1800], True),
]

LEVEL5 = Level(
    lower_map=LEVEL5_MAP,
    upper_map=_build_upper_map(LEVEL5_MAP, LEVEL5_UPPER_OVERRIDES),
    player_start=LEVEL5_START,
    sky_mode=True,
    time_limit=45,
    number=5,
    props=LEVEL5_PROPS,
    interactables=LEVEL5_INTERACTABLES,
    traps=LEVEL5_TRAPS,
    floor_overrides=LEVEL5_FLOOR_OVERRIDES,
    battery_traps=LEVEL5_BATTERY_TRAPS,
    music="sonic_drive_fast.wav",
    music_loop=False,
)

LEVELS = [LEVEL1, LEVEL2, LEVEL3, LEVEL4, LEVEL5]
DEFAULT_LEVEL = LEVEL1
