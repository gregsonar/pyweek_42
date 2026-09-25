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
        # Меню и экраны
        "game_title": "ChronoKhryshch",
        "menu_new_game": "New Game",
        "menu_continue": "Continue",
        "menu_language": "Language",
        "menu_quit": "Quit",
        "lang_en": "English",
        "lang_ru": "Русский",
        "pause_title": "Paused",
        "pause_resume": "Resume",
        "pause_main_menu": "Main Menu",
        "pause_quit": "Quit Game",
        "confirm_new_game": "Start over? Progress will be lost.",
        "confirm_yes": "Yes",
        "confirm_no": "No",
        "menu_credits": "Credits",
        "credits_title": "Credits",
        "credits_back": "Back",
        "victory_title": "Level Complete",
        "victory_menu": "Main Menu",
        "victory_credits": "Credits",
        "level_complete_title": "Level {n} Complete",
        "level_complete_time": "Time: {t}",
        "level_complete_next": "Next",
    },
    "ru": {
        "level": "Уровень {n}",
        "level_1_msg": "Всё когда-то начинается",
        "time_up": "Время вышло!",
        # Меню и экраны
        "game_title": "ХроноХрущ",
        "menu_new_game": "Новая игра",
        "menu_continue": "Продолжить",
        "menu_language": "Язык",
        "menu_quit": "Выход",
        "lang_en": "English",
        "lang_ru": "Русский",
        "pause_title": "Пауза",
        "pause_resume": "Продолжить",
        "pause_main_menu": "В главное меню",
        "pause_quit": "Выйти совсем",
        "confirm_new_game": "Начать заново? Прогресс будет потерян.",
        "confirm_yes": "Да",
        "confirm_no": "Нет",
        "menu_credits": "Титры",
        "credits_title": "Титры",
        "credits_back": "Назад",
        "victory_title": "Уровень пройден",
        "victory_menu": "В главное меню",
        "victory_credits": "Титры",
        "level_complete_title": "Уровень {n} пройден",
        "level_complete_time": "Время: {t}",
        "level_complete_next": "Дальше",
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
