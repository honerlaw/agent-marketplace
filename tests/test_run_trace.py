"""Attribution coverage for the wall-time tracer (``scripts/run_trace.py``).

Every rule the tracer applies to a real Claude Code transcript is pinned here on
a synthetic fixture whose timestamps are chosen so the right answer is exact:

* **Turns** start at the event that began them and end at their
  ``turn_duration`` marker; ``durationMs`` is a cross-check only (it can
  overshoot the turn by 12x on real data).
* **In-turn time** partitions into model / tool:<Name> / user / harness and sums
  to active time; **between turns** is background / scheduled / user-idle.
* **Subagents** come from ``<session>/subagents/`` sidecars, prefer the
  task-notification's ``duration_ms``, and report both sum and union.
* **Gate/tier/role** — a panel is recognised by its launch batch even when no
  description says "panel"; a lone Skeptic is a reviewer; unknowns are kept.
* **Runs and phases** — one session can hold several orchestrator runs, and a
  run's phase signals never leak into another run.
"""
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone

import pytest

import run_trace as rt

T0 = datetime(2026, 9, 1, 12, 0, 0, tzinfo=timezone.utc)


def ts(sec: float) -> str:
    return (T0 + timedelta(seconds=sec)).isoformat().replace("+00:00", "Z")


_n = [0]


def _uuid():
    _n[0] += 1
    return f"u{_n[0]}"


def prompt(t, text="do the thing", kind="human", meta=False):
    e = {"type": "user", "uuid": _uuid(), "timestamp": ts(t), "origin": {"kind": kind},
         "message": {"role": "user", "content": text}}
    if meta:
        e["isMeta"] = True
    return e


def assistant(t, *tools, mid=None, text="ok"):
    content = [{"type": "text", "text": text}]
    for tool in tools:
        content.append({"type": "tool_use", "id": tool["id"], "name": tool["name"],
                        "input": tool.get("input", {})})
    return {"type": "assistant", "uuid": _uuid(), "timestamp": ts(t),
            "message": {"id": mid or f"m{_uuid()}", "role": "assistant", "content": content,
                        "usage": {"output_tokens": 10}}}


def result(t, tool_id):
    return {"type": "user", "uuid": _uuid(), "timestamp": ts(t),
            "message": {"role": "user", "content": [
                {"type": "tool_result", "tool_use_id": tool_id, "content": "done"}]}}


def marker(t, duration_s):
    return {"type": "system", "subtype": "turn_duration", "uuid": _uuid(), "timestamp": ts(t),
            "durationMs": int(duration_s * 1000)}


def tool(tid, name, **inp):
    return {"id": tid, "name": name, "input": inp}


def notification(t, tool_use_id, duration_ms):
    body = (f"<task-notification>\n<task-id>x</task-id>\n<tool-use-id>{tool_use_id}</tool-use-id>\n"
            f"<status>completed</status>\n<usage><subagent_tokens>5</subagent_tokens>"
            f"<duration_ms>{duration_ms}</duration_ms></usage>\n</task-notification>")
    return {"type": "queue-operation", "operation": "enqueue", "timestamp": ts(t), "content": body}


def write_session(tmp_path, events, name="sess", subagents=()):
    path = tmp_path / f"{name}.jsonl"
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n")
    if subagents:
        d = tmp_path / name / "subagents"
        d.mkdir(parents=True)
        for i, (meta, sub_events) in enumerate(subagents):
            (d / f"agent-a{i}.jsonl").write_text("\n".join(json.dumps(e) for e in sub_events) + "\n")
            (d / f"agent-a{i}.meta.json").write_text(json.dumps(meta))
    return path


def orchestrator_prompt(t, name="minerva:propose-ship-auto", args="build it"):
    return prompt(t, f"<command-message>{name}</command-message>\n<command-name>/{name}</command-name>\n"
                     f"<command-args>{args}</command-args>")


# --------------------------------------------------------------------------- turns


def test_turn_spans_define_active_time_and_duration_ms_is_only_a_crosscheck():
    # Turn 1: 0 → 10. Turn 2: 100 → 130, but its marker claims 5000 s (the real
    # harness reaches back across turns); summing durationMs would give active > wall.
    events = [
        prompt(0), assistant(10), marker(10, 10),
        prompt(100), assistant(130), marker(130, 5000),
    ]
    events = [dict(e, _t=rt._ts(e["timestamp"])) for e in events]
    att = rt.attribute(events)
    assert att["active_s"] == pytest.approx(40.0)
    assert att["reported_active_s"] == pytest.approx(5010.0)
    assert att["reported_disagreements"] == 1
    turns = rt._turns(events)
    assert all(turns[i + 1]["start"] >= turns[i]["end"] for i in range(len(turns) - 1))


