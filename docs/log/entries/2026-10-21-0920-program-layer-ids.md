---
type: decision
module: lens-core
surfaces: [definition, roadmap]
date: 2026-10-21T09:20
source_commits: {}
---

# Program-layer IDs pr-001 to pr-007 assigned

## What was done
- `decomposition.json` now has `ids`:

  | ID | Module |
  |---|---|
  | pr-001 | lens-core |
  | pr-002 | lens-ingest |
  | pr-003 | lens-review |
  | pr-004 | lens-serve |
  | pr-005 | lens-observe |
  | pr-006 | workflow oversight (proposed) |
  | pr-007 | access + tenancy (proposed) |

  It also has an empty `retired_ids`.
- `scripts/roadmap.py` `check_ids()` runs in `check` and CI:
  - every module and proposed repo needs a unique `pr-NNN`;
  - an ID naming a removed module must move to `retired_ids`;
  - retired IDs are never reused.

  Two new tests; the suite has 17 passing.
- Roadmap item `program-layer-ids` is done with evidence.

## What was found / decided
lens-core owns the `pr-` records (tapestry master plan line 29). Tapestry had none reserved; its
manifest's component-017 (program-layer-standard) is already marked lens-core-owned. The IDs
are stable references that cross-layer records can cite before final names exist (procedure
step 8). Adding IDs does not change the module map, so no evaluation was required. Confirmed
with lens-log's `module_map_problem` on this repo.

## Lessons
An ID is only stable if reuse is prevented mechanically. The retired list makes "never reused"
checkable.
