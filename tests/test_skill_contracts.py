"""Declarative structural-contract checks for the minerva skills.

Each skill under ``plugins/minerva/skills/<name>/`` must carry a companion
``evals/<name>/contract.json`` that declares its structural contract:

* ``frontmatter`` — required keys, exact-value constraints, non-empty keys, and
  raw substrings the frontmatter block must contain.
* ``anchors``     — substrings the SKILL.md body must contain. An anchor is
  either a plain string (must-contain, case-sensitive) or an object
  ``{"any_of": [...], "ignore_case": true}`` expressing a disjunction. An
  object anchor may carry ``"file": "references/<name>.md"`` to check a
  reference file in the skill directory instead of the SKILL.md body — used
  when work unit 035 moved anchored prose verbatim into references/.
* ``cross_surface`` — which catalog surfaces (root README, plugin README,
  using-minerva body) must list ``minerva:<skill>``.

This module *enumerates* the skill directories and fails when any of them is
missing a contract, so coverage can never silently lag the skill set. It is the
deterministic regression floor; behavioral "does this skill add value" evals are
a separate layer (``scripts/run_skill_evals.py``) that reads sibling
``evals/<skill>/behavioral.json`` files (see ``evals/README.md``).

The companion module ``test_minerva.py`` keeps the non-per-skill checks
(marketplace registration, plugin.json, feature-cycle absence).
"""
import json
import re
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


def _present(needle: str, text: str, ignore_case: bool = False) -> bool:
    """Is ``needle`` present in ``text``?

    ``minerva:<skill>`` tokens are matched on a token boundary so that, e.g.,
    ``minerva:propose`` is NOT satisfied by ``minerva:propose-ship`` — otherwise
    deleting a standalone catalog row would slip past the very catalog-sync
    regression this floor exists to catch.
    """
    flags = re.IGNORECASE if ignore_case else 0
    if needle.startswith("minerva:"):
        return re.search(re.escape(needle) + r"(?![\w-])", text, flags) is not None
    if ignore_case:
        return needle.lower() in text.lower()
    return needle in text


def _anchor_satisfied(anchor, body: str) -> bool:
    """A plain string must be present; an object is an any-of disjunction."""
    if isinstance(anchor, str):
        return _present(anchor, body)
    ignore_case = anchor.get("ignore_case", False)
    return any(_present(alt, body, ignore_case) for alt in anchor["any_of"])


def _anchor_text(skill: str, anchor, skill_body: str) -> str:
    """Resolve the text an anchor is checked against.

    Default is the SKILL.md body. An object anchor with a ``file`` key is
    checked against that file (path relative to the skill directory) — the
    deliberate-retarget mechanism for prose moved into ``references/``.
    """
    if isinstance(anchor, dict) and "file" in anchor:
        path = SKILLS_DIR / skill / anchor["file"]
        assert path.is_file(), (
            f"{skill} contract anchor targets {anchor['file']!r}, "
            "which does not exist in the skill directory"
        )
        return path.read_text()
    return skill_body


def _anchor_label(anchor) -> str:
    if isinstance(anchor, str):
        return repr(anchor)
    flag = " (ignore_case)" if anchor.get("ignore_case") else ""
    where = f" in {anchor['file']}" if anchor.get("file") else ""
    return f"any_of {anchor['any_of']}{flag}{where}"


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
    allowed = {"skill", "frontmatter", "anchors", "cross_surface"}
    unknown = set(contract) - allowed
    assert not unknown, f"{skill} contract has unknown keys: {sorted(unknown)}"
    # Behavioral "does this skill add value" evals live in a sibling
    # evals/<skill>/behavioral.json, read by scripts/run_skill_evals.py — not here.
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
        text = _anchor_text(skill, anchor, body)
        where = anchor.get("file", "SKILL.md body") if isinstance(anchor, dict) else "SKILL.md body"
        assert _anchor_satisfied(anchor, text), (
            f"{skill} {where} missing required anchor: {_anchor_label(anchor)}"
        )


def test_anchor_object_keys_are_known():
    """An object anchor may only use any_of / ignore_case / file — typos in a
    contract must fail loudly rather than silently widening the check."""
    allowed = {"any_of", "ignore_case", "file"}
    for skill in SKILLS:
        for anchor in _load_contract(skill).get("anchors", []):
            if isinstance(anchor, dict):
                unknown = set(anchor) - allowed
                assert not unknown, (
                    f"{skill} contract anchor {_anchor_label(anchor)} has "
                    f"unknown keys: {sorted(unknown)}"
                )
                assert anchor.get("any_of"), (
                    f"{skill} object anchor must carry a non-empty any_of"
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
        assert _present(token, text), (
            f"{token} must appear in {SURFACE_FILES[surface].relative_to(REPO_ROOT)} "
            f"(cross_surface.{surface})"
        )


def test_token_match_is_boundary_aware():
    # Guards the Finding-1 fix: a prefix token must not satisfy a longer one.
    assert _present("minerva:propose", "see minerva:propose for details")
    assert _present("minerva:propose", "minerva:propose.")
    assert not _present("minerva:propose", "only minerva:propose-ship here")
    assert _present("minerva:propose-ship", "minerva:propose-ship runs the lifecycle")
    assert not _present("minerva:propose-ship", "only minerva:propose-ship-auto here")
