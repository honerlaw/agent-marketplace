# Proposal: one-by-one-question-skill

**Date**: 2026-11-01
**Status**: Draft

## Goal
A new minerva skill, `minerva:one-by-one`, that takes the questions still outstanding in the current
session and asks them one at a time: it states how many there are, shows `Question k of N` on every
question, waits for the answer before the next, offers three to five concrete options on each, marks a
recommended option (or says explicitly that there is none), and always accepts the user's own direction
instead of any option.

## Why
Agents regularly end a turn with a list of questions. Answering ten at once in one reply is awkward:
answers get skipped, later questions depend on earlier ones, and a free-form reply is hard to map back.
The user asked for a skill that turns such a list into a sequential walk-through. No existing skill does
this: `minerva:grill-plan` *generates* probing questions about a drafted plan until understanding is
reached (open-ended, no total), and `minerva:explore` is a divergent conversation before any plan exists.
Neither takes a finite existing set, nor shows a position, nor guarantees options.

## Approach
One new skill file, standalone, wired into no orchestrator.

**Skill protocol (`plugins/minerva/skills/one-by-one/SKILL.md`, no references/ needed):**
1. **Collect.** Gather outstanding questions from the inline argument if any, questions the assistant
   asked this session that went unanswered, decisions blocking in-progress work, and the `## Open
   Questions` of a work unit the session is working on. The set is finite: the skill never invents new
   probing questions to extend it.
2. **Reduce.** Drop what is already answered; answer with a quick lookup what is discoverable
   (runtime contract: "Resolve discoverable facts first") and report those; merge duplicates. A question
   a quick lookup does not settle stays a question.
3. **Order.** Questions whose answers change other questions go first.
4. **Announce.** State the total N, a one-line topic list and the reply words (`skip`, `back`, `stop`, or
   add a question), then ask question 1 in the same turn (no confirmation gate). N = 0: say so, name what
   was checked, stop.
5. **Ask, one per turn.** Each question carries `Question k of N` *inside the question itself*, because
   a question dialog may be all the user sees. 3–5 concrete options. A recommendation is the first option,
   marked `(Recommended)`, with a one-line reason; otherwise the question states `No recommendation —
   <why>` and no option is marked. Question fewer than three natural answers gets completed with a real
   variant or a real disposition ("decide later"), never filler.
   Prefer three or four options; use a fifth only for a real fifth answer.
   Use the runtime contract's user question operation ("use the host's available interaction mechanism")
   when it can carry every option plus a free-form answer; when it cannot, or when unsure, ask directly in
   a message and wait. Never drop a real option to fit the tool. The automatic free-form slot does not count
   toward the 3–5, because the user asked for it separately from the options. On Claude Code `AskUserQuestion` holds 2–4 options plus
   an automatic "Other", so 3–4 options go through it and a 5-option question goes as a direct message.
   The skill text stays host-neutral (a test bans the tool's name outside the adapter); no adapter change
   is needed because the schema itself enforces the cap.
6. **Handle the reply.** A picked option or the user's own words are equally valid; own direction
   overrides a recommendation with no re-argument. Ambiguous reply: one clarification under the same
   number. `skip` moves on and records it. `back` re-asks an earlier one and re-checks dependents. `stop`
   ends with the recap. "Take your recommendations" applies only to questions that have one; `No
   recommendation` questions are still asked. A question back from the user is answered and the same
   question re-asked. A silent or dismissed question is not an answer and nothing is assumed.
   The user may add a question at any point. Anything that adds or obsoletes questions updates N visibly (`Question 4 of 11 (1 added)`); the total
   never changes silently.
7. **Recap, then hand back.** A table of number / question / answer / how answered (recommended, other
   option, own words, skipped). The skill itself then takes no further action: control returns to the
   caller or conversation, and the interrupted work continues under whatever authorization it already had.
   The answers grant nothing beyond what they say.

**Out of scope, stated in the skill:** writing files (the answers live in the conversation; a caller owns
persistence), generating new probing questions (grill-plan), weighing directions (explore), and being a
gate inside an autonomous orchestrator. No orchestrator calls this skill.

**Files changed:**
- `plugins/minerva/skills/one-by-one/SKILL.md` (new)
- `evals/one-by-one/contract.json` (new; required by the enumerating test), with clause-level anchors
- `scripts/run_compatibility_evals.py`: a non-mutating `one-by-one` scenario in `SCENARIOS` (the prompt carries
  a fixed list of four outstanding questions) and a pure acceptance function over the final text
- `tests/test_compatibility_evals.py`: model-free tests of that acceptance function, passing and failing cases
  (the runner's checks are inline today, so the function and its call are new code in `run()`; the scenario needs
  no fixture-set entry, because the default fixture and the `not mutating` checks already cover it)
- Four catalog surfaces: `plugins/minerva/README.md` table (after grill-plan), `plugins/minerva/skills/using-minerva/SKILL.md`
  decision matrix (after grill-plan), root `README.md` skills cell, `pages/index.md` catalog (utilities)
- Version `3.0.0` → `3.1.0` (new capability; matches the 2.0→2.1 precedent): both manifests, `COMPATIBILITY.md`,
  and test pins in `tests/test_host_adapters.py` (also skill count 19 → 20) and `tests/test_install_plugin.py`

## Success criteria
1. `plugins/minerva/skills/one-by-one/SKILL.md` exists; its description is ≤1024 chars, leads with function
   and ambient triggers, separates its trigger from `minerva:grill-plan` (a finite existing list of questions
   versus probing a drafted plan), and ends with the invocation clause; the file is under the 9 KB budget and
   names no host-specific tool (`tests/test_skill_budget.py`, `tests/test_host_adapters.py` pass).
2. The skill text carries each requirement as an imperative clause, each anchored in
   `evals/one-by-one/contract.json` on the sentence that does the work rather than a heading: collects from
   session context; one question per turn and waits; `Question k of N` inside every question; three to five
   options; never drops an option to fit the question tool, asking directly instead; a recommended option or
   `No recommendation`; the user's own answer always accepted; the total never changes silently. Each anchor is
   proven by a deletion pass: a throwaway script removes each anchored clause in turn, runs
   `python -B -m pytest tests/test_skill_contracts.py -k one-by-one`, requires a failure, restores the file, and
   the per-anchor result is recorded in the scratchpad.
3. All four catalog surfaces list `minerva:one-by-one` with text excerpted from the description
   (`tests/test_skill_contracts.py`, `tests/test_site_catalog.py` pass).
4. Both manifests and `COMPATIBILITY.md` read `3.1.0`, and the pinned tests agree.
5. The full test suite passes.
6. `scripts/run_compatibility_evals.py --host claude --scenario one-by-one` passes once as a manual, non-CI
   check: the final text shows `Question 1 of 4`, at least three options, `(Recommended)` or `No recommendation`,
   does not ask question 2, and the fixture is unchanged. The acceptance function's pass and fail cases are
   tested without model calls in CI. The Codex host is not run live (not checked here); its gap is reported.

## Open Questions
None. The skill name is `one-by-one`, the user's own phrasing and the likely slash command.
