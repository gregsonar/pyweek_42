import os
import sys

import pygame as pg

from . import config

_SOUNDS_DIR = "assets/sounds"
_MUSIC_DIR = "assets/sounds"

SOUND_FILES = {
    "intro": "intro.wav",
    "ui_move": "ui_move.wav",
    "ui_select": "ui_select.wav",
    "hurt": "hurt.wav",
    "freeze": "freeze.wav",
    "unfreeze": "unfreeze.wav",
    "death": "death.wav",
    "buzz": "buzz.wav",
}

class SoundManager:

    def __init__(self):
        self._sounds = {}
        self._enabled = False
        self._loop_channel = None
        self._loop_name = None
        self._music_path = None

        self._music_on = True
        self._sfx_on = True

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
                continue
            try:
                snd = pg.mixer.Sound(path)
                snd.set_volume(config.SFX_VOLUME)
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
        if self._loop_channel is not None:
            self._loop_channel.stop()
            self._loop_channel = None
            self._loop_name = None

    def play_music(self, filename, loop=True):
        self._music_filename = filename
        self._music_loop = loop
        if not self._enabled:
            return
        if not filename or not self._music_on:
            self.stop_music()
            return
        path = os.path.join(_MUSIC_DIR, filename)
        if not os.path.exists(path):
            self.stop_music()
            return
        try:
            pg.mixer.music.load(path)
            pg.mixer.music.set_volume(config.MUSIC_VOLUME)
            pg.mixer.music.play(-1 if loop else 0)
            self._music_path = path
        except pg.error:
            self._music_path = None

    def stop_music(self, clear=False):
        if clear:
            self._music_filename = ""
        if not self._enabled:
            return
        try:
            pg.mixer.music.stop()
            if hasattr(pg.mixer.music, "unload"):
                pg.mixer.music.unload()
        except pg.error:
            pass
        self._music_path = None

    def set_music_enabled(self, on):
        self._music_on = bool(on)
        if self._music_on:
            self.play_music(self._music_filename, self._music_loop)
        else:
            self.stop_music()

    def set_sfx_enabled(self, on):
        self._sfx_on = bool(on)
        if not self._sfx_on:
            self.stop_loop()

_manager = None

def init():
    global _manager
    if _manager is None:
        _manager = SoundManager()

def play(name):
    if _manager is not None:
        _manager.play(name)

def loop(name, volume):
    if _manager is not None:
        _manager.loop(name, volume)

def stop_loop():
    if _manager is not None:
        _manager.stop_loop()

def play_music(filename, loop=True):
    if _manager is not None:
        _manager.play_music(filename, loop)

def stop_music(clear=False):
    if _manager is not None:
        _manager.stop_music(clear)

def set_music_enabled(on):
    if _manager is not None:
        _manager.set_music_enabled(on)

def set_sfx_enabled(on):
    if _manager is not None:
        _manager.set_sfx_enabled(on)
