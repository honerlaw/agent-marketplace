# Upgrading: the finding count is expected to rise

The first `minerva:lint` run after upgrading minerva will usually report **more** findings
than the same corpus reported before, and that is not damage. The `## Related` edge model
was unified so the linter and the fixer read one edge set; the old detector saw only a
line's first wikilink, so every additional target on a shared line was invisible to it. On
one 637-entry corpus the count went **41 → 59** — the extra 18 were always real and merely
unreportable.

Two consequences worth stating, because one of them cost a real team a post-merge surprise:

- **Do not read the rise as a regression** introduced by the migration or the upgrade.
- **Re-baseline any pending finding-count comparison.** A "verified finding-neutral, N
  before and N after" claim made under the old detector does not survive the upgrade. In
  the case this note comes from, a migration measured as exactly neutral under the old
  detector produced 0 findings before merge and 9 after, on byte-identical content.


## Why the old number was wrong, not the new one

The linter derived a `## Related` line's edges from a start-anchored pattern, so on a line
like `- [[a]] / [[b]] — label` it saw only `a`. The fixer used a differently-anchored
pattern and saw neither. Unifying them on one shared `related_edges()` means every
wikilink in the block is now an edge — which is what the block always meant.

So the rise is the detector catching up to the corpus, not the corpus degrading. The
entries the new findings point at were already missing their reciprocal links; nothing
could report it.

## What to do on first run after upgrade

1. Run `minerva:lint` and record the new count as the baseline. Do not compare it against
   any number recorded before the upgrade.
2. Run `minerva:lint-fix` (or `minerva:cleanup`'s reconciliation) to write the newly-visible
   reciprocals. Most of the delta is mechanically repairable.
3. Re-run `minerva:lint`. What remains is genuine, and was genuine before — it was just
   unreportable.
