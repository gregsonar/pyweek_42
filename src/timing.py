# src/timing.py
"""Учёт времени в тиках и механика заёма/возврата времени (Borrowed Time)."""

import random

from . import config


class Timer:
    """
    Чистый учёт времени: фиксированный логический шаг + аккумулятор dt.

    Отвязывает логику (фиксированная частота тиков) от рендера (переменный FPS),
    поэтому скорость игры одинакова на разном железе. update() накапливает
    реальное время кадра и отдаёт число логических тиков к отработке.
    """

    def __init__(self, tick_rate=None, max_ticks_per_frame=None):
        rate = tick_rate if tick_rate is not None else config.TICK_RATE
        self.tick_dt = 1.0 / rate  # длительность одного тика в секундах
        self.max_ticks_per_frame = (
            max_ticks_per_frame
            if max_ticks_per_frame is not None
            else config.MAX_TICKS_PER_FRAME
        )
        self.tick = 0  # монотонный счётчик логических тиков
        self.last_frame_dt = 0.0  # время последнего кадра (для HUD/диагностики)
        self._accum = 0.0  # накопленное реальное время

    def update(self, dt):
        """
        Накопить время кадра и вернуть число логических тиков к отработке.
        Ограничено max_ticks_per_frame (защита от "спирали смерти" при лаге).
        """
        self.last_frame_dt = dt
        self._accum += dt
        n = int(self._accum / self.tick_dt)
        if n > self.max_ticks_per_frame:
            n = self.max_ticks_per_frame
            self._accum = 0.0  # накопленное сверх лимита отбрасываем
        else:
            self._accum -= n * self.tick_dt
        self.tick += n
        return n

    @property
    def seconds(self):
        """Прошедшее логическое время в секундах."""
        return self.tick * self.tick_dt


# Состояния времени
STATE_NORMAL = "normal"  # мир и игрок идут
STATE_WORLD_FROZEN = "world_frozen"  # игрок остановил мир (способность)
STATE_PLAYER_FROZEN = "player_frozen"  # мир идёт, игрок заморожен (возврат долга)


class TimeController:
    """
    Механика Borrowed Time: заём (остановка мира) и возврат (заморозка игрока).

    Считает в тиках Timer. Наружу отдаёт флаги world_running / player_running
    (их читают сущности мира и контроллер игрока) и запросы состояния для HUD.

    Модель:
    - тоггл-способность останавливает мир, пока есть бюджет; каждый тик заморозки
      мира тратит бюджет и копит долг;
    - при наличии долга в NORMAL планируется случайный интервал возврата; когда
      он наступает, игрок замораживается на время, пропорциональное долгу, мир в
      это время идёт; долг гасится, бюджет восстанавливается.
    """

    def __init__(self, timer, rng=None):
        self.timer = timer
        self._rng = rng if rng is not None else random
        self.state = STATE_NORMAL
        self.budget_max = config.FREEZE_BUDGET_TICKS
        self.budget = self.budget_max  # остаток бюджета заморозки (тики)
        self.debt = 0  # накопленный долг времени (тики)
        self._repay_at = None  # тик, на котором сработает возврат долга
        self._freeze_left = 0  # осталось тиков заморозки игрока

    # --- флаги для остального кода ---
    @property
    def world_running(self):
        """Идёт ли время мира (враги/ловушки)."""
        return self.state != STATE_WORLD_FROZEN

    @property
    def player_running(self):
        """Может ли игрок двигаться/взаимодействовать."""
        return self.state != STATE_PLAYER_FROZEN

    def _set_state(self, new_state):
        """Сменить состояние и залогировать переход в консоль (пока нет HUD)."""
        old = self.state
        if new_state == old:
            return
        self.state = new_state
        if new_state == STATE_WORLD_FROZEN:
            print("time stopped for world", flush=True)
        elif old == STATE_WORLD_FROZEN and new_state == STATE_NORMAL:
            print("time resumed for world", flush=True)
        elif new_state == STATE_PLAYER_FROZEN:
            print("time stopped for player", flush=True)
        elif old == STATE_PLAYER_FROZEN and new_state == STATE_NORMAL:
            print("time resumed for player", flush=True)

    # --- ввод игрока ---
    def toggle_freeze(self):
        """Способность: вкл/выкл остановку мира (тоггл). В PLAYER_FROZEN недоступна."""
        if self.state == STATE_WORLD_FROZEN:
            self._set_state(STATE_NORMAL)
        elif self.state == STATE_NORMAL and self.budget > 0:
            self._set_state(STATE_WORLD_FROZEN)

    # --- один логический тик ---
    def step(self):
        if self.state == STATE_WORLD_FROZEN:
            self.budget -= 1
            self.debt += 1
            if self.budget <= 0:
                self.budget = 0
                self._set_state(STATE_NORMAL)  # бюджет кончился - мир снова идёт
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
            self.budget = min(self.budget_max, self.budget + 1)  # восстановление
            if self._freeze_left <= 0 or self.debt <= 0:
                self.debt = max(0, self.debt)
                self._set_state(STATE_NORMAL)
                self._repay_at = None

    def _schedule_repayment(self):
        """Запланировать возврат долга на случайный тик в заданных пределах."""
        delay = self._rng.randint(
            config.REPAY_INTERVAL_MIN, config.REPAY_INTERVAL_MAX
        )
        self._repay_at = self.timer.tick + delay

    def _begin_repayment(self):
        """Начать возврат: заморозить игрока на время, пропорциональное долгу."""
        self._freeze_left = self.debt
        self._set_state(STATE_PLAYER_FROZEN)
        self._repay_at = None

    # --- запросы для будущего HUD ---
    @property
    def ticks_to_repay(self):
        """Тиков до возврата долга, или None если не запланировано."""
        if self._repay_at is None:
            return None
        return max(0, self._repay_at - self.timer.tick)

    @property
    def budget_fraction(self):
        """Доля оставшегося бюджета заморозки [0..1] - для шкалы в HUD."""
        if self.budget_max <= 0:
            return 0.0
        return self.budget / self.budget_max
