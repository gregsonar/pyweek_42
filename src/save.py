# src/save.py
"""Портативное сохранение: язык интерфейса и прогресс в save.json рядом с игрой.

Файл лежит в корне проекта (рядом с run.py). Если запись невозможна (например,
папка только для чтения рядом с exe) - предупреждаем и продолжаем в памяти.
"""

import json
import os
import sys

# Корень проекта (на уровень выше пакета src) - "рядом с игрой"
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAVE_PATH = os.path.join(_ROOT, "save.json")

_DEFAULT = {"language": None, "progress": None}


class SaveData:
    """Состояние сохранения: язык интерфейса и прогресс (номер уровня)."""

    def __init__(self, data=None):
        base = dict(_DEFAULT)
        if isinstance(data, dict):
            base.update(data)
        self.language = base.get("language")
        prog = base.get("progress")
        self.progress_level = prog.get("level") if isinstance(prog, dict) else None

    def has_progress(self):
        """Есть ли сохранённый прогресс (доступна ли кнопка 'Продолжить')."""
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
        }


def load():
    """Загрузить сохранение (или значения по умолчанию при отсутствии/ошибке)."""
    try:
        with open(SAVE_PATH, "r", encoding="utf-8") as fh:
            return SaveData(json.load(fh))
    except (OSError, ValueError):
        return SaveData()


def persist(data):
    """Записать сохранение. Молча предупреждает при невозможности записи."""
    try:
        with open(SAVE_PATH, "w", encoding="utf-8") as fh:
            json.dump(data.to_dict(), fh, ensure_ascii=False, indent=2)
    except OSError as exc:
        print("save failed: %s" % exc, file=sys.stderr, flush=True)
