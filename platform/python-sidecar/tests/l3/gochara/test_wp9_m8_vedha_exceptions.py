"""WP9 task 5.2 — M-8 vedha exceptions, vipareeta vedha, retrograde qualifier.

GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0 §5.2 / GOCHARA_FAMILY_ELEVATION_PLAN_
v2_1 M-8 (F-26): (a) mutual exclusions Sun↔Saturn and Moon↔Mercury — occupancy
of the vedha house by the excluded partner is never an obstruction; when it is
the ONLY occupancy, no house_vedha row is emitted and coverage records
`searched, exception_applied`; (b) vipareeta vedha — a companion joining the
transiting graha cancels the obstruction for the companionship interval
(cancelled=true, cancelled_by, cancelled_from/until, suppression_factor=1.0,
vipareeta.source_qualification='translator_commentary'); (c)
intensity_qualifier='retrograde_malefic' when the obstructing malefic is
retrograde within the obstruction window. Evaluation order: exceptions first,
then vipareeta.

Runs ONLY against the disposable WP6 Postgres; skips NOT_RUN when unreachable.
Schema + shared seed DDL are reused from test_wp9_stamp_columns (5.1); each
scenario here wipes the global ephemeris and the rule tables, seeds its own
synthetic layout, and runs the real writer end-to-end under a per-scenario
chart_id.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import psycopg  # noqa: E402

from tests.l3.gochara.test_wp9_stamp_columns import (  # noqa: E402
    BASE_DDL,
    BPHS_CH29,
    HORIZON_BACK_DAYS,
    HORIZON_FORWARD_DAYS,
    JANMA_FACT_ID,
    JANMA_MOON_LON,
    MIGRATION_1082,
    SCALE_CIT,
    WP6_DSN,
    _wp6_reachable,
)

import services.ka_vedha_gochara.writer as vedha_writer  # noqa: E402
from services.ka_vedha_gochara.logic import (  # noqa: E402
    MUTUAL_EXCLUSION_PAIRS,
    is_mutual_exclusion,
    vipareeta_cancellation,
)

BODIES = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")


@pytest.fixture(scope="session")
def wp9_m8_schema():
    if not _wp6_reachable():
        pytest.skip("NOT_RUN: disposable WP6 database unreachable")
    conn = psycopg.connect(WP6_DSN, autocommit=True)
    conn.execute(BASE_DDL)
    conn.execute(MIGRATION_1082.read_text())
    conn.close()
    return True


# ── Pure-logic unit tests ────────────────────────────────────────────────────

class TestMutualExclusionLogic:
    def test_pairs_are_exactly_the_two_ruled(self):
        assert MUTUAL_EXCLUSION_PAIRS == frozenset({
            frozenset({"Sun", "Saturn"}),
            frozenset({"Moon", "Mercury"}),
        })

    def test_symmetric(self):
        assert is_mutual_exclusion("Sun", "Saturn")
        assert is_mutual_exclusion("Saturn", "Sun")
        assert is_mutual_exclusion("Moon", "Mercury")
        assert is_mutual_exclusion("Mercury", "Moon")

    def test_non_pairs(self):
        assert not is_mutual_exclusion("Sun", "Mars")
        assert not is_mutual_exclusion("Moon", "Saturn")
        assert not is_mutual_exclusion("Rahu", "Ketu")


class TestVipareetaCancellation:
    def test_overlap_returns_intersection(self):
        comp = [{"sign_idx": 2, "start_date": date(2026, 3, 10), "end_date": date(2026, 3, 15),
                 "start_truncated": False, "end_truncated": False}]
        ov = vipareeta_cancellation(date(2026, 3, 5), date(2026, 3, 20), comp)
        assert ov == {"start": date(2026, 3, 10), "end": date(2026, 3, 15)}

    def test_no_overlap_returns_none(self):
        comp = [{"sign_idx": 2, "start_date": date(2026, 4, 1), "end_date": date(2026, 4, 5),
                 "start_truncated": False, "end_truncated": False}]
        assert vipareeta_cancellation(date(2026, 3, 5), date(2026, 3, 20), comp) is None


# ── End-to-end scenario harness ──────────────────────────────────────────────

def _run_scenario(wp9_m8_schema, *, chart_id: str, lon_fn, rules, retro_fn=None):
    """Wipes the global ephemeris + rule tables, seeds this scenario, runs the
    real writer. Returns (rows, result)."""
    today = date.today()
    horizon_start = today - timedelta(days=HORIZON_BACK_DAYS)
    days = HORIZON_BACK_DAYS + HORIZON_FORWARD_DAYS + 1

    conn = psycopg.connect(WP6_DSN, autocommit=True)
    with conn.cursor() as cur:
        cur.execute("DELETE FROM ephemeris_daily")
        cur.execute("DELETE FROM bg_transit_rules")
        cur.execute("DELETE FROM bg_phaladeepika_latta")
        cur.execute("DELETE FROM bg_vedha_malefic_scale")
        cur.execute("DELETE FROM bg_sarvatobhadra_grid")
        cur.execute("DELETE FROM l1_sarvatobhadra_vedha")
        cur.execute("DELETE FROM kala_vedha_gochara WHERE chart_id = %s", (chart_id,))
        cur.execute("DELETE FROM chart_facts WHERE chart_id = %s OR fact_id = %s", (chart_id, JANMA_FACT_ID))
        cur.execute(
            "INSERT INTO chart_facts (fact_id, chart_id, ayanamsha_id, fact_category, "
            "fact_subject, fact_key, fact_value_num) VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (JANMA_FACT_ID, chart_id, "lahiri_chitrapaksha", "graha_position",
             "MOON", "longitude_sidereal", JANMA_MOON_LON),
        )
        cur.executemany(
            "INSERT INTO bg_transit_rules (rule_type, graha, primary_house, vedha_house, "
            "phala, classical_citation) VALUES (%s,%s,%s,%s,%s,%s)",
            rules,
        )
        cur.executemany(
            "INSERT INTO bg_vedha_malefic_scale (malefic_count, effect_grade, "
            "effect_description, source_citation) VALUES (%s,%s,%s,%s)",
            [(n, f"grade-{n}", f"{n} malefic(s) obstructing", SCALE_CIT) for n in range(1, 6)],
        )
        cur.executemany(
            "INSERT INTO ephemeris_daily (date, body, ayanamsha_id, tropical_longitude, "
            "speed_dps, is_retrograde) VALUES (%s,%s,%s,%s,%s,%s)",
            [
                (horizon_start + timedelta(days=off), body, "tropical",
                 lon_fn(body, off), 1.0, bool(retro_fn and retro_fn(body, off)))
                for off in range(days)
                for body in BODIES
            ],
        )
    conn.close()

    run_conn = psycopg.connect(WP6_DSN)
    ctx = SimpleNamespace(db_conn=run_conn, config={"chart_id": chart_id}, dry_run=False)
    orig = vedha_writer._compute_ayanamsha_offset
    vedha_writer._compute_ayanamsha_offset = lambda _d: 0.0
    try:
        result = vedha_writer.KaVedhaGocharaWriter().run(ctx)
        run_conn.commit()
    finally:
        vedha_writer._compute_ayanamsha_offset = orig
        run_conn.close()

    with psycopg.connect(WP6_DSN, autocommit=True) as c:
        with c.cursor(row_factory=psycopg.rows.dict_row) as cur:
            cur.execute(
                "SELECT * FROM kala_vedha_gochara WHERE chart_id = %s ORDER BY graha, window_start",
                (chart_id,),
            )
            rows = [dict(r) for r in cur.fetchall()]
    return rows, result


# Innocuous constant longitudes: every body parked away from the crafted
# signs (2 = the primary, 8 = the vedha sign of sun/3) and away from nak 14
# (the algorithmic SBC vedha nak of janma nak 0), so no stray sarvatobhadra
# or companionship rows interfere with the scenario under test.
_BASE_LONS = {
    "Sun": 155.0, "Moon": 40.0, "Mars": 200.0, "Mercury": 40.0, "Jupiter": 100.0,
    "Venus": 310.0, "Saturn": 100.0, "Rahu": 305.0, "Ketu": 125.0,
}


def _lon_fn(overrides):
    """overrides: {body: (special_lon, start_off, end_off)} — body sits at
    special_lon for horizon offsets start..end, else at its base longitude.
    (The Moon is parked constant too — a cycling Moon would wander through
    the vedha sign every few days and register as a stray obstruction.)"""
    def fn(body: str, off: int) -> float:
        special = overrides.get(body)
        if special and special[1] <= off <= special[2]:
            return special[0]
        return _BASE_LONS[body]
    return fn


class TestM8MutualExclusion:
    """(a) Saturn-in-9th vs Sun-in-3rd -> NO house_vedha row; the exception is
    recorded in coverage with searched, exception_applied."""

    def test_excluded_partner_only_occupancy_emits_no_row(self, wp9_m8_schema):
        chart_id = "a1111111-0000-0000-0000-000000000001"
        rows, result = _run_scenario(
            wp9_m8_schema,
            chart_id=chart_id,
            lon_fn=_lon_fn({
                "Sun": (65.0, 100, 130),      # sign 2 = house 3 from Moon
                "Saturn": (245.0, 110, 120),  # sign 8 = the vedha house (9th)
            }),
            rules=[("favourable", "sun", 3, 9, "Courage, travel, gain from siblings", BPHS_CH29)],
        )
        house_rows = [r for r in rows if r["vedha_kind"] == "house_vedha"]
        assert house_rows == [], f"expected no house_vedha row, got {house_rows}"
        assert "m8_exceptions=1" in result.notes
        payload = result.notes.split("m8_exception_windows=", 1)[1].split(";horizon=", 1)[0]
        records = json.loads(payload)
        assert len(records) == 1
        rec = records[0]
        assert rec["graha"] == "Sun"
        assert rec["excluded_obstructors"] == ["Saturn"]
        assert rec["searched"] is True and rec["exception_applied"] is True

    def test_excluded_partner_alongside_effective_obstructor_keeps_row(self, wp9_m8_schema):
        """Saturn (excepted) AND Mars (effective) both in the vedha house ->
        the row survives with Mars as the obstruction and the exception
        recorded on detail.vedha_exception."""
        chart_id = "a1111111-0000-0000-0000-000000000002"
        rows, result = _run_scenario(
            wp9_m8_schema,
            chart_id=chart_id,
            lon_fn=_lon_fn({
                "Sun": (65.0, 100, 130),
                "Saturn": (245.0, 100, 130),
                "Mars": (245.0, 105, 125),
            }),
            rules=[("favourable", "sun", 3, 9, "Courage, travel, gain from siblings", BPHS_CH29)],
        )
        house_rows = [r for r in rows if r["vedha_kind"] == "house_vedha"]
        assert len(house_rows) == 1
        detail = house_rows[0]["detail"]
        assert detail["obstruction_active"] is True
        assert detail["obstructing_graha"] == "Mars"
        assert detail["malefic_obstructing_grahas"] == ["Mars"]
        assert detail["vedha_exception"] == {
            "pair_with": ["Saturn"], "searched": True, "exception_applied": True}
        assert "m8_exceptions=0" in result.notes


class TestM8Vipareeta:
    """(b) A companion joining the transiting graha cancels the obstruction
    for the companionship interval; the row is kept, suppression_factor=1.0."""

    def test_companion_cancels_obstruction(self, wp9_m8_schema):
        chart_id = "a1111111-0000-0000-0000-000000000003"
        rows, _result = _run_scenario(
            wp9_m8_schema,
            chart_id=chart_id,
            lon_fn=_lon_fn({
                "Sun": (65.0, 100, 130),        # primary, sign 2
                "Mars": (245.0, 105, 125),      # obstruction, sign 8
                "Jupiter": (65.0, 110, 115),    # companion joining the Sun
            }),
            rules=[("favourable", "sun", 3, 9, "Courage, travel, gain from siblings", BPHS_CH29)],
        )
        house_rows = [r for r in rows if r["vedha_kind"] == "house_vedha"]
        assert len(house_rows) == 1
        detail = house_rows[0]["detail"]
        assert detail["obstruction_active"] is True
        assert detail["obstructing_graha"] == "Mars"
        assert detail["cancelled"] is True
        assert detail["cancelled_by"] == "Jupiter"
        # cancelled interval = companionship ∩ obstruction = offsets 110..115
        horizon_start = date.today() - timedelta(days=HORIZON_BACK_DAYS)
        assert detail["cancelled_from"] == (horizon_start + timedelta(days=110)).isoformat()
        assert detail["cancelled_until"] == (horizon_start + timedelta(days=115)).isoformat()
        assert detail["suppression_factor"] == 1.0
        assert detail["vipareeta"]["source_qualification"] == "translator_commentary"
        # Row-level stamp stays verse_cited — the house_vedha RULE is verse-cited;
        # only the vipareeta application is translator commentary.
        assert house_rows[0]["source_qualification"] == "verse_cited"

    def test_no_companion_no_cancellation(self, wp9_m8_schema):
        chart_id = "a1111111-0000-0000-0000-000000000004"
        rows, _result = _run_scenario(
            wp9_m8_schema,
            chart_id=chart_id,
            lon_fn=_lon_fn({
                "Sun": (65.0, 100, 130),
                "Mars": (245.0, 105, 125),
            }),
            rules=[("favourable", "sun", 3, 9, "Courage, travel, gain from siblings", BPHS_CH29)],
        )
        detail = [r for r in rows if r["vedha_kind"] == "house_vedha"][0]["detail"]
        assert detail["cancelled"] is False
        assert detail["suppression_factor"] is None
        assert detail["vipareeta"] is None


class TestM8RetrogradeQualifier:
    """(c) An obstructing malefic retrograde within the obstruction window
    carries intensity_qualifier='retrograde_malefic'."""

    def test_retrograde_malefic_obstructor(self, wp9_m8_schema):
        chart_id = "a1111111-0000-0000-0000-000000000005"
        rows, _result = _run_scenario(
            wp9_m8_schema,
            chart_id=chart_id,
            lon_fn=_lon_fn({
                "Sun": (65.0, 100, 130),
                "Mars": (245.0, 105, 125),
            }),
            retro_fn=lambda body, off: body == "Mars" and 108 <= off <= 112,
            rules=[("favourable", "sun", 3, 9, "Courage, travel, gain from siblings", BPHS_CH29)],
        )
        detail = [r for r in rows if r["vedha_kind"] == "house_vedha"][0]["detail"]
        assert detail["intensity_qualifier"] == "retrograde_malefic"

    def test_direct_malefic_obstructor_no_qualifier(self, wp9_m8_schema):
        chart_id = "a1111111-0000-0000-0000-000000000006"
        rows, _result = _run_scenario(
            wp9_m8_schema,
            chart_id=chart_id,
            lon_fn=_lon_fn({
                "Sun": (65.0, 100, 130),
                "Mars": (245.0, 105, 125),
            }),
            retro_fn=lambda body, off: body == "Mars" and 200 <= off <= 210,  # outside window
            rules=[("favourable", "sun", 3, 9, "Courage, travel, gain from siblings", BPHS_CH29)],
        )
        detail = [r for r in rows if r["vedha_kind"] == "house_vedha"][0]["detail"]
        assert detail["intensity_qualifier"] is None

    def test_every_row_date_grain_on_this_path(self, wp9_m8_schema):
        """The DATE-grain overlap path never stamps an instant claim."""
        chart_id = "a1111111-0000-0000-0000-000000000007"
        rows, _result = _run_scenario(
            wp9_m8_schema,
            chart_id=chart_id,
            lon_fn=_lon_fn({
                "Sun": (65.0, 100, 130),
                "Mars": (245.0, 105, 125),
            }),
            rules=[("favourable", "sun", 3, 9, "Courage, travel, gain from siblings", BPHS_CH29)],
        )
        assert rows
        for r in rows:
            assert r["precision_regime"] == "date_grain"
