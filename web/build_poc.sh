#!/usr/bin/env bash
# PoC-сборка веб-версии (Фаза 0). Собирает чистый пакет (без .git/venv) и
# поднимает локальный сервер pygbag. Требуется интернет-доступ к
# pygame-web.github.io (CDN рантайма). Запускать с машины с открытой сетью.
#
#   bash web/build_poc.sh
#   -> открой http://localhost:8000  (Chrome/Firefox)
#   -> открой консоль браузера (F12) и смотри строки POC_FPS / POC_RESULT
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUILD_DIR="${TMPDIR:-/tmp}/chrono_webpoc"

# Необязательный аргумент: входной файл (по умолчанию PoC-харнес web/main.py).
# Для продакшн-входа: bash web/build_poc.sh web/web_main.py
ENTRY="${1:-web/main.py}"

echo ">> сборочная директория: $BUILD_DIR (вход: $ENTRY)"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
cp -r "$REPO_ROOT/src"    "$BUILD_DIR/src"
cp -r "$REPO_ROOT/assets" "$BUILD_DIR/assets"
cp    "$REPO_ROOT/$ENTRY" "$BUILD_DIR/main.py"

# Своя index.html-обёртка: дефолтный шаблон pygbag без <!DOCTYPE html> грузится
# в Quirks mode (отсюда лишние полосы прокрутки). chrono.tmpl добавляет DOCTYPE,
# overflow:hidden и тёмный фон. Передаётся pygbag через --template.
TMPL_ARG=()
if [ -f "$REPO_ROOT/web/chrono.tmpl" ]; then
  cp "$REPO_ROOT/web/chrono.tmpl" "$BUILD_DIR/chrono.tmpl"
  TMPL_ARG=(--template chrono.tmpl)
fi

# Веб-версия использует .ogg (pygame в pygbag не умеет .wav). Конвертируем ЛОКАЛЬНО
# в сборочную директорию и удаляем .wav, чтобы в пакет попал только .ogg.
# Медиа в репозиторий не коммитим — это делается только перед релизом.
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "!! ffmpeg не найден в PATH — установи его и повтори (нужен для .wav->.ogg)" >&2
  exit 1
fi
echo ">> конвертирую звук .wav -> .ogg"
for wav in "$BUILD_DIR"/assets/sounds/*.wav; do
  [ -e "$wav" ] || continue
  ffmpeg -y -loglevel error -i "$wav" -c:a libvorbis -q:a 5 "${wav%.wav}.ogg"
  rm -f "$wav"
done

python -m pip install --quiet --upgrade pygbag
echo ">> запускаю pygbag на http://localhost:8000 (Ctrl+C для остановки)"
cd "$BUILD_DIR"
# pygbag читает входной main.py системной кодировкой (на Windows это cp1251),
# из-за чего UTF-8 с кириллицей ломает его парсер. UTF-8 mode это чинит.
export PYTHONUTF8=1
# --width/--height: размер фреймбуфера pygbag под нашу игру (config 960x600,
# ar 1.6). По умолчанию pygbag ставит 1280x720 (ar 1.77) — не наши пропорции.
exec python -m pygbag --port 8000 --width 960 --height 600 "${TMPL_ARG[@]}" main.py
