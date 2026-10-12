import json
import os
import sys

# В вебе (pygbag/emscripten) файловая система в памяти (MEMFS) не переживает
# перезагрузку страницы. Сейв крошечный (язык, уровень, 2 флага звука), поэтому
# храним его в localStorage браузера. На десктопе — по-прежнему файл save.json.
_WEB = sys.platform == "emscripten"
_LS_KEY = "chronokhryshch_save"

if getattr(sys, "frozen", False):
    _ROOT = os.path.dirname(sys.executable)
else:
    _ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_PATH = os.path.join(_ROOT, "save.json")

_DEFAULT = {"language": None, "progress": None, "music_on": None, "sfx_on": None}

class SaveData:

    def __init__(self, data=None):
        base = dict(_DEFAULT)
        if isinstance(data, dict):
            base.update(data)
        self.language = base.get("language")
        prog = base.get("progress")
        self.progress_level = prog.get("level") if isinstance(prog, dict) else None
        self.music_on = base.get("music_on")
        self.sfx_on = base.get("sfx_on")

    def has_progress(self):
        return self.progress_level is not None

    def set_progress(self, level):
        self.progress_level = level

    def reset_progress(self):
        self.progress_level = None

    def to_dict(self):
        return {
            "language": self.language,
            "progress": (
                {"level": self.progress_level}
                if self.progress_level is not None
                else None
            ),
            "music_on": self.music_on,
            "sfx_on": self.sfx_on,
        }

def _read_raw():
    if _WEB:
        try:
            import platform
            raw = platform.window.localStorage.getItem(_LS_KEY)
            return str(raw) if raw else None
        except Exception:
            return None
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return None

def _write_raw(text):
    if _WEB:
        try:
            import platform
            platform.window.localStorage.setItem(_LS_KEY, text)
        except Exception as exc:
            print("save failed (web): %s" % exc, file=sys.stderr, flush=True)
        return
    try:
        with open(SAVE_PATH, "w", encoding="utf-8") as fh:
            fh.write(text)
    except OSError as exc:
        print("save failed: %s" % exc, file=sys.stderr, flush=True)

def load():
    raw = _read_raw()
    if raw:
        try:
            return SaveData(json.loads(raw))
        except ValueError:
            pass
    return SaveData()

def persist(data):
    _write_raw(json.dumps(data.to_dict(), ensure_ascii=False, indent=2))
