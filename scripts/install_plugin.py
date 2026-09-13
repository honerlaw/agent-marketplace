#!/usr/bin/env python3
"""Install a local plugin without replacing unrelated host configuration."""
from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def object_file(path: Path) -> dict:
    value = json.loads(path.read_text()) if path.exists() else {}
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path}")
    return value


def marketplace_name(value: dict) -> str:
    name = value.get("name")
    if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", name):
        raise ValueError("marketplace must have a lowercase name, not a path")
    return name


def write_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent, prefix=".install-")
    try:
        with os.fdopen(descriptor, "w") as output:
            json.dump(value, output, indent=2)
            output.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def check_link(path: Path) -> None:
    if path.exists() and not path.is_symlink():
        raise ValueError(f"refusing to replace a real directory/file: {path}")


def link(path: Path, target: Path) -> None:
    check_link(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink():
        if path.resolve() == target.resolve():
            return
        path.unlink()
    path.symlink_to(target, target_is_directory=True)


def claude_registration(repo: Path, plugin: str, config: Path) -> list[tuple[Path, dict]]:
    plugin_root = repo / "plugins" / plugin
    manifest = object_file(plugin_root / ".claude-plugin" / "plugin.json")
    if manifest.get("name") != plugin:
        raise ValueError("Claude manifest name does not match plugin")
    marketplace = marketplace_name(object_file(repo / ".claude-plugin" / "marketplace.json"))
    key = f"{plugin}@{marketplace}"
    plugins = config / "plugins"
    check_link(plugins / plugin)
    check_link(plugins / "marketplaces" / marketplace)
    settings = object_file(config / "settings.json")
    known = object_file(plugins / "known_marketplaces.json")
    installed = object_file(plugins / "installed_plugins.json") or {"version": 2, "plugins": {}}
    if "plugins" in settings:
        if not isinstance(settings["plugins"], list):
            raise ValueError("legacy settings.plugins must be an array")
        settings["plugins"] = [p for p in settings["plugins"] if p != str(plugins / plugin)]
        if not settings["plugins"]:
            del settings["plugins"]
    enabled = settings.setdefault("enabledPlugins", {})
    if not isinstance(enabled, dict):
        raise ValueError("enabledPlugins must be an object")
    enabled[key] = True
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    known.setdefault(marketplace, {
        "source": {"source": "github", "repo": "honerlaw/agent-marketplace"},
        "installLocation": str(plugins / "marketplaces" / marketplace), "lastUpdated": now,
    })
    entries = installed.setdefault("plugins", {})
    if not isinstance(entries, dict) or not isinstance(entries.get(key, []), list):
        raise ValueError("installed plugin registrations must be arrays in an object")
    if any(not isinstance(p, dict) for p in entries.get(key, [])):
        raise ValueError("installed plugin registrations must contain objects")
    original = next((p for p in entries.get(key, []) if p.get("scope") == "user"), {})
    version = manifest.get("version", "1.0.0")  # Preserve unversioned Claude plugins.
    registration = {**original, "scope": "user", "installPath": str(plugin_root),
                    "version": version, "installedAt": original.get("installedAt", now), "lastUpdated": now}
    entries[key] = [p for p in entries.get(key, []) if p.get("scope") != "user"] + [registration]
    return [(config / "settings.json", settings),
            (plugins / "known_marketplaces.json", known),
            (plugins / "installed_plugins.json", installed)]


def install(repo: Path, plugin: str, host: str, config: Path, dry_run=False) -> None:
    if host not in {"claude", "codex", "both"}:
        raise ValueError("unknown host")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", plugin):
        raise ValueError("plugin must be a lowercase plugin name")
    root = repo / "plugins" / plugin
    if not root.is_dir():
        raise ValueError(f"plugin not found: {plugin}")
    # Preflight all selected hosts before any registration changes.
    writes = claude_registration(repo, plugin, config) if host in {"claude", "both"} else []
    codex_commands = []
    if host in {"codex", "both"}:
        manifest = object_file(root / ".codex-plugin" / "plugin.json")
        if manifest.get("name") != plugin:
            raise ValueError("plugin does not have a matching Codex manifest")
        if not shutil.which("codex"):
            raise ValueError("Codex CLI is required for Codex installation")
        marketplace = object_file(repo / ".agents" / "plugins" / "marketplace.json")
        name = marketplace_name(marketplace)
        entries = marketplace.get("plugins", [])
        if not isinstance(entries, list) or any(not isinstance(p, dict) for p in entries):
            raise ValueError("Codex marketplace plugins must be an array of objects")
        if not any(p.get("name") == plugin for p in entries):
            raise ValueError("plugin is not listed in the Codex marketplace")
        codex_commands = [["codex", "plugin", "marketplace", "add", str(repo)],
                          ["codex", "plugin", "add", f"{plugin}@{name}"]]
    if dry_run:
        print(json.dumps({"host": host, "configuration_files": [str(p) for p, _ in writes],
                          "codex_commands": codex_commands}, indent=2))
        return
    requirements = root / "scripts" / "requirements.txt"
    if requirements.is_file():
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", str(requirements)], check=True)
    if subprocess.run([sys.executable, "-c", "import playwright"],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    if writes:
        marketplace = marketplace_name(object_file(repo / ".claude-plugin" / "marketplace.json"))
        link(config / "plugins" / plugin, root)
        link(config / "plugins" / "marketplaces" / marketplace, repo)
        for path, value in writes:
            write_json(path, value)
        print(f"Installed {plugin} in Claude Code; run /reload-plugins.")
    try:
        for command in codex_commands:
            subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        prefix = "Claude registration succeeded; " if writes else ""
        raise ValueError(prefix + f"Codex installation failed at {' '.join(exc.cmd)}; rerun --host codex") from exc
    if codex_commands:
        print(f"Installed {plugin} in Codex; start a new app, CLI or IDE conversation.")


def main(argv=None) -> int:
    if sys.version_info < (3, 11):
        print("plugin-install: Python 3.11+ is required", file=sys.stderr)
        return 1
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plugin")
    parser.add_argument("--host", choices=("claude", "codex", "both"), default="claude")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--claude-config-dir", type=Path, default=Path.home() / ".claude")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    try:
        install(args.repo.resolve(), args.plugin, args.host, args.claude_config_dir.resolve(), args.dry_run)
        return 0
    except (ValueError, OSError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        print(f"plugin-install: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
