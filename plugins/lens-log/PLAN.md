# lens-log (build step 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** In lens-core, enforce that any turn touching a declared decomposition surface ends with a file-based log entry, driven only by `decomposition.json`.

**Architecture:** A Claude Code plugin at `plugins/lens-log/`. A `PostToolUse` hook records which declared surfaces each tool call touched (main agent and subagents) into a per-session file outside the repo. A `Stop` hook blocks the end of a turn until new entry files under `docs/log/entries/` cover every touched surface; it blocks at most once, then writes a `docs/log/missed/` marker. A helper script creates correctly shaped entries.

**Tech Stack:** Python ≥3.11 stdlib only (hook logic), Node (hook launcher, already required by Claude Code), pytest (tests).

**Spec:** [`plugins/lens-log/DESIGN.md`](DESIGN.md) — sections 3.1–3.4 and build step 1. Steps 3 (siblings) and 4 (index Action) get their own plans.

## Global Constraints

- Python stdlib only at runtime; must run on Python 3.11 (`requires-python = ">=3.11"` in `pyproject.toml`).
- Hooks must never crash a session: every entry point catches exceptions, prints to stderr, exits 0.
- The only way to block is Stop hook JSON `{"decision": "block", "reason": "..."}` on stdout, exit 0.
- No machine-specific paths in committed files. Paths are matched by pattern (`**/PROVES_LIBRARY/**`).
- Hook code never hardcodes surfaces; everything comes from `decomposition.json`.
- Session state lives outside the repo: `~/.claude/cache/lens-log/`, overridable with env `LENS_LOG_STATE_DIR`.
- Names `lens-log` and `decomposition.json` are placeholders the operator may rename.
- PROVES repos are read-only source. Never write to them.
- Commit trailer: `Co-Authored-By: Claude <noreply@anthropic.com>`.
- Run tests with: `python -m pytest plugins/lens-log/tests -v` from the repo root.

## Review Focus

1. **Windows path spelling** (`c:\Users\...` vs `C:/Users/...`) must match the same surface. → Task 1 test `test_windows_case_and_slashes`.
2. **A source repo's root folder itself** (Grep `path` = `...\PROVES_LIBRARY`, no trailing slash) must count as touching the source. → Task 1 test `test_source_root_folder_itself`.
3. **Malformed or missing `decomposition.json`** must never block or crash; the turn ends normally. → Task 5 tests `test_invalid_definition_warns_not_blocks`, `test_no_definition_is_silent`.
4. **An entry with the Lessons section left as the template** must not count, and the block message must say why. → Task 5 test `test_template_lessons_not_counted`.
5. **An agent that ignores the block** must not loop forever; the second stop is allowed and a miss is recorded. → Task 5 test `test_second_stop_records_miss_and_allows`.

---

## File Structure

```text
lens-core/
├── decomposition.json                         # Task 7 — the whole (lens-core's definition)
├── .claude-plugin/marketplace.json            # Task 6 — lens-core as a plugin marketplace
├── .claude/settings.json                      # Task 7 — enable lens-log (modify)
├── docs/log/entries/.gitkeep                  # Task 7
└── plugins/lens-log/
    ├── DESIGN.md / PLAN.md                    # spec + this plan
    ├── .claude-plugin/plugin.json             # Task 6
    ├── hooks/hooks.json                       # Task 6 — PostToolUse + Stop
    ├── hooks/run-python.mjs                   # Task 6 — Node launcher (finds Python)
    ├── skills/log-entry/SKILL.md              # Task 6
    ├── scripts/
    │   ├── lenslog/__init__.py                # Task 1
    │   ├── lenslog/definition.py              # Task 1 — load definition, match paths
    │   ├── lenslog/state.py                   # Task 2 — per-session touch record
    │   ├── lenslog/entries.py                 # Task 2 — list/parse entries, lessons, misses
    │   ├── new_entry.py                       # Task 3 — helper CLI
    │   ├── record_touch.py                    # Task 4 — PostToolUse entry point
    │   └── stop_check.py                      # Task 5 — Stop entry point
    └── tests/
        ├── conftest.py                        # Task 1
        ├── test_definition.py                 # Task 1
        ├── test_state_entries.py              # Task 2
        ├── test_new_entry.py                  # Task 3
        ├── test_record_touch.py               # Task 4
        ├── test_stop_check.py                 # Task 5
        ├── test_launcher.py                   # Task 6
        └── test_real_definition.py            # Task 7
```

---

### Task 1: Definition loading and path matching

**Files:**
- Create: `plugins/lens-log/scripts/lenslog/__init__.py`
- Create: `plugins/lens-log/scripts/lenslog/definition.py`
- Create: `plugins/lens-log/tests/conftest.py`
- Test: `plugins/lens-log/tests/test_definition.py`

**Interfaces:**
- Produces:
  - `DEFINITION_FILE = "decomposition.json"`, `ENTRY_TYPES = ("process","decision","skill","lesson")`, `WRITE_TOOLS: dict[str, tuple[str, ...]]`
  - `class DefinitionError(ValueError)`
  - `@dataclass Surface(name: str, patterns: tuple[str,...], on: str, entry: str)`
  - `@dataclass Definition(root: Path, module: str, surfaces: tuple[Surface,...], sources: tuple[str,...])` with `.surface(name) -> Surface` (raises `KeyError`)
  - `find_root(start: Path) -> Path | None`
  - `load(root: Path) -> Definition` (raises `DefinitionError`)
  - `norm(path: str) -> str`
  - `match_path(defn, path: str, kind: str) -> set[str]` — `kind` is `"read"` or `"write"`
  - `touches(defn, tool_name: str, tool_input: dict) -> dict[str, list[str]]` — surface name → evidence strings; shell evidence starts with `"$ "`
  - `source_root(defn, path: str) -> str | None`
  - test fixture `repo(tmp_path) -> Path` (a repo root containing a sample `decomposition.json`)

