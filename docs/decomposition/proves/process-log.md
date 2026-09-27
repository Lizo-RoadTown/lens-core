# PROVES decomposition — process log (living)

**Status:** in progress, started 2026-09-26. Capture-as-we-go (IAKM principle:
record the process + provenance while it happens, before loss).

**Read-only constraint:** `C:\Users\Liz\PROVES_LIBRARY`, `C:\Users\Liz\proves-curation-dashboard`,
`C:\Users\Liz\proves-paper-explainer` are **source only** — never modified. All
decomposition output lands in Tapestry (here) or new repos, never in them.

**Terms:** neutral NDA — module / coupling / interface / sustaining mechanism.
No coined or proprietary names; the operator names the pieces.

---

## The process (this is what becomes the decomposition plugin's skills)

1. **Orient to the whole** — state what the system is and the end goal, so no
   agent mistakes its slice for the whole.
2. **Read-only inventory** — per repo, enumerate candidate modules.
3. **Interface mapping** — for each module, the interface it depends on (DB
   tables / RPCs / MCP calls / imports). A module's real interface is *what it
   touches*, nothing more.
4. **Bond-strength seams** — cluster tight-internal / loose-across; flag where a
   seam must be *defined* because coupling is tangled.
5. **Name (operator-led)** — placeholder NDA labels until the operator names them.
6. **Repo-tree logic** — composable drop-in modules + a self-locating index the
   tree can read (so a repo can "call into itself").
7. **Extract to plugin** — crystallize steps 1-6 into reusable skills.

---

## The whole (orientation)

PROVES is an agentic knowledge-extraction + curation system for modular
university space programs (PROVES Kit / F´ satellite work). Extraction reads
artifacts and writes candidate records to a staging database; a dashboard lets a
human review/verify them into a core library; agent-health/oversight tracks the
agents' proposals and trust. Grounded in the operator's IAKM methodology and
nearly-decomposable architecture (Simon 1962). Goal of THIS effort: find the
reusable modules so they become standalone, mix-and-match pieces.

---

## Findings so far (first pass — deeper read in progress)

### Dashboard repo (`proves-curation-dashboard`, React/Vite/Supabase)
Features are loosely coupled — each talks to a distinct table-set (the seam):
- **Extraction review** — `useExtractions` ↔ `staging_extractions` + `record_human_decision` RPC (`src/hooks/useExtractions.ts:5,42,61`).
- **Agent health / oversight** — `useAgentOversight` ↔ `agent_capabilities`, `agent_proposals`, `agent_trust_history` (`src/hooks/useAgentOversight.ts:5-7`). Its own logic (trust, proposal lifecycle, auto-approve thresholds).
- **Library** — `src/app/components/Library.tsx` (verified-records view; tables TBC).
- **Shared substrate (sustaining mechanism)** — Supabase client + generated DB types + auth + `ui/` kit.

### Extraction side (`PROVES_LIBRARY`, top-level candidate modules)
`extraction-api/`, `production/` (core/curator/worker/schemas — the pipeline),
`mcp-server/` (agent-facing interface), `supabase/` (schema/migrations),
`canon/` (theory/ontology), `PROVES_NOTION/` (nested repo — Notion sync).

### The load-bearing interface
The **database schema** (Supabase tables) is the low-bandwidth interface between
most modules; the **MCP server** is the agent-facing interface. Extraction
*writes* staging; the dashboard *reads* staging + records decisions + reads agent
health.

### Open flags
- **Reusability blocker:** `proves-curation-dashboard/src/lib/supabase.ts:5-6`
  hardcodes a specific Supabase URL + anon key as fallback. A drop-in module
  can't hardcode its backend — that coupling must become an injected interface.
- **Duplication:** a `curation_dashboard/` exists *inside* `PROVES_LIBRARY` AND
  as the separate `proves-curation-dashboard` repo — reconcile during decomposition.

---

## Research log (read-only passes)

- 2026-09-26 — deployed 3 read-only researchers: (R1) dashboard modules+interfaces,
  (R2) extraction pipeline modules+interfaces, (R3) shared interface layer
  (supabase schema + mcp-server). Findings appended here on return.
  - **R3 RETURNED 2026-09-26** — captured below. R1, R2 still running.

## Interface inventory — the shared seam (R3, 2026-09-26)

**Primary coupling seam = the database schema** (`PROVES_LIBRARY/supabase/migrations/`).
Within it, the load-bearing spine is a triad:

`staging_extractions` (`000_initial_base_schema.sql:73`, status starts `pending` @:87)
→ `validation_decisions` (append-only decision log, `000:111`)
→ `core_entities` (verified layer, versioned via `is_current`/`superseded_by`, `000:130`).

