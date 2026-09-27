---
name: decomposition-launch
description: How to LAUNCH the repos produced by a decomposition so each can build itself out correctly. Use when spinning out / setting up the module repos of a decomposed system. Each repo is given directions on how decomposition works, what its piece is, how to coordinate with its siblings, and where the source is — then directed to derive its build FROM THE SOURCE ITSELF. It is never handed a substantive build spec written by an outside agent that has not worked the source.
---

# Decomposition — project launch

When you create the repos for a decomposed system, each one must be able to build
**itself** out correctly from day one. This skill governs what each repo is given at
launch.

## Core principle
**A repo cannot understand its piece from the outside.** That understanding forms only
by **deliberately working the original source**. So launch gives each repo *orientation*
and points it AT the source — it does not hand it a substantive build directive. An
outside agent (a scaffolder, an assistant) has had **zero friction with the reality of
the actual build**; its understanding is shallow and must never be treated as the spec.

## What each repo gets at launch — and only this

1. **How decomposition works** — the method (nearly-decomposable architecture: modules
   have tight *internal* and loose *cross-boundary* coupling; they meet only on
   well-defined interfaces / a shared bus). Reference the `decomposition` skill; don't
   restate it in full.
2. **What its piece is, in the overall scope** — its identity + boundary: which module
   it is, what it owns, what it does NOT own. This is a structural output of the
   decomposition and it HOLDS — it stops the repo drifting into thinking its task is the
   whole.
3. **How it works together with the other pieces** — the fragment map (all the pieces)
   and the shared interface/bus they coordinate through, so it builds WITH them, not in
   isolation.
4. **Where the source is + the directive to work it** — the original source
   (read-only), a map of it, and the parts relevant to this piece as a place to START
   looking. Explicit instruction: *derive what this module actually does, and how, by
   working the source; where any sketch and the source conflict, the source + your own
   investigation win; record what you learn.*
5. **Structural constraints that hold regardless** — e.g. injected connection (never
   hardcoded), write only to the shared schema, named anti-patterns to avoid.

## What launch must NOT include
- A prescriptive "what this module must become" step list authored by an agent that
  has not worked the source. That is an outside directive — do not write it.
- Any framing that makes a scaffolder's/assistant's understanding authoritative
  ("when in doubt, this plan wins"). It is a pointer at most; on substance the source
  wins.

## The artifacts per repo
- **`CHARTER.md`** — identity + boundary + interface (items 2 + 3). Legitimate to
  author: it's the decomposition's structural decision. It fixes WHO the repo is; it
  does NOT fix the substance of what it builds.
- **`CLAUDE.md`** — auto-loaded; carries the "figure it out from the source" directive
  (item 4) up front, plus how-to-work conventions.
- **`docs/BUILD.md`** (or equivalent) — **not a spec.** It gives items 1, 3, 4, 5:
  how decomposition works, the fragment map + your piece, where the source is + go work
  it, and the structural constraints. The repo writes its actual plan AS IT WORKS THE
  SOURCE, and records what it learns.
- Platform wiring so the repo is a real, observable project (memory, plugins,
  telemetry) — see the platform onboarding.

## Why this exists (the lesson it encodes)
From a real miss: a scaffolding agent handed the decomposed repos its own one-line
"core directive" + a "what it must become" checklist, and wrote "when in doubt, this
charter wins." That elevates a friction-free, shallow read above the real source, and a
repo built on it would drift badly. Launch gives orientation + the source; each repo
earns its understanding by working it.