- [ ] **Step 1: Write the fixture and failing tests**

`plugins/lens-log/tests/conftest.py`:

```python
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

SAMPLE = {
    "version": 1,
    "role": "whole",
    "module": "lens-core",
    "sources": [
        {"name": "PROVES_LIBRARY", "repo": "Lizo-RoadTown/PROVES_LIBRARY",
         "match": ["**/PROVES_LIBRARY/**"]},
        {"name": "proves-curation-dashboard", "repo": "Lizo-RoadTown/proves-curation-dashboard",
         "match": ["**/proves-curation-dashboard/**"]},
    ],
    "surfaces": [
        {"name": "source", "paths": ["@sources"], "on": "read-or-write", "entry": "process"},
        {"name": "bus", "paths": ["docs/schema/**"], "on": "write", "entry": "decision"},
        {"name": "identity", "paths": ["CHARTER.md", "CLAUDE.md"], "on": "write", "entry": "decision"},
        {"name": "skills", "paths": ["skills/**"], "on": "write", "entry": "skill"},
        {"name": "module", "paths": ["src/**"], "on": "write", "entry": "process"},
    ],
}


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "lens-core"
    root.mkdir()
    (root / "decomposition.json").write_text(json.dumps(SAMPLE), encoding="utf-8")
    return root


@pytest.fixture
def source_dir(tmp_path):
    d = tmp_path / "elsewhere" / "PROVES_LIBRARY"
    (d / "supabase").mkdir(parents=True)
    return d


@pytest.fixture(autouse=True)
def state_dir(tmp_path, monkeypatch):
    d = tmp_path / "state"
    monkeypatch.setenv("LENS_LOG_STATE_DIR", str(d))
    return d
```

`plugins/lens-log/tests/test_definition.py`:

```python
import json
import os

import pytest

from lenslog import definition as d


def test_find_root_walks_up(repo):
    nested = repo / "src" / "deep"
    nested.mkdir(parents=True)
    assert d.find_root(nested) == repo.resolve()


def test_find_root_none(tmp_path):
    assert d.find_root(tmp_path) is None


def test_load_expands_sources(repo):
    defn = d.load(repo)
    assert defn.module == "lens-core"
    assert defn.surface("source").patterns == ("**/PROVES_LIBRARY/**", "**/proves-curation-dashboard/**")
    assert defn.sources == ("**/PROVES_LIBRARY/**", "**/proves-curation-dashboard/**")


@pytest.mark.parametrize("bad", [
    "not json",
    json.dumps({"version": 2, "module": "x", "surfaces": []}),
    json.dumps({"version": 1, "surfaces": [{"name": "a", "paths": ["x"], "entry": "process"}]}),
    json.dumps({"version": 1, "module": "x", "surfaces": [{"name": "a", "paths": ["x"], "entry": "nope"}]}),
    json.dumps({"version": 1, "module": "x", "surfaces": [{"name": "a", "paths": ["x"], "on": "sometimes", "entry": "process"}]}),
    json.dumps({"version": 1, "module": "x", "surfaces": []}),
])
def test_load_rejects_malformed(tmp_path, bad):
    (tmp_path / "decomposition.json").write_text(bad, encoding="utf-8")
    with pytest.raises(d.DefinitionError):
        d.load(tmp_path)


def test_write_surfaces_relative_to_root(repo):
    defn = d.load(repo)
    assert d.match_path(defn, str(repo / "CHARTER.md"), "write") == {"identity"}
    assert d.match_path(defn, "docs/schema/spine.sql", "write") == {"bus"}
    assert d.match_path(defn, str(repo / "skills" / "x" / "SKILL.md"), "write") == {"skills"}
    assert d.match_path(defn, str(repo / "README.md"), "write") == set()


def test_reads_only_trigger_read_or_write_surfaces(repo, source_dir):
    defn = d.load(repo)
    assert d.match_path(defn, str(repo / "CHARTER.md"), "read") == set()
    assert d.match_path(defn, str(source_dir / "supabase" / "009.sql"), "read") == {"source"}


def test_other_repo_same_relative_path_not_matched(repo, tmp_path):
    defn = d.load(repo)
    other = tmp_path / "lens-review" / "CHARTER.md"
    assert d.match_path(defn, str(other), "write") == set()


def test_source_root_folder_itself(repo, source_dir):
    defn = d.load(repo)
    assert d.match_path(defn, str(source_dir), "read") == {"source"}


@pytest.mark.skipif(os.name != "nt", reason="Windows paths are case-insensitive")
def test_windows_case_and_slashes(repo, source_dir):
    defn = d.load(repo)
    upper = str(source_dir / "x.py").upper()
    assert d.match_path(defn, upper, "read") == {"source"}
    assert d.match_path(defn, str(repo / "CHARTER.md").replace("\\", "/").lower(), "write") == {"identity"}


def test_single_star_does_not_cross_folders(tmp_path):
    (tmp_path / "decomposition.json").write_text(json.dumps({
        "version": 1, "module": "m",
        "surfaces": [{"name": "top", "paths": ["docs/*.md"], "on": "write", "entry": "process"}],
    }), encoding="utf-8")
    defn = d.load(tmp_path)
    assert d.match_path(defn, "docs/a.md", "write") == {"top"}
    assert d.match_path(defn, "docs/sub/a.md", "write") == set()


def test_touches_file_tools(repo, source_dir):
    defn = d.load(repo)
    path = str(source_dir / "a.py")
    assert d.touches(defn, "Read", {"file_path": path}) == {"source": [path]}
    assert d.touches(defn, "Grep", {"pattern": "x", "path": str(source_dir)}) == {"source": [str(source_dir)]}
    assert d.touches(defn, "Edit", {"file_path": str(repo / "CHARTER.md")}) == {"identity": [str(repo / "CHARTER.md")]}
    assert d.touches(defn, "Read", {"file_path": str(repo / "CHARTER.md")}) == {}
    assert d.touches(defn, "Grep", {"pattern": "x"}) == {}


def test_touches_shell_needs_path_segment(repo):
    defn = d.load(repo)
    hit = d.touches(defn, "Bash", {"command": "ls /c/Users/Liz/PROVES_LIBRARY/supabase"})
    assert list(hit) == ["source"] and hit["source"][0].startswith("$ ")
    assert d.touches(defn, "PowerShell", {"command": 'Get-ChildItem "C:\\Users\\Liz\\proves-curation-dashboard"'}) != {}
    # mentioned inside a search pattern, not as a path: not a touch
    assert d.touches(defn, "Bash", {"command": 'grep "proves-curation-dashboard|2687a35" notes.md'}) == {}
    # shell never counts as writing a write-only surface
    assert d.touches(defn, "Bash", {"command": "sed -i s/a/b/ CHARTER.md"}) == {}


def test_source_root(repo, source_dir):
    defn = d.load(repo)
    root = d.source_root(defn, str(source_dir / "supabase" / "x.sql"))
    assert d.norm(root) == d.norm(str(source_dir))
    assert d.source_root(defn, str(repo / "CHARTER.md")) is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest plugins/lens-log/tests/test_definition.py -v`