def test_duration_ms_undershoot_keeps_the_question_wait_as_user_time():
    # The harness's durationMs excludes an open AskUserQuestion (real turn:
    # 1,471 s span, 476 s reported). The trace keeps that wait in active time,
    # attributed to `user` — the question was on the critical path.
    ask = tool("q1", "AskUserQuestion")
    events = [prompt(0), assistant(10, ask), result(1000, "q1"), assistant(1010), marker(1010, 20)]
    events = [dict(e, _t=rt._ts(e["timestamp"])) for e in events]
    att = rt.attribute(events)
    assert att["active_s"] == pytest.approx(1010.0)
    assert att["reported_active_s"] == pytest.approx(20.0)
    assert att["reported_disagreements"] == 1
    assert rt._clip(att["segments"], 0, 1e12)["user"] == pytest.approx(990.0)


def test_idle_bookkeeping_before_the_starting_event_is_not_turn_time():
    # A queue-operation and a PR-link line land at t=20, long before the human
    # prompt at t=300 that actually starts the turn.
    events = [prompt(0), assistant(5), marker(5, 5),
              {"type": "queue-operation", "operation": "enqueue", "timestamp": ts(20), "content": "x"},
              {"type": "pr-link", "uuid": _uuid(), "timestamp": ts(21)},
              prompt(300), assistant(310), marker(310, 10)]
    events = [dict(e, _t=rt._ts(e["timestamp"])) for e in events]
    turns = rt._turns(events)
    assert turns[1]["start"] == pytest.approx(rt._ts(ts(300)))
    att = rt.attribute(events)
    assert att["active_s"] == pytest.approx(15.0)
    assert rt._clip(att["segments"], 0, 1e12)["user-idle"] == pytest.approx(295.0)


def test_between_turn_gaps_are_classified_by_what_started_the_next_turn():
    wake = tool("w1", "ScheduleWakeup", delaySeconds=60)
    events = [
        prompt(0), assistant(1), marker(1, 1),
        prompt(11, kind="task-notification"), assistant(12), marker(12, 1),     # 10 s background
        prompt(32, "hand-back", kind="peer", meta=True), assistant(33), marker(33, 1),  # 20 s background
        prompt(35), assistant(36, wake), result(37, "w1"), assistant(38), marker(38, 3),  # 2 s user-idle
        {"type": "user", "uuid": _uuid(), "timestamp": ts(98), "message": {"content": "wake"}},
        assistant(99), marker(99, 1),                                            # 60 s scheduled
    ]
    events = [dict(e, _t=rt._ts(e["timestamp"])) for e in events]
    by = rt._clip(rt.attribute(events)["segments"], 0, 1e12)
    assert by["background-wait"] == pytest.approx(30.0)
    assert by["user-idle"] == pytest.approx(2.0)
    assert by["scheduled-wait"] == pytest.approx(60.0)


def test_in_turn_time_partitions_into_model_tool_user_harness():
    bash = tool("b1", "Bash", command="python3 -m pytest -q")
    ask = tool("q1", "AskUserQuestion")
    events = [
        prompt(0),
        assistant(4, bash),                 # model 0→4
        result(10, "b1"),                   # tool:Bash 4→10
        assistant(12, ask),                 # model 10→12
        result(40, "q1"),                   # user 12→40
        assistant(45),                      # model 40→45
        {"type": "system", "subtype": "stop_hook_summary", "uuid": _uuid(), "timestamp": ts(47)},  # harness 45→47
        marker(47, 47),
    ]
    events = [dict(e, _t=rt._ts(e["timestamp"])) for e in events]
    att = rt.attribute(events)
    by = rt._clip(att["segments"], 0, 1e12)
    assert by == pytest.approx({"model": 11.0, "tool:Bash": 6.0, "user": 28.0, "harness": 2.0})
    assert sum(by.values()) == pytest.approx(att["active_s"])


