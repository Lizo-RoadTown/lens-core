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