Expected: FAIL / errors with `ModuleNotFoundError: No module named 'lenslog'`.

- [ ] **Step 3: Implement**

`plugins/lens-log/scripts/lenslog/__init__.py`:

```python
"""lens-log: enforce file-based logging of decomposition work."""
```

`plugins/lens-log/scripts/lenslog/definition.py`:

```python
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

_BEFORE = r"(?:^|[\s/\\\"'=])"
_AFTER = r"(?=$|[\s/\\\"'])"


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
                if m and re.search(_BEFORE + re.escape(m) + _AFTER, cmdn):
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest plugins/lens-log/tests/test_definition.py -v`
Expected: all PASS (the Windows test is skipped on non-Windows).

- [ ] **Step 5: Commit**

```bash
git add plugins/lens-log/scripts/lenslog plugins/lens-log/tests/conftest.py plugins/lens-log/tests/test_definition.py
git commit -m "lens-log: load decomposition.json and match touched paths to surfaces

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 2: Session state and entry files

**Files:**
- Create: `plugins/lens-log/scripts/lenslog/state.py`
- Create: `plugins/lens-log/scripts/lenslog/entries.py`
- Test: `plugins/lens-log/tests/test_state_entries.py`

**Interfaces:**
- Consumes: nothing from Task 1 except the `state_dir` / `repo` fixtures.
- Produces:
  - `state.record(session_id: str, hits: dict[str, list[str]], entries_now: list[str]) -> None`
  - `state.pending(session_id: str) -> dict[str, list[str]]` (deduplicated, ≤10 evidence each)
  - `state.meta(session_id: str) -> dict | None` — keys `entries_before: list[str]`, `blocked: bool`
  - `state.set_blocked(session_id: str) -> None`
  - `state.clear(session_id: str) -> None`
  - `entries.ENTRIES_DIR = ("docs","log","entries")`, `entries.MISSED_DIR = ("docs","log","missed")`
  - `entries.list_entries(root: Path) -> list[str]` (sorted `*.md` file names)
  - `entries.front_matter(text: str) -> dict[str, object]` (list values for `[a, b]`)
  - `entries.has_lessons(text: str) -> bool`
  - `entries.coverage(root: Path, names: set[str]) -> tuple[set[str], list[str]]` — (covered surfaces, rejected entry names)
  - `entries.write_missed(root: Path, missing: dict[str, list[str]], session_id: str, now: datetime) -> Path`

- [ ] **Step 1: Write the failing tests**

`plugins/lens-log/tests/test_state_entries.py`:

```python
import json
from datetime import datetime

from lenslog import entries, state

GOOD = """---
type: process
module: lens-core
surfaces: [source, bus]
date: 2026-09-29T10:00
source_commits:
  PROVES_LIBRARY: 02ab37e
---

# Title

## What was done
Read the migrations.

## Lessons
The clone was stale.
"""


def test_state_roundtrip_and_dedupe():
    state.record("s1", {"source": ["a", "b"]}, ["old.md"])
    state.record("s1", {"source": ["a"], "bus": ["x"]}, ["old.md", "new.md"])
    assert state.pending("s1") == {"source": ["a", "b"], "bus": ["x"]}
    assert state.meta("s1") == {"entries_before": ["old.md"], "blocked": False}


def test_state_caps_evidence():
    state.record("s1", {"source": [str(i) for i in range(25)]}, [])
    assert len(state.pending("s1")["source"]) == 10


def test_state_blocked_and_clear():
    state.record("s1", {"source": ["a"]}, [])
    state.set_blocked("s1")
    assert state.meta("s1")["blocked"] is True
    state.clear("s1")
    assert state.pending("s1") == {}
    assert state.meta("s1") is None


def test_state_ignores_corrupt_lines(state_dir):
    state.record("s1", {"source": ["a"]}, [])
    with open(state_dir / "s1.touches.jsonl", "a", encoding="utf-8") as f:
        f.write("{not json\n")
    assert state.pending("s1") == {"source": ["a"]}


def test_state_session_id_is_sanitized(state_dir):
    state.record("../../evil", {"source": ["a"]}, [])
    assert all(p.parent == state_dir for p in state_dir.iterdir())


def test_front_matter():
    fm = entries.front_matter(GOOD)
    assert fm["type"] == "process"
    assert fm["surfaces"] == ["source", "bus"]
    assert "PROVES_LIBRARY" not in fm
    assert entries.front_matter("no header") == {}
    assert entries.front_matter("---\ntype: x\n") == {}


def test_has_lessons():
    assert entries.has_lessons(GOOD)
    assert entries.has_lessons(GOOD.replace("The clone was stale.", "none"))
    template = GOOD.replace("The clone was stale.", "<!-- required: what was learned, or write the word none -->")
    assert not entries.has_lessons(template)
    assert not entries.has_lessons(GOOD.split("## Lessons")[0])


