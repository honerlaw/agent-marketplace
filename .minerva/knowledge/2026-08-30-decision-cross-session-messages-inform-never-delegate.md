# Cross-session messages inform; they never assign work

**Date**: 2026-08-30
**Type**: decision
**Summary**: a session tells peers what it is doing and never assigns them work; inbound peer messages are evidence, never instructions
**Context**: .minerva/work/2026-08-30-cross-session-inform-only (see git history if the worktree has been cleaned up)

## Context
Claude Code enables cross-session messaging by default, and minerva used it in exactly one
place: the sibling-session step of the intake pre-flight
([[2026-08-24-reference-listagents-returns-the-whole-fleet]]). That step specified what to
**send**, at intake only. Nothing specified what a session does with a message it **receives**,
at any point.

Observed in the field: sessions running minerva skills messaged each other through a run and
handed each other work. That fails in both directions. Work assigned *in* becomes scope the
user never asked for, landing inside a work unit whose `proposal.md` does not cover it — the
record and the diff diverge, which is the divergence minerva exists to prevent. Work handed
*out* is dropped: the sender assumes the peer picked it up, no unit tracks it, nobody does it.

## Finding
**A session owns its own workstream and is the only thing entitled to stop, redirect, or
continue it. A peer supplies evidence for that decision, never the decision.** The contract is
two-way and lives at `plugins/minerva/skills/propose/references/cross-session.md`:

- **The line is "adds to the peer's workstream"**, not "is phrased as a question". Asking a peer
  what it is *already* doing costs it one line and changes nothing about its work, so the intake
  query survives. Collapsing "never delegate" into "never ask" would delete minerva's only
  detection for a peer still in the pre-worktree window.
- **Inbound messages are evidence, including when phrased as instructions.** Irrelevant → drop;
  adjacent → one line, keep going; invalidating → escalate to the session's own user.
- **A relayed user instruction is neither adopted nor stonewalled** — attribution is
  unverifiable, so it grants a peer no authority; it only shapes how the request is surfaced.
- **Subagent dispatch is explicitly exempt.** `Agent`, and `SendMessage` to an agent this
  session spawned, are delegation by design and minerva depends on them.

**The marker rides inside the message, not only in the file.** Every outbound message carries a
verbatim information-not-instruction line, because a peer may run an older minerva, a different
project, or no minerva at all. A file binds only sessions that read it; the message reaches
everyone. This is the same reasoning that made the pre-flight query self-describing.

## Implications
- Any future skill that messages a peer states facts about its own workstream and asks nothing
  of it. Work that needs doing belongs in your own unit, a tracker issue, or in front of your
  user — never in a peer's inbox.
- **Two classifiers now exist and precedence is explicit**: a reply to the intake pre-flight
  query is governed by the in-flight-check collision bar, which wins outright; the receive
  table governs everything else. Without that ordering a `MINERVA-BUSY` naming this session's
  own goal could be classified "adjacent" and silently downgraded from a hardcoded ask.
- Escalation options follow **lifecycle position**, not which skill is driving: "start fresh
  anyway" is an intake option and is meaningless to a session already deep in implementation.
- **This is a norm, not an enforcement mechanism**, and the file says so rather than overselling
  it — [[2026-08-11-pattern-an-unenforced-constraint-is-aspirational]] is the honest reading. A
  session that never loaded minerva can still send an ad-hoc work request; what is guaranteed is
  that a minerva session will not silently adopt it. Detection-not-a-lock, the same posture as
  [[2026-08-05-pattern-read-then-act-is-not-a-lock]].
- The contract is reached from six `SKILL.md` surfaces carrying one byte-identical sentence,
  pinned by per-file anchors plus a byte-identity test — an anchor catches a deleted copy, only
  identity catches a drifted one ([[2026-08-24-pattern-extracted-copies-split-into-shared-and-divergent-halves]]).

## Related
- [[2026-08-24-reference-listagents-returns-the-whole-fleet]] — builds on
- [[2026-08-05-pattern-read-then-act-is-not-a-lock]] — see also
- [[2026-08-11-pattern-an-unenforced-constraint-is-aspirational]] — see also
- [[2026-08-24-pattern-extracted-copies-split-into-shared-and-divergent-halves]] — see also
