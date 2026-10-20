---
type: decision
module: lens-core
surfaces: [source]
date: 2026-10-20T12:21
source_commits:
  PROVES_LIBRARY: 02ab37e
---

# Scope = working parts; every module labeled; a doc agent per module

## What was done
- Operator answered the open "unmounted modules" call and added two requirements.
- Surveyed what A3 needs: `production/Version 3` is the current tracked backend; earlier
  versions exist only in git history; `exports/zenodo_supabase_2026-04-25/` (47 files) can
  confirm which tables the live database had.
- Dispatched two read-only passes: A3 (backend inventory with a status per module,
  version history, where promotion really happens, live-schema check) and a survey of
  Tapestry's docs setup (`C:/Users/Liz/tapestry/apps/docs-site` + doc agents).
- Wrote a loom-memory handoff asking education-lab to make similar plans for itself
  (`handoff-education-lab-make-similar-plans-from-lens-2026-10-20`).

## What was found / decided
Operator decisions (memory `decision-lens-module-scope-labels-and-doc-agents-2026-10-20`):
1. Scope is the WORKING part of everything: drop versions that don't work or were
   replaced by newer ones; KEEP modules that are incomplete or still being built.
   Unmounted alone is not a reason to drop. Status per module: working / in-progress
   (keep) vs superseded / broken old version (drop).
2. Every module is labeled: what it does, where it sits relative to the rest, its usual
   order in a working pipeline.
3. Every module is paired with a documentation agent that starts its docs site (at least
   a skeleton), modeled on Tapestry's setup.

## Lessons
"Unmounted" and "not working" are different axes. The A1 inventory marked reachability;
the module map also needs version status (current vs superseded).
