#!/usr/bin/env python3
"""Deterministic, read-only **cost + context-usage** report for a Claude Code run.

Parses a Claude Code session transcript (the per-session JSONL under
``~/.claude/projects/<encoded-cwd>/<session>.jsonl``) and reports the run's
**exact** token usage and the **derived** USD cost, broken down by main-loop vs
subagent (sidechain) and by model. This is the measurement artifact unit 035's
followup #2 asked for: it answers "how much context and money did this run
actually cost?", which the per-file `tests/test_skill_budget.py` floor cannot
see (that caps each `SKILL.md`; a run's cost is dominated by dynamic
tool-result accumulation, multi-turn re-billing, and subagent panels — none of
which live in the skill files).

Token counts are **exact** — read straight from each assistant message's
``message.usage`` record. There is no tokenizer and deliberately so: the
`claude-api` reference is explicit that `tiktoken` must never be used for Claude
(it undercounts). The transcript's own counts are ground truth; the only
Claude-specific constant here is the pricing table.

Cost is `usage x PRICING`, with prompt-cache multipliers on the input rate
(write-5m 1.25x, write-1h 2x, read 0.1x). The harness cross-checks the derived
total against Claude Code's own ``total_cost_usd`` from ``claude -p
--output-format json`` (see ``run_benchmark.py``), so a pricing-table drift or a
parsing bug fails loudly rather than silently.

Read-only; never writes. Returns plain JSON-serializable primitives.
"""
import json
import re
import sys
from pathlib import Path

