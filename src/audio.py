# src/audio.py
"""Звук: тонкий менеджер эффектов с хуками по имени.

Каркас на будущее: логические имена звуков -> файлы в assets/sounds. Файлов
может ещё не быть - тогда play() просто ничего не делает. Если аудио недоступно
(нет устройства/микшер не инициализировался), звук молча отключается.
"""

import os
import sys

import pygame as pg

from . import config

_SOUNDS_DIR = "assets/sounds"
_MUSIC_DIR = "assets/sounds"

# Логические имена -> имена файлов. Файлы добавим позже; отсутствующие
# пропускаются при загрузке, а play() по такому имени - no-op.
SOUND_FILES = {
    "intro": "intro.wav",
    "ui_move": "ui_move.wav",
    "ui_select": "ui_select.wav",
    "hurt": "hurt.wav",
    "freeze": "freeze.wav",
    "unfreeze": "unfreeze.wav",
    "death": "death.wav",  # проигрыш (HP=0 или вышло время)
    "buzz": "buzz.wav",  # гудение активной спрайтовой ловушки (зацикленный)
}


class SoundManager:
    """Загружает доступные звуки и проигрывает их по логическому имени."""

    def __init__(self):
        self._sounds = {}
        self._enabled = False
        self._loop_channel = None  # канал под зацикленный звук (гудение)
        self._loop_name = None
        self._music_path = None  # путь текущего потокового трека (саундтрек уровня)
        # Переключатели категорий (out of sync с сейвом до set_*). Музыка и эффекты
        # независимы; оба off - полная тишина.
        self._music_on = True
        self._sfx_on = True
        # Последний запрошенный трек (запоминаем, даже если музыка выключена),
        # чтобы возобновить его при включении музыки в меню паузы.
        self._music_filename = ""
        self._music_loop = True
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
                snd = pg.mixer.Sound(path)
                snd.set_volume(config.SFX_VOLUME)  # базовая громкость эффектов
                self._sounds[name] = snd
            except pg.error:
                pass

    def play(self, name):
        if not self._sfx_on:
            return
        snd = self._sounds.get(name)
        if snd is not None:
            snd.play()

    def loop(self, name, volume):
        """Зациклить звук name с громкостью volume (0..1) на общем канале.

        volume<=0 или звук не загружен - остановить зацикленный звук. Один канал
        под один зацикленный звук (напр. гудение ближайшей активной ловушки).
        """
        if not self._enabled or not self._sfx_on:
            self.stop_loop()
            return
        snd = self._sounds.get(name)
        if snd is None or volume <= 0.0:
            self.stop_loop()
            return
        ch = self._loop_channel
        if ch is None or self._loop_name != name or not ch.get_busy():
            self._loop_channel = snd.play(loops=-1)
            self._loop_name = name
        if self._loop_channel is not None:
            vol = min(1.0, max(0.0, volume)) * config.SFX_VOLUME
            self._loop_channel.set_volume(vol)

    def stop_loop(self):
        """Остановить зацикленный звук (при выходе со сцены/паузе проигрыша)."""
        if self._loop_channel is not None:
            self._loop_channel.stop()
            self._loop_channel = None
            self._loop_name = None

    def play_music(self, filename, loop=True):
        """Запустить потоковый трек (саундтрек) из assets/music.

        filename - имя файла в _MUSIC_DIR (пусто/нет файла -> тишина). loop=True -
        зациклить бесконечно, иначе проиграть один раз. Один трек одновременно:
        новый вызов заменяет предыдущий. Запрос запоминается всегда (даже при
        выключенной музыке), чтобы возобновить трек при включении музыки.
        """
        self._music_filename = filename
        self._music_loop = loop
        if not self._enabled:
            return
        if not filename or not self._music_on:
            self.stop_music()
            return
        path = os.path.join(_MUSIC_DIR, filename)
        if not os.path.exists(path):
            self.stop_music()  # трека ещё нет - тишина (как и с эффектами)
            return
        try:
            pg.mixer.music.load(path)
            pg.mixer.music.set_volume(config.MUSIC_VOLUME)  # саундтрек тише эффектов
            pg.mixer.music.play(-1 if loop else 0)
            self._music_path = path
        except pg.error:
            self._music_path = None

    def stop_music(self, clear=False):
        """Остановить саундтрек. clear=True - забыть запомненный трек (уход со
        сцены в меню/прохождение), чтобы включение музыки не возобновило его.
        clear=False (по умолч.) - только остановить, запрос сохранить (выключение
        музыки в меню, пауза проигрыша)."""
        if clear:
            self._music_filename = ""
        if not self._enabled:
            return
        try:
            pg.mixer.music.stop()
            if hasattr(pg.mixer.music, "unload"):
                pg.mixer.music.unload()  # освободить файл (pygame 2.0+)
        except pg.error:
            pass
        self._music_path = None

    def set_music_enabled(self, on):
        """Вкл/выкл музыку. При включении - возобновить запомненный трек уровня."""
        self._music_on = bool(on)
        if self._music_on:
            self.play_music(self._music_filename, self._music_loop)
        else:
            self.stop_music()  # запрос помним - вернётся при включении

    def set_sfx_enabled(self, on):
        """Вкл/выкл звуковые эффекты. При выключении глушим и зацикленные (гудение)."""
        self._sfx_on = bool(on)
        if not self._sfx_on:
            self.stop_loop()


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


def loop(name, volume):
    """Зациклить звук с громкостью 0..1 (no-op, если звука/аудио нет)."""
    if _manager is not None:
        _manager.loop(name, volume)


def stop_loop():
    """Остановить зацикленный звук."""
    if _manager is not None:
        _manager.stop_loop()


def play_music(filename, loop=True):
    """Запустить саундтрек уровня (no-op, если музыки/аудио нет)."""
    if _manager is not None:
        _manager.play_music(filename, loop)


def stop_music(clear=False):
    """Остановить саундтрек (clear=True - забыть запомненный трек)."""
    if _manager is not None:
        _manager.stop_music(clear)


def set_music_enabled(on):
    """Вкл/выкл музыку (возобновит запомненный трек при включении)."""
    if _manager is not None:
        _manager.set_music_enabled(on)


def set_sfx_enabled(on):
    """Вкл/выкл звуковые эффекты."""
    if _manager is not None:
        _manager.set_sfx_enabled(on)
