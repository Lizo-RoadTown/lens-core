---
type: process
module: lens-core
surfaces: [source]
date: 2026-10-21T09:16
source_commits:
  PROVES_LIBRARY: 02ab37e
---

# proves_viewer apply script: connection failures diagnosed and fixed

## What was done

- The operator ran the staged `apply_proves_viewer.py` (`!` handoff from the
  previous entry); every connection candidate failed. Probed the structure of the
  three URLs in `PROVES_LIBRARY/.env` (`PROVES_DATABASE_URL`, `DATABASE_URL`,
  `DIRECT_URL`) printing only user/host/port/query/password-length — no secrets.
- Re-verified the identity guard read-only via the PROVES MCP before anything
  else: `staging_extractions` = 211, unchanged. Confirmed nothing was applied
  (no credentials file, role absent).
- Fixed the script (session scratchpad): connect with psycopg keyword arguments
  instead of URIs, try pooler port 6543 before 5432, `prepare_threshold=None`,
  and list both pooler ports in the credentials file it writes.

## What was found / decided

- The database password contains a literal `%`. The script's pooler-fallback
  builder re-URL-encoded it (`%` → `%25`), so the one attempt that reached the
  server (port 6543) sent a corrupted password. Decided: never round-trip this
  password through URI encoding — pass it raw as a keyword argument.
- `DATABASE_URL` (the URL with correct credentials on the reachable port) was
  rejected before connecting: psycopg/libpq refuses its Prisma-only
  `?pgbouncer=true` query parameter.
- Outbound port 5432 times out from this network; the transaction pooler on
  6543 is the only reachable path. Guest instructions now name 6543 as default.
- Execution still sits with the operator (same `!` command); the permission
  classifier again denied running the production write from the agent side —
  confirmed classifier-level denials don't change across sessions, so skip the
  retry next time.

## Lessons

When a connection secret may contain URI-special characters, never reconstruct
a URL around it — hand it to the driver as a parameter. And when one candidate
fails at parse time and another at auth, diagnose both before rerunning: the
parse failure hid the only correct credential path.
