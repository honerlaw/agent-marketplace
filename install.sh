#!/usr/bin/env bash
set -e

PLUGIN_NAME="${1:-}"
if [ -z "$PLUGIN_NAME" ]; then
  echo "Usage: ./install.sh <plugin-name>"
  echo "Available: $(ls plugins/)"
  exit 1
fi

REPO_DIR="$(pwd)"
PLUGIN_DIR="$REPO_DIR/plugins/$PLUGIN_NAME"
if [ ! -d "$PLUGIN_DIR" ]; then
  echo "Plugin '$PLUGIN_NAME' not found in plugins/"
  exit 1
fi

SCRIPTS_DIR="$PLUGIN_DIR/scripts"
REQUIREMENTS="$SCRIPTS_DIR/requirements.txt"
CLAUDE_SETTINGS="$HOME/.claude/settings.json"
CLAUDE_PLUGINS_DIR="$HOME/.claude/plugins"
MARKETPLACE_NAME="agent-marketplace"

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

# ── 4. Register marketplace + plugin in Claude Code plugin system ────────────
mkdir -p "$HOME/.claude"

python3 - "$CLAUDE_SETTINGS" "$CLAUDE_PLUGINS_DIR" "$REPO_DIR" "$PLUGIN_DIR" "$PLUGIN_NAME" "$MARKETPLACE_NAME" <<'PYEOF'
import json, sys, os, datetime
from pathlib import Path

settings_path   = Path(sys.argv[1])
plugins_dir     = Path(sys.argv[2])
repo_dir        = Path(sys.argv[3])
plugin_dir      = Path(sys.argv[4])
plugin_name     = sys.argv[5]
marketplace     = sys.argv[6]
plugin_key      = f"{plugin_name}@{marketplace}"
now             = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

# --- settings.json: enabledPlugins ---
settings_path.parent.mkdir(parents=True, exist_ok=True)
settings = json.loads(settings_path.read_text()) if settings_path.exists() else {}

# Remove old-style plugins array entry if present (symlink path)
old_plugins = settings.get("plugins", [])
symlink_path = str(plugins_dir / plugin_name)
settings["plugins"] = [p for p in old_plugins if p != symlink_path]
if not settings["plugins"]:
    del settings["plugins"]

enabled = settings.get("enabledPlugins", {})
enabled[plugin_key] = True
settings["enabledPlugins"] = enabled

settings_path.write_text(json.dumps(settings, indent=2) + "\n")
print(f"✓ Enabled {plugin_key} in settings.json")

# --- known_marketplaces.json ---
km_path = plugins_dir / "known_marketplaces.json"
km = json.loads(km_path.read_text()) if km_path.exists() else {}
if marketplace not in km:
    km[marketplace] = {
        "source": {"source": "github", "repo": "honerlaw/agent-marketplace"},
        "installLocation": str(plugins_dir / "marketplaces" / marketplace),
        "lastUpdated": now,
    }
    km_path.write_text(json.dumps(km, indent=4) + "\n")
    print(f"✓ Registered marketplace {marketplace} in known_marketplaces.json")
else:
    print(f"✓ Marketplace {marketplace} already registered")

# --- installed_plugins.json ---
ip_path = plugins_dir / "installed_plugins.json"
ip = json.loads(ip_path.read_text()) if ip_path.exists() else {"version": 2, "plugins": {}}
if "plugins" not in ip:
    ip["plugins"] = {}
ip["plugins"][plugin_key] = [{
    "scope": "user",
    "installPath": str(plugin_dir),
    "version": "1.0.0",
    "installedAt": now,
    "lastUpdated": now,
}]
ip_path.write_text(json.dumps(ip, indent=4) + "\n")
print(f"✓ Registered {plugin_key} in installed_plugins.json")
PYEOF

# ── 5. Marketplace install location (symlink so updates flow through) ────────
MARKETPLACE_DIR="$CLAUDE_PLUGINS_DIR/marketplaces/$MARKETPLACE_NAME"
mkdir -p "$(dirname "$MARKETPLACE_DIR")"
[ -L "$MARKETPLACE_DIR" ] && rm "$MARKETPLACE_DIR"
ln -s "$REPO_DIR" "$MARKETPLACE_DIR"
echo "✓ Linked marketplace → $MARKETPLACE_DIR"

# ── 6. Done ──────────────────────────────────────────────────────────────────
echo ""
echo "Done! Run /reload-plugins in Claude Code to activate. Skills available:"
shopt -s nullglob
for skill_dir in "$PLUGIN_DIR"/skills/*/; do
  skill_name="$(basename "$skill_dir")"
  echo "  ${PLUGIN_NAME}:${skill_name}"
done
shopt -u nullglob
