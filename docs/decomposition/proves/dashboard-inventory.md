# PROVES dashboard — module inventory (A1)

**Source:** `proves-curation-dashboard` at commit **c484e52** (GitHub main, 2026-08-17).
**Made:** 2026-10-10, read-only subagent pass + spot checks. Supersedes the dashboard
section of [`process-log.md`](process-log.md) (lines 103-122), which was made from a clone
50 commits older. Paths below are relative to the dashboard's `src/`.
Labels are neutral working descriptions, not names.

## The big finding: half the code is not mounted

`app/App.tsx:22-23` mounts only the `Library`, `Admin` and `MissionControl` surfaces
(`app/surfaces/index.ts:1-3`), plus `MobileReview` and the auth pages. Unreachable from
`main.tsx`: the `Ask` surface, `components/instruments/*`, `PendingExtractions`,
`PeerReflection`, `CytoscapeGraph`, `KnowledgeGraph`, `Library.tsx`, `Dashboard`,
`ActivityHistory`, `ActivityFeed`, `Settings`, `FRAMESGuide`, `EvaluationCriteria`,
`CouplingCard`, `ReviewForEngineers`, `OrganizationContext`, and the hooks only they use
(`useExtractions`, `usePeerReflectionMetrics`, `useGraphData`, `useMissionControlData`,
`useAttachments`, `useMCP`, `useModelConfig`; `useEvidence` is imported by nothing).

## Shared base (not modules)

- **Supabase client** `lib/supabase.ts`: hardcoded fallback instance URL + anon key
  (`:5-6`), auth storage key with the project ref hardcoded (`:9`), `createClient` (`:11`).
- **DB types** `types/database.ts`: tables `staging_extractions`, `validation_decisions`,
  `teams`, `batch_claims`, `agent_capabilities`, `agent_proposals`, `agent_trust_history`;
  views `extractions_awaiting_review`, `review_queue_view`; functions
  `record_human_decision`, `record_review_decision`, `record_review_edit`; domain enum
  `ecosystem: 'fprime'|'proveskit'|'generic'` (`:64`).
- **Auth** `contexts/AuthContext.tsx`: password, Google and GitHub sign-in, global
  sign-out, password reset; purges localStorage keys containing `proves` (`:91`).
- **App shell**: teams/role/org from real auth + org RPCs, with fallbacks to 5 hardcoded
  universities (`App.tsx:148`) and role `"lead"` (`:152`); nav gating is client-side only;
  `pendingCount = 0` stub (`:153`); "PROVES" titles and `proves_*` storage keys.

## Mounted modules

| # | Module | Touches | Real? |
|---|---|---|---|
| R1 | Organization / tenancy (`useCurrentOrganization`, `OrganizationPicker`, `TeamDashboard`) | RPCs `get_user_organizations`, `get_org_stats`, `activate_organization` | real |
| R2 | Review queue + decision write, desktop (`useReviewExtractions`, `ExtractionDetail`, `EngineerReview`, Admin review section) | view `review_queue_view`; RPCs `record_review_decision`, `record_review_edit`; realtime on `staging_extractions` | real |
| R3 | Mobile review (`MobileReview`) | via R2; `auth.getUser` | real |
| R4 | Source registry + ingestion (`useSources`, Sources/AddSource/Ingestion sections) | `team_sources` CRUD + realtime; `crawl_jobs`; RPCs `get_ingestion_stats`, `trigger_crawl`; extraction API | real |
| R5 | Discovery client (`lib/extractionApi.ts`, `DiscoverySection`) | HTTP `VITE_EXTRACTION_API_URL` (default `localhost:8080`): `/health`, `/extract`, `/extract/job`, `/tasks/{id}`, `/discover`, `/discover/pending` | real if API up |
| R6 | Agent oversight (`AgentOversight`, `useAgentOversight`) | `agent_capabilities`, `agent_proposals` (read/update), `agent_trust_history`; realtime | real |
| R7 | Admin health/policy panels (`AdminView.tsx:328-448`) | nothing | mock |
| R8 | Library (`surfaces/Library/*`, `useLibrary`) | `core_entities` (counts, text search, lists), `core_equivalences`, `organizations` via FK `core_entities_contributed_by_org_id_fkey` | real; `referenceCount`/`needsReview` are `Math.random()` (`useLibrary.ts:179,183`) |
| R9 | Mission Control (`MissionControlView`, `Graph3D`, `PipelineColumn`, `AgentOrbs`) | RPCs `get_graph_nodes`, `get_graph_edges` | graph real; pipeline + agent panels mock |

## Unmounted modules (present, not reachable)

