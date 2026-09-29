# Enforced decomposition log — design

**Status:** design agreed with the operator, 2026-09-27. Not yet built.
**Kind:** dev-tooling (plugin, hooks, CI, docs). Nothing here runs inside a lab.
**Names are placeholders** until the operator names them: `lens-log` (the plugin),
`decomposition.json` (the definition file).

## 1. The problem

The PROVES decomposition has been recorded mostly in memory and in one hand-written
file (`docs/decomposition/proves/process-log.md`). Recording depended on an agent
remembering to do it. Two things went wrong because of that:

- The dashboard inventory was made from a local clone 50 commits behind GitHub, and
  nothing recorded which source commit it was made from.
- The end-of-session "upskilling report" hook only warned; the report went to memory,
  not to a file anyone can read.

**Goal:** the decomposition process, the lessons learned, and the skills are written to
files in git, and writing them is **enforced by tooling**, not left to memory. Memory
stays as a secondary pointer; the file is the record.

**Success:** anyone (person or agent) can open the repos and see what was done in the
decomposition, when, against which source commit, what was learned, and which skills
came out of it, without querying memory.

## 2. Decisions made

| # | Decision | Why |
|---|---|---|
| D1 | Every Lens repo keeps its **own** log; lens-core also holds a generated **index** of all five. | Siblings own their process; the index keeps the whole visible (guards the "lost the whole" failure mode). |
| D2 | Log entries are enforced by a **`Stop` hook**, which fires after **every assistant turn**, not at session end. | Sessions stay open for weeks; session start/end triggers would almost never fire. |
| D3 | The index is built by a **GitHub Action** on a schedule, not by a session. | Must run with no window open and no prompt. Mechanical work, so no AI needed. |
| D4 | The hook is **deterministic**: it fires only when a turn touches a surface declared in the decomposition definition. It never judges wording. | Only fire when necessary; no guessing. |
| D5 | What "the decomposition" is lives in **one specialized file**, `decomposition.json`. Redefining the decomposition = editing that file. Editing it is itself a logged decision. | Hook code never changes when the architecture changes. |
| D6 | **Two layers:** lens-core's file defines the whole; each sibling's file defines only its piece. Each hook reads only its own repo's file. | Mirrors charter-per-repo + fragment map. Hooks stay inside their own repo, fast, offline. |
| D7 | The plugin lives **in lens-core** (`plugins/lens-log/`); lens-core acts as the plugin marketplace. | The log format and the definition file are part of the shared standard, which lens-core holds. Not Tapestry: The Lens is independent. |
| D8 | **Reading** the PROVES source counts as touching the source surface. | Research passes change no files but are the core of the process. |

## 3. The pieces

```text
lens-core/
├── decomposition.json            # the WHOLE: sources, module map, bus, lens-core's own surfaces
├── .claude-plugin/marketplace.json
├── plugins/lens-log/
│   ├── DESIGN.md                 # this file
│   ├── .claude-plugin/plugin.json
│   ├── hooks/hooks.json          # Stop + SubagentStop
│   ├── scripts/                  # hook logic, entry helper, index builder (stdlib Python)
│   └── skills/log-entry/SKILL.md # how to write a good entry
├── docs/log/
│   ├── entries/                  # lens-core's own entries
│   └── INDEX.md                  # generated; do not edit by hand
└── .github/workflows/log-index.yml

lens-ingest/ (and each sibling)
├── decomposition.json            # this PIECE only: its surfaces + relevant source paths
└── docs/log/entries/
```

### 3.1 `decomposition.json`

**lens-core (the whole):**

```json
{
  "version": 1,
  "role": "whole",
  "sources": [
    {"name": "PROVES_LIBRARY", "repo": "Lizo-RoadTown/PROVES_LIBRARY",
     "match": ["**/PROVES_LIBRARY/**"]},
    {"name": "proves-curation-dashboard", "repo": "Lizo-RoadTown/proves-curation-dashboard",
     "match": ["**/proves-curation-dashboard/**"]}
  ],
  "modules": ["lens-core", "lens-ingest", "lens-review", "lens-serve", "lens-observe"],
  "bus": {"owner": "lens-core", "paths": ["docs/schema/**"]},
  "surfaces": [
    {"name": "source",   "paths": ["@sources"],                          "on": "read-or-write", "entry": "process"},
    {"name": "bus",      "paths": ["docs/schema/**"],                    "on": "write",         "entry": "decision"},
    {"name": "identity", "paths": ["CHARTER.md", "CLAUDE.md", "docs/BUILD.md"], "on": "write", "entry": "decision"},
    {"name": "definition","paths": ["decomposition.json"],               "on": "write",         "entry": "decision"},
    {"name": "skills",   "paths": ["skills/**", "SKILLS.md", "plugins/**/skills/**"], "on": "write", "entry": "skill"},
    {"name": "module",   "paths": ["src/**"],                            "on": "write",         "entry": "process"}
  ]
}
```

