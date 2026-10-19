"""PRAVAHA_CALL_TIMEOUT_S and PRAVAHA_VERIFY_BUDGET_S (incident 2026-10-19: a loaded machine made
`gh pr list` take ~7.4 s against a hard-coded 5 s, so the gh source timed out on every tick)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from pravaha_tracker import detectors as D
from pravaha_tracker import server as S

PKG_PARENT = str(Path(__file__).resolve().parents[2])


def read_module_settings(**env) -> dict:
    """Import detectors in a fresh interpreter (the settings are read at import) and report them."""
    base = {k: v for k, v in os.environ.items() if not k.startswith("PRAVAHA_")}
    code = ("import sys, json; sys.path.insert(0, sys.argv[1]); from pravaha_tracker import detectors as D; "
            "print(json.dumps([D.CALL_TIMEOUT_S, D.VERIFY_BUDGET_S, D.Config('r', None, 'h').verify_budget_s, D.CONFIG_NOTES]))")
    out = subprocess.run([sys.executable, "-I", "-c", code, PKG_PARENT], env={**base, **env},
                         capture_output=True, text=True, timeout=60, check=True).stdout
    call, budget, cfg_budget, notes = json.loads(out)
    return dict(call=call, budget=budget, cfg_budget=cfg_budget, notes=notes)


def test_defaults_unchanged():
    got = read_module_settings()
    assert (got["call"], got["budget"], got["cfg_budget"], got["notes"]) == (5.0, 20.0, 20.0, [])


def test_env_override_honoured():
    got = read_module_settings(PRAVAHA_CALL_TIMEOUT_S="20", PRAVAHA_VERIFY_BUDGET_S="45")
    assert (got["call"], got["budget"], got["cfg_budget"], got["notes"]) == (20.0, 45.0, 45.0, [])


@pytest.mark.parametrize("bad", ["abc", "0", "-3", "120.5", "1e9", "nan", "inf", "5s"])
def test_invalid_value_falls_back_with_a_health_note(bad):
    got = read_module_settings(PRAVAHA_CALL_TIMEOUT_S=bad, PRAVAHA_VERIFY_BUDGET_S=bad)
    assert (got["call"], got["budget"]) == (5.0, 20.0)
    assert len(got["notes"]) == 2 and all("rejected" in n for n in got["notes"])
    assert "PRAVAHA_CALL_TIMEOUT_S" in got["notes"][0] and "PRAVAHA_VERIFY_BUDGET_S" in got["notes"][1]


def test_upper_bound_120_is_accepted():
    assert read_module_settings(PRAVAHA_CALL_TIMEOUT_S="120")["call"] == 120.0


def test_live_verification_deadline_follows_configured_budget(tmp_path):
    """A budget above the old fixed 20 s cap reaches the detector's subprocess deadline."""
    det = D.Detectors(D.Config(repo=str(tmp_path), pgenv=None, home=str(tmp_path), verify_budget_s=45.0))
    det.d_probe = lambda spec: D.DetectorResult("done", str(D._remaining()), D.now_iso(), "detector:probe")
    try:
        remaining = float(det.verify({"type": "probe"}).detail)
    finally:
        det._pool.shutdown(wait=True)
    assert 40 < remaining <= 45


def test_timed_out_call_stays_visible_in_source_health(tmp_path):
    """Earned signal: a call cut off by the (configured) timeout marks its source stale, unmeasured."""
    monitor = D.SourceMonitor()
    with patch.object(D, "CALL_TIMEOUT_S", 0.3), D.external_context(monitor):
        with pytest.raises(subprocess.TimeoutExpired):
            D._run(["sleep", "30"])
    row = monitor.snapshot()["sleep"]
    assert row["stale"] is True and row["error"] == "timed out" and row["age_s"] is None


def test_rejected_setting_is_served_in_health(tmp_path):
    cfg = dict(home=str(tmp_path), events=str(tmp_path / "EVENTS.jsonl"), snapshot=str(tmp_path / "snapshot.json"),
               backup_dir=str(tmp_path / "backup"), hold=str(tmp_path / "HOLD"), model=str(tmp_path / "model.json"),
               repo=str(tmp_path), pgenv=None, db_port=1, detectors_enabled=False, git_every_s=3600,
               backup_every_s=3600, tick_budget_s=8)
    (tmp_path / "model.json").write_text(json.dumps({"campaign": "x", "tracks": [], "items": [], "streams": [],
                                                      "decisions": [], "phases": []}))
    eng = S.Engine(cfg)
    try:
        with patch.object(D, "port_open", return_value=False), \
             patch.object(D, "CONFIG_NOTES", ["PRAVAHA_CALL_TIMEOUT_S='abc' rejected"]):
            eng.tick()
            health = eng.health()
        assert health["config_notes"] == ["PRAVAHA_CALL_TIMEOUT_S='abc' rejected"]
        assert health["call_timeout_s"] == D.CALL_TIMEOUT_S and health["verify_budget_s"] == 20.0
    finally:
        eng.stop()
        eng.det._pool.shutdown(wait=True)
