# Scratchpad: dot-minerva-init

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `/promote`: significant items get promoted to
> `.minerva/decisions/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## 2026-05-18 — execution plan (phases)

Phased TDD, one commit per phase:

1. Path migration in the four existing commands (`propose`, `replan`, `work`, `promote`) — update tests first to assert `.minerva/work/` and `.minerva/decisions/` substrings, then update command bodies.
2. `using-minerva` skill update — detection switches to "single `.minerva/` dir check"; body path references prefixed.
3. Plugin README file-layout diagram update.
4. `/init` command — TDD, new structural test then command body.
5. Root README + plugin README — mention `/init` in the command tables.

Tests should always go green at the end of each phase. Avoid touching the proposal/scratchpad in the work dir from the commands themselves — the dogfood loop is conceptual, not enforced.
