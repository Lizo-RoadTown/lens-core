---
type: decision
module: lens-core
surfaces: [identity]
date: 2026-10-21T05:53
source_commits: {}
---

# Approved: the Lens is the project observatory; roadmap method

## What was done
- The operator approved `docs/architecture/observatories.md`: the Lens, with all its modules,
  is the project observatory; Tapestry and Loom memory build personal observatories from Lens
  elements; the project observatory sees only what happens at shared project interfaces.
- The operator approved `docs/plans/2026-10-21-roadmap-method-proposal.md`, drawn from four
  read-only agents (tool audit, dependency map, method research, Tapestry's needs).
- Tapestry was updated through loom memory.

## What was found / decided
This changes how lens-core connects: it is the frame of the project observatory, and its
modules must stay neutral about scale so personal observatories can reuse them. lens-core will
hold one roadmap as data (now / next / later; firm / loose / hypothesis; exit checks; evidence),
with automatic checks and operator gates. First tool work: put the four siblings under lens-log,
fix lens-log M6/M7/M8, make the `modules` list the enforced module map, then create the roadmap.

## Lessons
A plan that several agents and a second team will follow needs to be data with checks, not
prose. Prose plans get copied into memory and drift.
