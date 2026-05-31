"""Declarative structural-contract checks for the minerva skills.

Each skill under ``plugins/minerva/skills/<name>/`` must carry a companion
``evals/<name>/contract.json`` that declares its structural contract:

* ``frontmatter`` — required keys, exact-value constraints, non-empty keys, and
  raw substrings the frontmatter block must contain.
* ``anchors``     — substrings the SKILL.md body must contain. An anchor is
  either a plain string (must-contain, case-sensitive) or an object
  ``{"any_of": [...], "ignore_case": true}`` expressing a disjunction.
* ``cross_surface`` — which catalog surfaces (root README, plugin README,
  using-minerva body) must list ``minerva:<skill>``.

This module *enumerates* the skill directories and fails when any of them is
missing a contract, so coverage can never silently lag the skill set. It is the
deterministic regression floor; behavioral "does this skill add value" evals are
a separate, sequenced layer that consumes the same ``evals/`` format (see
``evals/README.md`` — the reserved ``behavioral`` namespace).

The companion module ``test_minerva.py`` keeps the non-per-skill checks
(marketplace registration, plugin.json, feature-cycle absence).
"""
import json
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = REPO_ROOT / "plugins" / "minerva"
SKILLS_DIR = PLUGIN_DIR / "skills"
EVALS_DIR = REPO_ROOT / "evals"

# Catalog surfaces a contract can require ``minerva:<skill>`` to appear in.
SURFACE_FILES = {
    "root_readme": REPO_ROOT / "README.md",
    "plugin_readme": PLUGIN_DIR / "README.md",
    "using_minerva_body": SKILLS_DIR / "using-minerva" / "SKILL.md",
}


def _discover_skills() -> list[str]:
    """Enumerate skill directories (those holding a SKILL.md) under SKILLS_DIR.

    Rooted at the repo's own ``plugins/minerva/skills`` — never a loose glob, so
    worktree copies under ``.minerva/worktrees/`` can't be picked up.
    """
    return sorted(
        d.name for d in SKILLS_DIR.iterdir() if (d / "SKILL.md").is_file()
    )


SKILLS = _discover_skills()


def _contract_path(skill: str) -> Path:
    return EVALS_DIR / skill / "contract.json"


def _load_contract(skill: str) -> dict:
    path = _contract_path(skill)
    assert path.is_file(), f"missing contract: {path.relative_to(REPO_ROOT)}"
    return json.loads(path.read_text())


def _read_skill(skill: str) -> tuple[str, dict, str]:
    """Return (raw_frontmatter, parsed_frontmatter, body) for a skill."""
    text = (SKILLS_DIR / skill / "SKILL.md").read_text()
    assert text.startswith("---\n"), f"{skill}/SKILL.md missing frontmatter"
    _, raw_fm, body = text.split("---\n", 2)
    parsed = yaml.safe_load(raw_fm)
    assert isinstance(parsed, dict), f"{skill} frontmatter is not a mapping"
    return raw_fm, parsed, body


def _anchor_satisfied(anchor, body: str) -> bool:
    """A plain string must be a substring; an object is an any-of disjunction."""
    if isinstance(anchor, str):
        return anchor in body
    alts = anchor["any_of"]
    if anchor.get("ignore_case"):
        low = body.lower()
        return any(alt.lower() in low for alt in alts)
    return any(alt in body for alt in alts)


def _anchor_label(anchor) -> str:
    if isinstance(anchor, str):
        return repr(anchor)
    flag = " (ignore_case)" if anchor.get("ignore_case") else ""
    return f"any_of {anchor['any_of']}{flag}"


def test_evals_dir_exists():
    assert EVALS_DIR.is_dir(), f"missing evals/ directory at {EVALS_DIR}"
    assert (EVALS_DIR / "README.md").is_file(), "evals/README.md must document the format"


def test_skills_discovered():
    # Guards the enumeration itself: if discovery silently returns nothing,
    # every parametrized test below would vacuously pass.
    assert len(SKILLS) >= 13, f"expected >=13 skills, discovered {len(SKILLS)}: {SKILLS}"


@pytest.mark.parametrize("skill", SKILLS)
def test_every_skill_has_contract(skill):
    """No vacuous pass: every enumerated skill must carry a contract.json."""
    path = _contract_path(skill)
    assert path.is_file(), (
        f"skill {skill!r} has no {path.relative_to(REPO_ROOT)} — "
        "every skill must declare a structural contract"
    )


@pytest.mark.parametrize("skill", SKILLS)
def test_contract_well_formed(skill):
    contract = _load_contract(skill)
    assert contract.get("skill") == skill, (
        f"contract 'skill' field {contract.get('skill')!r} must equal dir name {skill!r}"
    )
    allowed = {"skill", "frontmatter", "anchors", "cross_surface", "behavioral"}
    unknown = set(contract) - allowed
    assert not unknown, f"{skill} contract has unknown keys: {sorted(unknown)}"
    # The behavioral namespace is reserved for the Unit 2 runner; this floor
    # treats it as opaque and ignores its contents.
    assert isinstance(contract.get("frontmatter", {}), dict)
    assert isinstance(contract.get("anchors", []), list)
    assert isinstance(contract.get("cross_surface", {}), dict)


@pytest.mark.parametrize("skill", SKILLS)
def test_frontmatter_contract(skill):
    raw_fm, parsed, _ = _read_skill(skill)
    fm = _load_contract(skill).get("frontmatter", {})
    for key in fm.get("required_keys", []):
        assert key in parsed, f"{skill} frontmatter missing required key {key!r}"
    for key, expected in fm.get("values", {}).items():
        assert parsed.get(key) == expected, (
            f"{skill} frontmatter {key!r} is {parsed.get(key)!r}, expected {expected!r}"
        )
    for key in fm.get("non_empty", []):
        assert parsed.get(key), f"{skill} frontmatter {key!r} must be non-empty"
    for needle in fm.get("contains", []):
        assert needle in raw_fm, f"{skill} frontmatter must contain {needle!r}"


@pytest.mark.parametrize("skill", SKILLS)
def test_body_anchors(skill):
    _, _, body = _read_skill(skill)
    for anchor in _load_contract(skill).get("anchors", []):
        assert _anchor_satisfied(anchor, body), (
            f"{skill}/SKILL.md body missing required anchor: {_anchor_label(anchor)}"
        )


@pytest.mark.parametrize("skill", SKILLS)
def test_cross_surface(skill):
    cross = _load_contract(skill).get("cross_surface", {})
    token = f"minerva:{skill}"
    for surface, required in cross.items():
        assert surface in SURFACE_FILES, f"{skill} declares unknown surface {surface!r}"
        if not required:
            continue
        text = SURFACE_FILES[surface].read_text()
        assert token in text, (
            f"{token} must appear in {SURFACE_FILES[surface].relative_to(REPO_ROOT)} "
            f"(cross_surface.{surface})"
        )
