#!/usr/bin/env python3
"""Deterministic, read-only **wall-time trace** of a Claude Code session.

``run_analyzer.py`` answers "what did this run cost?"; this answers "where did
the time go?" — the tracing view a service gets from spans, rebuilt after the
fact from the session's on-disk transcripts:

* ``~/.claude/projects/<encoded-cwd>/<session>.jsonl`` — the main thread;
* ``<session>/subagents/agent-<id>.jsonl`` + ``agent-<id>.meta.json`` — one file
  per Agent-spawned subagent (NOT marked ``isSidechain`` in the main file).

It is built to optimise ``minerva:propose-ship-auto``: time is broken down by
orchestrator **run**, lifecycle **phase**, decision **gate × tier × role**,
**tool** (Bash by command head) and **subagent**, per run and across runs.

Time model (what partitions what — never add the overlapping views):

* **In-turn active time** = the sum of per-turn spans (a turn's first event →
  its ``turn_duration`` marker; turns never overlap). The markers' own
  ``durationMs`` is reported only as a cross-check — it is not a per-turn wall
  time (see ``_turns``). Active time is partitioned into ``model`` (the main model generating), ``tool:<Name>``
  (a tool call is open; the earliest-opened wins when several are — a disclosed
  heuristic; this includes any permission-prompt wait for that call), ``user``
  (an ``AskUserQuestion`` is open) and ``harness`` (a gap ending at a ``system``
  event — hooks). Any other gap with no tool open is ``model``.
* **Between turns** the gap is ``background-wait`` (the next turn was started
  by a task-notification or a subagent hand-back), ``scheduled-wait`` (the
  previous turn armed ``ScheduleWakeup`` and no human started the next one) or
  ``user-idle`` (a human prompt started it).
* **Subagents** are an *overlapping* view: ``sum`` is total subagent compute,
  ``union`` the wall-clock with at least one running. Most of it sits inside
  background-wait or in-turn tool time already.

Subagent durations prefer the ``<task-notification>``'s own ``duration_ms``
(ground truth) and fall back to the sidecar file's first→last timestamp — a
background Agent call's ``tool_result`` returns in ~1s, so pairing tool calls
alone would report a 3-minute Skeptic as 1s.

Phases are **inferred** from observable events inside each run's window and
every boundary names the event that set it; a missing signal is a warning,
never a guess. Descriptions the gate/role vocabulary cannot read are kept and
reported as ``unknown`` — never dropped.

Stdlib only; read-only; every return value is JSON-serializable.
"""
import json
import re
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ORCHESTRATORS = (
    "minerva:propose-ship-auto",
    # Retired callers, folded into propose-ship-auto on 2026-09-23 — still
    # present in older sessions, tagged by caller so `--all` can filter them.
    "minerva:propose-ship-quick",
    "minerva:propose-ship-balanced",
)
PHASES = ("propose", "work", "verify", "review", "promote", "ship", "cleanup")
# Two orchestrator invocations this close together are one run (a slash
# command's prompt followed by the model's own Skill call for it).
SAME_RUN_WINDOW_S = 120.0
# Proponent + Skeptic of one panel are dispatched together; a Skeptic launched
# this close to a same-gate Proponent is a panel member, not a lone reviewer.
PANEL_BATCH_WINDOW_S = 10.0
MULTIPLEXERS = {"gh", "git", "npm", "uv", "docker", "pnpm", "yarn", "cargo"}

_NOTIFICATION_RE = re.compile(r"<task-notification>(.*?)</task-notification>", re.S)
_TOOL_USE_ID_RE = re.compile(r"<tool-use-id>\s*([^<\s]+)\s*</tool-use-id>")
_DURATION_RE = re.compile(r"<duration_ms>\s*(\d+)\s*</duration_ms>")
_COMMAND_NAME_RE = re.compile(r"<command-name>/?([^<\s]+)</command-name>")
_AGENT_ID_RE = re.compile(r"agentId:\s*([A-Za-z0-9]+)")
_COMMAND_ARGS_RE = re.compile(r"<command-args>(.*?)</command-args>", re.S)


# --------------------------------------------------------------------------- loading


def _ts(value) -> "float | None":
    if not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)  # transcripts are UTC; never read a naive stamp as local
    return dt.timestamp()


def load_events(path) -> list:
    """Timestamped events of one JSONL file, deduped by ``uuid``, in time order.

    Streamed assistant messages repeat with the same ``message.id`` but distinct
    ``uuid`` values; they are kept (each copy is a real point in time) and tool
    blocks are deduped by block id downstream. Events without a timestamp are
    dropped; ties keep file order (``sorted`` is stable).
    """
    out, seen = [], set()
    for line in Path(path).read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        t = _ts(obj.get("timestamp"))
        if t is None:
            continue
        uid = obj.get("uuid")
        if uid is not None:
            if uid in seen:
                continue
            seen.add(uid)
        obj["_t"] = t
        out.append(obj)
    return sorted(out, key=lambda e: e["_t"])


def _content_blocks(event) -> list:
    content = (event.get("message") or {}).get("content")
    return content if isinstance(content, list) else []


def _text_of(event) -> str:
    """The plain text a user/queue event carries (string content or text blocks)."""
    if event.get("type") == "queue-operation":
        c = event.get("content")
        return c if isinstance(c, str) else ""
    content = (event.get("message") or {}).get("content")
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    return "".join(
        b["text"] for b in content
        if isinstance(b, dict) and b.get("type") == "text" and isinstance(b.get("text"), str)
    )


def _tool_uses(event):
    if event.get("type") != "assistant":
        return
    for b in _content_blocks(event):
        if isinstance(b, dict) and b.get("type") == "tool_use" and b.get("id"):
            yield b


def _tool_results(event):
    if event.get("type") != "user":
        return
    for b in _content_blocks(event):
        if isinstance(b, dict) and b.get("type") == "tool_result" and b.get("tool_use_id"):
            yield b


def _result_text(block) -> str:
    c = block.get("content")
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        return "".join(x["text"] for x in c if isinstance(x, dict) and isinstance(x.get("text"), str))
    return ""


