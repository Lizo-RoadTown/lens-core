---
type: skill
module: lens-core
surfaces: [skills, tooling]
date: 2026-10-10T12:43
source_commits: {}
---

# log-entry skill carries the deciding factor; lens-log 0.1.1

## What was done
- `plugins/lens-log/skills/log-entry/SKILL.md`: added the deciding factor (decision vs
  progress) and listed tooling under `process` entries.
- `plugins/lens-log/.claude-plugin/plugin.json`: version 0.1.0 → 0.1.1 so installed copies
  pick up the skill change (the plugin cache is keyed by version). The `lizo-skills`
  marketplace entry needs the same version.
- `plugins/lens-log/tests/test_real_definition.py`: pins `plugins/**` → `tooling`,
  `docs/BUILD.md` → `identity`. Watched it fail on `{'module','skills'}`, then pass;
  suite 74/74.

## What was found / decided
The skill is where an agent looks when the Stop hook asks for an entry, so the deciding
factor belongs there as well as in BUILD.md §6 and DESIGN D9.

## Lessons
A skill text change inside a plugin does not reach installed machines unless the plugin
version is bumped in both plugin.json and the marketplace entry.
