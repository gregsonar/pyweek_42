"""PoC web entrypoint for pygbag: async loop + FPS instrumentation.

Boots directly into a gameplay level to measure the raycaster in WASM.
This is a throwaway harness for Phase 0 (PoC), not the production entry.

All diagnostics go to the browser DevTools console (via pygbag's JS bridge)
AND to stdout, so the result is visible regardless of where output lands.
"""
import asyncio
import sys
import time
import traceback


def jslog(msg):
    """Log to the browser DevTools console if possible, and to stdout."""
    try:
        import platform  # pygbag injects .window into the stdlib module
        platform.window.console.log("[POC] " + str(msg))
    except Exception:
        pass
    print(msg, flush=True)


async def main():
    jslog("POC_BOOT_OK: main() started")

    import pygame as pg
    jslog("POC_STEP: pygame imported")

    try:
        import numpy as np  # noqa: F401
        jslog("POC_STEP: numpy imported OK, version " + np.__version__)
    except Exception as exc:
        jslog("POC_FATAL numpy import failed: %r" % exc)
        raise

    from src import audio, config
    from src.app import App
    jslog("POC_STEP: game modules imported")

    app = App()
    jslog("POC_STEP: App() constructed")

    from src.main import GameplayScene
    app.push_scene(GameplayScene(app, level_index=0))
    jslog("POC_STEP: GameplayScene pushed, entering loop")

    frames = 0
    window = 0
    t_window = time.perf_counter()
    fps_samples = []
    MAX_FRAMES = 600

    while app.running and app._scenes and frames < MAX_FRAMES:
        dt = min(app.clock.tick() / 1000.0, config.MAX_DT)

        events = pg.event.get()
        for event in events:
            if event.type == pg.QUIT:
                app.running = False

        scene = app.scene
        if scene is not None and hasattr(scene, "player"):
            scene.player["angle"] += 0.03

        fading = app._fade is not None
        if scene is not None and not fading:
            scene.handle_events(events)
        if app.scene is not None:
            app.scene.update(dt)
        if app._fade is not None:
            app._advance_fade(dt)
        app._draw()
        if app._fade is not None:
            app._draw_fade()
        pg.display.flip()

        frames += 1
        window += 1
        if window >= 30:
            now = time.perf_counter()
            fps = window / (now - t_window)
            if frames > 30:
                fps_samples.append(fps)
            jslog("POC_FPS %.2f (frame %d)" % (fps, frames))
            window = 0
            t_window = now

        await asyncio.sleep(0)

    if fps_samples:
        avg = sum(fps_samples) / len(fps_samples)
        jslog("POC_RESULT avg=%.2f min=%.2f max=%.2f windows=%d"
              % (avg, min(fps_samples), max(fps_samples), len(fps_samples)))
    jslog("POC_DONE")
    pg.quit()


async def _guarded():
    try:
        await main()
    except Exception:
        jslog("POC_TRACEBACK:\n" + traceback.format_exc())
        raise


asyncio.run(_guarded())
