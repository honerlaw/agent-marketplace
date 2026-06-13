---
name: capture-session
description: Use when the user wants to analyze or record token/cost usage from a Claude Code session they just ran, in any repo. Finds the most recent transcript, runs the cost analyzer, and optionally records to the benchmark baseline.
---

# Capture Session

Analyze and optionally record context usage from any completed Claude Code run.

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

Show the user the full JSON output. Call out:
- `total_cost_usd` — derived cost
- `totals` — breakdown of all five token classes (input, output, cache-write-5m, cache-write-1h, cache-read)
- `by_model` — per-model cost split
- `num_subagent_messages` — how many subagent turns fired
- `by_tool` — tool call counts

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
