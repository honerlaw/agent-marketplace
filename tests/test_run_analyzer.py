"""Cost-math and attribution coverage for the run analyzer + benchmark harness.

Pins the two things that must stay honest as the run-usage benchmark evolves:

* **Cost math** — synthetic ``usage`` dicts at known rates produce a known USD
  cost, with the prompt-cache multipliers (write-5m 1.25x, write-1h 2x,
  read 0.1x) applied to the input rate. This is the arithmetic the
  ``total_cost_usd`` cross-check leans on.
* **Attribution** — a fixture transcript with a main turn, a subagent
  (sidechain) turn, a tool call, and an unpriced model is split correctly across
  ``by_scope`` / ``by_model`` / ``by_tool``, and an unpriced model is surfaced
  (never silently $0).

Plus the harness record/diff plumbing (build_record cross-check flag,
diff_last_two delta).
"""
import json

import pytest

from run_analyzer import analyze_transcript, normalize_model, usage_cost, _zero_usage
import run_benchmark


def _usage(**kw):
    u = _zero_usage()
    u.update(kw)
    return u


def test_normalize_model_strips_context_tier_suffix():
    assert normalize_model("claude-opus-4-8[1m]") == "claude-opus-4-8"
    assert normalize_model("claude-sonnet-4-6") == "claude-sonnet-4-6"
    assert normalize_model(None) == ""


def test_plain_input_output_cost():
    # Sonnet: $3/1M in, $15/1M out.
    cost = usage_cost(_usage(input_tokens=1_000_000, output_tokens=1_000_000),
                      "claude-sonnet-4-6")
    assert cost == pytest.approx(3.0 + 15.0)


def test_cache_multipliers_applied_to_input_rate():
    # Opus: $5/1M in. write-5m 1.25x -> $6.25/1M; write-1h 2x -> $10/1M; read 0.1x -> $0.50/1M.
    assert usage_cost(_usage(cache_write_5m_tokens=1_000_000), "claude-opus-4-8") == pytest.approx(6.25)
    assert usage_cost(_usage(cache_write_1h_tokens=1_000_000), "claude-opus-4-8") == pytest.approx(10.0)
    assert usage_cost(_usage(cache_read_tokens=1_000_000), "claude-opus-4-8") == pytest.approx(0.50)


def test_unpriced_model_returns_none():
    assert usage_cost(_usage(input_tokens=100), "made-up-model") is None


def _write_transcript(tmp_path, lines):
    p = tmp_path / "t.jsonl"
    p.write_text("\n".join(json.dumps(l) for l in lines) + "\n")
    return p


def test_analyze_splits_main_subagent_tool_and_unpriced(tmp_path):
    lines = [
        {"type": "user"},  # ignored
        # main turn, opus, writes 1h cache + a tool call
        {"type": "assistant", "isSidechain": False, "message": {
            "model": "claude-opus-4-8",
            "usage": {"input_tokens": 10, "output_tokens": 20,
                      "cache_creation": {"ephemeral_1h_input_tokens": 1_000_000,
                                         "ephemeral_5m_input_tokens": 0}},
            "content": [{"type": "tool_use", "name": "Bash"},
                        {"type": "text", "text": "hi"}],
        }},
        # subagent (sidechain) turn, sonnet, cache read
        {"type": "assistant", "isSidechain": True, "message": {
            "model": "claude-sonnet-4-6",
            "usage": {"cache_read_input_tokens": 1_000_000},
            "content": [],
        }},
        # unpriced model — usage counted, cost excluded, surfaced
        {"type": "assistant", "isSidechain": False, "message": {
            "model": "mystery-model", "usage": {"input_tokens": 5}, "content": [],
        }},
    ]
    report = analyze_transcript(_write_transcript(tmp_path, lines))

    assert report["assistant_messages"] == 3
    assert report["unpriced_models"] == ["mystery-model"]
    assert report["by_tool"] == {"Bash": 1}

    # main scope: opus 1h-write $10 + tiny in/out; subagent: sonnet read $0.30.
    assert report["by_scope"]["main"]["messages"] == 2
    assert report["by_scope"]["subagent"]["messages"] == 1
    assert report["by_scope"]["main"]["cost_usd"] == pytest.approx(
        10.0 + 10 * 5e-6 + 20 * 25e-6, rel=1e-6)
    assert report["by_scope"]["subagent"]["cost_usd"] == pytest.approx(0.30, rel=1e-6)

    # totals fold every class across scopes.
    assert report["totals"]["cache_write_1h_tokens"] == 1_000_000
    assert report["totals"]["cache_read_tokens"] == 1_000_000


