# Proposal: trace-orchestrator-run-time

**Date**: 2026-09-26
**Status**: Shipped (2026-09-26)

## Goal
Add a deterministic, read-only tracer, `scripts/run_trace.py`. It rebuilds a time trace of a
Claude Code session from its on-disk transcripts: the main `<session>.jsonl` plus
`<session>/subagents/agent-*.jsonl`. It reports where a `minerva:propose-ship-auto` run spends
wall-clock time, broken down by lifecycle phase, by decision gate and tier, by tool, and by
subagent. It reports on a single run and aggregated across runs. In the same unit it also fixes two small defects in the sibling cost analyzer `scripts/run_analyzer.py`: a stale pricing table and subagent files it never reads. With that evidence, the
orchestrator's time cost can be optimized, including deciding whether a fast classifier such as
jev would save time on tier routing, before anyone builds it.

## Why
The user asked: "is there a way to measure where we spend most of our time when executing on a
workstream with propose-ship-auto? E.g. a similar thing could be tracing in services", and then
"lets go ahead and add tracing then so we can better optimize the tool and what it is spending
time on".

The two tools we have today can't answer that:
- `plugins/minerva/scripts/decision_telemetry.py` counts decision outcomes by tier × gate, with
  no time data.
- `scripts/run_analyzer.py` counts tokens and cost, with no time data. It also reads only the
  main transcript file.

### Facts gathered (2026-09-26, from this repo's own transcripts)
- Every transcript event has an ISO `timestamp`. `parentUuid`, `toolUseID` and
  `sourceToolUseID` link events causally.
- Tool calls pair up: an assistant `tool_use` block's `id` matches a later user `tool_result`
  block's `tool_use_id`.
- Each turn ends with a `system` event, `subtype: turn_duration`, which carries `durationMs`.
  One past auto session's 24 turns report 7,355 s in total. That is the `durationMs` sum, which
  overcounts: the session's real active time is 3,941 s (see replan.md, 2026-09-26).
- Subagents write separate files, `<session>/subagents/agent-<id>.jsonl`, next to
  `agent-<id>.meta.json` = `{agentType, description, toolUseId, model?}`. The main-file
  `isSidechain` flag no longer marks them. In one past session `run_analyzer` reports 0 subagent
  messages although 16 subagents ran.
- Subagents launched in the background return their `tool_result` within about 1 s, so pairing
  tool calls alone reports a 3-minute Skeptic as 1 s. When a subagent finishes, the main
  transcript gets a `queue-operation` enqueue whose content is a `<task-notification>` carrying
  `<tool-use-id>` and `<usage>…<duration_ms>N</duration_ms>` (ground-truth subagent duration)
  plus `subagent_tokens` and `tool_uses`.
- Prototype on session `51b73da3` (a propose-ship-auto run with 16 subagents):
  - Subagent wall-time sum: 2,069 s. Skeptics took about 200–250 s each, Proponents 40–100 s.
  - `AskUserQuestion`: 1,611 s. Bash (140 calls): 900 s.
- Panel Proponent and Skeptic run in parallel, so the sum of subagent time overcounts wall-clock
  time. The union of their intervals is the wall-clock contribution.

## Approach
*(Rewritten at promote to describe what shipped. The replan of 2026-09-26 and three review rounds
changed the turn model and phase signals. See replan.md and the archived scratchpad.)*

**`scripts/run_trace.py`** is a stdlib, read-only dev tool in the repo-root `scripts/`, next to
`run_analyzer.py`. It is not shipped in the minerva plugin.

1. **Load.** Input is a transcript path or a session id. `--project-dir` defaults to Claude Code's
   directory for the *primary checkout*: a linked worktree re-anchors through
   `git --git-common-dir`, while submodules and subdirectories keep their own directory. Loading
   reads the main JSONL plus `<session>/subagents/agent-*.jsonl` and `.meta.json`, dedupes events
   by `uuid` and reads naive timestamps as UTC.
2. **Turns.** A turn is the events between `turn_duration` markers. It starts at the event that
   began it (the first user event with an `origin`: human, task-notification, or peer hand-back,
   which is `isMeta`) and ends at the marker; a trailing unmarked turn is started the same way.
   Turns never overlap. Active time is the sum of turn spans, and `durationMs` is only a reported
   cross-check (it is not per-turn wall time; see replan.md).
