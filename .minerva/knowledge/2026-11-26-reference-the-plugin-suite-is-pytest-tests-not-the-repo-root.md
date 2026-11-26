# The plugin suite is `pytest tests/`; the repository root also collects the MCP servers' tests

**Date**: 2026-11-26
**Type**: reference
**Theme**: mcp-servers
**Summary**: CI's evals workflow runs `python -m pytest tests/`; a bare `pytest` at the repo root also collects `mcp/*/tests`, which need each server's own dependencies (`make install`, run by the mcp workflow) and fail to import without them.
**Context**: .minerva/work/2026-11-26-lorestrom-connect-via-agents-page

## Context

Verifying a lorestrom plugin change ("the repository's full test suite passes"), a bare `python3 -m pytest -q -x` at the repository root stopped at once: `ERROR mcp/clerk/tests - ModuleNotFoundError: No module named 'httpx2'`.

## Finding

- `.github/workflows/evals.yml` runs `python -m pytest tests/ -q`, then `scripts/run_skill_evals.py --dry-run`, `scripts/run_compatibility_evals.py --host both --dry-run` and `scripts/knowledge_lint.py .minerva/knowledge`. That is the plugin and marketplace suite (about 2,600 tests, about 4.5 minutes locally).
- `.github/workflows/mcp.yml` runs each server under `mcp/` separately, per server directory: `make install`, then `make check`, with its own dependencies.
- Pytest at the repository root walks into `mcp/*/tests` as well, and fails at collection wherever a server's dependencies are not installed in the current environment. That failure says nothing about a plugin change.

## Implications

- To verify a change to `plugins/`, `scripts/` or `tests/`, run what `evals.yml` runs, starting with `python -m pytest tests/`; a success criterion that says "the full suite" means that.
- To verify a change to an MCP server, run `make install && make check` in its directory, as `mcp.yml` does.

## Related

- [[2026-08-11-decision-ci-runs-the-whole-suite]] — the evals workflow's whole-`tests/` run this describes
