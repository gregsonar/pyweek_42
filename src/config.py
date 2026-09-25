# src/config.py
"""Глобальные настройки рендерера."""

import math

from .level import Level
from .maze import generate_maze

# Разрешения
VIRT_WIDTH = 320
VIRT_HEIGHT = 200
WIN_WIDTH = 960
WIN_HEIGHT = 600

# Рендеринг
TEX_SIZE = 64
FOV = 0.6  # поле зрения в радианах
FPS = 30

# Высота уровня (два пояса стен). Потолок = CEILING_HEIGHT тайлов по высоте.
# EYE_HEIGHT - высота глаза над полом; оставлена как раньше (0.5), чтобы игрок
# стоял у пола, а весь прирост высоты уходил вверх (в потолок), а не поднимал
# камеру. Пол и потолок при этом несимметричны и считаются раздельно.
CEILING_HEIGHT = 2.0
EYE_HEIGHT = 0.5

# Режим верха (потолок или небо) задаётся на уровне - см. Level.sky_mode и
# DEFAULT_LEVEL ниже. Здесь только тюнинг рендера неба.
SKY_TILES = 3.0  # сколько раз текстура неба повторяется на 360 градусов

# Рандомизация тайлов пола/потолка между двумя вариантами. Значение - доля
# ВТОРОГО тайла (floor2 / ceil2). Пол 60/40 -> 0.4; потолок 80/20 -> 0.2. Выбор
# пер-клеточный и фиксируется при старте уровня (стабилен между кадрами).
FLOOR_VARIANT_SECOND = 0.4  # доля второго тайла пола (floor_grate_2)
CEIL_VARIANT_SECOND = 0.2  # доля второго тайла потолка (ceiling_panel-2)

# Физика частиц
SPARK_COUNT = 50
SPARK_SPEED_MIN = 0.02
SPARK_SPEED_MAX = 0.05
SPARK_GRAVITY = 0.008
SPARK_LIFE_DECAY = 0.05

# God rays
GOD_RAY_COUNT = 60

# Освещение (все параметры затемнения/яркости сцены - здесь)
BASE_BRIGHTNESS = 2.6  # базовая яркость сцены (когда не зажата ЛКМ)
DEPTH_FALLOFF = 0.15  # скорость затемнения по расстоянию (больше = темнее вдаль)
AMBIENT_FLOOR = 0.16  # минимальная подсветка (чтобы тени не были чёрными)
VIGNETTE = 7.0  # базовая виньетка/фокус (меньше = светлее края)

# Управление
MOUSE_SENSITIVITY = 0.003
MOVE_SPEED = 2.1  # единиц карты в секунду
MAX_DT = 0.05  # максимальный шаг кадра (сек): защита от туннелирования при лаге

# Время и способность заёма времени (Borrowed Time)
TICK_RATE = 60  # логических тиков в секунду (фиксированный шаг логики)
MAX_TICKS_PER_FRAME = 5  # максимум тиков за кадр (защита от спирали смерти при лаге)
FREEZE_BUDGET_TICKS = 180  # бюджет заморозки мира (тики; 180 = 3 с при 60 тик/с)
REPAY_INTERVAL_MIN = 300  # мин. задержка до возврата долга (тики; 5 с)
REPAY_INTERVAL_MAX = 720  # макс. задержка до возврата долга (тики; 12 с)

# Игрок и ловушки
PLAYER_MAX_HP = 3  # запас здоровья (обновляется при старте уровня)
TRAP_ON_TICKS = 90  # тиков во включённом состоянии (1.5 с при 60 тик/с)
TRAP_OFF_TICKS = 90  # тиков в выключенном состоянии
TRAP_DAMAGE_PERIOD = TICK_RATE  # период урона при стоянии на активной (1/с)
TRAP_OFF_DESATURATE = 0.65  # насколько обесцветить текстуру выключенной ловушки
TRAP_OFF_DIM = 0.85  # затемнение выключенной ловушки (временно, пока 1 текстура)
PLAYER_STUN_TICKS = round(0.3 * TICK_RATE)  # стан игрока при уроне (0.3 с)

# Локализация интерфейса. Языки: "en", "ru". Переключение в игре - клавиша L.
LANGUAGE = "en"

# Лимит времени на попытку по умолчанию (сек) - см. Level.time_limit.
LEVEL_TIME_LIMIT = 90.0

