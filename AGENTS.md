## minerva

This project uses [minerva](https://github.com/honerlaw/agent-marketplace/tree/main/plugins/minerva) for durable record discipline.

- `.minerva/knowledge/overview.md` — theme-grouped synthesis of everything known. Read first to orient (absent until `minerva:synthesize` first runs — fall back to the index).
- `.minerva/knowledge/index.md` — the catalog, one line per entry. Look up specifics here; drill into entries via their `[[YYYY-MM-DD-type-slug]]` links only when a theme bears on your task.
- `.minerva/reference/` — present-tense operational docs (architecture, glossary, conventions): how the system works now. Read on demand.
- `.minerva/work/` — historical proposals and replans. Grep when you need the reasoning behind a past feature.

Active work units live at `.minerva/work/<date-slug>/`. Load the installed `minerva:using-minerva` skill for the full methodology using your host's skill loader. In Claude Code use `/minerva:using-minerva`; in Codex select `$minerva:using-minerva`. Follow the loaded plugin's runtime contract for tools and installed paths.
