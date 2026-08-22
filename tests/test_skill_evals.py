"""Deterministic unit tests for the behavioral skill-value runner.

The runner's only non-deterministic layer is ``invoke``/``judge`` (which shell
out to ``claude -p`` in production). Every test here injects STUBS, so the suite
runs with zero API and is fully deterministic. ``--dry-run`` is also exercised
(it must never call invoke/judge at all).

``scripts/`` is on sys.path via the repo conftest.py.
"""
import json

import pytest

import run_skill_evals as rse


# --------------------------------------------------------------------------- #
# Stubs — stand in for `claude -p`
# --------------------------------------------------------------------------- #
def stub_invoke(prompt, skill_available, skill):
    # Treatment transcript is richer than control; judge (below) rewards length.
    return "GOOD STRUCTURED ANSWER " * 3 if skill_available else "ok"


def stub_judge(prompt, transcript, rubric):
    # Deterministic: score = min(rubric_max, words//2).
    score = min(len(rubric), len(transcript.split()) // 2)
    return {"score": score, "notes": "stub"}


def exploding_invoke(*a, **k):  # must never be called in --dry-run
    raise AssertionError("invoke called during dry-run / pure layer")


def exploding_judge(*a, **k):
    raise AssertionError("judge called during dry-run / pure layer")


# --------------------------------------------------------------------------- #
# Layer 1 — parse
# --------------------------------------------------------------------------- #
def test_load_cases_exemplars_parse():
    for skill in ("debug", "propose"):
        cases = rse.load_cases(skill)
        assert cases, f"{skill} has no cases"
        for c in cases:
            assert c.id and c.prompt and isinstance(c.rubric, list) and c.rubric


def test_discover_skills_includes_exemplars():
    skills = rse.discover_skills()
    assert "debug" in skills and "propose" in skills


def test_load_cases_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        rse.load_cases("nope", evals_dir=tmp_path)


@pytest.mark.parametrize("load_as, doc", [
    # skill field mismatches the directory/loaded name
    ("x", {"skill": "y", "cases": [{"id": "a", "prompt": "p", "rubric": ["r"]}]}),
    ("x", {"skill": "x", "cases": []}),
    ("x", {"skill": "x", "cases": [{"prompt": "p", "rubric": ["r"]}]}),
    ("x", {"skill": "x", "cases": [{"id": "a", "rubric": ["r"]}]}),
    ("x", {"skill": "x", "cases": [{"id": "a", "prompt": "p", "rubric": []}]}),
    ("x", {"skill": "x", "cases": [{"id": "a", "prompt": "p", "rubric": ["r"]},
                                    {"id": "a", "prompt": "q", "rubric": ["r"]}]}),
])
def test_load_cases_rejects_malformed(tmp_path, load_as, doc):
    skill_dir = tmp_path / load_as
    skill_dir.mkdir()
    (skill_dir / "behavioral.json").write_text(json.dumps(doc))
    with pytest.raises(ValueError):
        rse.load_cases(load_as, evals_dir=tmp_path)


# --------------------------------------------------------------------------- #
# Layer 2 — plan (control always present)
# --------------------------------------------------------------------------- #
def test_build_plan_has_treatment_control_judge():
    case = rse.Case(id="c", prompt="p", rubric=["r1", "r2"])
    plan = rse.build_plan(case)
    arms = [s.arm for s in plan.steps]
    assert arms == ["treatment", "control", "judge"]
    # The control arm must be present and marked skill-unavailable — never dropped.
    control = [s for s in plan.steps if s.arm == "control"]
    assert len(control) == 1 and control[0].skill_available is False


# --------------------------------------------------------------------------- #
# Layer 4 — score (stubbed)
# --------------------------------------------------------------------------- #
def test_score_case_computes_delta_from_stubs():
    case = rse.Case(id="c", prompt="p", rubric=["a", "b", "c", "d"])
    r = rse.score_case(case, stub_invoke, stub_judge)
    assert r["treatment_score"] > r["control_score"]
    assert r["delta"] == r["treatment_score"] - r["control_score"]


def test_run_skill_with_stubs_computes_mean_delta():
    report = rse.run_skill("debug", invoke=stub_invoke, judge=stub_judge)
    assert report["skill"] == "debug"
    assert report["provisional"] is True
    assert report["summary"]["n_cases"] == len(report["cases"])
    assert report["summary"]["mean_delta"] > 0  # stub rewards the treatment arm


# --------------------------------------------------------------------------- #
# Layer 5 — report
# --------------------------------------------------------------------------- #
def test_render_markdown_flags_provisional():
    report = rse.run_skill("propose", invoke=stub_invoke, judge=stub_judge)
    md = rse.render_markdown(report)
    assert "PROVISIONAL" in md
    assert "delta" in md.lower()
    assert report["cases"][0]["id"] in md


# --------------------------------------------------------------------------- #
# --dry-run — pure, zero API (invoke/judge must NOT be called)
# --------------------------------------------------------------------------- #
def test_dry_run_does_not_invoke(monkeypatch, capsys):
    monkeypatch.setattr(rse, "claude_invoke", exploding_invoke)
    monkeypatch.setattr(rse, "claude_judge", exploding_judge)
    rc = rse.main(["--dry-run", "--skill", "debug"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out[0]["skill"] == "debug" and out[0]["dry_run"] is True
    # Every case's plan must include the control arm.
    for case in out[0]["cases"]:
        arms = [s["arm"] for s in case["steps"]]
        assert "treatment" in arms and "control" in arms and "judge" in arms


def test_dry_run_all_skills(monkeypatch, capsys):
    monkeypatch.setattr(rse, "claude_invoke", exploding_invoke)
    monkeypatch.setattr(rse, "claude_judge", exploding_judge)
    rc = rse.main(["--dry-run"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    skills = {entry["skill"] for entry in out}
    assert {"debug", "propose"} <= skills


# --- The control arm actually suppresses (issue #74) ------------------------------
#
# The previous control ran the identical command for both arms, so `treatment - control`
# compared a configuration against itself and every delta was run-to-run noise. These
# tests pin the property that makes a delta mean anything: the two arms differ in exactly
# one skill directory, and nothing else.

def test_control_arm_dir_is_missing_exactly_the_one_skill(tmp_path, monkeypatch):
    import run_skill_evals as r
    plugin = tmp_path / "minerva"
    (plugin / "skills" / "debug").mkdir(parents=True)
    (plugin / "skills" / "debug" / "SKILL.md").write_text("---\nname: debug\n---\n")
    (plugin / "skills" / "promote").mkdir(parents=True)
    (plugin / "skills" / "promote" / "SKILL.md").write_text("---\nname: promote\n---\n")
    monkeypatch.setattr(r, "PLUGIN_ROOT", plugin)
    monkeypatch.setattr(r, "_ARM_DIRS", {})

    treatment = r.arm_plugin_dir("debug", True)
    control = r.arm_plugin_dir("debug", False)

    assert (treatment / "skills" / "debug").is_dir(), "treatment must keep the skill"
    assert not (control / "skills" / "debug").exists(), "control must drop the skill"
    # ...and differ in NOTHING else, or the delta measures more than the skill.
    t_rest = {p.relative_to(treatment) for p in treatment.rglob("*")
              if "debug" not in p.relative_to(treatment).parts}
    c_rest = {p.relative_to(control) for p in control.rglob("*")}
    assert t_rest == c_rest


def test_control_arm_refuses_when_there_is_no_skill_to_suppress(tmp_path, monkeypatch):
    """Suppressing nothing would make the delta meaningless rather than merely noisy —
    the precise failure the old no-op control shipped with, so it must be loud."""
    import run_skill_evals as r
    plugin = tmp_path / "minerva"
    (plugin / "skills").mkdir(parents=True)
    monkeypatch.setattr(r, "PLUGIN_ROOT", plugin)
    monkeypatch.setattr(r, "_ARM_DIRS", {})
    with pytest.raises(RuntimeError, match="no skills/ghost directory"):
        r.arm_plugin_dir("ghost", False)


def test_arm_dirs_are_cached_per_arm(tmp_path, monkeypatch):
    """A multi-case run must not re-copy the plugin tree per invocation."""
    import run_skill_evals as r
    plugin = tmp_path / "minerva"
    (plugin / "skills" / "debug").mkdir(parents=True)
    monkeypatch.setattr(r, "PLUGIN_ROOT", plugin)
    monkeypatch.setattr(r, "_ARM_DIRS", {})
    assert r.arm_plugin_dir("debug", True) is r.arm_plugin_dir("debug", True)
    assert r.arm_plugin_dir("debug", True) != r.arm_plugin_dir("debug", False)


def test_invocation_passes_the_arm_specific_plugin_dir(tmp_path, monkeypatch):
    """The two arms must reach `claude -p` with DIFFERENT --plugin-dir values.

    Without this the suppression is unobservable from the outside and could silently
    regress to the old same-command-twice behaviour.
    """
    import run_skill_evals as r
    plugin = tmp_path / "minerva"
    (plugin / "skills" / "debug").mkdir(parents=True)
    monkeypatch.setattr(r, "PLUGIN_ROOT", plugin)
    monkeypatch.setattr(r, "_ARM_DIRS", {})

    seen = []

    class _Result:
        returncode = 0
        stdout = "ok"
        stderr = ""

    monkeypatch.setattr(r.subprocess, "run",
                        lambda cmd, **kw: (seen.append(cmd), _Result())[1])
    r.claude_invoke("task", True, "debug")
    r.claude_invoke("task", False, "debug")

    assert all("--plugin-dir" in cmd for cmd in seen)
    assert "--bare" not in seen[0], "--bare breaks credential resolution (measured)"
    dirs = [cmd[cmd.index("--plugin-dir") + 1] for cmd in seen]
    assert dirs[0] != dirs[1], "both arms used the same plugin dir — no control at all"


def test_plugin_root_points_at_a_real_plugin_tree():
    """PLUGIN_ROOT must be the plugin, not the repo.

    This runner lives in `<repo>/scripts/`, not inside the plugin, so the obvious
    `parent.parent` is the repo root — and a control arm built from the repo root
    removes nothing. Caught on the first live run by `arm_plugin_dir`'s guard; pinned
    here so it cannot come back silently.
    """
    import run_skill_evals as r
    assert (r.PLUGIN_ROOT / "skills").is_dir(), f"{r.PLUGIN_ROOT} has no skills/"
    assert r.PLUGIN_ROOT.name == "minerva"
    assert (r.PLUGIN_ROOT / "skills" / "debug").is_dir()
