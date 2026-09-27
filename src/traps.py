from . import config

class _CyclicTrap:

    def __init__(self, intervals_ms, start_active=True):
        self._intervals = [
            max(1, round(ms / 1000.0 * config.TICK_RATE)) for ms in intervals_ms
        ]
        self.start_active = start_active
        self.active = start_active
        self._index = 0
        self._phase_ticks = 0

    def reset(self):
        self.active = self.start_active
        self._index = 0
        self._phase_ticks = 0

    def step(self):
        if not self._intervals:
            return
        self._phase_ticks += 1
        if self._phase_ticks >= self._intervals[self._index]:
            self._index = (self._index + 1) % len(self._intervals)
            self._phase_ticks = 0
            self.active = not self.active

class Trap(_CyclicTrap):

    def __init__(self, x, y, tex_on, tex_off, intervals_ms, start_active=True):
        super().__init__(intervals_ms, start_active)
        self.x = int(x)
        self.y = int(y)
        self.tex_on = tex_on
        self.tex_off = tex_off

    @property
    def cell(self):
        return (self.y, self.x)

    @property
    def texture(self):
        return self.tex_on if self.active else self.tex_off

class BatteryTrap(_CyclicTrap):

    def __init__(self, x, y, tex_on, tex_off, intervals_ms, start_active=True,
                 angle=0.0, width=1.0, height=1.0, y_offset=0.0, billboard=True):
        super().__init__(intervals_ms, start_active)
        self.col = int(x)
        self.row = int(y)
        self.tex_on = tex_on
        self.tex_off = tex_off

        self.x = self.col + 0.5
        self.y = self.row + 0.5
        self.angle = angle
        self.width = width
        self.height = height
        self.y_offset = y_offset
        self.billboard = billboard
        self.solid = False
        self.highlight_sprite = None

    @property
    def cell(self):
        return (self.row, self.col)

    @property
    def sprite(self):
        return self.tex_on if self.active else self.tex_off
