# Proposal: pin-agent-dispatch-sync

**Date**: 2026-07-27
**Status**: Shipped (2026-07-27)

## Goal
Stop minerva orchestrator runs from parking mid-lifecycle at their subagent gates. Every place in minerva skill text that instructs spawning a subagent via the `Agent` tool must pin the execution mode — `run_in_background: false` — alongside the `subagent_type` / `model` pins it already carries, and a new enumerating test must fail any future dispatch site that omits it.

## Why
The `Agent` tool runs subagents in the **background by default**; a backgrounded dispatch returns only a handle (`"Async agent launched successfully… you will be notified automatically when it completes"`), not the agent's output. Every minerva protocol that dispatches an agent needs that output **in the same turn**: `round-table` counts votes and then dispatches an Arbiter "sequentially after both complete"; `propose-ship-balanced` arbitrates the reviewer's critique inline; `review`'s local-diff mode feeds its findings into the same turn's parallel presentation. When the dispatch is backgrounded, the next protocol step is unexecutable, the model has no legal action left, and it ends the turn announcing that it is waiting.

The dispatch instructions pin `subagent_type` and `model` but say nothing about execution mode, so the model guesses per dispatch. Measured across 105 real orchestrator runs (session transcripts under `~/.claude/projects/`, analyzed 2026-07-27):

| orchestrator | runs | runs with ≥1 "awaiting" turn-end | background dispatches | sync dispatches |
|---|---|---|---|---|
| `propose-ship-auto` | 30 | 28 | 404 | 342 |
| `propose-ship-balanced` | 34 | 31 | 76 | 124 |
| `propose-ship-quick` | 41 | 36 | 82 | 19 |

562 of 1047 dispatches (54%) were backgrounded — a near coin-flip, which is exactly why the symptom is intermittent. 95 of 105 runs parked at least once, with turn-ending messages like *"Waiting on the Skeptic before dispatching the Arbiter"* and *"Awaiting the Skeptic's re-vote."* Most parks self-recover when the completion notification fires, but each one reads to the user as the run having stopped, and at least one run sat idle until the user typed "go ahead" — there the model compounded the problem by using `ScheduleWakeup` to poll for its own backgrounded subagent, which the tool's own guidance calls out as wasted.

This is the same defect class as [[2026-05-19-constraint-skills-must-call-tools-not-prose]] and [[2026-07-21-constraint-handoffs-name-skill-tool]]: the skill text names a tool but omits the parameter that makes it behave the way the surrounding protocol assumes.

## Approach
Approach A, revised after both propose-phase reviewer gates returned `revise`. Pin the mode inline at each dispatch site — at the point of use, where the model reads it at gate time — and mechanize the rule with an enumerating test so a new dispatch site cannot reintroduce the gap.

Rejected alternatives:
- **B — inline pin, no test.** Smaller diff, but nothing prevents recurrence; [[2026-06-06-pattern-rejected-alternative-reinvented-at-runtime]] is precisely the observation that an unmechanized convention comes back.
- **C — one shared "dispatch discipline" reference file + pointers.** DRY, but `tests/test_skill_budget.py` enforces reference-pointer integrity **per skill** (every `references/*.md` is named from *its own* `SKILL.md`), so a shared file would need either per-skill duplication or a new cross-skill pointer convention. It also loses on point-of-use directness, which is the whole finding behind [[007]].

### 1. Pin the five dispatch sites
The propose-phase Skeptics found a fifth site my enumeration missed; all five are edited:

| # | Site | Note |
|---|---|---|
| 1 | `round-table/SKILL.md` — Dispatch section | The 3-agent panel; carries the full rationale (see below). |
| 2 | `propose-ship-balanced/SKILL.md` — binding-floor bullet | Restates `subagent_type`/`model` for the reviewer gate. **Terse pin only** — this file is 8960 bytes against the 9216 cap ([[036]]), 256 bytes of headroom. |
| 3 | `propose-ship-balanced/references/verify-protocol.md` — Single-reviewer mechanism | Authoritative statement + rationale (reference files are uncapped). |
| 4 | `propose-ship-balanced/references/phases.md` — dispatch-params line | Restates the params for every reviewer gate. |
| 5 | `review/references/protocol.md` — local-diff dispatch | Unlike 1–4 this site pins **no** params today, so the pin is added rather than appended to an existing list. |

