#!/bin/sh
# Crossweave offline launcher (macOS / Linux). Needs Python 3.
# The app fetches its data files, so it must be served - double-clicking index.html will not work.
cd "$(dirname "$0")/app" || exit 1
PORT="${PORT:-8017}"
URL="http://localhost:$PORT/"
PY=python3; command -v python3 >/dev/null 2>&1 || PY=python
command -v "$PY" >/dev/null 2>&1 || { echo "Python 3 is required: https://www.python.org/downloads/"; exit 1; }
echo "Crossweave running at $URL  (Ctrl+C to stop)"
( sleep 1; if command -v open >/dev/null 2>&1; then open "$URL"; elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL"; fi ) >/dev/null 2>&1 &
exec "$PY" -m http.server "$PORT" --bind 127.0.0.1
