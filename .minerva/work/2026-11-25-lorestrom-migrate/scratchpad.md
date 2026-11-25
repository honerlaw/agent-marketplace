# Scratchpad: lorestrom-migrate

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Decisions 2026-11-25
- [reviewed — clean] scope check: one unit, one PR, no phases (tier: reviewer — not provably small, multi-file; parallel wave); dismissed non-blocking: live dry-run (stays an open question), in-flight scale and stale init-handover text (both folded at whole-proposal)
- [reviewed — folded] approach: A (released-unit import) + new migrate skill, init reduced to the link; folded record-key change, other-branch warning, batch size with one confirmation per run, changed-record handling, abandoned-import wording, storage/using-lorestrom/test surfaces (tier: reviewer — scrutiny: existing interface change, genuine ambiguity; parallel wave)
- [rechecked — residual folded] approach: C4 partially (changed records still landed in keep with no path out) — wired to the leftovers offer; new spec gaps (minerva-branches unlisted, gh absent) folded
- [reviewed — folded] whole-proposal: C1 removal statuses, C2 unit-state criterion, C3 batched in-flight yes, C4 clean agent file/.gitignore, C5 goal reworded + final report, C6 id/collision checks, C7 branches (tier: reviewer — scrutiny: blast radius not ruled out; parallel wave; restart check: approach pick unchanged, no scope/approach fold touched Goal or criteria — kept)
- [rechecked — residual folded] whole-proposal: removal offered per run over done units; changed-record wording; unit_file_key added beside an unchanged record_key so lifecycle writers keep their restriction
