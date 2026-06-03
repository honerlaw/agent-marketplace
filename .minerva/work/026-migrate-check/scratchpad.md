# Scratchpad: migrate-check (026)

## Panel decisions 2026-06-03

- [3/3 accept] scope check: single READ-ONLY unit (detect-and-report only). Both agents
  agreed it's one unit; revise/accept was about scoping read-only — strip
  orchestration/renames/cross-ref-backfill to deferred APPLY follow-ups.
- [2/3 accept → revise → 3/3 accept] approach (A′ over B/C): round 1 Skeptic revise
  (state the bright line; cite-don't-re-emit; plain-primitive dict). Round 2 folded —
  bright line = the ENTRY_RE false-clean blind spot only migrate inventories; cite
  lint/synthesize not re-render; dict returns own primitives, no Finding namedtuples.
  4 build conditions: shape-not-health disclaimer; named RESERVED_NONENTRY allowlist;
  code-token contract anchors; reuse parse_entry + tmp_path tests.
- [3/3 accept] whole-proposal: both verified against the live repo (false-clean gap real
  at all 3 glob sites; parse_entry crash-free on malformed conforming-named entries; live
  corpus reports zero non_conforming_files). 4 LOW build items folded (below).

## Build-time items (carry into WORK)

1. SKILL body MUST state: migration_status is a SHAPE check, NOT a health check — a clean
   inventory still requires a green minerva:lint + minerva:synthesize pass.
2. Named extensible `RESERVED_NONENTRY = {"index.md","overview.md"}` (future log.md).
3. Contract anchors on stable CODE tokens (migration_status, non_conforming_files) — must
   appear LITERALLY in the SKILL body (enumerate the dict keys in the checklist prose).
4. Pin malformed-input robustness as an explicit test (conforming-named entry w/ no Type /
   no Related → counted in entries_without_related, not crash).
5. Checklist states renames + cross-ref backfill are NOT automated (manual / future APPLY).
6. using-minerva WHEN row = "one-time, pre-existing populated corpus" (not recurring).
7. Reuse parse_entry/_strip_fences (fence-aware, 023); plain-primitive dict (no Finding).
8. tests/test_migration_status.py appended to evals.yml enumerated list.

- [3/3 accept] completion verification: all 7 criteria independently re-verified (162
  tests, contracts 88 incl. migrate, runner exit 0, live corpus clean, no frozen file
  touched, all anchors resolve incl. standalone minerva:lint).
- [skipped — small] review triage: 4 LOW findings, no medium+ (skip predicate met). FIX 3
  (cheap): docstring `_strip_fences` is transitive-via-parse_entry not direct; parse_entry
  returns a dict not None; SKILL Out-of-scope note that glob is non-recursive (consistent
  w/ frozen toolchain). SKIPPED #3 (case-insensitive-FS edge — platform-specific, no fix
  required, consistent on CI/Linux). Evidence: reviewer found no load-bearing issues.

## Review triage 2026-06-03

- FIX: migration_status.py docstring — `_strip_fences` is transitive via parse_entry; "returns a dict" not None. (low)
- FIX: migrate/SKILL.md Out of scope — non-recursive glob note. (low)
- SKIP: case-insensitive-FS Index.md edge — platform-specific, consistent on CI. (low)

## Notes
