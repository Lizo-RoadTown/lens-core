---
type: decision
module: lens-core
surfaces: [definition]
date: 2026-10-21T06:35
source_commits: {}
evaluation: surveyor/docs/decomposition/evaluations/2026-10-21-observation-layers.md
modules: [lens-core, lens-ingest, lens-review, lens-serve, lens-observe, workflow oversight, access + tenancy]
---

# Module map baseline: five repos plus two proposed

## What was done
- `decomposition.json` now lists `proposed: ["workflow oversight", "access + tenancy"]` next to
  `modules`. These are descriptive labels until the operator names the repos.
- Added two surfaces: `architecture` (`docs/architecture/**`, decision entry) and `roadmap`
  (`roadmap.yaml`, `ROADMAP.md`, `docs/plans/**`, process entry, so routine status updates
  stay light; firmness changes are operator gates and get their own decision entries).
- This entry is the first baseline for lens-log 0.1.4's module-map check (DESIGN.md D11):
  its `evaluation:` and `modules:` header lines record the map as last evaluated.

## What was found / decided
The map came from Surveyor's evaluations 1 (two modules without a repo) and 3 (observation
layers, which widened agent oversight into workflow oversight). Any later change to
`modules` or `proposed`, including naming the two repos, now needs a Surveyor evaluation and a
decision entry with a new `modules:` list.

## Lessons
Naming the proposed repos will itself trip the check. That is intended: a rename is a
recategorization of the map, and it gets one short evaluation.
