# lens-core — build-out plan (self-directed)

This is lens-core's own plan for working itself out. Work top-down; check items off
and append what you learned. Precedent to consult (not to copy as identity): the
PROVES reference inventory at
`tapestry/docs/decomposition/proves/process-log.md`, and the PROVES spine
`staging_extractions → validation_decisions → core_entities`.

## What lens-core must become

- [ ] **1. Launcher applies the standard.** `lens-core new` connects to
  `LENS_DB_URL` and applies [`schema/spine.sql`](schema/spine.sql) idempotently
  (create-if-not-exists), then reports the tables it ensured. Today `launch.py` is a
  stub that only prints the plan — make it real. Add a `--dry-run` that prints the
  SQL it would run without connecting (testable with no DB).
- [ ] **2. Composition / index.** A manifest (e.g. `lens.modules.json`) listing which
  modules are installed and how they wire onto the standard, so `lens-core` can read
  it and a lab can "call into itself." `lens-core new --modules …` records the choice.
- [ ] **3. Refine the neutral schema with the operator.** The names in
  `schema/spine.sql` are placeholders (candidates/decisions/verified/sources/oversight_*).
  Confirm/rename before first real use; keep it domain-neutral (no subject columns).
- [ ] **4. Tests.** Schema-application idempotency (mocked/temp DB), manifest parsing,
  `--dry-run` output. Mirror the stdlib + pytest style of `tapestry-cli`.
- [ ] **5. Injected-config contract.** Document how a lab supplies its domain
  specifics (candidate kinds, prompts, source registry) as config, not code —
  the PROVES specifics (FRAMES prompt, epistemic checklist, ecosystem enums) become
  a lab's injected configuration.

## What you own vs. don't
Own: the schema standard, the composition/index, the launcher. Do NOT implement
intake/review/serve/observe here — those are the sibling repos; lens-core only
defines the shared shape they meet on.

## Record as you go
Append here: what you built, what you needed, what's missing, what you had to decide.
Also write it to loom-memory scoped to `lens-core`. This log is capture-before-loss.
