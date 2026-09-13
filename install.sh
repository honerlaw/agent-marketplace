#!/usr/bin/env bash
set -e
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3.11+ is required to install plugins." >&2
  exit 1
fi
exec python3 "$REPO_DIR/scripts/install_plugin.py" "$@"
