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
