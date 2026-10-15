"""KYD-118: both legacy routes refuse an unknown target, preserving explicit 0°."""
import pytest
from services.ka_sangam.engine import mode_a_search, mode_b_sweep


@pytest.mark.parametrize("mode", ["A", "B"])
@pytest.mark.parametrize("target", ["absent", None, 0.0])
def test_missing_target_never_scans_and_explicit_zero_is_passed(mode, target, monkeypatch):
    calls = []
    def scan(**kwargs):
        calls.append(kwargs["target_longitude_deg"])
        return []
    monkeypatch.setattr("pipeline.transit_search.find_aspect_events", scan)
    monkeypatch.setattr("pipeline.transit_search.search_long_horizon", scan)
    trig = {"transit_planet": "Jupiter"}
    if target != "absent":
        trig["target_longitude_deg"] = target
    predicate = {"signature_class": "YOGA", "transit_trigger_jsonb": trig,
                 "dasha_eligibility_rule_jsonb": {"constituent_lords": ["Jupiter"]}}
    if mode == "A":
        result = mode_a_search(predicate, 2451545, 2451550, None, None, None, "CODEX-fixture", 0)
    else:
        result = mode_b_sweep("fixture", predicate, 2451545, 2451550, None, 0)
    assert result == []
    assert calls == ([0.0] if target == 0.0 else [])
