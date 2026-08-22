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


# --- Description ceiling (issue #79) ------------------------------------------
#
# The platform truncates a skill description past this many characters, and the
# tail is exactly where the disambiguating ambient-trigger phrases sit — so an
# over-long description silently loses the part that makes it fire correctly.
# `.minerva/knowledge/2026-07-21-constraint-skill-description-house-style.md`
# has documented the ceiling since unit 046, which trimmed three skills to fit
# it as prose. Nothing tested it, so nothing stopped it regressing — the shape
# `2026-08-11-pattern-an-unenforced-constraint-is-aspirational` is named for.
DESCRIPTION_MAX_CHARS = 1024


def description_overflow(parsed: dict) -> int:
    """Chars by which a skill's description exceeds the ceiling; 0 when it fits.

    Extracted as a predicate so the negative case below can exercise the SAME
    code the parametrized check runs, rather than restating its arithmetic — a
    negative case that re-derives the rule cannot prove the rule is enforced.
    """
    return max(0, len(parsed.get("description") or "") - DESCRIPTION_MAX_CHARS)


@pytest.mark.parametrize("skill", SKILLS)
def test_description_within_ceiling(skill):
    _raw, parsed, _body = _read_skill(skill)
    over = description_overflow(parsed)
    assert over == 0, (
        f"{skill}/SKILL.md description is {over} chars over the "
        f"{DESCRIPTION_MAX_CHARS}-char ceiling — the platform truncates past it and the "
        "tail is where the ambient-trigger phrases live; move detail into the body"
    )


def test_description_ceiling_fires_on_an_over_long_description():
    """Negative coverage: the predicate must flag the class it exists for.

    Without this, `test_description_within_ceiling` is only ever observed passing
    on a corpus that already fits, which cannot distinguish a working check from
    a vacuous one (`2026-08-10-pattern-presence-assertions-rot-into-green-lies`).
    """
    assert description_overflow({"description": "x" * (DESCRIPTION_MAX_CHARS + 7)}) == 7
    assert description_overflow({"description": "x" * DESCRIPTION_MAX_CHARS}) == 0
    assert description_overflow({}) == 0


# --- Cross-skill section citations (issue #78) ---------------------------------
#
# Skills cite each other's protocols. Citing by INTERNAL STEP NUMBER ("per
# `minerva:propose` steps 8-9, 11") breaks silently the moment the cited skill
# renumbers — nothing detects it, and the reader follows a pointer to the wrong
# text. The corpus already had a better form in live use, so this makes it the
# rule and checks it: `minerva:<skill>`'s "<Heading>".
from knowledge_spans import FENCE_RE  # noqa: E402  (single-sourced fence grammar)

HEADING_CITATION_RE = re.compile(r"`minerva:([a-z-]+)`'s \"([^\"]+)\"")


def _unfenced(body: str) -> str:
    """`body` with fenced blocks removed — a citation inside a fence is an
    illustration, not a live pointer (the same rule the pointer-integrity checks use)."""
    out, fenced = [], False
    for line in body.splitlines():
        if FENCE_RE.match(line):
            fenced = not fenced
            continue
        if not fenced:
            out.append(line)
    return "\n".join(out)


def _headings(skill: str) -> list[str]:
    """Every ATX heading in a skill's SKILL.md and references/*.md, hashes stripped."""
    d = SKILLS_DIR / skill
    files = [d / "SKILL.md", *sorted((d / "references").glob("*.md"))]
    return [ln.lstrip("#").strip()
            for f in files if f.is_file()
            for ln in f.read_text().splitlines() if ln.startswith("#")]


