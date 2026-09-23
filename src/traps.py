# src/traps.py
"""Ловушки на полу: циклическое вкл/выкл по мировым тикам."""


class Trap:
    """
    Ловушка в клетке пола. Циклит: on_ticks тиков включена, off_ticks выключена.
    step() вызывается на мировом тике (когда мир идёт); при остановке времени
    игроком ловушка замирает вместе с миром.

    Координаты - целочисленная клетка (x = столбец, y = строка), как в карте
    (map[y][x]). Активная текстура - floor_trap_enabled, пассивная - её
    обесцвеченная версия (временно, пока одна текстура).
    """

    def __init__(self, x, y, tex_on, tex_off, on_ticks, off_ticks,
                 start_active=True):
        self.x = int(x)  # столбец
        self.y = int(y)  # строка
        self.tex_on = tex_on
        self.tex_off = tex_off
        self.on_ticks = on_ticks
        self.off_ticks = off_ticks
        self.start_active = start_active
        self.active = start_active
        self._phase_ticks = 0  # тиков в текущей фазе

    def reset(self):
        """Вернуть ловушку в исходную фазу (при рестарте уровня)."""
        self.active = self.start_active
        self._phase_ticks = 0

    def step(self):
        """Один мировой тик: продвижение фазы вкл/выкл."""
        self._phase_ticks += 1
        limit = self.on_ticks if self.active else self.off_ticks
        if self._phase_ticks >= limit:
            self.active = not self.active
            self._phase_ticks = 0

    @property
    def cell(self):
        """Клетка (строка, столбец) - ключ для подмены тайла пола в рендере."""
        return (self.y, self.x)

    @property
    def texture(self):
        """Текущая текстура тайла (активная или пассивная)."""
        return self.tex_on if self.active else self.tex_off
