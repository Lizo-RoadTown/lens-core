# PROVES database bus — interface map from the migrations (A2)

**Source:** `PROVES_LIBRARY/supabase/migrations/` at commit **02ab37e**.
**Made:** 2026-10-10, read-only subagent pass over all 41 SQL files; the claims marked
✔ were re-checked by hand. Nothing was executed. This is the raw material for deriving
the neutral standard (`docs/schema/spine.sql`, Phase B). Paths are relative to the
migrations folder. Labels are neutral working descriptions, not names.

## 1. The migrations are not a faithful record of the live database

- ✔ **035 is missing; 036 exists twice** (`036_org_selection_auth_flow`, `036_sandbox_auto_admin`).
  `003b`/`005b` suffixes; `20260115191105_teams_and_batch_claims.sql` sorts last but must
  have run before 032 (032 alters its functions).
- The live DB came from a Neon dump ("All migrations 000-019 were included in dump",
  `MIGRATION_LOG.md`). Migrations reference objects no migration creates:
  `004:66-70` drops an `evidence_type` column 000 never made; 032 writes RLS on ~20 tables
  with no CREATE anywhere (`kg_relationships`, `core_equivalences`, `findings`,
  `derived_graph_*`, `training_*`, ...); seeds use columns no migration adds
  (`core_entities.created_by_run_id`, `027:25`).
- **Consequence for The Lens:** the neutral standard cannot be produced by "replaying" PROVES.
  It has to be derived from what the modules actually use (A1 + this map), then made
  self-consistent.

## 2. Areas of the bus (final state)

| Area | Objects (tables / views / functions) |
|---|---|
| A. Candidate staging | `staging_extractions` (key, type, payload jsonb, confidence 0–1, status, evidence jsonb, lineage + re-extraction + org + promotion columns), `staging_relationships`, `entity_alias`, `knowledge_epistemics` (epistemic sidecar, 010) |
| B. Review decisions | `validation_decisions` (append log: decision enum, decided_by, reason, before/after/patch, rejection_category, confidence override, source flag), `validation_edits` (019), view `review_queue_view` (final 037), RPCs `record_review_decision`, `record_review_edit` (019), legacy `record_human_decision` (012), `webhook_already_processed`, stats views (012, 018) |
| C. Verified library | `core_entities` (type, canonical_key, name, attributes jsonb, is_current/superseded_by/version, verification_status, verified_by, org), `knowledge_enrichment`, `knowledge_component_relationships`, `knowledge_episode_relationships`, `promote_to_verified_knowledge` (009) |
| D. Lineage | `raw_snapshots` (source_url, payload, content_hash, source_commit_sha, ...), `pipeline_runs`, lineage columns on staging, `episodic_entities` |
| E. Ingestion / crawl | `urls_to_process` (002), `team_sources`, `crawl_jobs`, `crawl_items` (022), `curator_errors/reports`; RPCs `create_team_source`, `trigger_crawl`, `claim_next_crawl_job` (`FOR UPDATE SKIP LOCKED`), `complete_crawl_job`, `get_ingestion_stats` |
| F. Agent oversight | `agent_capabilities`, `agent_proposals`, `agent_trust_history` (017) + triggers: auto-approve when trust ≥ threshold, trust +0.05 approve / −0.10 reject; `improvement_suggestions` (006, overlapping) |
| G. Orgs / teams / auth | `organizations`, `organization_members` (023), `user_profiles` (031), `app_settings` (036), `teams`/`team_members`/`batch_claims` (20260115...); role and active-org RPCs; sign-up trigger |
| H. Knowledge graph | `get_graph_*` RPCs (024–028) reading `core_entities` + `core_equivalences`; the `kg_*`/`core_equivalences` tables exist only outside the migrations |
| I. Attachments / answers | `user_attachments`, `user_oauth_tokens` (020), `conversations`, `messages`, `answer_evidence`, `answer_metadata` (021) |

**Spine links:** A→D (`snapshot_id`, `pipeline_run_id`); A↔B (`validation_decisions.extraction_id`
and `staging.latest_decision_id`); A→C (`staging.promoted_to_entity_id`); C→D
(`core_entities.source_snapshot_id`); A/C/E→G (org columns). Several cross-area links are
soft (uuid arrays or polymorphic ids, no FK): crawl items→staging, batch claims, agent
proposals→extractions, answer evidence→sources.

