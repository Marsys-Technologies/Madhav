"""K7-B2: execute immutable 849/1377 SQL and dispatch their stored JSONB.

Collected by the mandatory Kāla DB CI job, with guarded throwaway DB cleanup.
No historical composite or confidence label is promoted to a current axis.
"""
from pathlib import Path
from unittest.mock import Mock

import psycopg
import pytest

from pipeline.orchestrator.service_probes import run_health_probe
from services.ka_tulana.ranker import KaTulanaService

PLATFORM = Path(__file__).resolve().parents[4]
MIGRATIONS = (
    "849_nirmana_l3_w3_tulana_health_probe.sql",
    "1377_k7_4_tulana_pareto_health_probe.sql",
)


@pytest.fixture(params=[0, 1], ids=["before-1377", "after-1377"])
def stored_probe(kala_db_dsn, request):
    with psycopg.connect(kala_db_dsn) as conn:
        conn.execute("CREATE TEMP TABLE asset_registry (asset_id text PRIMARY KEY, health_probe jsonb)")
        conn.execute("INSERT INTO asset_registry VALUES ('ka_tulana', NULL), ('other', '{\"untouched\": true}')")
        for migration in MIGRATIONS[:request.param + 1]:
            sql = (PLATFORM / "migrations" / migration).read_text()
            conn.execute(sql)
            first = conn.execute("SELECT health_probe FROM asset_registry WHERE asset_id = 'ka_tulana'").fetchone()[0]
            conn.execute(sql)
            assert conn.execute("SELECT health_probe FROM asset_registry WHERE asset_id = 'ka_tulana'").fetchone()[0] == first
        assert conn.execute("SELECT health_probe FROM asset_registry WHERE asset_id = 'other'").fetchone()[0] == {"untouched": True}
        yield first
        conn.rollback()


def test_stored_contract_dispatch_executes_real_detectors(stored_probe, monkeypatch):
    method = KaTulanaService.compare_windows
    calls = Mock(wraps=method)
    monkeypatch.setattr(KaTulanaService, "compare_windows", lambda *a, **kw: calls(*a, **kw))
    result = run_health_probe("ka_tulana", stored_probe)
    assert result["status"] == "GREEN", result
    assert calls.call_count == 2, "validation alone cannot earn GREEN"
    assert result["stored_contract_version"] == stored_probe.get("contract_version", "849:unversioned")
    measured = {c["check"]: c["passed"] for c in result["checks"]}
    assert measured["forensic_front_and_order"] and measured["forensic_compare_verdict"]
    if "contract_version" not in stored_probe:
        assert result["retired_expectations_measured"] is False
        assert "compatibility" in result["scope"]
        for call in calls.call_args_list:
            windows = call.args[1] if len(call.args) > 1 else call.kwargs["windows"]
            for window in windows:
                data = window if isinstance(window, dict) else window.model_dump()
                assert data.get("jury") is None
                assert data.get("confidence_tier") is None


@pytest.mark.parametrize("corruption", ["relation", "axis", "raise"])
def test_stored_contract_cannot_green_a_broken_detector(stored_probe, monkeypatch, corruption):
    original = KaTulanaService.compare_windows
    def broken(*args, **kwargs):
        if corruption == "raise":
            raise RuntimeError("detector unavailable")
        result = original(*args, **kwargs)
        pair = result["comparisons"][0]
        if corruption == "relation":
            pair["relation"] = "tie"
        else:
            pair["axes"]["nearest"]["relation"] = "tie"
        return result
    monkeypatch.setattr(KaTulanaService, "compare_windows", broken)
    result = run_health_probe("ka_tulana", stored_probe)
    assert result["status"] != "GREEN"
    failed = {c["check"] for c in result["checks"] if not c["passed"]}
    assert {"forensic_front_and_order", "forensic_compare_verdict"} <= failed


@pytest.mark.parametrize("version", [None, "", "unknown:future"])
def test_explicit_bad_version_never_falls_back_to_849(stored_probe, version):
    result = run_health_probe("ka_tulana", dict(stored_probe, contract_version=version))
    assert result["status"] != "GREEN"
    assert any(c["check"] == "probe_config_valid" and not c["passed"] for c in result["checks"])
