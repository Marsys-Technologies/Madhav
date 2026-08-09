"""
test_bo_pratijna_v4_engine_live.py — PRATIJÑĀ v4 Lane B2 live-DB acceptance
test: the engine LIBRARY (`bo_pratijna_v4_engine.py`), run against the live
chart 482012f1, must reproduce `RUNG_P3_HAND_WORKED_v1_0.md`'s hand-worked
marriage/separation/childbirth numbers EXACTLY — the acceptance oracle for
this whole lane.

Skipped, not failed, when DBURL is unset (mirrors test_chart_reader_v4.py's
convention). R19: read-only — this test never writes to the database.
"""
from __future__ import annotations

import os
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from brahmagyan.chart_reader_v4 import ChartReaderV4, connect  # noqa: E402
from pipeline.orchestrator.writers.bo_pratijna_v4_engine import (  # noqa: E402
    PratijnaV4Engine,
)

CHART_482012F1 = "482012f1-710e-4a25-994a-93821f5871aa"
CHART_1C826D5A = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"
AYANAMSHA = "lahiri_chitrapaksha"

DBURL = os.environ.get("DBURL")
requires_db = pytest.mark.skipif(not DBURL, reason="DBURL not set — see PRATIJNA_V4_STATE.md")


@pytest.fixture(scope="module")
def conn():
    if not DBURL:
        pytest.skip("DBURL not set")
    c = connect(DBURL)
    yield c
    c.close()


@pytest.fixture()
def engine(conn):
    return PratijnaV4Engine(ChartReaderV4(conn, ayanamsha=AYANAMSHA))


# ── RUNG_P3's acceptance numbers, verbatim from RUNG_P3_HAND_WORKED_v1_0.md ──

RUNG_P3_EXPECTED = {
    "marriage": {"occurrence": 0.321, "occurrence_label": "WEAK", "condition": 5.83, "condition_label": "MODERATE"},
    "separation": {"occurrence": 0.505, "occurrence_label": "MODERATE", "condition": 8.75, "condition_label": "CRITICAL"},
    "childbirth": {"occurrence": 0.593, "occurrence_label": "MODERATE", "condition": 7.50, "condition_label": "SEVERE"},
}


@requires_db
@pytest.mark.parametrize("event_class_id", list(RUNG_P3_EXPECTED))
def test_reproduces_rung_p3_hand_worked_numbers_exactly(engine, event_class_id):
    expected = RUNG_P3_EXPECTED[event_class_id]
    result = engine.score_class(CHART_482012F1, event_class_id)
    assert result.status == "scored"
    assert result.occurrence == expected["occurrence"], (
        f"{event_class_id} occurrence {result.occurrence} != RUNG_P3's {expected['occurrence']}"
    )
    assert result.occurrence_label == expected["occurrence_label"]
    assert result.condition == expected["condition"], (
        f"{event_class_id} condition {result.condition} != RUNG_P3's {expected['condition']}"
    )
    assert result.condition_label == expected["condition_label"]


@requires_db
def test_marriage_and_separation_occurrence_and_condition_genuinely_differ(engine):
    """The exact defect class (v2/v3's marriage≡separation identical grades
    from identical evidence) this campaign exists to fix, re-verified at the
    engine level, not just the raw number — the underlying weights/factor
    ledgers must differ too, not just coincide in the final float."""
    marriage = engine.score_class(CHART_482012F1, "marriage")
    separation = engine.score_class(CHART_482012F1, "separation")
    assert marriage.occurrence != separation.occurrence
    assert marriage.condition != separation.condition
    marriage_karakas = {f["graha"] for f in marriage.factor_ledger if f["slot"] == "karaka"}
    separation_karakas = {f["graha"] for f in separation.factor_ledger if f["slot"] == "karaka"}
    assert marriage_karakas != separation_karakas, "marriage/separation must score DIFFERENT karakas"


