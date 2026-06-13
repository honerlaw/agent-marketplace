# A prose skill wraps a sibling Python tool via its importable API, anchored to the working-tree root — not the CLI, not CWD-relative paths

**Date**: 2026-06-03
**Type**: constraint
**Context**: .minerva/work/022-knowledge-lint-skill (see git history if the worktree has been cleaned up)

## Context

`minerva:lint` is a prose skill that needs the mechanical findings produced by a
sibling Python tool (`scripts/knowledge_lint.py`). Two plausible ways to consume it
— scraping the CLI's stdout/exit code, or importing its functions — are not
equivalent, and the path handling has a worktree trap. This entry records the rule
for any skill that wraps a script. Complements
[[007-constraint-skills-must-call-tools-not-prose]] (which says *call* tools rather
than describe them; this says *how* to call a sibling script).

## Finding

A prose skill that wraps a sibling Python tool should:

- **Consume the tool's importable API, not its CLI surface.** Call the module's
  functions from a `python3 -c` snippet (`from knowledge_lint import lint_knowledge`)
  and read the structured return value. Do **not** branch on the CLI's exit code:
  `knowledge_lint.py` returns `1` only on *error*-severity findings and `0` on
  warnings-only, so exit-code branching silently drops warning-severity findings
  (e.g. a stale-slug warning). The API returns the full list regardless.
- **Resolve the scripts directory via plugin cache first, falling back to the
  working-tree root.** Compute once as:
  ```bash
  PLUGIN_SCRIPTS=$(find "${HOME}/.claude/plugins/cache/agent-marketplace/minerva" \
    "${HOME}/.claude/plugins/minerva" -maxdepth 2 -type d -name "scripts" 2>/dev/null | head -1)
  SCRIPTS="${PLUGIN_SCRIPTS:-$ROOT/scripts}"
  ```
  Use `$SCRIPTS` (not `$ROOT/scripts`) for the `sys.path` insert and direct
  invocations. The real script files live in `plugins/minerva/scripts/` and are
  deployed to the plugin cache; the repo's `scripts/` directory holds relative
  symlinks to them for development. **Never use CWD-relative paths** — invoked from
  a subdirectory they raise `ModuleNotFoundError` or, worse, glob an empty/wrong
  directory and silently produce a falsely-clean result from a tool whose whole value
  is trustworthy coverage.

## Implications

- **`git rev-parse --show-toplevel` resolves to the *current* working tree's root —
  the active worktree when invoked mid-lifecycle, not the main checkout.** For
  `minerva:lint` this is deliberate: it audits the corpus of the branch you're on,
  matching the per-branch semantics of the unit-021 CI drift gate (which lints the
  PR branch's corpus). A skill that genuinely needs the *main* checkout cannot use
  `--show-toplevel` from inside a worktree — it would get the worktree root.
- Future skills that wrap `scripts/` tools (e.g. the deferred Phase-B.3 fix-applier)
  follow this rule: import the API, anchor to `$ROOT`, never scrape the CLI.
- This is why the detector exposes plain importable functions (`lint_knowledge`,
  `parse_entry`) and not only a CLI — the API is the supported integration surface.

## Related
- [[020-decision-minerva-lint-read-only]] — see also
- [[007-constraint-skills-must-call-tools-not-prose]] — see also
- [[037-constraint-fence-scans-import-fence-re]] — see also