def _origin_kind(event) -> "str | None":
    origin = event.get("origin")
    if isinstance(origin, dict):
        return origin.get("kind")
    return origin if isinstance(origin, str) else None


# --------------------------------------------------------------------------- bash heads


def bash_head(command: str) -> str:
    """Command head for bucketing Bash time.

    First token of the first command after stripping ``cd … &&`` prefixes and
    ``VAR=value`` assignments; multiplexers (``gh``, ``git``, …) add their next
    non-flag token and ``python -m`` adds its module.
    """
    if not isinstance(command, str):
        return "?"
    segments = re.split(r"&&|\|\||;|\n", command)
    for seg in segments:
        toks = seg.strip().split()
        while toks and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", toks[0]):
            toks = toks[1:]
        if not toks or toks[0] in {"cd", "pushd", "set", "export", "source", "."}:
            continue
        head = Path(toks[0]).name
        rest = toks[1:]
        if head in MULTIPLEXERS:
            sub, skip = None, False
            for t in rest:
                if skip:
                    skip = False
                elif t in ("-C", "-c", "--git-dir", "--work-tree", "-R", "--repo"):
                    skip = True  # option that takes a value (git -C <path>, gh -R <repo>)
                elif not t.startswith("-"):
                    sub = t
                    break
            return f"{head} {sub}" if sub else head
        if re.match(r"^python[0-9.]*$", head):
            if len(rest) >= 2 and rest[0] == "-m":
                return f"{head} -m {rest[1]}"
            if rest and rest[0] == "-c":
                return f"{head} -c"
            if not rest or rest[0] == "-" or rest[0].startswith("<<"):
                return f"{head} (stdin)"
            script = next((t for t in rest if not t.startswith("-")), None)
            return f"{head} {Path(script).name}" if script else head
        return head
    return "?"


def _span_key(name: str, tool_input: dict) -> str:
    if name == "Bash":
        return "Bash:" + bash_head((tool_input or {}).get("command", ""))
    if name == "Skill":
        return "Skill:" + str((tool_input or {}).get("skill", "?"))
    return name


# --------------------------------------------------------------------------- attribution


def _turns(events: list) -> list:
    """Split a thread into turns: ``[{start, end, events, duration_known}]``.

    A turn is the events between consecutive ``system/turn_duration`` markers:
    it starts at the event that began it (see ``_starter_index`` — bookkeeping
    written while idle, such as queue operations or PR links, comes earlier and
    is idle time, not turn time) and ends at the marker, so turns never overlap.

    The marker's ``durationMs`` is NOT a per-turn wall time. Across the 150
    marked turns of this project's finished sessions (measured 2026-09-26) it is
    shorter than the span in 13 — it excludes time an ``AskUserQuestion`` waited
    on the user, which here stays in active time as ``user`` — and far longer in
    11, up to 12.4x (best-fitting inference: measured from a request that began
    many turns earlier). So it is kept only as ``reported_s``, a cross-check.

    Events after the last marker form a trailing turn (in-flight or cut off),
    started the same way — at its starting event — and ending at its last event.
    """
    turns, bucket = [], []
    for e in events:
        if e.get("type") == "system" and e.get("subtype") == "turn_duration":
            if bucket:
                i = _starter_index(bucket) or 0
                turns.append({"start": bucket[i]["_t"], "end": e["_t"], "events": bucket[i:],
                              "reported_s": _seconds(e.get("durationMs"))})
            bucket = []
        else:
            bucket.append(e)
    if bucket:
        i = _starter_index(bucket) or 0
        turns.append({"start": bucket[i]["_t"], "end": bucket[-1]["_t"], "events": bucket[i:],
                      "reported_s": None})
    return turns


def _seconds(ms) -> float:
    """``durationMs`` as seconds; a non-numeric value reads as 0 (it is only a cross-check)."""
    try:
        return float(ms or 0) / 1000.0
    except (TypeError, ValueError):
        return 0.0


def _starter_index(events) -> "int | None":
    """Index of the event that began a turn: the first user event carrying an
    ``origin`` (human prompt, task-notification, subagent hand-back — the latter
    is ``isMeta``), else the first non-tool-result user message."""
    fallback = None
    for i, e in enumerate(events):
        if e.get("type") != "user" or any(True for _ in _tool_results(e)):
            continue
        if _origin_kind(e):
            return i
        if fallback is None and not e.get("isMeta"):
            fallback = i
    return fallback


def _turn_starter(turn) -> "str | None":
    """How the turn began: the origin kind of its starting event."""
    i = _starter_index(turn["events"])
    if i is None:
        return None
    return _origin_kind(turn["events"][i]) or "unknown"


