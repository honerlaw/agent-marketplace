"""Enforces the fence-awareness constraint over `plugins/minerva/scripts/`.

`2026-06-11-constraint-fence-scans-import-fence-re` says any scan over markdown must use
the single-sourced fence grammar. It was prose with nothing behind it, and it kept being
violated — both readers in `work_status.py` shipped fence-blind past three reviewers, and
`knowledge_fix.plan_index` scanned `index.md` fence-blind while `knowledge_lint.parse_index`
scanned the same file fence-aware. Every skill in this repo that documents a convention
contains a fenced example of it, so a fence-blind scan reads documentation as data.

The rule is deny-by-default and asks the corpus rather than naming the modules that matter:
a hand-maintained list of "things that scan markdown" is the artifact
`2026-08-11-pattern-the-enumeration-is-what-fails` describes, and it would decay in the
dangerous direction, since a module missing from it reads as checked. The escape hatch is a
`# not-markdown: <reason>` marker on the scanning line, so a justified exemption lives next
to the code it excuses instead of in this file.

**Granularity, stated so the gate is not overclaimed.** The fence-aware check is per
MODULE, not per scan: a module that references the grammar anywhere satisfies it, so a
second, fence-blind scan added to an already-aware module would pass. Per-scan checking
would need real dataflow — whether *this* iteration reads markdown, and whether it goes
through a helper defined elsewhere — and a static approximation would fire on the fence
helper's own `splitlines()`. Module granularity is what both real violations needed
(`work_status.py` had no grammar at all; `knowledge_fix.py` had dropped its import), so
this catches the observed class and not a narrower one inside an aware module.
"""
import re
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parent.parent / "plugins" / "minerva" / "scripts"
# Any reference to the shared grammar, or a helper built on it.
# `unfenced` is the shared scan primitive; the older names are helpers built on it.
FENCE_AWARE_RE = re.compile(r"FENCE_RE|unfenced|_strip_fences|_nonfenced")
SPLIT_RE = re.compile(r"\.splitlines\(\)")
EXEMPT_RE = re.compile(r"#\s*not-markdown:\s*(\S.*)$")

# Every module, no name filter. A deny-by-default gate that quietly skips a filename
# pattern is the gap it exists to close.
MODULES = sorted(SCRIPTS.glob("*.py"))


def scanning_lines(text: str):
    """Lines that iterate text line-by-line, paired with any exemption marker."""
    return [(i + 1, ln) for i, ln in enumerate(text.splitlines()) if SPLIT_RE.search(ln)]


@pytest.mark.parametrize("path", MODULES, ids=lambda p: p.name)
def test_a_line_scan_is_fence_aware_or_declares_why_not(path):
    text = path.read_text()
    scans = scanning_lines(text)
    if not scans:
        return
    unexplained = [(n, ln.strip()) for n, ln in scans if not EXEMPT_RE.search(ln)]
    if unexplained and not FENCE_AWARE_RE.search(text):
        pytest.fail(
            f"{path.name} scans lines but never references the shared fence grammar.\n"
            + "\n".join(f"  line {n}: {s}" for n, s in unexplained)
            + "\n\nUse knowledge_spans.FENCE_RE (or a helper built on it), or mark the "
              "line `# not-markdown: <reason>` if it genuinely does not read markdown."
        )


@pytest.mark.parametrize("path", MODULES, ids=lambda p: p.name)
def test_every_exemption_states_a_reason(path):
    for n, ln in scanning_lines(path.read_text()):
        m = EXEMPT_RE.search(ln)
        if m:
            assert m.group(1).strip(), f"{path.name}:{n} exempts a scan with no reason"


def test_no_exemptions_are_needed_today():
    """Starts at zero. A first exemption should be a deliberate, reviewed act."""
    exempt = [f"{p.name}:{n}" for p in MODULES
              for n, ln in scanning_lines(p.read_text()) if EXEMPT_RE.search(ln)]
    assert exempt == [], f"new fence-awareness exemptions: {exempt}"


# --- Negative coverage: the check must fire on its violation class ---------------
def test_the_check_fires_on_a_fence_blind_module(tmp_path):
    """Guards against the check passing vacuously — the failure mode that makes a green
    gate worse than no gate."""
    bad = tmp_path / "bad.py"
    bad.write_text("def f(t):\n    for ln in t.splitlines():\n        pass\n")
    assert scanning_lines(bad.read_text())
    assert not FENCE_AWARE_RE.search(bad.read_text())


