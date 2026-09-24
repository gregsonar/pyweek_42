# src/i18n.py
"""Локализация строк интерфейса (английский и русский)."""

DEFAULT_LANGUAGE = "en"
LANGUAGES = ("en", "ru")

# Таблицы строк по языкам. Ключ - идентификатор строки, значение - шаблон
# (поддерживает подстановку через str.format, например {n}).
STRINGS = {
    "en": {
        "level": "Level {n}",
        "level_1_msg": "Everything has a beginning",
        "time_up": "Time's up!",
    },
    "ru": {
        "level": "Уровень {n}",
        "level_1_msg": "Всё когда-то начинается",
        "time_up": "Время вышло!",
    },
}


def has(key, language=DEFAULT_LANGUAGE):
    """Есть ли строка с таким ключом (в языке или в языке по умолчанию)."""
    table = STRINGS.get(language) or {}
    return key in table or key in STRINGS[DEFAULT_LANGUAGE]


def tr(key, language=DEFAULT_LANGUAGE, **fmt):
    """
    Строка по ключу для указанного языка.

    Неизвестный язык -> язык по умолчанию. Неизвестный ключ -> сам ключ.
    Ошибки подстановки -> шаблон без подстановки (чтобы HUD не падал).
    """
    table = STRINGS.get(language) or STRINGS[DEFAULT_LANGUAGE]
    template = table.get(key)
    if template is None:
        template = STRINGS[DEFAULT_LANGUAGE].get(key, key)
    try:
        return template.format(**fmt)
    except (KeyError, IndexError):
        return template
