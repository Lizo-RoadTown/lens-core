# skills/

Your own skills, scoped to this project. A skill is a short, reusable procedure
you (or Claude) can invoke by name instead of re-deriving it each time.

## Layout

    skills/
      <skill-name>/
        SKILL.md     # frontmatter (name, description) + the procedure

One directory per skill. Keep each SKILL.md tight and action-oriented.

## Where skills live — three homes, don't confuse them

- **`skills/` (here)** — skills specific to *this* project, authored by hand.
- **`.project-intelligence/local-skills/`** — skill *candidates* the agency
  optimizer emits automatically during use. Raw material, not curated.
- **`tapestry-patterns` plugin** — canonical patterns reused across *all*
  projects, one name / one home. If a skill here proves useful everywhere,
  promote it to the plugin rather than copying it into other repos.

## The skills-audit / upskilling loop

1. **Notice friction** — a workflow you repeat, or a correction made twice.
2. **Capture it** as a skill here, or as a candidate in `.project-intelligence/`.
3. **Audit at session end** — the upskilling report surfaces promotion candidates.
4. **Promote** the winners to the `tapestry-patterns` plugin; retire the ones
   that stopped earning use.

This is how a project gets sharper over time instead of re-deriving the same
procedures every session.
