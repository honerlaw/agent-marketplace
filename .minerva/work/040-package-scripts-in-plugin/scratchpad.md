# Scratchpad: 040-package-scripts-in-plugin

## Panel decisions 2026-06-13

- [skipped — small] scope check: single additive unit (evidence: 6 scripts + 4 SKILL.md updates + 1 knowledge entry, all co-dependent, one goal)
- [3/3 accept] approach selection: Option B (symlinks, single source of truth in plugins/minerva/scripts/; rejected A — sync burden; rejected C — incomplete)
- [2/3 accept, skeptic dissented, 2 votes] whole-proposal-acceptance: proceed (arbiter both rounds: dangling-symlinks / guard concern not load-bearing; no normal deployment reaches $ROOT/scripts fallback in plugin-only install)

## Panel concerns 2026-06-13

- [MEDIUM] Skeptic (R2): guard check `[ -d "$SCRIPTS" ]` not in proposal; arbiter ruled not load-bearing since plugin-only deployment always resolves PLUGIN_SCRIPTS before fallback
- [MEDIUM] Bash two-path discovery snippet (`ls -td ... | head -1`) not tested against live cache before implementation — verify during work phase
- [LOW] lint-fix direct invocation pattern is distinct from sys.path-insert pattern in other 3 skills — implementation must handle both explicitly
