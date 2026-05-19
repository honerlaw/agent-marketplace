"""Structural validation for the minerva plugin.

These tests verify file layout, JSON validity, and the presence of key
frontmatter / behavior keywords. They do not exercise runtime behavior —
the plugin is pure-markdown protocol executed by Claude.
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = REPO_ROOT / "plugins" / "minerva"


def test_plugin_json_exists_and_parses():
    plugin_json = PLUGIN_DIR / ".claude-plugin" / "plugin.json"
    assert plugin_json.is_file(), f"missing: {plugin_json}"
    data = json.loads(plugin_json.read_text())
    assert data["name"] == "minerva"
    assert "description" in data and data["description"]
    assert data["author"]["name"] == "Derek Honerlaw"


def test_marketplace_lists_minerva():
    marketplace = json.loads((REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text())
    entries = {p["name"]: p for p in marketplace["plugins"]}
    assert "minerva" in entries, "minerva not registered in marketplace.json"
    assert entries["minerva"]["source"] == "./plugins/minerva"
    assert entries["minerva"]["description"], "minerva entry must have a description"


def test_marketplace_does_not_list_feature_cycle():
    marketplace = json.loads((REPO_ROOT / ".claude-plugin" / "marketplace.json").read_text())
    names = {p["name"] for p in marketplace["plugins"]}
    assert "feature-cycle" not in names, "feature-cycle was superseded by minerva"


def test_root_readme_mentions_minerva():
    readme = (REPO_ROOT / "README.md").read_text()
    assert "minerva" in readme, "root README must list minerva in the plugin table"
    for command in ["/propose", "/replan", "/work", "/promote"]:
        assert command in readme, f"root README must mention {command}"


def test_root_readme_does_not_mention_feature_cycle():
    readme = (REPO_ROOT / "README.md").read_text()
    assert "feature-cycle" not in readme, "feature-cycle was superseded by minerva"


COMMANDS_DIR = PLUGIN_DIR / "commands"


def _read_command(name: str) -> tuple[dict, str]:
    """Parse a command markdown file's frontmatter and body."""
    text = (COMMANDS_DIR / f"{name}.md").read_text()
    assert text.startswith("---\n"), f"{name}.md missing frontmatter"
    _, frontmatter, body = text.split("---\n", 2)
    fm = {}
    for line in frontmatter.strip().splitlines():
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip()
    return fm, body


def test_propose_command_exists_with_frontmatter():
    fm, body = _read_command("propose")
    assert fm.get("description"), "propose.md must have a description in frontmatter"
    # Key behaviors from the spec
    assert "proposal.md" in body
    assert "work/" in body
    assert "brainstorm" in body.lower() or "questions one at a time" in body.lower()
    assert "scratchpad.md" in body  # the empty scratchpad is created alongside


def test_replan_command_exists_with_frontmatter():
    fm, body = _read_command("replan")
    assert fm.get("description"), "replan.md must have a description in frontmatter"
    assert "replan.md" in body
    assert "Original plan" in body
    assert "What changed" in body
    assert "New plan" in body
    assert "most-recently-modified" in body.lower() or "most recently modified" in body.lower()


def test_work_command_exists_with_frontmatter():
    fm, body = _read_command("work")
    assert fm.get("description"), "work.md must have a description in frontmatter"
    # Core behaviors per spec
    assert "scratchpad.md" in body
    assert "proposal.md" in body
    assert "replan.md" in body
    # Auto-trigger of /replan on divergence
    assert "/replan" in body
    assert "diverge" in body.lower() or "divergence" in body.lower()
    # Smart resume language
    assert "resume" in body.lower() or "left off" in body.lower()


def test_promote_command_exists_with_frontmatter():
    fm, body = _read_command("promote")
    assert fm.get("description"), "promote.md must have a description in frontmatter"
    # Both modes
    assert "end-of-work" in body.lower() or "end of work" in body.lower()
    assert "single-item" in body.lower() or "single item" in body.lower() or "with argument" in body.lower()
    # Three-way partition language
    assert "PROMOTE" in body
    assert "DISCARD" in body
    # Idempotency
    assert "idempotent" in body.lower() or "idempotency" in body.lower()
    # Decision file destination
    assert "decisions/" in body
    # Heuristic from the spec / image
    assert "new engineer" in body.lower() or "year" in body.lower()


def test_plugin_readme_lists_all_four_commands():
    readme = (PLUGIN_DIR / "README.md").read_text()
    for command in ["/propose", "/replan", "/work", "/promote"]:
        assert command in readme, f"plugin README must list {command}"
    # Persistence hierarchy concept should be present
    assert "decisions" in readme.lower()
    assert "scratchpad" in readme.lower()


def test_using_minerva_skill_exists_with_frontmatter():
    skill_path = PLUGIN_DIR / "skills" / "using-minerva" / "SKILL.md"
    assert skill_path.is_file(), f"missing: {skill_path}"
    text = skill_path.read_text()
    assert text.startswith("---\n"), "SKILL.md must start with YAML frontmatter"
    _, frontmatter, body = text.split("---\n", 2)
    # Frontmatter declares the skill
    assert "name: using-minerva" in frontmatter
    assert "description:" in frontmatter
    # Body covers the four commands
    for command in ["/propose", "/replan", "/work", "/promote"]:
        assert command in body, f"using-minerva must mention {command}"
    # Detection signals
    assert "work/" in body
    assert "decisions/" in body
    # Anti-patterns section exists
    assert "anti-pattern" in body.lower() or "when not to use" in body.lower() or "NOT to use" in body