def attribute(events: list, include_idle: bool = True) -> dict:
    """Attribute a thread's timeline to categories.

    Returns ``segments`` (``[start, end, category]`` — in-turn categories plus,
    when ``include_idle``, the between-turn waits) and ``spans`` (one per tool
    call: ``{key, name, start, end, dur, tool_use_id, message_id, input}``).
    """
    segments, spans = [], []
    open_calls: dict = {}   # tool_use_id -> (start, name, key, message_id, input)
    seen_blocks: set = set()
    turns = _turns(events)
    prev_turn = None
    for turn in turns:
        if include_idle and prev_turn is not None and turn["start"] > prev_turn["end"]:
            starter = _turn_starter(turn)
            if starter == "human":
                kind = "user-idle"
            elif starter in ("task-notification", "peer"):
                kind = "background-wait"
            elif prev_turn.get("armed_wakeup"):
                kind = "scheduled-wait"
            else:
                kind = "idle-other"
            segments.append([prev_turn["end"], turn["start"], kind])
        cursor = turn["start"]
        for e in turn["events"] + [None]:
            t = turn["end"] if e is None else min(max(e["_t"], turn["start"]), turn["end"])
            if t > cursor:
                if open_calls:
                    first = min(open_calls.values(), key=lambda c: c[0])
                    cat = "user" if first[1] == "AskUserQuestion" else "tool:" + first[1]
                elif e is not None and e.get("type") == "system":
                    cat = "harness"   # hooks and other harness work
                else:
                    # No tool open: the model is generating. Bookkeeping lines
                    # (queue operations, attachments) can land mid-generation.
                    cat = "model"
                segments.append([cursor, t, cat])
                cursor = t
            if e is None:
                break
            for b in _tool_uses(e):
                if b["id"] in seen_blocks:
                    continue
                seen_blocks.add(b["id"])
                name = b.get("name", "?")
                if name == "ScheduleWakeup":
                    turn["armed_wakeup"] = True
                inp = b.get("input") or {}
                open_calls[b["id"]] = (e["_t"], name, _span_key(name, inp),
                                       (e.get("message") or {}).get("id"), inp)
            for b in _tool_results(e):
                call = open_calls.pop(b["tool_use_id"], None)
                if call is None:
                    continue
                start, name, key, mid, inp = call
                span = {"key": key, "name": name, "start": start, "end": e["_t"],
                        "dur": max(0.0, e["_t"] - start), "tool_use_id": b["tool_use_id"],
                        "message_id": mid, "input": inp}
                if name in ("Agent", "Task"):
                    # The launch/hand-back text names the sidecar's agent id; a
                    # foreground report appends it after the report, so take the
                    # LAST match over the whole text (a quoted id comes earlier).
                    ids = _AGENT_ID_RE.findall(_result_text(b))
                    span["agent_id"] = ids[-1] if ids else None
                spans.append(span)
        # Calls still open at turn end (interrupted / backgrounded) close there.
        for tid, (start, name, key, mid, inp) in list(open_calls.items()):
            spans.append({"key": key, "name": name, "start": start, "end": turn["end"],
                          "dur": max(0.0, turn["end"] - start), "tool_use_id": tid,
                          "message_id": mid, "input": inp, "unclosed": True})
        open_calls.clear()
        prev_turn = turn
    reported = [t for t in turns if t["reported_s"] is not None]
    return {"segments": segments, "spans": spans, "turns": len(turns),
            "active_s": sum(t["end"] - t["start"] for t in turns),
            "reported_active_s": sum(t["reported_s"] for t in reported),
            "reported_disagreements": sum(
                1 for t in reported if abs(t["reported_s"] - (t["end"] - t["start"])) > 2.0)}


def _clip(segments, lo, hi) -> dict:
    out: dict = {}
    for s, e, cat in segments:
        a, b = max(s, lo), min(e, hi)
        if b > a:
            out[cat] = out.get(cat, 0.0) + (b - a)
    return out


# --------------------------------------------------------------------------- subagents


def parse_description(desc: str) -> dict:
    """Map an Agent description onto the closed gate/role/round vocabulary.

    Anything the vocabulary cannot read keeps ``role``/``gate`` = ``unknown``;
    it is reported, never dropped.
    """
    d = (desc or "").lower()
    # Only the explicit role word: "re-check"/"recheck" also appear in slugs and
    # diff names ("Verify balanced-rechecks-folds completion").
    if "fold-audit" in d or "fold audit" in d:
        role = "fold-audit"
    elif "proponent" in d:
        role = "proponent"
    elif "arbiter" in d:
        role = "arbiter"
    elif "skeptic" in d:
        role = "skeptic"
    elif "verifier" in d or re.search(r"\bverif(y|ication)\b", d):
        role = "verifier"
    elif "review" in d or "audit" in d:
        role = "code-review"
    else:
        role = "unknown"

    gate = "unknown"
    for name, pats in (
        ("whole-proposal", ("whole-proposal", "whole proposal", "soundness")),
        ("scope", ("scope",)),
        ("approach", ("approach",)),
        ("completion", ("completion", "criteria")),
        ("divergence", ("divergence",)),
        ("replan", ("replan", "new-plan", "new plan")),
        ("triage", ("triage",)),
        ("partition", ("partition",)),
        ("todo", ("todo",)),
    ):
        if any(p in d for p in pats):
            gate = name
            break
    if gate == "unknown" and role == "verifier":
        gate = "completion"
    if gate == "unknown" and role == "code-review":
        gate = "review"
    rnd = 2 if re.search(r"\br2\b|round 2|revision round", d) else 1
    return {"role": role, "gate": gate, "round": rnd, "says_panel": "panel" in d}


def _notification_durations(events) -> dict:
    """``{tool_use_id: duration_s}`` from every ``<task-notification>`` block."""
    out = {}
    for e in events:
        if e.get("type") not in ("user", "queue-operation"):
            continue
        for block in _NOTIFICATION_RE.findall(_text_of(e)):
            tid = _TOOL_USE_ID_RE.search(block)
            dur = _DURATION_RE.search(block)
            if tid and dur and tid.group(1) not in out:
                out[tid.group(1)] = int(dur.group(1)) / 1000.0
    return out


def load_subagents(main_path, main_events, agent_spans) -> list:
    """One record per sidecar subagent file, linked to its Agent call."""
    main_path = Path(main_path)
    sub_dir = main_path.parent / main_path.stem / "subagents"
    by_tool_use = {s["tool_use_id"]: s for s in agent_spans}
    # Without a meta file, the Agent call's result text still names the agent id
    # ("agentId: a764eb…"), which is the sidecar's file name.
    by_agent_id = {}
    for s in agent_spans:
        if s.get("agent_id"):
            by_agent_id.setdefault(s["agent_id"], s["tool_use_id"])
    notif = _notification_durations(main_events)
    out = []
    for f in sorted(sub_dir.glob("agent-*.jsonl")):
        meta_path = f.with_name(f.stem + ".meta.json")
        try:
            meta = json.loads(meta_path.read_text())
        except (OSError, json.JSONDecodeError):
            meta = {}
        if not isinstance(meta, dict):
            meta = {}
        events = load_events(f)
        if not events:
            continue
        att = attribute(events, include_idle=False)
        first, last = events[0]["_t"], events[-1]["_t"]
        tid = meta.get("toolUseId") or by_agent_id.get(f.stem[len("agent-"):])
        launch = by_tool_use.get(tid)
        desc = meta.get("description") or (launch or {}).get("input", {}).get("description", "")
        out_tokens, seen = 0, set()
        for e in events:
            if e.get("type") != "assistant":
                continue
            msg = e.get("message") or {}
            if msg.get("id") in seen:
                continue
            seen.add(msg.get("id"))
            out_tokens += (msg.get("usage") or {}).get("output_tokens", 0) or 0
        file_span = max(0.0, last - first)
        dur = notif.get(tid, file_span)
        start = launch["start"] if launch else first
        out.append({
            "file": f.name,
            "tool_use_id": tid,
            "description": desc,
            "model": meta.get("model") or "inherit",
            "start": start,
            "end": start + dur,
            "dur": dur,
            "dur_source": "notification" if tid in notif else "file-span",
            "file_span": file_span,
            "launch_message_id": (launch or {}).get("message_id"),
            "output_tokens": out_tokens,
            "tool_calls": len(att["spans"]),
            "breakdown": _clip(att["segments"], first, last),
            **parse_description(desc),
        })
    _assign_tiers(out)
    return out


