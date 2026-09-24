# src/hud.py
"""HUD: таймер, здоровье, маска урона и строка текста поверх сцены.

Рисуется в разрешении окна (после масштабирования сцены), чтобы текст и
иконки были чёткими. Своё состояние (сообщение, вспышка урона) HUD хранит
сам; игровые данные (HP, остаток времени, номер уровня) получает в draw().
"""

import math

import pygame as pg

from . import config
from .i18n import tr


class Hud:
    """Интерфейс поверх сцены."""

    def __init__(self, language):
        self.language = language

        # Шрифты. Текст и таймер - шрифт с кириллицей (для русского языка).
        # Иконки HP - отдельный символьный шрифт с глифами ♥/♡ (в кириллических
        # шрифтах этих символов обычно нет). Списки запасных - в config.
        self.font_timer = pg.font.SysFont(
            config.HUD_FONT_NAME, config.HUD_TIMER_SIZE, bold=True
        )
        self.font_text = pg.font.SysFont(
            config.HUD_FONT_NAME, config.HUD_TEXT_SIZE, bold=True
        )
        self.font_hp = pg.font.SysFont(config.HUD_SYMBOL_FONT_NAME, config.HUD_HP_SIZE)

        # Полноэкранные поверхности масок (переиспользуются между кадрами):
        # красная - урон, синяя - заморозка игрока (возврат долга)
        self._flash_surf = pg.Surface((config.WIN_WIDTH, config.WIN_HEIGHT))
        self._flash_surf.fill(config.DAMAGE_FLASH_COLOR)
        self._freeze_surf = pg.Surface((config.WIN_WIDTH, config.WIN_HEIGHT))
        self._freeze_surf.fill(config.FREEZE_MASK_COLOR)

        # Состояние
        self.damage_flash = 0.0  # интенсивность вспышки урона (0..1)
        self._freeze_level = 0.0  # плавная видимость синей маски (0..1)
        self._anim_t = 0.0  # накопитель времени для пульсации
        self._msg_key = None  # ключ сообщения (i18n) или None -> номер уровня
        self._msg_fmt = {}  # параметры подстановки для сообщения
        self._msg_time_left = 0.0  # сколько ещё показывать сообщение (сек)

    def set_language(self, language):
        """Сменить язык интерфейса."""
        self.language = language

    def set_message(self, key, seconds=None, **fmt):
        """Показать сообщение (ключ i18n) вместо номера уровня.

        seconds=None - показывать до следующего сообщения/сброса.
        """
        self._msg_key = key
        self._msg_fmt = fmt
        self._msg_time_left = math.inf if seconds is None else seconds

    def clear_message(self):
        """Убрать сообщение (строка вернётся к номеру уровня)."""
        self._msg_key = None
        self._msg_fmt = {}
        self._msg_time_left = 0.0

    def flash_damage(self):
        """Зажечь маску урона на полную (дальше гаснет в update)."""
        self.damage_flash = 1.0

    def reset(self):
        """Сброс к состоянию по умолчанию (при рестарте уровня)."""
        self.damage_flash = 0.0
        self._freeze_level = 0.0
        self.clear_message()

    def update(self, dt, player_frozen=False):
        """Анимация масок и истечение сообщения. dt - секунды кадра.

        player_frozen - идёт ли сейчас заморозка игрока (синяя маска).
        """
        self._anim_t += dt
        # Затухание вспышки урона
        if self.damage_flash > 0.0:
            self.damage_flash = max(
                0.0, self.damage_flash - config.DAMAGE_FLASH_FADE * dt
            )
        # Плавное появление/угасание синей маски заморозки игрока
        target = 1.0 if player_frozen else 0.0
        step = config.FREEZE_MASK_FADE * dt
        if self._freeze_level < target:
            self._freeze_level = min(target, self._freeze_level + step)
        elif self._freeze_level > target:
            self._freeze_level = max(target, self._freeze_level - step)
        # Истечение сообщения
        if self._msg_key is not None and self._msg_time_left != math.inf:
            self._msg_time_left -= dt
            if self._msg_time_left <= 0.0:
                self.clear_message()

    # --- отрисовка ---

    def _blit_text(self, surface, font, text, color, anchor, pos):
        """Текст с тенью. anchor - имя атрибута Rect (midtop/topright/...)."""
        label = font.render(text, True, color)
        shadow = font.render(text, True, config.HUD_SHADOW_COLOR)
        rect = label.get_rect(**{anchor: pos})
        surface.blit(shadow, rect.move(1, 1))
        surface.blit(label, rect)
        return rect

    def draw(
        self,
        surface,
        *,
        time_left,
        hp,
        max_hp,
        level_number,
        world_frozen=False,
        budget_fraction=1.0,
    ):
        """Отрисовать HUD поверх сцены на surface (разрешение окна)."""
        w = surface.get_width()
        h = surface.get_height()
        m = config.HUD_MARGIN

        # 1. Маски (под текстом HUD): красная - урон, синяя пульсирующая -
        # заморозка игрока (возврат долга)
        if self.damage_flash > 0.0:
            alpha = int(self.damage_flash * config.DAMAGE_FLASH_MAX_ALPHA)
            self._flash_surf.set_alpha(alpha)
            surface.blit(self._flash_surf, (0, 0))
        if self._freeze_level > 0.0:
            pulse = 0.5 + 0.5 * math.sin(
                2.0 * math.pi * config.FREEZE_MASK_PULSE_HZ * self._anim_t
            )
            lo, hi = config.FREEZE_MASK_MIN_ALPHA, config.FREEZE_MASK_MAX_ALPHA
            alpha = int(self._freeze_level * (lo + (hi - lo) * pulse))
            if alpha > 0:
                self._freeze_surf.set_alpha(alpha)
                surface.blit(self._freeze_surf, (0, 0))

        # 2. Таймер (верх по центру), формат M:SS; при остановленном мире -
        # другим цветом (индикация, что отсчёт заморожен игроком).
        secs = max(0, int(math.ceil(time_left)))
        timer_text = "%d:%02d" % (secs // 60, secs % 60)
        timer_color = (
            config.HUD_TIMER_FROZEN_COLOR if world_frozen else config.HUD_COLOR
        )
        timer_rect = self._blit_text(
            surface, self.font_timer, timer_text, timer_color, "midtop", (w // 2, m)
        )

        # 2b. Шкала баланса заёма (полоса под таймером): длина по остатку бюджета,
        # сужается симметрично к центру до BUDGET_BAR_MIN_WIDTH при нуле
        frac = max(0.0, min(1.0, budget_fraction))
        bar_len = config.BUDGET_BAR_MIN_WIDTH + int(
            (config.BUDGET_BAR_WIDTH - config.BUDGET_BAR_MIN_WIDTH) * frac
        )
        bar = pg.Rect(0, 0, bar_len, config.BUDGET_BAR_HEIGHT)
        bar.midtop = (w // 2, timer_rect.bottom + config.BUDGET_BAR_GAP)
        # тёмная подложка на 1px по кругу - для контраста поверх сцены
        surface.fill(config.HUD_SHADOW_COLOR, bar.inflate(2, 2))
        surface.fill(config.BUDGET_BAR_COLOR, bar)

        # 3. Строка текста (верх справа): сообщение или номер уровня
        if self._msg_key is not None:
            line = tr(self._msg_key, self.language, **self._msg_fmt)
        else:
            line = tr("level", self.language, n=level_number)
        self._blit_text(
            surface, self.font_text, line, config.HUD_COLOR, "topright", (w - m, m)
        )

        # 4. Здоровье (низ слева): ♥ за оставшийся HP, ♡ за потерянный
        hp = max(0, min(hp, max_hp))
        hearts_full = "♥" * hp
        hearts_lost = "♡" * (max_hp - hp)
        x, y = m, h - m
        if hearts_full:
            rect = self._blit_text(
                surface,
                self.font_hp,
                hearts_full,
                config.HUD_HP_FULL_COLOR,
                "bottomleft",
                (x, y),
            )
            x = rect.right
        if hearts_lost:
            self._blit_text(
                surface,
                self.font_hp,
                hearts_lost,
                config.HUD_HP_LOST_COLOR,
                "bottomleft",
                (x, y),
            )