- **Extraction pipeline** writes `staging_extractions` (+ `raw_snapshots` `000:61`, `pipeline_runs` `000:51`); never reads dashboard state.
- **Dashboard** reads staging + views, writes decisions via RPC `record_human_decision` (`012_enhance_human_approval_workflow.sql:188`), and promotes into core via RPC `promote_to_verified_knowledge` (`009_add_verified_knowledge_layer.sql:382`). Promotion is idempotent via `staging_extractions.promoted_at/promoted_to_entity_id/promotion_action` (`013_add_promotion_tracking.sql:12-25`); queue/metrics views `extractions_awaiting_promotion` (`013:68`), `promotion_statistics` (`013:91`).
- **Agent oversight** is a *parallel, self-contained* triad: `agent_proposals` → `agent_capabilities` (trust_score, auto_approve_threshold) → `agent_trust_history`, all in `017_add_agent_oversight.sql`, mediated by DB **triggers** not app code (`check_auto_approve` `017:293`/`:359`; `update_agent_trust_on_review` `017:161`/`:347` = +0.05 approve / −0.10 reject; `update_agent_trust_on_measurement` `017:229`/`:353`). This is a sustaining mechanism that can move with the agent-health module.

Two contracts live in the schema: (1) shared **tables** = data contract; (2) **RPCs/triggers** = behavioral contract that moves rows across the staging→core and proposal→trust boundaries. Key enum `decider_type` (human/agent) is what distinguishes agent vs human writes to `validation_decisions`.

**Secondary interface = MCP server** (`PROVES_LIBRARY/mcp-server/`, FastMCP "PROVES Library" `server.py:33`): 18 tools, **zero** resources/prompts. DB-backed tools (`search_knowledge` `server.py:40`, `get_entity` `:100`, `list_entities` `:120`, `get_library_stats` `:153`, `health_check` `:717`) are **read-only** (SELECT-only via `db.py` singleton; never writes, never calls RPCs). Plus registry-backed tools (static `source_registry.yaml`) and external-reach tools (`external.py`, URL/suggestion generators — no DB). Config: `DATABASE_URL`, `NEXT_PUBLIC_SUPABASE_URL/ANON_KEY`, `ANTHROPIC_API_KEY` (`config.py:21-41`). → The MCP server is a clean read-only projection of the schema; it carries none of the write-path coupling, so it's a strong candidate standalone module.

**Peripheral module groups seen in schema** (loosely coupled, mostly dashboard-side): Notion sync (`003`), ingestion/crawl queue (`002`, `022`), Q&A + answer-evidence (`021`), auth/RBAC/orgs/teams (`020`, `023`, `031`, `036`, teams migration), knowledge-graph API for the Cytoscape renderer (`024`/`026`/`028`).

**Flags:** `consolidated_migrations_001_to_015.sql` duplicates 001–015 (not an independent source). `agent_*` tables have RLS (authenticated-read + service_role-all, `017:382-426`).

---

## Module inventory — dashboard repo (R1, 2026-09-26)

Seam rule used: one feature component + the hook it exclusively owns + the tables/RPCs/channels that hook touches = one module. Client, DB types, auth, UI kit = shared substrate.

**Shared substrate (sustaining mechanisms, not features):**
- **S1 Supabase client** — `src/lib/supabase.ts:8`. Hard pin: hardcoded instance URL + anon JWT fallback at `:5-6`. Every data module funnels through this — the tightest coupling point in the repo.
- **S2 Generated DB types** — `src/types/database.ts` (tables: `staging_extractions:30`, `validation_decisions:78`, `teams:102`, `batch_claims:117`, `agent_capabilities:133`, `agent_proposals:158`, `agent_trust_history:205`; view `extractions_awaiting_review:219`; RPC `record_human_decision:237`). Several typed tables are unread by any component — latent surface.
- **S3 Auth** — `src/contexts/AuthContext.tsx` (`supabase.auth.*` only; OAuth google/github). Portable except providers must be enabled on the pinned instance.
- **S4 UI kit** — `src/app/components/ui/**` (~45 shadcn/Radix wrappers). Pure presentational, high fan-in.
- **App shell** — `App.tsx` (view-state switch, hardcoded `teams`/`userRole`/`pendingCount` stubs `:48-51`), `main.tsx`, `Navigation.tsx`, `Header.tsx`. Thin shell, not a feature.

