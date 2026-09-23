"""Installer acceptance with disposable config and stubbed external CLIs."""
import json
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

import install_plugin as installer

REPO = Path(__file__).resolve().parents[1]


@pytest.fixture
def repo(tmp_path):
    dest = tmp_path / "marketplace with spaces"
    for relative in ("plugins/minerva/.claude-plugin/plugin.json",
                     "plugins/minerva/.codex-plugin/plugin.json",
                     ".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json"):
        path = dest / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / relative, path)
    return dest


@pytest.fixture
def config(tmp_path):
    return tmp_path / "isolated Claude config"


@pytest.fixture
def commands(monkeypatch):
    calls = []
    monkeypatch.setattr(installer.shutil, "which", lambda tool: "/stub/" + tool)
    def run(command, **kwargs):
        calls.append(command)
        if command[:3] == [sys.executable, "-c", "import playwright"]:
            return SimpleNamespace(returncode=1)
        return SimpleNamespace(returncode=0, stdout="fixture-commit-sha\n")
    monkeypatch.setattr(installer.subprocess, "run", run)
    return calls


def test_default_install_registers_claude_manifest_version(repo, config, commands):
    assert installer.main(["minerva", "--repo", str(repo), "--claude-config-dir", str(config)]) == 0
    settings = json.loads((config / "settings.json").read_text())
    assert settings["enabledPlugins"] == {"minerva@agent-marketplace": True}
    installed = json.loads((config / "plugins/installed_plugins.json").read_text())
    assert installed["plugins"]["minerva@agent-marketplace"][0]["version"] == "2.0.0"
    assert (config / "plugins/minerva").resolve() == repo / "plugins/minerva"
    assert (config / "plugins/marketplaces/agent-marketplace").resolve() == repo
    assert not any(command[0] == "codex" for command in commands)


def test_upgrade_and_repeat_preserve_other_settings_and_scopes(repo, config, commands):
    config.mkdir()
    (config / "settings.json").write_text(json.dumps({
        "theme": "custom", "enabledPlugins": {"unrelated@other": False},
        "plugins": ["unrelated/path", str(config / "plugins/minerva")],
    }))
    (config / "plugins").mkdir()
    (config / "plugins/known_marketplaces.json").write_text('{"other": {"custom": true}}')
    (config / "plugins/installed_plugins.json").write_text(json.dumps({"version": 2, "plugins": {
        "unrelated@other": [{"scope": "user", "version": "old"}],
        "minerva@agent-marketplace": [
            {"scope": "project", "version": "project-version"},
            {"scope": "user", "version": "1.0.0", "installedAt": "original", "custom": True}],
    }}))
    for _ in range(2):
        installer.install(repo, "minerva", "claude", config)
    settings = json.loads((config / "settings.json").read_text())
    assert settings["theme"] == "custom"
    assert settings["plugins"] == ["unrelated/path"]
    assert settings["enabledPlugins"]["unrelated@other"] is False
    known = json.loads((config / "plugins/known_marketplaces.json").read_text())
    assert known["other"] == {"custom": True}
    entries = json.loads((config / "plugins/installed_plugins.json").read_text())["plugins"]
    assert entries["unrelated@other"] == [{"scope": "user", "version": "old"}]
    assert entries["minerva@agent-marketplace"][0]["scope"] == "project"
    assert entries["minerva@agent-marketplace"][1]["installedAt"] == "original"
    assert entries["minerva@agent-marketplace"][1]["custom"] is True
    assert len(entries["minerva@agent-marketplace"]) == 2


def test_codex_install_uses_supported_commands_and_leaves_claude_untouched(repo, config, commands):
    installer.install(repo, "minerva", "codex", config)
    assert not config.exists()
    assert [command for command in commands if command[0] == "codex"] == [
        ["codex", "plugin", "marketplace", "add", str(repo)],
        ["codex", "plugin", "add", "minerva@agent-marketplace"],
    ]


def test_both_hosts_install_and_reinstall(repo, config, commands):
    for _ in range(2):
        installer.install(repo, "minerva", "both", config)
    assert (config / "settings.json").is_file()
    assert sum(command[:3] == ["codex", "plugin", "add"] for command in commands) == 2


@pytest.mark.parametrize("host", ["claude", "codex", "both"])
def test_dry_run_has_no_configuration_or_cli_side_effects(repo, config, commands, host, capsys):
    before = sorted(repo.rglob("*"))
    installer.install(repo, "minerva", host, config, dry_run=True)
    assert json.loads(capsys.readouterr().out)["host"] == host
    assert not config.exists()
    assert sorted(repo.rglob("*")) == before
    assert commands == []


