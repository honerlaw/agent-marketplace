---
name: init
description: Links a Git repository to a Lorestrom project through a connected Lorestrom MCP server — finds an existing project by the repository's remote, or creates one in a workspace the user picks — caches the link in this clone (or commits it with `--shared`), and offers a confirmed import of the repository's minerva knowledge entries as a snapshot copy. Re-runs import new entries and report changed ones. Use when the user wants to connect a repository to Lorestrom, publish or share its minerva knowledge there, or invokes `lorestrom:init`.
---

## Runtime

Read `skills/using-lorestrom/references/runtime.md` before executing; follow its host adapter.

Links this repository to a Lorestrom project and publishes a snapshot of its minerva
knowledge. It changes no tracked file unless `--shared` is given, and it never edits,
moves or deletes the repository's minerva files: they stay authoritative in this version.

## Usage

- `lorestrom:init` — link this clone (or report its link) and offer the import.
- `lorestrom:init --shared` — also commit the link as `.lorestrom/config.json`, so every
  clone with the Lorestrom MCP server connected uses it.

## Protocol

Read `skills/using-lorestrom/references/storage.md` for every `storage:` operation and its
ground rules, then read `references/link.md` and follow it: it is `storage:project.link`,
and it runs `storage:project.discover` and `storage:knowledge.import` where it says.

Before any write, Git and a connected Lorestrom MCP server are required. Without a server,
stop and say how to connect one, as the host adapter shows; nothing is linked or written.

A re-run on a linked repository reports the link, checks the project node and its remote
aliases, and offers only what is missing: an import of entries Lorestrom does not have yet.
Changed entries are reported, never overwritten. It offers no removal of the minerva files.
