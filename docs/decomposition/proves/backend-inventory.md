# PROVES backend — module inventory with status (A3)

**Source:** `PROVES_LIBRARY` at commit **02ab37e** (tracked files only; last real code change
2026-01-19, `a66a0be`). **Made:** 2026-10-20, read-only subagent pass; promotion and the
security finding re-checked by hand. Nothing was run, so runtime behaviour is not verified.
Supersedes the backend sections of [`process-log.md`](process-log.md) (R2, R3).
Labels are neutral working descriptions, not names.

**Scope rule (operator, 2026-10-20):** keep *working* and *in-progress* modules; exclude
*superseded* versions and *broken old* ones. Unmounted/unused alone is not exclusion.

> **Security:** `scripts/check_jobs.ps1:1` and `scripts/check_sources.ps1:1` contain a
> Supabase **service_role** key (verified by decoding the token's role claim, not by
> printing it), committed 2026-01-19 in a **public** repo, expiring 2036. It must be
> rotated by the operator. Nothing from these files is carried into The Lens.

## Pipeline order (stages) and modules

```text
discovery/queue → crawl/ingest → extract → validate/lineage → stage candidates
   → [human review: dashboard] → promote → library/graph → query/serve
cross-cutting: config/DB · oversight/logging
```

| # | Module (files) | Stage, order | Status | Touches |
|---|---|---|---|---|
| 1 | URL discovery + quality pre-scan (`production/scripts/find_good_urls.py`) | discovery, 1st | working | writes `urls_to_process`; reads `raw_snapshots` |
| 2 | Queueing HTTP API (`extraction-api/app.py`) | queue, 1st–2nd | working | `/extract`, `/extract/job`, `/discover`, `/jobs/{id}`, `/discover/pending`, `/queue/stats`, `/health`; `urls_to_process`, `crawl_jobs`, `team_sources` |
| 3 | Queue worker + source processors (`extraction-api/worker.py`, `processors/`) | ingest, 2nd | working (`url_list` only) | polls `urls_to_process`, `crawl_jobs`⋈`team_sources` (no claim RPC) |
| 4 | Extraction prompt builder (`extraction-api/task_builder.py`) | extract (inside 3) | in-progress — prompt is discarded by `agent_v3.py:331` | none |
| 5 | Three-agent extraction orchestrator (`Version 3/agent_v3.py`) | extract→validate→stage, 3rd | working | LangGraph checkpoint tables; calls 6–9 |
| 6 | Extractor tools (`Version 3/extractor_v3.py`) | extract | working | writes `raw_snapshots`, `pipeline_runs`; reads `core_entities`, `staging_extractions` |
| 7 | Team-source loader tools — Notion/GDrive/Discord (`Version 3/team_loaders.py`) | ingest/extract | in-progress (LLM-callable only) | `raw_snapshots`, `pipeline_runs` |
| 8 | Validator tools — lineage + duplicates (`Version 3/validator_v3.py`) | validate, 3rd | working; graph tools broken (`kg_nodes` absent live); no longer writes `validation_decisions` | reads `raw_snapshots`, `core_entities`, `staging_extractions` |
| 9 | Candidate staging writer (`storage_v3.py:63-552`) | stage, 4th | working | writes `staging_extractions` (`pending`), `knowledge_epistemics` |
| 10 | **Promotion** (`storage_v3.py:556` `promote_to_core`, driven by `curator/batch_promote_accepted.py`) | promote, after review | working (manual CLI; last logged run 2026-01-03) | `core_entities` create/merge, `knowledge_enrichment`, `entity_alias`; sets `promoted_at`/`promoted_to_entity_id`/`promotion_action` (`:719-721`) |
| 11 | Promotion dry-run report (`curator/analyze_accepted_batch.py`) | promote, before 10 | working | read-only |
| 12 | Team-source crawler (`Version 3/crawl_orchestrator.py`) | ingest, 2nd | in-progress (GitHub only; only writer of `crawl_items`; results discarded) | `claim_next_crawl_job`, `crawl_jobs`, `crawl_items` |
| 13 | Domain value objects + repositories (`production/core/domain`, `repositories`) | library (refactor) | in-progress (tested, not yet used) | `core_entities`, `raw_snapshots` |
| 14 | Legacy graph store helper (`core/graph_manager.py`) | library/graph | **broken** (`kg_nodes` not in live DB) — but imported by 8 and 9 | `kg_nodes`, `kg_relationships` |
| 15 | MCP read server (`mcp-server/`) | query/serve, last | working shell; DB tools probably broken (`$1` placeholders with psycopg3) | `staging_extractions`, `core_entities` |
| 16 | DB pool + extraction schema check (`Version 3/database.py`, `schema_validator.py`) | config | working (a second psycopg2 pool in `core/db_connector.py`) | env `DIRECT_URL`/`PROVES_DATABASE_URL`/`DATABASE_URL` |
| 17 | Error + suggestion logging (`curator/error_logger.py`) | oversight | working but unused; `scripts/improvement_analyzer.py` broken | `staging_extractions.error_log`, `improvement_suggestions` |
| 18 | Diagnostic scripts (`scripts/`) | oversight | ad-hoc | read-only checks (two carry the key above) |