# Игровой шрифт (HomeVideo) - для HUD и всех экранов. Покрывает цифры, латиницу
# и кириллицу. При сбое загрузки файла - системный фолбэк.
FONT_PATH = "assets/fonts/HomeVideo-Regular.ttf"
HUD_FONT_FALLBACK = "segoeui,dejavusans,arial"
# Символьный шрифт только для плейсхолдеров HP (♥/♡): в HomeVideo этих глифов
# нет (рисуется "тофу"). Уйдёт, когда HP заменим на реальные иконки.
HUD_SYMBOL_FONT_NAME = "segoeuisymbol,dejavusans,arial"

# HUD (интерфейс поверх сцены; рисуется в разрешении окна после масштаба)
HUD_TIMER_SIZE = 40  # кегль шрифта таймера (верх по центру)
HUD_TEXT_SIZE = 24  # кегль шрифта строки текста (верх справа)
HUD_HP_SIZE = 34  # кегль шрифта иконок здоровья (низ слева)
HUD_MARGIN = 12  # отступ HUD от краёв экрана (пиксели окна)
HUD_COLOR = (230, 230, 230)  # основной цвет текста HUD
HUD_TIMER_FROZEN_COLOR = (120, 210, 255)  # цвет таймера при остановленном мире
HUD_HP_FULL_COLOR = (235, 80, 80)  # цвет символа оставшегося HP (♥)
HUD_HP_LOST_COLOR = (110, 110, 110)  # цвет символа потерянного HP (♡)
HUD_SHADOW_COLOR = (0, 0, 0)  # цвет тени под текстом (для читаемости)

# Маска урона (полноэкранная вспышка при получении урона)
DAMAGE_FLASH_COLOR = (200, 0, 0)  # цвет вспышки
DAMAGE_FLASH_MAX_ALPHA = 140  # максимальная альфа вспышки (0..255)
DAMAGE_FLASH_FADE = 2.5  # скорость затухания вспышки (единиц в секунду)

# Пауза проигрыша (HP=0 или вышло время): держим маску урона, потом рестарт
FAIL_PAUSE_SECONDS = 2.0  # длительность паузы перед рестартом (сек)

# Маска заморозки игрока (возврат долга): синяя, пульсирует, пока игрок заморожен
FREEZE_MASK_COLOR = (30, 90, 220)  # цвет маски заморозки игрока
FREEZE_MASK_MIN_ALPHA = 35  # альфа в нижней точке пульса (0..255)
FREEZE_MASK_MAX_ALPHA = 105  # альфа в верхней точке пульса (0..255)
FREEZE_MASK_PULSE_HZ = 1.1  # частота пульсации (Гц)
FREEZE_MASK_FADE = 6.0  # скорость плавного появления/угасания (единиц в секунду)

# Вводное сообщение уровня (показывается при первом входе)
LEVEL_MSG_SECONDS = 3.0  # длительность вводного сообщения уровня (сек)

# Шкала баланса заёма времени (полоса под таймером; длина = остаток бюджета,
# сужается симметрично к центру до BUDGET_BAR_MIN_WIDTH при пустом балансе)
BUDGET_BAR_WIDTH = 140  # полная длина шкалы (px) при полном бюджете
BUDGET_BAR_MIN_WIDTH = 3  # длина шкалы (px) при пустом бюджете
BUDGET_BAR_HEIGHT = 6  # толщина шкалы (px)
BUDGET_BAR_GAP = 6  # зазор между таймером и шкалой (px)
BUDGET_BAR_COLOR = HUD_TIMER_FROZEN_COLOR  # цвет шкалы (как таймер при заморозке)

# Меню и экраны (рисуются в разрешении окна)
MENU_BG_COLOR = (12, 14, 20)  # фон экранов меню
MENU_TITLE_SIZE = 64  # кегль заголовка
MENU_TITLE_COLOR = (235, 240, 250)
MENU_ITEM_SIZE = 32  # кегль пунктов меню
MENU_ITEM_SPACING = 16  # доп. зазор между пунктами (px)
MENU_COLOR = (200, 205, 215)  # обычный пункт
MENU_COLOR_SELECTED = (120, 210, 255)  # выбранный пункт (в тон HUD-заморозке)
MENU_COLOR_DISABLED = (90, 95, 105)  # неактивный пункт
PAUSE_TITLE_SIZE = 52  # кегль заголовка паузы
PAUSE_DIM_COLOR = (0, 0, 0)  # цвет затемнения игры под паузой
PAUSE_DIM_ALPHA = 170  # альфа затемнения (0..255)

