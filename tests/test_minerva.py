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
