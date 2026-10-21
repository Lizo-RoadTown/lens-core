---
type: process
module: lens-core
surfaces: [source]
date: 2026-10-21T09:23
source_commits:
  PROVES_LIBRARY: 02ab37e
---

# RLS fix and proves_viewer guest access applied and verified

## What was done

- The operator ran the staged `apply_proves_viewer.py` (third attempt, after the
  percent-encoding fix); it connected via the transaction pooler on 6543,
  passed both identity guards, applied everything in one transaction, and ended
  with `ALL VERIFICATIONS PASSED`.
- Independently re-verified the end state through the read-only PROVES MCP:
  RLS enabled on all 5 previously exposed tables; role `proves_viewer` exists
  with 25 `proves_viewer_read` policies; the viewer can SELECT 49 objects
  (25 spine tables + 24 views), has zero write privileges, zero access to
  `user_oauth_tokens` / `organizations` / `organization_members` /
  `user_profiles`, and can execute zero SECURITY DEFINER functions.
- Guest credentials were written to `C:\Users\Liz\proves_viewer_credentials.txt`
  (pooler host, ports 5432/6543, connection limit 3, 30s statement timeout,
  default read-only transactions).

## What was found / decided

- The RLS exposure flagged in the 2026-10-21 verification session is closed,
  and external guests can now view the PROVES knowledge spine through a
  least-privilege login instead of any service key. This keeps the bus rule
  intact: guests get an injected connection URL, never a backend key.
- The watch item from the staging entry (anon-key reads of `core_entities`)
  is now moot for the viewer path; anon access is governed by RLS with no
  anon policy on that table.

## Lessons

The staged-script handoff pattern completed end to end across three sessions:
stage with guards, re-verify guards read-only on resume, fix at the boundary,
let the operator execute, then verify the result through an independent
read-only channel rather than trusting the script's own output. The credentials
file must be deleted once the login is passed on.
