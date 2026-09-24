"""WP9 task 5.3 — Vedha + Moorti on the kernel.

GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0 §5.3 / GOCHARA_FAMILY_ELEVATION_PLAN
v2_1 §5.4 (F-11, A08/H-6):

  - Coverage = the REQUESTED horizon (not the ±460 d default): both overlay
    writers accept ctx.config['horizon_start']/['horizon_end'].
  - Every gap → `unavailable`, never quality_gates=1.0 by default: the kernel
    overlay projection (services/gochara_kernel/overlays.py) takes the
    searched horizon explicitly and returns factor=None outside it.
  - Moorti graded at the TRUE kernel sign_ingress instant
    (precision_regime='instant_grain'); the day-grade misclassification rate
    is measured and reported.
  - independence_group on every vedha row (detail JSONB) via the family's
    single identity scheme, so one obstruction root attenuates once (A08).

Plan §10 fixtures implemented here:
  "Negative"           — overlay gap → unavailable (TestOverlayProjection).
  "Overlay at instant" — recomputing overlay state at an instant reproduces
                         the projection's own interval-set answer.

DB scenarios run ONLY against the disposable WP6 Postgres; NOT_RUN otherwise.
"""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import psycopg  # noqa: E402

from tests.l3.gochara.test_wp9_stamp_columns import (  # noqa: E402
    BASE_DDL,
    HORIZON_BACK_DAYS,
    HORIZON_FORWARD_DAYS,
    MIGRATION_1082,
    MOORTI_CIT,
    WP6_DSN,
    _wp6_reachable,
)

import services.ka_moorti_nirnaya.writer as moorti_writer  # noqa: E402
import services.ka_vedha_gochara.writer as vedha_writer  # noqa: E402
from services.gochara_kernel.overlays import (  # noqa: E402
    OverlayInterval,
    coverage_gaps,
    date_to_jd,
    moorti_at,
    quality_gates_at,
)

BODIES = ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")

GROUP_CHART_ID = "c2222222-2222-4222-8222-222222222222"
INSTANT_CHART_ID = "c3333333-3333-4333-8333-333333333333"
HORIZON_CHART_ID = "c4444444-4444-4444-8444-444444444444"


@pytest.fixture(scope="session")
def wp9_kernel_schema():
    if not _wp6_reachable():
        pytest.skip("NOT_RUN: disposable WP6 database unreachable")
    conn = psycopg.connect(WP6_DSN, autocommit=True)
    conn.execute(BASE_DDL)
    conn.execute(MIGRATION_1082.read_text())
    conn.close()
    return True


# ── Plan §10 fixtures, pure (no DB) ─────────────────────────────────────────

def _iv(kind, start, end, group=None, factor=1.0, cancelled=False, **payload):
    return OverlayInterval(
        kind=kind, start_jd=start, end_jd=end, independence_group=group,
        suppression_factor=factor, cancelled=cancelled, payload=payload,
    )


