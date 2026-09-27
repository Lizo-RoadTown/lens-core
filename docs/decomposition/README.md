# `docs/decomposition/`

Working home for the **repo-decomposition** effort: identifying the reusable,
nearly-decomposable modules inside a repo so they can be split into standalone,
composable pieces.

Two things live here, and they grow together **as we go** (capture-before-loss —
the process is documented while it happens, not reconstructed afterward):

1. **The process log** for each decomposition run (e.g. `proves/process-log.md`)
   — what was read, what modules were found, with `file:line` provenance.
2. **The method** distilled from those runs — which becomes a reusable
   **decomposition plugin** (a suite of skills) so the process is repeatable and
   doesn't have to be re-derived.

The first run is PROVES (`proves/`). The repos being decomposed are **read-only
source** — this effort reads them to *produce* the decomposition elsewhere; it
never modifies them.

Terminology: neutral **NDA** (nearly decomposable architecture) working terms —
module, coupling, interface, sustaining mechanism. No coined or proprietary
names; the operator names the pieces.