**Feature modules (candidates), by bond strength:**
- **M1 — Extraction review queue** (operator's "observation window"): `PendingExtractions.tsx` + `ExtractionDetail.tsx` + `useExtractions.ts`. Interface: `staging_extractions` SELECT pending (`useExtractions.ts:39-44`) + realtime channel (`:16-29`) + RPC `record_human_decision` (`:61-66`,`:80-85`). **Broken seam:** `ExtractionDetail.tsx` is entirely mock (`:63-87`), disconnected from the hook/RPC; batch-claim is an `alert()` stub. Actor hardcoded `'dashboard_user'` (`:64,:83`), not wired to S3 auth.
- **M2 — Agent oversight** (operator's "agent health"): `AgentOversight.tsx` + `useAgentOversight.ts`. Interface: `agent_capabilities` (SELECT+UPDATE), `agent_proposals` (SELECT+UPDATE lifecycle), `agent_trust_history` (SELECT) + 2 realtime channels. Cohesive (proposals↔capabilities joined in-hook). Fully real. Reviewer id hardcoded `'dashboard_user'` (`:126,:145`).
- **M3 — Peer reflection analytics** (read-only): `PeerReflection.tsx` + `usePeerReflectionMetrics.ts`. Interface: 7 `v_*` analytics views + `staging_extractions` (read-only), graceful fallback if views absent. **Undeclared interface**: the `v_*` views aren't in `database.ts`. Shares `staging_extractions` (read) with M1.
- **M4 — Library** (operator's "library function"): `Library.tsx`. **Currently a full mock** — hardcoded `verifiedEntities` array (`:23-84`), static non-functional filters; **no Supabase, no backend coupling at all.** To become real it needs a verified-entities table/view binding (none typed yet).
- **Mock-only views** (UI shell + mock data, no backend): `Dashboard.tsx`, `ActivityHistory.tsx`, `Settings.tsx`.

**Dashboard seam summary:** genuinely backend-coupled = M1, M2, M3. UI-only-so-far = M4, Dashboard, ActivityHistory, Settings. Universal reuse blocker = the single hardcoded instance+key at `lib/supabase.ts:5-6`. Recurring gap = writer identity hardcoded `'dashboard_user'` instead of S3 auth. `staging_extractions` is the one table coupling two feature modules (M1 write-path + M3 read).

## Module inventory — extraction side (R2, 2026-09-26)

Dominant coupling: every backend module re-resolves ONE Postgres from env `DIRECT_URL|PROVES_DATABASE_URL|DATABASE_URL` (inline, duplicated). Empty shells confirmed: `curator-agent/` = only TRACING_GUIDE.md; `PROVES_AI/` = only a doc.

Candidate code modules (label — what — interface/seam — provenance):
- **A. Queueing API** — thin FastAPI, does NOT extract; enqueues URLs/jobs. Writes `urls_to_process` (`extraction-api/app.py:285-292`), reads `crawl_jobs`/`team_sources`. CORS hardcodes the dashboard URL (`app.py:230-231`).
- **B. Worker / processor dispatch** — polls `urls_to_process`+`crawl_jobs`, routes by `source_type`, builds a FRAMES prompt, invokes the V3 graph (`extraction-api/worker.py`, `processors/base.py:57-210`). `task_builder.py` is pure prompt construction — the cleanest standalone unit. Tight to V3 via hardcoded `sys.path` (`worker.py:34-42`) + parsing LLM prose (`base.py:190-210`).
- **C. V3 pipeline orchestrator** — Extractor→dup-check→Validator→Storage via LangGraph + ChatAnthropic; PostgresSaver checkpointer (`production/Version 3/agent_v3.py:66-107`); regex-parses LLM text as control flow (`:180-206`).
- **D. V3 extractor tools** — web/GitHub fetch; writes `raw_snapshots` (`extractor_v3.py:138`); reads verified entities (`:689`).
- **E. V3 validator tools** — lineage + duplicate/schema checks; highest DB touch (`staging_extractions`/`core_entities`/`raw_snapshots`/`validation_decisions`), `validator_v3.py:147,313,685`.
- **F. V3 storage tool** — terminal write `INSERT staging_extractions` (`storage_v3.py:452`).
- **G. Source loaders** — Notion/GDrive/Discord fetchers, each env-keyed; write `raw_snapshots` (`team_loaders.py:72,100-148`). Per-source decomposable.
- **H. Batch/crawl orchestration** — `process_extractions_v3.py` + `crawl_orchestrator.py`; **crawl_orchestrator is a PARALLEL entry point that also invokes `agent_v3.graph`** (`:44-48`) — duplicated orchestration with B.
- **I. Discovery / URL pre-scan** — `SmartWebFetchAgent` writes `urls_to_process` (`production/scripts/find_good_urls.py:307`). Clean DB seam.
- **J. Promotion / curator batch** — post-review: reads accepted `staging_extractions`, promotes to `core_entities` (`production/curator/analyze_accepted_batch.py:51,67`, `batch_promote_accepted.py:54`). The human-review boundary.
- **K. Core domain + repositories** — `core/domain/` pure value objects (reusable, low IO); `core/repositories/` over `core_entities` (**not used by V3**, which uses inline SQL → duplicated DB strategy); `core/graph_manager.py` writes `kg_nodes`/`kg_relationships` — a **divergent/legacy graph schema** apparently unused by V3.
- **L. MCP read server** — FastMCP, read-only over the shared DB; own pyproject/Dockerfile → **most independently deployable module** (`mcp-server/`).

**Duplication flags:** worker (B) vs crawl_orchestrator (H); two DB-access strategies (repositories vs inline SQL); `kg_*` vs `core_entities` schemas. **In-repo `curation_dashboard/`** is a Figma export (`package.json` name `@figma/my-make-file`, README "Engineer Interface UX Design") — likely duplicates the separate dashboard repo; backend CORS expects `proves-curation-dashboard.vercel.app`.

## Synthesis — consolidated candidate modules (UNNAMED; operator names these)

Working descriptions only (from code identifiers) — **not names**. Numbered for reference. The DB schema is the interface bus every module rides.

**Backend (Python, one Postgres):**
1. Discovery / URL pre-scan (R2:I) — seam: `urls_to_process`. Cleanly reusable.
2. Queueing API (R2:A) — seam: `urls_to_process`/`crawl_jobs`/`team_sources`.
3. Ingestion/crawl orchestration (R2:B+H) — **consolidate the two entry points**.
4. Extraction pipeline core (R2:C+D+E+F, tight cluster) — with prompt-builder (task_builder) extractable as its own piece.
5. Source loaders (R2:G) — per-source sub-modules (Notion / GDrive / Discord).
6. Promotion / curator batch (R2:J) — seam: `staging_extractions`→`core_entities`.
7. Core domain value objects + repositories (R2:K) — reusable, currently bypassed.
8. Knowledge-graph store `kg_*` (R2:K) — isolated/divergent; decide keep-or-retire.
9. MCP read server (R2:L) — most independently deployable.

**Frontend (React, one Supabase):**
10. Extraction review queue (R1:M1) — real list, mock detail (fix seam).
11. Agent oversight / health (R1:M2) — real, cohesive.
12. Peer-reflection analytics (R1:M3) — real, read-only.
13. Library / verified-entities view (R1:M4) — **currently a mock stub; no backend.**
14. Overview / activity / settings shells (R1) — mock; not yet modules.

**Shared interface bus (the coupling all of the above ride):** the Postgres/Supabase schema — spine `staging_extractions → validation_decisions → core_entities`; ingestion (`urls_to_process`/`crawl_jobs`/`team_sources`/`crawl_items`); lineage (`raw_snapshots`); oversight triad (`agent_*`); isolated (`kg_*`). Behavioral contract = RPCs/triggers (`promote_to_verified_knowledge`, `record_human_decision`, agent-trust triggers).

**Cross-cutting reuse blockers (must become injected interfaces for mix-and-match):**
- DB connection re-resolved inline in every backend module; frontend hardcodes the Supabase instance+anon key (`lib/supabase.ts:5-6`).
- Hardcoded `sys.path` to `production/Version 3`; hardcoded source URLs/registries; CORS allowlist.
- Fragile text-format (LLM-prose) coupling between worker and V3.
- Duplications listed above (orchestration; DB strategy; graph schema; in-repo dashboard export).

**Repo-tree implication:** a reusable drop-in module = its code + a manifest declaring what it reads/writes on the bus (tables / RPCs / MCP tools) + an *injected* connection (no hardcoded instance). The schema is effectively the index modules resolve through — that's what lets a repo "call into itself."

## Operator oversight kit

**Lookup items (check these yourself):** this log · the module list (below, as it
fills) · the interface inventory · the read-only proof (`git -C <repo> status --porcelain` clean for all three).

**Prompts for your outside agents:**
- "Here is the module list [paste]. Find overlaps/gaps. Which module owns `<capability>`? Is any module bunched with another that should be separate?"
- "For module X, is its listed interface (tables/RPCs/MCP calls) actually all it touches, or is there hidden coupling?"
- "Confirm the source repos are untouched: `git -C <repo> status --porcelain` for all three; show clean."