@pytest.mark.parametrize("relative", ["plugins/minerva", "plugins/marketplaces/agent-marketplace"])
def test_real_directory_conflicts_fail_before_any_registration(repo, config, commands, relative):
    conflict = config / relative
    conflict.mkdir(parents=True)
    (conflict / "keep").write_text("mine")
    with pytest.raises(ValueError, match="real directory"):
        installer.install(repo, "minerva", "claude", config)
    assert (conflict / "keep").read_text() == "mine"
    assert not (config / "settings.json").exists()
    assert commands == []


def test_missing_codex_cli_fails_both_preflight_without_claude_changes(repo, config, commands, monkeypatch):
    monkeypatch.setattr(installer.shutil, "which", lambda tool: None)
    with pytest.raises(ValueError, match="CLI is required"):
        installer.install(repo, "minerva", "both", config)
    assert not config.exists()


def test_unsupported_codex_plugin_fails_without_claude_changes(repo, config, commands):
    (repo / "plugins/minerva/.codex-plugin/plugin.json").unlink()
    with pytest.raises(ValueError, match="Codex manifest"):
        installer.install(repo, "minerva", "both", config)
    assert not config.exists()


def test_partial_codex_failure_reports_successful_claude_registration(repo, config, commands, monkeypatch, capsys):
    fake = installer.subprocess.run
    def fail(command, **kwargs):
        if command[:3] == ["codex", "plugin", "add"]:
            raise subprocess.CalledProcessError(1, command)
        return fake(command, **kwargs)
    monkeypatch.setattr(installer.subprocess, "run", fail)
    assert installer.main(["minerva", "--host", "both", "--repo", str(repo),
                           "--claude-config-dir", str(config)]) == 1
    assert (config / "settings.json").exists()
    assert "Claude registration succeeded" in capsys.readouterr().err


@pytest.mark.parametrize("payload", ["{invalid", "[]", '{"enabledPlugins": []}'])
def test_invalid_configuration_is_preserved(repo, config, commands, payload):
    config.mkdir()
    (config / "settings.json").write_text(payload)
    assert installer.main(["minerva", "--repo", str(repo), "--claude-config-dir", str(config)]) == 1
    assert (config / "settings.json").read_text() == payload
    assert not (config / "plugins").exists()


@pytest.mark.parametrize("plugin", ["../minerva", "minerva/other", "missing", "$(pwd)"])
def test_invalid_or_missing_plugin_cannot_mutate_config(repo, config, commands, plugin):
    with pytest.raises(ValueError):
        installer.install(repo, plugin, "claude", config)
    assert not config.exists()


def test_dependency_and_browser_commands_stay_argument_safe(repo, config, commands, monkeypatch):
    requirements = repo / "plugins/minerva/scripts/requirements.txt"
    requirements.parent.mkdir()
    requirements.write_text("fixture\n")
    fake = installer.subprocess.run
    def playwright(command, **kwargs):
        if command[:3] == [sys.executable, "-c", "import playwright"]:
            return SimpleNamespace(returncode=0)
        return fake(command, **kwargs)
    monkeypatch.setattr(installer.subprocess, "run", playwright)
    installer.install(repo, "minerva", "claude", config)
    assert [sys.executable, "-m", "pip", "install", "-q", "-r", str(requirements)] in commands
    assert [sys.executable, "-m", "playwright", "install", "chromium"] in commands


@pytest.mark.parametrize("name", ["../escape", "/absolute", "$(pwd)", None])
@pytest.mark.parametrize("host", ["claude", "codex", "both"])
def test_malformed_marketplace_name_fails_preflight(repo, config, commands, name, host):
    relative = ".claude-plugin/marketplace.json" if host != "codex" else ".agents/plugins/marketplace.json"
    path = repo / relative
    value = json.loads(path.read_text())
    value["name"] = name
    path.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="marketplace"):
        installer.install(repo, "minerva", host, config)
    assert not config.exists()
    assert commands == []


def test_malformed_installed_entries_fail_before_mutation(repo, config, commands):
    plugins = config / "plugins"
    plugins.mkdir(parents=True)
    path = plugins / "installed_plugins.json"
    original = '{"plugins": {"minerva@agent-marketplace": [null]}}'
    path.write_text(original)
    assert installer.main(["minerva", "--repo", str(repo), "--claude-config-dir", str(config)]) == 1
    assert path.read_text() == original
    assert not (config / "settings.json").exists()
    assert commands == []


def test_existing_unversioned_utils_plugin_keeps_default_claude_install(repo, config, commands):
    path = repo / "plugins/utils/.claude-plugin/plugin.json"
    path.parent.mkdir(parents=True)
    shutil.copyfile(REPO / "plugins/utils/.claude-plugin/plugin.json", path)
    installer.install(repo, "utils", "claude", config)
    entries = json.loads((config / "plugins/installed_plugins.json").read_text())["plugins"]
    assert entries["utils@agent-marketplace"][0]["version"] == "1.0.0"
    assert not any(command[0] == "codex" for command in commands)
