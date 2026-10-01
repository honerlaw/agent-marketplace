#!/usr/bin/env python3
"""Tombstone: knowledge reconciliation was removed in minerva 3.0.

This script used to write `index.md`, the index watermark, reciprocal `## Related` links
and supersession banners on the default branch after a work unit merged. minerva 3.0
derives all of them on read (`knowledge_catalog.py`) from the entries' own `**Theme**` /
`**Summary**` lines and forward links, so there is nothing left to reconcile
(`2026-10-01-decision-knowledge-aggregates-are-derived-on-read`).

It is kept only so a caller — typically a CI job that reconciled on merge — fails LOUDLY
with migration instructions. It deliberately exits non-zero: a job that "succeeds" while
doing nothing is a silent-success failure, and nobody would learn the job is dead.
"""
import sys

MESSAGE = """knowledge_fix.py: knowledge reconciliation was removed in minerva 3.0.

The catalog, backlinks and supersession are now derived on read from each entry's
**Theme** / **Summary** lines (knowledge_catalog.py); nothing is written after merge.

To migrate:
  1. Delete the CI job (or script) that calls knowledge_fix.py.
  2. Run minerva:migrate, then minerva:migrate-fix to fold index.md / overview.md
     into the entries and delete them.
  3. Re-run minerva:init to refresh the agent-file Routing section.
See plugins/minerva/COMPATIBILITY.md ("Upgrading to 3.0").
"""


def main(argv=None) -> int:
    sys.stderr.write(MESSAGE)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
