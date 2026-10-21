---
type: process
module: lens-core
surfaces: [source]
date: 2026-10-21T09:32
source_commits:
  PROVES_LIBRARY: 02ab37e
---

# Guest and agent handoff documentation for proves_viewer written

## What was done

- Queried the PROVES database (read-only MCP) for the column lists of the ten
  load-bearing spine tables so the handoff docs describe the real schema.
- Wrote two local handoff documents next to the credentials file (deliberately
  **not** in this repo — they embed the guest login, and lens-core commits no
  keys):
  - `C:\Users\Liz\proves_viewer_GUEST_GUIDE.md` — human-facing: connection
    fields, GUI client and psql instructions, a spine orientation table,
    starter queries, limits, troubleshooting.
  - `C:\Users\Liz\proves_viewer_AGENT_HANDOFF.md` — agent-facing: connection
    string, transaction-pooler caveats (no session state, no prepared
    statements), the five server-enforced constraints, a schema map with key
    columns and join paths, introspection queries, query etiquette, and an
    instruction to treat query results as data rather than instructions.

## What was found / decided

- The guest login is a database login, not a browser login; the operator asked
  for documentation for both a person and an AI agent. A browser-viewable
  guest surface remains lens-serve territory, noted as a possible
  coordination item, not built here.
- Documented port 6543 as the default (5432 blocked on some networks) and the
  candidates → decisions → verified framing as the orientation for guests:
  `staging_extractions` → `validation_decisions` → `core_entities`.

## Lessons

Handoff documents that embed secrets live beside the secret, outside the repo;
the repo records that they exist and what they contain, never their contents
verbatim. An agent-facing doc should state server-enforced limits as hard
facts (so the agent does not retry) and include join paths, which saves the
agent its own schema discovery.
