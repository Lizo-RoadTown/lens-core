---
name: log-entry
description: How to write a decomposition log entry when the lens-log Stop hook asks for one, or when recording a lesson on your own. Use whenever a turn touched a surface declared in decomposition.json.
---

# Writing a decomposition log entry

The log is the record of the decomposition. Memory may point at it; it does not replace it.

1. Run the exact command the hook gave you (it already names the type, surfaces and
   source folders). It creates `docs/log/entries/<date>-<slug>.md` with the header filled.
2. Fill in the three sections:
   - **What was done** — what you examined or changed, with file paths.
   - **What was found / decided** — the findings or decision, and why. For source work,
     say what the source actually does; cite `file:line`.
   - **Lessons** — what you learned that should change how the work is done, including
     operator corrections. If nothing, write `none`. An empty or template-only Lessons
     section does not count.
3. One entry may cover several surfaces touched in the same turn. Keep it short and factual.

Entry types: `process` (what was done to or learned from the source or module code),
`decision` (a change to the standard, identity, or the decomposition definition),
`skill` (a skill was created or changed), `lesson` (a standalone lesson).

To record a lesson with no surface touched:
`python <plugin>/scripts/new_entry.py --type lesson --surfaces "" --slug <slug> --title "<lesson>"`
