"""ga_structural must accept the REAL pyjhora adapter output (TI-l1-writer-fixes-001).

Regression for the S-L1 data-plane rehearsal finding: ``compute_chart()['ascendant']``
carries the longitude under ``longitude_deg`` ONLY, while the completeness validator
added by #2607 (and ``_extract_chart_state`` / the bhava-chalit family) required or
silently defaulted ``ascendant['longitude']``.  The writer's other tests mock the
ascendant dict with a ``longitude`` key and therefore could not see this; every test
here runs the real adapter on a SYNTHETIC chart (not any real native).
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from ga_writers.ga_structural_writer import (
    CANONICAL_AYANAMSHAS,
    _ascendant_longitude,
    _build_bhava_chalit_divergence_rows,
    _extract_chart_state,
    _validate_chart_output_complete,
)
from ga_writers.ga_positions_writer import _build_chalit_rows
from pipeline.orchestrator.writers.bo_laksana import _build_signal_row
from pyjhora_adapter.compute import compute_chart

# Synthetic birth parameters (deliberately NOT the native): Cancer lagna, so a
# defaulted 0-degree ascendant is observably different from the real one.
SYNTHETIC_BP = {
    "datetime_iso": "1991-07-19T06:20:00",
    "latitude_deg": 18.52,
    "longitude_deg": 73.86,
    "tz_offset_hours": 5.5,
    "place_name": "synthetic",
    "subject_label": "syn",
}


@pytest.fixture(scope="module", params=sorted(CANONICAL_AYANAMSHAS.items())[:2], ids=lambda p: p[0])
def real_chart(request):
    canonical_id, adapter_id = request.param
    return canonical_id, compute_chart(inputs=SYNTHETIC_BP, ayanamsha_id=adapter_id)


def _house_fact_conn(rows):
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value.fetchall.return_value = [
        (r["fact_subject"], r["fact_key"], r["fact_value_num"], r["fact_id"])
        for r in rows
        if r["fact_category"] == "house_chalit"
        and r["fact_key"] in ("whole_sign_house", "chalit_house_sripati", "dist_to_nearest_boundary_deg")
    ]
    return conn


def test_real_adapter_ascendant_carries_longitude_deg_only(real_chart):
    """Pins the adapter contract this writer must follow (if it ever adds the alias, this test
    is the signal to simplify the helper -- not a failure of the writer)."""
    _, chart = real_chart
    assert "longitude_deg" in chart["ascendant"]


# The exact key set the REAL adapter emits for the ascendant.  Hand-built fixtures in the writer's other
# tests must carry a subset of these (no invented ``longitude`` key -- that is what hid the defect).
REAL_ASCENDANT_KEYS = frozenset({
    "degree_in_sign", "longitude_deg", "nakshatra", "nakshatra_id", "pada",
    "sign", "sign_id", "sign_lord",
})


def test_real_adapter_ascendant_key_set_is_pinned(real_chart):
    """A new/renamed adapter key must be a conscious change here, next to the validator it feeds."""
    _, chart = real_chart
    assert set(chart["ascendant"]) == REAL_ASCENDANT_KEYS


def test_validator_and_extractor_read_only_keys_the_real_adapter_emits(real_chart):
    """Strip the real ascendant to the keys the writer is entitled to read: still accepted.
    Removing the one longitude key must fail loudly (never default)."""
    _, chart = real_chart
    minimal = {**chart, "ascendant": {k: chart["ascendant"][k] for k in ("sign", "sign_id", "longitude_deg")}}
    _validate_chart_output_complete(minimal)
    assert _extract_chart_state(minimal)["LAGNA"]["longitude"] == pytest.approx(chart["ascendant"]["longitude_deg"])
    broken = {**chart, "ascendant": {k: v for k, v in chart["ascendant"].items() if k != "longitude_deg"}}
    with pytest.raises(RuntimeError, match="ascendant 'longitude_deg' missing"):
        _validate_chart_output_complete(broken)
    with pytest.raises(RuntimeError, match="ascendant 'longitude_deg' missing"):
        _extract_chart_state(broken)


def test_validator_accepts_real_adapter_output(real_chart):
    _, chart = real_chart
    _validate_chart_output_complete(chart)  # raised "ascendant 'longitude' missing" before the fix


def test_chart_state_lagna_uses_the_real_ascendant_longitude(real_chart):
    _, chart = real_chart
    asc_long = chart["ascendant"]["longitude_deg"]
    assert asc_long > 1.0  # Cancer lagna: a defaulted 0.0 would be visibly wrong
    lagna = _extract_chart_state(chart)["LAGNA"]
    assert lagna["longitude"] == pytest.approx(asc_long)
    assert lagna["degree"] == pytest.approx(asc_long % 30.0)


def test_bhava_chalit_uses_sripati_boundaries(real_chart):
    canonical_id, chart = real_chart
    asc_long = chart["ascendant"]["longitude_deg"]
    cusps = chart["bhava_chalit"]["sripati"]["cusps"]
    expected = []
    for graha in chart["grahas"]:
        longitude = graha["longitude"]
        chalit = next(cusp["house"] for cusp in cusps
                      if (longitude - cusp["start"]) % 360 < (cusp["end"] - cusp["start"]) % 360)
        if chalit != graha["house"]:
            expected.append((round(longitude, 4), graha["house"], chalit))
    equal_house_count = sum(int(((g["longitude"] - asc_long) % 360.0) // 30.0) + 1 != g["house"]
                            for g in chart["grahas"])
    assert len(expected) != equal_house_count
    args = (chart, "chart", "build", canonical_id, "2026-01-01T00:00:00+00:00")
    source_rows = _build_chalit_rows(*args)
    rows = _build_bhava_chalit_divergence_rows(_house_fact_conn(source_rows), *args, "test")
    values = [row["fact_value_jsonb"] for row in rows]
    assert [(v["graha_longitude"], v["rasi_house"], v["chalit_house"]) for v in values] == expected
    assert all(v["chalit_method"] == "sripati" for v in values)
    assert all(len(v["constituent_fact_ids"]) == 3 for v in values)
    assert all(row["verification_pass_status"] == "single" for row in rows)
    for fact in rows:
        ids = fact["fact_value_jsonb"]["constituent_fact_ids"]
        signal = _build_signal_row(fact, "chart", "build", {}, {}, {}, args[-1],
                                   valid_fact_ids={fact["fact_id"], *ids})
        configuration = json.loads(signal["configuration_jsonb"])
        assert configuration["chalit_method"] == "sripati"
        assert configuration["chalit_house"] == fact["fact_value_jsonb"]["chalit_house"]
        assert signal["constituent_facts_array"] == [fact["fact_id"], *ids]
        assert signal["verification_pass_status"] == "single"

    with pytest.raises(RuntimeError, match="source facts missing or stale"):
        _build_bhava_chalit_divergence_rows(_house_fact_conn([]), *args, "test")


def test_ascendant_longitude_prefers_l25_key_accepts_alias_and_never_defaults():
    assert _ascendant_longitude({"longitude_deg": 94.5}) == 94.5
    assert _ascendant_longitude({"longitude": 12.0}) == 12.0
    assert _ascendant_longitude({"longitude_deg": 94.5, "longitude": 12.0}) == 94.5
    with pytest.raises(RuntimeError, match="ascendant 'longitude_deg' missing"):
        _ascendant_longitude({"sign": "Aries"})