**A sibling (its piece):** same shape with `"role": "piece"`, `"module": "lens-review"`,
its own `surfaces`, and `sources` narrowed to the source paths relevant to it. It does
not repeat the module map or the bus. The index Action checks it against the whole.

Only the source list, the modules and the path patterns are domain-specific. The file's
shape is the part of the standard.

### 3.2 Log entries

One file per entry: `docs/log/entries/YYYY-MM-DD-HHMM-<slug>.md`. One file per entry
means no merge conflicts and a parse the index can trust.

```markdown
---
type: process            # process | decision | skill | lesson
module: lens-core
surfaces: [source]
source_commits:          # filled in by the helper from git, never typed by hand
  proves-curation-dashboard: c484e52
date: 2026-09-27T14:05
---

## What was done
...

## What was found / decided
...

## Lessons
...                      # required; write "none" explicitly if there are none
```

`lesson` entries can also be written on their own, for example after an operator
correction. Lessons are never inferred by the hook; they are prompted by the required
**Lessons** section on every entry.

### 3.3 The hooks (per tool call + per turn)

*Revised 2026-09-29 after checking <https://code.claude.com/docs/en/hooks.md>: the
transcript is written asynchronously and "may not yet include the current turn's most
recent messages when a hook fires", so the hooks do not parse it. `PostToolUse` fires
for tool calls inside subagents too, which replaces the separate `SubagentStop` step.
`stop_hook_active` is not a loop indicator, so the hook keeps its own guard.*

**`PostToolUse` (every tool call, main agent and subagents):**

1. Find this repo's `decomposition.json` (walking up from `cwd`). None → do nothing.
2. Take the paths the call touched: `file_path` / `notebook_path` / `path` / Glob
   `pattern`; for Bash/PowerShell, a source name appearing as a path segment in the
   command text (reads only).
3. Match them against the declared surfaces (`on: read-or-write` vs `write`).
4. Any match → append it to a per-session touch file outside the repo
   (`~/.claude/cache/lens-log/<session>.touches.jsonl`), and on the first touch, save
   the list of entry files that already existed.

**`Stop` (end of every turn):**

1. Also match the turn's `tool_calls` from the hook input (belt and braces).
2. Nothing pending → allow the turn to end.
3. Pending → do new entry files (created since the first touch) cover every pending
   surface, each with a non-empty **Lessons** section? Yes → clear and allow.
   No → **block**, naming each surface, the entry type it needs, and the exact helper
   command to run.
4. **Loop guard:** block at most once per pending set. If the next stop still has no
   entry, allow it, but write a `docs/log/missed/<timestamp>.json` marker naming the
   surfaces. The index lists every miss, so nothing is lost silently.
5. A malformed `decomposition.json` never blocks: the hook reports it and allows.

**Known limit:** a shell command that *writes* a surface (e.g. `sed -i CHARTER.md`) is
not detected by the hooks. The index audit (3.5) catches it from the commit.

### 3.4 Entry helper + skill

A small stdlib-Python script creates a correctly shaped entry: fills `date`, `module`,
`surfaces`, and `source_commits` (by running `git rev-parse HEAD` in each touched source
repo), and leaves the prose sections for the agent. The `log-entry` skill explains what a
useful entry contains. The hook's block message points at both.

### 3.5 The index GitHub Action (lens-core)

- **Triggers:** schedule (daily), `workflow_dispatch`, and push to lens-core.
- **Reads** each module's `decomposition.json` and `docs/log/entries/*` from GitHub (the
  repos are public).
- **Writes** `docs/log/INDEX.md` and commits it:
  - one table row per entry: date, module, type, surfaces, one-line summary, link;
  - a **staleness stamp**: the commit of each repo the index was built from;
  - **consistency check:** every piece's surfaces and sources agree with the whole;
  - **audit:** commits that changed a declared surface without adding an entry file,
    plus every `missed/` marker.
- No AI; deterministic; no cost beyond Actions minutes.

## 4. What is NOT in scope

- Judging the operator's wording to detect corrections (not deterministic).
- Writing entries into another repo. Each repo writes only its own log.
- Replacing loom-memory. Entries may reference memory records; memory may point at entries.
- Rewriting the existing `docs/decomposition/proves/process-log.md`. It stays as the
  pre-log history and is linked from `INDEX.md`.

## 5. To verify during implementation

- ~~Exact hook input fields and block format~~ — checked 2026-09-29, see 3.3.
- Whether GitHub disables scheduled workflows in quiet repos, and whether the index's own
  commits count as activity. The push and manual triggers are the fallback.
- That `enabledPlugins` in each sibling's `.claude/settings.json` can reference a
  marketplace hosted in lens-core.

## 6. Build order

1. `decomposition.json` for lens-core + the `PostToolUse` and `Stop` hooks + entry
   helper, enforced in lens-core only. Use it on the real work (re-deriving the
   dashboard inventory). Plan: [`PLAN.md`](PLAN.md).
2. ~~`SubagentStop` capture~~ — folded into step 1 (`PostToolUse` covers subagents).
3. Siblings: their `decomposition.json` + enable the plugin.
4. Index Action with staleness stamp, consistency check and audit.
