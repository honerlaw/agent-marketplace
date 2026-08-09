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
