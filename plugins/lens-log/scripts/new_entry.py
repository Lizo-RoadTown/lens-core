#!/usr/bin/env python3
"""Create a correctly shaped decomposition log entry and print its path.

The agent then fills in the prose sections. The header (type, module, surfaces,
date, source commits) is filled here so it is never typed by hand.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lenslog import definition, entries  # noqa: E402

SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def source_commit(path: str) -> str:
    """Short HEAD of the repo whose root is exactly `path`; 'unknown' otherwise.

    The root check matters: a plain folder inside another repo (e.g. a home folder that
    is itself a git repo) would otherwise report that outer repo's commit.
    """
    try:
        out = subprocess.run(["git", "-C", path, "rev-parse", "--show-toplevel", "--short", "HEAD"],
                             capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    lines = out.stdout.split()
    if out.returncode != 0 or len(lines) != 2:
        return "unknown"
    toplevel, sha = lines
    same = definition.norm(str(Path(toplevel).resolve())) == definition.norm(str(Path(path).resolve()))
    return sha if same else "unknown"


def render(defn, entry_type: str, surfaces: list[str], title: str,
           commits: dict[str, str], now: datetime) -> str:
    if commits:
        commit_lines = "source_commits:\n" + "".join(f"  {k}: {v}\n" for k, v in sorted(commits.items()))
    else:
        commit_lines = "source_commits: {}\n"
    return (
        "---\n"
        f"type: {entry_type}\n"
        f"module: {defn.module}\n"
        f"surfaces: [{', '.join(surfaces)}]\n"
        f"date: {now:%Y-%m-%dT%H:%M}\n"
        f"{commit_lines}"
        "---\n\n"
        f"# {title}\n\n"
        "## What was done\n<!-- what was examined or changed, with file paths -->\n\n"
        "## What was found / decided\n<!-- findings, decisions, and why -->\n\n"
        "## Lessons\n<!-- required: what was learned, or write the word none -->\n"
    )


def _fail(msg: str) -> int:
    print(f"[lens-log] {msg}", file=sys.stderr)
    return 2


def main(argv: list[str] | None = None, now: datetime | None = None) -> int:
    p = argparse.ArgumentParser(description="Create a decomposition log entry.")
    p.add_argument("--type", required=True)
    p.add_argument("--surfaces", required=True, help="comma-separated surface names ('' for none)")
    p.add_argument("--slug", required=True)
    p.add_argument("--title", default=None)
    p.add_argument("--source", action="append", default=[], help="local folder of a source repo that was read")
    p.add_argument("--root", default=None, help="repo root (default: found from the current folder)")
    args = p.parse_args(argv)

    root = Path(args.root) if args.root else definition.find_root(Path.cwd())
    if root is None:
        return _fail("no decomposition.json found here or above")
    try:
        defn = definition.load(root)
    except definition.DefinitionError as e:
        return _fail(str(e))
    if args.type not in definition.ENTRY_TYPES:
        return _fail(f"--type must be one of {definition.ENTRY_TYPES}")
    surfaces = [s.strip() for s in args.surfaces.split(",") if s.strip()]
    known = {s.name for s in defn.surfaces}
    unknown = [s for s in surfaces if s not in known]
    if unknown:
        return _fail(f"unknown surface(s) {unknown}; declared: {sorted(known)}")
    if not SLUG.match(args.slug):
        return _fail("--slug must be lowercase letters, digits and dashes")

    now = now or datetime.now()
    commits = {Path(src).name: source_commit(src) for src in args.source}
    folder = Path(root).joinpath(*entries.ENTRIES_DIR)
    folder.mkdir(parents=True, exist_ok=True)
    stem = f"{now:%Y-%m-%d-%H%M}-{args.slug}"
    path, n = folder / f"{stem}.md", 2
    while path.exists():
        path, n = folder / f"{stem}-{n}.md", n + 1
    path.write_text(render(defn, args.type, surfaces, args.title or args.slug, commits, now), encoding="utf-8")
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
