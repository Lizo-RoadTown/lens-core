---
type: process
module: lens-core
surfaces: [source]
date: 2026-10-21T06:01
source_commits:
  PROVES_LIBRARY: 02ab37e
---

# Supabase MCP added locally, read-only, for the PROVES project

## What was done
- The operator pasted Supabase's MCP setup for project ref `guigtpwxlqwueylbbcpx`.
- Searched the PROVES env files for the ref only, by file name (`grep -l`); no contents were
  printed. Found in `PROVES_LIBRARY/.env`, so the ref is the PROVES database.
- Added the server with `--scope local` and `read_only=true` instead of `--scope project`.
  It lives in the operator's `~/.claude.json` under `C:/Users/Liz/lens-core`. lens-core's
  committed `.mcp.json` is unchanged.
- Skipped `npx skills add supabase/agent-skills`; a Supabase skill is already available.

## What was found / decided
- Project scope would have committed the PROVES backend into public lens-core, breaking the
  bus rule (no hardcoded backend).
- The suggested feature set includes writes, and PROVES is read-only source.
- The operator still has to authenticate in a regular terminal (`claude /mcp`).
- The lens-log plugin cache in use here is 0.1.1, while 0.1.2 is published. Check the install.

## Lessons
Check what a pasted setup command points at before running it. A project-scoped config in a
public, backend-neutral repo is a commitment, not a convenience.
