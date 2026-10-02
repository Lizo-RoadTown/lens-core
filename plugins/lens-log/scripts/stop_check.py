#!/usr/bin/env python3
"""Stop hook: a turn that touched declared decomposition surfaces must leave a log entry.

Blocks once with exact instructions. If the next stop still has no entry, it allows
the stop and writes a docs/log/missed/ marker instead of looping.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lenslog import definition, entries, state  # noqa: E402

HELPER = Path(__file__).resolve().parent / "new_entry.py"


def _context(text: str) -> dict:
    return {"hookSpecificOutput": {"hookEventName": "Stop", "additionalContext": text}}


def block_message(defn, missing: dict[str, list[str]], rejected: list[str]) -> str:
    lines = ["[lens-log] This turn touched parts of the decomposition that need a log entry before you finish:"]
    by_type: dict[str, list[str]] = {}
    for name, evidence in sorted(missing.items()):
        surface = defn.surface(name)
        more = f" (+{len(evidence) - 1} more)" if len(evidence) > 1 else ""
        lines.append(f"  - {name} (needs a {surface.entry} entry): {evidence[0]}{more}")
        by_type.setdefault(surface.entry, []).append(name)
    if rejected:
        lines.append("Not counted, because the '## Lessons' section is empty (write what was learned, or 'none'): "
                     + ", ".join(rejected))
    lines.append("Create the entry with:")
    for entry_type, names in sorted(by_type.items()):
        roots = sorted({r for n in names for e in missing[n] if (r := definition.source_root(defn, e))})
        sources = "".join(f' --source "{r}"' for r in roots)
        lines.append(f'  python "{HELPER}" --type {entry_type} --surfaces {",".join(names)} '
                     f'--slug <short-slug> --title "<what this was>"{sources}')
    lines.append("Then fill in 'What was done', 'What was found / decided' and 'Lessons'. "
                 "See the lens-log:log-entry skill.")
    return "\n".join(lines)


def decide(data: dict, now: datetime | None = None) -> dict | None:
    if data.get("stop_hook_active"):
        return None
    root = definition.find_root(Path(data.get("cwd") or "."))
    if root is None:
        return None
    try:
        defn = definition.load(root)
    except definition.DefinitionError as e:
        return _context(f"[lens-log] decomposition.json is invalid, so logging is not enforced: {e}")

    sid = data.get("session_id", "")
    entries_dir = definition.norm(str(Path(root).joinpath(*entries.ENTRIES_DIR))).rstrip("/") + "/"
    written_now: set[str] = set()
    for call in data.get("tool_calls") or []:
        name, tool_input = call.get("tool_name", ""), call.get("tool_input") or {}
        hits = definition.touches(defn, name, tool_input)
        if hits:
            state.record(sid, hits, entries.list_entries(root))
        for key in definition.WRITE_TOOLS.get(name, ()):
            value = tool_input.get(key)
            if isinstance(value, str) and definition.norm(str(Path(value).resolve())).startswith(entries_dir):
                written_now.add(Path(value).name)

    known = {s.name for s in defn.surfaces}
    pending = {k: v for k, v in state.pending(sid).items() if k in known}
    if not pending:
        state.clear(sid)
        return None
    meta = state.meta(sid) or {}
    before = set(meta.get("entries_before") or [])
    new = {n for n in entries.list_entries(root) if n not in before} | written_now
    covered, rejected = entries.coverage(root, new)
    missing = {k: v for k, v in pending.items() if k not in covered}
    if not missing:
        state.clear(sid)
        return None
    if meta.get("blocked"):
        path = entries.write_missed(root, missing, sid, now or datetime.now())
        state.clear(sid)
        rel = path.relative_to(root).as_posix()
        return _context(f"[lens-log] No log entry was written; recorded a miss at {rel}. The index will list it.")
    state.set_blocked(sid)
    return {"decision": "block", "reason": block_message(defn, missing, rejected)}


def main() -> int:
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0
    try:
        out = decide(data)
    except Exception as e:  # noqa: BLE001 — a hook must never break the session
        print(f"[lens-log] stop_check error: {e!r}", file=sys.stderr)
        return 0
    if out:
        print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
