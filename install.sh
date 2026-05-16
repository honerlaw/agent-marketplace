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

CLAUDE_PLUGINS_DIR="$HOME/.claude/plugins"
mkdir -p "$CLAUDE_PLUGINS_DIR"

TARGET="$CLAUDE_PLUGINS_DIR/$PLUGIN_NAME"
[ -L "$TARGET" ] && rm "$TARGET"
ln -s "$PLUGIN_DIR" "$TARGET"
echo "Linked plugins/$PLUGIN_NAME -> $TARGET"
echo ""
echo "Add to ~/.claude/settings.json:"
echo "  \"plugins\": [\"$TARGET\"]"
echo ""
echo "Skills available after restart:"
shopt -s nullglob
for skill in "$PLUGIN_DIR"/skills/*.md; do
  echo "  /$(basename "${skill%.md}")"
done
shopt -u nullglob