**Final enums:** `candidate_status` = pending, accepted, rejected, needs_context, merged,
flagged; `validation_decision_type` = accept, reject, needs_more_evidence, defer, merge,
edit, flag_for_review, request_more_evidence; `entity_type` = component, interface,
subsystem, dependency, connection, port, event, telemetry, data_type, parameter, command;
`ecosystem_type` = fprime, proveskit, generic (domain-specific).

## 3. The behavioral contract (functions) and its defects

- ✔ **`promote_to_verified_knowledge` (009) is broken after 011**: it inserts dimension
  columns (`knowledge_form`, `contact_level`, ...) that `011:92-93` drops, and no later
  migration redefines it. **No SQL function sets `promoted_at`/`promoted_to_entity_id`**;
  promotion must happen outside the DB (not verified where).
- ✔ **`record_review_decision` (019) vs CHECK**: writes the decision value into
  `review_decision` (`019:290`), but `005b:13` only allows approve/reject/modified; an
  `accept`/`merge`/`defer` would fail (not verified at runtime).
- ✔ **`staging_extractions_auto_org` trigger reads `NEW.source_id`** (`023:454-456`); no
  migration adds that column.
- **`review_queue_view` loses `security_invoker`** when 037 drops and recreates it (inferred),
  and 037's `DROP ... CASCADE` likely drops `get_org_review_queue_v2` (inferred).
- **Sign-up trigger** (final `036_sandbox:100`): while `app_settings.sandbox_mode = true`,
  every new user becomes admin of every org.

## 4. Access control

- RLS (032) gates by `user_profiles` flags (engineer / researcher / admin); **no policy checks
  the organization** for staging, decisions or the library. Org isolation exists only on
  `organizations`/`organization_members`, `team_sources` writes, and inside SECURITY DEFINER
  functions.
- ✔ **Anonymous access (033):** anon can SELECT staging, snapshots, decisions, edits and
  `review_queue_view`, and EXECUTE `record_review_decision`/`record_review_edit` (`033:26-27`);
  the A2 pass also reports anon UPDATE on staging and INSERT on decisions/edits with
  `USING(true)`.
- Three authorization models coexist: `user_profiles` flags, `organization_members.role`,
  `team_members.role`.

## 5. Duplicate or divergent models

1. Relationships stored four ways: `staging_relationships`, `knowledge_component_relationships`,
   `core_equivalences`, `kg_relationships` (the graph uses `core_equivalences`).
2. Aliases three ways: `entity_alias` (points at **staging**), `knowledge_enrichment`
   type alias, view `entity_aliases`.
3. Review state four ways: `staging.status`, `staging.review_decision`,
   `validation_decisions.decision`, `improvement_suggestions.review_decision`; reviewer as
   text and as uuid side by side.
4. Two dimension models (008/009 rolled back by 011; 010 epistemics sidecar kept).
5. Two tenancy models: organizations vs teams (not linked).
6. Two proposal mechanisms: `improvement_suggestions` vs `agent_proposals`.
7. `ecosystem` as TEXT in `raw_snapshots`, enum elsewhere.

## 6. Data, not schema

Seed/test migrations 025, 027, 029, 030; seed rows inside 017 (agents), 023 (default org),
036 (`sandbox_mode=true`, backfill all users as admin). University/org names hardcoded in
023, 029, 030 and the sign-up function.

## 7. Domain-specific vocabulary to strip for the neutral standard

`ecosystem` (fprime/proveskit), `entity_type` values (component, telemetry, port, ...),
rejection categories `wrong_frames`/`wrong_ecosystem`, `notion_*` and LangGraph
`*_thread_id` columns, `standard_*` (XTCE/SysML) on enrichment, epistemic sidecar
vocabulary (010), `org_type` default `university`.

## How this matches the dashboard (A1)

Everything the mounted dashboard touches exists here (`review_queue_view`,
`record_review_*`, org RPCs, `team_sources`/`crawl_jobs`, `agent_*`, `core_entities`,
graph RPCs) **except `core_equivalences`**, which only exists outside the migrations.
