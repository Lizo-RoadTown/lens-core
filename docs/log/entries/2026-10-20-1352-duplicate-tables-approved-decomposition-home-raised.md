---
type: decision
module: lens-core
surfaces: []
date: 2026-10-20T13:52
source_commits: {}
---

# One table per kind of data approved; decomposition component's home raised

## What was done
Operator answered the A4 questions; checked GitHub and local folders for a repo holding
the decomposition component (none: only lens-core, lens-ingest/review/serve/observe,
tapestry, the-loom and others) and recalled the five-layer and system-architecture
memories.

## What was found / decided
- Approved: the standard keeps one table per kind of data, as used by the working code
  (`docs/decomposition/proves/module-map.md` section 5). Applies in Phase B.
- Approved: design an automatic decomposition-evaluation trigger.
- Open: names for the two proposed repos (access + tenancy; agent oversight + trust).
- Raised by the operator: the decomposition component (one of five layers, each with its
  own core teachings) should probably have its own repo. Finding: it has none; the method,
  decomposition-launch skill, lens-log, evaluations and PROVES run records all sit in
  lens-core, whose charter is narrower (the lab's standard, composition, launcher).
  This is an identity/boundary question for lens-core, so it is logged as a decision
  pending the operator's choice.

## Lessons
The 9/26 move of the method into lens-core answered "not Tapestry" but not "which repo";
a component that operates across many repos needs a home of its own.
