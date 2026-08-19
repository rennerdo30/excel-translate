#!/bin/zsh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TARGET_DIR="$HOME/Library/Containers/com.microsoft.Excel/Data/Documents/wef"

mkdir -p "$TARGET_DIR"
cp "$ROOT_DIR/manifest.xml" "$TARGET_DIR/cell-translator-manifest.xml"

echo "Installed manifest to:"
echo "$TARGET_DIR/cell-translator-manifest.xml"
