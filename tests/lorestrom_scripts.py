"""Load the lorestrom plugin's scripts in-process without minerva's copies standing in.

`conftest.py` puts the root `scripts/` directory first on `sys.path`, and its modules are
symlinks to minerva's. `lorestrom_backend` imports `knowledge_lint` and `knowledge_spans` by
plain name, so a plain import would bind minerva's copies. These loaders execute lorestrom's
own files, swapping them into `sys.modules` only while loading, then restore whatever was
there and keep the loaded modules under unique names.
"""
import importlib.util
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "plugins" / "lorestrom" / "scripts"
PREFIX = "lorestrom_plugin_"


def load(*names):
    """Each named module (in dependency order) from lorestrom's scripts, freshly executed."""
    saved = {name: sys.modules.get(name) for name in names}
    loaded = {}
    try:
        for name in names:
            spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            loaded[name] = module
    finally:
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
    for name, module in loaded.items():
        sys.modules[PREFIX + name] = module
    return loaded


def backend():
    return load("knowledge_spans", "knowledge_lint", "work_status", "lorestrom_backend")["lorestrom_backend"]
