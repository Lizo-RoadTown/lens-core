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
