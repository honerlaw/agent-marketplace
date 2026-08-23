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

from knowledge_spans import unfenced_lines

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "plugins" / "minerva" / "skills"

# 9 KB. The number is the work unit's approved budget — see
# .minerva/work/035-skill-progressive-disclosure/proposal.md.
BUDGET_BYTES = 9216

# A reference pointer as written in skill prose: ``references/<name>.md``.
REF_MENTION_RE = re.compile(r"references/[A-Za-z0-9._-]+\.md")

# A CROSS-SKILL pointer names its owning skill explicitly:
# ``plugins/minerva/skills/<skill>/references/<name>.md``. Without this form a
# skill cannot path-reference a sibling's reference file at all — the bare
# pattern above matches the *tail* of a qualified path and resolves it against
# the CITING skill, where it dangles. That was inert while every skill's
# references were private to it, and stopped being inert once skills began
# reusing each other's protocols verbatim rather than restating them.
QUALIFIED_MENTION_RE = re.compile(
    r"plugins/minerva/skills/([A-Za-z0-9._-]+)/(references/[A-Za-z0-9._-]+\.md)"
)

# Any references/ token at all, canonical or not — superset of REF_MENTION_RE
# used to catch malformed pointers (``references/briefs`` missing ``.md``).
REF_LOOSE_RE = re.compile(r"references/[A-Za-z0-9._-]+")

# The mandatory-instruction marker: a pointer line must tell the reader to
# *read* the file, not merely mention it in passing.
READ_VERB_RE = re.compile(r"\bread\b", re.IGNORECASE)


# Lines outside fenced blocks. Fenced examples are illustrations, not live pointers
# (knowledge 023's fence-aware edge derivation), so the checks below must not flag them.
# The loop itself is `knowledge_spans.unfenced_lines` — imported, never re-derived, the
# same rule the grammar has always followed and the loop around it now does too.
_unfenced_lines = unfenced_lines


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


def skill_docs(skill: str) -> list[Path]:
    """Every prose file a skill ships: its ``SKILL.md`` plus its ``references/*.md``.

    The pointer-integrity checks below originally read ``SKILL.md`` alone, which made
    them blind to the pointers that most need guarding: a reference file is where a
    protocol is written out, so it is where one skill cites another's protocol by the
    qualified ``plugins/minerva/skills/<skill>/references/<f>.md`` path. Those citations
    were invisible to every check in this module — a rename would break them silently,
    exactly the shape of `2026-08-11-pattern-a-gate-blind-to-what-it-checks` (the gate
    read clean because its model of "a pointer" was narrower than the corpus's). Widening
    the scan to reference files caught four already-dangling cross-skill pointers on the
    day it was written.
    """
    d = SKILLS_DIR / skill
    return [d / "SKILL.md", *sorted((d / "references").glob("*.md"))]


def _pointer_text(path: Path) -> str:
    """A doc's pointer-bearing prose: unfenced lines only.

    A pointer inside a fence is an illustration, not a live reference — the rule
    `malformed_pointers` already followed, applied here too so the two checks cannot
    disagree about what counts as a pointer. Verified behavior-preserving for the
    ``SKILL.md`` scan when this widened: no SKILL.md in the corpus carries a pointer
    that appears only inside a fence.
    """
    return "\n".join(_unfenced_lines(path.read_text()))


def reference_mentions(body: str) -> list[tuple]:
    """Every reference pointer in ``body`` as ``(owning_skill_or_None, "references/<f>.md")``.

    ``None`` means "resolve against the citing skill" — the bare, local form.
    A named skill means the pointer is qualified and resolves against THAT skill.

    Qualified mentions are matched and stripped FIRST so the bare pass cannot
    re-match their tail: a qualified path contains a literal ``references/x.md``
    substring, and attributing that to the citing skill is the whole defect.
    """
    qualified = [(m.group(1), m.group(2)) for m in QUALIFIED_MENTION_RE.finditer(body)]
    bare_only = QUALIFIED_MENTION_RE.sub("", body)
    bare = [(None, m.group(0)) for m in REF_MENTION_RE.finditer(bare_only)]
    return qualified + bare


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
    """No dangling pointers: each reference mention must exist.

    Scanned across ``SKILL.md`` **and** ``references/*.md`` (see `skill_docs`).
    A bare mention resolves under the citing skill; a qualified
    ``plugins/minerva/skills/<other>/references/<f>.md`` mention resolves under
    the skill it names, so one skill can cite another's protocol by path.
    """
    for doc in skill_docs(skill):
        body = _pointer_text(doc)
        for owner, mention in sorted(set(reference_mentions(body)), key=lambda t: (t[0] or "", t[1])):
            target = SKILLS_DIR / (owner or skill) / mention
            assert target.is_file(), (
                f"{doc.relative_to(SKILLS_DIR)} points at {mention} under "
                f"{owner or skill}/, which does not exist — a dangling pointer "
                "fails exactly when the detail is needed. Citing a sibling skill's "
                "protocol needs the qualified plugins/minerva/skills/<skill>/"
                "references/<file>.md form; a bare mention resolves locally"
            )


