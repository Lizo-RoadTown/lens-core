# Proposal: how to run the observatory roadmap (2026-10-21)

**Status:** approved by the operator (2026-10-21). Next step: build the roadmap from it.
**From:** four read-only agents (tool audit, dependency map, method research, Tapestry's
needs), combined by the lens-core session.

## 1. The method

- **One roadmap, kept as data, owned by lens-core.**
  - `roadmap.yaml` is the source of truth; `ROADMAP.md` is generated from it.
  - It is organised by horizon (now / next / later), not by dates.
  - Only "now" items carry detailed exit checks.
- **Every item is marked `firm`, `loose` or `hypothesis`.**
  - Only firm items may be built.
  - A loose item names the fact that would let it be decided. Decide at the last moment that
    still keeps the options open, not earlier.
- **Decisions stay in the log.** The roadmap links to log entries and never copies them.
  Memory and BUILD.md point to roadmap item ids; they don't restate them.
- **Automatic checks plus a few operator gates** (section 3).
- **Each "now" item gets a time budget.** If it runs over, it comes to the operator to
  continue, reshape or drop; it is not extended automatically.

Sources for the method: rolling-wave planning; Now/Next/Later; last responsible moment;
architecture fitness functions; consumer-driven contracts and expand/contract migrations for
the shared schema; ADRs; Shape Up appetites. Citations are in the research agent's report.

## 2. Fields for each roadmap item

| Field | What it holds |
|---|---|
| `id`, `title` | identifier and short name |
| `outcome` | one sentence on the result, not the feature |
| `horizon` | now / next / later |
| `firmness` | firm / loose / hypothesis |
| `status` | proposed / in-progress / blocked / done / dropped / superseded |
| `owner_repo` | must be a module in `decomposition.json` |
| `approver` | the operator, for gated items |
| `depends_on` | item ids |
| `touches_bus` | tables or columns read or written, or none |
| `exit_check` | a runnable command or test, or `human:` plus the named criterion |
| `evidence` | commit, test run or log entry; required for done |
| `decision_ref` | the log entry that created or changed the item |
| `revisit_trigger` | the condition that reopens the item |
| `assumptions` | PROVES facts relied on, each with file:line |
| `consumers` | other modules or Tapestry, for anything shared |
| `last_verified` | date the item was last checked |

## 3. Checks

**Automatic** (lens-log, a GitHub Action, drift-watcher):
- The file is valid and the dependency graph has no cycles.
- Nothing is in progress while something it depends on isn't done.
- Every done item has evidence that resolves, and every firm item has a runnable exit check.
- Every `owner_repo` is in the `decomposition.json` module list, and every module has at least
  one item or is marked parked.
- Each repo's declared table reads and writes match `spine.sql`.
- A destructive migration fails unless an earlier expand step exists.
- An item is flagged when its cited PROVES file:line changes, or when it goes stale.

**Operator gates:**
- Moving an item from loose to firm, or from later to now.
- Any change to `spine.sql` or `decomposition.json`. These already require a decision entry.
- Accepting a new consumer (Tapestry) of a shared table.
- An item that has run over its time budget.

**Triggers that force a replan:**
- A new module, split or recategorization (this already triggers an evaluation).
- A failed contract or fitness check.
- A PROVES assumption proven wrong.
- A `revisit_trigger` firing.
- Tapestry asking to depend on a loose item.
- Two repos claiming the same table.

**Review cadence:** the tapestry `periodic-architectural-checkin` triggers (a new repo; a
run of merged PRs), pointed at `observatories.md` and the roadmap.

## 4. Tool changes

**Now (small):**
1. Put the four sibling repos under lens-log: add a `decomposition.json` and enable the
   plugin in each. Add a `docs/architecture/**` and roadmap decision surface in lens-core.
   Today most roadmap work in the siblings would leave no record.
2. Fix lens-log defects that silently drop records:
   - M6: a `## Lessons learned` heading is not accepted (`entries.py:12`).
   - M7: one malformed state line turns enforcement off for the whole session
     (`state.py:72`, swallowed at `stop_check.py:106`).
   - M8: surfaces written without brackets are read as one name.
   Tests currently pass (74).