def _assign_tiers(subs) -> None:
    """Panel vs reviewer, by launch batch — never by keyword alone.

    Proponent and Arbiter only exist inside panels; a description saying
    "panel" is a panel. A Skeptic is a panel member when a same-gate, same-round
    Proponent was dispatched in the same assistant message or within
    ``PANEL_BATCH_WINDOW_S`` — real panels often omit the word ("Whole-proposal:
    Proponent" + "Whole-proposal: Skeptic"), while a lone reviewer Skeptic at the
    same gate must not be swept into a later escalation panel.
    """
    for s in subs:
        if s["role"] in ("proponent", "arbiter") or s["says_panel"]:
            s["tier"] = "panel"
        elif s["role"] == "skeptic":
            batch = any(
                p["role"] == "proponent" and p["gate"] == s["gate"] and p["round"] == s["round"]
                and (
                    (s["launch_message_id"] and p["launch_message_id"] == s["launch_message_id"])
                    or abs(p["start"] - s["start"]) <= PANEL_BATCH_WINDOW_S
                )
                for p in subs
            )
            s["tier"] = "panel" if batch else "reviewer"
        elif s["role"] in ("verifier", "fold-audit"):
            s["tier"] = "reviewer"
        elif s["role"] == "code-review":
            s["tier"] = "code-review"  # not "review": too close to "reviewer" in one column
        else:
            s["tier"] = "unknown"


def _union(intervals) -> float:
    total, cur_s, cur_e = 0.0, None, None
    for s, e in sorted(intervals):
        if cur_e is None or s > cur_e:
            if cur_e is not None:
                total += cur_e - cur_s
            cur_s, cur_e = s, e
        else:
            cur_e = max(cur_e, e)
    if cur_e is not None:
        total += cur_e - cur_s
    return total


# --------------------------------------------------------------------------- runs + phases


def _invocations(events) -> list:
    """Orchestrator invocations: ``[{t, caller, cleanup_only, via}]``."""
    out = []
    for e in events:
        if e.get("type") == "user" and not any(True for _ in _tool_results(e)):
            text = _text_of(e)
            m = _COMMAND_NAME_RE.search(text)
            if m and m.group(1) in ORCHESTRATORS:
                args = _COMMAND_ARGS_RE.search(text)
                out.append({"t": e["_t"], "caller": m.group(1), "via": "command",
                            "cleanup_only": "--cleanup-only" in (args.group(1) if args else "")})
        for b in _tool_uses(e):
            if b.get("name") == "Skill" and (b.get("input") or {}).get("skill") in ORCHESTRATORS:
                args = str((b.get("input") or {}).get("args", ""))
                out.append({"t": e["_t"], "caller": b["input"]["skill"], "via": "skill",
                            "cleanup_only": "--cleanup-only" in args})
    return sorted(out, key=lambda i: i["t"])


def segment_runs(events) -> list:
    """Split a session into runs, one per orchestrator invocation.

    A run is bounded by the next invocation or the end of the file. A
    ``--cleanup-only`` re-entry extends the run it resumes; two invocations within
    ``SAME_RUN_WINDOW_S`` are one run.
    """
    if not events:
        return []
    runs = []
    for inv in _invocations(events):
        if runs and (inv["cleanup_only"] or inv["t"] - runs[-1]["last_invocation"] <= SAME_RUN_WINDOW_S):
            runs[-1]["last_invocation"] = inv["t"]
            if inv["cleanup_only"]:
                runs[-1]["resumes"] += 1
            continue
        runs.append({"start": inv["t"], "caller": inv["caller"], "via": inv["via"],
                     "last_invocation": inv["t"], "resumes": 0})
    end_of_file = events[-1]["_t"]
    for i, r in enumerate(runs):
        r["end"] = runs[i + 1]["start"] if i + 1 < len(runs) else end_of_file
    return runs


_HEREDOC_RE = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1[^\n]*\n(.*?)\n\s*\2\s*(?:\n|$)", re.S)
_QUOTED_RE = re.compile(r"'[^'\n]*'|\"[^\"\n]*\"")
_PY_KNOWLEDGE_WRITE_RE = re.compile(
    r"\.minerva/knowledge/[^\"'\s]+\.md[\"']\s*\)?\s*\.write_text"
    r"|open\(\s*[\"'][^\"']*\.minerva/knowledge/[^\"']+\.md[\"']\s*,\s*[\"'][wa]")
# index.md / overview.md are the catalog and synthesis — reconciliation, not promote.
_NOT_AN_ENTRY = ("index.md", "overview.md")