# Переходы между сценами (фейд через чёрное)
FADE_DURATION = 0.25  # длительность половины перехода (сек): затемнение/проявление
FADE_COLOR = (0, 0, 0)  # цвет затемнения перехода

# Сплеш-заставка при запуске (фикс. длительность + скип любой клавишей/кликом)
SPLASH_LOGO_PATH = "assets/textures/ui/logo.png"  # опц.; иначе текст-заглушка
SPLASH_TITLE_SIZE = 72  # кегль текста-заглушки (когда нет лого)
SPLASH_FADE_IN = 0.7  # сек появления
SPLASH_HOLD = 1.1  # сек показа на полной яркости
SPLASH_FADE_OUT = 0.7  # сек угасания

# Взаимодействие с объектами
INTERACT_RADIUS = 2.5  # максимальная дистанция взаимодействия (клетки)
OBJECT_BLOCK_RADIUS = 0.35  # радиус блокировки прохода твёрдым объектом
HIGHLIGHT_BRIGHTNESS = 1.3  # множитель яркости подсвеченного объекта
SPRITE_NEAR_CLIP = 0.1  # ближняя отсечка для билбордов

# Карта по умолчанию (14×11). Задействованы все 15 стеновых тайлов (id 1..15).
# Крайние клетки - всегда стены. Панорама-окно (11..15) и консоль (9,10)
# стоят в соседних клетках северной стены строго по порядку слева направо.
# Внутренняя перегородка (строка 5) делит зал на две половины с проёмом,
# в котором стоит дверь.
#
# id: 1 бетон_01, 2 бетон_02, 3 бетон_мох, 4 постер_шаман, 5 постер_шлем,
#     6 ферма, 7 вентиляция, 8 терминал, 9 консоль_0, 10 консоль_1,
#     11..15 панорама-окно (тайлы 1..5)
DEFAULT_MAP = [
    [1, 1, 15, 16, 1, 1, 1, 1, 9, 8, 10, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 12],
    [7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 3],
    [11, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 1, 0, 2],
    [2, 1, 1, 1, 1, 1, 0, 1, 1, 14, 1, 1, 1, 3],  # перегородка с проёмом (x=6)
    [3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
    [3, 0, 5, 0, 0, 0, 0, 0, 0, 1, 1, 0, 1, 2],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 3],
    [1, 4, 5, 1, 10, 1, 7, 1, 3, 1, 23, 23, 23, 1],
]


# Стартовая позиция игрока (в северной половине, взгляд на север - к панораме)
PLAYER_START = {"x": 6.5, "y": 4.2, "angle": -math.pi / 2}


# Верхний пояс стен (z 1..2) строится из нижнего. Для каждого типа нижнего блока
# задаётся, какой блок верхнего пояса ставить над ним по умолчанию
# (UPPER_BY_LOWER). Нижние блоки без записи получают UPPER_DEFAULT; пустые
# клетки (0) остаются пустыми. Чтобы поменять верх над типом блока - правим здесь.
UPPER_DEFAULT = 21  # верхний тайл по умолчанию (бетон_01_up)
UPPER_BY_LOWER = {
    1: 21,  # бетон_01 -> бетон_01_up
    2: 22,  # бетон_02 -> бетон_02_up
    11: 21,  # окно_0 -> окно_0_up
    12: 13,  # окно_1 -> окно_1_up
    # 13: 18,  # окно_2 -> окно_2_up
    # 14: 19,  # окно_3 -> окно_3_up
    # 15: 20,  # окно_4 -> окно_4_up
}

# Ручные переопределения верхнего пояса: (строка, столбец) -> id верхнего тайла.
# Приоритетнее UPPER_BY_LOWER и работают даже над пустой нижней клеткой (для
# висящих блоков и перемычек). Сюда - точечные исключения.
UPPER_OVERRIDES = {
    (5, 6): 21,  # перемычка над проёмом двери (низ пустой)
    (3, 5): 21,  # ТЕСТ: висящий блок (низ пустой)
    (8, 11): 21,  # над консолью_0 - бетон_02
    # (0, 9): 2,  # над консолью_1 - бетон_02
}

