"""Per-session record of surfaces touched since the last satisfied log check.

Touches are appended one JSON line at a time, so parallel subagents do not overwrite
each other. Lives outside the repo: ~/.claude/cache/lens-log/ (or LENS_LOG_STATE_DIR).
"""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

MAX_EVIDENCE = 10


def _dir() -> Path:
    return Path(os.environ.get("LENS_LOG_STATE_DIR") or Path.home() / ".claude" / "cache" / "lens-log")


def _base(session_id: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", session_id or "unknown")
    return _dir() / safe


def _touches(session_id: str) -> Path:
    return _base(session_id).with_name(_base(session_id).name + ".touches.jsonl")


def _meta(session_id: str) -> Path:
    return _base(session_id).with_name(_base(session_id).name + ".json")


def meta(session_id: str) -> dict | None:
    try:
        return json.loads(_meta(session_id).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _write_meta(session_id: str, data: dict) -> None:
    path = _meta(session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(data), encoding="utf-8")
    os.replace(tmp, path)


def record(session_id: str, hits: dict[str, list[str]], entries_now: list[str]) -> None:
    if meta(session_id) is None:
        _write_meta(session_id, {"entries_before": list(entries_now), "blocked": False,
                                 "since": time.time()})
    path = _touches(session_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for surface, evidence in hits.items():
            for e in evidence:
                f.write(json.dumps({"surface": surface, "evidence": e}) + "\n")


def pending(session_id: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    try:
        lines = _touches(session_id).read_text(encoding="utf-8").splitlines()
    except OSError:
        return out
    for line in lines:
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        bucket = out.setdefault(item["surface"], [])
        if item["evidence"] not in bucket and len(bucket) < MAX_EVIDENCE:
            bucket.append(item["evidence"])
    return out


def set_blocked(session_id: str) -> None:
    data = meta(session_id) or {"entries_before": [], "blocked": False}
    data["blocked"] = True
    _write_meta(session_id, data)


def clear(session_id: str) -> None:
    for path in (_touches(session_id), _meta(session_id)):
        try:
            path.unlink()
        except FileNotFoundError:
            pass