def test_list_and_coverage(repo):
    d = repo.joinpath(*entries.ENTRIES_DIR)
    d.mkdir(parents=True)
    (d / "b.md").write_text(GOOD, encoding="utf-8")
    (d / "a.md").write_text(GOOD.replace("The clone was stale.", ""), encoding="utf-8")
    (d / "notes.txt").write_text("x", encoding="utf-8")
    assert entries.list_entries(repo) == ["a.md", "b.md"]
    covered, rejected = entries.coverage(repo, {"a.md", "b.md", "gone.md"})
    assert covered == {"source", "bus"}
    assert rejected == ["a.md"]


def test_list_entries_missing_dir(repo):
    assert entries.list_entries(repo) == []


def test_write_missed(repo):
    path = entries.write_missed(repo, {"source": ["p"]}, "s1", datetime(2026, 9, 29, 10, 5, 7))
    assert path.parent == repo.joinpath(*entries.MISSED_DIR)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data == {"session_id": "s1", "at": "2026-09-29T10:05:07", "surfaces": {"source": ["p"]}}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest plugins/lens-log/tests/test_state_entries.py -v`
Expected: FAIL with `ImportError: cannot import name 'entries'`.

- [ ] **Step 3: Implement**

`plugins/lens-log/scripts/lenslog/state.py`:

```python
"""Per-session record of surfaces touched since the last satisfied log check.

Touches are appended one JSON line at a time, so parallel subagents do not overwrite
each other. Lives outside the repo: ~/.claude/cache/lens-log/ (or LENS_LOG_STATE_DIR).
"""
from __future__ import annotations

import json
import os
import re
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
        _write_meta(session_id, {"entries_before": list(entries_now), "blocked": False})
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
```

`plugins/lens-log/scripts/lenslog/entries.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest plugins/lens-log/tests -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/lens-log/scripts/lenslog/state.py plugins/lens-log/scripts/lenslog/entries.py plugins/lens-log/tests/test_state_entries.py
git commit -m "lens-log: per-session touch record and log entry parsing

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 3: Entry helper CLI

**Files:**
- Create: `plugins/lens-log/scripts/new_entry.py`
- Test: `plugins/lens-log/tests/test_new_entry.py`

**Interfaces:**
- Consumes: `definition.find_root`, `definition.load`, `definition.ENTRY_TYPES`, `Definition.surfaces`; `entries.ENTRIES_DIR`.
- Produces:
  - `new_entry.source_commit(path: str) -> str` (short SHA or `"unknown"`)
  - `new_entry.render(defn, entry_type: str, surfaces: list[str], title: str, commits: dict[str, str], now: datetime) -> str`
  - `new_entry.main(argv: list[str] | None = None, now: datetime | None = None) -> int` — prints the created path; exit 2 on bad input.
  - CLI: `python new_entry.py --type T --surfaces a,b --slug s [--title "..."] [--source PATH ...] [--root PATH]`

- [ ] **Step 1: Write the failing tests**

`plugins/lens-log/tests/test_new_entry.py`:

```python
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import new_entry  # noqa: E402
from lenslog import entries  # noqa: E402

NOW = datetime(2026, 9, 29, 14, 5)


def _git_repo(path: Path) -> str:
    path.mkdir(parents=True, exist_ok=True)
    run = lambda *a: subprocess.run(["git", "-C", str(path), *a], check=True, capture_output=True)  # noqa: E731
    run("init", "-q")
    (path / "f.txt").write_text("x", encoding="utf-8")
    run("add", "f.txt")
    run("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "init")
    return subprocess.run(["git", "-C", str(path), "rev-parse", "--short", "HEAD"],
                          check=True, capture_output=True, text=True).stdout.strip()


def test_creates_entry_with_commits(repo, tmp_path, capsys):
    src = tmp_path / "elsewhere" / "PROVES_LIBRARY"
    sha = _git_repo(src)
    code = new_entry.main(["--type", "process", "--surfaces", "source", "--slug", "dash-reinventory",
                           "--title", "Re-derive dashboard inventory", "--source", str(src),
                           "--root", str(repo)], now=NOW)
    assert code == 0
    path = repo.joinpath(*entries.ENTRIES_DIR, "2026-09-29-1405-dash-reinventory.md")
    assert capsys.readouterr().out.strip() == str(path)
    text = path.read_text(encoding="utf-8")
    fm = entries.front_matter(text)
    assert fm["type"] == "process" and fm["module"] == "lens-core" and fm["surfaces"] == ["source"]
    assert f"  PROVES_LIBRARY: {sha}" in text
    assert "# Re-derive dashboard inventory" in text
    assert not entries.has_lessons(text)  # template must be filled in by the agent


def test_name_collision_gets_suffix(repo):
    args = ["--type", "lesson", "--surfaces", "", "--slug", "x", "--root", str(repo)]
    assert new_entry.main(args, now=NOW) == 0
    assert new_entry.main(args, now=NOW) == 0
    assert entries.list_entries(repo) == ["2026-09-29-1405-x-2.md", "2026-09-29-1405-x.md"]


def test_no_sources_writes_empty_map(repo):
    new_entry.main(["--type", "decision", "--surfaces", "identity", "--slug", "c", "--root", str(repo)], now=NOW)
    text = repo.joinpath(*entries.ENTRIES_DIR, "2026-09-29-1405-c.md").read_text(encoding="utf-8")
    assert "source_commits: {}" in text


@pytest.mark.parametrize("args", [
    ["--type", "nope", "--surfaces", "source", "--slug", "a"],
    ["--type", "process", "--surfaces", "unknown", "--slug", "a"],
    ["--type", "process", "--surfaces", "source", "--slug", "Bad Slug"],
])
def test_rejects_bad_input(repo, args, capsys):
    assert new_entry.main([*args, "--root", str(repo)], now=NOW) == 2
    assert "lens-log" in capsys.readouterr().err


def test_source_commit_unknown_for_non_repo(tmp_path):
    assert new_entry.source_commit(str(tmp_path / "missing")) == "unknown"


def test_source_commit_ignores_enclosing_repo(tmp_path):
    outer = tmp_path / "outer"
    _git_repo(outer)
    inner = outer / "PROVES_LIBRARY"
    inner.mkdir()
    assert new_entry.source_commit(str(inner)) == "unknown"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest plugins/lens-log/tests/test_new_entry.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'new_entry'`.

