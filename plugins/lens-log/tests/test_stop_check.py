import io
import json
import sys
import time
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
            "stop_hook_active": False, "last_assistant_message": "done",
            "background_tasks": [], "session_crons": [], **extra}


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
    # systemMessage warns the operator without continuing the turn;
    # additionalContext on Stop would continue it (hooks.md:2614)
    assert set(out) == {"systemMessage"}
    assert "decomposition.json" in out["systemMessage"]


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
    # the continuation after our block arrives with stop_hook_active=true (hooks.md:2535)
    out = stop_check.decide(stop(repo, stop_hook_active=True), NOW)
    assert set(out) == {"systemMessage"}
    missed = list(repo.joinpath(*entries.MISSED_DIR).glob("*.json"))
    assert len(missed) == 1
    assert "source" in json.loads(missed[0].read_text(encoding="utf-8"))["surfaces"]
    assert state.pending("s1") == {}
    assert stop_check.decide(stop(repo), NOW) is None  # next turn starts clean


def test_next_turn_touches_get_their_own_block(repo, source_dir):
    touch_source(repo, source_dir)
    stop_check.decide(stop(repo), NOW)
    stop_check.decide(stop(repo, stop_hook_active=True), NOW)
    record_touch.handle({"session_id": "s1", "cwd": str(repo), "tool_name": "Edit",
                         "tool_input": {"file_path": str(repo / "CHARTER.md")}})
    out = stop_check.decide(stop(repo), NOW)
    assert out["decision"] == "block" and "identity (needs a decision entry)" in out["reason"]


def test_first_block_not_skipped_when_another_hook_continued(repo, source_dir):
    touch_source(repo, source_dir)
    assert stop_check.decide(stop(repo, stop_hook_active=True), NOW)["decision"] == "block"


def test_entry_filled_in_after_first_touch_counts(repo, source_dir):
    # created (e.g. by the helper) before the touch, Lessons filled in afterwards
    write_entry(repo, "2026-09-29-1500-x.md", lessons="<!-- required -->")
    touch_source(repo, source_dir)
    time.sleep(0.05)
    write_entry(repo, "2026-09-29-1500-x.md", lessons="The clone was stale.")
    assert stop_check.decide(stop(repo), NOW) is None


def test_block_without_local_source_path_asks_for_it(repo):
    record_touch.handle({"session_id": "s1", "cwd": str(repo), "tool_name": "Bash",
                         "tool_input": {"command": "git -C ../PROVES_LIBRARY log -1"}})
    reason = stop_check.decide(stop(repo), NOW)["reason"]
    assert '--source "<local folder of each source repo read>"' in reason


def test_main_prints_json_and_exits_zero(repo, source_dir, monkeypatch, capsys):
    touch_source(repo, source_dir)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(stop(repo))))
    assert stop_check.main() == 0
    assert json.loads(capsys.readouterr().out)["decision"] == "block"


def test_main_survives_bad_input(monkeypatch):
    monkeypatch.setattr(sys, "stdin", io.StringIO("nope"))
    assert stop_check.main() == 0