| # | Module | Touches |
|---|---|---|
| U1 | Legacy extraction queue (`PendingExtractions`, `useExtractions`) | `staging_extractions`; RPC `record_human_decision` (now dead code) |
| U2 | Peer reflection (`PeerReflection`, `usePeerReflectionMetrics`) | 7 views `v_confidence_calibration`, `v_rejection_trend`, `v_lineage_failures`, `v_extraction_volume`, `v_reviewer_patterns`, `v_entity_type_performance`, `v_calibration_drift_alert`; `staging_extractions` |
| U3 | Instruments (`HeatMap`, `PipelineFlow`, `useMissionControlData`) | RPCs `get_all_orgs_activity`, `get_pipeline_stats`; `staging_extractions` |
| U4 | Cytoscape graph (`CytoscapeGraph`, `useGraphData`) | RPCs `get_graph_nodes`, `get_graph_edges`, `get_graph_category_counts` |
| U5 | Ask / chat (`surfaces/Ask/*`, `useAttachments`, `useMCP`, `useModelConfig`) | `user_attachments`; attachment RPCs; MCP server (`NEXT_PUBLIC_MCP_SERVER_URL`, a Next-style env in a Vite app); direct browser calls to LLM providers with keys in localStorage; many mocks |
| U6 | Evidence / Q&A (`useEvidence`, imported by nothing) | RPCs `get_or_create_conversation`, `add_message`, `record_answer_evidence`, `get_answer_evidence`; `answer_metadata` |
| U7 | Mock leftovers (`Library.tsx`, `Dashboard`, `ActivityHistory`, `Settings`, `KnowledgeGraph`, `FRAMESGuide`, ...) | nothing |

## Reuse blockers and defects (for the neutral Lens versions)

- Hardcoded Supabase instance + anon key + auth storage key (`lib/supabase.ts:5-9`).
- Reviewer identity hardcoded `"dashboard_user"` (`AdminView.tsx:118,127,144`;
  `useAgentOversight.ts:126,145`) instead of the signed-in user.
- Org filter dropped on refresh/realtime (`useReviewExtractions.ts:338,379,399`).
- Admin approve discards the reviewer's capture answers, corrections and epistemic edits
  (`EngineerReview.tsx:344,865` vs `AdminView.tsx:114-120`).
- Mobile review never saves edits (`MobileReview.tsx:224-226`); rejects always `"other"`.
- New sources inserted without `organization_id` (`useSources.ts:146-157`); tenancy relies
  on RLS (to check against A2).
- Library filters `.eq('domain')` but stats read `attributes->domain` — possible column
  mismatch (to check against A2).
- `VITE_EXTRACTION_API_URL` missing from `.env.example`.
- Domain vocabulary throughout: `fprime`/`proveskit` ecosystems, `wrong_frames` rejection
  category, "7 Knowledge Capture Questions", FRAMES review fields, PROVES titles, university
  team lists.

## Every distinct database dependency (to match against the migrations)

- **Tables (queried):** staging_extractions, team_sources, crawl_jobs, agent_capabilities,
  agent_proposals, agent_trust_history, core_entities, core_equivalences, organizations,
  user_attachments, answer_metadata. **Typed but never queried:** validation_decisions,
  teams, batch_claims.
- **Views:** review_queue_view, v_confidence_calibration, v_rejection_trend,
  v_lineage_failures, v_extraction_volume, v_reviewer_patterns, v_entity_type_performance,
  v_calibration_drift_alert. **Typed, never queried:** extractions_awaiting_review.
- **RPCs (mounted):** get_user_organizations, get_org_stats, activate_organization,
  record_review_decision, record_review_edit, get_ingestion_stats, trigger_crawl,
  get_graph_nodes, get_graph_edges.
- **RPCs (unmounted):** record_human_decision, get_graph_category_counts,
  get_all_orgs_activity, get_pipeline_stats, get_recent_attachments,
  has_provider_connection, attach_resource, detach_resource, get_or_create_conversation,
  add_message, record_answer_evidence, get_answer_evidence.
- **Realtime:** staging_extractions, team_sources, agent_capabilities, agent_proposals.

## What the 9/26 inventory got wrong

1. Library (M4) is real (`surfaces/Library` on `core_entities`), not a mock; the mock
   `Library.tsx` is an orphan.
2. Review detail (M1) is real (`review_queue_view` + `record_review_*`); the old
   `PendingExtractions` path and `record_human_decision` are dead code.
3. Peer reflection (M3) and the mock views are unmounted, not live.
4. App shell uses real auth and org RPCs; only fallbacks are hardcoded.
5. Missed entirely: org/tenancy, sources/crawl, the extraction-API client, graph RPCs,
   Mission Control, the Ask/attachments/evidence/MCP/LLM modules.
6. `staging_extractions` is no longer "the one coupling table": live reads go through
   `review_queue_view`.