Site 1 carries the reason, stated once where the panel mechanism lives: the panel is blocking by construction (votes are counted in the same turn and the Arbiter needs both outputs), and a backgrounded dispatch returns only a handle, stranding the run mid-panel. It also records that synchronous dispatches issued in a single message still run **concurrently** — so pinning the mode costs no wall-clock parallelism, which is what makes this cheap.

### 2. Mechanize it — `tests/test_skill_dispatch.py`
An enumerating test in the mould of `test_skill_contracts.py` / `test_skill_budget.py`. Both reviewers independently showed that the two obvious heuristics fail in opposite directions — matching `subagent` false-positives on frontmatter descriptions and prose framing; matching the literal `` `Agent` tool `` misses site 4, which names no tool. The detector is therefore **conjunctive**. A markdown block counts as a dispatch instruction iff it contains **both**:

- a dispatch verb (`spawn` / `dispatch` / `launch` / `invoke` / `create`, any case) — deliberately wider than the phrasings in the corpus today, since `launch` is the `Agent` tool's own canonical verb and a future author is at least as likely to reach for it, **and**
- a dispatch token — an `Agent`-tool reference **or** `subagent_type` **or** `model: sonnet` / `model: "sonnet"`. Matching is case-insensitive and tolerant of how the markdown falls (`` `Agent` tool ``, `` `Agent tool` ``, or unbackticked), because one site rests on this token alone and a cosmetic reformat there must not drop it out of detection.

Every matching line must also contain `run_in_background`. Detection is line-based: this corpus writes one paragraph or list item per line, so a line is the natural instruction unit and gives the tightest scope for the pin check.

Fenced regions are excluded first, built on `knowledge_spans`'s `FENCE_RE` rather than a re-derived grammar ([[023]], [[037]]). Fences are **paired**, not toggled: a fence closes only on the same character at the same-or-greater run length, so a `~~~` line inside a ``` block is content rather than a close. A bare toggle fails silently in the direction that matters — content wrongly treated as fenced is content the detector never inspects — so the same scan also reports a file that *ends* inside a fence, and a corpus-wide test rejects one.

Verified against the current corpus, this detector selects exactly the five sites above and excludes every near-miss: `round-table/SKILL.md`'s description and body framing (verb, no token), `review/SKILL.md`'s description (no verb, no token), `propose-ship-auto/SKILL.md:8` (delegates panel mechanics to round-table rather than dispatching), and the budget statements in both orchestrators' `governance.md` ("6 subagent dispatches max", "dispatches **one** subagent"). To keep the detector honest as the corpus grows, the test also **pins the detected-site set** — a new dispatch site is a deliberate update, not a silent pass.

Beyond the corpus checks, synthetic unit tests pin both halves of the conjunction independently (recall over seven dispatch phrasings; precision over verb-without-token, token-without-verb, and the `Skill`-tool handoff form that must never be caught) plus the fence-pairing and unclosed-fence semantics — so a future edit to either regex reds a test rather than silently narrowing the guarantee.

The module is appended to the CI enumerated pytest list, without which it is invisible to CI ([[2026-06-11-constraint-ci-test-enumeration-explicit]]).

### Deliberately out of scope
`ship/references/protocol.md`'s CI-watch cadence justifies `delaySeconds: 270` as *"stays under the 5-minute prompt-cache TTL"*, a rationale current tool guidance contradicts. Both reviewers flagged bundling it as an unrelated defect class, and under a 1-hour TTL the corrected sentence would be near-vacuous rather than merely stale. It goes to `followups.md` for its own change.

## Success criteria
1. All five sites in the table above pin `run_in_background: false`.
2. `round-table/SKILL.md`'s Dispatch section states why the panel is blocking by construction, and that single-message synchronous dispatches still run concurrently.
3. `tests/test_skill_dispatch.py` exists and implements the conjunctive, fence-aware detector described above, importing `FENCE_RE` from `knowledge_spans`.
4. That test pins the detected-site set to exactly the five sites, so both a missing pin and an unregistered new dispatch site fail CI.
5. The new module is appended to the CI enumerated pytest list.
6. Full `pytest` suite green, and every `SKILL.md` remains ≤ 9216 bytes — specifically `propose-ship-balanced/SKILL.md`, which has 256 bytes of headroom.

## Open questions
None blocking. The one judgment call already made: site 5 (`review/references/protocol.md`) gets only the `run_in_background` pin, not the `subagent_type`/`model` pins it also lacks — adding those is a separate authoring decision this unit does not make.
