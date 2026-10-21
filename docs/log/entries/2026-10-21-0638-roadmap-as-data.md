---
type: decision
module: lens-core
surfaces: [roadmap, identity]
date: 2026-10-21T06:38
source_commits: {}
---

# The roadmap as data: roadmap.yaml, checks, generated ROADMAP.md

## What was done
- `roadmap.yaml`: 33 items across phase 0 (hygiene and tooling), B (standard v1), C (modules),
  D (composition and docs), and coordination with Tapestry and Surveyor, from the approved
  method and the four agents' reports.
- `scripts/roadmap.py`: `check` and `render`. `check` enforces:
  - required fields and enum values; unique ids
  - owners must be in the decomposition.json module map or the listed outside owners
  - known dependencies, no cycles, nothing in progress or done before its dependencies are done
  - firm items need an exit_check; loose and hypothesis items need decide_when and cannot be
    built; done needs evidence
  - every module has an item or is parked
  - ROADMAP.md matches the YAML
- `tests/test_roadmap.py`: 15 tests, including the real roadmap. PyYAML added to dev extras
  (runtime stays standard-library-only).
- `docs/BUILD.md` section 7 points to the roadmap. That makes this a decision entry.

## What was found / decided
Sibling items are phrased as outcomes ("work your source and record your own plan"), not
specs, to keep lens-core from writing specs for its siblings. Three items are the operator's
to act on now: rotate the PROVES key, install lens-log 0.1.4 in each repo, name the two
proposed repos. `roadmap-as-data` stays in progress until the check runs in CI
(`roadmap-check-in-ci`).

## Lessons
Putting the "only firm items are built" rule into the checker, not just the prose, is what
stops agents from treating a loose item as a spec.