def test_the_check_accepts_a_declared_non_markdown_scan(tmp_path):
    ok = tmp_path / "ok.py"
    ok.write_text("def f(t):\n    for ln in t.splitlines():  # not-markdown: git log output\n"
                  "        pass\n")
    n, ln = scanning_lines(ok.read_text())[0]
    assert EXEMPT_RE.search(ln).group(1).strip() == "git log output"


# --- One fence-scan loop, and the three readers exempt from it (issue #88) --------
#
# `FENCE_RE` was single-sourced from the start; the six-line toggle loop around it was
# not, and four independent copies accumulated — in `knowledge_lint`, `work_status`,
# `test_skill_budget` and `test_skill_contracts`. They now all derive from
# `knowledge_spans.unfenced`.
#
# Three readers keep their own loop ON PURPOSE. They look like the same code and are
# not, which is the whole point of
# `2026-08-22-pattern-repeated-blocks-may-be-deliberate-divergence-not-duplication`:
# unify the copies that are copies, and leave the ones that differ.
REPO = Path(__file__).resolve().parent.parent
TOGGLE_RE = re.compile(r"FENCE_RE\.match")

# path -> why this reader cannot use the shared primitive.
FENCE_LOOP_EXEMPT = {
    "plugins/minerva/scripts/knowledge_spans.py":
        "defines the shared primitive",
    "plugins/minerva/scripts/knowledge_edits.py":
        "classifies EVERY line incl. delimiters as a boolean flag list; the byte-identity "
        "guard needs a verdict per line, not a filtered subset",
    "plugins/minerva/scripts/knowledge_rename.py":
        "KEEPS fences and fenced content in its output — it rewrites text rather than "
        "filtering it, so dropping lines would corrupt the file",
    "tests/test_skill_dispatch.py":
        "measures the fence's run length for pairing, which the shared regex does not expose",
}


# This module is the checker; its only `FENCE_RE.match` occurrence is the pattern
# literal above, not a loop. Excluded by identity rather than by an exemption entry,
# so it can never be mistaken for a reader that was granted a pass.
_CHECKER = str(Path(__file__).resolve().relative_to(REPO))


def _files_with_a_fence_toggle() -> set:
    roots = [REPO / "plugins" / "minerva" / "scripts", REPO / "tests"]
    return {
        str(f.relative_to(REPO))
        for root in roots for f in root.rglob("*.py")
        if TOGGLE_RE.search(f.read_text())
    } - {_CHECKER}


def test_only_sanctioned_readers_write_their_own_fence_loop():
    """A new `FENCE_RE.match` loop must be a deliberate, reviewed act.

    Without this the refactor is an unenforced constraint — the shape
    `2026-08-11-pattern-an-unenforced-constraint-is-aspirational` is named for, and the
    one this very cleanup exists to undo.
    """
    unexpected = _files_with_a_fence_toggle() - set(FENCE_LOOP_EXEMPT)
    assert not unexpected, (
        f"{sorted(unexpected)} write their own fence-toggle loop — use "
        "knowledge_spans.unfenced / unfenced_lines, or add the file to "
        "FENCE_LOOP_EXEMPT with the reason it genuinely differs"
    )


def test_every_fence_loop_exemption_still_exists_and_still_loops():
    """A stale exemption is a lie that reads as coverage.

    If a listed file stops looping, the entry must go — otherwise the set silently
    grows into a permission slip nobody re-checks
    (`2026-08-10-pattern-presence-assertions-rot-into-green-lies`).
    """
    looping = _files_with_a_fence_toggle()
    for path, reason in FENCE_LOOP_EXEMPT.items():
        assert (REPO / path).is_file(), f"exempt file {path} no longer exists"
        assert path in looping, (
            f"{path} is exempted from the shared fence scan but no longer writes its "
            "own loop — drop the exemption")
        assert reason.strip(), f"{path} is exempted with no stated reason"


def test_the_converged_readers_share_one_implementation():
    """The four that were unified must not have quietly re-derived."""
    from knowledge_spans import unfenced, unfenced_lines
    import knowledge_lint, work_status
    assert knowledge_lint._strip_fences is unfenced
    assert list(unfenced_lines("a\n```\nb\n```\nc")) == ["a", "c"]
    assert list(work_status._nonfenced("a\n```\nb\n```\nc")) == ["a", "c"]


def test_the_exemption_check_fires_on_a_new_unsanctioned_loop(tmp_path):
    """Negative coverage: exercise the same set difference the check runs."""
    looping = {"tests/test_skill_dispatch.py", "tests/some_new_file.py"}
    assert looping - set(FENCE_LOOP_EXEMPT) == {"tests/some_new_file.py"}
