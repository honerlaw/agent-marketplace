# Agent Marketplace

A personal plugin marketplace for AI coding agents. Each plugin in `plugins/` is self-contained with its own skills and automation scripts.

## Install a Plugin

```bash
git clone https://github.com/honerlaw/agent-marketplace
cd agent-marketplace
./install.sh financials
```

Restart Claude Code — that's it. The installer handles Python dependencies, Playwright browser download, and Claude Code settings registration automatically.

## Update

```bash
git pull  # symlink keeps the plugin live immediately
```

## Plugins

| Plugin | Skills | Description |
|--------|--------|-------------|
| financials | `/pull-finances` `/spending-summary` `/spending-breakdown` `/recurring-expenses` `/cross-account` | Pull and analyze personal finances from Truist, Amex, Citi |
| minerva | `/init` `/propose` `/replan` `/work` `/promote` | Durable record discipline for software work — proposal → work → replan → promote, with a `.minerva/` persistence hierarchy of decisions, proposals, and scratchpads |
