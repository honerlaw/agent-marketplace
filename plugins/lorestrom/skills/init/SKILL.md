---
name: init
description: Links a Git repository to a Lorestrom project through a connected Lorestrom MCP server — finds an existing project by the repository's remote, or creates one in a workspace the user picks — and caches the link in this clone (or commits it with `--shared`). In a repository that still holds minerva's `.minerva/` records it names `lorestrom:migrate`, which imports them and removes `.minerva/`, and offers to continue into it. Use when the user wants to connect a repository to Lorestrom, set up lorestrom in a repository, or invokes `lorestrom:init`.
---

## Runtime

Read `skills/using-lorestrom/references/runtime.md` before executing; follow its host adapter.

Links this repository to a Lorestrom project, which is then authoritative for its work units,
knowledge and reference docs. It is the setup for any repository; a repository that used
minerva moves its records over with `lorestrom:migrate`, minerva's successor path. Init
changes no tracked file unless `--shared` is given: with defaults, `git status --porcelain`
is unchanged.

## Usage

- `lorestrom:init` — link this clone, or report its link.
- `lorestrom:init --shared` — also commit the link as `.lorestrom/config.json`, so every
  clone with the Lorestrom MCP server connected uses it.

## Protocol

Read `skills/using-lorestrom/references/storage.md` for every `storage:` operation and its
ground rules, then read `references/link.md` and follow it: it is `storage:project.link`,
and it runs `storage:project.discover` where it says.

Before any write, Git and a connected Lorestrom MCP server are required. Without a server,
stop and say how to connect one, as the host adapter shows; nothing is linked or written.

After the link, run `git ls-files -- .minerva`. When it lists files, the repository still
holds minerva's records: say that Lorestrom is now authoritative and never reads them as
lore, that `lorestrom:migrate` imports them into Lorestrom and then removes `.minerva/`, every
send and every removal confirmed, and ask whether to continue into it now. On a yes, load
`lorestrom:migrate` with the skill loader (it finds the link and goes on from there); on a
no, report and stop, changing nothing more. Init never imports or removes anything itself.

A re-run on a linked repository reports the link, checks the project node and its remote
aliases, and names `lorestrom:migrate` again while `.minerva/` holds files. A plugin never
edits host settings: disabling minerva is the user's step, which migrate explains.
