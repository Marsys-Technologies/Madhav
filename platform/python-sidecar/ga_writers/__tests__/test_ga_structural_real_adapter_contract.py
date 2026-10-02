"""ga_structural must accept the REAL pyjhora adapter output (TI-l1-writer-fixes-001).

Regression for the S-L1 data-plane rehearsal finding: ``compute_chart()['ascendant']``
carries the longitude under ``longitude_deg`` ONLY, while the completeness validator
added by #2607 (and ``_extract_chart_state`` / the bhava-chalit family) required or
silently defaulted ``ascendant['longitude']``.  The writer's other tests mock the
ascendant dict with a ``longitude`` key and therefore could not see this; every test
here runs the real adapter on a SYNTHETIC chart (not any real native).
"""
from __future__ import annotations

import pytest

from ga_writers.ga_structural_writer import (
    CANONICAL_AYANAMSHAS,
    _ascendant_longitude,
    _build_bhava_chalit_divergence_rows,
    _extract_chart_state,
    _validate_chart_output_complete,
)
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


class _NoDbConn:
    """The bhava-chalit builder's constituent-fact prefetch is best-effort."""

    def cursor(self, *args, **kwargs):
        raise RuntimeError("no db in this unit test")


def test_real_adapter_ascendant_carries_longitude_deg_only(real_chart):
    """Pins the adapter contract this writer must follow (if it ever adds the alias, this test
    is the signal to simplify the helper -- not a failure of the writer)."""
    _, chart = real_chart
    assert "longitude_deg" in chart["ascendant"]


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


def test_bhava_chalit_cusps_anchor_on_the_real_ascendant(real_chart):
    """Before the fix the family read ascendant.get('longitude', 0.0): cusps anchored at 0 degrees
    Aries, so EVERY graha of a non-Aries-lagna chart was reported as 'diverging from rasi'."""
    canonical_id, chart = real_chart
    asc_long = chart["ascendant"]["longitude_deg"]
    expected = {
        g["name"]
        for g in chart["grahas"]
        if int(((g["longitude"] - asc_long) % 360.0) // 30.0) + 1 != int(g["house"])
    }
    assert len(expected) < len(chart["grahas"])  # the synthetic chart must discriminate
    rows = _build_bhava_chalit_divergence_rows(
        _NoDbConn(), chart, "chart", "build", canonical_id, "2026-01-01T00:00:00+00:00", "test",
    )
    assert len(rows) == len(expected)
    for row in rows:
        assert row["fact_value_jsonb"]["asc_longitude"] == pytest.approx(round(asc_long, 4))


def test_ascendant_longitude_prefers_l25_key_accepts_alias_and_never_defaults():
    assert _ascendant_longitude({"longitude_deg": 94.5}) == 94.5
    assert _ascendant_longitude({"longitude": 12.0}) == 12.0
    assert _ascendant_longitude({"longitude_deg": 94.5, "longitude": 12.0}) == 94.5
    with pytest.raises(RuntimeError, match="ascendant 'longitude_deg' missing"):
        _ascendant_longitude({"sign": "Aries"})