3. Make the `modules` list in `lens-core/decomposition.json:12` the machine-readable module
   map. Nothing reads it today. Add the two proposed repos, and require a decision entry plus
   a Surveyor evaluation file whenever it changes. This is the automatic evaluation trigger,
   built on data that already exists.
4. Create `roadmap.yaml` and the generated `ROADMAP.md` in lens-core. Use the method's gateable
   checks as gate rows: source freshness, secrets scan, proprietary check, cross-cutting scan,
   observation layers, home check, injected connection. The launch skill's "platform wiring"
   should name `decomposition.json` and lens-log.

**Along the way:**
- The log-index GitHub Action. It is the only backstop for shell edits and for cross-repo
  checks. Build it before more than two repos are logging.
- The remaining lens-log defects:
  - M1: the hardcoded `python` command.
  - M3: state is keyed by session only, so a touch can be counted in the wrong repo.
  - M4: relative paths resolve against the repo root, not the working directory.
  - M5: miss filenames can collide.
- Point `roadmap-maintenance` at the roadmap.
- Give drift-watcher the Lens rules in place of Tapestry's manifesto.

**Later:** the docs agent and docs-site skeletons. They don't gate the roadmap.

## 5. Roadmap skeleton (phases)

| Phase | Items | Firmness | Exit check |
|---|---|---|---|
| **0 · Hygiene** | Rotate the leaked PROVES key (operator) | firm | key no longer authenticates |
| | Approve `observatories.md` | firm | committed |
| | Siblings under lens-log | firm | `decomposition.json` in all Lens repos |
| | Tool fixes from section 4 "Now" | firm | tests pass |
| **B · Standard v1** (lens-core) | Neutral table names; the five one-table choices | firm | lens-core applies `spine.sql` to an empty database idempotently |
| | Review and promotion contract that fixes the PROVES defects | firm | a test runs source → candidate → decision → verified |
| | No anonymous grants; trigger bug removed | firm | |
| | Org/scope column, neutral about scale (project or person) | loose | |
| | Whether the oversight tables stay in the spine or move to the oversight repo | loose | |
| **C · Modules** | Siblings work their source (can start now, in parallel) | firm | each repo has its own derived plan in its log; stub replaced; smoke test on a shared test database |
| | Access + tenancy and workflow oversight repos (wait for names) | firm / loose | |
| | lens-observe signals (unmounted in PROVES) | loose | |
| **D · Composition** | Launcher that stands up all modules | firm | one command stands up a lab |
| | Index Action | loose | |
| | Docs sites | firm | |
| | Org isolation | | a second org cannot see the first org's rows |
| **E · Personal reuse** | Owned by Tapestry / Loom memory | loose; outside this roadmap | |

**Hard dependencies:**
- The scope-column contract blocks spine v1.
- Spine v1 blocks the siblings' database code, but not their source work.
- Repo names block creating the two new repos.
- The access + tenancy implementation blocks any shared deployment.

## 6. Coordination with Tapestry

These go in the roadmap as open items with Tapestry as a consumer:
1. **"Lens" means two different things.** Tapestry's unconfirmed proposal says "Lens = the
   interface" (`tapestry/docs/proposals/2026-10-20-loom-mcp-module.md:11-13`) and plans to
   move its dashboard and docs site "toward Lens". The operator's 2026-10-21 decision says the
   Lens is the project observatory.
2. **Two signal engines.** Tapestry `services/project-observatory` computes hot_path /
   orphaned / degrading / blind; lens-observe's charter plans active / orphaned / degrading /
   blind. Decide which is canonical and settle one vocabulary.
3. **Two candidate → decision flows:** Tapestry's architecture-registry and the Lens spine.
4. **Up to three homes for tenancy:** access + tenancy, Loom_MCP, project-registry.
5. **How reuse happens.** A 2026-10-10 memory says Tapestry uses published Lens packages, never
   a runtime dependency. The roadmap should adopt that.

## 7. Risks to watch

- lens-core writing specs for siblings. Spine v1 defines tables and constraints only.
- The oversight tables sitting in lens-core's spine, which absorbs a sibling's territory.
- PROVES table names carried into the standard.
- Tenancy put off because the repo has no name. The scope column goes into the spine now.
- Agents treating loose items as specs, or marking items done without evidence.
