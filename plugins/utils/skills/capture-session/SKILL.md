---
name: capture-session
description: Use when the user wants to analyze or record token/cost usage from a Claude Code session they just ran — or see where the time went (which phase, decision gate, tool or subagent a propose-ship-auto run spent its wall-clock on) — in any repo. Finds the most recent transcript, runs the cost analyzer and the time tracer, and optionally records to the benchmark baseline.
---

# Capture Session

Analyze and optionally record context usage — and trace where the wall-clock time went — for any completed Claude Code run.

## Step 1 — Find the transcript

List the 10 most recently modified session transcripts across all projects:

```bash
ls -t ~/.claude/projects/*/*.jsonl 2>/dev/null | head -10
```

If the user mentions a specific repo, scope it. Encode the path by replacing `/` with `-`:
```bash
# e.g. /Users/foo/Development/my-repo → -Users-foo-Development-my-repo
ls -t ~/.claude/projects/-Users-derekhonerlaw-Development-<repo-name>/*.jsonl | head -5
```

Pick the most recently modified file. Confirm with the user if it's unclear which run they mean.

## Step 2 — Analyze it

```bash
python3 /Users/derekhonerlaw/Development/agent-marketplace/scripts/run_analyzer.py <transcript.jsonl>
```

This reports the whole session: the main transcript plus its subagent sidecar files
(`<session>/subagents/agent-*.jsonl`). Add `--main-only` to exclude the subagents.

Show the user the full JSON output. Call out:
- `total_cost_usd` — derived cost
- `totals` — breakdown of all five token classes (input, output, cache-write-5m, cache-write-1h, cache-read)
- `by_model` — per-model cost split
- `by_scope.subagent.messages` — how many subagent turns fired
- `by_tool` — tool call counts

## Step 2b — Time breakdown (where the time went)

```bash
python3 /Users/derekhonerlaw/Development/agent-marketplace/scripts/run_trace.py <transcript.jsonl>
```

It accepts a transcript path or a bare session id (resolved under
`~/.claude/projects/<encoded cwd>/`, or pass `--project-dir`). Add `--json` for the
full structure. For the cross-run view of every `minerva:propose-ship-auto` run in a
project, with per-phase and per-gate totals and medians, use:

```bash
python3 /Users/derekhonerlaw/Development/agent-marketplace/scripts/run_trace.py --all --project-dir ~/.claude/projects/<encoded-cwd>
```

How to read it:
- **wall = active + between-turn waits.** Active time splits into `model`
  (generating), `tools` (a tool call open, including permission prompts), `user` (an
  `AskUserQuestion` open) and `harness` (hooks). Waits split into `background` (the
  model idled until a subagent or background task reported back), `scheduled`, and
  `user idle`.
- **Subagents are an overlapping view.** `sum` is total subagent compute, and
  `union` is wall-clock with at least one running. Most of it already sits inside
  background waits, so never add it to the other figures.
- **Phases are inferred** from observable events: `git worktree add`, the completion
  Verifier, the code-review agent, knowledge writes, and the `minerva:ship` and
  `minerva:cleanup` calls. Each boundary names the event that set it, and `!` lines
  flag missing or out-of-order signals.
- The **gate table** groups subagents by gate, tier (panel / reviewer / code-review) and
  role, so you can see which adjudication tier the time went to.

## Step 3 — Record to baseline (optional)

Ask the user if they want to record this run to `benchmarks/baseline.jsonl` for comparison.
If yes, ask for a short `task-id` label (e.g. `psa-add-feature`, `debug-run-1`).

**Interactive session (most common):** No result.json exists. Write a stub and record:
```bash
echo '{"session_id": "unknown", "total_cost_usd": null, "num_turns": null}' > /tmp/_session_stub.json
python3 /Users/derekhonerlaw/Development/agent-marketplace/scripts/run_benchmark.py record \
  --result /tmp/_session_stub.json \
  --transcript <transcript.jsonl> \
  --task-id <label>
```
`cost_crosscheck_ok` will be `false` (no `claude -p` result to cross-check against) but token counts are exact.

**Headless session (`claude -p --output-format json`):** The user has a `result.json`. Pass it directly:
```bash
python3 /Users/derekhonerlaw/Development/agent-marketplace/scripts/run_benchmark.py record \
  --result <result.json> \
  --transcript <transcript.jsonl> \
  --task-id <label>
```

## Compare two recorded runs

```bash
python3 /Users/derekhonerlaw/Development/agent-marketplace/scripts/run_benchmark.py diff \
  --task-id <label>
```

Prints the delta (cost, tokens, turns, subagents) between the two most recent records for that task id.