# Кастомные тайлы пола на отдельных клетках: (строка, столбец) -> ключ текстуры
# (ключи см. в texture_paths, GameplayScene). Перекрывают обычный пол и его
# варианты; ловушки рисуются поверх этих клеток (динамически).
FLOOR_OVERRIDES = {
    (9, 10): "floor_outside",  # пол ниши с окном
    (9, 11): "floor_outside",
    (9, 12): "floor_outside",
}


def _build_upper_map(lower, upper_overrides={}):
    """Верхний пояс из нижнего: тайл по умолчанию (UPPER_BY_LOWER / UPPER_DEFAULT)
    плюс ручные переопределения UPPER_OVERRIDES (имеют приоритет)."""
    upper = [
        [UPPER_BY_LOWER.get(v, UPPER_DEFAULT) if v > 0 else 0 for v in row]
        for row in lower
    ]
    for (row, col), tile in upper_overrides.items():
        upper[row][col] = tile
    return upper


DEFAULT_MAP_UPPER = _build_upper_map(DEFAULT_MAP, UPPER_OVERRIDES)


# --- Объекты уровня 1: дата-таблицы (совместимо с дизайнером уровней) ---
# Загрузчики - в GameplayScene (_load_props / _load_interactables / _load_traps).
# Пути к спрайтам - относительно assets/textures/ (например "sprites/window.png").

