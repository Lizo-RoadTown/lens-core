---
type: process
module: lens-core
surfaces: [source]
date: 2026-10-20T12:26
source_commits:
  PROVES_LIBRARY: 02ab37e
---

# A3 in progress: backend reads by the subagent (interim)

## What was done
The A3 read-only subagent (dispatched 2026-10-20, entry
`2026-10-20-1221-scope-working-parts-labels-doc-agents.md`) is reading the PROVES backend:
`production/` (Version 3, core, curator, worker, scripts), `extraction-api/`, `mcp-server/`,
and git history (`git log --all --name-status` over earlier version folders) to find
superseded versions. These reads landed while the main session finished the Tapestry docs
survey, so they need an entry before A3 itself reports.

## What was found / decided
Nothing yet; the A3 findings get their own entry when the report arrives.

## Lessons
A long-running background subagent produces source touches across several of the
main session's turns; each of those turns needs an interim entry. Expected, not a defect.
