# Proposal: move-lorestrom-to-its-own-repo

**Date**: 2026-11-26
**Status**: Draft

## Goal

The lorestrom plugin lives in its own public repository, **`onerlaw/lorestrom-plugins`**
(cloned at `~/Development/lorestrom-plugins`), a plugin marketplace named `lorestrom-plugins`
for Claude Code and Codex, and no longer in agent-marketplace.

The new repository holds:

- `plugins/lorestrom/` with its git history (the six release commits, 0.1.0 to 0.5.1);
- `.claude-plugin/marketplace.json` and `.agents/plugins/marketplace.json` listing it, so
  `/plugin marketplace add onerlaw/lorestrom-plugins` then `/plugin install
  lorestrom@lorestrom-plugins` works in Claude Code, and Codex adds the marketplace likewise;
- the installer (`install.sh`, `scripts/install_plugin.py`), for installing from a clone;
- `tests/`: the plugin's own test modules and the lorestrom halves of the contract tests it
  shares today with minerva, with the minerva-parity checks reading minerva from a pinned
  agent-marketplace checkout;
- CI (GitHub Actions) running those tests, a README, the MIT LICENSE and a `.gitignore`.

The plugin becomes **0.6.0**, its README's install section names the new repository, and
anyone who installed `lorestrom@agent-marketplace` is told, in both repositories, how to
uninstall it and reinstall from the new one.

agent-marketplace loses `plugins/lorestrom/`, its test modules and every lorestrom parameter
in the shared tests, and both marketplace entries. Its README's lorestrom row becomes a
sentence pointing at the new repository. Its `.minerva/` records about lorestrom stay: they
are that repository's history.

## Why

The user asked for lorestrom to move to a public repository of its own on the `onerlaw`
organization, which also hosts the Lorestrom app. lorestrom is minerva's successor and is
released on its own cadence; agent-marketplace is a personal marketplace of unrelated plugins
and MCP servers. The minor version changes because the install id, marketplace and install
location change: `lorestrom@agent-marketplace` becomes `lorestrom@lorestrom-plugins`.

## Approach

**A (recommended): history-preserving split, tests ported with minerva parity pinned.**

1. **History.** `git subtree split --prefix=plugins/lorestrom` in agent-marketplace gives a
   branch of the plugin's commits with the plugin at its root. The new repository starts
   from an initial commit (README, LICENSE, `.gitignore`, manifests), then
   `git subtree add --prefix=plugins/lorestrom <split>` (no squash), so `git log --
   plugins/lorestrom` shows the release commits. Tests, installer and CI arrive in later
   commits that name where they came from.
