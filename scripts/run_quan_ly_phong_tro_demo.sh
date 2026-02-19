#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${1:-4173}"

cd "$ROOT_DIR"
echo "[TroManager Demo] Running at: http://127.0.0.1:${PORT}/demo/quan-ly-phong-tro-ui.html"
exec python3 -m http.server "$PORT" --directory "$ROOT_DIR"
