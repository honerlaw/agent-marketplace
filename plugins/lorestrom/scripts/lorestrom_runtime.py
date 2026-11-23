#!/usr/bin/env python3
"""Installed-script resolution for the lorestrom plugin.

`resolve` validates that a skill file belongs to a lorestrom package, that its scripts
directory holds every shipped module, and that it is not a stale copy of the scripts being
edited. It creates no file. Lifecycle checkpoints arrive with the lifecycle skills (0.2.0)
and will live under `<git-common-dir>/lorestrom/runtime/`, apart from minerva's.
"""
import argparse
import json
import os
import sys
from pathlib import Path

from plugin_guard import divergence, working_tree_root

PLUGIN = "lorestrom"
REQUIRED_MODULES = {
    "knowledge_lint.py", "knowledge_spans.py", "lorestrom_backend.py",
    "lorestrom_runtime.py", "plugin_guard.py",
}


def resolve_scripts(skill_file: Path, override=None) -> Path:
    skill_file = skill_file.expanduser().resolve(strict=True)
    if skill_file.name != "SKILL.md" or skill_file.parent.parent.name != "skills":
        raise ValueError("expected an installed skills/<name>/SKILL.md")
    root = skill_file.parents[2]
    manifests = [root / d / "plugin.json" for d in (".claude-plugin", ".codex-plugin")]
    values = [json.loads(p.read_text(encoding="utf-8")) for p in manifests if p.is_file()]
    if not any(isinstance(value, dict) and value.get("name") == PLUGIN for value in values):
        raise ValueError("skill is not inside a lorestrom plugin package")
    choice = override if override is not None else os.environ.get("LORESTROM_SCRIPTS")
    scripts = Path(choice).expanduser().resolve(strict=True) if choice else root / "scripts"
    missing = sorted(name for name in REQUIRED_MODULES if not (scripts / name).is_file())
    if missing:
        raise ValueError(f"incomplete scripts directory {scripts}: missing {', '.join(missing)}")
    if not choice and divergence(scripts, working_tree_root()):
        raise ValueError("stale installed scripts; update lorestrom or explicitly set LORESTROM_SCRIPTS")
    return scripts.resolve()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    resolve = sub.add_parser("resolve")
    resolve.add_argument("--skill-file", type=Path, required=True)
    resolve.add_argument("--scripts")
    args = parser.parse_args(argv)
    try:
        print(resolve_scripts(args.skill_file, args.scripts))
        return 0
    except (ValueError, OSError, TypeError) as exc:
        print(f"lorestrom-runtime: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