@pytest.mark.parametrize("skill", SKILLS)
def test_no_malformed_reference_pointers(skill):
    """A pointer that lost its .md (``references/briefs``) dangles invisibly —
    the canonical-mention checks above never see it. Work unit 036.

    Scanned across ``SKILL.md`` and ``references/*.md`` alike."""
    for doc in skill_docs(skill):
        bad = malformed_pointers(doc.read_text())
        assert not bad, (
            f"{doc.relative_to(SKILLS_DIR)} has malformed reference pointers {bad} — "
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


def test_reference_files_are_in_the_pointer_scan(tmp_path):
    """Negative coverage for the widened scan: a dangling pointer written in a
    ``references/*.md`` file must be reachable by the same predicates that guard
    ``SKILL.md``. Without this, `skill_docs` could silently narrow back to the core
    and both widened tests would keep passing on a corpus that is already clean
    (`2026-08-10-pattern-presence-assertions-rot-into-green-lies`)."""
    docs = skill_docs("propose")
    assert docs[0].name == "SKILL.md"
    assert any(d.parent.name == "references" for d in docs[1:]), (
        "skill_docs returned no reference files — the widened scan is vacuous")

    # The two predicates the widened tests apply, exercised on reference-file prose.
    assert reference_mentions("see plugins/minerva/skills/promote/references/nope.md") == [
        ("promote", "references/nope.md")]
    assert malformed_pointers("see references/nope") == ["references/nope"]


def test_fenced_pointer_in_a_reference_file_is_not_live():
    """A pointer inside a fence is an illustration — `_pointer_text` drops it, so a
    documented example naming a file that does not exist cannot red the suite."""
    assert reference_mentions(_pointer_text_of("```\nreferences/nope.md\n```")) == []


def _pointer_text_of(raw: str) -> str:
    """`_pointer_text` for a literal string rather than a file on disk."""
    return "\n".join(_unfenced_lines(raw))


def test_qualified_mention_is_attributed_to_the_named_skill():
    """The #85 defect: a qualified path's tail matched the bare pattern, so a
    sibling's file resolved against the citing skill and dangled."""
    body = "Read plugins/minerva/skills/promote/references/github-issues.md verbatim."
    assert reference_mentions(body) == [("promote", "references/github-issues.md")]
    # and crucially NOT also attributed locally
    assert (None, "references/github-issues.md") not in reference_mentions(body)


def test_bare_mention_still_resolves_locally():
    assert reference_mentions("read references/phases.md") == [(None, "references/phases.md")]


def test_mixed_mentions_keep_their_owners():
    body = ("read references/phases.md, then "
            "plugins/minerva/skills/promote/references/modes.md")
    assert sorted(reference_mentions(body), key=lambda x: (x[0] or "", x[1])) == [
        (None, "references/phases.md"),
        ("promote", "references/modes.md"),
    ]


def test_qualified_mention_of_a_real_sibling_file_exists():
    """The live citation added for #85 must actually resolve — a qualified form
    that cannot be checked against disk is no better than the phrasing it replaced."""
    owner, mention = ("promote", "references/github-issues.md")
    assert (SKILLS_DIR / owner / mention).is_file()


def test_qualified_pointer_to_a_missing_file_is_still_a_dangling_pointer():
    """Qualification must not become an escape hatch: naming another skill does
    not exempt the pointer from resolving."""
    owner, mention = reference_mentions(
        "see plugins/minerva/skills/promote/references/does-not-exist.md")[0]
    assert not (SKILLS_DIR / owner / mention).is_file()