def test_parallel_tool_calls_give_the_gap_to_the_earliest_opened():
    events = [prompt(0), assistant(1, tool("r1", "Read")), assistant(2, tool("b1", "Bash", command="ls")),
              result(5, "r1"), result(9, "b1"), assistant(10), marker(10, 10)]
    events = [dict(e, _t=rt._ts(e["timestamp"])) for e in events]
    by = rt._clip(rt.attribute(events)["segments"], 0, 1e12)
    assert by["tool:Read"] == pytest.approx(4.0)   # 1→5, although Bash was also open 2→5
    assert by["tool:Bash"] == pytest.approx(4.0)   # 5→9


@pytest.mark.parametrize("command,head", [
    ("gh pr checks 12 --watch", "gh pr"),
    ("W=.minerva/worktrees/x && git -C $W status", "git status"),
    ("cd /repo && python3 -m pytest -q tests", "python3 -m pytest"),
    ("python3 - <<'PY'\nprint(1)\nPY", "python3 (stdin)"),
    ("python3 -c 'print(1)'", "python3 -c"),
    ("python3 scripts/run_trace.py x.jsonl", "python3 run_trace.py"),
    ("FOO=1 sed -n 1,5p a.md", "sed"),
    ("gh -R owner/repo issue list", "gh issue"),
])
def test_bash_head(command, head):
    assert rt.bash_head(command) == head


# --------------------------------------------------------------------------- subagents


@pytest.mark.parametrize("desc,role,gate,rnd", [
    ("Whole-proposal: Proponent", "proponent", "whole-proposal", 1),
    ("Scope panel r2: Skeptic", "skeptic", "scope", 2),
    ("Skeptic — approach selection", "skeptic", "approach", 1),
    ("Completion Verifier", "verifier", "completion", 1),
    ("Verifier — final check", "verifier", "completion", 1),
    ("Verify completion criteria", "verifier", "completion", 1),
    ("Scope fold-audit re-check", "fold-audit", "scope", 1),
    ("Code quality review of diff", "code-review", "review", 1),
    ("Skeptic on replan acceptance", "skeptic", "replan", 1),
    ("Research Reddit Ads API facts", "unknown", "unknown", 1),
    # "recheck" inside a slug or diff name is not the fold-audit role.
    ("Verify balanced-rechecks-folds completion", "verifier", "completion", 1),
    ("Code-quality review of balanced re-check diff", "code-review", "review", 1),
    ("New-plan panel: Skeptic", "skeptic", "replan", 1),
])
def test_description_vocabulary(desc, role, gate, rnd):
    got = rt.parse_description(desc)
    assert (got["role"], got["gate"], got["round"]) == (role, gate, rnd)


def _sub(tid, desc, start, dur_events=60.0, model="sonnet"):
    meta = {"agentType": "general-purpose", "description": desc, "toolUseId": tid, "model": model}
    evs = [prompt(start, "brief"), assistant(start + dur_events / 2),
           assistant(start + dur_events)]
    return meta, evs


def _agent(tid, desc):
    return tool(tid, "Agent", description=desc, prompt="...")


def test_subagents_link_prefer_notification_duration_and_report_sum_and_union(tmp_path):
    # Two overlapping subagents launched in ONE assistant message at t=10.
    events = [
        orchestrator_prompt(0),
        assistant(10, _agent("t1", "Whole-proposal: Proponent"), _agent("t2", "Whole-proposal: Skeptic"),
                  mid="batch"),
        result(11, "t1"), result(11, "t2"), assistant(12), marker(12, 12),
        notification(80, "t1", 60000),
        prompt(80, "<task-notification>t1</task-notification>", kind="task-notification"),
        assistant(81), marker(81, 1),
        prompt(200, "<task-notification>t2</task-notification>", kind="task-notification"),
        assistant(201), marker(201, 1),
    ]
    subs = [_sub("t1", "Whole-proposal: Proponent", 10, 55), _sub("t2", "Whole-proposal: Skeptic", 10, 180)]
    tr = rt.trace_session(write_session(tmp_path, events, subagents=subs))
    by_desc = {s["description"]: s for s in tr["subagents"]}
    assert by_desc["Whole-proposal: Proponent"]["dur"] == pytest.approx(60.0)       # notification wins
    assert by_desc["Whole-proposal: Proponent"]["dur_source"] == "notification"
    assert by_desc["Whole-proposal: Skeptic"]["dur"] == pytest.approx(180.0)        # file-span fallback
    assert by_desc["Whole-proposal: Skeptic"]["dur_source"] == "file-span"
    # No description says "panel": the shared launch batch makes both panel members.
    assert {s["tier"] for s in tr["subagents"]} == {"panel"}
    s = tr["runs"][0]["summary"]
    assert s["subagent_sum_s"] == pytest.approx(240.0)
    assert s["subagent_union_s"] == pytest.approx(180.0)
    assert s["subagent_union_s"] < s["subagent_sum_s"]


