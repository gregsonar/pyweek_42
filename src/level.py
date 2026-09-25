# src/level.py
"""Данные уровня, сгруппированные в один объект."""

from dataclasses import dataclass, field


@dataclass
class Level:
    """
    Один уровень: карты стен, старт игрока, режим верха и объекты.

    Режим верха (потолок или небо) - свойство уровня, а не глобальная
    настройка движка: разные уровни могут его выбирать по-своему. Объекты
    (props/interactables/traps) и floor_overrides - дата-таблицы уровня
    (совместимы с дизайнером уровней), грузятся загрузчиками GameplayScene.
    """
    lower_map: list           # нижний пояс стен (id клеток)
    upper_map: list           # верхний пояс стен (id клеток), та же форма
    player_start: dict        # {"x": ..., "y": ..., "angle": ...}
    sky_mode: bool = False    # True - небо (параллакс), False - потолок
    time_limit: float = 90.0  # лимит времени на одну попытку (сек)
    number: int = 1           # номер уровня (для строки HUD)
    props: list = field(default_factory=list)          # декор (дата-таблица)
    interactables: list = field(default_factory=list)  # объекты (дата-таблица)
    traps: list = field(default_factory=list)          # ловушки (дата-таблица)
    floor_overrides: dict = field(default_factory=dict)  # кастомный пол по клеткам
