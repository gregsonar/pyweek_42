"""PoC web entrypoint for pygbag: async loop + FPS instrumentation.

Boots directly into a gameplay level to measure the raycaster in WASM.
This is a throwaway harness for Phase 0 (PoC), not the production entry.
"""
import asyncio
import time

import pygame as pg

from src import audio, config
from src.app import App


async def main():
    app = App()

    # Boot straight into gameplay level 0 to exercise the raycaster.
    from src.main import GameplayScene
    app.push_scene(GameplayScene(app, level_index=0))

    frames = 0
    window = 0
    t_window = time.perf_counter()
    fps_samples = []
    MAX_FRAMES = 600  # ~ a few seconds of rendering, then stop

    print("POC_BOOT_OK", flush=True)

    while app.running and app._scenes and frames < MAX_FRAMES:
        # No FPS cap: measure the true max render throughput in WASM.
        dt = min(app.clock.tick() / 1000.0, config.MAX_DT)

        events = pg.event.get()
        for event in events:
            if event.type == pg.QUIT:
                app.running = False

        # Nudge the view so we never measure a degenerate static frame.
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
            # ignore the first window (includes JIT / asset warmup)
            if frames > 30:
                fps_samples.append(fps)
            print("POC_FPS %.2f (frame %d)" % (fps, frames), flush=True)
            window = 0
            t_window = now

        await asyncio.sleep(0)

    if fps_samples:
        avg = sum(fps_samples) / len(fps_samples)
        lo = min(fps_samples)
        hi = max(fps_samples)
        print("POC_RESULT avg=%.2f min=%.2f max=%.2f windows=%d"
              % (avg, lo, hi, len(fps_samples)), flush=True)
    print("POC_DONE", flush=True)
    pg.quit()


asyncio.run(main())
