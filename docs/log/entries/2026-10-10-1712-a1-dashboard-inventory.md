---
type: process
module: lens-core
surfaces: [source]
date: 2026-10-10T17:12
source_commits:
  proves-curation-dashboard: c484e52
---

# A1: dashboard re-inventory at c484e52

## What was done
- Read-only subagent inventoried every module of `proves-curation-dashboard` (hooks,
  lib, types, surfaces, components), with the tables / views / RPCs / external calls each
  touches and file:line evidence.
- Spot-checked the key claims myself: `app/App.tsx:22-23` mounts only Library, Admin,
  MissionControl (+ MobileReview); no file imports `PeerReflection`, the Ask surface, or
  `PendingExtractions`; `hooks/useLibrary.ts:179,183` use `Math.random()`.
- Recorded the result in `docs/decomposition/proves/dashboard-inventory.md` (pinned to
  c484e52; supersedes `process-log.md:103-122`).
- Live test of lens-log subagent capture: the PostToolUse hook recorded 51 touches,
  including the A2 subagent's shell reads of the migrations. Subagent capture works.

## What was found / decided
- About half of the dashboard's `src/` is not mounted (Ask, peer reflection, instruments,
  cytoscape graph, evidence/Q&A, legacy queue, mock views).
- Nine mounted modules (R1-R9): org/tenancy, review queue + decisions, mobile review,
  sources/ingestion, discovery API client, agent oversight, mock admin panels, Library,
  Mission Control.
- The 9/26 inventory was wrong on Library, review detail, peer reflection and the app
  shell, and missed org/tenancy, sources/crawl, discovery, graph RPCs, Mission Control,
  and the Ask/evidence modules.
- Reuse blockers recorded for the neutral versions: hardcoded instance/keys, hardcoded
  reviewer `"dashboard_user"`, dropped org filter, discarded reviewer input, domain
  vocabulary.
- Open: whether unmounted modules count as part of the prototype "that works" (an
  operator call for A4).

## Lessons
Reachability matters for decomposition: "present in the repo" is not "part of the
working system". An inventory should mark mounted vs unmounted, not only real vs mock.