- [ ] **Step 3: Implement**

`plugins/lens-log/scripts/new_entry.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest plugins/lens-log/tests -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/lens-log/scripts/new_entry.py plugins/lens-log/tests/test_new_entry.py
git commit -m "lens-log: entry helper fills header and source commits

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 4: PostToolUse hook — record touches

**Files:**
- Create: `plugins/lens-log/scripts/record_touch.py`
- Test: `plugins/lens-log/tests/test_record_touch.py`

**Interfaces:**
- Consumes: `definition.find_root/load/touches/DefinitionError`, `entries.list_entries`, `state.record`.
- Produces: `record_touch.handle(data: dict) -> None`; `record_touch.main() -> int` (reads stdin JSON, always returns 0).

- [ ] **Step 1: Write the failing tests**

`plugins/lens-log/tests/test_record_touch.py`:

```python
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import record_touch  # noqa: E402
from lenslog import state  # noqa: E402


def event(repo, tool, tool_input, **extra):
    return {"session_id": "s1", "cwd": str(repo), "hook_event_name": "PostToolUse",
            "tool_name": tool, "tool_input": tool_input, **extra}


def test_records_source_read(repo, source_dir):
    path = str(source_dir / "a.py")
    record_touch.handle(event(repo, "Read", {"file_path": path}))
    assert state.pending("s1") == {"source": [path]}


def test_records_subagent_calls_too(repo, source_dir):
    path = str(source_dir / "b.py")
    record_touch.handle(event(repo, "Grep", {"pattern": "x", "path": path}, agent_id="a1", agent_type="Explore"))
    assert state.pending("s1") == {"source": [path]}


def test_ignores_unrelated(repo):
    record_touch.handle(event(repo, "Read", {"file_path": str(repo / "README.md")}))
    assert state.pending("s1") == {}
    assert state.meta("s1") is None


def test_no_definition_does_nothing(tmp_path):
    record_touch.handle({"session_id": "s1", "cwd": str(tmp_path), "tool_name": "Write",
                         "tool_input": {"file_path": str(tmp_path / "CHARTER.md")}})
    assert state.pending("s1") == {}


def test_main_survives_bad_input(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO("{not json"))
    assert record_touch.main() == 0


def test_main_survives_bad_definition(tmp_path, monkeypatch, capsys):
    (tmp_path / "decomposition.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(sys, "stdin", io.StringIO(
        '{"session_id": "s1", "cwd": "%s", "tool_name": "Read", "tool_input": {}}' % str(tmp_path).replace("\\", "/")))
    assert record_touch.main() == 0
    assert "lens-log" in capsys.readouterr().err
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest plugins/lens-log/tests/test_record_touch.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'record_touch'`.

- [ ] **Step 3: Implement**

`plugins/lens-log/scripts/record_touch.py`:

```python
#!/usr/bin/env python3
"""PostToolUse hook: remember which declared decomposition surfaces a tool call touched.

Fires for the main agent and for subagents. Never blocks, never fails the call.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lenslog import definition, entries, state  # noqa: E402


def handle(data: dict) -> None:
    root = definition.find_root(Path(data.get("cwd") or "."))
    if root is None:
        return
    try:
        defn = definition.load(root)
    except definition.DefinitionError as e:
        print(f"[lens-log] {e}", file=sys.stderr)
        return
    hits = definition.touches(defn, data.get("tool_name", ""), data.get("tool_input") or {})
    if hits:
        state.record(data.get("session_id", ""), hits, entries.list_entries(root))


def main() -> int:
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return 0
    try:
        handle(data)
    except Exception as e:  # noqa: BLE001 — a hook must never break the session
        print(f"[lens-log] record_touch error: {e!r}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest plugins/lens-log/tests -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/lens-log/scripts/record_touch.py plugins/lens-log/tests/test_record_touch.py
git commit -m "lens-log: PostToolUse hook records surface touches (incl. subagents)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 5: Stop hook — enforce the entry

**Files:**
- Create: `plugins/lens-log/scripts/stop_check.py`
- Test: `plugins/lens-log/tests/test_stop_check.py`

**Interfaces:**
- Consumes: `definition.*` (incl. `WRITE_TOOLS`, `source_root`, `Definition.surface`), `entries.list_entries/coverage/write_missed/ENTRIES_DIR`, `state.record/pending/meta/set_blocked/clear`.
- Produces: `stop_check.decide(data: dict, now: datetime | None = None) -> dict | None`; `stop_check.block_message(defn, missing: dict[str, list[str]], rejected: list[str]) -> str`; `stop_check.main() -> int`.

- [ ] **Step 1: Write the failing tests**

`plugins/lens-log/tests/test_stop_check.py`:

```python
import io
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import record_touch  # noqa: E402
import stop_check  # noqa: E402
from lenslog import entries, state  # noqa: E402

NOW = datetime(2026, 9, 29, 15, 0, 0)
ENTRY = """---
type: process
module: lens-core
surfaces: [{surfaces}]
date: 2026-09-29T15:00
source_commits: {{}}
---

# t

## What was done
x

