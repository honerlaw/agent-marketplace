---
name: lorestrom-lives-in-its-own-repository
description: Use when changing minerva's shared scripts or contracts, or looking for the lorestrom plugin — it moved to onerlaw/lorestrom-plugins, whose CI checks it against a pinned minerva checkout and agent-marketplace's main daily.
metadata:
  type: decision
---

# lorestrom lives in onerlaw/lorestrom-plugins, checked against minerva from outside

**Date**: 2026-11-26
**Type**: decision
**Theme**: lifecycle
**Summary**: lorestrom moved to onerlaw/lorestrom-plugins at 0.6.0; its CI checks minerva parity against a pinned checkout and a daily drift job
**Context**: .minerva/work/2026-11-26-move-lorestrom-to-its-own-repo

## Context

The user asked, on 2026-11-26, for lorestrom to move into its own public repository on the
`onerlaw` organization, which also hosts the Lorestrom app. Here it shared the repository with
minerva, and the 2026-11-23 decision relied on that: a minerva PR touching a shared script
synced lorestrom's copy, and the shared skill guards ran over both plugins.

## Finding

- **Where it is.** [onerlaw/lorestrom-plugins](https://github.com/onerlaw/lorestrom-plugins), a
  marketplace named `lorestrom-plugins` (Claude Code and Codex manifests, the installer, tests,
  CI). The plugin is 0.6.0 there and installs as `lorestrom@lorestrom-plugins`. Its six release
  commits came along with the files under `plugins/lorestrom/`, so path history and blame reach
  0.1.0. This repository's README keeps only a pointer, with how to remove an
  `lorestrom@agent-marketplace` install.
- **Parity from outside.** Its tests read minerva from a checkout of this repository
  (`tests/minerva_checkout.py`: `MINERVA_ROOT`, else a sibling `../agent-marketplace`), and the
  run stops when there is none; no test skips for it. A **pinned** job checks every change
  against the commit in its `tests/minerva.ref`, and a **drift** job checks agent-marketplace's
  `main` daily.
- **The sync rule changes.** A minerva PR here can no longer see lorestrom, so nothing fails in
  this repository when a shared script (`knowledge_lint.py`, `knowledge_spans.py`,
  `work_status.py`) changes. The drift job fails within a day instead; then the lorestrom side
  copies the file, bumps `tests/minerva.ref` and its patch version. The shared skill guards here
  are minerva-only; lorestrom-plugins carries their lorestrom halves.

## Implications

- Changing a minerva script lorestrom copies, or a skill contract lorestrom's tests port, means
  a red drift run in lorestrom-plugins the next day, even with nothing wrong in minerva. Say so
  in the minerva PR when it is deliberate.
- The guarantee is detection after merge, not a gate on the minerva PR. Gating it here would
  take a workflow in this repository that checks out lorestrom-plugins; none exists.
- Commits in lorestrom-plugins up to 0.5.1 cite this repository's pull requests (`#152` to
  `#158`).

## Related
- [[2026-11-23-decision-lorestrom-is-a-separate-lorestrom-only-plugin]] — amends: its same-PR sync rule and two-plugin guards now run from lorestrom-plugins against a pinned checkout and a daily drift job
- [[2026-11-23-bug-a-test-loader-leaked-sys-path-across-plugins]] — relates to: the moved loader keeps lorestrom's copies first while minerva's scripts sit on sys.path
