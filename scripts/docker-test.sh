#!/bin/zsh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
HEALTH_URL="https://localhost:3000/api/health"
TRANSLATE_URL="https://localhost:3000/api/translate"

cd "$ROOT_DIR"
docker compose up --build -d

for _ in {1..30}; do
  if curl -ksS "$HEALTH_URL" >/tmp/excel_translate_health.json 2>/dev/null; then
    break
  fi
  sleep 1
done

echo "Health:"
cat /tmp/excel_translate_health.json
echo
echo
echo "Translate:"
curl -ksS "$TRANSLATE_URL" \
  -H "Content-Type: application/json" \
  -d '{"provider":"lm_studio","sourceLanguage":"auto","targetLanguage":"de","texts":["Hello world"]}'
echo
