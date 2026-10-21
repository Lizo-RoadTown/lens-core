---
type: process
module: lens-core
surfaces: [source]
date: 2026-10-21T06:32
source_commits: {}
---

# proves_viewer read-only SQL verified against the live PROVES database

## What was done
- Probed the live PROVES database over the read-only Supabase MCP (the source read
  was the live DB, not a local folder, so `source_commits` is empty): table list,
  row counts, `pg_roles`, `pg_policies`, view `security_invoker` flags, and
  `SECURITY DEFINER` functions in `public`.
- Rewrote the `proves_viewer` read-only login SQL from the live state and saved it
  outside this repo (PROVES backend specifics stay out of public lens-core), at
  `C:\Users\Liz\proves_viewer_setup.sql`. Nothing was executed; the MCP is read-only
  and the operator runs the SQL herself.

## What was found / decided
- The database is live with real data (211 staging extractions, 121 core entities,
  339 validation decisions). No `proves_viewer` role exists yet.
- Grants alone are not enough: every spine table except `core_entities` has RLS
  enabled and its SELECT policies target only `anon`/`authenticated`, so a new login
  role would see zero rows. The SQL adds a `for select to proves_viewer using (true)`
  policy per granted table.
- All 46 `SECURITY DEFINER` functions in `public` are executable by PUBLIC, including
  write/privilege functions (`make_admin`, `grant_capabilities`,
  `record_review_decision`). The SQL revokes PUBLIC execute on definer functions and
  re-grants to `anon`/`authenticated`/`service_role`, otherwise the viewer login is
  not actually read-only.
- Scope decided: 25 knowledge-spine tables + 24 analysis views; user/org/auth/agent
  ops tables excluded. `review_queue_view` is the one definer view; verified it reads
  only granted tables.
- Supabase advisory, for the operator: 5 tables have RLS disabled entirely
  (`core_entities`, `user_oauth_tokens`, `organizations`, `organization_members`,
  `user_profiles`) and are fully exposed to the anon key. `user_oauth_tokens` stores
  OAuth tokens. This compounds the still-unrotated leaked service_role key.

## Lessons
A "read-only Postgres login" on Supabase takes three independent layers: SELECT
grants, RLS policies naming the role, and a PUBLIC-execute lockdown on
SECURITY DEFINER functions. Any one alone silently fails open (writes via RPC)
or closed (zero rows). Verify all three against the live catalog, not the schema docs.
