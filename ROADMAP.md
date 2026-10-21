# Roadmap

<!-- generated from roadmap.yaml by scripts/roadmap.py; edit roadmap.yaml, not this file -->

One roadmap for the Lens. Only **firm** items are built; **loose** and **hypothesis** items
name the fact that decides them. Method: [docs/plans/2026-10-21-roadmap-method-proposal.md](docs/plans/2026-10-21-roadmap-method-proposal.md).

## Now

| id | item | outcome | owner | firmness | status | depends on | exit check / decides it |
|---|---|---|---|---|---|---|---|
| rotate-proves-key | Rotate the committed PROVES service_role key | The key committed in PROVES_LIBRARY scripts no longer authenticates. | operator | firm | proposed |  | human: Supabase shows the old service_role key revoked |
| roadmap-as-data | Roadmap as data with checks | One machine-checked roadmap everyone works from. | lens-core | firm | in-progress | approve-observatories | python scripts/roadmap.py check |
| install-lens-log-everywhere | Install or update lens-log to 0.1.4 in every Lens repo | The hooks actually run in each repo (settings alone only enable them). | operator | firm | proposed |  | human: /plugin shows lens-log 0.1.4 installed in lens-core, the four siblings and surveyor |
| ingest-derives-plan | lens-ingest works its source and records its own plan | lens-ingest has a plan it derived from PROVES, recorded in its log. | lens-ingest | firm | proposed | siblings-under-lens-log | a decision or process entry in lens-ingest docs/log naming its derived plan |
| review-derives-plan | lens-review works its source and records its own plan | lens-review has a plan it derived from PROVES, recorded in its log. | lens-review | firm | proposed | siblings-under-lens-log | a decision or process entry in lens-review docs/log naming its derived plan |
| serve-derives-plan | lens-serve works its source and records its own plan | lens-serve has a plan it derived from PROVES, recorded in its log. | lens-serve | firm | proposed | siblings-under-lens-log | a decision or process entry in lens-serve docs/log naming its derived plan |
| observe-derives-plan | lens-observe works its source and records its own plan | lens-observe has a plan it derived from PROVES, recorded in its log. | lens-observe | firm | proposed | siblings-under-lens-log | a decision or process entry in lens-observe docs/log naming its derived plan |
| name-proposed-repos | Name the two proposed repos | workflow oversight and access + tenancy can be created. | operator | firm | proposed |  | human: names chosen; lens-core decomposition.json updated with an evaluation entry |
| lens-meaning | Settle what "Lens" means across the system | Tapestry's proposal and the approved architecture agree. | operator | loose | proposed |  | decide when: the operator rules on Tapestry's "Lens = the interface" line (tapestry docs/proposals/2026-10-20-loom-mcp-module.md:11-13) |

## Next

