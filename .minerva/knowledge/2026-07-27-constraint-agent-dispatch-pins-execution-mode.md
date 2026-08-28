# Skill text that dispatches a subagent must pin the execution mode

**Date**: 2026-07-27
**Type**: constraint
**Context**: .minerva/work/2026-07-27-pin-agent-dispatch-sync

## Context
The `Agent` tool runs subagents in the **background by default**: the call returns a handle ("Async agent launched successfully… you will be notified automatically when it completes"), not the agent's output. Every minerva protocol that dispatches an agent needs that output *in the same turn* — `round-table` counts votes and then dispatches an Arbiter that needs both prior outputs, `propose-ship-balanced` arbitrates its reviewer's critique inline, `review`'s local-diff mode presents findings in the same turn.

The dispatch instructions pinned `subagent_type` and `model` but said nothing about execution mode, so the model chose per dispatch. Across 105 real orchestrator runs, 562 of 1047 dispatches (54%) were backgrounded and 95 of the 105 runs ended at least one turn mid-lifecycle with an "awaiting the Skeptic" message — the next protocol step was unexecutable, so there was no legal action left but to stop. Most parks self-recovered when the completion notification fired; the user-visible symptom was an orchestrator that "sometimes stops and says it's waiting."

## Finding
Any skill text that **instructs** a subagent dispatch must pin `run_in_background: false` alongside `subagent_type` / `model`. Omitting it is not a neutral default — it silently converts a blocking protocol step into a turn boundary. The pin costs no parallelism: multiple synchronous `Agent` invocations issued in a single message still run concurrently, so the only thing it changes is whether the caller can act on the results.

`tests/test_skill_dispatch.py` enforces this by enumeration. A line counts as a dispatch instruction iff it carries **both** a dispatch verb (`spawn` / `dispatch` / `launch` / `invoke` / `create`) **and** a dispatch-parameter token (an `Agent`-tool reference, `subagent_type`, or `model: sonnet`). The conjunction is load-bearing in both directions: matching the token alone false-positives on frontmatter descriptions ("Dispatches a 3-agent … panel of fresh-context subagents" instructs nothing), and matching the tool phrase alone misses a site that restates the parameters without naming the tool. The test also pins the registered site set, so a *new* dispatch site is a deliberate registration rather than a silent pass.

## Implications
- **Adding a dispatch site**: pin `run_in_background: false` in the instruction and add the file to `REGISTERED_SITES` in `tests/test_skill_dispatch.py`; CI fails otherwise.
- **Rephrasing an existing one**: the detector is tolerant of markdown form and verb choice, but a phrasing outside the verb list is invisible to it — widen the list rather than working around it.
- This is the same defect shape as [[2026-05-19-constraint-skills-must-call-tools-not-prose]] and [[2026-07-21-constraint-handoffs-name-skill-tool]] one level down: the text names the right tool but omits the parameter that makes it behave the way the surrounding protocol assumes. The general rule those three share: **a skill instruction must pin every argument the protocol's next step depends on** — naming the tool is not enough when a default silently changes the control flow.
- Per [[2026-06-06-pattern-rejected-alternative-reinvented-at-runtime]], the convention is mechanized rather than only recorded here; a knowledge entry alone would not have stopped the recurrence.

## Related
- [[2026-05-19-constraint-skills-must-call-tools-not-prose]] — builds on
- [[2026-07-21-constraint-handoffs-name-skill-tool]] — builds on
- [[2026-06-06-pattern-rejected-alternative-reinvented-at-runtime]] — see also
- [[2026-06-11-constraint-fence-scans-import-fence-re]] — see also
- [[2026-06-29-decision-propose-ship-balanced-single-reviewer]] — see also
- [[2026-07-29-pattern-wait-shape-matches-what-is-awaited]] — see also
- [[2026-08-28-constraint-reviewer-gates-assume-a-synchronous-dispatch]] — see also
