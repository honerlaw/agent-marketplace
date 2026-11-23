"""Portable skill wiring and host-specific protections formerly pinned inline."""
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
PLUGIN = REPO / "plugins/minerva"
SKILLS = PLUGIN / "skills"
REFERENCES = SKILLS / "using-minerva/references"
# Plugins whose skills share the runtime-pointer and host-tool checks, each with the skill
# that owns its runtime contract and the files allowed to name Claude-only tools.
PLUGINS = {
    "minerva": ("using-minerva", {REFERENCES / "claude.md", SKILLS / "init/references/steps.md"}),
    "lorestrom": ("using-lorestrom", {REPO / "plugins/lorestrom/skills/using-lorestrom/references/claude.md"}),
}
ALL_SKILLS = sorted(path for plugin in PLUGINS
                    for path in (REPO / "plugins" / plugin / "skills").glob("*/SKILL.md"))


def claude_dispatch_contract(body):
    return all(token in body for token in (
        "`Agent`", "fresh context", "`subagent_type: general-purpose`",
        "`run_in_background: false`", "`model: sonnet`", "Always wait for results"))


def codex_dispatch_contract(body):
    return all(token in body for token in (
        "`fork_turns: none`", "Leave model and reasoning effort unpinned",
        "Wait for results", "reconcile only once every result is in",
        "stop this workflow with recovery", "excludes the author's arbitration reasoning"))


def test_both_manifests_expose_the_same_canonical_skill_tree_and_version():
    claude = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text())
    codex = json.loads((PLUGIN / ".codex-plugin/plugin.json").read_text())
    assert claude["name"] == codex["name"] == "minerva"
    assert claude["version"] == codex["version"] == "4.0.1"
    assert (PLUGIN / codex["skills"]).resolve() == SKILLS
    assert len(list(SKILLS.glob("*/SKILL.md"))) == 19
    catalog = json.loads((REPO / ".agents/plugins/marketplace.json").read_text())
    entry = next(p for p in catalog["plugins"] if p["name"] == "minerva")
    assert (REPO / entry["source"]["path"]).resolve() == PLUGIN


@pytest.mark.parametrize("skill", ALL_SKILLS, ids=lambda p: f"{p.parents[2].name}:{p.parent.name}")
def test_every_skill_requires_the_shared_runtime(skill):
    body = skill.read_text()
    owner = PLUGINS[skill.parents[2].name][0]
    pointer = "references/runtime.md" if skill.parent.name == owner else f"skills/{owner}/references/runtime.md"
    assert "## Runtime" in body
    assert pointer in body
    assert f"Read `{pointer}` before executing" in body


def test_claude_adapter_keeps_synchronous_fresh_sonnet_reviews():
    assert claude_dispatch_contract((REFERENCES / "claude.md").read_text())


@pytest.mark.parametrize("pin", ["`run_in_background: false`", "`model: sonnet`", "fresh context"])
def test_missing_claude_dispatch_pin_is_rejected(pin):
    body = (REFERENCES / "claude.md").read_text()
    assert not claude_dispatch_contract(body.replace(pin, ""))


def test_codex_adapter_keeps_independence_and_session_model_settings():
    assert codex_dispatch_contract((REFERENCES / "codex.md").read_text())


@pytest.mark.parametrize("pin", ["`fork_turns: none`", "Leave model and reasoning effort unpinned", "Wait for results"])
def test_missing_codex_dispatch_protection_is_rejected(pin):
    body = (REFERENCES / "codex.md").read_text()
    assert not codex_dispatch_contract(body.replace(pin, ""))


@pytest.mark.parametrize("plugin", PLUGINS)
def test_only_host_adapter_names_claude_skill_and_question_tools(plugin):
    allowed = PLUGINS[plugin][1]
    for path in (REPO / "plugins" / plugin / "skills").rglob("*.md"):
        if path in allowed:
            continue
        body = path.read_text()
        assert "AskUserQuestion" not in body, path
        assert "ScheduleWakeup" not in body, path
        assert "via the `Skill`" not in body, path


def test_every_plugin_with_skills_is_checked():
    assert {p.parents[2].name for p in ALL_SKILLS} == set(PLUGINS)
    for _, allowed in PLUGINS.values():
        assert all(path.is_file() for path in allowed)
