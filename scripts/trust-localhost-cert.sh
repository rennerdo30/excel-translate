#!/bin/zsh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CERT_PATH="$ROOT_DIR/certs/localhost.pem"
KEYCHAIN_PATH="$HOME/Library/Keychains/login.keychain-db"

if [[ ! -f "$CERT_PATH" ]]; then
  echo "Certificate not found at $CERT_PATH"
  exit 1
fi

echo "This will trust the local development certificate in your login keychain:"
echo "  $CERT_PATH"
echo
security add-trusted-cert -d -r trustRoot -k "$KEYCHAIN_PATH" "$CERT_PATH"
echo "Trusted localhost certificate in $KEYCHAIN_PATH"
