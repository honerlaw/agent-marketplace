# Scratchpad: untrusted-ref-names

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Decisions 2026-11-22
- [user] intake: a separate patch release ahead of other in-flight work; the user merges the PR; no exploit detail in public records
- [solo] in-flight check: no collision — no open PR, issue or matching branch; no live peer in this project (tier: hardcoded check, nothing found)
- [solo] open-issue match: no open issues (tier: hardcoded check, nothing found)
- [reviewed — folded] scope check: C1 added promote's issue search; C2 status inventoried; C3 printed commands covered by the unit-id rule (tier: reviewer — scrutiny: blast radius, ambiguity; parallel wave)
- [rechecked — residual folded] scope check: C2 partially (status's fallback now takes the refs/ prefix); two wording residuals folded
- [reviewed — folded] approach: A kept; C1 unit ids checked by a no-input listing snippet and the Goal reworded to "checked id"; C2 PR state per branch; C3 explicit refs; C4 bare-mode names keep their shape (tier: reviewer — scrutiny: existing interface change, ambiguity; parallel wave)
- [rechecked — escalated] approach: F1 (remote-only default branch has no start point) → Adjudicator
- [adjudicated — escalated] approach: F1 unresolved — refs/heads/<name> fails where only the remote ref exists → user
- [escalated to user] approach: F1 — measured that today's form checks the worktree out on the default branch itself; user chose the local branch when present, otherwise origin's ref, as start point and for reads, with --no-track (escalation counter: 1)
- Residuals folded after the ruling: F2 bare-mode components start with a letter or digit and fall back to a fixed word when empty; F3 the shell, not the agent, takes commit ids from ls-remote; F4 an id from any source must equal a listed id
- [restart] whole-proposal: first-wave review discarded unread for folding — the approach fold rewrote the Goal; tier selected again on the merged draft: reviewer (scrutiny: blast radius, knowledge tension)
- [reviewed — folded] whole-proposal (restart): C1 criterion 3 narrowed to branch, ref and Python-source sites with the unit-id half tested separately; C2 --no-track enforced and tested; C3–C7 folded, the listing moves into minerva_runtime (tier: reviewer — scrutiny: blast radius, knowledge tension)
- [rechecked — residual folded] whole-proposal (restart): all seven addressed; residuals folded — the units command's compatibility and test coverage named, fetch-then-cut keeps today's tracking, allowed variables and the pointer assertion made exact