def test_lone_skeptic_is_reviewer_even_when_a_later_panel_shares_its_gate(tmp_path):
    events = [
        orchestrator_prompt(0),
        assistant(10, _agent("s0", "Skeptic: whole-proposal soundness")), result(11, "s0"),
        assistant(12), marker(12, 12),
        prompt(300, "x", kind="task-notification"),
        assistant(310, _agent("p1", "Panel Proponent: whole-proposal"),
                  _agent("p2", "Panel Skeptic: whole-proposal"), mid="panel"),
        result(311, "p1"), result(311, "p2"), assistant(312), marker(312, 12),
    ]
    subs = [_sub("s0", "Skeptic: whole-proposal soundness", 10),
            _sub("p1", "Panel Proponent: whole-proposal", 310),
            _sub("p2", "Panel Skeptic: whole-proposal", 310)]
    tr = rt.trace_session(write_session(tmp_path, events, subagents=subs))
    tiers = {s["description"]: s["tier"] for s in tr["subagents"]}
    assert tiers["Skeptic: whole-proposal soundness"] == "reviewer"
    assert tiers["Panel Skeptic: whole-proposal"] == "panel"


def test_unknown_descriptions_are_reported_not_dropped(tmp_path):
    events = [orchestrator_prompt(0), assistant(1, _agent("u1", "Research Reddit Ads API facts")),
              result(2, "u1"), assistant(3), marker(3, 3)]
    tr = rt.trace_session(write_session(tmp_path, events, subagents=[_sub("u1", "Research Reddit Ads API facts", 1)]))
    assert tr["runs"][0]["unknown_subagents"] == ["Research Reddit Ads API facts"]
    assert tr["subagents"][0]["tier"] == "unknown"


# --------------------------------------------------------------------------- runs + phases


def _lifecycle(t0, name="minerva:propose-ship-auto"):
    """One orchestrator run with every phase signal, starting at t0."""
    return [
        orchestrator_prompt(t0, name),
        assistant(t0 + 10, tool(f"wt{t0}", "Bash", command="git worktree add -b x .minerva/worktrees/x main")),
        result(t0 + 11, f"wt{t0}"),
        assistant(t0 + 50, _agent(f"v{t0}", "Completion Verifier")), result(t0 + 51, f"v{t0}"),
        assistant(t0 + 70, _agent(f"c{t0}", "Code quality review of diff")), result(t0 + 71, f"c{t0}"),
        assistant(t0 + 90, tool(f"k{t0}", "Write", file_path="/r/.minerva/knowledge/2026-x.md")),
        result(t0 + 91, f"k{t0}"),
        assistant(t0 + 100, tool(f"s{t0}", "Skill", skill="minerva:ship")), result(t0 + 101, f"s{t0}"),
        assistant(t0 + 120, tool(f"cl{t0}", "Skill", skill="minerva:cleanup")), result(t0 + 121, f"cl{t0}"),
        assistant(t0 + 130), marker(t0 + 130, 130),
    ]


def test_phases_are_inferred_in_order_with_the_event_that_set_each_boundary(tmp_path):
    tr = rt.trace_session(write_session(tmp_path, _lifecycle(0)))
    run = tr["runs"][0]
    assert [w["phase"] for w in run["phases"]] == list(rt.PHASES)
    events = {w["phase"]: w["event"] for w in run["phases"]}
    assert events["work"] == "Bash: git worktree add"
    assert events["verify"] == "Agent: Completion Verifier"
    assert events["promote"].startswith("Write ")
    assert events["cleanup"] == "Skill minerva:cleanup"
    assert run["phase_warnings"] == []


def test_missing_phase_signal_warns_and_never_guesses(tmp_path):
    events = [orchestrator_prompt(0), assistant(5, tool("s", "Skill", skill="minerva:ship")),
              result(6, "s"), assistant(7), marker(7, 7)]
    run = rt.trace_session(write_session(tmp_path, events))["runs"][0]
    assert [w["phase"] for w in run["phases"]] == ["propose", "ship"]
    assert any("no signal for phase 'work'" in w for w in run["phase_warnings"])