class TestOverlayProjection:
    """services/gochara_kernel/overlays.py — the projection the ledger's
    'no stored overlay copy' rule (plan §4.3) makes load-bearing."""

    H0 = date_to_jd(date(2026, 1, 1))
    H1 = date_to_jd(date(2026, 12, 31))
    T_IN = date_to_jd(date(2026, 6, 15))
    T_OUT = date_to_jd(date(2027, 6, 15))

    def test_negative_outside_searched_horizon_is_unavailable(self):
        # Plan §10 "Negative": overlay gap → unavailable, NEVER a default 1.0.
        factor, detail = quality_gates_at(
            [], self.T_OUT, searched_horizon=(self.H0, self.H1),
        )
        assert factor is None
        assert detail["state"] == "unavailable"

    def test_negative_coverage_gaps_report_unavailable_spans(self):
        built = [_iv("house_vedha", self.H0, date_to_jd(date(2026, 3, 1)))]
        gaps = coverage_gaps(built, self.H0, self.H1)
        assert gaps == [(date_to_jd(date(2026, 3, 1)), self.H1)]

    def test_coverage_gaps_empty_when_fully_covered(self):
        built = [_iv("moorti", self.H0, self.H1)]
        assert coverage_gaps(built, self.H0, self.H1) == []

    def test_clear_inside_coverage_with_no_vedha(self):
        factor, detail = quality_gates_at(
            [], self.T_IN, searched_horizon=(self.H0, self.H1),
        )
        assert factor == 1.0
        assert detail["state"] == "clear"

    def test_a08_one_root_attenuates_once(self):
        # Two rows rooted in the SAME physical obstruction (one
        # independence_group) contribute ONE factor, not a product of two.
        rows = [
            _iv("house_vedha", self.H0, self.H1, group="g1", factor=0.70),
            _iv("sarvatobhadra", self.H0, self.H1, group="g1", factor=0.85),
        ]
        factor, detail = quality_gates_at(
            rows, self.T_IN, searched_horizon=(self.H0, self.H1),
        )
        assert factor == pytest.approx(0.70)  # strongest of the group, once
        assert detail["independent_roots"] == 1

    def test_distinct_roots_multiply(self):
        rows = [
            _iv("house_vedha", self.H0, self.H1, group="g1", factor=0.70),
            _iv("latta", self.H0, self.H1, group="g2", factor=0.80),
        ]
        factor, _ = quality_gates_at(rows, self.T_IN, searched_horizon=(self.H0, self.H1))
        assert factor == pytest.approx(0.56)

    def test_cancelled_interval_is_coverage_at_factor_one(self):
        rows = [_iv("house_vedha", self.H0, self.H1, group="g1", factor=1.0, cancelled=True)]
        factor, detail = quality_gates_at(rows, self.T_IN, searched_horizon=(self.H0, self.H1))
        assert factor == 1.0
        assert detail["state"] == "obstructed"
        assert detail["fired_vedha"][0]["cancelled"] is True

    def test_overlay_at_instant_recompute_reproduces_projection(self):
        # Plan §10 "Overlay at instant": the ledger stores no overlay copy;
        # recomputing at a stored contact instant reproduces the projection's
        # own interval-set answer — deterministically, and equal to the direct
        # interval-membership computation.
        intervals = [
            _iv("house_vedha", date_to_jd(date(2026, 6, 1)), date_to_jd(date(2026, 7, 1)),
                group="g1", factor=0.75),
            _iv("latta", date_to_jd(date(2026, 6, 10)), date_to_jd(date(2026, 6, 20)),
                group="g2", factor=0.90),
            _iv("moorti", date_to_jd(date(2026, 6, 1)), date_to_jd(date(2026, 8, 1)),
                moorti_name="swarna", quality_tier=1),
        ]
        horizon = (self.H0, self.H1)
        first = quality_gates_at(intervals, self.T_IN, searched_horizon=horizon)
        second = quality_gates_at(intervals, self.T_IN, searched_horizon=horizon)
        assert first == second
        # Direct interval-set answer: covering vedha intervals, deduped by group.
        covering = [i for i in intervals if i.kind != "moorti" and i.covers(self.T_IN)]
        expected = 1.0
        for g in {i.independence_group for i in covering}:
            expected *= min(i.suppression_factor for i in covering if i.independence_group == g)
        assert first[0] == pytest.approx(expected)
        moorti = moorti_at(intervals, self.T_IN, searched_horizon=horizon)
        assert moorti["state"] == "active" and moorti["moorti_name"] == "swarna"
        assert moorti_at(intervals, self.T_OUT, searched_horizon=horizon)["state"] == "unavailable"


# ── DB harness ───────────────────────────────────────────────────────────────

def _wipe_global(conn):
    with conn.cursor() as cur:
        for table in (
            "ephemeris_daily", "bg_transit_rules", "bg_phaladeepika_latta",
            "bg_vedha_malefic_scale", "bg_sarvatobhadra_grid",
            "l1_sarvatobhadra_vedha", "bg_transit_moorti",
        ):
            cur.execute(f"DELETE FROM {table}")


def _seed_chart_fact(conn, chart_id, janma_lon=5.0):
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO chart_facts (fact_id, chart_id, ayanamsha_id, fact_category, "
            "fact_subject, fact_key, fact_value_num) VALUES (%s,%s,%s,%s,%s,%s,%s) "
            "ON CONFLICT DO NOTHING",
            (f"{chart_id}-janma-moon", chart_id, "lahiri_chitrapaksha",
             "graha_position", "MOON", "longitude_sidereal", janma_lon),
        )


