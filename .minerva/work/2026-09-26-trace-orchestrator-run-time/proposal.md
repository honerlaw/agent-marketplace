# Proposal: trace-orchestrator-run-time

**Date**: 2026-09-26
**Status**: Draft

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
  One past auto session had 24 turns totalling 7,355 s of active time.
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
Add a new standalone dev tool, `scripts/run_trace.py`, next to `run_analyzer.py` in the repo-root
`scripts/`. It is not shipped in the minerva plugin. It uses only the standard library, is
read-only, and returns JSON-serializable data.

1. **Load.** Take a transcript path or a session id (resolved under `--project-dir`, default
   `~/.claude/projects/<encoded cwd>`). Read the main JSONL and every `subagents/*.jsonl` + `.meta.json`.
   Streamed assistant messages repeat, so dedupe by `uuid` and tool blocks by `id`, as `run_analyzer` does.
2. **Active vs. idle.** Active time is the sum of `turn_duration.durationMs`. For a turn with no
   `turn_duration` event, use that turn's first→last event. Each gap between turns is classified
   by what started the next turn:
   - `background-wait`: a `<task-notification>` or agent hand-back started it.
   - `scheduled-wait`: a ScheduleWakeup re-entry started it.
   - `user-idle`: a human prompt started it.
3. **Main-thread attribution.** Walk non-sidechain events in timestamp order and give each
   in-turn gap to exactly one category:
   - `tool:<Name>` while a tool call is open. When several are open, the one opened earliest
     gets it.
   - `user`: `AskUserQuestion` is attributed as user time, not tool time.
   - `model`: the gap ends at an assistant message and no tool is open.
   Bash is sub-bucketed by command head: the first token of the first command after stripping
   `cd … &&` prefixes and env assignments. For the multiplexers `gh`, `git`, `npm`, `uv`, the
   next non-flag token is added (`gh pr`, `git worktree`). For `python`/`python3 -m`, the module
   is added (`python3 -m pytest`). The report also lists the slowest individual calls. The
   earliest-open tie-break for parallel tool calls is a disclosed heuristic.
4. **Subagent spans.** Each subagent span runs from the subagent file's first to last
   timestamp. Its duration is cross-checked against the `<task-notification>` `duration_ms` for
   the same `toolUseId`; the notification's figure is used when present. Each span records its
   description, model, output tokens, tool-call count and its own tool/model breakdown (the
   same algorithm as step 3). Two aggregates are reported:
   - **Sum:** total subagent compute.
   - **Union of intervals:** wall-clock time with at least one subagent running.
5. **Gate/tier/role attribution.** Agent descriptions are parsed against a small closed
   vocabulary:
   - role: `Proponent|Skeptic|Arbiter|Verifier|fold-audit|code review`
   - gate: `scope|approach|whole-proposal|completion|divergence|triage|partition|todo|replan`
   - round: `r2` → revision round.
   - tier: subagents are first grouped by (gate, round). A group containing a Proponent or an
     Arbiter, or whose description says `panel`, is a **panel**, and every member takes that
     tier. A lone Skeptic, Verifier or fold-audit is **reviewer**. Real panel descriptions often
     omit the word "panel": session `51b73da3` has `Whole-proposal: Proponent` +
     `Whole-proposal: Skeptic`. So keyword matching alone is wrong, and a fixture pins exactly
     that shape.
   A description the vocabulary doesn't match is kept, tagged `unknown` and listed. It is never
   dropped (per `2026-08-11-pattern-a-tolerant-reader-needs-a-boundary`).
6. **Run segmentation, then phase attribution (inferred, auditable).** One session file can hold
   several orchestrator runs. For example, session `51b73da3` holds a
   `minerva:propose-ship-quick` run with its own ship/cleanup, and later a
   `minerva:propose-ship-auto` run. So the tool first splits each session into **runs**. A run
   starts at an orchestrator invocation (a `Skill` call or `<command-name>` prompt naming
   `minerva:propose-ship-auto`, or the retired `propose-ship-quick` / `propose-ship-balanced`,
   which are tagged by caller). It ends at the next orchestrator invocation or at the end of the
   file. A `--cleanup-only` re-entry attaches to the run it resumes, not a new run. Every
   boundary signal below is searched **only within its own run's window**. Phase boundaries
   within a run come from observable events in the main thread:
   - The run starts at the `Skill` call to `minerva:propose-ship-auto`, or the first
     `<command-name>/minerva:propose-ship-auto` prompt.
   - `propose` ends at the first `git worktree add`.
   - `work` runs until the first completion-Verifier/completion-panel Agent.
   - `verify` runs until the first review Agent (code review / spec audit).
   - `review` runs until the first Write/Edit under `.minerva/knowledge/`, which starts `promote`.
   - `ship` starts at the `Skill` call to `minerva:ship`, and `cleanup` at the `Skill` call to
     `minerva:cleanup`.
   Each boundary records the event (timestamp and short description) that set it, so the
   report is auditable. A boundary the tool can't find leaves its time in the preceding phase
   and adds a warning; it is never guessed. Phases stay in order: a signal that appears out of
   order is ignored and reported. A replan re-entering design work after `work` began is
   expected. It stays in the current phase, and a `minerva:replan` Skill call or a
   `replan.md` write is reported as a `replan` event, not an ordering warning.
