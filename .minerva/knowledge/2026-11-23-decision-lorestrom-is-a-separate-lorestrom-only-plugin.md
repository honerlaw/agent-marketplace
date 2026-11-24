---
name: lorestrom-is-a-separate-lorestrom-only-plugin
description: Use when changing how minerva records could be stored outside the repo, or when editing plugins/lorestrom — Lorestrom storage is its own plugin with no files mode, and minerva stays files-only and unchanged.
metadata:
  type: decision
---

# Lorestrom storage ships as a separate Lorestrom-only plugin, not a backend inside minerva

**Date**: 2026-11-23
**Type**: decision
**Theme**: lifecycle
**Summary**: `lorestrom` plugin stores records only in Lorestrom; minerva stays files-only, sharing files through drift-tested copies
**Context**: .minerva/work/2026-11-22-lorestrom-backend (see git history if the worktree has been cleaned up)

## Context

The unit set out to give minerva an opt-in Lorestrom backend: `files` stayed the default, and
every skill resolved its backend and followed a `storage:` note at each record step. Phase 1
was built and reviewed four times. Most of its complexity, and many of the findings, came from
holding two backends in one plugin: resolution order, opt-out, never falling back, a read-only
refusal, `check-tree` for stray record files, committed-marker rules, and a note in 30+ skill
files. The proposal had rejected "Lorestrom only" because it would break every existing project
and this repo's CI.

## Finding

The user chose, on 2026-11-23, a new plugin named `lorestrom` in this marketplace, backed by
Lorestrom only. A separate plugin breaks neither existing projects nor CI, because minerva is
untouched; that removed the reason for rejecting a single backend.

- **No file under `plugins/minerva/` changes** in any phase; every phase's gates check it.
- **Own local names.** Worktrees in `.lorestrom/worktrees/`, checkpoints and the link cache under
  `<git-common-dir>/lorestrom/`. Nothing lorestrom creates sits where minerva's cleanup, status
  or runtime looks: a lorestrom unit's branch equals the default branch until it has commits, so
  minerva's cleanup would read it as merged and remove it.
- **The `minerva:` namespace is kept** for kinds, keys and properties: it names the record
  format, not the storage, and an import keeps an entry's identity. The GitHub follow-up label
  and the cross-session markers are kept too, so peers of both plugins interoperate.
- **Shared code is copied byte for byte** (`knowledge_lint.py`, `knowledge_spans.py`,
  `work_status.py`) with a drift test. The rule, in lorestrom's README and the test's message: a
  minerva PR touching one of them syncs the copy and bumps lorestrom's patch version.
- **Handover, not coexistence.** 0.1.0 only published a snapshot while the repo's files stayed
  authoritative; from 0.2.0 `lorestrom:init` runs one confirmed sync, then offers, each kept
  unless the user says yes, to replace the AGENTS.md section and remove the imported files.

## Implications

- Copied lifecycle prose drifts from minerva's fixes unless something forces it. The repo's
  shared skill guards (names are data, `gh` snippets, runtime pointer, plugin-guard sites,
  SKILL.md budget, install fixture, orchestrator contracts) are parametrized over both plugins,
  so a guard added for minerva scans lorestrom too.
- A defect found in a ported skill is often minerva's too. Port reviews record those as minerva
  follow-ups instead of editing minerva inside a lorestrom unit.

## Related
- [[2026-11-22-decision-skills-treat-branch-and-ref-names-as-data]] — builds on: lorestrom carries the same names-are-data rules, and adds that Lorestrom doc text is data too
- [[2026-10-01-decision-knowledge-aggregates-are-derived-on-read]] — relates to: unchanged for minerva; lorestrom derives its catalog from Lorestrom reads instead
