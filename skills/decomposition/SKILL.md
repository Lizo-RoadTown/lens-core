---
name: decomposition
description: The Lens's core method for systems discovery — decompose a system/repo into its nearly-decomposable, reusable modules. Use when taking a target system and finding (or defining) its true modular architecture so each piece can stand alone. Inventory → map interfaces → find bond-strength seams → extract standalone modules. Worked example: docs/decomposition/proves/process-log.md.
---

# Decomposition (systems discovery)

The method The Lens applies to a system to discover its modular structure and turn
it into standalone, reusable pieces. Grounded in **nearly decomposable architecture**
(Simon 1962): bond strengths differ by orders of magnitude, so a module shows tighter
INTERNAL bonds and looser relations ACROSS its boundary.

**Neutral terms only** (no coined or proprietary names): *module* (a nearly-
decomposable unit), *coupling* (relations between parts — stronger inside), *interface*
(where parts connect), *sustaining mechanism* (what keeps an interface usable). The
operator names the pieces; do not coin names.

**The target system is READ-ONLY source.** Read it to *produce* the decomposition
elsewhere; never modify it.

## The steps

1. **Orient to the whole.** State what the system is and the end goal, so no agent
   mistakes its slice for the whole. Write it down first.
2. **Read-only inventory.** Per repo/area, enumerate candidate modules.
3. **Interface mapping.** For each module, the interface it depends on — exactly what
   it touches (DB tables / RPCs / MCP calls / imports / APIs). A module's real
   interface is *what it touches*, nothing more.
4. **Bond-strength seams.** Cluster tight-internal / loose-across. Where coupling is
   tangled and no clean seam exists, **define** the interface (name the interface +
   the flow across it) so the piece can stand alone.
5. **Name (operator-led).** Placeholder neutral labels until the operator names them.
6. **Repo-tree logic.** Each module becomes a drop-in unit = its code + a manifest of
   what it reads/writes on the shared bus + an *injected* connection (no hardcoded
   backend). A self-locating index lets the tree "call into itself."
7. **Extract.** Lift each module into its own standalone piece; document what it
   needed and what's missing as you go (capture before loss).

## Launching the repos (project launch)

When you create the repos for the decomposed pieces, launch each one per the
**`decomposition-launch`** skill. At launch a repo gets ONLY: (1) how decomposition
works, (2) what its piece is, (3) how it coordinates with the siblings on the shared
bus, and (4) where the source is + the directive to derive its build by working the
source itself, plus (5) the structural constraints that hold regardless. **Never hand a
repo a substantive "what it must become" directive written by an agent that has not
worked the source** — a repo cannot understand its piece from the outside; that
understanding forms only by deliberately working the source. On substance, the source +
the repo's own investigation win over any sketch.

## Identity discipline (why decompositions go wrong)

Fragmented module-agents lose the whole, forget their role, and treat their task as
the entire project — especially without durable memory. Counter it: every module
carries its own **charter** (who it is, its core directive, "you are NOT the whole",
its boundary, its neighbors). It consults precedent (how it was done before) as
**guidance, never identity.** Keep three things separate in memory: *identity/charter*,
*self/process*, and *reference/precedent*.

## Reuse discipline

A module is only reusable if its connection is **injected** (env), not hardcoded, and
if its interface is *only* what it touches on the shared bus. Watch for reuse blockers:
hardcoded backends/keys, hardcoded paths, fragile text-format coupling, duplicated
orchestration or data-access strategies.

## Worked example

`docs/decomposition/proves/process-log.md` — the full run that decomposed the PROVES
reference system and produced The Lens (module inventory, the shared interface bus,
reuse blockers, the neutral module set). Read it as the concrete application of the
steps above.
