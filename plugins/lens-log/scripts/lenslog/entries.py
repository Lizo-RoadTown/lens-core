"""Log entry files: listing, parsing their header, and the Lessons requirement."""
from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path

ENTRIES_DIR = ("docs", "log", "entries")
MISSED_DIR = ("docs", "log", "missed")

_LESSONS = re.compile(r"^## Lessons[ \t]*\n(.*?)(?=^## |\Z)", re.S | re.M)
_COMMENT = re.compile(r"<!--.*?-->", re.S)


def list_entries(root: Path) -> list[str]:
    d = Path(root).joinpath(*ENTRIES_DIR)
    return sorted(p.name for p in d.glob("*.md")) if d.is_dir() else []


def front_matter(text: str) -> dict[str, object]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    out: dict[str, object] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return out
        if not line or line[0].isspace() or ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            out[key.strip()] = [v.strip() for v in value[1:-1].split(",") if v.strip()]
        else:
            out[key.strip()] = value
    return {}


def has_lessons(text: str) -> bool:
    m = _LESSONS.search(_COMMENT.sub("", text))
    return bool(m and m.group(1).strip())


def coverage(root: Path, names: set[str]) -> tuple[set[str], list[str]]:
    covered: set[str] = set()
    rejected: list[str] = []
    for name in sorted(names):
        try:
            text = Path(root).joinpath(*ENTRIES_DIR, name).read_text(encoding="utf-8")
        except OSError:
            continue
        if not has_lessons(text):
            rejected.append(name)
            continue
        surfaces = front_matter(text).get("surfaces", [])
        covered.update([surfaces] if isinstance(surfaces, str) else surfaces)
    return covered, rejected


def write_missed(root: Path, missing: dict[str, list[str]], session_id: str, now: datetime) -> Path:
    d = Path(root).joinpath(*MISSED_DIR)
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{now:%Y-%m-%d-%H%M%S}.json"
    record = {"session_id": session_id, "at": now.isoformat(timespec="seconds"), "surfaces": missing}
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return path
