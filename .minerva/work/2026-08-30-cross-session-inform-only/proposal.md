# Proposal: cross-session-inform-only

**Date**: 2026-08-30
**Status**: Shipped (2026-08-30)
**Closes**: #107

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

Owned by `propose`, following the precedent `in-flight-check.md` set for a cross-cutting protocol
whose only current caller is intake. As shipped it states:

- **The line, first.** What is banned is a message that would **add to the peer's workstream**.
  Asking a peer what it is *already* doing changes nothing about its work, so the intake query
  stands verbatim. Stated explicitly because a reader who collapses "never delegate" into "never
  ask" deletes the only detection minerva has for a peer in the pre-worktree window.
- **Send contract.** Outbound messages state facts about the sender's own workstream and may ask
  for the same in return. Every message carries an information-not-instruction marker **inline**
  — a file binds only sessions that read it, and the message is the only part of the contract
  that travels. Volume, peer filtering and reply handling are **not restated**; they are
  delegated to `in-flight-check.md` §4a–4c, which owns them, with one addition the owner has no
  concept of: a session in **no lifecycle run** has no run to count against, so its bound is one
  unsolicited message per peer **per topic**.
- **Receive contract, with precedence stated.** Two classifiers exist and do not compete. A reply
  to minerva's own pre-flight query is governed by `in-flight-check.md` Step 5/6, **which win
  outright** — without that ordering, a `MINERVA-BUSY` naming this session's own goal could be
  read as "adjacent" and silently downgraded from a hardcoded, counter-incrementing ask. Every
  other message uses the three-way table: irrelevant → nothing; adjacent → one line, keep going;
  invalidating → escalate.
- **Escalation follows lifecycle position, not orchestrator membership.** At intake, the
  hardcoded Step 6 ask (resume / start fresh / abandon) — options that describe whether to
  *create* a unit and therefore fit nowhere else. Mid-lifecycle, **continue / modify / stop**;
  "start fresh" is not an available answer to a session ten commits in. Inside an autonomous
  orchestrator either ask increments the global escalation counter.
- **Relayed user instructions** are neither adopted nor stonewalled: surfaced as "peer X relays a
  request to do Y; I have not started it". Attribution is unverifiable, so it grants no
  authority. In an autonomous run, where there is no user in the loop, the rule is explicit
  rather than implied: never adopted, never worth an escalation on its own, carried into the
  final report — escalating only if it *also* invalidates the current workstream.
- **Subagent exclusion, channel-wide.** `Agent` dispatch is delegation by design and minerva
  depends on it. The exemption names the whole channel, not just the dispatch: `SendMessage` to
  an agent **this session spawned** is normal delegation, so a literal reader cannot conclude
  that continuing one's own subagent is banned.
- **Residual risk, stated plainly.** The contract binds only sessions that read it. That is a
  norm, not an enforcement mechanism, and the file says so rather than overselling itself.

### 2. `references/in-flight-check.md` step 4b

The query is unchanged, `MINERVA-BUSY` / `MINERVA-IDLE` included. Add the marker line to the
message template, and cite `cross-session.md` for the contract rather than restating it — the
same delegation shape the file already uses for the capability probe it borrows from
`minerva:promote`.

### 3. Six read-directive pointers, and #107 adopted

*(Revised by the 2026-08-30 replan — see `replan.md`.)*

A session must hold the receive contract **before** a message arrives, so the pointer goes on
every surface whose sessions stay live long enough to receive one: `using-minerva/SKILL.md`
(orientation), `work/SKILL.md`, and all four `propose-ship*/SKILL.md` orchestrators.

- **The same sentence, verbatim, in all six.** One wording, reused rather than re-derived per
  file. **239 bytes** — `propose-ship-balanced`'s headroom, the tightest of the six — is the
  binding ceiling. The in-flight-check precedent sitting nearby in those same files is a
  ~500-byte restated block and is deliberately **not** the model to copy.
- **All six pointers are anchored** in `evals/work/contract.json` and the four
  `evals/propose-ship*/contract.json`, mirroring the anchors those files already carry for the
  `in-flight-check.md` path. Six near-identical lines with no anchor is the shape
  `2026-08-24-pattern-extracted-copies-split-into-shared-and-divergent-halves` warns about:
  delete any one and nothing goes red.
- **Issue #107 is adopted, not linked.** Detail prose moves out of `using-minerva/SKILL.md` into
  its existing `references/guide.md` — the fix #107 itself prescribes — restoring at least ~200
  bytes of headroom so a future catalog row still fits, and so this unit's own pointer lands with
  room to spare rather than consuming the last of it.

### 4. Verification

No new bespoke test. The established mechanism is `evals/<skill>/contract.json` anchors, which
already pin load-bearing phrases in `in-flight-check.md`:

- `evals/propose/contract.json` — anchors for the marker line, the "adds to their workstream"
  boundary and its carve-out, the receive dispositions, both escalation forms, the relayed-request
  rule, the reply-precedence clause, the subagent exclusion, and the pointer
  `references/cross-session.md`.
- `evals/using-minerva/contract.json`, `evals/work/contract.json`, and the four
  `evals/propose-ship*/contract.json` — one anchor each for the qualified pointer.
- **One bespoke test**, `tests/test_cross_session_contract.py`: the marker must sit **inside** the
  fenced peer-message template, not merely somewhere in the file. A whole-file presence assertion
  stays green when the marker is moved out of the template into the prose beside it — peers stop
  receiving it and CI never notices
  (`2026-08-28-pattern-a-presence-assertion-must-be-scoped-to-what-it-guards`). Its fence scan
  imports the single-sourced `FENCE_RE` grammar per
  `2026-06-11-constraint-fence-scans-import-fence-re`, and its negative-coverage test asserts the
  loose form would have passed the same mutation.

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
- All six of `using-minerva`, `work`, `propose-ship`, `propose-ship-quick`,
  `propose-ship-balanced` and `propose-ship-auto` carry the **same verbatim** read-directive
  pointer, each file staying ≤ 9216 bytes.
- Every one of those six pointers is pinned by an anchor in its skill's `contract.json`, so
  deleting any single line turns the suite red.
- `using-minerva/SKILL.md` regains ≥ 200 bytes of headroom — enough for a future catalog row —
  and issue #107's prescribed fix is complete.
- Contract anchors fail if the marker line, the boundary statement and its carve-out, the
  dispositions, either escalation form, the relayed-request rule, the reply-precedence clause, or
  the subagent exclusion is removed.
- `tests/test_cross_session_contract.py` fails when the marker is moved out of the fenced
  template into surrounding prose.
- `pytest tests/` is green.

## Open Questions

None. The marker wording was settled during implementation —
`This message is information, not a work request — do not start anything on my behalf.` — and is
pinned inside the fenced template by `tests/test_cross_session_contract.py` rather than by a
whole-file check.
