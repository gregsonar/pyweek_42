import random

from . import config

class Timer:

    def __init__(self, tick_rate=None, max_ticks_per_frame=None):
        rate = tick_rate if tick_rate is not None else config.TICK_RATE
        self.tick_dt = 1.0 / rate
        self.max_ticks_per_frame = (
            max_ticks_per_frame
            if max_ticks_per_frame is not None
            else config.MAX_TICKS_PER_FRAME
        )
        self.tick = 0
        self.last_frame_dt = 0.0
        self._accum = 0.0

    def update(self, dt):
        self.last_frame_dt = dt
        self._accum += dt
        n = int(self._accum / self.tick_dt)
        if n > self.max_ticks_per_frame:
            n = self.max_ticks_per_frame
            self._accum = 0.0
        else:
            self._accum -= n * self.tick_dt
        self.tick += n
        return n

    @property
    def seconds(self):
        return self.tick * self.tick_dt

STATE_NORMAL = "normal"
STATE_WORLD_FROZEN = "world_frozen"
STATE_PLAYER_FROZEN = "player_frozen"

class TimeController:

    def __init__(self, timer, rng=None):
        self.timer = timer
        self._rng = rng if rng is not None else random
        self.state = STATE_NORMAL
        self.budget_max = config.FREEZE_BUDGET_TICKS
        self.budget = self.budget_max
        self.debt = 0
        self._repay_at = None
        self._freeze_left = 0

        self._events = []

    @property
    def world_running(self):
        return self.state != STATE_WORLD_FROZEN

    @property
    def player_running(self):
        return self.state != STATE_PLAYER_FROZEN

    def _set_state(self, new_state):
        old = self.state
        if new_state == old:
            return
        self.state = new_state
        if new_state == STATE_WORLD_FROZEN:
            self._events.append("world_freeze")
        elif old == STATE_WORLD_FROZEN and new_state == STATE_NORMAL:
            self._events.append("world_unfreeze")
        elif new_state == STATE_PLAYER_FROZEN:
            self._events.append("player_freeze")
        elif old == STATE_PLAYER_FROZEN and new_state == STATE_NORMAL:
            self._events.append("player_unfreeze")

    def toggle_freeze(self):
        if self.state == STATE_WORLD_FROZEN:
            self._set_state(STATE_NORMAL)
        elif self.state == STATE_NORMAL and self.budget > 0:
            self._set_state(STATE_WORLD_FROZEN)

    def step(self):
        if self.state == STATE_WORLD_FROZEN:
            self.budget -= 1
            self.debt += 1
            if self.budget <= 0:
                self.budget = 0
                self._set_state(STATE_NORMAL)
        elif self.state == STATE_NORMAL:
            if self.debt > 0:
                if self._repay_at is None:
                    self._schedule_repayment()
                elif self.timer.tick >= self._repay_at:
                    self._begin_repayment()
            else:
                self._repay_at = None
        elif self.state == STATE_PLAYER_FROZEN:
            self._freeze_left -= 1
            self.debt -= 1
            self.budget = min(self.budget_max, self.budget + 1)
            if self._freeze_left <= 0 or self.debt <= 0:
                self.debt = max(0, self.debt)
                self._set_state(STATE_NORMAL)
                self._repay_at = None

    def _schedule_repayment(self):
        delay = self._rng.randint(config.REPAY_INTERVAL_MIN, config.REPAY_INTERVAL_MAX)
        self._repay_at = self.timer.tick + delay

    def _begin_repayment(self):
        self._freeze_left = self.debt
        self._set_state(STATE_PLAYER_FROZEN)
        self._repay_at = None

    def drain_events(self):
        events = self._events
        self._events = []
        return events

    @property
    def ticks_to_repay(self):
        if self._repay_at is None:
            return None
        return max(0, self._repay_at - self.timer.tick)

    @property
    def budget_fraction(self):
        if self.budget_max <= 0:
            return 0.0
        return self.budget / self.budget_max
