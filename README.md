# lens-core

**The Lens — main lab repo.**

The Lens is a neutral, reusable "lab-in-a-box" for **systems discovery**: you launch a
*lab* (a systems observatory) that reads a system's artifacts, stages candidate
findings, has a human verify them, and serves a verified knowledge library.

`lens-core` is the container you start a lab from. It holds:

1. **The standard** — the shared database shape every lab uses
   (`candidates → decisions → verified`, plus lineage and oversight). See
   [`docs/schema/spine.sql`](docs/schema/spine.sql).
2. **The composition** — how the modules snap together into a runnable lab.
3. **The launcher** — `lens-core` stands up a new lab against a database you point it at.

## The modules (each its own repo + PyPI launcher)

| Module | Role |
|---|---|
| **lens-core** (here) | the standard + composition + launcher |
| **lens-ingest** | source material → staged candidate records |
| **lens-review** | human accept/reject/edit → promote to the verified library |
| **lens-serve** | query the verified library (API + MCP) |
| **lens-observe** | signals over activity (active / orphaned / degrading / blind) |

Modules are **mix-and-match**: a lab uses the ones it needs. `lens-observe` is shared
with the platform observation layer (two distinct observatories, one module library).

## Launch (stub)

```bash
pip install lens-core        # once published
lens-core --help
```

Connection is **injected** (`LENS_DB_URL` in your environment) — never hardcoded.
See [`.env.example`](.env.example).

## Identity

This repo has a [`CHARTER.md`](CHARTER.md) — its core directive and its boundary
within The Lens. Read it first. Precedent (how PROVES/Tapestry did it before) is
*guidance*, not this repo's identity.

## Status

Scaffold, 2026-09-26. Neutral/open. No proprietary source data.
