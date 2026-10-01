## minerva

This project uses [minerva](https://github.com/honerlaw/agent-marketplace/tree/main/plugins/minerva) for durable record discipline.

- `.minerva/knowledge/` — write-once entries (decisions, bugs, patterns, constraints, references), each tagged with a `**Theme**` and a one-line `**Summary**`. Orient by listing the catalog — one `theme | entry | summary` line per entry, grouped by theme — then open only the entries whose theme bears on your task:

  ```sh
  awk 'function p(){if(f!=""){n=f;sub(/.*\//,"",n);sub(/\.md$/,"",n);print (t==""?"(unthemed)":t)" | "n" | "s};f=FILENAME;t="";s="";q=0} FNR==1{p()} /^[ \t]*(```|~~~)/{q=!q;next} q{next} /^\*\*Theme\*\*:/&&t==""{t=$2} /^\*\*Summary\*\*:/&&s==""{sub(/^\*\*Summary\*\*: */,"");s=$0} END{p()}' .minerva/knowledge/[0-9]*.md | sort
  ```

  Links between entries are forward-only `## Related` lines; find what links *to* an entry with `grep -l '\[\[<entry>\]\]' .minerva/knowledge/*.md`.
- `.minerva/reference/` — present-tense operational docs (architecture, glossary, conventions): how the system works now. Read on demand.
- `.minerva/work/` — historical proposals and replans. Grep when you need the reasoning behind a past feature.

Active work units live at `.minerva/work/<date-slug>/`. Load the installed `minerva:using-minerva` skill for the full methodology using your host's skill loader. In Claude Code use `/minerva:using-minerva`; in Codex select `$minerva:using-minerva`. Follow the loaded plugin's runtime contract for tools and installed paths.
