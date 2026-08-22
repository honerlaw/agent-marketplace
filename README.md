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

<!-- Source of truth for each plugin's "Skills" cell: that plugin's `skills/` subdirectory. When you add a skill there, add its `plugin:skill-name` to the cell here too. -->

| Plugin | Skills | Description |
|--------|--------|-------------|
| utils | `humanizer` | Miscellaneous utility skills |
| minerva | `minerva:init` `minerva:explore` `minerva:propose` `minerva:replan` `minerva:grill-plan` `minerva:round-table` `minerva:work` `minerva:promote` `minerva:review` `minerva:ship` `minerva:cleanup` `minerva:propose-ship` `minerva:propose-ship-auto` `minerva:propose-ship-quick` `minerva:propose-ship-balanced` `minerva:debug` `minerva:lint` `minerva:lint-fix` `minerva:synthesize` `minerva:migrate` `minerva:migrate-fix` `minerva:backfill-followups` `minerva:using-minerva` | Durable record discipline for software work — proposal → work → replan → promote → review → ship, with a `.minerva/` persistence hierarchy of knowledge artifacts, proposals, and scratchpads. `propose-ship` conducts the whole lifecycle with user gates; `propose-ship-auto` replaces the gates with a 3-agent Proponent/Skeptic/Arbiter consensus panel (extracted as `minerva:round-table`, usable standalone on any decision), skipping the panel for small low-risk decisions via a fail-closed skip predicate; `propose-ship-quick` runs the same lifecycle but has the main model decide each point directly (no panel) for small fast changes, escalating to the user only when it genuinely can't decide; `propose-ship-balanced` sits between the two — the main model decides each point but dispatches one independent reviewer at the high-signal gates (scope, approach, completion), for medium changes that want a second opinion without a full panel. |