# Per-1M-token rates (USD): (input, output). Source: the `claude-api` skill's
# `shared/models.md` model table (cached 2026-06-24, re-read 2026-09-26) —
# pricing drifts, so re-verify on update. The `total_cost_usd` cross-check in
# run_benchmark.py catches a stale table loudly.
PRICING = {
    "claude-fable-5-1": (10.0, 50.0),
    "claude-mythos-5-1": (10.0, 50.0),
    "claude-fable-5": (10.0, 50.0),
    "claude-mythos-5": (10.0, 50.0),
    "claude-opus-5-5": (4.0, 20.0),
    "claude-opus-5": (5.0, 25.0),
    "claude-opus-4-8": (5.0, 25.0),
    "claude-opus-4-7": (5.0, 25.0),
    "claude-opus-4-6": (5.0, 25.0),
    "claude-sonnet-5": (2.0, 10.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-haiku-4-5": (1.0, 5.0),
}

# Prompt-cache multipliers applied to the INPUT rate (shared/prompt-caching.md):
# a 5-minute cache write bills 1.25x, a 1-hour write 2x, a read 0.1x.
CACHE_WRITE_5M_MULT = 1.25
CACHE_WRITE_1H_MULT = 2.0
CACHE_READ_MULT = 0.1

# Models whose cache READ is not the standard 0.1x (shared/prompt-caching.md
# "Economics"; shared/models.md): Fable 5.1 / Mythos 5.1 read at $0.25/MTok
# (0.025x), Opus 5.5 at $0.20/MTok (0.05x). Every other model uses CACHE_READ_MULT.
CACHE_READ_MULT_BY_MODEL = {
    "claude-fable-5-1": 0.025,
    "claude-mythos-5-1": 0.025,
    "claude-opus-5-5": 0.05,
}

# A model id may carry a context-tier suffix (e.g. ``claude-opus-4-8[1m]``);
# the 1M tier is standard-priced, so strip the suffix before pricing.
_SUFFIX_RE = re.compile(r"\[[^\]]*\]$")


def normalize_model(model: str) -> str:
    """Strip a trailing context-tier suffix so the id matches the PRICING keys."""
    return _SUFFIX_RE.sub("", model or "").strip()


def _zero_usage() -> dict:
    return {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_write_5m_tokens": 0,
        "cache_write_1h_tokens": 0,
        "cache_read_tokens": 0,
    }


def _add_usage(acc: dict, raw: dict) -> None:
    """Fold one ``message.usage`` record into ``acc`` (the five billed classes).

    Uses the ``cache_creation`` 5m/1h split when present. When only the
    aggregate ``cache_creation_input_tokens`` is available (older transcripts),
    it is attributed to the 5-minute tier (the default TTL) — flagged via the
    return so the caller can note the assumption.
    """
    acc["input_tokens"] += raw.get("input_tokens", 0) or 0
    acc["output_tokens"] += raw.get("output_tokens", 0) or 0
    acc["cache_read_tokens"] += raw.get("cache_read_input_tokens", 0) or 0
    split = raw.get("cache_creation") or {}
    if split:
        acc["cache_write_5m_tokens"] += split.get("ephemeral_5m_input_tokens", 0) or 0
        acc["cache_write_1h_tokens"] += split.get("ephemeral_1h_input_tokens", 0) or 0
    else:
        # No split — attribute the aggregate to the 5m (default-TTL) tier.
        acc["cache_write_5m_tokens"] += raw.get("cache_creation_input_tokens", 0) or 0


def usage_cost(usage: dict, model: str) -> "float | None":
    """USD cost of one aggregated usage dict at ``model`` rates, or None if unpriced."""
    rates = PRICING.get(normalize_model(model))
    if rates is None:
        return None
    in_rate, out_rate = (r / 1_000_000 for r in rates)
    read_mult = CACHE_READ_MULT_BY_MODEL.get(normalize_model(model), CACHE_READ_MULT)
    return (
        usage["input_tokens"] * in_rate
        + usage["output_tokens"] * out_rate
        + usage["cache_write_5m_tokens"] * in_rate * CACHE_WRITE_5M_MULT
        + usage["cache_write_1h_tokens"] * in_rate * CACHE_WRITE_1H_MULT
        + usage["cache_read_tokens"] * in_rate * read_mult
    )


def subagent_files(path) -> list:
    """The sidecar transcripts Claude Code writes for Agent-spawned subagents.

    A session ``<dir>/<session>.jsonl`` keeps each subagent's turns in
    ``<dir>/<session>/subagents/agent-<id>.jsonl`` — they are NOT marked
    ``isSidechain`` in the main file. Sorted for determinism; empty when the
    directory is absent.
    """
    p = Path(path)
    return sorted((p.parent / p.stem / "subagents").glob("agent-*.jsonl"))


def _assistant_lines(sources):
    """Yield ``(assistant_obj, is_sidecar)`` for each parseable assistant line."""
    for src, is_sidecar in sources:
        for line in Path(src).read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("type") == "assistant":
                yield obj, is_sidecar


def analyze_transcript(path, include_subagent_files: bool = False) -> dict:
    """Return the deterministic cost + usage report for one transcript JSONL.

    ``include_subagent_files`` (opt-in) also folds the session's sidecar
    subagent transcripts (see ``subagent_files``) into the ``subagent`` scope.
    It defaults to False so existing callers keep their accounting:
    ``run_benchmark.build_record`` cross-checks a main-only total against
    Claude's main-only ``total_cost_usd`` and adds subagent files itself via
    ``subagent_paths`` — folding them here too would count them twice. The
    message-id dedupe is shared across the main file and its sidecars, so a
    message present in both is billed once.

    Keys (all JSON-serializable):
      total_cost_usd        float — derived cost across all priced messages
      unpriced_models       sorted list[str] — model ids with no PRICING entry
                            (their token usage is still counted, cost excluded)
      assistant_messages    int — number of billed assistant turns
      by_scope              {"main": {...}, "subagent": {...}} — per-scope
                            usage (the five classes) + cost + message count
      by_model              {model_id: {usage..., cost, messages}}
      by_tool               {tool_name: call_count} — what the run did (tool
                            calls are not separately priced; their token cost
                            lands in the following turn's input/cache)
      totals                aggregated usage (the five classes) across the run
    """
    by_scope = {
        "main": {"usage": _zero_usage(), "cost_usd": 0.0, "messages": 0},
        "subagent": {"usage": _zero_usage(), "cost_usd": 0.0, "messages": 0},
    }
    by_model: dict = {}
    by_tool: dict = {}
    totals = _zero_usage()
    unpriced = set()
    n_assistant = 0

    # Claude Code writes each assistant message to the transcript MULTIPLE times as
    # it streams (one line per content-block update), every copy carrying the
    # SAME message.id and the SAME final `usage`. Summing per line double-counts
    # usage 2-5x, so each unique message.id is billed exactly once, and tool_use
    # blocks are deduped by their own block id. (Verified against a real run: the
    # naive per-line sum overshot Claude's total_cost_usd ~2.5x.)
    seen_msg_ids: set = set()
    seen_tool_block_ids: set = set()
    fallback_idx = 0

    sources = [(Path(path), False)]
    if include_subagent_files:
        sources += [(sp, True) for sp in subagent_files(path)]

    for obj, is_sidecar in _assistant_lines(sources):
        msg = obj.get("message") or {}
        model = msg.get("model") or "unknown"
        scope = "subagent" if (is_sidecar or obj.get("isSidechain")) else "main"

        mid = msg.get("id")
        if mid is None:
            mid = f"__noid_{fallback_idx}"  # treat an id-less message as unique
            fallback_idx += 1

        # Bill each unique message's usage exactly once.
        if mid not in seen_msg_ids:
            seen_msg_ids.add(mid)
            n_assistant += 1
            u = _zero_usage()
            _add_usage(u, msg.get("usage") or {})
            for k, v in u.items():
                totals[k] += v
                by_scope[scope]["usage"][k] += v

            cost = usage_cost(u, model)
            if cost is None:
                unpriced.add(normalize_model(model))
                cost = 0.0
            by_scope[scope]["cost_usd"] += cost
            by_scope[scope]["messages"] += 1

            m = by_model.setdefault(
                normalize_model(model),
                {"usage": _zero_usage(), "cost_usd": 0.0, "messages": 0},
            )
            for k, v in u.items():
                m["usage"][k] += v
            m["cost_usd"] += cost
            m["messages"] += 1

        # Tool calls can arrive across the message's repeated lines; dedupe by
        # block id so a streamed tool_use is counted once.
        for block in msg.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                bid = block.get("id") or f"__tb_{fallback_idx}"
                if bid in seen_tool_block_ids:
                    continue
                seen_tool_block_ids.add(bid)
                name = block.get("name", "?")
                by_tool[name] = by_tool.get(name, 0) + 1

    total_cost = round(
        by_scope["main"]["cost_usd"] + by_scope["subagent"]["cost_usd"], 6
    )
    for scope in by_scope.values():
        scope["cost_usd"] = round(scope["cost_usd"], 6)
    for m in by_model.values():
        m["cost_usd"] = round(m["cost_usd"], 6)

    return {
        "total_cost_usd": total_cost,
        "unpriced_models": sorted(unpriced),
        "assistant_messages": n_assistant,
        "by_scope": by_scope,
        "by_model": by_model,
        "by_tool": dict(sorted(by_tool.items(), key=lambda kv: -kv[1])),
        "totals": totals,
    }


def main(argv=None) -> int:
    """CLI: report the WHOLE session by default (main transcript + its subagent
    sidecar files); ``--main-only`` restricts it to the main transcript."""
    argv = list(argv if argv is not None else sys.argv[1:])
    main_only = "--main-only" in argv
    paths = [a for a in argv if a != "--main-only"]
    if len(paths) != 1:
        print("usage: run_analyzer.py <transcript.jsonl> [--main-only]", file=sys.stderr)
        return 2
    print(json.dumps(analyze_transcript(paths[0], include_subagent_files=not main_only), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
