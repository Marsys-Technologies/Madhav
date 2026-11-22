"""
NIR-09 regression tests — deterministic D1 sign/dignity & composite classification check.

Replaces the blind `max_count / n_grahas >= 0.75` `(D-3 regression signature)` heuristic in
`ga_structural_writer._build_structural_relationship_rows` with an authoritative D1 check:
1. Authentic clustered charts (e.g. Abhisek's 7/9 `neutral` + Jupiter/Saturn `well_placed`)
   pass cleanly across all 5 canonical ayanamshas with ZERO warning logs, logging the
   verified observed distribution at INFO level.
2. Actual legacy D-3 off-by-one regressions (`Jupiter` in `Sagittarius` tagged `neutral` or
   `debilitated`, `Saturn` in `Libra` tagged `neutral`, `Mars` in `Scorpio` tagged `neutral`),
   `sign` vs `sign_id` mismatches, and corrupted composite classifications fail loudly.
3. Governed node treatment (Rahu/Ketu remain `'neutral'` in `dignity_status` and
   `graha_composite_state_classification` even when in Taurus/Scorpio and retrograde) is
   preserved and enforced against corruption (`exalted` node rejects loudly).
"""
from __future__ import annotations

import logging
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import ga_writers.ga_structural_writer as sut  # noqa: E402
from pyjhora_adapter.compute import compute_chart  # noqa: E402


_SE1_AVAILABLE = bool(os.environ.get("SE_EPHE_PATH")) and os.path.isdir(os.environ["SE_EPHE_PATH"])

_ABHISEK_BP = {
    "datetime_iso": "1984-02-05T10:43:00",
    "latitude_deg": 20.27,
    "longitude_deg": 85.84,
    "tz_offset_hours": 5.5,
}


def _seven_of_nine_neutral_chart() -> dict:
    """Offline reproduction of Abhisek's 7/9 neutral + 2/9 well_placed distribution."""
    return {
        "ascendant": {"sign": "Aries", "sign_id": 1, "longitude_deg": 12.43},
        "grahas": [
            {"name": "Sun", "sign": "Capricorn", "sign_id": 10, "house": 10, "longitude": 291.96, "retrograde": False, "dignity_status": "neutral"},
            {"name": "Moon", "sign": "Aquarius", "sign_id": 11, "house": 11, "longitude": 327.06, "retrograde": False, "dignity_status": "neutral"},
            {"name": "Mars", "sign": "Libra", "sign_id": 7, "house": 7, "longitude": 198.52, "retrograde": False, "dignity_status": "neutral"},
            {"name": "Mercury", "sign": "Capricorn", "sign_id": 10, "house": 10, "longitude": 270.84, "retrograde": False, "dignity_status": "neutral"},
            {"name": "Jupiter", "sign": "Sagittarius", "sign_id": 9, "house": 9, "longitude": 249.79, "retrograde": False, "dignity_status": "own_sign"},
            {"name": "Venus", "sign": "Sagittarius", "sign_id": 9, "house": 9, "longitude": 259.17, "retrograde": False, "dignity_status": "neutral"},
            {"name": "Saturn", "sign": "Libra", "sign_id": 7, "house": 7, "longitude": 202.43, "retrograde": False, "dignity_status": "exalted"},
            {"name": "Rahu", "sign": "Taurus", "sign_id": 2, "house": 2, "longitude": 49.03, "retrograde": True, "dignity_status": "neutral"},
            {"name": "Ketu", "sign": "Scorpio", "sign_id": 8, "house": 8, "longitude": 229.03, "retrograde": True, "dignity_status": "neutral"},
        ],
    }


def _classes_by_subject(rows: list[dict]) -> dict[str, str]:
    return {
        r["fact_subject"]: r["fact_value_text"]
        for r in rows
        if r["fact_category"] == "graha_composite_state_classification"
    }


def test_authentic_7_of_9_neutral_cluster_passes_with_zero_d3_warnings(caplog):
    chart = _seven_of_nine_neutral_chart()
    with caplog.at_level(logging.INFO, logger=sut.logger.name):
        rows = sut._build_structural_relationship_rows(
            chart,
            "482012f1-710e-4a25-994a-93821f5871aa",
            "build-nir09",
            "lahiri_chitrapaksha",
            "2026-11-21T00:00:00+00:00",
            "test-eng",
            conn=None,
        )

    classes = _classes_by_subject(rows)
    assert classes == {
        "SUN": "neutral",
        "MOON": "neutral",
        "MAR": "neutral",
        "MER": "neutral",
        "JUP": "well_placed",
        "VEN": "neutral",
        "SAT": "well_placed",
        "RAH_MEAN": "neutral",
        "KET_MEAN": "neutral",
    }
    warnings = [r for r in caplog.records if r.levelno >= logging.WARNING]
    assert not warnings, [w.message for w in warnings]
    assert not any("D-3 regression signature" in r.message for r in caplog.records)
    info_msgs = [r.message for r in caplog.records if r.levelno == logging.INFO]
    assert any("verified against D1 sign/dignity" in m and "concentrated=True" in m for m in info_msgs), info_msgs


