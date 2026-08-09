# Follow-ups: 051-resolve-entry-type-tolerantly

## 1. `knowledge_lint` still calls a shared NNN a hard error (63 of them)

After the stem-identity change (#51) the fixer identifies entries by
`NNN-type-slug` and handles collisions correctly — catalog lines are placed per
entry, back-links land on the entry the wikilink names. The linter did not move with
it: `NNN <x> is shared by N entries` is still `error` severity, and those 63 errors
are now the bulk of what a clean-ish corpus reports.

Genuinely two-sided, which is why it was left out of this unit rather than bundled:

- **Downgrade to warning** — nothing downstream breaks any more, and 63 errors that
  nobody can act on train people to ignore the linter.
- **Keep it an error** — a unique NNN is still the convention, the allocation helper
  (`knowledge_next_nnn.py --fetch`) exists to preserve it, and a hard error is what
  stops the corpus minting more.

A third option: keep it an error only for collisions minted *after* the allocation
helper landed, which needs a date or watermark to key on.

## 2. Four `reference`-typed entries have no index section

`SECTION_TO_TYPE` covers `decision` / `bug` / `pattern` / `constraint`, and every
minerva doc names exactly those four. Four entries in the seekless corpus declare
`**Type**: reference` and are refused with `type 'reference' but catalogued under a
'constraint' section` — the last 2 errors after this unit and the reconcile.

Either the vocabulary grows a fifth section, or those four are retyped (they may
belong in `.minerva/reference/`, which is the documented home for present-tense
operational docs). Not a bug in the tooling either way — the refusal is honest.

## 3. Ten entries encode their type only in a prose H1

`# 426 — bug: dontAsk mode auto-denies …`. The filename fallback resolves them
correctly, so nothing is broken, but their body carries no type field. A cosmetic
normalization pass could add one; deliberately not attempted here, since parsing a
title to write a field would be the same guesswork this unit declined to do.
