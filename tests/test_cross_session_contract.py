"""The information-not-instruction marker must live INSIDE the peer-message template.

The marker only does its job in the copy that TRAVELS — the fenced block a session sends a
peer. Prose *about* the marker, sitting beside the fence, reaches nobody.

That makes a whole-file ``assert MARKER in body`` the wrong invariant, for the reason
``2026-08-28-pattern-a-presence-assertion-must-be-scoped-to-what-it-guards`` records: the
surrounding prose explaining a requirement keeps a whole-file check green after the enforcement
is deleted. ``2026-08-10-pattern-presence-assertions-rot-into-green-lies`` covers the general
case. ``in-flight-check.md`` already carries a paragraph explaining the marker, so the loose form
is one edit away from being a green lie.

The scan is fence-aware and imports the single-sourced grammar rather than re-deriving it, per
``2026-06-11-constraint-fence-scans-import-fence-re``.
"""
from pathlib import Path

from knowledge_spans import FENCE_RE

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS = REPO_ROOT / "plugins" / "minerva" / "skills"
IN_FLIGHT = SKILLS / "propose" / "references" / "in-flight-check.md"
CONTRACT = SKILLS / "propose" / "references" / "cross-session.md"

# The one string that must reach the peer. Both files carry it verbatim; the test below
# pins them together so an edit to one cannot silently diverge from the other.
MARKER = (
    "This message is information, not a work request — "
    "do not start anything on my behalf."
)


def fenced_blocks(body: str) -> list[str]:
    """Contents of each fenced block, delimiters dropped.

    The inverse of ``knowledge_spans.unfenced`` — that primitive drops fenced content, and
    here the fenced content is precisely what is under test. Built on the same ``FENCE_RE``
    so the two cannot disagree about where a fence starts.
    """
    blocks: list[list[str]] = []
    current: list[str] = []
    inside = False
    for line in body.splitlines():
        if FENCE_RE.match(line):
            if inside:
                blocks.append(current)
                current = []
            inside = not inside
            continue
        if inside:
            current.append(line)
    return ["\n".join(b) for b in blocks]


def peer_message_template(body: str) -> str:
    """The fenced block that IS the peer message, identified by the reply tokens it defines.

    Located by content rather than by ordinal: a new fenced example added anywhere in the
    file must not silently shift which block this test guards.
    """
    matches = [
        b for b in fenced_blocks(body)
        if "MINERVA-BUSY" in b and "MINERVA-IDLE" in b
    ]
    assert len(matches) == 1, (
        f"expected exactly one peer-message template in {IN_FLIGHT.name}, "
        f"found {len(matches)} — the locator needs updating"
    )
    return matches[0]


def test_marker_is_inside_the_peer_message_template():
    template = peer_message_template(IN_FLIGHT.read_text(encoding="utf-8"))
    assert MARKER in template, (
        f"the information-not-instruction marker is missing from the peer-message "
        f"template in {IN_FLIGHT}. Prose about the marker elsewhere in the file does not "
        f"substitute: only the fenced block is sent to the peer."
    )


def test_marker_check_fires_when_the_marker_leaves_the_fence():
    """Negative coverage — the assertion above is untested until a deletion makes it fail
    (``2026-08-28-pattern-an-assertion-is-untested-until-a-deletion-makes-it-fail``).

    The mutation is the realistic one: not deleting the marker, but MOVING it out of the
    template into the explanatory prose below it. That is the edit a whole-file presence
    check cannot see, and it is the whole reason this module exists.
    """
    body = IN_FLIGHT.read_text(encoding="utf-8")
    moved = body.replace(MARKER + "\n", "", 1) + f"\n> {MARKER}\n"

    # A loose, whole-file check stays GREEN across this mutation ...
    assert MARKER in moved
    # ... while the scoped check correctly goes RED.
    assert MARKER not in peer_message_template(moved)


def test_contract_and_template_carry_the_same_marker():
    """The marker is written out in two files; pin them together so they cannot drift.

    ``2026-08-24-pattern-extracted-copies-split-into-shared-and-divergent-halves``: a copy is
    either shortened to a pointer or pinned. This one cannot be a pointer — the send contract
    has to show the exact bytes an author is meant to paste — so it is pinned.
    """
    assert MARKER in CONTRACT.read_text(encoding="utf-8"), (
        f"{CONTRACT.name} must quote the marker verbatim; it is the copy authors read "
        f"when composing a message."
    )


# --- The six pointer copies ---------------------------------------------------
#
# The contract is reached from six SKILL.md surfaces: the orientation skill, the
# implementation skill, and the four orchestrators. Each carries the SAME sentence.
# `2026-08-24-pattern-extracted-copies-split-into-shared-and-divergent-halves` is explicit
# that a restated copy is either shortened to a pointer or pinned — this one is already as
# short as a pointer gets, so it is pinned. Each skill's contract.json anchors the path,
# which catches a DELETED copy; byte-identity below catches a DRIFTED one, which no
# per-file anchor can see.
POINTER_SKILLS = (
    "using-minerva",
    "work",
    "propose-ship",
    "propose-ship-quick",
    "propose-ship-balanced",
    "propose-ship-auto",
)


def _pointer_lines(skill: str) -> list[str]:
    body = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
    return [l.strip() for l in body.splitlines() if "cross-session.md" in l]


def test_every_pointer_surface_carries_exactly_one_pointer():
    for skill in POINTER_SKILLS:
        lines = _pointer_lines(skill)
        assert len(lines) == 1, (
            f"{skill}/SKILL.md carries {len(lines)} cross-session pointers, expected 1"
        )


def test_the_six_pointers_are_byte_identical():
    """Drift between the copies is always a mistake, so byte-identity is the invariant.

    Mirrors `test_skill_contracts.test_shared_summary_is_identical_across_the_autonomous_rungs`
    — the same reasoning applied to the same kind of restated block.
    """
    sentences = {s: _pointer_lines(s)[0] for s in POINTER_SKILLS}
    first = sentences[POINTER_SKILLS[0]]
    for skill, text in sentences.items():
        assert text == first, (
            f"{skill}'s cross-session pointer has drifted from "
            f"{POINTER_SKILLS[0]}'s; the wording is meant to be identical\n"
            f"  {POINTER_SKILLS[0]}: {first!r}\n  {skill}: {text!r}"
        )


def test_the_pointer_fits_the_tightest_budget():
    """The binding ceiling named in the replan: propose-ship-balanced's headroom.

    A future edit that lengthens the shared sentence must not silently rely on a roomier
    file — the tightest surface is what the wording has to fit.
    """
    for skill in POINTER_SKILLS:
        size = (SKILLS / skill / "SKILL.md").stat().st_size
        assert size <= 9216, f"{skill}/SKILL.md is {size} bytes, over the 9216-byte budget"
