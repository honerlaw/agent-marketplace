# Agent Marketplace

A personal plugin marketplace for AI coding agents. Each plugin in `plugins/` is self-contained with its own skills and automation scripts.

## Install a Plugin

```bash
git clone https://github.com/honerlaw/agent-marketplace
cd agent-marketplace
./install.sh utils
```

Restart Claude Code — that's it. The installer handles Claude Code settings registration automatically (and Python dependencies / Playwright if the plugin ships any).

## Update

```bash
git pull  # symlink keeps the plugin live immediately
```

## Plugins

| Plugin | Skills | Description |
|--------|--------|-------------|
| utils | `humanizer` | Miscellaneous utility skills |
| minerva | `minerva:init` `minerva:propose` `minerva:replan` `minerva:work` `minerva:promote` `minerva:review` `minerva:ship` | Durable record discipline for software work — proposal → work → replan → promote → review → ship, with a `.minerva/` persistence hierarchy of knowledge artifacts, proposals, and scratchpads |
