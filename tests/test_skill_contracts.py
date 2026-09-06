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
from knowledge_spans import unfenced_lines  # noqa: E402  (single-sourced fence scan)

HEADING_CITATION_RE = re.compile(r"`minerva:([a-z-]+)`'s \"([^\"]+)\"")


def _unfenced(body: str) -> str:
    """`body` with fenced blocks removed — a citation inside a fence is an
    illustration, not a live pointer (the same rule the pointer-integrity checks use).

    A joined-string view over the shared `knowledge_spans.unfenced_lines`; the toggle
    loop lives there so this module and `test_skill_budget` cannot drift apart.
    """
    return "\n".join(unfenced_lines(body))


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


# A sibling cited by internal step number — the fragile form the heading anchors
# replace. The GAP (group 2) is the text between the skill mention and the step
# reference; the exclusion below reads only that span, never the whole sentence.
STEP_CITATION_RE = re.compile(r"(`minerva:[a-z-]+`((?:'s)?[^.\n]{0,60}?)\bsteps? \d)")

# Markers that make the step reference point at THIS document rather than the
# skill just mentioned: "invoke `minerva:replan`, return to step 3" is a jump back
# to the current protocol's own step 3.
#
# Scoped to the gap deliberately. An earlier version banned commas anywhere in the
# gap, which silenced a genuine citation phrased with a natural comma
# ("See `minerva:promote`, step 5"). Scanning the whole sentence instead would
# reintroduce the mirror defect — "re-run `minerva:promote`'s step 3" would be
# excluded by a marker that belongs to a different clause.
SELF_REFERENCE_MARKERS = ("return to", "back to", "re-run", "rerun", "above")


def step_number_citations(body: str) -> list:
    """Cross-skill step-number citations in `body`, self-references excluded.

    Module-level and shared, so the negative cases below exercise the SAME predicate
    the enforcement check runs. An earlier draft defined this regex twice — once in
    the check, once in its own negative test — which would have let the negative case
    keep passing against a stale copy after the real one was edited
    (`2026-08-10-pattern-presence-assertions-rot-into-green-lies`).
    """
    out = []
    for whole, gap in STEP_CITATION_RE.findall(_unfenced(body)):
        if any(marker in gap.lower() for marker in SELF_REFERENCE_MARKERS):
            continue
        out.append(whole)
    return out


@pytest.mark.parametrize("skill", SKILLS)
def test_no_cross_skill_step_number_citations(skill):
    """Citing a sibling by internal step number is the form this check replaces."""
    d = SKILLS_DIR / skill
    for f in [d / "SKILL.md", *sorted((d / "references").glob("*.md"))]:
        if not f.is_file():
            continue
        hits = step_number_citations(f.read_text())
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


def test_step_number_check_ignores_a_self_reference():
    """`invoke minerva:replan, return to step 3` cites THIS skill's step 3.

    Flagging it would push authors to reword correct prose to satisfy a false positive.
    """
    assert not step_number_citations("trigger `minerva:replan`, return to step 3")
    assert not step_number_citations("then re-run step 4 of this protocol")
    assert step_number_citations("per `minerva:promote` Mode A step 7")


def test_step_number_check_catches_a_citation_phrased_with_a_comma():
    """The false negative a blanket comma ban produced.

    A genuine cross-skill citation can be phrased with a natural comma, and banning
    commas in the gap silenced it — the check would have passed forever on the exact
    defect it exists to catch.
    """
    assert step_number_citations("See `minerva:promote`, step 5 for details")


def test_step_number_check_catches_a_citation_whose_sentence_starts_with_a_marker():
    """The mirror defect a whole-sentence marker scan would introduce.

    "re-run" here belongs to the leading clause, not to the gap between the skill
    mention and the step reference — so this IS a cross-skill citation and must be
    caught. Scoping the marker scan to the gap is what keeps both cases right.
    """
    assert step_number_citations("re-run `minerva:promote`'s step 3")
    assert step_number_citations("go back to the top, then see `minerva:review` step 2")


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


