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


def test_listed_in_lizo_skills_only_and_enabled_per_project():
    root = PLUGIN.parents[1]
    # one listing only: the lizo-skills marketplace points here with git-subdir
    assert not (root / ".claude-plugin" / "marketplace.json").exists()
    settings = json.loads((root / ".claude" / "settings.json").read_text(encoding="utf-8"))
    assert settings["enabledPlugins"]["lens-log@lizo-skills"] is True
    market = settings["extraKnownMarketplaces"]["lizo-skills"]["source"]
    assert market == {"source": "github", "repo": "Lizo-RoadTown/claude-skills-marketplace"}
