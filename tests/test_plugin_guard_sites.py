"""Every PLUGIN_SCRIPTS resolution site is guarded, and a new one is a deliberate registration.

`PLUGIN_SCRIPTS` resolves through `~/.claude/plugins/minerva`, which on a self-hosting checkout is
a symlink to the PRIMARY checkout — so a snippet run while working in a linked worktree executes
that checkout's branch rather than the code being edited. `scripts/plugin_guard.py` turns the
silent half of that into a non-zero exit; this module makes sure no site is missing it.

Structured after `tests/test_skill_dispatch.py`: enumerate the sites, require the property, and
**pin the set**, so adding a resolution site is a conscious act rather than a silent omission.
That pinning is the part that survives — a bare "every site found by grep has a guard" passes
vacuously the day someone writes a site the grep does not match.
"""
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "plugins" / "minerva" / "skills"

# Every file that resolves the scripts directory. Adding a row here is the registration; CI fails
# until the guard is actually present.
#
# Deliberately files, not (file, module) pairs. The first version of this set paired each file with
# one module name, which made a real hole invisible: `cleanup/references/reconciliation.md` runs
# BOTH `knowledge_lint` and `synthesis_status`, and only the first was registered or guarded. The
# guard now compares the whole scripts directory, so there is no module to pair and no second
# module to forget.
REGISTERED_SITES = {
    "propose/references/on-approval.md",
    "lint/SKILL.md",
    "migrate-fix/SKILL.md",
    "status/SKILL.md",
    "cleanup/references/reconciliation.md",
    "cleanup/references/phased-units.md",
    "migrate/SKILL.md",
    "lint-fix/SKILL.md",
    "ship/references/protocol.md",
    "synthesize/SKILL.md",
}

_RESOLVE_RE = re.compile(r"PLUGIN_SCRIPTS=\$\(find")
_GUARD_RE = re.compile(r'python3 "\$PLUGIN_SCRIPTS/plugin_guard\.py"')


def _docs():
    return sorted(p for p in SKILLS.rglob("*.md"))


def _resolving_files():
    return {p for p in _docs() if _RESOLVE_RE.search(p.read_text())}


def test_the_registered_set_matches_reality():
    """A new resolution site must be registered, not silently unguarded."""
    found = {str(p.relative_to(SKILLS)) for p in _resolving_files()}
    registered = set(REGISTERED_SITES)
    assert found == registered, (
        f"unregistered resolution sites: {sorted(found - registered)}; "
        f"registered but absent: {sorted(registered - found)}"
    )


@pytest.mark.parametrize("rel", sorted(REGISTERED_SITES))
def test_every_resolution_is_guarded(rel):
    """One guard per resolution. Counted, not merely present: a file with two resolution sites
    (`lint/SKILL.md`, `lint-fix/SKILL.md`) must carry two guards, or one path is unprotected."""
    text = (SKILLS / rel).read_text()
    assert len(_GUARD_RE.findall(text)) == len(_RESOLVE_RE.findall(text)), (
        f"{rel}: {len(_RESOLVE_RE.findall(text))} resolution site(s) but "
        f"{len(_GUARD_RE.findall(text))} guard(s)"
    )


@pytest.mark.parametrize("rel", sorted(REGISTERED_SITES))
def test_each_resolution_line_is_paired_with_a_guard(rel):
    """One guard per resolution, positioned so it runs BEFORE the call it protects.

    Two shapes exist and both are legal: the assignment on its own line (guard on the next line),
    or the assignment sharing a line with the `python3` call it feeds (guard injected inline
    before that call). What is illegal is a resolution with no guard reachable from it — and,
    specifically, a guard placed *after* a same-line call, which would run too late.
    """
    lines = (SKILLS / rel).read_text().splitlines()
    for i, line in enumerate(lines):
        if not _RESOLVE_RE.search(line):
            continue
        if "python3 -c" in line or re.search(r'; python3 "', line):
            assert _GUARD_RE.search(line), (
                f"{rel}:{i+1} resolves and calls on one line but carries no inline guard"
            )
            # the guard must precede the call it protects
            call = re.search(r'; python3 (?:-c |")', line)
            assert call and line.index("plugin_guard.py") < call.start() + len("; python3"), (
                f"{rel}:{i+1} guard is positioned after the call it should protect"
            )
        else:
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            assert _GUARD_RE.search(nxt), (
                f"{rel}:{i+1} resolves PLUGIN_SCRIPTS but the next line is not a guard"
            )


def test_no_guard_reintroduces_the_root_interpolation():
    """`tests/test_skill_snippets.py` byte-substitutes inside the `python3 -c` payload and then
    asserts no `$ROOT` survives. A guard written as `${PLUGIN_SCRIPTS:-$ROOT/scripts}` tripped
    that on the first attempt; the guard deliberately has no `$ROOT` fallback, which is also
    correct semantically — when PLUGIN_SCRIPTS is empty the fallback IS the working tree, so
    there is nothing to diverge from."""
    invocation = re.compile(r'\[ -n "\$PLUGIN_SCRIPTS" \][^;]*;[^}]*\}')
    for p in _resolving_files():
        for m in invocation.finditer(p.read_text()):
            # Scoped to the guard invocation itself: a combined line legitimately carries $ROOT
            # in its own `ROOT=` assignment and in the program body it feeds.
            assert "$ROOT" not in m.group(0), (
                f"{p.relative_to(SKILLS)}: guard reintroduced $ROOT: {m.group(0)}")