def test_out_of_order_signal_is_ignored_and_reported_but_replan_is_an_event(tmp_path):
    events = [orchestrator_prompt(0),
              assistant(5, tool("s", "Skill", skill="minerva:ship")), result(6, "s"),
              assistant(8, tool("w", "Bash", command="git worktree add y")), result(9, "w"),
              assistant(10, tool("r", "Skill", skill="minerva:replan")), result(11, "r"),
              assistant(12), marker(12, 12)]
    run = rt.trace_session(write_session(tmp_path, events))["runs"][0]
    assert [w["phase"] for w in run["phases"]] == ["propose", "ship"]
    assert any("out-of-order" in w and "work" in w for w in run["phase_warnings"])
    assert [r["event"] for r in run["replans"]] == ["Skill minerva:replan"]
    assert not any("replan" in w for w in run["phase_warnings"])


def test_two_runs_in_one_session_keep_their_own_phase_signals(tmp_path):
    # A quick run (with its own ship + cleanup) followed by an auto run that
    # never reaches ship: the auto run must not inherit the quick run's signals.
    events = _lifecycle(0, "minerva:propose-ship-quick") + [
        orchestrator_prompt(1000),
        assistant(1010, tool("wt2", "Bash", command="git worktree add z")), result(1011, "wt2"),
        assistant(1020), marker(1020, 20),
    ]
    tr = rt.trace_session(write_session(tmp_path, events))
    assert [r["caller"] for r in tr["runs"]] == ["minerva:propose-ship-quick", "minerva:propose-ship-auto"]
    assert [w["phase"] for w in tr["runs"][1]["phases"]] == ["propose", "work"]
    assert "ship" in [w["phase"] for w in tr["runs"][0]["phases"]]
    # The quick run ends where the auto run begins — the auto run's worktree
    # signal must not reach back into it as an out-of-order warning.
    assert tr["runs"][0]["end"] == tr["runs"][1]["start"]
    assert tr["runs"][0]["phase_warnings"] == []


def test_cleanup_only_reentry_extends_the_run_it_resumes(tmp_path):
    events = _lifecycle(0) + [
        orchestrator_prompt(5000, args="--cleanup-only 2026-09-01-x --retry=1"),
        assistant(5001), marker(5001, 1),
    ]
    tr = rt.trace_session(write_session(tmp_path, events))
    assert len(tr["runs"]) == 1
    assert tr["runs"][0]["resumes"] == 1


# --------------------------------------------------------------------------- aggregate + CLI


def test_all_aggregates_auto_runs_with_totals_and_medians(tmp_path):
    subs = [_sub("v0", "Completion Verifier", 50), _sub("c0", "Code quality review of diff", 70)]
    write_session(tmp_path, _lifecycle(0), name="a", subagents=subs)
    write_session(tmp_path, _lifecycle(0) + [orchestrator_prompt(4000, "minerva:propose-ship-quick"),
                                               assistant(4001), marker(4001, 1)], name="b", subagents=subs)
    agg = rt.aggregate(tmp_path)
    assert [(r["session"], r["caller"]) for r in agg["runs"]] == [
        ("a", "minerva:propose-ship-auto"), ("b", "minerva:propose-ship-auto")]
    assert agg["phases"]["propose"]["runs"] == 2
    assert agg["phases"]["propose"]["total_s"] == pytest.approx(20.0)
    assert agg["phases"]["propose"]["median_s"] == pytest.approx(10.0)
    assert {g["gate"] for g in agg["gates"]} == {"completion", "review"}
    assert all(g["runs"] == 2 for g in agg["gates"])
    assert len(rt.aggregate(tmp_path, rt.ORCHESTRATORS)["runs"]) == 3


