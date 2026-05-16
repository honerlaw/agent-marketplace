# Claude Marketplace

A personal plugin marketplace for Claude Code. Each plugin in `plugins/` is self-contained with its own skills and scripts.

## Install a Plugin

```bash
git clone https://github.com/<you>/claude-marketplace
cd claude-marketplace
./install.sh financials
```

Add the printed path to `~/.claude/settings.json` under `"plugins"`, then restart Claude Code.

## Update

```bash
git pull  # symlink keeps the plugin live immediately
```

## Plugins

| Plugin | Skills | Description |
|--------|--------|-------------|
| financials | `/pull-finances` `/spending-summary` `/spending-breakdown` `/recurring-expenses` `/cross-account` | Pull and analyze personal finances from Truist, Amex, Citi |