# PROPS: (file, w, h, x, y, y_offset, solid, block_radius[, angle[, billboard]]).
# Сторона квадрата = max(w, h). block_radius=None -> дефолт OBJECT_BLOCK_RADIUS.
# angle (опц., радианы) - поворот плоской поверхности; billboard (опц.) -> спрайт
# всегда лицом к игроку (angle тогда не важен).
PROPS = [
    ("sprites/spr_plant.png", 0.62, 0.85, 10.5, 1.6, 0.0, True, None, None, True),
    ("sprites/spr_plant.png", 0.62, 0.85, 7.5, 1.6, 0.0, True, None, None, True),
    ("sprites/spr_bottles_1.png", 1.20, 0.82, 3.5, 8.5, 0.0, False, None),
    ("sprites/spr_garbage_1.png", 1.00, 1.05, 5.0, 9.5, 0.0, True, None),
    ("sprites/spr_garbage_1.png", 0.55, 0.34, 7.0, 7.7, 0.0, True, None),
    ("sprites/spr_wires_1.png", 0.85, 0.52, 9.5, 7.5, 1.0, False, None),
    # второй spr_wires_1 повёрнут на 90 градусов
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

# INTERACTABLES: {kind, x, y, angle, width, height, y_offset, cyclic, <файлы>}.
# kind: "button" (кнопка, id для ссылок; файлы off/on - иначе заглушка),
# "locked_door" (запираемая, button=id управляющей кнопки; файлы locked/closed/
# open), "door" (closed/open), "exit" (closed - по E завершает уровень).
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

# TRAPS: (x, y, intervals_ms, start_active). intervals_ms - список длительностей
# фаз в миллисекундах: фазы чередуются вкл/выкл начиная со start_active, список
# зациклен. Пример: [2000,1000,3500,2000] при True = 2с вкл,1с выкл,3.5с вкл,2с
# выкл, повтор. Текстуры ловушек - на стороне игры.
TRAPS = [
    (6, 3, [1500, 1500], True),
    (8, 9, [2000, 1000, 500, 3000], False),
]


# Уровень 1: карты + старт + объекты (дата-таблицы выше).
LEVEL1 = Level(
    lower_map=DEFAULT_MAP,
    upper_map=DEFAULT_MAP_UPPER,
    player_start=PLAYER_START,
    sky_mode=False,  # True - небо (параллакс); False - потолок
    time_limit=LEVEL_TIME_LIMIT,
    number=1,
    props=PROPS,
    interactables=INTERACTABLES,
    traps=TRAPS,
    floor_overrides=FLOOR_OVERRIDES,
)


# Уровень 2: лабиринт (рекурсивный бэктрекинг), >=15 клеток по длинной стороне,
# с тупиками. Старт в углу (0,0), выход - в дальнем углу; одна ловушка в проходе
# для примера. Сид фиксирован, чтобы уровень был стабильным.
_MAZE_GRID, _MAZE_START, _MAZE_ANGLE, _MAZE_EXIT = generate_maze(
    cw=9, ch=7, seed=42, wall_id=1
)

_MAZE_GRID[14][2] = 9
_MAZE_GRID[7][10] = 2
_MAZE_GRID[10][17] = 7
_MAZE_GRID[6][15] = 7

print("_MAZE_GRID")
print(_MAZE_GRID)


# PROPS: (file, w, h, x, y, y_offset, solid, block_radius[, angle[, billboard]]).
LEVEL2_PROPS = [
    ("sprites/spr_plant.png", 0.62, 0.85, 10.5, 1.6, 0.0, True, None, None, True),
    ("sprites/spr_plant.png", 0.62, 0.85, 7, 1.6, 0.0, True, None, None, True),
    ("sprites/spr_bottles_1.png", 1.20, 0.82, 3.5, 8.5, 0.0, False, None),
    # ("sprites/spr_window.png", 1, 1, 3, 6.5, 0, True, 0.4, math.radians(90)),
    ("sprites/spr_garbage_1.png", 0.80, 0.85, 3.3, 9.5, 0.0, True, 0.4, 0, True),  #
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
        # Выход - билборд (всегда лицом к игроку): удобно в лабиринте
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
)

_MAZE_GRID_2, _MAZE_START_2, _MAZE_ANGLE_2, _MAZE_EXIT_2 = generate_maze(
    cw=3, ch=40, seed=42, wall_id=2
)

print("_MAZE_GRID 2")
print(_MAZE_GRID_2)
_MAZE_GRID_2[80][5] = 1

LEVEL3 = Level(
    lower_map=_MAZE_GRID_2,
    upper_map=_build_upper_map(_MAZE_GRID_2),
    player_start={"x": _MAZE_START_2[0], "y": _MAZE_START_2[1], "angle": _MAZE_ANGLE_2},
    sky_mode=True,
    time_limit=120.0,
    number=3,
    props=[],
    interactables=[
        # Выход - билборд (всегда лицом к игроку): удобно в лабиринте
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
    traps=[(5, 3, [1500, 1500], True)],
    floor_overrides={},
)

LEVEL4_MAP = [
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

LEVEL4_UPPER_OVERRIDES = {
    (6, 3): 21,
    (16, 0): 21,
}

LEVEL4_FLOOR_OVERRIDES = {
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

LEVEL4_START = {"x": 1.5, "y": 1.5, "angle": 90}

# PROPS: (file, w, h, x, y, y_offset, solid, block_radius)
LEVEL4_PROPS = [
    ("sprites/spr_window.png", 1, 1, 3, 6.5, 0, True, 0.4, math.radians(90)),
    ("walls/wall_concrete_01_up.png", 1, 1, 3, 6.5, 1, True, 0.4, math.radians(90)),
    ("sprites/spr_window.png", 1, 1, 1, 16.5, 0, True, 0.4, math.radians(90)),
    ("walls/wall_concrete_01_up.png", 1, 1, 1, 16.5, 1, True, 0.4, math.radians(90)),
]

LEVEL4_INTERACTABLES = [
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

# TRAPS: (x, y, on_ticks, off_ticks, start_active)
LEVEL4_TRAPS = [
    (2, 4, [90, 90], True),
    (1, 6, [90, 1000], True),
    (2, 6, [90, 90], True),
    (1, 4, [90, 90], True),
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

LEVEL4 = Level(
    lower_map=LEVEL4_MAP,
    upper_map=_build_upper_map(LEVEL4_MAP, LEVEL4_UPPER_OVERRIDES),
    player_start=LEVEL4_START,
    sky_mode=True,  # True - небо (параллакс); False - потолок
    time_limit=45,
    number=4,
    props=LEVEL4_PROPS,
    interactables=LEVEL4_INTERACTABLES,
    traps=LEVEL4_TRAPS,
    floor_overrides=LEVEL4_FLOOR_OVERRIDES,
)
# Список уровней (по порядку прохождения) и алиас на первый.
LEVELS = [LEVEL1, LEVEL2, LEVEL3, LEVEL4]
DEFAULT_LEVEL = LEVEL1
