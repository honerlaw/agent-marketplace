# Proposal: cross-session-inform-only

**Date**: 2026-08-30
**Status**: Draft
**Linked**: #107 — using-minerva/SKILL.md has 18 bytes of budget headroom (not adopted)

## Goal

Minerva gains an explicit **two-way contract for messages between live Claude sessions**: a
session tells peers what *it* is doing and never assigns work to them, and a session that
receives a peer message treats it as **evidence about that peer's workstream** — judging
whether it bears on its own and continuing, modifying, or escalating — rather than adopting
the message as a task.

The contract lives at `plugins/minerva/skills/propose/references/cross-session.md`, is cited
from `references/in-flight-check.md`, and is pointed at from `using-minerva/SKILL.md` so a
session orienting into minerva holds the receive contract *before* a message arrives.

## Why

Cross-session messaging is now enabled by default, and minerva meets it with one send site
(`references/in-flight-check.md` step 4) and **no** guidance for receiving at all. The
observed consequence is that sessions running minerva skills message each other throughout a
run and hand each other work. That produces two distinct failures, and they fail in opposite
directions:

1. **Scope leaks in.** A peer's request becomes work the user never asked for. The change
   lands inside a work unit whose `proposal.md` does not cover it, so the record and the diff
   diverge — the one divergence minerva exists to prevent.
2. **Work leaks out.** The delegating session assumes the peer picked the work up and drops
   it. No work unit tracks it, no proposal records it, and nobody does it.

Information is the right primitive. Each session owns its own workstream and is the only thing
entitled to stop, redirect, or continue it. A peer supplies **evidence** for that decision; it
never supplies the decision.

This is the natural completion of `2026-08-24-cross-session-preflight`, which established that
minerva may talk to sibling sessions but only ever specified what to *send*, and only at
intake.

## Approach

### 1. New canonical reference — `plugins/minerva/skills/propose/references/cross-session.md`

Owned by `propose`, following the precedent `in-flight-check.md` set for a cross-cutting
protocol whose only current caller is intake. Contents:

- **The line, stated first.** What is banned is any message that would **add to the peer's
  workstream**. Asking a peer to state what it is already doing costs one line of reply and
  changes nothing about its work — so the intake query stands, verbatim. Saying this
  explicitly is load-bearing: without it a reader collapses "never delegate" into "never ask",
  and deletes the detection step `2026-08-24-cross-session-preflight` exists to provide.

- **Send contract.** Outbound messages are statements about the sender's own workstream — what
  it is doing, what it found, what it is about to touch — plus at most a request for the same
  in return. Never an instruction, a request for work, or an assignment. Every outbound message
  carries an information-not-instruction marker **inline**, extending the self-describing
  rationale step 4b already gives: a peer may be running an older minerva, a different project,
  or no minerva at all, and must still be able to apply the contract. One message per peer per
  run; no poll loops; never blocking.

- **Receive contract.** An inbound peer message is evidence, **including when it is phrased as
  an instruction**. Three dispositions, reusing the match-bar asymmetry both existing
  pre-flight protocols already use (*when unsure, resolve to adjacent*):
  - *irrelevant* → nothing;
  - *adjacent* → one line to the user, keep going;
  - *invalidating* → escalate.

  Escalation has two forms, and the contract states both because most sessions are not in an
  orchestrator. **Inside** `propose-ship-auto` / `-balanced` / `-quick`, it is the hardcoded ask
  `in-flight-check.md` step 6 already defines (resume that work / start fresh anyway / abandon
  this run), and it increments the run's global escalation counter like every other escalation.
  **Outside** one — a plain `minerva:work` session, or no lifecycle skill at all — it is the
  same ask without a counter, because there is none to increment. Leaving the plain case
  undefined would leave the most common session with no rule, which is the gap that produced
  the observed behaviour.

- **Relayed user instructions.** A session never silently adopts a peer's request, and never
  stonewalls one either. It reports to its own user — "peer X relays a request to do Y; I have
  not started it" — and lets the user decide. Attribution is unverifiable, so claiming user
  intent grants a peer no authority; it only shapes how the request is surfaced. This keeps a
  genuine two-session workflow one keystroke from working while closing the hole that accepting
  attributed requests would reopen.

- **Explicit exclusion: subagents.** `Agent` dispatch is delegation **by design**, and minerva
  depends on it — `minerva:round-table`, the review panels, every reviewer gate. The contract
  binds **peer sessions** only. Without this exclusion stated, a reader applying the contract
  literally would break the orchestrators.

- **Residual risk, stated plainly.** `in-flight-check.md` already models this honesty and the
  same discipline applies here: **this contract binds only sessions that read it.** A session
  that never loaded minerva can still send an ad-hoc work request. That is precisely why the
  marker rides inside the message rather than living only in a file — the message is the only
  part of the protocol that reaches a peer who never read it.

### 2. `references/in-flight-check.md` step 4b

The query is unchanged, `MINERVA-BUSY` / `MINERVA-IDLE` included. Add the marker line to the
message template, and cite `cross-session.md` for the contract rather than restating it — the
same delegation shape the file already uses for the capability probe it borrows from
`minerva:promote`.

### 3. `using-minerva/SKILL.md`

One terse read-directive pointer to the new file, so a session orienting into minerva holds the
receive contract before any message arrives. The file has **178 bytes** of headroom against the
9216-byte cap in `tests/test_skill_budget.py`, and the pointer must fit inside it. This
knowingly consumes most of the headroom issue #107 is about; #107 is linked rather than adopted
because its fix is a prose move through unrelated sections of the same file.

### 4. Verification

No new bespoke test. The established mechanism is `evals/<skill>/contract.json` anchors, which
already pin load-bearing phrases in `in-flight-check.md`:

- `evals/propose/contract.json` — anchors for the marker line, the "adds to their workstream"
  boundary, the subagent exclusion, and the pointer `references/cross-session.md`.
- `evals/using-minerva/contract.json` — anchor for the qualified pointer.

`tests/test_skill_budget.py` covers the byte budget and both directions of pointer integrity
automatically, because it enumerates the skill directories.

## Success criteria

- `plugins/minerva/skills/propose/references/cross-session.md` exists, defines both the send and
  the receive contract, and is read-directed from `propose/SKILL.md`.
- The contract states the "adds to the peer's workstream" boundary, the two escalation forms
  (orchestrator and plain session), the relayed-instruction rule, the subagent exclusion, and
  the residual-risk statement.
- `in-flight-check.md` step 4b's template carries the information-not-instruction marker and
  cites `cross-session.md`; `MINERVA-BUSY` / `MINERVA-IDLE` are unchanged.
- `using-minerva/SKILL.md` carries a read-directive pointer to the new file and is ≤ 9216 bytes.
- Contract anchors fail if the marker line, the boundary statement, or the subagent exclusion is
  removed.
- `pytest tests/` is green.

## Open Questions

- Exact marker wording — settled during implementation against the `using-minerva` byte budget.
