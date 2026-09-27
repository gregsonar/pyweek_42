DEFAULT_LANGUAGE = "en"
LANGUAGES = ("en", "ru")

STRINGS = {
    "en": {
        "level": "Level {n}",
        "level_1_msg": "Everything has a beginning",
        "level_2_msg": "Stay the course!",
        "level_3_msg": "Doors, buttons...",
        "level_4_msg": "Run!",
        "level_5_msg": "Watch out for live wires!",
        "time_up": "Time's up!",

        "game_title": "ChronoKhryshch",
        "menu_new_game": "New Game",
        "menu_continue": "Continue",
        "menu_language": "Language",
        "menu_music": "Music",
        "menu_sfx": "Sound FX",
        "state_on": "On",
        "state_off": "Off",
        "menu_quit": "Quit",

        "menu_howto_1": "Move: WASD (you know, just like in games...), look with the mouse.",
        "menu_howto_2": "E - interact, F freezes the time (but you'll have to pay off your debt of time)",
        "menu_howto_3": "Find your way out of ChronoKhrushchevka before time swallows you up!",
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
        "credits_title": "Thanks for playing!",
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
        "level_2_msg": "Держи курс!",
        "level_3_msg": "Двери, кнопки...",
        "level_4_msg": "Беги!",
        "level_5_msg": "Берегись оголённых проводов!",
        "time_up": "Время вышло!",

        "game_title": "ХроноХрущ",
        "menu_new_game": "Новая игра",
        "menu_continue": "Продолжить",
        "menu_language": "Язык",
        "menu_music": "Музыка",
        "menu_sfx": "Звуки",
        "state_on": "Вкл",
        "state_off": "Выкл",
        "menu_quit": "Выход",

        "menu_howto_1": "Движение: WASD (знаете, ну как в играх...), обзор - мышью.",
        "menu_howto_2": "E - взаимодействие, F останавливает время (но долги времени придётся вернуть).",
        "menu_howto_3": "Доберись до выхода из ХроноХрущёвки, пока время не поглотило тебя!",
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
        "credits_title": "Спасибо, что играли!",
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
    table = STRINGS.get(language) or {}
    return key in table or key in STRINGS[DEFAULT_LANGUAGE]

def tr(key, language=DEFAULT_LANGUAGE, **fmt):
    table = STRINGS.get(language) or STRINGS[DEFAULT_LANGUAGE]
    template = table.get(key)
    if template is None:
        template = STRINGS[DEFAULT_LANGUAGE].get(key, key)
    try:
        return template.format(**fmt)
    except (KeyError, IndexError):
        return template