def _seed_ephemeris(conn, lon_fn, back=HORIZON_BACK_DAYS, forward=HORIZON_FORWARD_DAYS):
    today = date.today()
    horizon_start = today - timedelta(days=back)
    days = back + forward + 1
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO ephemeris_daily (date, body, ayanamsha_id, tropical_longitude, "
            "speed_dps, is_retrograde) VALUES (%s,%s,%s,%s,%s,%s)",
            [
                (horizon_start + timedelta(days=off), body, "tropical",
                 lon_fn(body, off), 1.0, False)
                for off in range(days)
                for body in BODIES
            ],
        )
    return horizon_start


def _seed_moorti_table(conn):
    moorti_names = {1: "swarna", 2: "rajata", 3: "tamra", 4: "loha"}
    with conn.cursor() as cur:
        cur.executemany(
            "INSERT INTO bg_transit_moorti (nakshatra_offset, moorti_name, quality_tier, "
            "phala_brief, classical_citation) VALUES (%s,%s,%s,%s,%s)",
            [
                (off, moorti_names[((off - 1) % 4) + 1], ((off - 1) % 4) + 1,
                 f"moorti phala for offset {off}", MOORTI_CIT)
                for off in range(1, 28)
            ],
        )


def _run_moorti(chart_id, extra_config=None):
    conn = psycopg.connect(WP6_DSN)
    config = {"chart_id": chart_id}
    config.update(extra_config or {})
    ctx = SimpleNamespace(db_conn=conn, config=config, dry_run=False)
    orig = moorti_writer._compute_ayanamsha_offset
    moorti_writer._compute_ayanamsha_offset = lambda _d: 0.0
    try:
        result = moorti_writer.KaMoortiNirnayaWriter().run(ctx)
        conn.commit()
    finally:
        moorti_writer._compute_ayanamsha_offset = orig
        conn.close()
    return result


def _fetch_moorti_rows(chart_id):
    with psycopg.connect(WP6_DSN) as c:
        return c.execute(
            "SELECT graha, window_start, window_end, moorti_computed, precision_regime, "
            "moon_nakshatra_idx_at_ingress, nakshatra_offset, moorti_name "
            "FROM kala_moorti_nirnaya WHERE chart_id = %s ORDER BY graha, window_start",
            (chart_id,),
        ).fetchall()


# ── independence_group on vedha rows (A08) ───────────────────────────────────

def _group_lon(body: str, off: int) -> float:
    """Janma Moon sign 0 / nak 0. Sun in sign 2 (house 3) days 100-130 with
    Mars in sign 8 (house 9 — the vedha house) days 110-120 (Saturn would trip
    the M-8 Sun↔Saturn exclusion; Mars is an effective malefic obstructor).
    Mars otherwise parked in nak 14 (the algorithmic SBC vedha nak of janma
    nak 0); Venus in nak 23 (latta rule 5-forward → latta nak 0 = janma)."""
    if body == "Sun":
        return 65.0 if 100 <= off <= 130 else 155.0
    if body == "Moon":
        return 40.0
    if body == "Mars":
        return 245.0 if 110 <= off <= 120 else 190.0
    if body == "Saturn":
        return 100.0
    if body == "Venus":
        return 310.0
    if body == "Mercury":
        return 40.0
    if body == "Jupiter":
        return 100.0
    if body == "Rahu":
        return 305.0
    return 125.0  # Ketu