@pytest.mark.skipif(not _SE1_AVAILABLE, reason="NOT_RUN: SE_EPHE_PATH (pinned .se1 files) is not set")
def test_real_ephemeris_abhisek_all_5_ayanamshas_emit_zero_d3_warnings(caplog):
    with caplog.at_level(logging.INFO, logger=sut.logger.name):
        for canonical_id, adapter_id in sut.CANONICAL_AYANAMSHAS.items():
            chart = compute_chart(inputs=_ABHISEK_BP, ayanamsha_id=adapter_id)
            rows = sut._build_structural_relationship_rows(
                chart,
                "482012f1-710e-4a25-994a-93821f5871aa",
                "build-nir09-real",
                canonical_id,
                "2026-11-21T00:00:00+00:00",
                "pyjhora/test",
                conn=None,
            )
            classes = _classes_by_subject(rows)
            assert classes["JUP"] == "well_placed", canonical_id
            assert classes["SAT"] == "well_placed", canonical_id
            assert classes["RAH_MEAN"] == "neutral", canonical_id
            assert classes["KET_MEAN"] == "neutral", canonical_id
            assert sum(1 for v in classes.values() if v == "neutral") == 7, (canonical_id, classes)

    warnings = [r for r in caplog.records if r.levelno >= logging.WARNING]
    assert not warnings, [w.message for w in warnings]
    assert not any("D-3 regression signature" in r.message for r in caplog.records)


@pytest.mark.parametrize(
    ("planet", "bad_dignity"),
    [
        ("Jupiter", "debilitated"),  # exact pre-D-3 1-based sign_id collision (Sagittarius sid=9 vs 0-based Capricorn=9)
        ("Saturn", "neutral"),       # exact pre-D-3 Libra miss (sid=7 != 0-based Libra=6)
        ("Mars", "neutral"),         # single non-concentrated own-sign -> neutral miss
    ],
)
def test_corrupted_dignity_mapping_fails_deterministically(planet, bad_dignity):
    chart = _seven_of_nine_neutral_chart()
    if planet == "Mars":
        chart["grahas"][2]["sign"] = "Scorpio"
        chart["grahas"][2]["sign_id"] = 8
        chart["grahas"][2]["longitude"] = 220.0
    for g in chart["grahas"]:
        if g["name"] == planet:
            g["dignity_status"] = bad_dignity

    with pytest.raises(RuntimeError, match=rf"D-3 INTEGRITY HALT:.*graha={planet}\b"):
        sut._build_structural_relationship_rows(
            chart, "chart-bad", "build-bad", "lahiri_chitrapaksha", "2026-11-21T00:00:00+00:00", "eng"
        )


def test_sign_vs_sign_id_off_by_one_fails_deterministically():
    chart = _seven_of_nine_neutral_chart()
    # Corrupt Saturn Libra sign_id=7 -> 6 (the off-by-one boundary error)
    chart["grahas"][6]["sign_id"] = 6
    with pytest.raises(RuntimeError, match=r"D-3 INTEGRITY HALT:.*graha=Saturn sign/sign_id mismatch"):
        sut._build_structural_relationship_rows(
            chart, "chart-sid", "build-sid", "lahiri_chitrapaksha", "2026-11-21T00:00:00+00:00", "eng"
        )


@pytest.mark.parametrize(("node_name", "bad_dignity"), [("Rahu", "exalted"), ("Ketu", "exalted"), ("Rahu", "debilitated")])
def test_governed_node_dignity_rule_enforced(node_name, bad_dignity):
    """Under currently governed node treatment, Rahu/Ketu stay 'neutral' in composite classification."""
    chart = _seven_of_nine_neutral_chart()
    for g in chart["grahas"]:
        if g["name"] == node_name:
            g["dignity_status"] = bad_dignity

    with pytest.raises(RuntimeError, match=rf"D-3 INTEGRITY HALT:.*graha={node_name}\b.*expected='neutral'"):
        sut._build_structural_relationship_rows(
            chart, "chart-node", "build-node", "lahiri_chitrapaksha", "2026-11-21T00:00:00+00:00", "eng"
        )


def test_corrupted_composite_classification_caught_deterministically():
    chart = _seven_of_nine_neutral_chart()
    rows = sut._build_structural_relationship_rows(
        chart, "chart-cls", "build-cls", "lahiri_chitrapaksha", "2026-11-21T00:00:00+00:00", "eng"
    )
    cls_rows = [r for r in rows if r["fact_category"] == "graha_composite_state_classification"]
    # Tamper Saturn's emitted classification from 'well_placed' -> 'neutral'
    for r in cls_rows:
        if r["fact_subject"] == "SAT":
            r["fact_value_text"] = "neutral"

    with pytest.raises(RuntimeError, match=r"D-3 INTEGRITY HALT:.*graha=Saturn classification='neutral', expected='well_placed'"):
        sut._verify_composite_dignity_integrity(
            grahas_data=chart["grahas"],
            classification_rows=cls_rows,
            classification_counts={"neutral": 8, "well_placed": 1},
            nbry_d1_bhanga_planets=set(),
            chart_id="chart-cls",
            ayanamsha_id="lahiri_chitrapaksha",
        )
