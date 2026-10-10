# lens-core — directions for building yourself out

This is not a spec. It orients you: how decomposition works, which piece you are,
where the source is, and the constraints that hold. You derive what to build by
working the source.

## 1. You figure out what to build — from the source

This repo was **not** handed a specification of what to build. What this module
actually does, and how, is derived by **deliberately working the original source**.
A repo cannot understand its piece from the outside. No outside agent here walked the
real build — nothing in this file was written with friction against the actual source,
so treat nothing here as authoritative. It is a starting orientation, not a plan to
execute.

## 2. How decomposition works

The Lens uses a **nearly-decomposable architecture**: modules have tight coupling
*internally* and loose coupling *across boundaries*. They meet only on well-defined
interfaces — a shared bus (the schema) — and otherwise stay out of each other's
internals. The full method lives in the `decomposition` skill in the lens-core repo
(`skills/decomposition/SKILL.md`). Read it; don't restate it from memory.

## 3. Your piece + the fragment map

**Your piece:** lens-core holds the shared **schema/standard** (the bus), the
**module composition**, and the **launcher**. You define the shape every module meets
on; you do not perform intake, review, serving, or observation yourself.

**The fragment map** — all the pieces and how they meet on the shared bus:

- **lens-core** — defines the shared schema (the bus) + module composition + launcher.
- **lens-ingest** — writes `candidates` + `sources`.
- **lens-review** — reads `candidates`, writes `decisions` + `verified`.
- **lens-serve** — reads `verified` (API + MCP).
- **lens-observe** — reads activity, writes/serves signals.

Coordinate only through the shared schema. Stay in your piece; don't absorb a sibling's
work.

## 4. The source — go work it

The original source is **PROVES** (read-only) — the system The Lens was decomposed
from. A map of it lives in lens-core `docs/decomposition/proves/process-log.md`.

The parts relevant to your piece, **as places to START looking** (not a spec to copy):

- PROVES `supabase/migrations/` — the spine
  (`staging_extractions → validation_decisions → core_entities`, plus `raw_snapshots`
  and `agent_*`).
- The RPCs `promote_to_verified_knowledge` (migration 009) and `record_human_decision`
  (migration 012).
- This repo's own `docs/decomposition/` and `skills/decomposition/`.

Read the actual source, understand how it really works, and derive what this module
should be. Where any sketch here conflicts with the source or your own investigation,
**the source and your investigation win.** Then write down what you learned.

## 5. Structural constraints that hold regardless

- The database connection is **injected via `LENS_DB_URL`**, never hardcoded.
- Write only to the schema defined here in lens-core.
- Avoid the PROVES anti-patterns: parsing LLM prose as control flow; hardcoded
  `sys.path`; inline DB-URL.

## 6. Record as you go

Progress is recorded as **log entries** in [`docs/log/entries/`](log/entries/), not in
this file. The lens-log plugin enforces it: a turn that touches a surface declared in
[`decomposition.json`](../decomposition.json) cannot end until an entry covers it.

Deciding factor for the entry type: it is a **decision** if it changes what this repo
*is* or how it *connects* (identity, boundary, the shared standard, the decomposition
definition). Everything else (what was done, found, or built) is **progress**, a
`process` entry. This file holds orientation only, so editing it is a decision.
Also write what you needed and what is missing to loom-memory scoped to `lens-core`.
