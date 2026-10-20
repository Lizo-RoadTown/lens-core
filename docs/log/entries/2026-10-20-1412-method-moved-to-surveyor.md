---
type: decision
module: lens-core
surfaces: [identity, definition, skills]
date: 2026-10-20T14:12
source_commits: {}
---

# Decomposition method and records moved to Surveyor

## What was done
- Removed from lens-core (now in `Lizo-RoadTown/surveyor`, history kept there and here):
  `skills/decomposition/`, `skills/decomposition-launch/`, `plugins/lens-log/`,
  `docs/decomposition/`.
- `decomposition.json`: dropped the `tooling` surface and `plugins/**/skills/**`.
- `docs/BUILD.md` sections 2 and 4, `docs/README.md` and `README.md` now point to Surveyor.

## What was found / decided
Operator decision, 2026-10-20: the decomposition component is **Surveyor**, its own repo.
lens-core goes back to its charter job: the lab's database standard, the module
composition, and the launcher, plus its own `decomposition.json` piece and its own log.
lens-log is now installed from Surveyor (lizo-skills listing updated, version 0.1.2).

## Lessons
lens-core had been holding a component whose job is wider than lens-core's charter;
the move makes each repo's contents match its identity.
