# Extracted copies split into a shared half and a divergent half — invert the invariant per half

**Date**: 2026-08-24
**Type**: pattern
**Summary**: after extracting a repeated block, byte-identity is right for the shared half and wrong for the rung-specific half; test both
**Context**: .minerva/work/2026-08-24-cross-session-preflight

## Context
Four orchestrator skills each restated the same pre-flight protocol inline. Extracting it to
one shared file left each surface with a short block that cites the file.
[[2026-08-22-pattern-repeated-blocks-may-be-deliberate-divergence-not-duplication]] warns
that such blocks are often divergent on purpose and that a byte-identity test over them
either cannot pass or passes vacuously. That is true here — and incomplete.

## Finding
**The block did not divide into "shared" or "divergent". It divided into a shared half and a
divergent half, inside every copy**, and the two halves need *opposite* invariants:

- The **summary half** — what the check does, that it is not a lock — was written once and
  pasted four times. Drift between copies is always a bug. **Byte-identity is exactly right.**
- The **qualifier half** — who adjudicates that rung's other gates, how much user contact the
  rung permits at all — differs per surface on purpose. Byte-identity here would be the
  vacuous test the 08-22 entry warns about. **Per-copy presence of its own clause is right.**

Testing only one half leaves the other free to rot while the suite reads green. The first
draft pinned only the qualifier half, and an independent review caught that a fifth evidence
source would have left four stale summaries with nothing going red.

## Implications
- After extracting a repeated block, **partition what remains** before choosing a test. Ask
  of each sentence: is drift here always a bug, or sometimes the point?
- A "we removed the duplication" claim is unfinished while a verbatim paraphrase of the
  extracted content still sits in every caller. Either shorten it to a pointer, or pin it.
- Tie the summary to the source: a check asserting the summary's "four evidence sources"
  still matches the protocol file's actual step run turns a silent staleness into a red build.
- **Mutation-test each new guard.** Three mutations — drift a summary, add a fifth source,
  flatten a qualifier — each reddened exactly one guard, which is what distinguishes these
  from [[2026-08-10-pattern-presence-assertions-rot-into-green-lies]].

## Related
- [[2026-08-22-pattern-repeated-blocks-may-be-deliberate-divergence-not-duplication]] — builds on
- [[2026-08-10-pattern-presence-assertions-rot-into-green-lies]] — see also
- [[2026-08-11-pattern-a-comment-cannot-enforce-a-shared-invariant]] — see also