# --- The four intake pre-flight blocks ----------------------------------------
#
# The in-flight collision protocol was extracted to one shared file
# (`propose/references/in-flight-check.md`) and the four orchestrator blocks that
# used to restate it inline now cite it. The blocks are NOT copies, and that is
# deliberate — `2026-08-22-pattern-repeated-blocks-may-be-deliberate-divergence-not-duplication`.
# Each orchestrator's block carries a qualifier that is true only of that rung:
# who adjudicates the run's other gates, and how much user contact the rung permits
# at all. A later "let's dedupe these" pass that flattens them into one generic
# citation line would erase exactly that, silently.
#
# So byte-identity is the wrong invariant here too. What is asserted instead is the
# pair that must hold together: every block reaches the ONE shared protocol, and
# every block still says the thing only it says.
PREFLIGHT_BLOCKS = {
    "propose-ship": ("references/phases.md", "## Pre-flight: detect in-flight work"),
    "propose-ship-quick": ("SKILL.md", "## Pre-flight: in-flight work collision"),
    "propose-ship-balanced": ("SKILL.md", "## Pre-flight: in-flight work collision"),
    "propose-ship-auto": ("SKILL.md", "## Pre-flight: in-flight work collision"),
}

# The per-rung qualifier each block must keep. Losing one is not a wording nit: it
# is the sentence that tells a run how much it is allowed to bother the user.
PREFLIGHT_QUALIFIERS = {
    "propose-ship": "foot-cannon",
    "propose-ship-quick": "only guaranteed",
    "propose-ship-balanced": "only mandatory pre-run user interaction",
    "propose-ship-auto": "only permitted",
}

# The second half of each rung's qualifier: WHO adjudicates the run's other gates.
# `propose-ship` is human-gated end to end, so it has no adjudicator clause to keep —
# mapped to None rather than omitted, so the enumeration still covers all four blocks
# and a dropped entry cannot look like an intentional exemption.
PREFLIGHT_ADJUDICATORS = {
    "propose-ship": None,
    "propose-ship-quick": "**not** main-model-decided",
    "propose-ship-balanced": "**not** main-model-decided",
    "propose-ship-auto": "**not** panel-decided",
}

SHARED_PREFLIGHT_REF = "plugins/minerva/skills/propose/references/in-flight-check.md"


def block_keeps_qualifier(block: str, qualifier: str) -> bool:
    """Whether `block` still carries `qualifier`. One definition, so the real check and
    its negative coverage cannot drift apart about what "kept" means."""
    return qualifier in block


def preflight_block(skill: str) -> str:
    """The pre-flight section of `skill`, up to the next heading."""
    rel, heading = PREFLIGHT_BLOCKS[skill]
    path = SKILLS_DIR / skill / rel
    m = re.search(rf"^{re.escape(heading)}\n(.*?)(?=^## |\Z)", path.read_text(), re.S | re.M)
    assert m, f"{skill}: no '{heading}' section in {rel}"
    return m.group(1)


def test_all_four_preflight_blocks_exist():
    """Guards the enumeration itself — a silently-empty locator would make every
    check below pass vacuously (`2026-08-10-pattern-presence-assertions-rot-into-green-lies`)."""
    assert len(PREFLIGHT_BLOCKS) == 4
    for skill in PREFLIGHT_BLOCKS:
        assert preflight_block(skill).strip(), f"{skill}: empty pre-flight block"


@pytest.mark.parametrize("skill", sorted(PREFLIGHT_BLOCKS))
def test_preflight_block_cites_the_shared_protocol(skill):
    """One protocol, four citations — no orchestrator restates it inline again."""
    block = preflight_block(skill)
    assert SHARED_PREFLIGHT_REF in block, (
        f"{skill}: pre-flight block does not cite {SHARED_PREFLIGHT_REF}; a rung that "
        "restates the protocol inline drifts from the other three")


@pytest.mark.parametrize("skill", sorted(PREFLIGHT_BLOCKS))
def test_preflight_block_keeps_its_own_qualifier(skill):
    """The deliberate divergence, enforced.

    Without this, collapsing four blocks to one shared citation is indistinguishable
    from collapsing them to one shared *sentence* — and the rung-specific clause about
    permitted user contact is the first thing such a pass would drop.
    """
    qualifier = PREFLIGHT_QUALIFIERS[skill]
    block = preflight_block(skill)
    assert block_keeps_qualifier(block, qualifier), (
        f"{skill}: pre-flight block lost its rung-specific qualifier {qualifier!r} — "
        "the four blocks diverge on purpose; do not flatten them")


