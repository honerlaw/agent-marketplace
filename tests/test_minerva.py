"""Plugin- and marketplace-level validation for the minerva plugin.

These tests verify plugin registration, JSON validity, and catalog-document
structure. They do not exercise runtime behavior — the plugin is pure-markdown
protocol executed by Claude.

Per-skill structural contracts (frontmatter, body anchors, and the
catalog-sync presence of each ``minerva:<skill>`` token across surfaces) live in
``test_skill_contracts.py``, driven by the declarative ``evals/<skill>/contract.json``
files. This module keeps only the non-per-skill checks.
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
    # Per-skill `minerva:<skill>` presence in the root README is enforced per skill
    # via each contract's cross_surface.root_readme clause (test_skill_contracts.py).
    readme = (REPO_ROOT / "README.md").read_text()
    assert "minerva" in readme, "root README must list minerva in the plugin table"


def test_root_readme_does_not_mention_feature_cycle():
    readme = (REPO_ROOT / "README.md").read_text()
    assert "feature-cycle" not in readme, "feature-cycle was superseded by minerva"


def test_plugin_readme_structure():
    # Per-skill `minerva:<skill>` presence in the plugin README is enforced per skill
    # via each contract's cross_surface.plugin_readme clause (test_skill_contracts.py).
    # This check covers the README's own document structure.
    readme = (PLUGIN_DIR / "README.md").read_text()
    assert "decisions" in readme.lower()
    assert "scratchpad" in readme.lower()
    assert ".minerva/work/" in readme, "README file-layout must use .minerva/work/"
    assert ".minerva/knowledge/" in readme, "README file-layout must use .minerva/knowledge/"