def _writes_knowledge(command: str) -> bool:
    """Does this Bash command write a knowledge ENTRY (``.minerva/knowledge/*.md``)?

    Structural, not a substring search: heredoc bodies and quoted strings are
    set aside before looking for write targets (a proposal heredoc that merely
    mentions the path is not a write), ``$VAR`` targets are expanded from
    assignments in the same command (``K=.minerva/knowledge; cat > $K/x.md``),
    a ``cd`` into the directory is honoured, and a Python heredoc that
    ``write_text``s / ``open(..., "w")``s an entry counts.
    """
    if not isinstance(command, str) or ".minerva/knowledge" not in command:
        return False
    bodies = [m.group(3) for m in _HEREDOC_RE.finditer(command)]
    if any(_PY_KNOWLEDGE_WRITE_RE.search(b) for b in bodies):
        return True
    shell = _QUOTED_RE.sub("Q", _HEREDOC_RE.sub(" ", command))
    env = dict(re.findall(r"(?:^|[\s;&])([A-Za-z_][A-Za-z0-9_]*)=([^\s;&]+)", shell))
    cwd = ""
    for seg in re.split(r"&&|\|\||;|\n|\|", shell):
        seg = re.sub(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?", lambda m: env.get(m.group(1), m.group(0)), seg).strip()
        toks = seg.split()
        if not toks:
            continue
        if toks[0] == "cd" and len(toks) > 1:
            cwd = toks[1]
            continue
        targets = re.findall(r"(?<![0-9&])>>?\s*([^\s<>]+)", seg)
        if toks[0] == "tee":
            targets += [t for t in toks[1:] if not t.startswith("-")]
        if toks[0] in ("cp", "mv") and len(toks) >= 3:
            targets.append(toks[-1])
        if toks[:2] == ["git", "mv"] and len(toks) >= 4:
            targets.append(toks[-1])
        for t in targets:
            full = t if "/" in t or not cwd else f"{cwd}/{t}"
            if ".minerva/knowledge/" in full + "/" and full.endswith(".md") and Path(full).name not in _NOT_AN_ENTRY:
                return True
    return False


def _phase_signals(events, spans, lo, hi) -> list:
    """Candidate ``(t, phase, description)`` boundary signals inside ``[lo, hi)``."""
    sig = []
    for s in spans:
        if not (lo <= s["start"] < hi):
            continue
        inp = s["input"] or {}
        if s["name"] == "Bash" and "git worktree add" in str(inp.get("command", "")):
            sig.append((s["start"], "work", "Bash: git worktree add"))
        elif s["name"] in ("Write", "Edit") and ".minerva/knowledge/" in str(inp.get("file_path", "")):
            sig.append((s["start"], "promote", f"{s['name']} {Path(inp['file_path']).name}"))
        elif s["name"] == "Bash" and _writes_knowledge(str(inp.get("command", ""))):
            sig.append((s["start"], "promote", "Bash: write under .minerva/knowledge/"))
        elif s["name"] in ("Write", "Edit") and str(inp.get("file_path", "")).endswith("replan.md"):
            sig.append((s["start"], "replan", f"{s['name']} replan.md"))
        elif s["name"] == "Skill":
            skill = inp.get("skill")
            if skill == "minerva:ship":
                sig.append((s["start"], "ship", "Skill minerva:ship"))
            elif skill == "minerva:cleanup":
                sig.append((s["start"], "cleanup", "Skill minerva:cleanup"))
            elif skill == "minerva:replan":
                sig.append((s["start"], "replan", "Skill minerva:replan"))
            elif skill == "minerva:promote":
                sig.append((s["start"], "promote", "Skill minerva:promote"))
    # Agent calls in the main thread — present even when a sidecar file is not.
    for s in spans:
        if s["name"] not in ("Agent", "Task") or not (lo <= s["start"] < hi):
            continue
        desc = str((s["input"] or {}).get("description", ""))
        parsed = parse_description(desc)
        if parsed["gate"] == "completion":
            sig.append((s["start"], "verify", f"Agent: {desc}"))
        elif parsed["role"] == "code-review":
            sig.append((s["start"], "review", f"Agent: {desc}"))
    return sorted(sig)


def infer_phases(events, spans, lo, hi) -> dict:
    """Ordered phase windows inside a run, with auditable boundaries."""
    order = {p: i for i, p in enumerate(PHASES)}
    boundaries = [{"phase": "propose", "t": lo, "event": "orchestrator invocation"}]
    warnings, replans, captures = [], [], []
    signals = _phase_signals(events, spans, lo, hi)
    # A knowledge write BEFORE a later verify/review signal is a mid-work capture
    # (minerva:promote's capture mode), not the start of the promote phase.
    # Only checks before the first ship/cleanup count — a post-ship CI-fix review
    # must not turn the real promote writes into "captures".
    shipped = min((t for t, p, _ in signals if p in ("ship", "cleanup")), default=float("inf"))
    last_check = max((t for t, p, _ in signals if p in ("verify", "review") and t < shipped), default=None)
    for t, phase, desc in signals:
        if phase == "replan":
            replans.append({"t": t, "event": desc})
            continue
        if phase == "promote" and last_check is not None and t < last_check:
            captures.append({"t": t, "event": desc})
            continue
        cur = boundaries[-1]["phase"]
        if phase == cur:
            continue
        if order[phase] < order[cur]:
            warnings.append(f"out-of-order signal ignored: {phase} ({desc}) during {cur}")
            continue
        boundaries.append({"phase": phase, "t": t, "event": desc})
    seen = {b["phase"] for b in boundaries}
    for p in PHASES:
        if p not in seen:
            warnings.append(f"no signal for phase '{p}' — its time stays in the preceding phase")
    windows = []
    for i, b in enumerate(boundaries):
        end = boundaries[i + 1]["t"] if i + 1 < len(boundaries) else hi
        windows.append({**b, "end": end})
    return {"windows": windows, "warnings": warnings, "replans": replans, "captures": captures}


# --------------------------------------------------------------------------- report


def _end_after_cleanup(events, phases, hi) -> float:
    """A run is over once cleanup has begun and a human asks for something else.

    The first human prompt after the cleanup boundary ends the run (a
    ``--cleanup-only`` re-entry is an invocation, not a new request, and does
    not); without it, unrelated follow-on work in the same session would be
    charged to the run's cleanup phase.
    """
    cleanup = next((w["t"] for w in phases["windows"] if w["phase"] == "cleanup"), None)
    if cleanup is None:
        return hi
    for e in events:
        if not (cleanup < e["_t"] < hi) or e.get("type") != "user" or _origin_kind(e) != "human":
            continue
        if any(True for _ in _tool_results(e)):
            continue
        m = _COMMAND_NAME_RE.search(_text_of(e))
        if m and m.group(1) in ORCHESTRATORS:
            continue
        return e["_t"]
    return hi


def resolve_session(arg: str, project_dir=None) -> Path:
    p = Path(arg).expanduser()
    if p.suffix == ".jsonl" and p.exists():
        return p
    base = Path(project_dir).expanduser() if project_dir else default_project_dir()
    cand = base / f"{arg}.jsonl"
    if cand.exists():
        return cand
    raise FileNotFoundError(f"no transcript for {arg!r} (looked in {base})")


def default_project_dir(cwd=None) -> Path:
    """Claude Code's transcript directory for this project.

    Anchored to the PRIMARY checkout: sessions run from the repo root, so from
    inside a linked worktree (``.minerva/worktrees/…``) the cwd would encode to a
    directory that does not exist (2026-08-28 worktree-reaching-paths constraint).
    """
    cwd = Path(cwd or Path.cwd()).resolve()
    try:
        out = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-dir", "--git-common-dir"],
                             cwd=cwd, capture_output=True, text=True, check=True).stdout.split("\n")
        git_dir, common = out[0].strip(), out[1].strip()
        # Only a LINKED worktree has git-dir != common-dir (…/.git/worktrees/<name>).
        # A submodule or a plain subdirectory keeps its own launch directory.
        if git_dir and common and Path(git_dir) != Path(common) and Path(git_dir).parent.name == "worktrees":
            cwd = Path(common).parent
    except (OSError, subprocess.CalledProcessError, IndexError):
        pass
    return Path.home() / ".claude" / "projects" / re.sub(r"[^A-Za-z0-9]", "-", str(cwd))


