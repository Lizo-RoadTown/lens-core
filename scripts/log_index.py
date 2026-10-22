#!/usr/bin/env python3
"""Build docs/log/INDEX.md: one index of every Lens module's decomposition log.

    python scripts/log_index.py                 # repos are siblings of this one
    python scripts/log_index.py --repos-dir X   # repos checked out under X (CI)

Deterministic, standard library plus git (lens-log DESIGN.md 3.5). It records the commit
each repo was read at, checks every piece's decomposition.json against the whole, audits
commits that changed a declared surface without adding a log entry (the backstop for shell
edits the hooks cannot see), and lists every recorded miss. Exit 1 on consistency problems.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys
from pathlib import Path

ENTRIES = Path("docs/log/entries")
MISSED = Path("docs/log/missed")
INDEX = Path("docs/log/INDEX.md")


def _load(repo: Path) -> dict:
    return json.loads((repo / "decomposition.json").read_text(encoding="utf-8"))


def _git(repo: Path, *args: str) -> str:
    out = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                         encoding="utf-8", check=True)
    return out.stdout


def front_matter(text: str) -> dict:
    lines = text.splitlines()
    out: dict = {}
    if not lines or lines[0].strip() != "---":
        return out
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if not line or line[0].isspace() or ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            out[key.strip()] = [v.strip() for v in value[1:-1].split(",") if v.strip()]
        else:
            out[key.strip()] = value
    return out


def _title(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def _entries(module: str, repo: Path) -> list[dict]:
    out = []
    for path in sorted((repo / ENTRIES).glob("*.md")):
        text = path.read_text(encoding="utf-8")
        fm = front_matter(text)
        surfaces = fm.get("surfaces", [])
        if isinstance(surfaces, str):
            surfaces = [s.strip() for s in surfaces.split(",") if s.strip()]
        out.append({"module": module, "file": path.name, "date": fm.get("date", ""),
                    "type": fm.get("type", ""), "surfaces": surfaces, "title": _title(text)})
    return out


def _misses(module: str, repo: Path) -> list[dict]:
    out = []
    for path in sorted((repo / MISSED).glob("*.json")):
        try:
            surfaces = sorted(json.loads(path.read_text(encoding="utf-8")).get("surfaces", {}))
        except (OSError, json.JSONDecodeError):
            surfaces = ["(unreadable)"]
        out.append({"module": module, "file": path.name, "surfaces": surfaces})
    return out


def _consistency(module: str, piece: dict, whole: dict) -> list[str]:
    problems = []
    if piece.get("role") != "piece":
        problems.append(f"{module}: role is {piece.get('role')!r}, expected 'piece'")
    if piece.get("module") != module:
        problems.append(f"{module}: decomposition.json names module {piece.get('module')!r}")
    known = {(s.get("name"), tuple(s.get("match", []))) for s in whole.get("sources", [])}
    for s in piece.get("sources", []):
        if (s.get("name"), tuple(s.get("match", []))) not in known:
            problems.append(f"{module}: source {s.get('name')!r} is not declared by the whole")
    return problems


def _audit(module: str, repo: Path, defn: dict) -> list[dict]:
    patterns = [p for s in defn.get("surfaces", []) for p in s.get("paths", []) if p != "@sources"]
    log = _git(repo, "log", "--reverse", "--name-status", "--format=%x1e%h%x1f%s")
    rows, logging_began = [], False
    for block in log.split("\x1e")[1:]:
        head, _, body = block.partition("\n")
        sha, _, subject = head.partition("\x1f")
        files = [line.split("\t")[-1] for line in body.splitlines() if "\t" in line]
        adds_entry = any(f.startswith(ENTRIES.as_posix() + "/") for f in files)
        if not logging_began:
            logging_began = adds_entry
            continue
        touched = [f for f in files if any(fnmatch.fnmatch(f, p) for p in patterns)]
        if touched and not adds_entry:
            rows.append({"module": module, "commit": sha, "subject": subject, "files": touched})
    return rows


def build(root: Path, repos_dir: Path) -> dict:
    root, repos_dir = Path(root), Path(repos_dir)
    whole = _load(root)
    idx: dict = {"whole": whole.get("module"), "commits": {}, "entries": [], "misses": [],
                 "audit": [], "problems": [], "not_created": list(whole.get("proposed", []))}
    for module in whole.get("modules", []):
        repo = root if module == whole.get("module") else repos_dir / module
        if not (repo / "decomposition.json").is_file():
            idx["problems"].append(f"{module}: no repo with a decomposition.json at {repo}")
            continue
        defn = _load(repo)
        if repo != root:
            idx["problems"].extend(_consistency(module, defn, whole))
        idx["commits"][module] = _git(repo, "rev-parse", "--short", "HEAD").strip()
        idx["entries"].extend(_entries(module, repo))
        idx["misses"].extend(_misses(module, repo))
        idx["audit"].extend(_audit(module, repo, defn))
    idx["entries"].sort(key=lambda e: (e["date"], e["file"]), reverse=True)
    return idx


def _cell(value) -> str:
    if isinstance(value, list):
        value = ", ".join(value)
    return str(value).replace("|", "\\|").replace("\n", " ")


def render(idx: dict, owner: str) -> str:
    def link(e: dict) -> str:
        if e["module"] == idx["whole"]:
            return f"[{e['file']}](entries/{e['file']})"
        return f"[{e['file']}](https://github.com/{owner}/{e['module']}/blob/main/{ENTRIES.as_posix()}/{e['file']})"

    out = ["# Decomposition log index", "",
           "<!-- generated by scripts/log_index.py; do not edit by hand -->", "",
           "Every Lens module's log in one place. Entries are written in each repo; this file is rebuilt",
           "by the log-index workflow (daily, on demand, and on push to lens-core).", "",
           "## Built from", "", "| module | commit |", "|---|---|"]
    out += [f"| {m} | {c} |" for m, c in sorted(idx["commits"].items())]
    if idx["not_created"]:
        out += ["", "Proposed, no repo yet: " + ", ".join(idx["not_created"]) + "."]
    out += ["", "## Consistency", ""]
    out += [f"- {p}" for p in idx["problems"]] or ["Every piece agrees with the whole."]
    out += ["", "## Audit", "",
            "Commits that changed a declared surface without adding a log entry, after the repo's",
            "logging began. Usually a shell edit, or an entry committed separately; check each.", ""]
    if idx["audit"]:
        out += ["| module | commit | subject | files |", "|---|---|---|---|"]
        out += [f"| {a['module']} | {a['commit']} | {_cell(a['subject'])} | {_cell(a['files'])} |"
                for a in idx["audit"]]
    else:
        out.append("None.")
    out += ["", "## Misses", ""]
    if idx["misses"]:
        out += ["| module | marker | surfaces |", "|---|---|---|"]
        out += [f"| {m['module']} | {m['file']} | {_cell(m['surfaces'])} |" for m in idx["misses"]]
    else:
        out.append("None.")
    out += ["", f"## Entries ({len(idx['entries'])})", "",
            "| date | module | type | surfaces | entry | file |", "|---|---|---|---|---|---|"]
    out += [f"| {e['date']} | {e['module']} | {e['type']} | {_cell(e['surfaces'])} | {_cell(e['title'])} | {link(e)} |"
            for e in idx["entries"]]
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    root_default = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", default=str(root_default))
    ap.add_argument("--repos-dir", default=None, help="folder holding the sibling repos")
    ap.add_argument("--owner", default="Lizo-RoadTown")
    args = ap.parse_args(argv)
    root = Path(args.root)
    idx = build(root, Path(args.repos_dir) if args.repos_dir else root.parent)
    (root / INDEX).parent.mkdir(parents=True, exist_ok=True)
    (root / INDEX).write_text(render(idx, args.owner), encoding="utf-8", newline="\n")
    for p in idx["problems"]:
        print(p)
    print(f"{len(idx['entries'])} entries, {len(idx['audit'])} audit rows, {len(idx['misses'])} misses")
    return 1 if idx["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