def test_streamed_duplicate_message_billed_once(tmp_path):
    # Claude Code writes the SAME assistant message multiple times as it streams,
    # each copy carrying the same message.id and identical usage. Summing per line
    # double-counts; the analyzer must bill each message.id once and dedupe
    # tool_use by block id. (Regression: the naive sum overshot total_cost_usd ~2.5x.)
    usage = {"output_tokens": 1000, "cache_creation": {
        "ephemeral_1h_input_tokens": 0, "ephemeral_5m_input_tokens": 0}}
    dup = {"type": "assistant", "isSidechain": False, "message": {
        "id": "msg_dup", "model": "claude-sonnet-4-6", "usage": usage,
        "content": [{"type": "tool_use", "id": "tb1", "name": "Bash"}]}}
    lines = [dup, dict(dup), dict(dup)]  # same message streamed three times
    report = analyze_transcript(_write_transcript(tmp_path, lines))

    assert report["assistant_messages"] == 1          # billed once, not 3x
    assert report["totals"]["output_tokens"] == 1000  # not 3000
    assert report["by_tool"] == {"Bash": 1}           # tool deduped by block id


def test_aggregate_cache_without_split_attributed_to_5m(tmp_path):
    # Older transcript: only cache_creation_input_tokens, no 5m/1h split.
    lines = [{"type": "assistant", "isSidechain": False, "message": {
        "model": "claude-opus-4-8",
        "usage": {"cache_creation_input_tokens": 1_000_000}, "content": []}}]
    report = analyze_transcript(_write_transcript(tmp_path, lines))
    assert report["totals"]["cache_write_5m_tokens"] == 1_000_000
    # 5m multiplier 1.25x on opus $5/1M input -> $6.25
    assert report["total_cost_usd"] == pytest.approx(6.25)


def test_build_record_crosscheck_flag(tmp_path):
    lines = [{"type": "assistant", "isSidechain": False, "message": {
        "model": "claude-sonnet-4-6",
        "usage": {"cache_creation": {"ephemeral_1h_input_tokens": 1_000_000,
                                     "ephemeral_5m_input_tokens": 0}},
        "content": []}}]
    transcript = _write_transcript(tmp_path, lines)
    derived = analyze_transcript(transcript)["total_cost_usd"]  # sonnet 1h write 2x -> $6

    ok = run_benchmark.build_record(
        {"total_cost_usd": derived, "session_id": "s", "num_turns": 1},
        transcript, "task", "abc123")
    assert ok["cost_crosscheck_ok"] is True
    assert ok["derived_cost_usd"] == pytest.approx(6.0)

    off = run_benchmark.build_record(
        {"total_cost_usd": derived * 2, "session_id": "s", "num_turns": 1},
        transcript, "task", "abc123")
    assert off["cost_crosscheck_ok"] is False


def test_diff_last_two(tmp_path):
    baseline = tmp_path / "baseline.jsonl"
    recs = [
        {"task_id": "t", "git_sha": "aaa", "derived_cost_usd": 1.0, "num_turns": 10,
         "num_subagent_messages": 2, "claude_total_cost_usd": 1.0,
         "totals": {"input_tokens": 100}},
        {"task_id": "t", "git_sha": "bbb", "derived_cost_usd": 1.5, "num_turns": 12,
         "num_subagent_messages": 3, "claude_total_cost_usd": 1.5,
         "totals": {"input_tokens": 150}},
    ]
    baseline.write_text("\n".join(json.dumps(r) for r in recs) + "\n")
    d = run_benchmark.diff_last_two("t", baseline)
    assert d["from_sha"] == "aaa" and d["to_sha"] == "bbb"
    assert d["derived_cost_usd"]["delta"] == pytest.approx(0.5)
    assert d["totals"]["input_tokens"]["delta"] == 50


def test_diff_needs_two_records(tmp_path):
    baseline = tmp_path / "baseline.jsonl"
    baseline.write_text(json.dumps(
        {"task_id": "t", "totals": {}}) + "\n")
    assert "error" in run_benchmark.diff_last_two("t", baseline)
