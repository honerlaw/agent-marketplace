# Scratchpad: resolve-entry-type-tolerantly

## Quick decisions 2026-08-09
- [decided] seed: taken from chat context — the "entries that can't be catalogued" loose end
  left after #51. Investigating it CORRECTED my own closing claim from that turn: I had said
  "46 entries typed `reference`". The corpus has 4 `reference` entries; the 46 refusals were
  42 entries whose `**Type**` line the parser cannot see, plus 4 genuinely out-of-vocab.
  Measured before proposing rather than building on the wrong premise.
- [decided] scope check: single unit. One function (`parse_entry`), one regex plus a two-step
  fallback, plus tests. No public-interface change, no consumer change — `declared_type` keeps
  its type and meaning, it just stops being `None` for entries that do declare one.
- [decided] approach: resolve from body field (3 spellings) → frontmatter `metadata.type` →
  filename segment. Dominant on evidence: filename type and declared type agree 642/642 across
  both corpora, so the fallback can only fill a gap. Rejected migrating the 42 entries (fixes
  one corpus, not the parser) and frontmatter-only (covers 3 of 42 — the measurement is what
  showed the plain-`Type:` and colon-inside variants dominate).
- [decided] whole-proposal soundness: bounded and reversible. Body-field-first ordering means
  an author's explicit statement always wins, so the change is additive by construction.
- [decided] scope boundary: `knowledge_lint` still calls a shared NNN a hard error (63), which
  sits oddly now the fixer keys on stems. Left OUT — whether that becomes a warning is a policy
  call with a real argument each way (harmless now vs. still a convention worth enforcing), and
  it is not blocking. Recorded as a follow-up instead of quietly bundled in.
- [decided] completion verification (never elided): all 7 criteria met against the diff.
  Unresolvable types 42 -> 0 on the 629-entry corpus; `type 'None'` lint errors -> 0; errors
  91 -> 84 from the parser alone and -> 65 once the fixer can finally relocate those lines;
  71 knowledge tests pass. The 4 failures in tests/test_pull.py are a different plugin and
  fail identically on main.
- [decided] review triage (solo): two findings, both my own, both FIXED rather than noted.
  (1) The frontmatter regex used a lazy `.*?` under DOTALL, so it could reach past the closing
  `---` and read a `type:` line out of the body or a fenced example — split into an explicit
  block match plus a search inside it, with a test. (2) A comment said "29 entries" where the
  proposal says 42; 29 is the count for that regex line specifically, so the comment now says
  both numbers. Also caught at promote: the drafted `## Related` cited
  `057-constraint-a-corpus-outlives-...`, an entry that does not exist — repointed at 026 and
  018, which do.
- [decided] promote partition (solo): PROMOTE 058 (read authored metadata from where it is —
  the fallback-chain ordering as the safety property, and measure the last resort's concordance
  before trusting it). MERGE: proposal Approach matches what shipped. TODO -> followups.md x3.
  DISCARD: routine decision lines.

## Promote 2026-08-09
Promoted. Knowledge: 058-pattern-read-authored-metadata-from-where-it-is.
Follow-ups: followups.md (3). Escalations this run: 0.
