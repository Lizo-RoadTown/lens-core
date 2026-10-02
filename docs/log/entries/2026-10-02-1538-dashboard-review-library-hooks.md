---
type: process
module: lens-core
surfaces: [source]
date: 2026-10-02T15:38
source_commits:
  proves-curation-dashboard: c484e52
---

# Dashboard Library and review hooks are real, not mocks

## What was done
Read two data hooks in the PROVES dashboard (read-only), after fast-forwarding the
local clone from 2687a35 to GitHub main c484e52 (it had been 50 commits behind):

- `proves-curation-dashboard/src/hooks/useLibrary.ts` lines 1-60
- `proves-curation-dashboard/src/hooks/useReviewExtractions.ts` lines 1-80

This was also the first live test of the lens-log enforcement: the PostToolUse hook
recorded the read, and the Stop hook blocked the turn until this entry existed.

## What was found / decided
- **Library has a real backend.** `useLibrary.ts:5` searches `core_entities`;
  `useLibrary.ts:38-44` maps library tiles (procedures, architecture, interfaces,
  decisions, lessons) to `entity_type` values. The 2026-09-26 inventory's "Library is a
  full mock, no backend" (`docs/decomposition/proves/process-log.md:118`) was made from
  the stale clone and is wrong for the current source.
- **Review detail is real.** `useReviewExtractions.ts:4` reads `review_queue_view` and
  writes through `record_review_*` RPCs; it parses typed evidence (raw text, byte
  offset/length, checksum, rationale, duplicate check) at `:61-79` and carries lineage,
  snapshot, confidence, latest decision and epistemics types (`:10-21`). It filters by
  `organizationId` for tenant isolation (`:51`). The inventory's "real list, MOCK detail"
  is also wrong for the current source.
- Not yet decided: what this means for the neutral spine. The review RPC names and the
  evidence shape are inputs to re-deriving `docs/schema/spine.sql`; the full dashboard
  re-inventory is still to do.

## Lessons
- An inventory must record the source commit it was made from. The earlier one did
  not, and a stale clone silently produced wrong module findings. lens-log now fills
  `source_commits` automatically.
- Install path case matters on Windows: installing the plugin from a shell recorded
  `C:\...` while the VS Code session uses `c:\...`, so the plugin "wasn't installed" for
  this project until the row was corrected.
