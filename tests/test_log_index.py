import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import log_index  # noqa: E402

SOURCES = [{"name": "SRC", "repo": "o/SRC", "match": ["**/SRC/**"]}]

ENTRY = """---
type: {type}
module: {module}
surfaces: [{surfaces}]
date: {date}
---

# {title}

## Lessons
x
"""


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                   env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                        "GIT_COMMITTER_EMAIL": "t@t", "PATH": __import__("os").environ["PATH"],
                        "SYSTEMROOT": __import__("os").environ.get("SYSTEMROOT", "")})


def make_repo(base, name, defn):
    r = base / name
    r.mkdir()
    git(r, "init", "-q", "-b", "main")
    (r / "decomposition.json").write_text(json.dumps(defn), encoding="utf-8")
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", "init")
    return r


def add_entry(repo, fname, commit=True, **kw):
    d = repo / "docs" / "log" / "entries"
    d.mkdir(parents=True, exist_ok=True)
    fields = dict(type="process", module=repo.name, surfaces="module", date="2026-10-21T10:00",
                  title="Did a thing")
    fields.update(kw)
    (d / fname).write_text(ENTRY.format(**fields), encoding="utf-8")
    if commit:
        git(repo, "add", "-A")
        git(repo, "commit", "-q", "-m", f"entry {fname}")


@pytest.fixture
def fleet(tmp_path):
    whole = {"version": 1, "role": "whole", "module": "core", "sources": SOURCES,
             "modules": ["core", "ingest"], "proposed": ["future thing"],
             "surfaces": [{"name": "module", "paths": ["src/**"], "on": "write", "entry": "process"}]}
    piece = {"version": 1, "role": "piece", "module": "ingest", "sources": SOURCES,
             "surfaces": [{"name": "module", "paths": ["src/**"], "on": "write", "entry": "process"},
                          {"name": "source", "paths": ["@sources"], "on": "read-or-write",
                           "entry": "process"}]}
    core = make_repo(tmp_path, "core", whole)
    ingest = make_repo(tmp_path, "ingest", piece)
    return tmp_path, core, ingest


def test_collects_entries_from_every_existing_module(fleet):
    base, core, ingest = fleet
    add_entry(core, "2026-10-21-1000-a.md", title="Core thing")
    add_entry(ingest, "2026-10-21-1100-b.md", type="decision", title="Ingest thing")
    idx = log_index.build(core, base)
    titles = [(e["module"], e["title"], e["type"]) for e in idx["entries"]]
    assert titles == [("ingest", "Ingest thing", "decision"), ("core", "Core thing", "process")]
    assert set(idx["commits"]) == {"core", "ingest"}
    assert "future thing" in idx["not_created"]


def test_missing_repo_is_reported_not_fatal(fleet):
    base, core, ingest = fleet
    ingest.rename(base / "moved-away")
    idx = log_index.build(core, base)
    assert any("ingest" in p for p in idx["problems"])


def test_consistency_flags_piece_disagreeing_with_whole(fleet):
    base, core, ingest = fleet
    bad = json.loads((ingest / "decomposition.json").read_text(encoding="utf-8"))
    bad["sources"] = [{"name": "OTHER", "repo": "o/OTHER", "match": ["**/OTHER/**"]}]
    bad["role"] = "whole"
    (ingest / "decomposition.json").write_text(json.dumps(bad), encoding="utf-8")
    problems = log_index.build(core, base)["problems"]
    assert any("role" in p for p in problems)
    assert any("OTHER" in p for p in problems)


def test_consistency_flags_module_name_mismatch(fleet):
    base, core, ingest = fleet
    d = json.loads((ingest / "decomposition.json").read_text(encoding="utf-8"))
    d["module"] = "something-else"
    (ingest / "decomposition.json").write_text(json.dumps(d), encoding="utf-8")
    assert any("something-else" in p for p in log_index.build(core, base)["problems"])


def test_audit_flags_surface_commit_without_entry_after_logging_began(fleet):
    base, core, ingest = fleet
    (ingest / "src").mkdir()
    (ingest / "src" / "old.py").write_text("x", encoding="utf-8")
    git(ingest, "add", "-A")
    git(ingest, "commit", "-q", "-m", "before logging began")
    add_entry(ingest, "2026-10-21-1000-first.md")
    (ingest / "src" / "a.py").write_text("x", encoding="utf-8")
    git(ingest, "add", "-A")
    git(ingest, "commit", "-q", "-m", "shell edit without entry")
    (ingest / "src" / "b.py").write_text("x", encoding="utf-8")
    add_entry(ingest, "2026-10-21-1100-second.md", commit=False)
    git(ingest, "add", "-A")
    git(ingest, "commit", "-q", "-m", "edit with entry")
    audit = log_index.build(core, base)["audit"]
    assert [a["subject"] for a in audit] == ["shell edit without entry"]
    assert audit[0]["module"] == "ingest" and "src/a.py" in audit[0]["files"]


def test_misses_are_listed(fleet):
    base, core, ingest = fleet
    d = ingest / "docs" / "log" / "missed"
    d.mkdir(parents=True)
    (d / "2026-10-21-100000.json").write_text(json.dumps({"surfaces": {"module": ["src/x.py"]}}),
                                              encoding="utf-8")
    misses = log_index.build(core, base)["misses"]
    assert misses == [{"module": "ingest", "file": "2026-10-21-100000.json", "surfaces": ["module"]}]


def test_render_has_stamp_tables_and_links(fleet):
    base, core, ingest = fleet
    add_entry(ingest, "2026-10-21-1100-b.md", title="Ingest | thing")
    md = log_index.render(log_index.build(core, base), owner="o")
    assert "generated by scripts/log_index.py" in md
    assert "| ingest |" in md and "Ingest \\| thing" in md
    assert "https://github.com/o/ingest/blob/main/docs/log/entries/2026-10-21-1100-b.md" in md
    assert "## Built from" in md and "## Consistency" in md and "## Audit" in md


def test_main_writes_index_and_exit_code_reflects_problems(fleet, capsys):
    base, core, ingest = fleet
    assert log_index.main(["--root", str(core), "--repos-dir", str(base), "--owner", "o"]) == 0
    assert (core / "docs" / "log" / "INDEX.md").exists()
    d = json.loads((ingest / "decomposition.json").read_text(encoding="utf-8"))
    d["role"] = "whole"
    (ingest / "decomposition.json").write_text(json.dumps(d), encoding="utf-8")
    assert log_index.main(["--root", str(core), "--repos-dir", str(base), "--owner", "o"]) == 1
