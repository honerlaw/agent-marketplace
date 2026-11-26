# Scratchpad: lorestrom-connect-via-agents-page

> **Ephemeral working memory.** Most of what lands here is noise — small
> decisions that don't matter, dead ends, momentary confusion. At feature
> completion, run `minerva:promote`: significant items get promoted to
> `.minerva/knowledge/`, `proposal.md` gets updated to match reality, and
> the raw scratchpad is archived.

## Decisions 2026-11-26

- [reviewed — clean] scope check: one unit, one PR, no phases (tier: reviewer — could not rule out blast radius: user-facing plugin text and a version bump; parallel wave); noted: name the skills that already defer to the host adapter, scan the whole plugin for the banned phrase, take care with runtime.md's prose version line, the Agents URL and its content are assumptions from outside the repo (criterion 7 gates ship)
- [reviewed — clean] approach: A, one canonical connect block per host adapter with every other mention pointing at it (rejected B: the plugin builds the command — the client id is per deployment and an org id is the same unanswerable question; C: README only — the skills that say what a stopped write tells the person keep the unanswerable text) (tier: reviewer — rewrites existing text, so not additive; could not rule out existing interface change or knowledge tension, both tested and not holding; parallel wave); adopted non-blocking notes: name the deferring skills, drop COMPATIBILITY's endpoint placeholder, say what to do when Agents says Claude Code can't connect yet
- [reviewed — folded] whole-proposal: C1 tests/test_install_plugin.py's installed-version assertion added to the bump list, runtime.md's prose version line named; C2 claude.md describes the command in prose, the ban scans plugins/lorestrom/ only; C3 deferred-tool search before suggesting /mcp sign-in; C4 no Codex command named; C5 criterion 7 counts a 200 or a sign-in redirect, checked by hand (tier: reviewer — scrutiny: existing interface change, version- and wording-pinned tests; parallel wave; restart check: approach and scope unchanged, no fold from those gates touched Goal or criteria — kept)
- [rechecked — clean] whole-proposal: fold-audit found C1–C6 addressed; low notes (the deferring skills' list is unverified by it — the criterion 1 test would catch a miss; the can't-connect sentence adds a fourth situation, untested) need no change

## Work notes 2026-11-26

- The connect guidance lives once per host: claude.md's and codex.md's "Lorestrom tools" sections. storage.md's write-stop remedy, link.md step 2, README Setup and COMPATIBILITY point at the Agents page; init/migrate SKILL.md already said "as the host adapter shows" and are unchanged.
- claude.md keeps its deferred-tool search first; the sign-in advice applies only when no Lorestrom tools exist, deferred or not. A test pins that order.
- Criterion 6's "full suite" is CI's: `pytest tests/` (2565 passed), the skill and compatibility eval dry-runs, and knowledge lint. `pytest` from the repo root also collects `mcp/*/tests`, which need each server's own dependencies (`httpx2` missing locally), unrelated.
- README gained a "Connecting (0.5.1)" bullet in "This version", so a reader of the release notes sees the change.