def test_cli_text_and_json(tmp_path, capsys):
    path = write_session(tmp_path, _lifecycle(0))
    assert rt.main([str(path)]) == 0
    out = capsys.readouterr().out
    for needle in ("== run 0", "phase", "slowest spans", "cross-check", "overlapping view"):
        assert needle in out
    assert rt.main([str(path), "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["runs"][0]["caller"] == "minerva:propose-ship-auto"
    assert rt.main(["--all", "--project-dir", str(tmp_path)]) == 0
    assert "1 run(s)" in capsys.readouterr().out
    assert rt.main(["sess", "--project-dir", str(tmp_path), "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["session"] == "sess"


# --------------------------------------------------------------------------- review fixes


def test_trailing_unmarked_turn_starts_at_its_starting_event():
    # No closing marker: idle bookkeeping at t=20..200 before the human prompt at
    # t=2600 must be idle, not 40 minutes of active `model`/`harness`.
    events = [prompt(0), assistant(5), marker(5, 5),
              {"type": "pr-link", "uuid": _uuid(), "timestamp": ts(20)},
              {"type": "system", "subtype": "away_summary", "uuid": _uuid(), "timestamp": ts(200)},
              prompt(2600), assistant(2610)]
    events = [dict(e, _t=rt._ts(e["timestamp"])) for e in events]
    att = rt.attribute(events)
    assert att["active_s"] == pytest.approx(15.0)
    assert rt._clip(att["segments"], 0, 1e12)["user-idle"] == pytest.approx(2595.0)


def _promote_run(knowledge_cmd):
    return [
        orchestrator_prompt(0),
        assistant(10, tool("wt", "Bash", command="git worktree add x")), result(11, "wt"),
        assistant(20, tool("cap", "Bash", command="cat > .minerva/knowledge/2026-x-constraint-a.md <<'EOF'\nx\nEOF")),
        result(21, "cap"),                                                      # mid-work capture
        assistant(50, _agent("v", "Completion Verifier")), result(51, "v"),
        assistant(70, _agent("c", "Code quality review of diff")), result(71, "c"),
        assistant(90, tool("k", "Bash", command=knowledge_cmd)), result(91, "k"),
        assistant(100), marker(100, 100),
    ]


@pytest.mark.parametrize("cmd", [
    "cat > .minerva/knowledge/2026-09-26-pattern-x.md <<'EOF'\nbody\nEOF",
    "cd .minerva/worktrees/u/.minerva/knowledge && cat > 2026-09-26-pattern-x.md <<'EOF'\nb\nEOF",
    "git mv .minerva/work/u/note.md .minerva/knowledge/2026-09-26-pattern-x.md",
])
def test_knowledge_written_through_bash_starts_promote(tmp_path, cmd):
    run = rt.trace_session(write_session(tmp_path, _promote_run(cmd)))["runs"][0]
    phases = {w["phase"]: w for w in run["phases"]}
    assert "promote" in phases
    assert phases["promote"]["event"] == "Bash: write under .minerva/knowledge/"


def test_reading_knowledge_is_not_a_promote_signal():
    assert not rt._writes_knowledge("grep -rn foo .minerva/knowledge/ | head")
    assert not rt._writes_knowledge("cat .minerva/knowledge/index.md")


def test_mid_work_knowledge_capture_does_not_swallow_verify_and_review(tmp_path):
    run = rt.trace_session(write_session(tmp_path, _promote_run(
        "cat > .minerva/knowledge/2026-y-pattern-b.md <<'EOF'\nb\nEOF")))["runs"][0]
    assert [w["phase"] for w in run["phases"]] == ["propose", "work", "verify", "review", "promote"]
    assert [c["event"] for c in run["knowledge_captures"]] == ["Bash: write under .minerva/knowledge/"]
    assert not any("out-of-order" in w for w in run["phase_warnings"])


def test_skill_promote_is_a_promote_signal(tmp_path):
    events = [orchestrator_prompt(0), assistant(5, tool("p", "Skill", skill="minerva:promote")),
              result(6, "p"), assistant(7), marker(7, 7)]
    run = rt.trace_session(write_session(tmp_path, events))["runs"][0]
    assert [w["phase"] for w in run["phases"]] == ["propose", "promote"]


def test_aggregate_phase_totals_are_active_time_with_waits_apart(tmp_path):
    # The run's last phase is followed by 5,000 s of unrelated user idle.
    events = _lifecycle(0) + [prompt(5130), assistant(5140), marker(5140, 10)]
    write_session(tmp_path, events, name="a")
    agg = rt.aggregate(tmp_path)
    cleanup = agg["phases"]["cleanup"]
    assert cleanup["total_s"] == pytest.approx(20.0)        # 120→130 and 5130→5140
    assert cleanup["waits_total_s"] == pytest.approx(5000.0)


def test_missing_meta_links_the_sidecar_through_the_agent_result(tmp_path):
    events = [orchestrator_prompt(0),
              assistant(10, _agent("t1", "Scope panel: Skeptic")),
              {"type": "user", "uuid": _uuid(), "timestamp": ts(11), "message": {"content": [
                  {"type": "tool_result", "tool_use_id": "t1",
                   "content": [{"type": "text", "text": "Async agent launched. agentId: a0 (internal)"}]}]}},
              assistant(12), marker(12, 12)]
    path = write_session(tmp_path, events, subagents=[_sub("t1", "Scope panel: Skeptic", 10)])
    (tmp_path / "sess" / "subagents" / "agent-a0.meta.json").unlink()
    sub = rt.trace_session(path)["subagents"][0]
    assert sub["description"] == "Scope panel: Skeptic"
    assert sub["tier"] == "panel"
    assert sub["tool_use_id"] == "t1"


def test_non_object_meta_is_tolerated(tmp_path):
    events = [orchestrator_prompt(0), assistant(1, _agent("u1", "Completion Verifier")),
              result(2, "u1"), assistant(3), marker(3, 3)]
    path = write_session(tmp_path, events, subagents=[_sub("u1", "Completion Verifier", 1)])
    (tmp_path / "sess" / "subagents" / "agent-a0.meta.json").write_text("[1, 2]")
    assert len(rt.trace_session(path)["subagents"]) == 1


def test_malformed_transcript_is_skipped_and_reported_not_fatal(tmp_path, monkeypatch):
    write_session(tmp_path, _lifecycle(0), name="good")
    write_session(tmp_path, _lifecycle(0), name="bad")
    real = rt.trace_session

    def flaky(path):
        if Path(path).stem == "bad":
            raise TypeError("boom")
        return real(path)

    monkeypatch.setattr(rt, "trace_session", flaky)
    agg = rt.aggregate(tmp_path)
    assert [r["session"] for r in agg["runs"]] == ["good"]
    assert agg["skipped"] == [{"session": "bad", "error": "TypeError: boom"}]


def test_null_text_and_string_duration_do_not_crash(tmp_path):
    events = [orchestrator_prompt(0),
              {"type": "user", "uuid": _uuid(), "timestamp": ts(1),
               "message": {"content": [{"type": "text", "text": None}]}},
              assistant(2),
              {"type": "system", "subtype": "turn_duration", "uuid": _uuid(), "timestamp": ts(3),
               "durationMs": "not-a-number"}]
    tr = rt.trace_session(write_session(tmp_path, events))
    assert tr["turns"] == 1


def test_naive_timestamps_are_utc():
    assert rt._ts("2026-09-26T10:00:00") == rt._ts("2026-09-26T10:00:00Z")


def test_cli_argument_errors_exit_2(tmp_path, capsys):
    assert rt.main(["--project-dir"]) == 2
    assert rt.main(["nope", "--project-dir", str(tmp_path)]) == 2
    assert rt.main(["--all", "--project-dir", str(tmp_path / "missing")]) == 2
    err = capsys.readouterr().err
    assert "needs a directory" in err and "no transcript" in err


def test_default_project_dir_anchors_to_the_primary_checkout(tmp_path):
    import subprocess
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "--allow-empty", "-m", "i"], check=True,
                   env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                        "GIT_COMMITTER_EMAIL": "t@t", "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"})
    wt = repo / ".minerva" / "worktrees" / "u"
    subprocess.run(["git", "-C", str(repo), "worktree", "add", "-q", "-b", "u", str(wt)], check=True)
    assert rt.default_project_dir(wt) == rt.default_project_dir(repo)
    assert "worktrees" not in rt.default_project_dir(wt).name


def test_panel_batch_match_requires_the_same_round(tmp_path):
    # A round-2 Proponent launched within the batch window of a lone round-1
    # Skeptic at the same gate does not make that Skeptic a panel member.
    events = [orchestrator_prompt(0),
              assistant(10, _agent("s", "Skeptic: scope check")), result(11, "s"),
              assistant(15, _agent("p", "Scope r2: Proponent")), result(16, "p"),
              assistant(17), marker(17, 17)]
    subs = [_sub("s", "Skeptic: scope check", 10), _sub("p", "Scope r2: Proponent", 15)]
    tiers = {s["description"]: s["tier"] for s in rt.trace_session(write_session(tmp_path, events, subagents=subs))["subagents"]}
    assert tiers["Skeptic: scope check"] == "reviewer"