def unresolved_heading_citations(body: str) -> list[tuple]:
    """Citations in `body` that name a section which does not exist.

    Matching is by PREFIX, not equality, and that is deliberate rather than lax.
    Headings in this corpus carry trailing clarifiers — `## Implementation protocol
    — apply throughout the session`, `## On approval — worktree setup + file writes`
    — while citations name the stable head of the phrase. Two such citations were
    already live and correct when this check was written; demanding equality would
    have reded CI against correct prose on day one. The prefix must still start at
    the beginning of the heading, so it cannot match an unrelated section.
    """
    bad = []
    for m in HEADING_CITATION_RE.finditer(_unfenced(body)):
        skill, heading = m.group(1), m.group(2)
        if not (SKILLS_DIR / skill).is_dir():
            bad.append((skill, heading, "no such skill"))
        elif not any(h.startswith(heading) for h in _headings(skill)):
            bad.append((skill, heading, "no heading with this prefix"))
    return bad


@pytest.mark.parametrize("skill", SKILLS)
def test_cross_skill_citations_resolve(skill):
    d = SKILLS_DIR / skill
    for f in [d / "SKILL.md", *sorted((d / "references").glob("*.md"))]:
        if not f.is_file():
            continue
        bad = unresolved_heading_citations(f.read_text())
        assert not bad, (
            f"{f.relative_to(REPO_ROOT)} cites sections that do not exist: {bad} — "
            "cite a real heading so a renumbering or rename is caught here"
        )


@pytest.mark.parametrize("skill", SKILLS)
def test_no_cross_skill_step_number_citations(skill):
    """Citing a sibling by internal step number is the form this check replaces."""
    # No comma in the gap: a comma means the sentence moved on, so
    # "invoke `minerva:replan`, return to step 3" is a self-reference to THIS
    # skill's own step 3, not a citation of replan's.
    step_cite = re.compile(r"`minerva:[a-z-]+`(?:'s)?[^.,\n]{0,60}?\bsteps? \d")
    d = SKILLS_DIR / skill
    for f in [d / "SKILL.md", *sorted((d / "references").glob("*.md"))]:
        if not f.is_file():
            continue
        hits = step_cite.findall(_unfenced(f.read_text()))
        assert not hits, (
            f"{f.relative_to(REPO_ROOT)} cites a sibling skill by step number "
            f"({hits}) — renumbering breaks it silently; cite the section heading "
            "as `minerva:<skill>`'s \"<Heading>\" instead"
        )


def test_citation_check_fires_on_a_missing_heading():
    """Negative coverage for the resolver."""
    assert unresolved_heading_citations('per `minerva:promote`\'s "No Such Section"') == [
        ("promote", "No Such Section", "no heading with this prefix")]
    assert unresolved_heading_citations('per `minerva:nonexistent-skill`\'s "Anything"') == [
        ("nonexistent-skill", "Anything", "no such skill")]


def test_citation_check_accepts_exact_and_prefix_matches():
    # exact heading
    assert unresolved_heading_citations('per `minerva:review`\'s "Triage persistence"') == []
    # prefix of `## Implementation protocol — apply throughout the session`
    assert unresolved_heading_citations('per `minerva:work`\'s "Implementation protocol"') == []


def test_citation_check_ignores_fenced_examples():
    assert unresolved_heading_citations('```\n`minerva:promote`\'s "Fake"\n```') == []


def test_step_number_check_ignores_a_self_reference_after_a_comma():
    """`invoke minerva:replan, return to step 3` cites THIS skill's step 3.

    Without the comma exclusion the check flags it, which would push authors to
    reword correct prose to satisfy a false positive.
    """
    step_cite = re.compile(r"`minerva:[a-z-]+`(?:'s)?[^.,\n]{0,60}?\bsteps? \d")
    assert not step_cite.findall("trigger `minerva:replan`, return to step 3")
    assert step_cite.findall("per `minerva:promote` Mode A step 7")