7. **Report.**
   - Default output is a text report:
     - summary: wall, active, model, tools, user, subagent sum and union, background and
       scheduled waits;
     - a phase table;
     - a gate × tier × role table;
     - the 10 slowest spans.
   - The summary states which figures **partition** active time and which **overlap** with them:
     - model + tool + user partition in-turn active time;
     - background-wait / scheduled-wait / user-idle partition the time between turns;
     - subagent sum and union are overlapping views of subagent activity. Most of that activity
       falls inside background-wait or in-turn tool time, so they must not be added to the
       other figures.
   - `--json` emits the full structure.
   - `--all` aggregates every session in the project directory that invoked
     `minerva:propose-ship-auto`, with per-run rows plus totals and medians per phase and gate.
8. **Discoverability.** Add a "Time breakdown" step to `plugins/utils/skills/capture-session/SKILL.md`,
   the existing dev-facing skill that already runs `run_analyzer.py` by absolute repo path.
   The new step's body is a command block,
   `python3 /Users/derekhonerlaw/Development/agent-marketplace/scripts/run_trace.py <transcript.jsonl>`
   (plus `--all` for the cross-run view), mirroring Step 2's `run_analyzer.py` block, with a
   short guide to reading the report. Broaden its frontmatter description from token/cost usage to "token/cost usage and where the
   time went", so a question about time reaches it. This edits a `plugins/utils` skill file, a
   plugin surface. The skill-contract and site-catalog tests scope only
   `plugins/minerva/skills`, so it is not contract-tested.
9. **Absorbed fixes to `scripts/run_analyzer.py`.** The deferral bar applies
   (`2026-09-23-decision-a-defect-earns-a-tracker-slot-only-if-urgent-and-unabsorbable`): both
   defects are local and small, need no new design, and change interfaces only additively (one
   keyword argument defaulting to today's behavior and one CLI flag), so they are fixed here
   rather than filed.
   - (a) Add the current models to `PRICING`, with rates verified from the `claude-api`
     skill's pricing reference (`shared/models.md`, `shared/prompt-caching.md`) and not from
     memory. The transcripts in this repo use `claude-opus-5`, `claude-opus-5-5`,
     `claude-sonnet-5` and `claude-fable-5-1`. Today every current-model message is unpriced,
     so the analyzer reports $0.00. Newer models have their own cache-read rates:
     - Fable 5.1 and Mythos 5.1: $0.25/MTok (0.025x);
     - Opus 5.5: $0.20/MTok (0.05x);
     - every other model: the standard 0.1x.
     Add a per-model cache-read override. The 0.1x default stays, and the existing cost-math
     tests stay valid.
   - (b) `analyze_transcript(path, include_subagent_files=False)` gets an **opt-in** keyword.
     When `True`, it also folds `<session>/subagents/agent-*.jsonl` (resolved from the main
     transcript's stem) into `by_scope["subagent"]`, `by_model`, `by_tool` and `totals`.
     - **The default stays `False`, so every existing caller keeps its current
       subagent accounting.** The only change they see is that current-model messages are now
       priced instead of reported as $0. `run_benchmark.build_record` still calls it main-only. Its
       `cost_crosscheck_ok` still compares a main-only derived total with Claude's main-only
       `total_cost_usd`, and its manual `subagent_paths` / `--subagent` loop is still the only
       place a benchmark record picks up subagent cost. Nothing can be counted twice.
     - The standalone CLI (`run_analyzer.py <transcript>`, which `capture-session` runs) turns
       discovery **on** by default and takes `--main-only` to turn it off, so a person asking
       what a session cost sees the whole session.
     - Tests build the **real on-disk shape** (`tmp_path/<stem>.jsonl` +
       `tmp_path/<stem>/subagents/agent-x.jsonl`). They pin that:
       - the default call ignores the sibling file;
       - the opt-in call counts it once;
       - `build_record` with `--subagent` pointing at that same sibling file counts it
         exactly once and keeps `cost_crosscheck_ok` computed from main-only cost.
     - Assumption: a session's main file and its `subagents/` sidecar are non-overlapping
       records of subagent activity. Both real sessions checked have zero `isSidechain: true`
       lines despite populated `subagents/` dirs. As a guard for a hybrid or legacy transcript,
       the message-id dedupe set is shared across the main file and its sidecar files, so an
       overlapping message is billed once.
     - `build_record`'s docstring gains one sentence noting that it deliberately calls the
       analyzer main-only.
10. **Tests.** Add `tests/test_run_trace.py` with synthetic fixture transcripts written to
   `tmp_path`. It covers every attribution rule above. CI already runs the whole `tests/`
   suite (`2026-08-11-decision-ci-runs-the-whole-suite`). Each assertion gets a deletion pass
   (`2026-08-28-pattern-an-assertion-is-untested-until-a-deletion-makes-it-fail`).

### Candidate approaches considered
- **A (picked): new root `scripts/run_trace.py` dev tool.** It sits next to the cost analyzer
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
2. Active time equals the sum of `turn_duration.durationMs`. Inter-turn gaps are classified as
   background-wait / scheduled-wait / user-idle. Covered by fixture tests.
3. Main-thread in-turn time is split into model / `tool:<Name>` / user (`AskUserQuestion`). The
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
