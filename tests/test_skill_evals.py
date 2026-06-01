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
