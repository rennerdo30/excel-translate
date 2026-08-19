#!/bin/zsh

set -euo pipefail

WEF_DIR="$HOME/Library/Containers/com.microsoft.Excel/Data/Documents/wef"
OSF_HOST_DIR="$HOME/Library/Containers/com.Microsoft.OsfWebHost/Data"

echo "This will clear Excel's sideloaded add-in cache on macOS."
echo "It removes contents from:"
echo "  $WEF_DIR"
echo "  $OSF_HOST_DIR"
echo
echo "Quit Excel before continuing."
read "REPLY?Type YES to continue: "

if [[ "$REPLY" != "YES" ]]; then
  echo "Canceled."
  exit 1
fi

mkdir -p "$WEF_DIR"
find "$WEF_DIR" -mindepth 1 -maxdepth 1 -exec rm -rf {} +

if [[ -d "$OSF_HOST_DIR" ]]; then
  find "$OSF_HOST_DIR" -mindepth 1 -maxdepth 1 -exec rm -rf {} +
fi

echo "Excel add-in cache cleared."
echo "Next steps:"
echo "  1. npm run install-manifest"
echo "  2. Reopen Excel"
echo "  3. Open Cell Translator once"