Human review sits between 9 and 10 and lives in the dashboard (A1: `record_review_decision`,
`record_review_edit`); the backend no longer writes decisions.

## Superseded / dead — exclude

| Item | Replaced by |
|---|---|
| `production/Version 2/*` (deleted `9127a03`) | `production/Version 3/*` |
| `production/scripts/process_extractions*.py` (deleted `f49dab3`) | `Version 3/process_extractions_v3.py` → then module 3 |
| `Version 3/process_extractions_v3.py` (still tracked) | `extraction-api/worker.py` (module 3) |
| `production/worker/extraction_worker.py` (still tracked) | `extraction-api/worker.py` — note its one unique feature: claiming jobs via `claim_next_crawl_job`/`complete_crawl_job` |
| In-process `run_extraction_task` in `app.py` (removed `a66a0be`) | queue + worker |
| `curator-agent/*`, `.archive/legacy-agents/*` (deleted Dec 2025) | production pipeline |
| Notion sync, Neon scripts (deleted `314d7ff`) | Supabase |
| `core/exporters/*` (deleted `c7b55db`) | none |
| `core/deep_extraction_agent.py` (placeholder), `curator/subagents` package (broken imports), `.deepagents/workflows` (tutorial examples) | not runtime |
| `PROVES_NOTION/api/auto_promote.py` (untracked separate repo; Vercel cron duplicating module 10) | out of scope; deploy status not verified |

## What the live database actually had (`exports/zenodo_supabase_2026-04-25/schema.sql`, DDL only)

- Live tables no migration creates: `kg_relationships`, `core_equivalences`, `equivalences`,
  `findings`, `crawled_sources`, `derived_*`, `training_*`, `learning_log`, `risk_patterns`,
  `detected_risks`, `repository_scans`, `curator_jobs`, `builder_jobs`, `sync_metadata`,
  LangGraph `checkpoint*`.
- **Not live:** `kg_nodes` (breaks 14 and part of 8); `teams`/`team_members`/`batch_claims`
  (that migration never ran live).
- Live DB was patched outside the migrations (e.g. the org trigger no longer uses `source_id`).
- Live columns match the Python writers (`core_entities.created_by_run_id`,
  `contributed_by_org_id`; `staging_extractions.promoted_to_entity_id`, ...).

## Reuse blockers (for the neutral Lens versions)

- Hardcoded `sys.path` into `production/Version 3` and `production/core`.
- **LLM prose used as control flow** (`"REJECTED"` / `snapshot_id` string tests, regex counts).
- Orchestrator built at import time and opens a DB pool; model IDs fixed (one retired).
- Two worker paths (worker = `url_list`, crawler = GitHub) and two DB-access strategies.
- Docker image for the API does not contain the worker.
- CORS allow-list hardcodes the dashboard URL; F´/PROVES/FRAMES vocabulary throughout.

## Corrections to the 9/26 backend inventory

Promotion is Python (`promote_to_core`), not the SQL RPC; the orchestrator is a Python
wrapper, not a LangGraph graph; the validator no longer writes decisions; `graph_manager`
IS used by V3 (and is broken); `storage_v3` also holds promotion and the epistemics writes;
`process_extractions_v3` and `production/worker` are superseded; the prompt builder's
output is discarded; the in-repo `curation_dashboard/` is untracked.
