# Особенности pygbag (грабли и решения)

Рабочие заметки по портированию на pygbag 0.9.3 (pygame-ce 2.5.7, CPython 3.12
в WebAssembly). НЕ для чистых веток main/web — только для рабочей ветки.

## 1. Порядок импортов: numpy ДО pygame (критично)

pygbag грузит .so-wheel'ы в порядке обнаружения импортов. В emscripten SDL
слинкован в несколько .so, и из-за дублирования символов «побеждает»
загруженный последним. Если **numpy грузится после pygame**, он затирает
регистрацию SDL-дисплея, и первый же `set_mode` падает:
`pygame.error: The video driver did not add any displays` (num_displays=0).

Решение: во входном файле `import numpy` стоит ДО `import pygame`. Тогда pygame
линкуется последним и дисплей сохраняется. На десктопе порядок безразличен.

Диагностировали бинарным поиском: pygame_ce в одиночку — ок; numpy раньше
pygame — ок; pygame раньше numpy — падает. Ни версия, ни размер окна, ни место
вызова set_mode, ни упаковка ассетов роли не играли.

## 2. Кодировка входного main.py (Windows)

pygbag читает входной скрипт системной кодировкой. На Windows это cp1251, и
UTF-8 с кириллицей ломает его парсер (`UnicodeDecodeError`). Решение: запускать
pygbag с `PYTHONUTF8=1` (см. build_poc.sh). Файлы в `src/` копируются бинарно —
их это не касается, кириллица в них безопасна.

## 3. ume_block: аудио ждёт пользовательский жест

pygbag по умолчанию (`ume_block:1`) блокирует запуск до user gesture (клик) для
разблокировки аудио (autoplay-политика браузера). В обычном браузере игрок
кликает «старт» — звук разблокируется сам. В headless клика нет, поэтому для
автотестов запускаем Chrome с `--autoplay-policy=no-user-gesture-required`.

## 4. Размер/пропорция canvas — timing-баг (квадрат в Firefox)

Подгонка размера canvas в pygbag (`window_canvas_adjust` в pythons.js) берёт
пропорцию из БУФЕРА canvas (`canvas.width/canvas.height`). Если она срабатывает
ДО нашего `set_mode` (буфер ещё стартовые 1x1) — `ar = 1` → экран рисуется
квадратным. Проявлялось в Firefox (в Chrome пересчёт случайно шёл после
set_mode). Усугубляется тем, что код шаблона после `await shell.source(main)`
не выполняется — наш игровой цикл бесконечный (см. п.7).

Решение: после создания дисплея (App → set_mode, буфер стал 960x600) зовём
`platform.window.window_resize()` — pygbag пересчитывает с правильной
пропорцией 1.6 (`web/web_main.py::_fix_web_canvas`). Дополнительно для
согласованности конфига: `--width 960 --height 600` и `fb_ar:1.6` в шаблоне.

## 5. index.html грузится в Quirks mode

Дефолтный шаблон pygbag начинается с `<html>` без `<!DOCTYPE html>` → Quirks
mode → лишние полосы прокрутки и расхождения раскладки. Плюс в его CSS есть
невалидное `body { padding: none; }`. Решение: свой шаблон `web/chrono.tmpl`
(копия default.tmpl + DOCTYPE + `html/body{overflow:hidden}` + тёмный фон +
тёмный лоадер), передаётся через `--template chrono.tmpl`.

## 6. Файловая система в памяти (MEMFS) не переживает reload

В вебе запись на «диск» идёт в MEMFS и теряется при перезагрузке страницы.
Сейв игры крошечный (язык, уровень, 2 флага звука), поэтому храним его в
`localStorage` через `platform.window.localStorage` (`src/save.py`, web-ветка).
Для больших данных понадобился бы IDBFS с `FS.syncfs`.

## 7. Бесконечный игровой цикл и async

pygbag ждёт async-`main` с `await asyncio.sleep(0)` после каждого кадра
(иначе браузер зависает). Наш цикл крутится вечно, поэтому код в шаблоне ПОСЛЕ
`await shell.source(main)` не выполняется — нельзя рассчитывать на пост-луп
инициализацию из шаблона (отсюда и п.4).

## 8. Загрузка wheel'ов на первом заходе

Dev-сервер pygbag на первом запросе тянет wheel'ы (pygame_ce ~1.5 МБ, numpy
~12 МБ) с CDN в локальный кэш — первый холодный заход может подвисать на
«computing required packages»/«Loading…». Повторный заход/reload быстрее.

## 9. Headless-тестирование (без реального браузера)

puppeteer-core + установленные Chrome/Firefox (scratchpad/hrunner). Ключевые
флаги Chrome: `--autoplay-policy=no-user-gesture-required` (ume), WebGL через
`--enable-unsafe-swiftshader --use-gl=angle --use-angle=swiftshader`, плюс
анти-троттлинг. Firefox тоже заводится (`browser:'firefox'`) — важно, т.к.
подгонка canvas в FF и Chrome расходится (см. п.4). Встроенная браузер-панель
Claude тротлит скрытую/фоновую вкладку и не догружает тяжёлые pygbag-приложения
— для автотестов она не годится, нужен headless или реальный браузер.
