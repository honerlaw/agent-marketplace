# Post-`minerva:promote` scratchpad is the canonical empty state for downstream skills

**Date**: 2026-05-19
**Type**: constraint
**Context**: .minerva/work/2026-05-19-add-ship-skill

## Context

`minerva:promote` archives the live `scratchpad.md` to `archive/scratchpad.md` and replaces the live file with a one-line marker:

```
Summarized at minerva:promote on YYYY-MM-DD — see archive/.
```

This is what `minerva:promote`'s own idempotency check looks for on re-run.

Downstream minerva skills that read `scratchpad.md` for live notes (e.g. `minerva:ship` skims it for commit-message highlights and PR-body bullets) will encounter the marker — not an empty file, not bullet content — whenever they run after `minerva:promote` in the canonical lifecycle order (`review → promote → ship`). If those skills silently fall back when they don't find bullets, the post-promote state still works, but the contract is implicit and easy to miss when authoring a new skill.

## Finding

The post-promote marker is the **canonical empty state** for `scratchpad.md`, not an edge case. Any minerva skill that reads scratchpad content as input must:

- Treat the marker line as "no live notes to consume" and fall back to other sources (`proposal.md`, git history, etc.) for whatever it was trying to extract.
- Not log a warning, error, or "scratchpad is unexpectedly empty" message — this is the canonical state, not a problem.
- Not append to the scratchpad blindly without preserving the marker (or knowingly re-entering the live-notes phase, e.g. how `minerva:review` appends review-fix entries under a `## Review finding YYYY-MM-DD` header, which intentionally triggers another promote cycle).

`minerva:ship`'s commit-message step encodes this explicitly: if `scratchpad.md` is the marker, fall back to `## Goal` + filenames.

## Implications

- New minerva skills that consume scratchpad content should call out the marker case in their protocol description so future readers don't trip over it.
- Knowledge entries are read at the start of every conversation; SKILL.md files aren't. This constraint lives here so a future agent authoring a new minerva skill doesn't have to reverse-engineer the contract from `minerva:promote`'s archive step.
- If the marker format ever changes again (see `.minerva/knowledge/002-bug-promote-idempotency-check-misses-old-marker.md` for prior history), downstream skill protocols that hard-code the marker text must be updated alongside the promote skill, or made lenient about the exact string.

## Related
- [[2026-05-19-bug-promote-idempotency-check-misses-old-marker]] — see also