@pytest.mark.parametrize("skill", sorted(PREFLIGHT_BLOCKS))
def test_preflight_block_says_it_is_not_a_lock(skill):
    """`2026-08-05-pattern-read-then-act-is-not-a-lock`'s documented failure mode is
    that a check-then-act guard *looks* sufficient, so the next reader extends it
    rather than replacing it. Every block states outright that it is not a lock."""
    block = preflight_block(skill).lower()
    assert "detection, not a lock" in block, (
        f"{skill}: pre-flight block does not say the check is detection rather than a "
        "lock — the framing this whole protocol depends on")


def test_qualifiers_are_distinct():
    """Negative coverage: if the four qualifiers ever collapse to one string, the
    divergence check above would pass while asserting nothing rung-specific."""
    assert len(set(PREFLIGHT_QUALIFIERS.values())) == 4


def test_preflight_qualifier_check_fires_on_a_flattened_block():
    """Negative coverage that actually exercises the production predicate.

    Asserting on a fabricated literal would prove nothing: it would still pass if
    `block_keeps_qualifier` were gutted to `return True`. Both the real check and this
    one call the same function, so they cannot disagree about what "kept" means.
    """
    real = preflight_block("propose-ship-auto")
    qualifier = PREFLIGHT_QUALIFIERS["propose-ship-auto"]
    assert block_keeps_qualifier(real, qualifier), "the live block should pass"

    flattened = real.replace(qualifier, "")
    assert not block_keeps_qualifier(flattened, qualifier), (
        "the check does not fire on a block whose qualifier was removed")


@pytest.mark.parametrize("skill", sorted(PREFLIGHT_ADJUDICATORS))
def test_preflight_block_keeps_its_adjudicator_clause(skill):
    """The other half of the divergence.

    `test_preflight_block_keeps_its_own_qualifier` pins how much user contact a rung
    permits; this pins WHO decides its other gates. Both halves distinguish the rungs,
    so testing only one leaves a flattening pass free to erase the other.
    """
    clause = PREFLIGHT_ADJUDICATORS[skill]
    block = preflight_block(skill)
    if clause is None:
        assert "panel-decided" not in block and "main-model-decided" not in block, (
            f"{skill}: human-gated rung acquired an adjudicator clause — if that is "
            "intentional, add it to PREFLIGHT_ADJUDICATORS rather than leaving it untested")
        return
    assert clause in block, (
        f"{skill}: pre-flight block lost its adjudicator clause {clause!r} — the four "
        "blocks diverge on purpose; do not flatten them")


def test_adjudicator_clauses_cover_every_preflight_block():
    """The two divergence checks must span the same four blocks; a block present in one
    enumeration and missing from the other would be half-guarded and look fully guarded."""
    assert set(PREFLIGHT_ADJUDICATORS) == set(PREFLIGHT_BLOCKS)


# The four blocks also share a two-sentence SUMMARY of the protocol, written once and
# pasted into each. That part is meant to be identical — unlike the qualifiers above,
# which are meant to differ. `2026-08-22-pattern-repeated-blocks-may-be-deliberate-divergence-not-duplication`
# says to read the copies before choosing the invariant: here the copies genuinely split
# into a shared half and a divergent half, so the two halves get opposite invariants.
# Byte-identity on the shared half is exactly right; applying it to the whole block would
# be the vacuous test that entry warns about.
#
# Without this, a fifth evidence source (or a reworded framing) in in-flight-check.md
# leaves four stale summaries and nothing goes red.
SHARED_SUMMARY_MARKERS = (
    "It reads four evidence sources",
    "each failing soft",
    "detection, not a lock",
    "serializes only sessions choosing the *same slug*",
)


SUMMARY_END = "not that nobody else is working the goal."


def shared_summary(skill: str) -> str:
    """The block's shared summary — from the read directive to the end of the
    not-a-lock sentence. Deliberately EXCLUDES the rung-specific lead and tail: those
    are meant to diverge and are pinned separately by the qualifier checks above."""
    block = preflight_block(skill)
    start = block.index("**Read `" + SHARED_PREFLIGHT_REF)
    end = block.index(SUMMARY_END, start) + len(SUMMARY_END)
    return block[start:end]


