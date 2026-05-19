"""Structural validation for the minerva plugin.

These tests verify file layout, JSON validity, and the presence of key
frontmatter / behavior keywords. They do not exercise runtime behavior —
the plugin is pure-markdown protocol executed by Claude.
"""
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_DIR = REPO_ROOT / "plugins" / "minerva"

SKILLS_DIR = PLUGIN_DIR / "skills"


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
    for skill in ["minerva:init", "minerva:propose", "minerva:replan", "minerva:work", "minerva:promote"]:
        assert skill in readme, f"root README must mention {skill}"


def test_root_readme_does_not_mention_feature_cycle():
    readme = (REPO_ROOT / "README.md").read_text()
    assert "feature-cycle" not in readme, "feature-cycle was superseded by minerva"


def _read_skill(name: str) -> tuple[dict, str]:
    """Parse a skill SKILL.md file's frontmatter and body."""
    text = (SKILLS_DIR / name / "SKILL.md").read_text()
    assert text.startswith("---\n"), f"{name}/SKILL.md missing frontmatter"
    _, frontmatter, body = text.split("---\n", 2)
    fm = {}
    for line in frontmatter.strip().splitlines():
        key, _, value = line.partition(":")
        fm[key.strip()] = value.strip()
    return fm, body


def test_propose_skill_exists_with_frontmatter():
    fm, body = _read_skill("propose")
    assert fm.get("name") == "propose", "propose/SKILL.md must have name: propose"
    assert fm.get("description"), "propose/SKILL.md must have a description in frontmatter"
    assert "proposal.md" in body
    assert ".minerva/work/" in body, "propose skill must use the .minerva/work/ layout"
    assert "brainstorm" in body.lower() or "questions one at a time" in body.lower()
    assert "scratchpad.md" in body


def test_replan_skill_exists_with_frontmatter():
    fm, body = _read_skill("replan")
    assert fm.get("name") == "replan", "replan/SKILL.md must have name: replan"
    assert fm.get("description"), "replan/SKILL.md must have a description in frontmatter"
    assert "replan.md" in body
    assert ".minerva/work/" in body, "replan skill must use the .minerva/work/ layout"
    assert "Original plan" in body
    assert "What changed" in body
    assert "New plan" in body
    assert "most-recently-modified" in body.lower() or "most recently modified" in body.lower()


def test_work_skill_exists_with_frontmatter():
    fm, body = _read_skill("work")
    assert fm.get("name") == "work", "work/SKILL.md must have name: work"
    assert fm.get("description"), "work/SKILL.md must have a description in frontmatter"
    assert "scratchpad.md" in body
    assert "proposal.md" in body
    assert "replan.md" in body
    assert ".minerva/work/" in body, "work skill must use the .minerva/work/ layout"
    assert "minerva:replan" in body
    assert "diverge" in body.lower() or "divergence" in body.lower()
    assert "resume" in body.lower() or "left off" in body.lower()


def test_init_skill_exists_with_frontmatter():
    fm, body = _read_skill("init")
    assert fm.get("name") == "init", "init/SKILL.md must have name: init"
    assert fm.get("description"), "init/SKILL.md must have a description in frontmatter"
    assert ".minerva/work/" in body
    assert ".minerva/knowledge/" in body
    assert ".gitkeep" in body
    assert ".gitignore" in body
    assert "CLAUDE.md" in body
    assert "AGENTS.md" in body
    assert "Routing" in body or "## minerva" in body
    assert "idempotent" in body.lower() or "idempotency" in body.lower() or "already initialized" in body.lower()
    assert "flat layout" in body.lower() or "mv work" in body or "pre-existing" in body.lower()


def test_promote_skill_exists_with_frontmatter():
    fm, body = _read_skill("promote")
    assert fm.get("name") == "promote", "promote/SKILL.md must have name: promote"
    assert fm.get("description"), "promote/SKILL.md must have a description in frontmatter"
    assert "end-of-work" in body.lower() or "end of work" in body.lower()
    assert "single-item" in body.lower() or "single item" in body.lower() or "with argument" in body.lower()
    assert "PROMOTE" in body
    assert "DISCARD" in body
    assert "idempotent" in body.lower() or "idempotency" in body.lower()
    assert ".minerva/knowledge/" in body, "promote skill must use the .minerva/knowledge/ layout"
    assert ".minerva/work/" in body, "promote skill must use the .minerva/work/ layout"
    assert "new engineer" in body.lower() or "year" in body.lower()


def test_plugin_readme_lists_all_skills():
    readme = (PLUGIN_DIR / "README.md").read_text()
    for skill in ["minerva:propose", "minerva:replan", "minerva:work", "minerva:promote"]:
        assert skill in readme, f"plugin README must list {skill}"
    assert "decisions" in readme.lower()
    assert "scratchpad" in readme.lower()
    assert ".minerva/work/" in readme, "README file-layout must use .minerva/work/"
    assert ".minerva/knowledge/" in readme, "README file-layout must use .minerva/knowledge/"


def test_using_minerva_skill_exists_with_frontmatter():
    skill_path = PLUGIN_DIR / "skills" / "using-minerva" / "SKILL.md"
    assert skill_path.is_file(), f"missing: {skill_path}"
    text = skill_path.read_text()
    assert text.startswith("---\n"), "SKILL.md must start with YAML frontmatter"
    _, frontmatter, body = text.split("---\n", 2)
    assert "name: using-minerva" in frontmatter
    assert "description:" in frontmatter
    assert ".minerva" in frontmatter, "trigger description must mention .minerva/ as the detection signal"
    for skill in ["minerva:propose", "minerva:replan", "minerva:work", "minerva:promote"]:
        assert skill in body, f"using-minerva must mention {skill}"
    assert ".minerva/work/" in body
    assert ".minerva/knowledge/" in body
    assert "anti-pattern" in body.lower() or "when not to use" in body.lower() or "NOT to use" in body
