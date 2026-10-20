---
type: process
module: lens-core
surfaces: []
date: 2026-10-20T13:10
source_commits: {}
---

# A4: module map with charts; first decomposition evaluation

## What was done
- Merged A1 (dashboard), A2 (database) and A3 (backend) into
  `docs/decomposition/proves/module-map.md`: every kept module with what it does, stage,
  order, status, source and Lens repo; three mermaid charts (pipeline, repo placement,
  database areas), each validated as rendering.
- Wrote the first decomposition evaluation:
  `docs/decomposition/evaluations/2026-10-20-two-modules-without-a-repo.md`.
- Saved operator direction to memory (`feedback-lens-new-module-triggers-decomposition-evaluation-2026-10-20`).

## What was found / decided
- Two kept modules have no Lens repo: access + tenancy (missed on 9/26: stale clone, no
  cross-cutting scan) and agent oversight + trust (found on 9/26, dropped when repos were
  drawn by pipeline stage). Proposed: two new repos, operator names them.
- Evaluation verdict: the core tenets held; gaps were a missing "module that governs the
  bus" case and procedural steps (source freshness, status axes, live-system check,
  cross-cutting scan, home check, secret scan) to add to the method.
- "Duplicate models" restated plainly as the same kind of data stored in several database
  tables (relationships x4, aliases x3, review state x4, groups x2, proposals x2).

## Lessons
Drawing repos only from pipeline stages leaves cross-cutting modules homeless; every
kept module must be assigned to exactly one repo before repos are created.