@pytest.mark.parametrize("skill", sorted(PREFLIGHT_BLOCKS))
def test_shared_summary_states_every_marker(skill):
    """Each copy carries the whole shared framing, not a truncated paraphrase."""
    summary = shared_summary(skill)
    missing = [m for m in SHARED_SUMMARY_MARKERS if m not in summary]
    assert not missing, f"{skill}: shared summary is missing {missing}"


def test_shared_summary_is_identical_across_the_autonomous_rungs():
    """The three autonomous orchestrators paste the same summary; drift between them is
    always a mistake, so byte-identity is the correct invariant for this half."""
    rungs = ["propose-ship-quick", "propose-ship-balanced", "propose-ship-auto"]
    summaries = {s: shared_summary(s).strip() for s in rungs}
    first = summaries[rungs[0]]
    for skill, text in summaries.items():
        assert text == first, (
            f"{skill}'s shared pre-flight summary has drifted from "
            f"{rungs[0]}'s; the summary half is meant to be identical")


def test_summary_source_count_matches_the_protocol_file():
    """The summary says 'four evidence sources'. Pin that against the protocol file's
    actual step count, so adding a fifth source cannot leave four stale summaries."""
    protocol = (SKILLS_DIR / "propose" / "references" / "in-flight-check.md").read_text()
    headings = dict(re.findall(r"^## Step ([0-9]) — (.+)$", protocol, re.M))
    # Steps 1-4 are the evidence sources; step 5 is the match bar, which is where the
    # run of sources ends. A fifth source would push the match bar to step 6.
    assert set("1234") <= set(headings), f"missing evidence-source steps: {headings}"
    assert "match bar" in headings.get("5", "").lower(), (
        f"step 5 is {headings.get('5')!r}, not the match bar — the evidence-source run "
        "is no longer four long, but every orchestrator summary says 'four evidence "
        "sources'; update the summaries")


# --- propose-ship-balanced: the one-dispatch cap is gone, and must stay gone ----------
#
# `2026-09-05-decision-balanced-rechecks-its-folds` replaced "one dispatch per gate, no
# revision-round re-dispatch" with "one review dispatch plus one fold-audit re-check after a
# fold — never a third". A positive anchor on the new wording lives in the contract; this is
# the INVERTED half (`2026-08-10-pattern-presence-assertions-rot-into-green-lies`): the old
# cap must appear in no file under the skill, so a stale sentence that survived the rewrite —
# or gets pasted back from an older copy — goes red rather than quietly contradicting the
# re-check it forbids.
RETIRED_BALANCED_CAP_PHRASES = [
    "no revision-round re-dispatch",
    "at most one reviewer dispatch per gate",
    "one dispatch per gate",
]


def _balanced_prose_files():
    root = SKILLS_DIR / "propose-ship-balanced"
    return sorted(p for p in root.rglob("*.md"))


def test_balanced_files_enumerated():
    """Guards the enumeration: an empty file set would make the inverted check vacuous."""
    files = _balanced_prose_files()
    assert {p.name for p in files} >= {"SKILL.md", "verify-protocol.md", "phases.md", "governance.md"}


@pytest.mark.parametrize("phrase", RETIRED_BALANCED_CAP_PHRASES)
def test_balanced_no_longer_states_the_one_dispatch_cap(phrase):
    offenders = [
        str(p.relative_to(SKILLS_DIR)) for p in _balanced_prose_files()
        if _present(phrase, p.read_text(encoding="utf-8"), ignore_case=True)
    ]
    assert not offenders, (
        f"retired cap phrase {phrase!r} still appears in {offenders}; balanced now allows one "
        "fold-audit re-check after a fold — see verify-protocol.md 'Re-check after a fold'"
    )


def test_balanced_states_the_recheck_cap():
    """The positive half, so the pair cannot both pass on a file that says nothing."""
    body = (SKILLS_DIR / "propose-ship-balanced" / "references" / "verify-protocol.md").read_text()
    assert "Re-check after a fold" in body and "never a third" in body
