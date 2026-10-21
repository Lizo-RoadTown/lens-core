---
type: process
module: lens-core
surfaces: []
date: 2026-10-21T09:28
source_commits: {}
---

# Recorded: the memory service moves to Loom_MCP now; ID register unified

## What was done
Recorded two facts relayed by tapestry-34 and checked against loom memory
(`decision-memory-service-moves-to-loom-mcp-now-2026-10-21`):
- **Liz's decision:** the loom memory service moves to its own repo,
  `Lizo-RoadTown/Loom_MCP` (private), now.
  - P1 (copying the service and tests, CI green) is running.
  - Production keeps deploying from tapestry until the gated P3 switch.
  - The service name `loom-agent-context`, its URL and `TAPESTRY_MEMORY_API_KEY` are kept.
  - The OAuth brief (`for-loom-memory-mcp-oauth-brief-2026-10-21`) lands in Loom_MCP after
    P1.
- **One ID scheme across layers** (tapestry commit 89e4f54):
  - `pl-*` personal layer, `sh-*` shared, `pr-*` program layer (lens-core's, source of truth
    in `decomposition.json` `ids`).
  - Tapestry's `component-NNN` numbers are retired unused. component-017 is now pr-001.
  - The roadmap's citation of pl-001 (the personal-signal-engine package lens-observe will
    instantiate) is unchanged.

## What was found / decided
Nothing lens-core depends on changes. Its only dependency on the memory service is the
`.mcp.json` URL, kept through the move. No roadmap item changes.

## Lessons
A move that preserves the service name and URL lets every consumer stay untouched. Record that
guarantee next to the move so consumers don't re-check it.