| id | item | outcome | owner | firmness | status | depends on | exit check / decides it |
|---|---|---|---|---|---|---|---|
| log-index-action | Log-index GitHub Action | Shell edits, misses and cross-repo consistency (pieces vs the whole) are caught in CI. | lens-core | firm | proposed | siblings-under-lens-log | CI run lists entries and misses for all Lens repos and fails on a piece that disagrees with the whole |
| roadmap-check-in-ci | Run the roadmap check in CI | A pull request cannot leave roadmap.yaml invalid or ROADMAP.md stale. | lens-core | firm | proposed | roadmap-as-data | CI fails on a deliberately broken roadmap.yaml |
| lens-log-remaining-defects | Fix lens-log M1, M3, M4, M5 | The hook works without a 'python' on PATH, keeps state per repo, resolves paths from the working directory and never overwrites a miss. | surveyor | firm | proposed |  | python -m pytest surveyor/plugins/lens-log/tests |
| spine-neutral-names | Neutral table names in the spine | The standard carries no PROVES table names. | lens-core | firm | proposed |  | grep finds no PROVES table names in docs/schema |
| spine-one-table-choices | Apply the five approved one-table choices | Each kind of data (relationships, aliases, review state, groups, proposals) has one home. | lens-core | firm | proposed | spine-neutral-names | schema test asserts one table per kind |
| spine-scope-column | Scope column on every spine table, neutral about scale | Every row is scoped (to a project or a person) so isolation can be enforced. | lens-core | loose | proposed |  | decide when: where the personal-to-project boundary is enforced is settled (with Tapestry); must land before spine v1 |
| oversight-tables-home | Decide whether the oversight tables stay in the spine | lens-core does not absorb workflow oversight's territory by accident. | lens-core | loose | proposed |  | decide when: the workflow oversight repo is named and has worked its source |
| review-promotion-contract | Review and promotion contract | Candidate -> decision -> verified works, fixing the PROVES 009/011 and CHECK defects. | lens-core | firm | proposed | spine-one-table-choices | test runs source -> candidate -> decision -> verified on an empty database |
| spine-security-defaults | No anonymous grants; remove the source_id trigger bug | The standard starts closed and has no broken trigger. | lens-core | firm | proposed |  | schema test: anon has no grants; all triggers compile |
| launcher-applies-spine | Launcher applies the spine | lens-core stands up the standard on an empty Postgres from LENS_DB_URL, repeatably. | lens-core | firm | proposed | review-promotion-contract, spine-security-defaults | lens-core new applies spine.sql twice to an empty database without error |
| observe-signal-vocabulary | One signal engine and one signal vocabulary | lens-observe and Tapestry's project-observatory do not compute the same signals twice under different names. | lens-observe | loose | proposed |  | decide when: the operator and Tapestry decide which engine is canonical |
| tenancy-home | One home for tenancy | Tenancy is owned once (access + tenancy, Loom_MCP or project-registry). | operator | loose | proposed |  | decide when: Tapestry's breakdown names the Loom_MCP and registry homes |
| teaching-material-handling | Decide which teaching material comes into Surveyor, and in what form | Surveyor's running records hold what agents are taught, without proprietary material in public. | operator | loose | proposed |  | decide when: the operator rules on FRAMES/IAKM and copy vs summary vs pointer |

## Later

| id | item | outcome | owner | firmness | status | depends on | exit check / decides it |
|---|---|---|---|---|---|---|---|
| access-tenancy-repo | Access + tenancy module | Organizations, members, roles, sign-in and row security exist as one module. | access + tenancy | firm | proposed | name-proposed-repos, spine-scope-column | a second org cannot see the first org's rows (test) |
| workflow-oversight-repo | Workflow oversight module (pluggable slot) | An agent team that watches pipeline and dashboard health and agent trust, swappable without touching the dashboard. | workflow oversight | loose | proposed | name-proposed-repos, oversight-tables-home | decide when: the repo is named and has worked its source |
| compose-lab | One command stands up a whole lab | The launcher composes every module against one injected database. | lens-core | firm | proposed | launcher-applies-spine | end-to-end smoke test on a shared test database |
| docs-sites | Docs agent and docs-site skeleton in every Lens repo | Each repo documents itself from a shared skeleton. | lens-core | firm | proposed |  | each repo builds its docs site skeleton |
| candidate-flow-one-pattern | One candidate -> decision flow | Tapestry's architecture-registry promotion and the Lens spine are not two versions of one pattern. | lens-core | hypothesis | proposed |  | decide when: Tapestry decides how personal confirmation works |
| personal-observatory-reuse | Personal observatories built from Lens elements | Tapestry and Loom memory reuse published Lens modules, never a runtime dependency. | tapestry | hypothesis | proposed |  | decide when: Tapestry names which Lens elements it needs |

## Done

| id | item | owner | status | evidence |
|---|---|---|---|---|
| approve-observatories | Approve the observatories architecture and roadmap method | lens-core | done | lens-core a881723 |
| siblings-under-lens-log | Put the four sibling repos under lens-log | lens-core | done | lens-ingest 4f44a63, lens-review 98969f7, lens-serve 7019d56, lens-observe e3f5ccd |
| lens-log-silent-loss-fixes | Fix lens-log M6, M7, M8 | surveyor | done | surveyor a984e18 |
| module-map-check | Module-map change needs an evaluation (lens-log D11) | surveyor | done | surveyor a5910e3, lens-core 4ee947b |
