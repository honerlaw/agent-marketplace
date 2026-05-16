#!/usr/bin/env bash
set -e

PLUGIN_NAME="${1:-}"
if [ -z "$PLUGIN_NAME" ]; then
  echo "Usage: ./install.sh <plugin-name>"
  echo "Available: $(ls plugins/)"
  exit 1
fi

PLUGIN_DIR="$(pwd)/plugins/$PLUGIN_NAME"
if [ ! -d "$PLUGIN_DIR" ]; then
  echo "Plugin '$PLUGIN_NAME' not found in plugins/"
  exit 1
fi

SCRIPTS_DIR="$PLUGIN_DIR/scripts"
REQUIREMENTS="$SCRIPTS_DIR/requirements.txt"
CLAUDE_SETTINGS="$HOME/.claude/settings.json"
CLAUDE_PLUGINS_DIR="$HOME/.claude/plugins"

# ── 1. Symlink plugin ────────────────────────────────────────────────────────
mkdir -p "$CLAUDE_PLUGINS_DIR"
TARGET="$CLAUDE_PLUGINS_DIR/$PLUGIN_NAME"
[ -L "$TARGET" ] && rm "$TARGET"
ln -s "$PLUGIN_DIR" "$TARGET"
echo "✓ Linked $PLUGIN_NAME → $TARGET"

# ── 2. Python dependencies ───────────────────────────────────────────────────
if [ -f "$REQUIREMENTS" ]; then
  if ! command -v python3 &>/dev/null; then
    echo "✗ python3 not found — install Python 3.11+ and re-run"
    exit 1
  fi
  echo "  Installing Python dependencies..."
  python3 -m pip install -q -r "$REQUIREMENTS"
  echo "✓ Python dependencies installed"
fi

# ── 3. Playwright browser ────────────────────────────────────────────────────
if python3 -c "import playwright" &>/dev/null 2>&1; then
  echo "  Installing Playwright Chromium..."
  python3 -m playwright install chromium --quiet 2>/dev/null || python3 -m playwright install chromium
  echo "✓ Playwright Chromium installed"
fi

# ── 4. Register plugin in ~/.claude/settings.json ───────────────────────────
mkdir -p "$HOME/.claude"

# Use Python to safely read/write JSON (avoids jq dependency)
python3 - "$CLAUDE_SETTINGS" "$TARGET" <<'PYEOF'
import json, sys, os
from pathlib import Path

settings_path = Path(sys.argv[1])
plugin_path = sys.argv[2]

if settings_path.exists():
    try:
        settings = json.loads(settings_path.read_text())
    except json.JSONDecodeError:
        settings = {}
else:
    settings = {}

plugins = settings.get("plugins", [])
if plugin_path not in plugins:
    plugins.append(plugin_path)
    settings["plugins"] = plugins
    settings_path.write_text(json.dumps(settings, indent=2) + "\n")
    print(f"✓ Registered in {settings_path}")
else:
    print(f"✓ Already registered in {settings_path}")
PYEOF

# ── 5. Done ──────────────────────────────────────────────────────────────────
echo ""
echo "Done! Restart Claude Code to activate. Skills available:"
shopt -s nullglob
for skill in "$PLUGIN_DIR"/skills/*.md; do
  echo "  /$(basename "${skill%.md}")"
done
shopt -u nullglob
