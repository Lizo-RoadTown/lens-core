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
