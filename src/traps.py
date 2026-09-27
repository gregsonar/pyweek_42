# src/traps.py
"""Ловушки: циклическое вкл/выкл по списку интервалов.

Два вида: напольная (`Trap`, подменяет тайл пола) и спрайтовая (`BatteryTrap`,
вертикальный спрайт). Общая логика цикла - в базовом `_CyclicTrap`.
"""

from . import config


class _CyclicTrap:
    """
    Общий цикл вкл/выкл по списку длительностей фаз в миллисекундах.

    Фазы чередуются вкл/выкл, начиная со `start_active`, список зациклен.
    Пример: [2000, 1000, 3500, 2000] при start_active=True -> 2 с вкл, 1 с выкл,
    3.5 с вкл, 2 с выкл, затем повтор. step() вызывается на мировом тике (когда
    мир идёт); при остановке времени ловушка замирает. Длительности переводятся
    в тики (TICK_RATE), минимум 1 тик на фазу.
    """

    def __init__(self, intervals_ms, start_active=True):
        self._intervals = [
            max(1, round(ms / 1000.0 * config.TICK_RATE)) for ms in intervals_ms
        ]
        self.start_active = start_active
        self.active = start_active
        self._index = 0  # индекс текущего интервала
        self._phase_ticks = 0  # тиков в текущей фазе

    def reset(self):
        """Вернуть в исходную фазу (при рестарте уровня)."""
        self.active = self.start_active
        self._index = 0
        self._phase_ticks = 0

    def step(self):
        """Один мировой тик: смена вкл/выкл по концу текущего интервала."""
        if not self._intervals:
            return
        self._phase_ticks += 1
        if self._phase_ticks >= self._intervals[self._index]:
            self._index = (self._index + 1) % len(self._intervals)
            self._phase_ticks = 0
            self.active = not self.active


class Trap(_CyclicTrap):
    """
    Напольная ловушка: подменяет тайл пола в клетке (x=столбец, y=строка).
    Активная текстура - floor_trap_enabled, пассивная - её обесцвеченная версия.
    Урон при стоянии на активной клетке (см. GameplayScene._apply_trap_damage).
    """

    def __init__(self, x, y, tex_on, tex_off, intervals_ms, start_active=True):
        super().__init__(intervals_ms, start_active)
        self.x = int(x)  # столбец
        self.y = int(y)  # строка
        self.tex_on = tex_on
        self.tex_off = tex_off

    @property
    def cell(self):
        """Клетка (строка, столбец) - ключ подмены тайла пола в рендере."""
        return (self.y, self.x)

    @property
    def texture(self):
        """Текущая текстура тайла (активная или пассивная)."""
        return self.tex_on if self.active else self.tex_off


class BatteryTrap(_CyclicTrap):
    """
    Спрайтовая ловушка: те же циклы, что у напольной, но стоит вертикальным
    спрайтом (on/off текстуры). Проход НЕ блокирует (solid=False), но наносит
    урон при касании клетки в состоянии on (логика урона - как у напольной,
    по клетке). Реализует интерфейс спрайта для render_sprites.
    """

    def __init__(self, x, y, tex_on, tex_off, intervals_ms, start_active=True,
                 angle=0.0, width=1.0, height=1.0, y_offset=0.0, billboard=True):
        super().__init__(intervals_ms, start_active)
        self.col = int(x)  # столбец
        self.row = int(y)  # строка
        self.tex_on = tex_on
        self.tex_off = tex_off
        # Интерфейс спрайта (мировая позиция - центр клетки)
        self.x = self.col + 0.5
        self.y = self.row + 0.5
        self.angle = angle
        self.width = width
        self.height = height
        self.y_offset = y_offset
        self.billboard = billboard
        self.solid = False  # проход не блокирует
        self.highlight_sprite = None  # не подсвечивается

    @property
    def cell(self):
        """Клетка (строка, столбец) - для проверки урона по клетке игрока."""
        return (self.row, self.col)

    @property
    def sprite(self):
        """Текущий спрайт (активный или пассивный) - для render_sprites."""
        return self.tex_on if self.active else self.tex_off
