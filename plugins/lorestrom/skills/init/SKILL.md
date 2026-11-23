---
name: init
description: Links a Git repository to a Lorestrom project through a connected Lorestrom MCP server — finds an existing project by the repository's remote, or creates one in a workspace the user picks — caches the link in this clone (or commits it with `--shared`), then hands a repository that used minerva over to Lorestrom — a confirmed sync of its knowledge entries and reference docs, then separately confirmed offers, each kept by default, to replace the agent file's minerva routing section and to remove the imported files in one commit — and says how to disable minerva for the repository. Use when the user wants to connect a repository to Lorestrom, move its minerva records there, or invokes `lorestrom:init`.
---

## Runtime

Read `skills/using-lorestrom/references/runtime.md` before executing; follow its host adapter.

Links this repository to a Lorestrom project, which is then authoritative for its work units,
knowledge and reference docs, and hands its minerva files over. It changes no tracked file
unless `--shared` is given or the user says yes to a handover offer, and every offer defaults
to keep: with each declined, `git status --porcelain` is unchanged.

## Usage

- `lorestrom:init` — link this clone (or report its link), then run the handover.
- `lorestrom:init --shared` — also commit the link as `.lorestrom/config.json`, so every
  clone with the Lorestrom MCP server connected uses it.

## Protocol

Read `skills/using-lorestrom/references/storage.md` for every `storage:` operation and its
ground rules, then read `references/link.md` and follow it: it is `storage:project.link`,
and it runs `storage:project.discover` where it says. Then read `references/handover.md` and
follow it: `storage:handover.sync`, the two offers, and the minerva-disable instruction.

Before any write, Git and a connected Lorestrom MCP server are required. Without a server,
stop and say how to connect one, as the host adapter shows; nothing is linked or written.

A re-run on a linked repository reports the link, checks the project node and its remote
aliases, and runs the handover again: it imports what is new, offers what changed, and repeats
any offer the user declined. A plugin never edits host settings: disabling minerva is the
user's step.
