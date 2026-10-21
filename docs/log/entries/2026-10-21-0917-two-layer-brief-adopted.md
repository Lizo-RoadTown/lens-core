---
type: decision
module: lens-core
surfaces: [roadmap]
date: 2026-10-21T09:17
source_commits: {}
---

# Two-layer brief from Tapestry: one signal package, names after reconciliation

## What was done
- Read and committed `docs/handoffs/2026-10-21-two-layer-context-and-tasks.md`, written into
  this repo by the tapestry-34 session. It has no secrets.
- Checked its two roadmap-relevant claims against the source,
  `tapestry/docs/plans/2026-10-21-master-plan-personal-loop.md`:
  - line 109: one signal package, with lens-observe as its program-layer instance;
  - lines 29 and 102: final names only after the full decomposition is reconciled (procedure
    step 8), with stable IDs and provisional names until then; `pr-` records are owned by
    lens-core.
- Roadmap changes:
  - `observe-signal-vocabulary` now names the direction (instantiate pl-001; evaluate it when
    Tapestry proposes it) and stays loose.
  - `name-proposed-repos` moves to later and loose, decided at step 8.
  - New firm item `program-layer-ids`.
  - `access-tenancy-repo` and `workflow-oversight-repo` no longer depend on final names; they
    can start under their descriptive labels and stable IDs.

## What was found / decided
lens-core is the program layer. The personal layer is built in Tapestry and loom memory and
reuses Lens elements through published packages. The management method is Tapestry's
`docs/prototype-reconstruction-procedure.md` v0.1, used by versioned reference and not copied
here. Nothing changes lens-core's own approved roadmap order.

## Lessons
Verify a peer's summary against the source before changing a plan on it. Here both claims
held, and the source added a fact the summary left out: lens-core owns the `pr-` IDs.
