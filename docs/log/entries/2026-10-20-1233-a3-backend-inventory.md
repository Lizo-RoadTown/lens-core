---
type: process
module: lens-core
surfaces: [source]
date: 2026-10-20T12:33
source_commits:
  PROVES_LIBRARY: 02ab37e
---

# A3: backend inventory with status at 02ab37e

## What was done
- Read-only subagent inventoried the tracked backend (production/, extraction-api/,
  mcp-server/, scripts/, .deepagents/, supabase/ tooling), its git history, and the DDL of
  the live-database export (`exports/zenodo_supabase_2026-04-25/schema.sql`).
- Re-checked by hand: promotion lives in `production/Version 3/storage_v3.py:556`
  (`promote_to_core`, sets promotion columns at `:719-721`), driven by
  `production/curator/batch_promote_accepted.py:56,203`; the committed key's role claim.
- Recorded `docs/decomposition/proves/backend-inventory.md`.

## What was found / decided
- 18 modules with stage, order and status: working (discovery, queue API, worker,
  orchestrator, extractor, validator, staging writer, promotion, DB pool), in-progress
  (prompt builder, team loaders, GitHub crawler, domain repositories), broken
  (graph helper on `kg_nodes`, which the live DB does not have).
- Superseded and excluded: Version 2, `process_extractions_v3.py`,
  `production/worker/extraction_worker.py`, the old in-process task runner, curator-agent,
  Notion/Neon tooling.
- Promotion is Python, run manually; the SQL function is dead. The backend no longer
  writes review decisions; the dashboard RPCs do.
- SECURITY: a Supabase service_role key is committed in `scripts/check_jobs.ps1:1` and
  `scripts/check_sources.ps1:1` in a public repo. Reported to the operator for rotation;
  not copied anywhere (memory `security-proves-library-committed-service-role-key-2026-10-20`).

## Lessons
A prototype's migrations, live database and code can each tell a different story; the
live-schema export settled which tables really existed. Inventory passes should also
scan for committed secrets, since a read-only decomposition is often the first full read.