2. **Tests.** Move `tests/test_lorestrom_{plugin,backend,units,migrate}.py` and
   `tests/lorestrom_scripts.py`. Port the lorestrom halves of the shared tests
   (`skills_corpus.py`, `test_phasing.py`, `test_skill_snippets.py`'s helper-block tests,
   `test_untrusted_names.py`, `test_plugin_guard_sites.py`, `test_host_adapters.py`,
   `test_skill_budget.py`, `test_install_plugin.py`'s lorestrom case), copying only the helper
   code they need.

   **Minerva in the new repository: required, never skipped.** Many tests need minerva: the
   parity checks (shared scripts byte-identical to minerva's, the guard covering minerva's
   skills, ported skills keeping minerva's files, untrusted-name classifications not widening
   minerva's, orchestrator parity; `MINERVA_SKILLS` and `MINERVA_SCRIPTS` in
   `test_lorestrom_plugin.py`); `test_lorestrom_backend.py`, which imports minerva's
   `knowledge_catalog` by plain name and converts agent-marketplace's `.minerva/knowledge`
   corpus (`converted > 100`); and `lorestrom_runtime`, loaded at import time by
   `test_lorestrom_units.py`, which imports `plugin_guard` by plain name and must bind
   minerva's (`test_lorestrom_units.py`'s check). So the suite always needs a minerva
   checkout. `tests/conftest.py` resolves `MINERVA_ROOT` (the environment variable, else a
   sibling `../agent-marketplace` only when the variable is unset). When the resolved root has
   no `plugins/minerva/scripts` (a set but wrong `MINERVA_ROOT` never falls back to the
   sibling), a `pytest_configure` hook stops the session with `pytest.exit` and a message
   saying how to set it. No test skips for a missing
   minerva, so a run is never green with the parity checks unrun. Otherwise it inserts
   `$MINERVA_ROOT/plugins/minerva/scripts` at `sys.path[0]`, as agent-marketplace's root
   `conftest.py` does with its `scripts/` symlinks. That serves the plain-name imports
   (`knowledge_catalog`, and `plugin_guard` from `lorestrom_runtime`); `lorestrom_scripts.py`
   loads lorestrom's own copies by file path whatever `sys.path` holds. Every constant that
   names minerva (`MINERVA_SKILLS`, `MINERVA_SCRIPTS`, the backend test's `CORPUS`, now
   `$MINERVA_ROOT/.minerva/knowledge`, pinned data) is derived from that root in one helper
   module. `tests/__init__.py` stays, so `from tests import ...` keeps working from the
   repository root. A test covers the stop: a subprocess pytest run with `MINERVA_ROOT`
   pointing at an empty directory exits non-zero with that message.

   **The sync rule stays enforced.** The rule (knowledge
   `2026-11-23-decision-lorestrom-is-a-separate-lorestrom-only-plugin`: a minerva change to
   a shared script syncs lorestrom's copy and bumps its patch version) can no longer fail a
   minerva PR, because the two live in different repositories. Two CI jobs keep it:
   - **pinned** (push and pull request, required): agent-marketplace at the commit in
     `tests/minerva.ref`, a commit on agent-marketplace `main`; the job checks that the
     checkout's `HEAD` equals that commit. A minerva change never breaks an unrelated
     lorestrom PR.
   - **drift** (daily schedule and manual dispatch): the same tests against agent-marketplace
     `main`. A failure is the signal to sync the copy, bump `tests/minerva.ref` and
     lorestrom's patch version. GitHub notifies the repository owner of a failed scheduled
     run.
   The plugin README's sync-rule text, the `SYNC_RULE` constant that
   `test_lorestrom_plugin.py` asserts against it, and the byte-identical test's failure
   message change together and say this instead of "a minerva PR syncs the copy". They also
   say that the drift job can fail on a minerva change to `plugin_guard`, which the runtime
   tests execute against, without owing a copy sync: then the lorestrom side adapts. An
   agent-marketplace workflow that checks out this repository and compares the shared files
   would gate the minerva PR itself; it is out of scope (Open Questions). A knowledge entry in agent-marketplace
   records the change and links the 2026-11-23 decision.
3. **Installer.** Copy `install.sh` and `scripts/install_plugin.py`; its known-marketplace
   source becomes `onerlaw/lorestrom-plugins`.
4. **CI.** `.github/workflows/tests.yml`: Python 3.11 and 3.13, agent-marketplace checked out
   into `minerva/` (at `tests/minerva.ref`, or `main` in the drift job), `MINERVA_ROOT` set,
   then `python -m pytest tests/ -q -rs`.
5. **Publish.** Before the first push, check what is published: `git log -p --all` of the
   new repository scanned for token and key shapes (`ghp_`, `gho_`, `sk-`, `-----BEGIN`,
   `AKIA`, `xox`, `dp.st.`), no `.env` or credentials file, no machine-specific path
   (`/Users/`). Then `gh repo create onerlaw/lorestrom-plugins --public`, push `main`, and
   wait for its CI to pass. Then install from the live repository with a throwaway
   configuration: `claude plugin marketplace add onerlaw/lorestrom-plugins` and `claude
   plugin install lorestrom@lorestrom-plugins` (or the manifests read from the pushed `main`
   validate, where the CLI cannot take a throwaway configuration), and `codex plugin
   marketplace add onerlaw/lorestrom-plugins` resolves. Only then touch agent-marketplace.
6. **agent-marketplace.** In this unit's worktree: remove `plugins/lorestrom/`, the moved
   test modules, the lorestrom entries in both marketplace manifests and every lorestrom
   parameter or branch in the shared tests (simplifying a two-plugin table to minerva's
   entry where only minerva remains). The README's lorestrom paragraph and table row become
   one pointer section: lorestrom moved to `onerlaw/lorestrom-plugins`; the install commands
   there (Claude Code and Codex); and, for anyone who installed `lorestrom@agent-marketplace`,
   uninstall it (`/plugin uninstall lorestrom@agent-marketplace`, or for a clone install
   remove the `~/.claude/plugins/lorestrom` link and its `enabledPlugins` entry) and install
   from the new marketplace. The evals workflow
   steps pass. Merged when CI is green.
7. **Version 0.6.0**: both plugin manifests, the plugin README and COMPATIBILITY,
   `using-lorestrom/SKILL.md`, `runtime.md`'s version line, and the new repository's version
   tests.

### Approaches considered

- **A — split with history, port the tests, pin minerva parity** (above).
- **B — copy the files, keep only lorestrom-only tests.** Simpler, but loses the plugin's
  history and the guarantees the parity checks give (the shared scripts staying identical to
  minerva's, the untrusted-name classifications not widening minerva's).
- **C — keep lorestrom in agent-marketplace and mirror it** (`git subtree push`). Two sources
  of truth; the user asked for a move.

## Success criteria

1. `onerlaw/lorestrom-plugins` exists, public, default branch `main`, with the layout above;
   `git log -- plugins/lorestrom` there includes six commits whose subjects are the 0.1.0 to
   0.5.1 releases (hashes rewritten; their `#NNN` refer to agent-marketplace, which the
   README says).
2. In the new repository, `python -m pytest tests/ -q` passes locally with a minerva checkout,
   and its CI passes on `main`.
3. With no minerva checkout the test run stops at start (a test proves it) and no test
   skips for a missing minerva; the pinned job checks out exactly `tests/minerva.ref`, a commit on agent-marketplace `main`;
   the drift job runs against `main` on a schedule; the sync-rule text names the drift job.
4. The new README documents installing in Claude Code (`/plugin marketplace add
   onerlaw/lorestrom-plugins`, `/plugin install lorestrom@lorestrom-plugins`), in Codex, and
   from a clone with `./install.sh lorestrom --host both`; an installer test covers the clone
   path with a temporary config, keyed `lorestrom@lorestrom-plugins`, and both marketplace
   manifests list lorestrom at `./plugins/lorestrom` (tested). Installing from the live
   repository works in Claude Code and `codex plugin marketplace add` accepts it.
5. lorestrom is 0.6.0 everywhere it states its version (`grep -rn '0\.5\.1'` finds only
   release history); its README has a 0.6.0 "This version" note, and its install section
   names the new repository and tells `lorestrom@agent-marketplace` users how to move.
6. agent-marketplace has no `plugins/lorestrom/`, no lorestrom marketplace entry, and no test
   that names lorestrom (`tests/test_install_plugin.py` keeps its minerva cases); `grep -rn lorestrom` outside `.minerva/` finds only the README's
   pointer section, which names the new repository, its install commands and how to move an
   old install; the evals workflow
   steps pass (`python -m pytest tests/`, the eval dry-runs, knowledge lint); the PR is
   merged.
7. Nothing secret is published: the step-5 scan of the new repository's full history finds
   no token or key shape, no `.env` or credentials file and no `/Users/` path, before the
   first push.

## Open Questions

- The new repository has no `.minerva/` or Lorestrom link; it can be linked with
  `lorestrom:init` later.
- The sync rule can be gated on the minerva PR itself only by an agent-marketplace workflow
  that checks out this repository; this unit relies on the daily drift job instead.
