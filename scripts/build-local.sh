#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Cleaning dist/"
rm -rf dist/ build/

echo "==> Installing dependencies"
uv sync
uv pip install pyinstaller

echo "==> Building with PyInstaller"
uv run pyinstaller roku_tui.spec

BINARY="dist/roku-tui"

echo "==> Build complete"
echo "    Path: $BINARY"
echo "    Arch: $(file "$BINARY" | sed 's/.*: //')"
echo ""
echo "Run it: $BINARY"