class TestVedhaIndependenceGroup:
    def test_group_present_stable_and_shared_per_physical_root(self, wp9_kernel_schema):
        conn = psycopg.connect(WP6_DSN, autocommit=True)
        _wipe_global(conn)
        _seed_chart_fact(conn, GROUP_CHART_ID)
        _seed_ephemeris(conn, _group_lon)
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO bg_transit_rules (rule_type, graha, primary_house, vedha_house, "
                "phala, classical_citation) VALUES (%s,%s,%s,%s,%s,%s)",
                ("favourable", "sun", 3, 9, "synthetic fixture phala",
                 "Phaladeepika Ch.26 (Gochara Vedha and Transit Phala)"),
            )
            cur.execute(
                "INSERT INTO bg_phaladeepika_latta (graha, count_from_graha, direction, "
                "effect_description, affliction_condition, source_citation) "
                "VALUES (%s,%s,%s,%s,%s,%s)",
                ("Venus", 5, "forward", "synthetic latta", "synthetic", "synthetic-cit"),
            )
            cur.executemany(
                "INSERT INTO bg_vedha_malefic_scale (malefic_count, effect_grade, "
                "effect_description, source_citation) VALUES (%s,%s,%s,%s)",
                [(n, f"grade-{n}", "synthetic", "synthetic-cit") for n in range(1, 6)],
            )
        conn.close()

        vconn = psycopg.connect(WP6_DSN)
        ctx = SimpleNamespace(
            db_conn=vconn, config={"chart_id": GROUP_CHART_ID}, dry_run=False,
        )
        orig = vedha_writer._compute_ayanamsha_offset
        vedha_writer._compute_ayanamsha_offset = lambda _d: 0.0
        try:
            vedha_writer.KaVedhaGocharaWriter().run(ctx)
            vconn.commit()
        finally:
            vedha_writer._compute_ayanamsha_offset = orig
            vconn.close()

        with psycopg.connect(WP6_DSN) as c:
            rows = c.execute(
                "SELECT vedha_kind, detail FROM kala_vedha_gochara WHERE chart_id = %s",
                (GROUP_CHART_ID,),
            ).fetchall()
        assert rows, "expected vedha rows for the group fixture"
        by_kind = {}
        for kind, detail_raw in rows:
            detail = detail_raw if isinstance(detail_raw, dict) else json.loads(detail_raw)
            by_kind.setdefault(kind, []).append(detail)

        house = by_kind["house_vedha"][0]
        assert house["obstruction_active"] is True
        group = house["independence_group"]
        assert isinstance(group, str) and group.startswith("sha256:")  # ids.py scheme
        for kind in ("sarvatobhadra", "latta"):
            assert by_kind[kind][0]["independence_group"]
            assert by_kind[kind][0]["independence_group"].startswith("sha256:")
        # Different physical roots → different groups.
        assert by_kind["sarvatobhadra"][0]["independence_group"] != group

        # Determinism: a rebuild (per-chart delete-then-insert) reproduces the
        # identical group — one root keeps one identity across rebuilds.
        vconn = psycopg.connect(WP6_DSN)
        ctx = SimpleNamespace(
            db_conn=vconn, config={"chart_id": GROUP_CHART_ID}, dry_run=False,
        )
        orig = vedha_writer._compute_ayanamsha_offset
        vedha_writer._compute_ayanamsha_offset = lambda _d: 0.0
        try:
            vedha_writer.KaVedhaGocharaWriter().run(ctx)
            vconn.commit()
        finally:
            vedha_writer._compute_ayanamsha_offset = orig
            vconn.close()
        with psycopg.connect(WP6_DSN) as c:
            detail_raw = c.execute(
                "SELECT detail FROM kala_vedha_gochara WHERE chart_id = %s "
                "AND vedha_kind = 'house_vedha'",
                (GROUP_CHART_ID,),
            ).fetchone()[0]
        detail = detail_raw if isinstance(detail_raw, dict) else json.loads(detail_raw)
        assert detail["independence_group"] == group

    def test_group_is_computed_from_physical_root_only(self):
        # Same physical (body, relation, target degree, window instant) reached
        # through two different rules → ONE group (H-6); the rule never enters.
        g1 = vedha_writer._vedha_independence_group(
            body="Saturn", relation="vedha_obstruction",
            target_deg=240.0, window_start=date(2026, 3, 10),
        )
        g2 = vedha_writer._vedha_independence_group(
            body="Saturn", relation="vedha_obstruction",
            target_deg=240.0, window_start=date(2026, 3, 10),
        )
        g3 = vedha_writer._vedha_independence_group(
            body="Saturn", relation="vedha_obstruction",
            target_deg=240.0, window_start=date(2026, 3, 11),
        )
        assert g1 == g2
        assert g1 != g3


# ── Moorti at the true kernel ingress instant ────────────────────────────────

def _instant_lon(body: str, off: int) -> float:
    """Engineered for a day-grade misclassification: Sun steps sign 0 → sign 1
    at day 70 (spline ingress ≈ day 69.667); the Moon (20°/day) crosses a
    nakshatra boundary BETWEEN that instant and the day-70 daily value, so
    day-grade and instant-grade disagree on this run. Saturn steps sign 0 →
    sign 1 at day 150 — a second computed run. Everything else is parked."""
    if body == "Sun":
        return 10.0 if off < 70 else 40.0
    if body == "Saturn":
        return 5.0 if off < 150 else 35.0
    if body == "Moon":
        return (20.0 * off + 0.5) % 360.0
    if body == "Mars":
        return 190.0
    if body == "Mercury":
        return 40.0
    if body == "Jupiter":
        return 100.0
    if body == "Venus":
        return 310.0
    if body == "Rahu":
        return 305.0
    return 125.0  # Ketu


