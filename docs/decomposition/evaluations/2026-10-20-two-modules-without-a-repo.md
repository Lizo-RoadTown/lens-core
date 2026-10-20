# Decomposition evaluation — two modules with no Lens repo (2026-10-20)

**Trigger:** the A4 module map ([`../proves/module-map.md`](../proves/module-map.md)) found two
kept modules that fit none of the five Lens repos:

1. **Access + tenancy**: organizations, members, roles, active org, sign-in, row security
   (dashboard R1 + `contexts/AuthContext.tsx`; database area G).
2. **Agent oversight + trust**: agent capabilities, proposals, trust scores and the
   triggers that auto-approve and adjust trust (dashboard R6; database area F, migration 017).

Operator rule (2026-10-20): any new module, further split, or recategorization triggers a
full evaluation of the decomposition method, reported every time, with the method adjusted
so the case is scanned for at the start. This is the first such report, written by hand;
automating the trigger is proposed separately.

**Method evaluated:** [`skills/decomposition/SKILL.md`](../../../skills/decomposition/SKILL.md),
steps 1–7, as run on 2026-09-26 (recorded in [`../proves/process-log.md`](../proves/process-log.md)).

## 1. Were the core tenets right?

| Tenet | Verdict | Evidence |
|---|---|---|
| Modules are found by bond strength: tight inside, loose across | **Right** | Both modules are tightly bound inside (oversight: three tables + three triggers that only touch each other, `017`; tenancy: org tables + org RPCs + auth context) and loosely bound outward (oversight links to candidates only by soft id arrays, no foreign keys; tenancy reaches other tables only through org columns). |
| A module's interface is what it touches | **Right** | Listing what each touches is exactly what exposed them as separate: neither touches the candidate → decision → library flow except through one column or soft link. |
| The database is the bus every module meets on | **Right, but incomplete** | Both meet the others on the bus. But tenancy is not just a participant: it **constrains every other table** (org columns, row-level security). The tenet treats the bus as neutral ground and has no slot for a module that governs access to the bus itself. |
| Pieces are named by the operator; placeholders until then | **Right** | Followed. These two are unnamed. |
| Launch gives orientation, substance comes from the source | **Right** | The five repos were launched with orientation only, which is why they can absorb this correction cheaply. |

**Overall: the core tenets held.** No tenet produced a wrong module. The gap is one
missing case in the bus tenet (a module that governs the bus) and a procedural gap
(below).

## 2. Was the original decomposition correct, and is this just more granular?

- **Agent oversight + trust:** the 9/26 pass **found it** (synthesis item 11, "agent
  oversight / health — real, cohesive"). It was correct and not too coarse. What went wrong
  was later: when the five repos were created by **pipeline stage**
  (ingest / review / serve / observe), this cross-cutting module had no stage and was
  **left without a home**. Not more granular; **dropped at repo creation**.
- **Access + tenancy:** the 9/26 pass **missed it entirely**. The dashboard's
  organization module landed in the 50 commits the stale clone did not have, and the
  backend's org columns were read as fields, not as a module. Not more granular;
  **missed because of a stale source** plus no scan for cross-cutting concerns.

## 3. Was a recategorization decision made? Did it create a new interface?

- **Yes, for agent oversight.** It moves from "a dashboard screen" (9/26) to
  **a governance module**: it decides what agents may do on their own (auto-approve when
  trust ≥ threshold, `017:359`). That creates a **new interface between oversight and
  ingest**: agents in the extraction pipeline must ask oversight what they are allowed to
  do. In PROVES that link is only implied (no code calls it); in The Lens it must be an
  explicit, declared interface.
- **Yes, for access + tenancy.** It moves from "columns on every table" to **a module that
  owns a cross-cutting interface**: every other module's tables carry an org column it
  defines, and row security it owns decides who sees what. That is a **new interface on
  the bus itself** (an org-scoping contract every module must follow), which the current
  draft `spine.sql` does not have at all.

## 4. Why the method missed or mishandled them (root causes)

1. **Stale source, not checked.** Step 2 (inventory) had no "is the source current?"
   check; the dashboard clone was 50 commits behind.
2. **Repos were drawn from pipeline stages only.** Steps 5–6 named and laid out repos by
   stage in the flow; anything cross-cutting (governance, access, config) had no stage
   and so no repo.
3. **No scan for cross-cutting concerns.** Nothing in steps 2–4 asks "what concerns cut
   across every stage?" (access/tenancy, oversight/governance, configuration,
   observability).
4. **Reachability and version status not recorded.** The 9/26 inventory did not mark
   mounted vs unmounted or current vs superseded, so "real vs mock" was the only axis.
5. **Schema folder trusted over the live system.** Step 3 used the migrations; they
   diverge from the live database (A2, A3), which hides which tables a module really uses.

## 5. Method adjustments (to add to the decomposition skill)

New categories of action to scan for **during the initial pass**:

- **Step 2, source freshness:** record the commit of every source read and compare it to
  the remote before inventorying; a stale source invalidates the pass.
- **Step 2, two status axes per candidate module:** reachability (mounted / unmounted /
  imported by nothing) and version status (working / in-progress / superseded / broken).
  Apply the scope rule (keep working + in-progress).
- **Step 3, verify against the running system:** check the schema folder against what the
  code calls and, where available, a live-schema export.
- **Step 4, cross-cutting scan:** explicitly look for concerns that touch every stage
  (access/tenancy, governance/oversight, configuration, observability, secrets) and
  classify each as a module, part of the standard, or a constraint on the bus.
- **Step 5–6, home check:** before creating repos, every kept module must be assigned
  to exactly one repo; any module without one is a new-repo candidate and triggers this
  evaluation.
- **Step 4, governing-the-bus case:** a module that constrains the bus (row security,
  scoping columns) adds a contract to the standard, not just tables.
- Also (from A3): **scan for committed secrets** during the first full read.

## 6. Proposed actions (operator decides)

- Two new Lens repos, set up like the other five (charter, CLAUDE.md, BUILD.md
  orientation, `decomposition.json` piece, lens-log, docs-site skeleton + doc agent),
  names to be chosen by the operator.
- Add the org-scoping contract to lens-core's standard (Phase B).
- Apply section 5 to `skills/decomposition/SKILL.md`.
- Automate this evaluation (see the proposal in the session; lens-log is the likely home).
