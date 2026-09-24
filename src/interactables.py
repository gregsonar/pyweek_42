# src/interactables.py
"""
Интерактивные объекты: кнопки, двери и т. п.

Объект - билборд-спрайт с позицией и набором состояний. При приближении,
нахождении в поле зрения и прямой видимости объект может быть подсвечен;
при использовании он переходит в следующее состояние.
"""

from . import config
from .utils import camera_space, has_line_of_sight


class InteractState:
    """Одно состояние объекта: спрайт, твёрдость и (задел) звук."""

    __slots__ = ("sprite", "solid", "sound")

    def __init__(self, sprite, solid=False, sound=None):
        self.sprite = sprite  # numpy RGBA (size, size, 4), индексация [x, y]
        self.solid = solid    # перекрывает ли проход игроку
        self.sound = sound    # ключ/путь звука; задел под следующий шаг


class Interactable:
    """Интерактивный объект-билборд с состояниями."""

    def __init__(self, x, y, states, angle=0.0, width=1.0, interact_radius=None,
                 height=1.0, y_offset=0.0, cyclic=True, highlight_sprite=None,
                 block_radius=None, billboard=False):
        self.x = x
        self.y = y
        self.states = states
        self.state = 0
        # Радиус блокировки прохода (если solid). None -> config.OBJECT_BLOCK_RADIUS.
        # Для крупных объектов задаётся больше, чтобы игрок не влезал в спрайт.
        self.block_radius = block_radius
        # Ориентация поверхности:
        #   billboard=False (по умолчанию) - плоская поверхность, зафиксированная
        #     в пространстве углом angle (не поворачивается за игроком);
        #   billboard=True - плоскость всегда параллельна экрану (лицом к игроку),
        #     angle игнорируется. Для мебели/декора обычно нужен билборд, для
        #     настенных объектов (кнопки/двери) - фиксированный.
        self.billboard = billboard
        self.angle = angle
        self.width = width
        self.interact_radius = (interact_radius if interact_radius is not None
                                else config.INTERACT_RADIUS)
        self.height = height          # высота поверхности в мировых единицах
        self.y_offset = y_offset      # подъём над полом в мировых единицах
        self.cyclic = cyclic          # циклическое переключение состояний
        # Если задан, рисуется вместо основного спрайта при подсветке.
        self.highlight_sprite = highlight_sprite

    @property
    def current(self):
        return self.states[self.state]

    @property
    def sprite(self):
        return self.current.sprite

    @property
    def solid(self):
        return self.current.solid

    def use(self):
        """
        Использовать объект: переход в следующее состояние.
        cyclic=True - по кругу, cyclic=False - до последнего с фиксацией.
        Возвращает новое состояние (пригодится для звука на следующем шаге).
        """
        if self.cyclic:
            self.state = (self.state + 1) % len(self.states)
        else:
            self.state = min(self.state + 1, len(self.states) - 1)
        return self.current


class ButtonLink:
    """
    Связь кнопки с дверьми: кнопка РАЗБЛОКИРУЕТ двери (не открывает их сразу).

    Пока кнопка в состоянии open_state (например, зелёном), дверь разблокирована:
    становится обычным E-объектом (её открывает игрок по E у самой двери). Иначе
    дверь заперта (состояние locked_index) и по E не используется.

    Состояния управляемой двери (по индексам):
      locked_index   (0) - заперта: solid, не подсвечивается/не по E;
      unlocked_index (1) - закрыта, но разблокирована: solid, открывается по E;
      open_index     (2) - открыта: не solid (управляется игроком по E).

    Удобно собирать уровни: одна кнопка -> список управляемых дверей.
    """

    def __init__(self, button, doors, open_state=1,
                 locked_index=0, unlocked_index=1):
        self.button = button
        self.doors = list(doors)
        self.open_state = open_state        # состояние кнопки, снимающее блокировку
        self.locked_index = locked_index    # индекс "заперта"
        self.unlocked_index = unlocked_index  # индекс "закрыта, разблокирована"

    def sync(self):
        """Обновить блокировку дверей по состоянию кнопки (каждый кадр)."""
        if self.button.state == self.open_state:
            # разблокировать: только запертые переводим в "закрыта" (открытую не
            # трогаем - её состоянием управляет игрок)
            for door in self.doors:
                if door.state == self.locked_index:
                    door.state = self.unlocked_index
        else:
            # запереть все связанные двери (закрывает открытую)
            for door in self.doors:
                door.state = self.locked_index

    def is_unlocked(self, door):
        """Разблокирована ли дверь (не заперта)."""
        return door.state != self.locked_index


def select_highlight(objects, px, py, pa, game_map):
    """
    Выбирает единственный подсвечиваемый объект.

    Кандидат должен быть: в пределах interact_radius, перед камерой,
    в поле зрения (|theta| <= FOV) и с прямой видимостью (нет стен между).
    Из кандидатов берётся ближайший к центру экрана (минимальный |theta|),
    при равенстве - ближайший по расстоянию.
    """
    best = None
    best_key = None
    for obj in objects:
        dist, theta, forward = camera_space(px, py, pa, obj.x, obj.y)
        if forward <= config.SPRITE_NEAR_CLIP:
            continue
        if dist > obj.interact_radius:
            continue
        if abs(theta) > config.FOV:
            continue
        if not has_line_of_sight(game_map, px, py, obj.x, obj.y):
            continue

        key = (abs(theta), dist)
        if best is None or key < best_key:
            best = obj
            best_key = key
    return best
