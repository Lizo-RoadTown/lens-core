#!/usr/bin/env python3
"""The roadmap: roadmap.yaml is the source of truth; ROADMAP.md is generated from it.

    python scripts/roadmap.py check    # validate roadmap.yaml and that ROADMAP.md is current
    python scripts/roadmap.py render   # regenerate ROADMAP.md

Rules come from the approved method (docs/plans/2026-10-21-roadmap-method-proposal.md):
only firm items are built, done needs evidence, loose items name what decides them, and
every owner is a module in decomposition.json (or a listed outside owner).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

REQUIRED = ("id", "title", "outcome", "horizon", "firmness", "status", "owner")
HORIZONS = ("now", "next", "later")
FIRMNESS = ("firm", "loose", "hypothesis")
STATUSES = ("proposed", "in-progress", "blocked", "done", "dropped", "superseded")
BUILDING = ("in-progress", "done")


def module_map(root: Path) -> set[str]:
    data = json.loads((Path(root) / "decomposition.json").read_text(encoding="utf-8"))
    return set(data.get("modules", [])) | set(data.get("proposed", []))


def _cycles(deps: dict[str, list[str]]) -> list[str]:
    found, state = [], {}

    def visit(node: str, path: list[str]) -> None:
        state[node] = "open"
        for nxt in deps.get(node, []):
            if state.get(nxt) == "open":
                found.append(" -> ".join(path[path.index(nxt):] + [nxt]))
            elif nxt in deps and nxt not in state:
                visit(nxt, path + [nxt])
        state[node] = "closed"

    for node in deps:
        if node not in state:
            visit(node, [node])
    return found


def check(doc: dict, modules: set[str]) -> list[str]:
    errs: list[str] = []
    if doc.get("version") != 1:
        errs.append("'version' must be 1")
    items = doc.get("items") or []
    owners = modules | set(doc.get("owners") or [])
    by_id: dict[str, dict] = {}
    for it in items:
        iid = it.get("id", "?")
        for field in REQUIRED:
            if not it.get(field):
                errs.append(f"{iid}: missing '{field}'")
        for field, allowed in (("horizon", HORIZONS), ("firmness", FIRMNESS), ("status", STATUSES)):
            if it.get(field) and it[field] not in allowed:
                errs.append(f"{iid}: '{field}' must be one of {', '.join(allowed)}")
        if iid in by_id:
            errs.append(f"{iid}: duplicate id")
        by_id[iid] = it
        if it.get("owner") and it["owner"] not in owners:
            errs.append(f"{iid}: owner '{it['owner']}' is not a module in decomposition.json "
                        "or a listed outside owner")
        if it.get("firmness") == "firm" and not it.get("exit_check"):
            errs.append(f"{iid}: a firm item needs an exit_check")
        if it.get("firmness") in ("loose", "hypothesis"):
            if not it.get("decide_when"):
                errs.append(f"{iid}: a {it['firmness']} item needs decide_when (the fact that decides it)")
            if it.get("status") in BUILDING:
                errs.append(f"{iid}: only firm items may be in progress or done")
        if it.get("status") == "done" and not it.get("evidence"):
            errs.append(f"{iid}: a done item needs evidence")
    deps = {i: list(it.get("depends_on") or []) for i, it in by_id.items()}
    for iid, ds in deps.items():
        for d in ds:
            if d not in by_id:
                errs.append(f"{iid}: depends on unknown item '{d}'")
            elif by_id[iid].get("status") in BUILDING and by_id[d].get("status") != "done":
                errs.append(f"{iid}: is {by_id[iid]['status']} but '{d}' is not done")
    errs.extend(f"dependency cycle: {c}" for c in _cycles(deps))
    covered = {it.get("owner") for it in items} | set(doc.get("parked") or [])
    errs.extend(f"module '{m}' has no item and is not parked" for m in sorted(modules - covered))
    return errs


def _cell(value) -> str:
    if isinstance(value, list):
        value = ", ".join(str(v) for v in value)
    return str(value or "").replace("|", "\\|").replace("\n", " ")


def render(doc: dict) -> str:
    items = doc.get("items") or []
    out = ["# Roadmap", "",
           "<!-- generated from roadmap.yaml by scripts/roadmap.py; edit roadmap.yaml, not this file -->",
           "",
           "One roadmap for the Lens. Only **firm** items are built; **loose** and **hypothesis** items",
           "name the fact that decides them. Method: "
           "[docs/plans/2026-10-21-roadmap-method-proposal.md](docs/plans/2026-10-21-roadmap-method-proposal.md).",
           ""]
    open_items = [i for i in items if i.get("status") not in ("done", "dropped", "superseded")]
    for horizon in HORIZONS:
        rows = [i for i in open_items if i.get("horizon") == horizon]
        if not rows:
            continue
        out += [f"## {horizon.capitalize()}", "",
                "| id | item | outcome | owner | firmness | status | depends on | exit check / decides it |",
                "|---|---|---|---|---|---|---|---|"]
        for i in rows:
            gate = i.get("exit_check") if i.get("firmness") == "firm" else f"decide when: {i.get('decide_when')}"
            out.append("| " + " | ".join(_cell(v) for v in (
                i.get("id"), i.get("title"), i.get("outcome"), i.get("owner"), i.get("firmness"),
                i.get("status"), i.get("depends_on"), gate)) + " |")
        out.append("")
    closed = [i for i in items if i not in open_items]
    if closed:
        out += ["## Done", "", "| id | item | owner | status | evidence |", "|---|---|---|---|---|"]
        for i in closed:
            out.append("| " + " | ".join(_cell(v) for v in (
                i.get("id"), i.get("title"), i.get("owner"), i.get("status"), i.get("evidence"))) + " |")
        out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("command", choices=("check", "render"))
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    args = ap.parse_args(argv)
    root = Path(args.root)
    doc = yaml.safe_load((root / "roadmap.yaml").read_text(encoding="utf-8")) or {}
    md_path = root / "ROADMAP.md"
    if args.command == "render":
        md_path.write_text(render(doc), encoding="utf-8", newline="\n")
        return 0
    errs = check(doc, module_map(root))
    current = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
    if current.replace("\r\n", "\n") != render(doc):
        errs.append("ROADMAP.md is out of date: run python scripts/roadmap.py render")
    for e in errs:
        print(e)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
