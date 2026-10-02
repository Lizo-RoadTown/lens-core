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


@pytest.mark.parametrize("cmd", [
    'grep -rn "PROVES_LIBRARY" docs/',
    'git commit -m "notes on PROVES_LIBRARY layout"',
    "echo PROVES_LIBRARY",
])
def test_shell_mention_without_path_is_not_a_touch(repo, cmd):
    assert d.touches(d.load(repo), "Bash", {"command": cmd}) == {}


@pytest.mark.parametrize("cmd", [
    r"cd C:\Users\Liz\PROVES_LIBRARY; git log",
    "(cd ../PROVES_LIBRARY&&ls)",
    "cat /c/Users/Liz/PROVES_LIBRARY|head",
    "cd PROVES_LIBRARY",
    "Set-Location 'PROVES_LIBRARY'",
    "git -C PROVES_LIBRARY log -1",
    "ls PROVES_LIBRARY/supabase",
])
def test_shell_path_forms_are_touches(repo, cmd):
    assert list(d.touches(d.load(repo), "PowerShell", {"command": cmd})) == ["source"]
