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

from knowledge_spans import FENCE_RE

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "plugins" / "minerva" / "skills"

# 9 KB. The number is the work unit's approved budget — see
# .minerva/work/035-skill-progressive-disclosure/proposal.md.
BUDGET_BYTES = 9216

# A reference pointer as written in skill prose: ``references/<name>.md``.
REF_MENTION_RE = re.compile(r"references/[A-Za-z0-9._-]+\.md")

# Any references/ token at all, canonical or not — superset of REF_MENTION_RE
# used to catch malformed pointers (``references/briefs`` missing ``.md``).
REF_LOOSE_RE = re.compile(r"references/[A-Za-z0-9._-]+")

# The mandatory-instruction marker: a pointer line must tell the reader to
# *read* the file, not merely mention it in passing.
READ_VERB_RE = re.compile(r"\bread\b", re.IGNORECASE)


def _unfenced_lines(body: str) -> list[str]:
    """Lines of ``body`` outside fenced code blocks.

    Fenced examples are illustrations, not live pointers (the same reasoning
    as knowledge 023's fence-aware edge derivation) — the strengthened checks
    must not flag them.
    """
    lines, fenced = [], False
    for line in body.splitlines():
        # FENCE_RE is the single-sourced fence grammar (indented + tilde
        # fences included) — imported, never re-derived (knowledge 019's rule,
        # applied beyond the wiki corpus). Toggle semantics pinned below.
        if FENCE_RE.match(line):
            fenced = not fenced
            continue
        if not fenced:
            lines.append(line)
    return lines


def malformed_pointers(body: str) -> list[str]:
    """references/ tokens (outside fences) that don't match the canonical
    ``references/<name>.md`` form — e.g. a pointer that lost its ``.md``."""
    bad = []
    for line in _unfenced_lines(body):
        for token in REF_LOOSE_RE.findall(line):
            # Sentence-ending periods after .md are prose, not malformation;
            # rstrip can't mask a real defect (".bak" doesn't end in dots).
            if not REF_MENTION_RE.fullmatch(token.rstrip(".")):
                bad.append(token)
    return bad


def files_missing_read_directive(refs_dir: Path, body: str) -> list[str]:
    """references/*.md files with no unfenced SKILL.md mention line carrying a
    read verb. Per-file, not per-mention: secondary verb-less mentions are
    legal as long as at least one line instructs the reader to read the file."""
    if not refs_dir.is_dir():
        return []
    lines = _unfenced_lines(body)
    missing = []
    for ref in sorted(refs_dir.glob("*.md")):
        needle = f"references/{ref.name}"
        if not any(needle in l and READ_VERB_RE.search(l) for l in lines):
            missing.append(ref.name)
    return missing


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


@pytest.mark.parametrize("skill", SKILLS)
def test_no_malformed_reference_pointers(skill):
    """A pointer that lost its .md (``references/briefs``) dangles invisibly —
    the canonical-mention checks above never see it. Work unit 036."""
    body = (SKILLS_DIR / skill / "SKILL.md").read_text()
    bad = malformed_pointers(body)
    assert not bad, (
        f"{skill}/SKILL.md has malformed reference pointers {bad} — "
        "write the canonical references/<name>.md form so the integrity checks see them"
    )


@pytest.mark.parametrize("skill", SKILLS)
def test_every_reference_has_read_directive(skill):
    """Each reference file must be reachable through a mandatory instruction:
    at least one unfenced mention line containing 'read'. Work unit 036."""
    body = (SKILLS_DIR / skill / "SKILL.md").read_text()
    missing = files_missing_read_directive(SKILLS_DIR / skill / "references", body)
    assert not missing, (
        f"{skill}: references/{missing} have no mention line with a read "
        "directive — a passing mention is not an instruction to load the detail"
    )


# --- Negative coverage: each strengthened check must fire on its violation class.


def test_malformed_pointer_detected():
    assert malformed_pointers("before step 2, read references/briefs") == ["references/briefs"]
    assert malformed_pointers("read references/briefs.md") == []
    assert malformed_pointers("see references/briefs.md.bak") == ["references/briefs.md.bak"]
    # fenced examples are illustrations, not live pointers
    assert malformed_pointers("```\nreferences/briefs\n```") == []
    # indented fences (list items) toggle too
    assert malformed_pointers("1. step\n   ```\n   references/briefs\n   ```") == []
    # sentence punctuation after .md is prose, not malformation — including ellipsis
    assert malformed_pointers("Read references/foo.md.") == []
    assert malformed_pointers("Read references/foo.md..") == []
    # but a token malformed even after stripping dots stays flagged
    assert malformed_pointers("read references/foo.") == ["references/foo."]


def test_fence_toggle_semantics_pinned():
    # a column-0 fence containing prose, plus an indented pair outside it:
    # only the unfenced indented-pair content is visible, fences themselves never are
    body = "```\nfenced references/a\n```\nvisible\n  ```\n  hidden references/b\n  ```\ntail"
    assert _unfenced_lines(body) == ["visible", "tail"]


def test_read_directive_check_detected(tmp_path):
    refs = tmp_path / "references"
    refs.mkdir()
    (refs / "detail.md").write_text("# detail\n")
    # mention exists, but nothing instructs the reader to read it
    assert files_missing_read_directive(refs, "see references/detail.md for more") == ["detail.md"]
    # one read-verb line suffices; secondary verb-less mentions stay legal
    body = "Read references/detail.md now.\nAlso references/detail.md applies."
    assert files_missing_read_directive(refs, body) == []
    # a read directive inside a fence does not count
    fenced = "```\nread references/detail.md\n```\nreferences/detail.md is mentioned"
    assert files_missing_read_directive(refs, fenced) == ["detail.md"]
    # no references/ dir → vacuously clean
    assert files_missing_read_directive(tmp_path / "absent", "anything") == []


def test_unfenced_lines_strips_fences():
    assert _unfenced_lines("a\n```\nb\n```\nc") == ["a", "c"]
    # tilde fences are part of the single-sourced grammar
    assert _unfenced_lines("a\n~~~\nb\n~~~\nc") == ["a", "c"]
