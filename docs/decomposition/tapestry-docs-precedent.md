# Precedent: how Tapestry does documentation (for the Lens doc agents)

**Surveyed:** 2026-10-20, read-only, `C:\Users\Liz\tapestry` (spot-checked).
**Status:** precedent, not identity. It informs the plan to pair every Lens module with a
documentation agent that starts its docs site (operator decision 2026-10-20).

## Finding: there is no documentation agent to copy

Tapestry's agents are `tapestry-discipline/agents/architecture-analyst.md` and nine
`tapestry-patterns/agents/*` (drift-watcher, roadmap-maintenance, ...); none writes docs.
The legacy `C:\Users\Liz\docs-agent` repo has empty `agents/` and `skills/`. Docs are
written by the main session agent using the **`documentation` skill**
(`tapestry-patterns/skills/documentation/SKILL.md`: Diátaxis, ADRs, docs-as-code, with
`references/`, `scripts/audit_docs.py`, ADR/README templates). The docs site was
scaffolded by hand. So the Lens doc agent is **new**, built from three existing parts:

1. **The site template:** `tapestry/apps/docs-site` (Astro 5 + Starlight 0.36).
2. **The writing discipline:** the `documentation` skill.
3. **The trigger pattern:** architecture-analyst = an agent `.md` (frontmatter `name`,
   `description`, `model`, `tools`) + a slash command that runs deterministic scripts and
   then invokes it + a SessionStart hook nudge scoped by `LOOM_PROJECT_ID`.

## The docs-site template (`tapestry/apps/docs-site`)

- `astro.config.mjs`: `site` (`:12`), `starlight({...})` with an explicit sidebar grouped by
  reader intent (Learn / Docs / Reference ...); `adapter: vercel()` only because Tapestry has
  on-demand routes; a pure docs site can be static.
- `src/content.config.ts`: 7-line `docsLoader()` / `docsSchema()` collection.
- `src/content/docs/`: Diátaxis folders `start/`, `how-to/`, `explanation/`, `reference/`,
  plus `systems/` ("Option D": one page per component with What it is / Why it exists /
  How it interacts / Setup / Verify / Troubleshoot) and a splash `docs.mdx`.
- Every page needs frontmatter `title` + `description` (used by the `llms.txt` generator
  and the docs MCP).
- `scripts/generate-static-docs.mjs` runs before dev/build and writes `public/llms.txt`
  and `public/raw/<slug>.md`.
- Deploy: Vercel, Root Directory = the docs folder, auto-deploy on push. No CI docs build.
- Docs MCP (`tapestry/services/docs-mcp`, `docs_mcp`): reads any Starlight content tree via
  `DOCS_ROOT`, so a module's docs could be searchable by agents with no new code.

## Minimum skeleton per module repo

`docs-site/package.json` (astro, @astrojs/starlight, sharp; dev/build/preview) ·
`astro.config.mjs` (static) · `src/content.config.ts` · `tsconfig.json` · `.gitignore` ·
`vercel.json` · `src/content/docs/index.mdx` (splash) · one page each in `start/`,
`how-to/`, `explanation/`, `reference/`, `systems/` · `README.md` (purpose, commands,
deploy, when to update). Optional: the `llms.txt` generator, a docs-MCP entry.

## Open design questions (for the operator, at A4)

- Where the doc agent lives: a Lens plugin (alongside lens-log) or tapestry-patterns
  (Tapestry ADR 0004 says reusable agents belong in tapestry-patterns).
- Trigger: on demand (`/docs-update`), a session-start nudge, and/or a lens-log-style
  check when `src/` changes without a matching docs change.
- One docs site per module repo, or one Lens site with a section per module.
