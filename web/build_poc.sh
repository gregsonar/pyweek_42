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

echo ">> сборочная директория: $BUILD_DIR"
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
cp -r "$REPO_ROOT/src"    "$BUILD_DIR/src"
cp -r "$REPO_ROOT/assets" "$BUILD_DIR/assets"
cp    "$REPO_ROOT/web/main.py" "$BUILD_DIR/main.py"

python -m pip install --quiet --upgrade pygbag
echo ">> запускаю pygbag на http://localhost:8000 (Ctrl+C для остановки)"
cd "$BUILD_DIR"
# --disable-sound-format-error: для PoC оставляем .wav как есть (звук для замера
# FPS не нужен). В Фазе 1 звук будет переведён в .ogg и флаг не понадобится.
exec python -m pygbag --port 8000 --disable-sound-format-error main.py
