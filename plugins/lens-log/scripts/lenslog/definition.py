"""Load a repo's decomposition.json and match touched paths to its surfaces.

The definition file is the only thing that says what "the decomposition" is for a
repo. Hook code never hardcodes paths; it asks this module.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

DEFINITION_FILE = "decomposition.json"
ENTRY_TYPES = ("process", "decision", "skill", "lesson")
TRIGGERS = ("write", "read-or-write")

READ_TOOLS: dict[str, tuple[str, ...]] = {
    "Read": ("file_path",),
    "Grep": ("path",),
    "Glob": ("path", "pattern"),
}
WRITE_TOOLS: dict[str, tuple[str, ...]] = {
    "Edit": ("file_path",),
    "Write": ("file_path",),
    "MultiEdit": ("file_path",),
    "NotebookEdit": ("notebook_path",),
}
SHELL_TOOLS = ("Bash", "PowerShell")

# A source name in a shell command counts only in a path context (commands are
# normalized to forward slashes first), so mentions in messages or grep patterns don't.
_END = r"(?=$|[\s/\"';&|),])"
_SHELL_FORMS = (
    r"/{m}" + _END,                                                    # inside a path
    r"(?:^|[\s\"'=(;&|]){m}/",                                         # relative path start
    r"(?:^|[\s(;&|])(?i:cd|pushd|set-location|sl)\s+[\"']?{m}" + _END,  # change into it
    r"(?:^|\s)-[cC]\s+[\"']?{m}" + _END,                               # git -C <dir>
)


class DefinitionError(ValueError):
    """decomposition.json is present but malformed."""


@dataclass(frozen=True)
class Surface:
    name: str
    patterns: tuple[str, ...]
    on: str
    entry: str


@dataclass(frozen=True)
class Definition:
    root: Path
    module: str
    surfaces: tuple[Surface, ...]
    sources: tuple[str, ...]

    def surface(self, name: str) -> Surface:
        for s in self.surfaces:
            if s.name == name:
                return s
        raise KeyError(name)


def find_root(start: Path) -> Path | None:
    start = Path(start).resolve()
    for folder in (start, *start.parents):
        if (folder / DEFINITION_FILE).is_file():
            return folder
    return None


def load(root: Path) -> Definition:
    try:
        data = json.loads((Path(root) / DEFINITION_FILE).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise DefinitionError(f"cannot read {DEFINITION_FILE}: {e}") from e
    if not isinstance(data, dict) or data.get("version") != 1:
        raise DefinitionError("'version' must be 1")
    module = data.get("module")
    if not isinstance(module, str) or not module:
        raise DefinitionError("'module' is required")
    sources = tuple(p for s in data.get("sources", []) for p in s.get("match", []))
    surfaces = []
    for raw in data.get("surfaces", []):
        name, on, entry = raw.get("name"), raw.get("on", "write"), raw.get("entry")
        if not name:
            raise DefinitionError("a surface has no 'name'")
        if on not in TRIGGERS:
            raise DefinitionError(f"surface {name}: 'on' must be one of {TRIGGERS}")
        if entry not in ENTRY_TYPES:
            raise DefinitionError(f"surface {name}: 'entry' must be one of {ENTRY_TYPES}")
        patterns: list[str] = []
        for p in raw.get("paths", []):
            patterns.extend(sources if p == "@sources" else [p])
        if not patterns:
            raise DefinitionError(f"surface {name}: no paths")
        surfaces.append(Surface(name, tuple(patterns), on, entry))
    if not surfaces:
        raise DefinitionError("no surfaces declared")
    return Definition(Path(root).resolve(), module, tuple(surfaces), sources)


def norm(path: str) -> str:
    p = str(path).replace("\\", "/")
    return p.lower() if os.name == "nt" else p


def _regex(pattern: str) -> re.Pattern[str]:
    out, i = [], 0
    while i < len(pattern):
        if pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("".join(out) + r"\Z")


def _candidates(defn: Definition, path: str) -> list[str]:
    p = Path(path)
    absn = norm(str((p if p.is_absolute() else defn.root / p).resolve())).rstrip("/")
    rootn = norm(str(defn.root)).rstrip("/") + "/"
    out = [absn, absn + "/"]
    if absn.startswith(rootn):
        rel = absn[len(rootn):]
        out += [rel, rel + "/"]
    return out


def match_path(defn: Definition, path: str, kind: str) -> set[str]:
    cands = _candidates(defn, path)
    hits = set()
    for s in defn.surfaces:
        if kind == "read" and s.on != "read-or-write":
            continue
        if any(_regex(norm(pat)).match(c) for pat in s.patterns for c in cands):
            hits.add(s.name)
    return hits


def _marker(pattern: str) -> str | None:
    """The literal folder name inside a pattern like '**/PROVES_LIBRARY/**'."""
    core = pattern
    if core.startswith("**/"):
        core = core[3:]
    if core.endswith("/**"):
        core = core[:-3]
    if not core or any(ch in core for ch in "*?[/"):
        return None
    return norm(core)


def touches(defn: Definition, tool_name: str, tool_input: dict) -> dict[str, list[str]]:
    hits: dict[str, list[str]] = {}

    def add(names: set[str], evidence: str) -> None:
        for n in names:
            hits.setdefault(n, []).append(evidence)

    if tool_name in SHELL_TOOLS:
        cmd = str(tool_input.get("command", ""))
        cmdn = norm(cmd)
        for s in defn.surfaces:
            if s.on != "read-or-write":
                continue
            for pat in s.patterns:
                m = _marker(pat)
                if m and any(re.search(form.format(m=re.escape(m)), cmdn) for form in _SHELL_FORMS):
                    add({s.name}, "$ " + cmd[:200])
                    break
        return hits
    kind = "write" if tool_name in WRITE_TOOLS else "read" if tool_name in READ_TOOLS else None
    if kind is None:
        return hits
    keys = WRITE_TOOLS.get(tool_name) or READ_TOOLS[tool_name]
    for key in keys:
        value = tool_input.get(key)
        if isinstance(value, str) and value:
            add(match_path(defn, value, kind), value)
    return hits


def source_root(defn: Definition, path: str) -> str | None:
    """The local folder of the source repo a path is inside, e.g. '.../PROVES_LIBRARY'."""
    if path.startswith("$ "):
        return None
    parts = str(path).replace("\\", "/").split("/")
    markers = {m for m in (_marker(p) for p in defn.sources) if m}
    for i, part in enumerate(parts):
        if norm(part) in markers:
            return "/".join(parts[: i + 1])
    return None
