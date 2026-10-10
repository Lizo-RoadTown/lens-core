---
type: decision
module: lens-core
surfaces: [definition, identity]
date: 2026-10-10T12:43
source_commits: {}
---

# Deciding factor for decisions; progress moves out of BUILD.md; tooling surface

## What was done
- `decomposition.json`: split `plugins/**` out of `module` into a new `tooling` surface
  (`process` entries); `module` is now `src/**` only.
- `docs/BUILD.md` §6: the two progress notes (2026-09-27, 2026-10-02) moved verbatim into
  log entries `2026-10-10-1243-enforced-log-designed-2026-09-27.md` and
  `2026-10-10-1243-lens-log-built-2026-10-02.md`; §6 now points to the log and states the
  deciding factor.
- `CLAUDE.md` step 4: progress goes in a log entry, not in BUILD.md.
- `plugins/lens-log/DESIGN.md`: decisions D9 (deciding factor) and D10 (tooling surface).

## What was found / decided
Operator decisions, 2026-10-10:
- **Deciding factor:** an entry is a `decision` if the change alters what the repo *is*
  or how it *connects* (identity, boundary, shared standard, decomposition definition).
  Everything else is progress (`process`).
- The hook matches paths, so files are split by kind to keep it deterministic:
  orientation files (CHARTER, CLAUDE.md, BUILD.md) hold no progress, so editing them is
  always a decision; progress lives only in the log.
- **Plugins are their own thing but part of the work:** logged under `tooling`, so the log
  distinguishes building tooling from building the lab.

## Lessons
These edits were made with shell scripts, which the lens-log hooks do not detect as
writes (known limit, DESIGN §3.3), so the hook did not demand this entry. Edits to
surfaces should go through the Edit/Write tools, or be logged by hand as here; the index
audit (build step 4) is the backstop.