3. **Attribution.** In-turn time is partitioned into:
   - `model`: no tool open;
   - `tool:<Name>`: a tool call is open (earliest-opened wins; includes permission waits);
   - `user`: an `AskUserQuestion` is open;
   - `harness`: a gap ending at a `system` event.
   Between-turn gaps are background-wait / scheduled-wait / user-idle / idle-other, by what started
   the next turn. Bash is bucketed by command head (multiplexer subcommand, `python -m <mod>`,
   `python (stdin)`).
4. **Subagents.** Each sidecar is linked to its Agent call by `toolUseId`, or failing that by the
   last `agentId:` in the Agent result. Its duration comes from the `<task-notification>`
   `duration_ms`, with the file span as fallback. Both sum and union are reported.
5. **Gate / role / round / tier.** These come from a closed description vocabulary. "fold-audit"
   is recognised only as the explicit word; "new-plan" maps to replan. Tier is panel for a
   Proponent or Arbiter, a description saying "panel", or a Skeptic dispatched in the same batch
   (same message or within 10 s) as a same-gate, same-round Proponent. Otherwise a Skeptic,
   Verifier or fold-audit is reviewer and a code review is code-review. Unknowns are reported,
   never dropped.
6. **Runs and phases.** A session splits into runs, one per orchestrator invocation (including
   retired callers). Two invocations within 120 s are one run, and a `--cleanup-only` re-entry
   extends the run it resumes. A run ends at the next invocation, at the first new human request
   after its cleanup began, or at the end of the file. Phase signals are searched only within the
   run and read from **shell structure**: heredoc bodies and quoted strings (including multi-line
   ones) are set aside first. The signals are:
   - `work`: `git worktree add … -b <branch>`, excluding the `minerva/` maintenance namespace;
   - `verify`: a completion Agent;
   - `review`: a code-review Agent;
   - `promote`: a write of a knowledge **entry** via Write/Edit, Bash redirect/tee/cp/mv (with
     `$VAR` expansion and `cd`) or a Python `write_text`/`open(…, "w")`, excluding index.md and
     overview.md; or `Skill minerva:promote`;
   - `ship` / `cleanup`: their Skill calls.
   A knowledge write before the last pre-ship verify/review is a mid-work capture event.
   Out-of-order or missing signals are warnings, and a replan is an event.
7. **Report.** The text report has a summary that states which figures partition and which
   overlap, a phase table (active vs waits, subagent sum and union, the event that set each
   boundary), a gate × tier × role × round table, Bash heads and the 10 slowest spans. `--json`
   emits the full structure. `--all [--any-orchestrator]` aggregates runs with per-phase *active*
   totals and medians (waits apart) and per-gate totals and medians; a transcript that can't be
   read is listed under `skipped`, not fatal.
8. **`capture-session` skill** (plugins/utils) has Step 2b for the time breakdown, and its
   description mentions time.
9. **`scripts/run_analyzer.py`** (absorbed fixes):
   - it prices the current models, with per-model cache-read rates;
   - `analyze_transcript(include_subagent_files=False)` is opt-in, and its message-id dedupe is
     shared across the main file and sidecars;
   - the CLI reports the whole session by default, with `--main-only` to restrict it;
   - `run_benchmark.build_record` stays main-only, so its cross-check and `--subagent` flow are
     unchanged.
10. **Tests.** `tests/test_run_trace.py` has 84 tests, and `tests/test_run_analyzer.py` has 24
    (13 new). A scripted deletion pass of 66 mutations, run with bytecode caching off, is 66/66
    killed. The full suite has 1115 passing.

### Candidate approaches considered
- **A (picked): new root `scripts/run_trace.py` dev tool.** It sits next to the cost analyzer.
  It has no minerva-plugin, contract-tested or host-compatibility impact. Its only plugin edit
  is the untested `plugins/utils` capture-session doc step. It re-implements the event-dedupe
  rule instead of importing it. `run_analyzer`'s dedupe is inline in a billing loop, not an
  importable primitive, and the tracer's dedupe (by event `uuid` across all event types) differs
  from the billing dedupe (by `message.id` on assistant turns only). Extracting a shared loader
  would refactor a module `run_benchmark` imports and tests pin, so that is left as a follow-up
  if a third transcript reader appears.