def trace_session(path) -> dict:
    """The full trace of one session: runs, phases, subagents, spans."""
    path = Path(path)
    events = [e for e in load_events(path) if not e.get("isSidechain")]
    att = attribute(events)
    agent_spans = [s for s in att["spans"] if s["name"] in ("Agent", "Task")]
    subs = load_subagents(path, events, agent_spans)
    runs = []
    for i, r in enumerate(segment_runs(events)):
        lo, hi = r["start"], r["end"]
        phases = infer_phases(events, att["spans"], lo, hi)
        hi = _end_after_cleanup(events, phases, hi)
        if hi != r["end"]:
            phases = infer_phases(events, att["spans"], lo, hi)
        run_subs = [s for s in subs if lo <= s["start"] < hi]
        run_spans = [s for s in att["spans"] if lo <= s["start"] < hi]
        for w in phases["windows"]:
            w["time"] = _round(_clip(att["segments"], w["t"], w["end"]))
            ws = [s for s in run_subs if w["t"] <= s["start"] < w["end"]]
            w["subagent_sum_s"] = round(sum(s["dur"] for s in ws), 3)
            w["subagent_union_s"] = round(_union([(s["start"], s["end"]) for s in ws]), 3)
        runs.append({
            "index": i,
            "caller": r["caller"],
            "resumes": r["resumes"],
            "start": _iso(lo),
            "end": _iso(hi),
            "summary": _summary(att["segments"], run_subs, lo, hi),
            "bash_heads": _round(_bash_heads(run_spans)),
            "phases": phases["windows"],
            "phase_warnings": phases["warnings"],
            "replans": phases["replans"],
            "knowledge_captures": phases["captures"],
            "gates": _gate_table(run_subs),
            "unknown_subagents": [s["description"] for s in run_subs if s["role"] == "unknown" or s["gate"] == "unknown"],
            "slowest": _slowest(run_spans, run_subs),
        })
    whole = _summary(att["segments"], subs, events[0]["_t"], events[-1]["_t"]) if events else {}
    return {
        "session": path.stem,
        "path": str(path),
        "turns": att["turns"],
        "reported_duration_crosscheck": _round({
            "sum_duration_ms_s": att["reported_active_s"],
            "sum_turn_spans_s": att["active_s"],
            "turns_disagreeing_over_2s": att["reported_disagreements"],
        }),
        "summary": whole,
        "runs": runs,
        "subagents": [_public_sub(s) for s in subs],
    }


def _summary(segments, subs, lo, hi) -> dict:
    by = _clip(segments, lo, hi)
    in_turn = {k: v for k, v in by.items() if k not in _WAITS}
    tools = sum(v for k, v in in_turn.items() if k.startswith("tool:"))
    return _round({
        "wall_s": max(0.0, hi - lo),
        "active_s": sum(in_turn.values()),
        "model_s": in_turn.get("model", 0.0),
        "tools_s": tools,
        "user_s": in_turn.get("user", 0.0),
        "harness_s": in_turn.get("harness", 0.0),
        "background_wait_s": by.get("background-wait", 0.0),
        "scheduled_wait_s": by.get("scheduled-wait", 0.0),
        "user_idle_s": by.get("user-idle", 0.0),
        "idle_other_s": by.get("idle-other", 0.0),
        "subagent_sum_s": sum(s["dur"] for s in subs),
        "subagent_union_s": _union([(s["start"], s["end"]) for s in subs]),
        "subagents": len(subs),
        "by_tool": {k[5:]: v for k, v in sorted(in_turn.items(), key=lambda kv: -kv[1]) if k.startswith("tool:")},
    })


_WAITS = ("background-wait", "scheduled-wait", "user-idle", "idle-other")


def _bash_heads(spans) -> dict:
    out: dict = {}
    for s in spans:
        if s["name"] == "Bash":
            out[s["key"][5:]] = out.get(s["key"][5:], 0.0) + s["dur"]
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


