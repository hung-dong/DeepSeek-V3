#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${1:-8000}"

echo "[Shop Demo] Root: ${ROOT_DIR}"
echo "[Shop Demo] URL : http://127.0.0.1:${PORT}/demo/trang-web-ban-hang-day-du.html"
echo "[Shop Demo] Index: http://127.0.0.1:${PORT}/demo/index.html"
echo "Nhấn Ctrl+C để dừng server."

cd "${ROOT_DIR}"
python3 -m http.server "${PORT}" --bind 0.0.0.0 --directory .