@requires_db
def test_no_denials_fired_for_the_three_rung_p3_classes(engine):
    """RUNG_P3 §1.1/§2.2/§3.1: no denial configuration fires for any of the
    three hand-worked classes on this chart."""
    for event_class_id in RUNG_P3_EXPECTED:
        result = engine.score_class(CHART_482012F1, event_class_id)
        fired = [d for d in result.denials if d["fired"]]
        assert fired == [], f"{event_class_id} unexpectedly fired denials: {fired}"


@requires_db
def test_score_all_covers_27_classes(engine):
    scores = engine.score_all(CHART_482012F1)
    assert len(scores) == 27


@requires_db
def test_runs_on_second_chart_without_error(engine):
    """R13 discipline check: the engine must run identically (no chart-
    specific branching) on the second canonical chart."""
    result = engine.score_class(CHART_1C826D5A, "marriage")
    assert result.status == "scored"
    assert 0.0 <= result.occurrence <= 1.0
    assert 0.0 <= result.condition <= 10.0


@requires_db
def test_provenance_non_empty_for_scored_class(engine):
    result = engine.score_class(CHART_482012F1, "marriage")
    assert len(result.provenance) > 0


# ── AMENDMENT F1 (R20 cycle 1) — live-chart proof that the amendment-gated
#    engine reproduces v4.0 unmodified by default, and moves marriage's
#    dignity-driven cells under 'F1' on the real chart 482012f1. ────────────


@pytest.fixture()
def engine_f1(conn):
    return PratijnaV4Engine(ChartReaderV4(conn, ayanamsha=AYANAMSHA), amendments=frozenset({"F1"}))


@requires_db
def test_f1_engine_default_off_matches_v40_rung_p3_marriage(engine):
    """The default-constructed engine (amendments unset) must still
    reproduce RUNG_P3's exact marriage number — merging F1 support changes
    no production behavior."""
    result = engine.score_class(CHART_482012F1, "marriage")
    assert result.occurrence == 0.321
    assert result.occurrence_label == "WEAK"
    assert "+F1" not in result.engine_version


@requires_db
def test_f1_amendment_moves_marriage_occurrence_on_482012f1(engine_f1):
    """Live proof of the dispositor-conjunction exception firing on the real
    chart: 7L=Venus and karaka=Venus are both dignity-scored against Venus's
    conjunction with its own dispositor Jupiter (both D1 house 9,
    RUNG_P3_HAND_WORKED_v1_0.md §0.3) — under F1 this reads naisargika-only
    (neutral/0.50) instead of v4.0's compound enemy/0.30, raising marriage's
    occurrence above the v4.0 RUNG_P3 baseline of 0.321."""
    result = engine_f1.score_class(CHART_482012F1, "marriage")
    assert result.occurrence > 0.321
    assert result.engine_version.endswith("+F1")
    venus_entries = [f for f in result.factor_ledger if f.get("graha") == "Venus" or f.get("lord") == "Venus"]
    assert any("AMENDMENT F1" in f.get("detail", "") for f in venus_entries)


@requires_db
def test_f1_amendment_does_not_change_condition_axis(engine, engine_f1):
    """§5.2's condition axis has no dignity-band input at all (§2.7 aspect
    fractions only) — F1 must leave condition scores byte-identical."""
    v40 = engine.score_class(CHART_482012F1, "marriage")
    v41 = engine_f1.score_class(CHART_482012F1, "marriage")
    assert v40.condition == v41.condition
    assert v40.condition_label == v41.condition_label


@requires_db
def test_f1_amendment_leaves_unaffected_classes_untouched(engine, engine_f1):
    """Surgical-scope live check: a class whose slots never touch a
    dispositor-conjunction pair on this chart must score byte-identical
    under F1. `career_entry` (10L=Saturn@exalted house7, karaka Sun/Saturn)
    has no Venus/Jupiter-in-Sagittarius dependency."""
    v40 = engine.score_class(CHART_482012F1, "career_entry")
    v41 = engine_f1.score_class(CHART_482012F1, "career_entry")
    assert v40.occurrence == v41.occurrence
    assert v40.condition == v41.condition