def _gate_table(subs) -> list:
    rows: dict = {}
    for s in subs:
        k = (s["gate"], s["tier"], s["role"], s["round"])
        r = rows.setdefault(k, {"gate": s["gate"], "tier": s["tier"], "role": s["role"],
                                "round": s["round"], "count": 0, "sum_s": 0.0, "output_tokens": 0})
        r["count"] += 1
        r["sum_s"] += s["dur"]
        r["output_tokens"] += s["output_tokens"]
    for r in rows.values():
        r["sum_s"] = round(r["sum_s"], 3)
    return sorted(rows.values(), key=lambda r: -r["sum_s"])


def _slowest(spans, subs, n=10) -> list:
    items = [{"kind": "tool", "what": s["key"] + _detail(s), "dur_s": s["dur"], "start": _iso(s["start"])}
             for s in spans if s["name"] not in ("Agent", "Task")]
    items += [{"kind": "subagent", "what": f"{s['description']} [{s['tier']}/{s['model']}]",
               "dur_s": s["dur"], "start": _iso(s["start"])} for s in subs]
    items.sort(key=lambda i: -i["dur_s"])
    return [{**i, "dur_s": round(i["dur_s"], 3)} for i in items[:n]]


def _detail(span) -> str:
    inp = span.get("input") or {}
    if span["name"] == "Bash":
        c = " ".join(str(inp.get("command", "")).split())
        return f" — {c[:70]}"
    if span["name"] in ("Read", "Write", "Edit"):
        return f" — {Path(str(inp.get('file_path', ''))).name}"
    return ""


def _public_sub(s) -> dict:
    keep = ("file", "tool_use_id", "description", "model", "dur", "dur_source", "file_span",
            "output_tokens", "tool_calls", "role", "gate", "round", "tier", "breakdown")
    out = {k: s[k] for k in keep}
    out["start"] = _iso(s["start"])
    return _round(out)


def _iso(t) -> str:
    return datetime.fromtimestamp(t).astimezone().isoformat(timespec="seconds")


