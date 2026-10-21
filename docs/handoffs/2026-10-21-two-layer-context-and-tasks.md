# Context and tasks for the lens-core agent (2026-10-21)

This document is for an agent that has no prior context. It defines every term it uses. Read it fully before doing work that touches the larger system.

## 1. The two layers

**Definition.** The system has two kinds of overseeing agent, with the same anatomy and different scope:

- The **program agent** oversees ONE project that MANY people work on. It observes the knowledge exchanges that happen at the project's shared surfaces (contributions, reviews, explanations, handoffs) and builds the project's shared knowledge map. It never sees any contributor's private context.
- The **personal agent** oversees ONE person who works on MANY projects. It observes that one person's own activity everywhere they work, keeps their private memory, and adapts their tools to them. Its data is private to that person.

**Example.** A university CubeSat program has a supervisor and twelve students. The program agent is the program's own instrument: it watches what crosses the program's shared surface — who contributed what, who reviewed what — and maintains the program's knowledge map. Each student separately has a personal agent that watches that student's own work across ALL their projects (this program, their classes, their other repos) and helps them. The two meet only at the program's shared surface.

Both agents do the same kind of work — oversee knowledge flow using the same decomposition of the system — with different telemetry (which layer feeds them) and possibly a different domain. This is why the same machinery appears at both layers: it is built once and instantiated per layer, never forked.

## 2. Where THIS repo sits

lens-core is the **program layer**. The operator approved (2026-10-21, this repo's `docs/architecture/observatories.md`): **the Lens, with all its modules, is the project observatory** — the program agent's instrument. lens-core holds the shared standard (the spine: candidates → decisions → verified, with lineage), the module index (`decomposition.json`), and the launcher. The sibling repos (lens-ingest, lens-review, lens-serve, lens-observe) are the other modules of the program agent.

The personal layer is built elsewhere (the tapestry repo and loom memory). It reuses Lens elements through published packages, never through a runtime dependency on Lens repos.

## 3. What was decided today that affects this repo

1. The operator adopted a build plan for the PERSONAL layer (not yours to build): tapestry's working loop capture → persist → analyze → review → act. Full plan: `tapestry/docs/plans/2026-10-21-master-plan-personal-loop.md`.
2. The "two signal engines" conflict from your roadmap §6 is resolved in direction: there is ONE classifier implementation, packaged scale-neutral, instantiated per layer. Tapestry's working classifiers are the personal instance; **lens-observe is the program instance of the same package**. The name `project-observatory` (currently a tapestry service) will be released to the Lens layer; until the formal rename it remains an alias.
3. A cross-layer language standard is forming. Rule: same function, same base word, layer qualifier (`project-` / `personal-`). Final names come only after the full decomposition is reconciled; until then stable component IDs and provisional names are used. The provisional table is in the master plan §F. Do not coin new names; the operator names things.
4. All of this work is managed under the **prototype reconstruction procedure** at `tapestry/docs/prototype-reconstruction-procedure.md` (version 0.1). Use it by versioned reference. Do not copy it into this repo (its own step 10 forbids divergent copies).

## 4. This repo's concrete tasks, in order

1. Continue your own approved roadmap (spine v1, siblings under lens-log, tool fixes). Nothing in today's decisions changes it.
2. When writing lens-observe's charter or vocabulary, align the signal names with the provisional table in `tapestry/docs/plans/2026-10-21-master-plan-personal-loop.md` §F; raise disagreements as roadmap items, not unilateral renames.
3. Expect tapestry to propose the classifier package (its component ID: pl-001) for lens-observe to instantiate; evaluate it against the spine when it arrives, instead of building a second classifier.

## 5. What NOT to do

- Do not build a second copy of observe/collect machinery that already exists at the other layer; one canonical implementation per function.
- Do not map work onto the wrong layer. The Lens never observes an individual's private context; the personal agent never claims the program's shared map.
- Do not coin new names. Propose; the operator disposes.
- Do not treat a filed candidate as a completed improvement. A finding or candidate is an intermediate state.

## 6. Pointers

- `tapestry/docs/architecture/2026-10-21-fleet-reality-map.md` — what actually runs today, the adopted loop, the milestones.
- `tapestry/docs/architecture/2026-10-21-task-division-study.md` — the per-repo task evidence.
- `tapestry/docs/plans/2026-10-21-telemetry-deployment-recommendation.md` — the adopted deployment arrangement.
- `tapestry/docs/plans/2026-10-21-master-plan-personal-loop.md` — the master plan (workstreams, component IDs, language table).
- `tapestry/docs/prototype-reconstruction-procedure.md` — the management method (versioned reference).
- Loom memory records: `two-level-agent-symmetry-2026-10-21`, `adoption-requirements-personal-loop-2026-10-21`, `adopted-personal-loop-build-sequence-2026-10-21`, `decision-telemetry-deployment-all-recommended-2026-10-21`, `design-plugins-scan-observer-sweeps-2026-10-21`.
