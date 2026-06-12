"""Byte-budget and reference-pointer integrity for the minerva skills.

Work unit 035 (skill-progressive-disclosure) restructured the fat skills into a
thin ``SKILL.md`` core plus on-demand ``references/*.md`` files. Two properties
keep that structure honest:

* **Budget** — every ``SKILL.md`` stays at or under ``BUDGET_BYTES`` (9 KB), so
  skill prose loaded into the main loop at invocation time cannot silently
  regrow. The cap applies to *all* skills, not just the restructured nine:
  skills already under the cap are frozen at it.
* **Pointer integrity** — the lazy-load mechanism only works if both directions
  hold: every ``references/*.md`` file is mentioned by name from its skill's
  ``SKILL.md`` (no orphaned reference a reader can never discover), and every
  ``references/<file>.md`` mention in a ``SKILL.md`` resolves to a real file
  (no dangling pointer that fails at the moment of need).

Like ``test_skill_contracts.py``, this module *enumerates* the skill
directories, so a newly added skill is covered automatically.
"""
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "plugins" / "minerva" / "skills"

# 9 KB. The number is the work unit's approved budget — see
# .minerva/work/035-skill-progressive-disclosure/proposal.md.
BUDGET_BYTES = 9216

# A reference pointer as written in skill prose: ``references/<name>.md``.
REF_MENTION_RE = re.compile(r"references/[A-Za-z0-9._-]+\.md")


def _discover_skills() -> list[str]:
    """Enumerate skill directories (those holding a SKILL.md) under SKILLS_DIR.

    Rooted at the repo's own ``plugins/minerva/skills`` — never a loose glob, so
    worktree copies under ``.minerva/worktrees/`` can't be picked up.
    """
    return sorted(
        d.name for d in SKILLS_DIR.iterdir() if (d / "SKILL.md").is_file()
    )


SKILLS = _discover_skills()


def test_skills_discovered():
    # Guards the enumeration itself: if discovery silently returns nothing,
    # every parametrized test below would vacuously pass.
    assert len(SKILLS) >= 13, f"expected >=13 skills, discovered {len(SKILLS)}: {SKILLS}"


@pytest.mark.parametrize("skill", SKILLS)
def test_skill_md_within_budget(skill):
    path = SKILLS_DIR / skill / "SKILL.md"
    size = path.stat().st_size
    assert size <= BUDGET_BYTES, (
        f"{skill}/SKILL.md is {size} bytes, over the {BUDGET_BYTES}-byte budget — "
        "move detail prose to references/*.md (verbatim) instead of growing the core"
    )


@pytest.mark.parametrize("skill", SKILLS)
def test_every_reference_file_is_pointed_to(skill):
    """No orphans: each references/*.md must be mentioned from its SKILL.md."""
    refs_dir = SKILLS_DIR / skill / "references"
    if not refs_dir.is_dir():
        return
    ref_files = sorted(refs_dir.glob("*.md"))
    assert ref_files, f"{skill}/references/ exists but holds no .md files"
    body = (SKILLS_DIR / skill / "SKILL.md").read_text()
    for ref in ref_files:
        assert f"references/{ref.name}" in body, (
            f"{skill}/references/{ref.name} is never mentioned in {skill}/SKILL.md — "
            "an unreferenced file can never be lazily loaded; point to it or remove it"
        )


@pytest.mark.parametrize("skill", SKILLS)
def test_every_reference_pointer_resolves(skill):
    """No dangling pointers: each references/<file>.md mention must exist."""
    body = (SKILLS_DIR / skill / "SKILL.md").read_text()
    for mention in sorted(set(REF_MENTION_RE.findall(body))):
        target = SKILLS_DIR / skill / mention
        assert target.is_file(), (
            f"{skill}/SKILL.md points at {mention}, which does not exist under "
            f"{skill}/ — a dangling pointer fails exactly when the detail is needed"
        )
