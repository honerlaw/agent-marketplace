# Scratchpad: move-lorestrom-to-its-own-repo

## Decisions 2026-11-26

- [reviewed — clean] scope: one unit, one agent-marketplace PR; the new repository is created, pushed and green (and installed from live) during work, before the removal PR (Skeptic: accept; non-blocking README-paragraph, old-install guidance, live-install gate and minerva.ref-on-main folded) (tier: reviewer — high blast radius: a new public repository and a removal from a public marketplace)
- [reviewed — folded] approach A, history-preserving split with tests ported: Skeptic revise (blocking: moved tests need minerva's scripts on sys.path; a minerva pin silently weakens the enforced sync rule) → folded (conftest + pinned and daily drift jobs) → fold-audit not clean (blocking: `test_lorestrom_units` loads `lorestrom_runtime` at import, which needs `plugin_guard`; the backend test reads agent-marketplace's own knowledge corpus) → revised to "minerva required, never skipped" with the corpus read from the minerva checkout → Adjudicator: settled (wording notes folded) (tier: reviewer — existing interface change and knowledge tension with 2026-11-23-decision-lorestrom-is-a-separate-lorestrom-only-plugin)
- [reviewed — folded] whole proposal: Skeptic accept with non-blocking concerns (old-install pointer with commands, grep-based criterion 6, Codex owner/repo syntax — verified `codex plugin marketplace add` takes owner/repo[@ref] — named secret scan, six-commit wording, why 0.6.0) → folded; the approach gate's fold-audit and Adjudicator covered the revised text (tier: reviewer — high blast radius)

## Work notes

- Repo `onerlaw/lorestrom-plugins` is free; the gh account is an admin of `onerlaw`.
- `git subtree split --prefix=plugins/lorestrom` (scratch clone) yields the six release commits, 0.1.0 to 0.5.1; the history scan finds no token or key shapes, no secret files and no `/Users/` paths.
