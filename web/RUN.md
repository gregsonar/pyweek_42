# Запуск веб-версии ChronoKhryshch локально

Браузерная сборка игры через pygbag (pygame → WebAssembly).

## Требуется

- `git`
- Python 3.10+ с `pip`
- **ffmpeg** в PATH (конвертация звука .wav → .ogg при сборке)
- bash (на Windows — Git Bash)
- доступ в интернет (на первом запуске тянется WASM-рантайм и колёса
  pygame/numpy с CDN pygame-web.github.io)

pygbag ставить вручную не нужно — скрипт сборки поставит сам.

## Шаги

1. Клонировать репозиторий и переключиться на ветку:

   ```bash
   git clone https://github.com/gregsonar/pyweek_42.git
   ```

   ```bash
   cd pyweek_42 && git checkout claude/chronokhryshch-web-port-78e345
   ```

2. Собрать и поднять локальный сервер:

   ```bash
   bash web/build_poc.sh web/web_main.py
   ```

3. Открыть http://localhost:8000 в Chrome или Firefox. Кликнуть по странице
   («старт») — это разблокирует звук (политика автоплея браузера).

## Заметки

- Первый холодный запуск скачивает рантайм и колёса (~15 МБ) — 20–40 с.
  Если застрянет на «Loading…» — обновить страницу (F5) один раз.
- `bash web/build_poc.sh` **без аргумента** поднимает PoC-харнес для замера
  FPS (строки `POC_FPS` / `POC_RESULT` в консоли браузера, F12).
  С аргументом `web/web_main.py` — полноценная игра (меню, уровни).
- Остановить сервер: Ctrl+C в терминале.
- Десктопная версия (без браузера): `python run.py`.

## Если что-то не так

- `ffmpeg не найден` — установить ffmpeg и добавить в PATH.
- Чёрный/зависший экран, в консоли браузера видно ошибку — свериться с
  `web/PYGBAG_NOTES.md` (известные грабли pygbag и их причины).
