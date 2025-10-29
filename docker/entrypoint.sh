#!/usr/bin/env sh
set -e

APP_DIR="/app/app"
STATIC_DIR="$APP_DIR/static"
MANUAL_FILE="$STATIC_DIR/manual.html"
MANUAL_EXAMPLE="$STATIC_DIR/manual.html.example"

if [ ! -f "$MANUAL_FILE" ] && [ -f "$MANUAL_EXAMPLE" ]; then
  echo "[entrypoint] manual.html não encontrado. Copiando manual.html.example -> manual.html"
  cp "$MANUAL_EXAMPLE" "$MANUAL_FILE"
fi

exec "$@"


