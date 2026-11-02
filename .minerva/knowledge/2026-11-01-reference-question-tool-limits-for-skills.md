# Question-tool limits that shape a skill's user questions

**Date**: 2026-11-01
**Type**: reference
**Theme**: skills-and-catalogs
**Summary**: AskUserQuestion holds 2–4 options plus Other; `claude -p` exposes no question tool; evals read only final text
**Context**: .minerva/work/2026-11-01-one-by-one-question-skill

## Context
`minerva:one-by-one` promises three to five options on every question, and skill bodies may not name the
question tool (`tests/test_host_adapters.py`).

## Finding
- Claude Code's `AskUserQuestion` takes 2–4 options per question and adds a free-form "Other" itself, so a
  five-option question cannot go through it. Its header chip is 12 characters.
- `claude -p` exposes no question tool, as observed in two live runs on 2.1.316. A model in a compatibility eval
  asks in its final message, so those evals exercise only the direct-message path.
- `transcript_output` in `scripts/run_compatibility_evals.py` reads final text only. A question asked through
  a dialog would be invisible to any final-text acceptance check.
- Codex's question-tool limits were not measured.

## Implications
State a tool-capacity rule in host-neutral words ("when it can carry every option plus a free-form answer"),
and let the tool's own schema enforce the cap. A passing compatibility eval is no evidence for a skill's
dialog path.

## Related
- [[2026-05-19-constraint-skills-must-call-tools-not-prose]] — see also
