# Proposal: related-backfill

**Date**: 2026-06-03
**Status**: Shipped (2026-06-03)

> The **cross-ref backfill** deferred by unit 026: author the initial `## Related` edges
> for the 9 early entries that have none. The other deferred item — **rename-APPLY** — is
> **re-deferred** with recorded rationale (the live corpus has zero non-conforming files:
> no fixture, speculative tooling, YAGNI).

## Goal

Author the initial `## Related` cross-reference edges for the 9 entries the live
`migration_status` inventory reports as having none —
001, 002, 003, 005, 006, 007, 008, 009, 014 — wherever a **genuine** relationship exists
(entries may legitimately stay standalone). A one-time **work unit** using only existing
tested machinery (no new skill / script / test surfaces); **the corpus itself is the
deliverable**.

## Why

The 9 entries predate the cross-reference convention
([[015-constraint-knowledge-cross-reference-convention]]); the wiki's navigability
([[017-decision-knowledge-wiki-navigability-layer]]) depends on edges. `minerva:migrate`
(unit 026) inventories them, but authoring is the judged work its read-only check
explicitly deferred.

## Approach (panel-confirmed)

1. **Edge-proposal pass.** Read the 9 entries + the full 26-entry corpus. For each of the
   9, propose forward edges with labels **fenced to `see also` / `builds on`**
   (`supersedes` / `contradicts` only as unambiguous-only exceptions through the gate — a
   retroactive supersedes writes a dated banner on the target, heavy content machinery) +
   a **one-line justification grounded in both entries' bodies**, OR record the entry
   **"legitimately standalone"** with a reason (per `minerva:lint`'s orphan guidance). A
   standalone disposition adds **zero** edges — no placeholder links.
2. **Self-review justification gate** before any write: re-read the proposed set against
   the bodies; drop non-load-bearing edges. The **per-edge disposition table** recorded in
   the scratchpad (entry → target → label → justification, or standalone + reason) is the
   **pinned completion artifact** the completion panel judges.
3. **Forward writes ONLY via `knowledge_edits.add_related_link`** — never freehand Edit
   ([[016-constraint-promote-narrowed-never-overwrite]]-safety is a property of the
   editor: dedupes via `_related_has_target`, creates the block at EOF when absent,
   `body_complement`-preserving, terminal-`## Related` asserted). The write driver is a
   throwaway `python3` invocation importing the function and writing the returned text
   back (no committed script — the function IS the reference editor and only the terminal
   `## Related` span changes).
4. **One `knowledge_fix.py` pass adds ALL reciprocals** (single-pass accumulate-per-target,
   pairs validated against the closed-vocab table before any write); detector verifies
   clean. **Forwards + reciprocals land in a single atomic commit — a hard CI
   requirement**: `tests/test_knowledge_lint.py::test_live_knowledge_clean` asserts zero
   error-severity findings on the live corpus, and missing reciprocals / broken links are
   error-severity, so a forwards-only commit would fail CI.
5. **Honest residual:** after the backfill, `migration_status`'s `entries_without_related`
   equals exactly the recorded legitimately-standalone set — a **non-empty residual is a
   PASS**, not a miss.
6. **Closing synthesize — POST-promote.** Promote writes entry 027 first; then
   `minerva:synthesize` refreshes `overview.md` with the **explicit in-place-drift
   rationale** (9 entries' `## Related` blocks reshaped — the synthesis watermark is a
   new-scope-only floor that cannot see in-place edits, and the bare count
   `unsynthesized=[027]` would wrongly self-skip via the one-minor-entry threshold).
   Post-promote ordering makes "watermark → corpus max (027)" satisfiable and covers the
   new entry in the same refresh.
7. **Promote records** the backfill decision, the **rename-APPLY re-deferral** (zero live
   instances → no fixture → speculative, YAGNI), and a **reusable-backfill-skill candidate
   followup**.

## Success criteria

1. Each of the 9 entries is explicitly dispositioned **pre-write** in the scratchpad's
   per-edge disposition table: forward edges (fenced label + one-line body-grounded
   justification) or legitimately-standalone (+ reason).
2. All entry writes go through `knowledge_edits.add_related_link`; **forward edges only**
   (the fixer owns all reciprocals); no freehand Edit of any entry.
3. One fixer pass adds the reciprocals; the detector reports clean; forwards + reciprocals
   land in a **single atomic commit** (no transiently-red commit).
4. `migration_status`'s `entries_without_related` residual equals the recorded standalone
   set (non-empty = PASS).
5. Post-promote, `minerva:synthesize` runs with the stated drift rationale and refreshes
   `overview.md` (synthesis-watermark → corpus max 027; zero `link_rot`).
6. Full enumerated CI suite green; no frozen file touched
   (`knowledge_lint.py` / `knowledge_fix.py` / `knowledge_spans.py`).
7. The promote entry records the backfill decision, the rename-APPLY re-deferral, and the
   reusable-backfill-skill candidate followup.
8. *(added by replan 2026-06-03)* `body_complement`, `_related_has_target`, and
   `add_related_link` are fence-aware (header-location-only, via `_fence_flags` /
   `FENCE_RE` from `knowledge_spans.py`); the crash, false-dedupe, and
   fenced-only-header cases are covered in `tests/test_promote_invariant.py` and green;
   the 7 existing property tests pass unchanged; a bug knowledge entry records the
   latent landmine (cross-ref 023).

## Open Questions

- None load-bearing.

## Out of scope

- **rename-APPLY** (re-deferred: zero live non-conforming files — revisit when a real
  legacy corpus provides a fixture).
- **A reusable backfill skill** (candidate followup; doing the judgment by hand once is
  the spike that would inform its shape).
- Touching entry bodies outside the `## Related` span; `index.md` (all 9 already
  catalogued — only promote's watermark bump).
- `supersedes` / `contradicts` edges except unambiguous-only exceptions through the gate.
