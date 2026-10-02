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
    meta = state.meta("s1")
    assert meta["entries_before"] == ["old.md"] and meta["blocked"] is False
    assert isinstance(meta["since"], float)


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