- **B: extend `run_analyzer.py` with a timing mode.** This puts two concerns (cost and time),
  two data models and two output contracts into one module that `run_benchmark.py` imports and
  pins with tests. It raises the blast radius for no reach gain.
- **C: ship it in the plugin (`plugins/minerva/scripts/run_trace.py`, symlinked into root
  `scripts/`) and wire it into a skill.** Transcripts are a Claude-Code-only format, while the
  plugin promises Claude Code and Codex parity (`plugins/minerva/COMPATIBILITY.md`), so a
  shipped skill surface would be host-coupled. It also adds skill-contract and catalog-sync
  surfaces. It can be promoted later once the tool proves out.

## Out of scope
- jev or any tier-routing change. This unit only produces the evidence for that decision.
- Explicit phase markers in `propose-ship-auto`. These are a follow-up if inference proves too fuzzy.
- OpenTelemetry export, Codex transcripts and live dashboards.
- Extracting a shared transcript loader for `run_analyzer` and `run_trace`. Revisit if a third
  transcript reader appears.
- Any change to shipped minerva plugin files.

## Success criteria
1. `python3 scripts/run_trace.py <session.jsonl>` prints a text report with a summary, a phase
   table, a gate × tier × role table and the 10 slowest spans. `--json` emits the same data as
   JSON. It runs on a real propose-ship-auto session in this repo without error.
2. Active time is the sum of per-turn spans (starting event → `turn_duration` marker). On every
   session in this project, turns never overlap and active ≤ wall, per session and per run.
   `durationMs` appears only as a cross-check (sums and the count of disagreeing turns).
   Inter-turn gaps are classified as background-wait / scheduled-wait / user-idle / idle-other.
   Covered by fixture tests, including a turn whose `durationMs` overshoots its span and one where
   it undershoots (an open `AskUserQuestion`). *(Replaced 2026-09-26; see replan.md.)*
3. Main-thread in-turn time is split into model / `tool:<Name>` / user (`AskUserQuestion`) / harness (hooks). The
   categories sum to active time within 1 s on the fixture. Bash is sub-bucketed by command head.
4. Subagent spans are read from `subagents/*.jsonl` + `.meta.json`, linked to their Agent call by
   `toolUseId`, and cross-checked against `<task-notification>` `duration_ms`. Both sum and
   union are reported. A fixture with two overlapping subagents shows union < sum.
5. Agent descriptions resolve to gate/tier/role/round through a closed vocabulary. Tier comes
   from (gate, round) grouping: a fixture of `X: Proponent` + `X: Skeptic` with no "panel" word
   resolves to panel, and a lone Skeptic resolves to reviewer. An unmatched description is
   reported as `unknown` with its text, and is never dropped. Covered by tests.
6. Each session is split into runs, one per orchestrator invocation, each bounded by the next
   invocation or the end of the file. Phases are inferred from the listed observable signals,
   searched only within their own run. Each boundary names the event that set it. A missing
   signal produces a warning, not a guess. Tests cover this, including a fixture with two
   orchestrator runs in one session whose ship/cleanup signals must not cross over.
7. `--all` aggregates the propose-ship-auto sessions in a project directory, with per-run rows
   and per-phase / per-gate totals and medians.
8. `tests/test_run_trace.py` passes. Every assertion was shown to fail under a deletion pass
   (logged in the scratchpad). The full `pytest tests/` suite stays green.
9. `capture-session/SKILL.md` documents the time-breakdown command, and its description mentions time.
10. `run_analyzer.py` prices the current Claude models, with rates cited to the `claude-api`
    pricing reference, including the per-model cache-read rates (Fable 5.1 and Mythos 5.1 at
    0.025x, Opus 5.5 at 0.05x, all others 0.1x). With `include_subagent_files=True`, and by
    default on the CLI, it counts `<session>/subagents/*.jsonl` under `by_scope["subagent"]`. On
    session `51b73da3` the CLI reports a non-zero cost and a non-zero subagent message count.
    The library default is unchanged (main-only). A test on the real `<stem>/subagents/` layout
    shows that `build_record` with `--subagent` counts each subagent file exactly once and that
    `cost_crosscheck_ok` still uses main-only cost. `tests/test_run_analyzer.py` stays green.

## Open Questions
- None blocking. Whether inferred phases are precise enough is answered by running the tool on
  the existing sessions (criterion 1). If they're too fuzzy, explicit markers become a follow-up.
