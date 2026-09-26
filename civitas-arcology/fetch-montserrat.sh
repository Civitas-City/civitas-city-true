#!/usr/bin/env bash
# Montserrat is the only permitted typeface (Design Canon, LOCKED).
# Installs Montserrat-Bold.ttf where civitas/util.montserrat() looks for it.
set -euo pipefail

DEST="${1:-$HOME/.fonts}"
URL="https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf"

mkdir -p "$DEST"
if [ -f "$DEST/Montserrat-Bold.ttf" ]; then
  echo "Montserrat already present at $DEST/Montserrat-Bold.ttf"
  exit 0
fi

curl -fsSL "$URL" -o "$DEST/Montserrat-Bold.ttf"
command -v fc-cache >/dev/null && fc-cache -f "$DEST" >/dev/null || true
echo "Installed $DEST/Montserrat-Bold.ttf"
