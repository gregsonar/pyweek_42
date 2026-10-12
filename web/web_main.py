"""Продакшн точка входа для веб-сборки (pygbag).

Десктоп по-прежнему стартует через run.py (блокирующий App.run).
Веб использует этот async-вход: App.run_async() отдаёт управление браузеру
после каждого кадра.

ВАЖНО: numpy импортируется ДО pygame. pygbag грузит .so-wheel'ы в порядке
обнаружения импортов; в emscripten SDL слинкован в несколько .so, и если numpy
грузится после pygame, он затирает регистрацию SDL-дисплея (set_mode падает:
"The video driver did not add any displays"). numpy раньше pygame -> pygame
линкуется последним и дисплей сохраняется. На десктопе порядок безразличен.
"""
import asyncio
import sys

import numpy as np  # noqa: F401  (must precede pygame on web)
import pygame  # noqa: F401


def _fix_web_canvas():
    """Пересчитать размер canvas после set_mode.

    pygbag считает пропорцию из буфера canvas (canvas.width/height). Если его
    подгонка (window_canvas_adjust) срабатывает ДО нашего set_mode, буфер ещё
    1x1 -> ar=1 -> экран рисуется квадратным (заметно в Firefox). После того как
    App создал дисплей (буфер стал 960x600, ar=1.6), заставляем pygbag
    пересчитать размер. На десктопе ничего не делаем.
    """
    if sys.platform != "emscripten":
        return
    try:
        import platform
        platform.window.window_resize()
    except Exception:
        pass


async def _main():
    from src import audio
    from src.app import App
    from src.splash import SplashScene

    app = App()
    _fix_web_canvas()
    app.push_scene(SplashScene(app))
    audio.play("intro")
    await app.run_async()


asyncio.run(_main())
