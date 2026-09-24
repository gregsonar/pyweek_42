# src/traps.py
"""Ловушки на полу: циклическое вкл/выкл по списку интервалов."""

from . import config


class Trap:
    """
    Ловушка в клетке пола. Фазы задаются списком длительностей в миллисекундах
    (`intervals_ms`); фазы чередуются вкл/выкл, начиная со `start_active`, список
    зациклен. Пример: [2000, 1000, 3500, 2000] при start_active=True -> 2 с вкл,
    1 с выкл, 3.5 с вкл, 2 с выкл, затем повтор.

    step() вызывается на мировом тике (когда мир идёт); при остановке времени
    игроком ловушка замирает вместе с миром. Длительности переводятся в тики
    (TICK_RATE), минимум 1 тик на фазу.

    Координаты - целочисленная клетка (x = столбец, y = строка), как в карте
    (map[y][x]). Активная текстура - floor_trap_enabled, пассивная - её
    обесцвеченная версия (временно, пока одна текстура).
    """

    def __init__(self, x, y, tex_on, tex_off, intervals_ms, start_active=True):
        self.x = int(x)  # столбец
        self.y = int(y)  # строка
        self.tex_on = tex_on
        self.tex_off = tex_off
        # Длительности фаз в тиках (из миллисекунд), минимум 1 тик.
        self._intervals = [
            max(1, round(ms / 1000.0 * config.TICK_RATE)) for ms in intervals_ms
        ]
        self.start_active = start_active
        self.active = start_active
        self._index = 0  # индекс текущего интервала в списке
        self._phase_ticks = 0  # тиков в текущей фазе

    def reset(self):
        """Вернуть ловушку в исходную фазу (при рестарте уровня)."""
        self.active = self.start_active
        self._index = 0
        self._phase_ticks = 0

    def step(self):
        """Один мировой тик: продвижение фазы; смена вкл/выкл по концу интервала."""
        if not self._intervals:
            return
        self._phase_ticks += 1
        if self._phase_ticks >= self._intervals[self._index]:
            self._index = (self._index + 1) % len(self._intervals)
            self._phase_ticks = 0
            self.active = not self.active

    @property
    def cell(self):
        """Клетка (строка, столбец) - ключ для подмены тайла пола в рендере."""
        return (self.y, self.x)

    @property
    def texture(self):
        """Текущая текстура тайла (активная или пассивная)."""
        return self.tex_on if self.active else self.tex_off
