# src/audio.py
"""Звук: тонкий менеджер эффектов с хуками по имени.

Каркас на будущее: логические имена звуков -> файлы в assets/sounds. Файлов
может ещё не быть - тогда play() просто ничего не делает. Если аудио недоступно
(нет устройства/микшер не инициализировался), звук молча отключается.
"""

import os
import sys

import pygame as pg

_SOUNDS_DIR = "assets/sounds"

# Логические имена -> имена файлов. Файлы добавим позже; отсутствующие
# пропускаются при загрузке, а play() по такому имени - no-op.
SOUND_FILES = {
    "ui_move": "ui_move.wav",
    "ui_select": "ui_select.wav",
    "hurt": "hurt.wav",
    "freeze": "freeze.wav",
    "unfreeze": "unfreeze.wav",
}


class SoundManager:
    """Загружает доступные звуки и проигрывает их по логическому имени."""

    def __init__(self):
        self._sounds = {}
        self._enabled = False
        try:
            pg.mixer.init()
            self._enabled = True
        except pg.error as exc:
            print("audio disabled: %s" % exc, file=sys.stderr, flush=True)
        if self._enabled:
            self._load()

    def _load(self):
        for name, fname in SOUND_FILES.items():
            path = os.path.join(_SOUNDS_DIR, fname)
            if not os.path.exists(path):
                continue  # файла ещё нет - хук останется тихим
            try:
                self._sounds[name] = pg.mixer.Sound(path)
            except pg.error:
                pass

    def play(self, name):
        snd = self._sounds.get(name)
        if snd is not None:
            snd.play()


# Глобальный менеджер (создаётся в init() после pg.init)
_manager = None


def init():
    """Создать менеджер звука (один раз, после инициализации pygame)."""
    global _manager
    if _manager is None:
        _manager = SoundManager()


def play(name):
    """Проиграть звук по логическому имени (no-op, если звука/аудио нет)."""
    if _manager is not None:
        _manager.play(name)
