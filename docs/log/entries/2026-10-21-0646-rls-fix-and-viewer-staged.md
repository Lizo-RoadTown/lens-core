---
type: process
module: lens-core
surfaces: [source]
date: 2026-10-21T06:46
source_commits:
  PROVES_LIBRARY: 02ab37e
---

# RLS fix and proves_viewer apply script staged; execution awaits the operator

## What was done
- The operator asked to apply the RLS fix and create the `proves_viewer` access (not
  just draft it). Checked write paths: the local PROVES MCP is read-only by design;
  the claude.ai Supabase connector sees only an unrelated project.
- Listed variable names only (no values) in `PROVES_LIBRARY/.env` to confirm usable
  connection URLs exist (`PROVES_DATABASE_URL`, `DATABASE_URL`, `DIRECT_URL`), and
  confirmed psycopg 3.2.3 is installed (no psql).
- Wrote a single apply script in the session scratchpad
  (`apply_proves_viewer.py`): identity guard (expected row count, role absent),
  enable RLS on the 5 exposed tables, create `proves_viewer` with grants + per-table
  policies + SECURITY DEFINER lockdown, verify as the viewer, write credentials to
  `C:\Users\Liz\proves_viewer_credentials.txt`.

## What was found / decided
- Execution was denied by the permission layer (write to a production database).
  Decided not to route around it: the command was handed to the operator to run
  with the `!` prefix. Nothing has been applied yet.
- Enabling RLS on the 5 tables is safe-by-policy (all five already have policies);
  the one watch item is anon-key reads of `core_entities`, which has no anon policy.

## Lessons
When the operator asks for a write to a protected backend, stage everything
(script, guards, verification) up to the execution boundary and stop there —
the denial then costs one keystroke, not a redo. Guards belong in the script
itself (expected row count, role-absent check), not in the conversation.