# --- The six target-resolution blocks (issue #77) ------------------------------
#
# The same "## Target resolution" protocol is stated in six skills, kept in sync by
# the sentence "**Keep all six blocks in sync if you edit one.**" and nothing else —
# the shape `2026-08-11-pattern-a-comment-cannot-enforce-a-shared-invariant` is named
# for, and it had already drifted.
#
# The blocks are NOT copies, and that is deliberate: `minerva:cleanup` has three steps
# because its no-argument mode means "all merged worktrees"; `minerva:review` and
# `minerva:ship` have materially different "none found" behaviour (skip to code review /
# bare mode). So byte-identity is the wrong invariant — normalizing enough to make
# cleanup's three steps match work's five would erase everything worth checking.
#
# What IS shared, exact, and load-bearing is asserted instead: each block enumerates
# its five siblings, and each states the two lookup rules whose absence has caused
# real bugs (a digit-anchored glob silently skipping date-named units).
TARGET_RESOLUTION_BLOCKS = {
    "work": "SKILL.md",
    "replan": "SKILL.md",
    "promote": "SKILL.md",
    "cleanup": "SKILL.md",
    "review": "references/protocol.md",
    "ship": "references/protocol.md",
}
SYNC_PLEA = "**Keep all six blocks in sync if you edit one.**"


def target_resolution_block(skill: str) -> str:
    """The `## Target resolution` section of `skill`, up to the next heading."""
    path = SKILLS_DIR / skill / TARGET_RESOLUTION_BLOCKS[skill]
    m = re.search(r"^## Target resolution\n(.*?)(?=^## )", path.read_text(), re.S | re.M)
    assert m, f"{skill}: no '## Target resolution' section in {TARGET_RESOLUTION_BLOCKS[skill]}"
    return m.group(1)


def cited_siblings(block: str) -> set:
    """The skills named in the block's 'Same pattern used by ...' enumeration."""
    m = re.search(r"Same pattern used by (.*?)\. \*\*Keep all six", block, re.S)
    return set(re.findall(r"`minerva:([a-z-]+)`", m.group(1))) if m else set()


def test_all_six_target_resolution_blocks_exist():
    """Guards the enumeration itself — if the locator silently found nothing, every
    check below would pass vacuously."""
    assert len(TARGET_RESOLUTION_BLOCKS) == 6
    for skill in TARGET_RESOLUTION_BLOCKS:
        assert target_resolution_block(skill).strip()


@pytest.mark.parametrize("skill", sorted(TARGET_RESOLUTION_BLOCKS))
def test_target_resolution_block_names_its_five_siblings(skill):
    """The sync invariant the plea asks for, now actually enforced.

    A rename, a seventh adopter, or a dropped name reds CI here instead of drifting.
    """
    expected = set(TARGET_RESOLUTION_BLOCKS) - {skill}
    block = target_resolution_block(skill)
    assert SYNC_PLEA in block, f"{skill}: the sync plea is missing from its block"
    assert cited_siblings(block) == expected, (
        f"{skill}'s target-resolution block names {sorted(cited_siblings(block))}, "
        f"expected the other five: {sorted(expected)}"
    )


@pytest.mark.parametrize("skill", sorted(TARGET_RESOLUTION_BLOCKS))
def test_target_resolution_block_states_both_lookup_rules(skill):
    """Both operational clauses, in every copy.

    These are not stylistic. Scanning only `.minerva/work/*/` misses units that live
    in a worktree; a digit-anchored glob misses `YYYY-MM-DD-<slug>` units entirely,
    which this repo has already shipped and fixed once.
    """
    block = target_resolution_block(skill)
    assert ".minerva/worktrees/" in block, (
        f"{skill}: block does not say worktrees are scanned — a unit in a worktree "
        "would be invisible to resolution")
    assert "id form" in block, (
        f"{skill}: block does not say BOTH id forms are matched — a digit-anchored "
        "glob silently skips date-named units")


def test_sibling_enumeration_check_fires_on_a_wrong_name():
    """Negative coverage: exercise the same comparison the check runs."""
    good = ("Same pattern used by `minerva:work`, `minerva:replan`, `minerva:promote`, "
            "`minerva:review`, `minerva:ship`. " + SYNC_PLEA)
    assert cited_siblings(good) == {"work", "replan", "promote", "review", "ship"}
    renamed = good.replace("`minerva:ship`", "`minerva:shipp`")
    assert cited_siblings(renamed) != {"work", "replan", "promote", "review", "ship"}
    dropped = good.replace(", `minerva:ship`", "")
    assert len(cited_siblings(dropped)) == 4