class TestMoortiKernelIngress:
    def test_instant_grading_and_misclassification_rate(self, wp9_kernel_schema, capsys):
        conn = psycopg.connect(WP6_DSN, autocommit=True)
        _wipe_global(conn)
        _seed_chart_fact(conn, INSTANT_CHART_ID, janma_lon=5.0)
        _seed_ephemeris(conn, _instant_lon)
        _seed_moorti_table(conn)
        conn.close()

        result = _run_moorti(INSTANT_CHART_ID)
        rows = _fetch_moorti_rows(INSTANT_CHART_ID)
        computed = [r for r in rows if r[3]]
        assert len(computed) == 2, f"expected the Sun + Saturn runs; got {computed}"
        for r in computed:
            assert r[4] == "instant_grain", f"{r[0]} run not graded at the instant"

        sun = next(r for r in computed if r[0] == "Sun")
        # Ingress ≈ day 69.667: Moon there is nak 23 (instant-grade); the
        # day-70 daily Moon is nak 24 (day-grade). janma nak 0 → offsets
        # 24 ('loha') vs 25 ('swarna'): the day-grade row is a MISCLASSIFICATION.
        assert sun[5] == 23, f"Sun instant-grade moon nak: {sun}"
        assert sun[7] == "loha", f"Sun moorti at instant: {sun}"

        notes = result.notes
        assert "kernel_instant_graded=2" in notes
        assert "day_grade_misclassified=" in notes
        misclassified = int(notes.split("day_grade_misclassified=")[1].split(";")[0])
        assert misclassified >= 1
        rate = float(notes.split("day_grade_misclassification_rate=")[1])
        print(
            "\nWP9 5.3 moorti error-rate fixture: "
            f"instant_graded=2, day_grade_misclassified={misclassified}, "
            f"rate={rate:.4f} (engineered synthetic layout — the real-ephemeris "
            "rate stays [U] NOT_RUN until measured on the production build)"
        )
        with capsys.disabled():
            pass  # keep the printed line in the test log for the report

    def test_uncomputed_runs_stay_date_grain(self, wp9_kernel_schema):
        rows = _fetch_moorti_rows(INSTANT_CHART_ID)
        uncomputed = [r for r in rows if not r[3]]
        assert uncomputed
        for r in uncomputed:
            assert r[4] == "date_grain"


# ── Coverage = requested horizon (F-11) ──────────────────────────────────────

class TestRequestedHorizon:
    def test_moorti_writer_honours_requested_horizon(self, wp9_kernel_schema):
        conn = psycopg.connect(WP6_DSN, autocommit=True)
        _wipe_global(conn)
        _seed_chart_fact(conn, HORIZON_CHART_ID)
        seed_start = _seed_ephemeris(conn, _instant_lon)
        _seed_moorti_table(conn)
        conn.close()

        req_start = seed_start + timedelta(days=30)
        req_end = seed_start + timedelta(days=120)
        result = _run_moorti(
            HORIZON_CHART_ID,
            {"horizon_start": req_start.isoformat(), "horizon_end": req_end.isoformat()},
        )
        assert f"horizon={req_start}..{req_end}" in result.notes
        rows = _fetch_moorti_rows(HORIZON_CHART_ID)
        assert rows
        for r in rows:
            assert r[1] >= req_start and r[2] <= req_end, (
                f"row window {r[1]}..{r[2]} escapes the requested horizon"
            )
        # The Sun ingress (day 70 of the seed) is inside the requested window
        # and still graded at the instant.
        sun = next(r for r in rows if r[0] == "Sun" and r[3])
        assert sun[4] == "instant_grain"

    def test_default_horizon_unchanged_when_not_requested(self, wp9_kernel_schema):
        conn = psycopg.connect(WP6_DSN, autocommit=True)
        _wipe_global(conn)
        _seed_chart_fact(conn, HORIZON_CHART_ID)
        _seed_ephemeris(conn, _instant_lon)
        _seed_moorti_table(conn)
        conn.close()
        today = date.today()
        result = _run_moorti(HORIZON_CHART_ID)
        expected_start = today - timedelta(days=HORIZON_BACK_DAYS)
        expected_end = today + timedelta(days=HORIZON_FORWARD_DAYS)
        assert f"horizon={expected_start}..{expected_end}" in result.notes
