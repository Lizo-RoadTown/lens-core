---
type: process
module: lens-core
surfaces: [roadmap]
date: 2026-10-21T06:40
source_commits: {}
---

# Roadmap check runs in CI; two items done

## What was done
- Added `.github/workflows/roadmap.yml` (10a8896): on pushes to main and on pull requests it
  runs `python scripts/roadmap.py check` and the tests.
- Verified the exit check. Run 39609823937 passed on main. A draft pull request (#1) with one
  item flipped to done without evidence failed in run 39609904466, reporting "a done item needs
  evidence" and "ROADMAP.md is out of date". The pull request was closed and its branch
  deleted.
- Marked `roadmap-as-data` and `roadmap-check-in-ci` done with evidence.

## What was found / decided
The workflow does not run on pushes to other branches, so a probe needs a pull request. That is
acceptable: changes reach main only by push (checked) or pull request (checked).

## Lessons
Prove a gate fails on bad input before calling it a gate.