def _round(obj):
    if isinstance(obj, float):
        return round(obj, 3)
    if isinstance(obj, dict):
        return {k: _round(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round(v) for v in obj]
    return obj


def aggregate(project_dir, callers=("minerva:propose-ship-auto",)) -> dict:
    """Every orchestrator run in a project directory, with totals and medians."""
    rows, phase_vals, wait_vals, gate_vals, skipped = [], {}, {}, {}, []
    for path in sorted(Path(project_dir).expanduser().glob("*.jsonl")):
        try:
            tr = trace_session(path)
        except Exception as exc:  # one unreadable transcript must not sink the report
            skipped.append({"session": path.stem, "error": f"{type(exc).__name__}: {exc}"})
            continue
        for run in tr["runs"]:
            if callers and run["caller"] not in callers:
                continue
            s = run["summary"]
            row = {"session": tr["session"], "run": run["index"], "caller": run["caller"],
                   "start": run["start"], **{k: s[k] for k in (
                       "wall_s", "active_s", "model_s", "tools_s", "user_s",
                       "background_wait_s", "user_idle_s", "subagent_sum_s", "subagent_union_s",
                       "subagents")}}
            # Active time only: waits (background, user idle — including any
            # unrelated conversation after the run finished) are reported apart.
            per_phase, per_wait = {}, {}
            for w in run["phases"]:
                active = sum(v for k, v in w["time"].items() if k not in _WAITS)
                waits = sum(v for k, v in w["time"].items() if k in _WAITS)
                per_phase[w["phase"]] = per_phase.get(w["phase"], 0.0) + active
                per_wait[w["phase"]] = per_wait.get(w["phase"], 0.0) + waits
            for p, v in per_phase.items():
                phase_vals.setdefault(p, []).append(v)
                wait_vals.setdefault(p, []).append(per_wait[p])
            row["phases_active"] = _round(per_phase)
            row["phases_waits"] = _round(per_wait)
            per_gate: dict = {}
            for g in run["gates"]:
                per_gate[(g["gate"], g["tier"])] = per_gate.get((g["gate"], g["tier"]), 0.0) + g["sum_s"]
            for k, v in per_gate.items():
                gate_vals.setdefault(k, []).append(v)
            rows.append(row)

    def stats(vals):
        return _round({"runs": len(vals), "total_s": sum(vals), "median_s": statistics.median(vals)})

    return {
        "project_dir": str(project_dir),
        "callers": list(callers),
        "runs": rows,
        "phases": {p: {**stats(phase_vals[p]), "waits_total_s": round(sum(wait_vals[p]), 3)}
                   for p in PHASES if p in phase_vals},
        "skipped": skipped,
        "gates": [{"gate": g, "tier": t, **stats(v)}
                  for (g, t), v in sorted(gate_vals.items(), key=lambda kv: -sum(kv[1]))],
    }


# --------------------------------------------------------------------------- text output


def _fmt(sec) -> str:
    sec = float(sec or 0)
    if sec >= 3600:
        return f"{sec / 3600:.1f}h"
    if sec >= 60:
        return f"{sec / 60:.1f}m"
    return f"{sec:.0f}s"


def _pct(part, whole) -> str:
    return f"{100 * part / whole:4.0f}%" if whole else "   -"


def render_session(tr) -> str:
    x = tr["reported_duration_crosscheck"]
    lines = [f"session {tr['session']} — {tr['turns']} turns, {len(tr['runs'])} orchestrator run(s)",
             f"  cross-check: turn spans {_fmt(x['sum_turn_spans_s'])} vs Claude's durationMs sum "
             f"{_fmt(x['sum_duration_ms_s'])} ({x['turns_disagreeing_over_2s']} turn(s) differ >2s; "
             "durationMs excludes question waits and can reach back across turns)"]
    if not tr["runs"]:
        lines.append("  (no orchestrator invocation found — whole-session summary only)")
        lines += _render_summary(tr["summary"])
    for run in tr["runs"]:
        lines.append("")
        lines.append(f"== run {run['index']} · {run['caller']} · {run['start']} → {run['end']}"
                     + (f" · {run['resumes']} resume(s)" if run["resumes"] else ""))
        lines += _render_summary(run["summary"])
        lines.append("")
        lines.append("  phase     start                      active   waits    subagents(sum/union)  set by")
        for w in run["phases"]:
            active = sum(v for k, v in w["time"].items() if k not in _WAITS)
            waits = sum(v for k, v in w["time"].items() if k in _WAITS)
            lines.append(f"  {w['phase']:<9} {w['t'] and _iso(w['t']):<26} {_fmt(active):>6}  {_fmt(waits):>6}"
                         f"   {_fmt(w['subagent_sum_s']):>6} / {_fmt(w['subagent_union_s']):<6}      {w['event']}")
        for msg in run["phase_warnings"]:
            lines.append(f"  ! {msg}")
        for rp in run["replans"]:
            lines.append(f"  ~ replan event: {rp['event']}")
        for cp in run["knowledge_captures"]:
            lines.append(f"  ~ mid-work knowledge capture: {cp['event']}")
        if run["gates"]:
            lines.append("")
            lines.append("  gate            tier         role         rnd  n   subagent time  out tokens")
            for g in run["gates"]:
                lines.append(f"  {g['gate']:<15} {g['tier']:<12} {g['role']:<12} {g['round']:>3}  {g['count']:<3} "
                             f"{_fmt(g['sum_s']):>12}  {g['output_tokens']:>10}")
        if run["unknown_subagents"]:
            lines.append("  unrecognised subagent descriptions: " + "; ".join(run["unknown_subagents"]))
        if run["bash_heads"]:
            lines.append("")
            lines.append("  bash by command head: " + ", ".join(
                f"{k} {_fmt(v)}" for k, v in list(run["bash_heads"].items())[:8]))
        lines.append("")
        lines.append("  slowest spans:")
        for s in run["slowest"]:
            lines.append(f"    {_fmt(s['dur_s']):>6}  {s['kind']:<8} {s['what']}")
    return "\n".join(lines)


def _render_summary(s) -> list:
    if not s:
        return []
    a = s["active_s"]
    out = [
        f"  wall {_fmt(s['wall_s'])} = active {_fmt(a)} + between-turn waits "
        f"(background {_fmt(s['background_wait_s'])}, scheduled {_fmt(s['scheduled_wait_s'])}, "
        f"user idle {_fmt(s['user_idle_s'])}, other {_fmt(s['idle_other_s'])})",
        f"  active: model {_fmt(s['model_s'])} {_pct(s['model_s'], a)} · tools {_fmt(s['tools_s'])} "
        f"{_pct(s['tools_s'], a)} · user {_fmt(s['user_s'])} {_pct(s['user_s'], a)} · harness "
        f"{_fmt(s['harness_s'])}",
        f"  subagents (overlapping view — do not add): {s['subagents']} ran, "
        f"sum {_fmt(s['subagent_sum_s'])}, wall-clock union {_fmt(s['subagent_union_s'])}",
    ]
    if s.get("by_tool"):
        out.append("  tools: " + ", ".join(f"{k} {_fmt(v)}" for k, v in list(s["by_tool"].items())[:8]))
    return out


def render_aggregate(agg) -> str:
    lines = [f"{len(agg['runs'])} run(s) of {', '.join(agg['callers']) or 'any orchestrator'} in {agg['project_dir']}", ""]
    lines.append("  session   run  start                      wall    active  model   tools   user    bg-wait  subagents(sum/union)")
    for r in agg["runs"]:
        lines.append(f"  {r['session'][:8]}  {r['run']:>3}  {r['start']:<26} {_fmt(r['wall_s']):>6}  {_fmt(r['active_s']):>6}  "
                     f"{_fmt(r['model_s']):>6}  {_fmt(r['tools_s']):>6}  {_fmt(r['user_s']):>6}  "
                     f"{_fmt(r['background_wait_s']):>6}   {_fmt(r['subagent_sum_s'])} / {_fmt(r['subagent_union_s'])}")
    lines.append("")
    lines.append("  phase     runs  active total  median/run  (waits total)")
    for p, st in agg["phases"].items():
        lines.append(f"  {p:<9} {st['runs']:>4}  {_fmt(st['total_s']):>12}  {_fmt(st['median_s']):>10}"
                     f"  ({_fmt(st['waits_total_s'])})")
    for sk in agg["skipped"]:
        lines.append(f"  ! skipped {sk['session']}: {sk['error']}")
    lines.append("")
    lines.append("  gate            tier         runs  subagent total  median/run")
    for g in agg["gates"]:
        lines.append(f"  {g['gate']:<15} {g['tier']:<12} {g['runs']:>4}  {_fmt(g['total_s']):>14}  {_fmt(g['median_s']):>10}")
    return "\n".join(lines)


def main(argv=None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    as_json = "--json" in argv
    all_runs = "--all" in argv
    project_dir = None
    callers = ("minerva:propose-ship-auto",)
    rest = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in ("--json", "--all"):
            pass
        elif a == "--project-dir":
            if i + 1 >= len(argv) or argv[i + 1].startswith("--"):
                print("--project-dir needs a directory", file=sys.stderr)
                return 2
            project_dir = argv[i + 1]
            i += 1
        elif a == "--any-orchestrator":
            callers = ORCHESTRATORS
        else:
            rest.append(a)
        i += 1
    if all_runs:
        directory = Path(project_dir).expanduser() if project_dir else default_project_dir()
        if not directory.is_dir():
            print(f"no transcript directory at {directory} (pass --project-dir)", file=sys.stderr)
            return 2
        agg = aggregate(directory, callers)
        print(json.dumps(agg, indent=2) if as_json else render_aggregate(agg))
        return 0
    if len(rest) != 1:
        print("usage: run_trace.py <session.jsonl | session-id> [--json] [--project-dir DIR]\n"
              "       run_trace.py --all [--any-orchestrator] [--json] [--project-dir DIR]",
              file=sys.stderr)
        return 2
    try:
        path = resolve_session(rest[0], project_dir)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    tr = trace_session(path)
    print(json.dumps(tr, indent=2) if as_json else render_session(tr))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