## Lessons
{lessons}
"""


def stop(repo, **extra):
    return {"session_id": "s1", "cwd": str(repo), "hook_event_name": "Stop",
            "stop_hook_active": False, "turn_number": 3, "tool_calls": [], **extra}


def touch_source(repo, source_dir):
    record_touch.handle({"session_id": "s1", "cwd": str(repo), "tool_name": "Read",
                         "tool_input": {"file_path": str(source_dir / "a.py")}})


def write_entry(repo, name, surfaces="source", lessons="The clone was stale."):
    d = repo.joinpath(*entries.ENTRIES_DIR)
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(ENTRY.format(surfaces=surfaces, lessons=lessons), encoding="utf-8")


def test_nothing_touched_allows(repo):
    assert stop_check.decide(stop(repo), NOW) is None


def test_no_definition_is_silent(tmp_path):
    assert stop_check.decide(stop(tmp_path), NOW) is None


def test_invalid_definition_warns_not_blocks(tmp_path):
    (tmp_path / "decomposition.json").write_text("{}", encoding="utf-8")
    out = stop_check.decide(stop(tmp_path), NOW)
    assert "decision" not in out
    assert "decomposition.json" in out["hookSpecificOutput"]["additionalContext"]


def test_touch_without_entry_blocks_with_command(repo, source_dir):
    touch_source(repo, source_dir)
    out = stop_check.decide(stop(repo), NOW)
    assert out["decision"] == "block"
    reason = out["reason"]
    assert "source (needs a process entry)" in reason
    assert "new_entry.py" in reason and "--type process --surfaces source" in reason
    assert "--source" in reason and "PROVES_LIBRARY" in reason


def test_entry_covering_surface_allows_and_clears(repo, source_dir):
    touch_source(repo, source_dir)
    write_entry(repo, "2026-09-29-1500-x.md")
    assert stop_check.decide(stop(repo), NOW) is None
    assert state.pending("s1") == {}


def test_entry_existing_before_touch_does_not_count(repo, source_dir):
    write_entry(repo, "2026-09-01-0000-old.md")
    touch_source(repo, source_dir)
    assert stop_check.decide(stop(repo), NOW)["decision"] == "block"


def test_entry_for_other_surface_does_not_count(repo, source_dir):
    touch_source(repo, source_dir)
    write_entry(repo, "2026-09-29-1500-x.md", surfaces="bus")
    assert stop_check.decide(stop(repo), NOW)["decision"] == "block"


def test_template_lessons_not_counted(repo, source_dir):
    touch_source(repo, source_dir)
    write_entry(repo, "2026-09-29-1500-x.md", lessons="<!-- required: what was learned, or write the word none -->")
    out = stop_check.decide(stop(repo), NOW)
    assert out["decision"] == "block"
    assert "2026-09-29-1500-x.md" in out["reason"] and "Lessons" in out["reason"]


def test_second_stop_records_miss_and_allows(repo, source_dir):
    touch_source(repo, source_dir)
    assert stop_check.decide(stop(repo), NOW)["decision"] == "block"
    out = stop_check.decide(stop(repo), NOW)
    assert "decision" not in out
    missed = list(repo.joinpath(*entries.MISSED_DIR).glob("*.json"))
    assert len(missed) == 1
    assert "source" in json.loads(missed[0].read_text(encoding="utf-8"))["surfaces"]
    assert state.pending("s1") == {}
    assert stop_check.decide(stop(repo), NOW) is None  # next turn starts clean


def test_tool_calls_in_stop_input_are_checked(repo):
    calls = [{"tool_name": "Edit", "tool_use_id": "t1", "tool_input": {"file_path": str(repo / "CHARTER.md")}}]
    out = stop_check.decide(stop(repo, tool_calls=calls), NOW)
    assert out["decision"] == "block" and "identity (needs a decision entry)" in out["reason"]


def test_entry_written_this_turn_counts_even_without_snapshot(repo):
    entry_path = repo.joinpath(*entries.ENTRIES_DIR, "2026-09-29-1500-c.md")
    write_entry(repo, entry_path.name, surfaces="identity")
    calls = [
        {"tool_name": "Edit", "tool_use_id": "t1", "tool_input": {"file_path": str(repo / "CHARTER.md")}},
        {"tool_name": "Write", "tool_use_id": "t2", "tool_input": {"file_path": str(entry_path)}},
    ]
    assert stop_check.decide(stop(repo, tool_calls=calls), NOW) is None


def test_subagent_frontmatter_stop_ignored(repo, source_dir):
    touch_source(repo, source_dir)
    assert stop_check.decide(stop(repo, stop_hook_active=True), NOW) is None


def test_main_prints_json_and_exits_zero(repo, source_dir, monkeypatch, capsys):
    touch_source(repo, source_dir)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(stop(repo))))
    assert stop_check.main() == 0
    assert json.loads(capsys.readouterr().out)["decision"] == "block"


def test_main_survives_bad_input(monkeypatch):
    monkeypatch.setattr(sys, "stdin", io.StringIO("nope"))
    assert stop_check.main() == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest plugins/lens-log/tests/test_stop_check.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'stop_check'`.

- [ ] **Step 3: Implement**

`plugins/lens-log/scripts/stop_check.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest plugins/lens-log/tests -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add plugins/lens-log/scripts/stop_check.py plugins/lens-log/tests/test_stop_check.py
git commit -m "lens-log: Stop hook blocks once until an entry covers touched surfaces

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 6: Plugin packaging — manifest, hooks, launcher, skill, marketplace

**Files:**
- Create: `plugins/lens-log/.claude-plugin/plugin.json`
- Create: `plugins/lens-log/hooks/hooks.json`
- Create: `plugins/lens-log/hooks/run-python.mjs` (copied)
- Create: `plugins/lens-log/skills/log-entry/SKILL.md`
- Create: `.claude-plugin/marketplace.json`
- Test: `plugins/lens-log/tests/test_launcher.py`

**Interfaces:**
- Consumes: `record_touch.py`, `stop_check.py` as `scripts/<name>.py`.
- Produces: hook commands `node "${CLAUDE_PLUGIN_ROOT}/hooks/run-python.mjs" record_touch|stop_check`; marketplace `lens` exposing plugin `lens-log`.

- [ ] **Step 1: Write the failing test**

`plugins/lens-log/tests/test_launcher.py`:

```python
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_launcher_runs_stop_check_end_to_end(repo, source_dir, state_dir):
    env = {**os.environ, "CLAUDE_PLUGIN_ROOT": str(PLUGIN), "LENS_LOG_STATE_DIR": str(state_dir)}
    launcher = str(PLUGIN / "hooks" / "run-python.mjs")
    touch = {"session_id": "e2e", "cwd": str(repo), "tool_name": "Read",
             "tool_input": {"file_path": str(source_dir / "a.py")}}
    r1 = subprocess.run(["node", launcher, "record_touch"], input=json.dumps(touch),
                        capture_output=True, text=True, env=env, timeout=60)
    assert r1.returncode == 0, r1.stderr
    stop = {"session_id": "e2e", "cwd": str(repo), "stop_hook_active": False, "tool_calls": []}
    r2 = subprocess.run(["node", launcher, "stop_check"], input=json.dumps(stop),
                        capture_output=True, text=True, env=env, timeout=60)
    assert r2.returncode == 0, r2.stderr
    assert json.loads(r2.stdout)["decision"] == "block"


def test_hooks_json_points_at_existing_scripts():
    hooks = json.loads((PLUGIN / "hooks" / "hooks.json").read_text(encoding="utf-8"))["hooks"]
    assert set(hooks) == {"PostToolUse", "Stop"}
    for groups in hooks.values():
        for group in groups:
            for h in group["hooks"]:
                name = h["command"].rsplit(" ", 1)[-1]
                assert (PLUGIN / "scripts" / f"{name}.py").is_file()


def test_manifests_are_valid():
    plugin = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert plugin["name"] == "lens-log"
    market = json.loads((PLUGIN.parents[1] / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    assert {"name": "lens-log", "source": "./plugins/lens-log"}.items() <= market["plugins"][0].items()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest plugins/lens-log/tests/test_launcher.py -v`
Expected: FAIL with `FileNotFoundError` for `hooks.json`.

- [ ] **Step 3: Create the files**

Copy the Node launcher (it finds Python on Windows and Unix, passes stdin through, runs `scripts/<name>.py`):

```bash
cp ~/.claude/plugins/cache/tapestry/tapestry-discipline/0.1.19/hooks/run-python.mjs plugins/lens-log/hooks/run-python.mjs
```

Then edit its header comment so the script list reads `record_touch, stop_check` and add one line under the title: ` * Copied from tapestry-discipline 0.1.19 (same author); logic unchanged.`

`plugins/lens-log/hooks/hooks.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Read|Grep|Glob|Edit|Write|MultiEdit|NotebookEdit|Bash|PowerShell",
        "hooks": [
          {
            "type": "command",
            "command": "node \"${CLAUDE_PLUGIN_ROOT}/hooks/run-python.mjs\" record_touch",
            "timeout": 10
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "node \"${CLAUDE_PLUGIN_ROOT}/hooks/run-python.mjs\" stop_check",
            "timeout": 15
          }
        ]
      }
    ]
  }
}
```

`plugins/lens-log/.claude-plugin/plugin.json`:

```json
{
  "name": "lens-log",
  "version": "0.1.0",
  "description": "Enforces a file-based log of decomposition work: any turn that touches a surface declared in decomposition.json must leave a log entry.",
  "author": { "name": "Liz Osborn" },
  "license": "Apache-2.0"
}
```

`.claude-plugin/marketplace.json`:

```json
{
  "name": "lens",
  "owner": { "name": "Lizo-RoadTown" },
  "plugins": [
    {
      "name": "lens-log",
      "source": "./plugins/lens-log",
      "description": "Enforced, file-based log of decomposition work for The Lens repos."
    }
  ]
}
```

`plugins/lens-log/skills/log-entry/SKILL.md`:

```markdown
---
name: log-entry
description: How to write a decomposition log entry when the lens-log Stop hook asks for one, or when recording a lesson on your own. Use whenever a turn touched a surface declared in decomposition.json.
---

# Writing a decomposition log entry

The log is the record of the decomposition. Memory may point at it; it does not replace it.

1. Run the exact command the hook gave you (it already names the type, surfaces and
   source folders). It creates `docs/log/entries/<date>-<slug>.md` with the header filled.
2. Fill in the three sections:
   - **What was done** — what you examined or changed, with file paths.
   - **What was found / decided** — the findings or decision, and why. For source work,
     say what the source actually does; cite `file:line`.
   - **Lessons** — what you learned that should change how the work is done, including
     operator corrections. If nothing, write `none`. An empty or template-only Lessons
     section does not count.
3. One entry may cover several surfaces touched in the same turn. Keep it short and factual.

Entry types: `process` (what was done to or learned from the source or module code),
`decision` (a change to the standard, identity, or the decomposition definition),
`skill` (a skill was created or changed), `lesson` (a standalone lesson).

To record a lesson with no surface touched:
`python <plugin>/scripts/new_entry.py --type lesson --surfaces "" --slug <slug> --title "<lesson>"`
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest plugins/lens-log/tests -v`
Expected: all PASS (launcher test skipped only if `node` is missing).

- [ ] **Step 5: Commit**

```bash
git add plugins/lens-log/.claude-plugin plugins/lens-log/hooks plugins/lens-log/skills plugins/lens-log/tests/test_launcher.py .claude-plugin/marketplace.json
git commit -m "lens-log: plugin manifest, hooks, launcher, log-entry skill; lens-core marketplace

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 7: Wire lens-core — its decomposition.json, log folder, settings

**Files:**
- Create: `decomposition.json`
- Create: `docs/log/entries/.gitkeep`
- Modify: `.claude/settings.json`
- Modify: `docs/BUILD.md` (append progress note)
- Test: `plugins/lens-log/tests/test_real_definition.py`

**Interfaces:**
- Consumes: `definition.load`, `definition.match_path`.
- Produces: lens-core's real definition (surfaces `source`, `bus`, `identity`, `definition`, `skills`, `module`).

- [ ] **Step 1: Write the failing test**

`plugins/lens-log/tests/test_real_definition.py`:

```python
from pathlib import Path

from lenslog import definition as d

ROOT = Path(__file__).resolve().parents[3]


def test_lens_core_definition():
    defn = d.load(ROOT)
    assert defn.module == "lens-core"
    m = lambda p, k="write": d.match_path(defn, p, k)  # noqa: E731
    assert m("C:/Users/Liz/PROVES_LIBRARY/supabase/migrations/009_x.sql", "read") == {"source"}
    assert m("C:/Users/Liz/proves-curation-dashboard/src/hooks/useLibrary.ts", "read") == {"source"}
    assert m(str(ROOT / "docs" / "schema" / "spine.sql")) == {"bus"}
    assert m(str(ROOT / "CHARTER.md")) == {"identity"}
    assert m(str(ROOT / "decomposition.json")) == {"definition"}
    assert m(str(ROOT / "skills" / "decomposition" / "SKILL.md")) == {"skills"}
    assert m(str(ROOT / "plugins" / "lens-log" / "skills" / "log-entry" / "SKILL.md")) == {"skills", "module"}
    assert m(str(ROOT / "src" / "lens_core" / "launch.py")) == {"module"}
    assert m(str(ROOT / "README.md")) == set()
    assert m(str(ROOT / "docs" / "log" / "entries" / "x.md")) == set()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest plugins/lens-log/tests/test_real_definition.py -v`
Expected: FAIL with `DefinitionError: cannot read decomposition.json`.

- [ ] **Step 3: Create and modify the files**

`decomposition.json`:

```json
{
  "version": 1,
  "role": "whole",
  "module": "lens-core",
  "sources": [
    {"name": "PROVES_LIBRARY", "repo": "Lizo-RoadTown/PROVES_LIBRARY",
     "match": ["**/PROVES_LIBRARY/**"]},
    {"name": "proves-curation-dashboard", "repo": "Lizo-RoadTown/proves-curation-dashboard",
     "match": ["**/proves-curation-dashboard/**"]}
  ],
  "modules": ["lens-core", "lens-ingest", "lens-review", "lens-serve", "lens-observe"],
  "bus": {"owner": "lens-core", "paths": ["docs/schema/**"]},
  "surfaces": [
    {"name": "source", "paths": ["@sources"], "on": "read-or-write", "entry": "process"},
    {"name": "bus", "paths": ["docs/schema/**"], "on": "write", "entry": "decision"},
    {"name": "identity", "paths": ["CHARTER.md", "CLAUDE.md", "docs/BUILD.md"], "on": "write", "entry": "decision"},
    {"name": "definition", "paths": ["decomposition.json"], "on": "write", "entry": "decision"},
    {"name": "skills", "paths": ["skills/**", "SKILLS.md", "plugins/**/skills/**"], "on": "write", "entry": "skill"},
    {"name": "module", "paths": ["src/**", "plugins/**"], "on": "write", "entry": "process"}
  ]
}
```

`docs/log/entries/.gitkeep`: empty file.

`.claude/settings.json` (full new content; keeps the two existing plugins):

```json
{
  "extraKnownMarketplaces": {
    "lens": {
      "source": { "source": "github", "repo": "Lizo-RoadTown/lens-core" }
    }
  },
  "enabledPlugins": {
    "tapestry-discipline@tapestry": true,
    "tapestry-patterns@tapestry": true,
    "lens-log@lens": true
  }
}
```

Append to `docs/BUILD.md`:

```markdown

### 2026-09-29 — lens-log built (step 1)
`plugins/lens-log/` implements the PostToolUse + Stop hooks, the entry helper and the
`log-entry` skill; lens-core now has its own `decomposition.json` and `docs/log/entries/`.
Enforcement starts once the plugin is installed from the `lens` marketplace (see
`plugins/lens-log/PLAN.md` Task 8).
```

- [ ] **Step 4: Run the full suite**

Run: `python -m pytest plugins/lens-log/tests -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add decomposition.json docs/log/entries/.gitkeep .claude/settings.json docs/BUILD.md plugins/lens-log/tests/test_real_definition.py
git commit -m "Wire lens-core into lens-log: decomposition.json, log folder, plugin enabled

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 8: Install and verify live (operator + agent)

No code. This proves the hooks fire in a real Claude Code session.

- [ ] **Step 1: Operator approves the push.** `git push origin main` (the marketplace is read from GitHub). Do not push without the operator's go-ahead.
- [ ] **Step 2: Check the settings format** against <https://code.claude.com/docs/en/plugin-marketplaces.md> and <https://code.claude.com/docs/en/settings.md> (`extraKnownMarketplaces`, `enabledPlugins`). Fix `.claude/settings.json` if the docs differ; commit.
- [ ] **Step 3: Operator installs** in the lens-core window: `/plugin marketplace add Lizo-RoadTown/lens-core`, then `/plugin install lens-log@lens`, then reload the window.
- [ ] **Step 4: Live check.** In a new turn, read one file under the PROVES dashboard (e.g. `src/hooks/useLibrary.ts`) and finish the turn. Expected: the Stop hook blocks with the `[lens-log]` message and a ready `new_entry.py` command.
- [ ] **Step 5: Write the first real entry** with that command, fill all three sections, finish the turn. Expected: the turn ends normally. Commit the entry.
- [ ] **Step 6: Subagent check.** Ask an Explore subagent to read one PROVES file; finish the turn. Expected: the block names that file. Write the entry; commit.
- [ ] **Step 7: Record** the result in `docs/BUILD.md` (and a loom-memory pointer), including anything the docs check in Step 2 changed.
