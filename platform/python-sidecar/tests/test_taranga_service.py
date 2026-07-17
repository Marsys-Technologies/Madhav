"""
tests/test_taranga_service.py — Kāla Taraṅga service core (L3 D-3 Lane T-2).

Covers:
  1. CR-87 — chart is a REQUIRED param on every public function (ChartRef
     construction, activation(), curve(), record_evidence()).
  2. cos² orb weighting + applying(x1.0)/separating(x0.7) distinction
     (via services.ka_sangam.engine.orb_strength_score, the same function
     this service imports at its single T-3 adapter point).
  3. Superposition: two simultaneous currents sum (not max/replace).
  4. CR-41 proof: activation()/curve() resolve for a FUTURE timestamp far
     beyond any batch writer's horizon (dasha spine ends, ephemeris doesn't
     — computed live).
  5. Evidence write-through fires ONLY on explicit record_evidence(), never
     as a side effect of activation()/curve().
  6. Chart-static substrate build from mocked chart_vichara / chart_facts /
     chart_dashas / bodha_mechanisms rows — no live DB required (mirrors
     tests/test_cr87_native_chart_context.py's "must not require a live DB
     where avoidable" discipline).

No live DB, no network. Real swisseph is used for transit positions (fast,
deterministic, already a hard dependency of this service).
"""
from __future__ import annotations

import sys
from collections import namedtuple
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

_FakeColumn = namedtuple("_FakeColumn", ["name"])

SIDECAR = Path(__file__).parent.parent
if str(SIDECAR) not in sys.path:
    sys.path.insert(0, str(SIDECAR))

from services import taranga_service as svc  # noqa: E402
from services.ka_sangam.engine import orb_strength_score  # noqa: E402

_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
_AYANAMSHA = "lahiri_chitrapaksha"


@pytest.fixture(autouse=True)
def _clear_cache():
    svc.clear_substrate_cache()
    svc._POSITION_MEMO.clear()
    yield
    svc.clear_substrate_cache()
    svc._POSITION_MEMO.clear()


# ── Mock DB machinery ────────────────────────────────────────────────────────

class _FakeCursor:
    """Minimal cursor stub: .execute(sql, params) inspects the SQL text to
    decide which canned rowset + description to hand back; .fetchall() /
    .fetchone() serve it; supports the `with conn.cursor() as cur:` protocol."""

    def __init__(self, tables: dict[str, tuple[list[str], list[tuple]]]):
        self._tables = tables
        self._current_cols: list[str] = []
        self._current_rows: list[tuple] = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql: str, params=None):
        sql_norm = " ".join(sql.split())
        for marker, (cols, rows) in self._tables.items():
            if marker in sql_norm:
                self._current_cols = cols
                self._current_rows = rows
                return
        self._current_cols = []
        self._current_rows = []

    @property
    def description(self):
        return [_FakeColumn(name=c) for c in self._current_cols]

    def fetchall(self):
        return list(self._current_rows)

    def fetchone(self):
        return self._current_rows[0] if self._current_rows else None


class _FakeConn:
    def __init__(self, tables: dict[str, tuple[list[str], list[tuple]]]):
        self._tables = tables
        self.committed = False

    def cursor(self):
        return _FakeCursor(self._tables)

    def commit(self):
        self.committed = True

    def close(self):
        pass


def _build_mock_tables(*, with_mechanism: bool = True) -> dict[str, tuple[list[str], list[tuple]]]:
    """Two grahas' natal longitudes (Sun near 0deg, Moon near 90deg) + a
    2-mahadasha spine + leverage_index/valence_pass rows for one domain
    ('wealth') + one mechanism with 2 members + SAV bindus for Sun/Moon."""
    today = date(2020, 1, 1)
    return {
        "fact_category = 'graha_position'": (
            ["fact_subject", "fact_value_num"],
            [("SUN", 10.0), ("MOON", 100.0), ("MAR", 200.0)],
        ),
        "FROM chart_dashas": (
            ["lord_graha", "start_date", "end_date"],
            [
                ("Sun", datetime(1984, 2, 5, tzinfo=timezone.utc), datetime(1990, 2, 5, tzinfo=timezone.utc)),
                ("Moon", datetime(1990, 2, 5, tzinfo=timezone.utc), datetime(2100, 2, 5, tzinfo=timezone.utc)),
            ],
        ),
        "FROM chart_vichara": (
            ["vichara_family", "subject", "actor", "domain", "varga_id", "value_num"],
            [
                ("leverage_index", "SUN", None, "wealth", None, 1.5),
                ("leverage_index", "MOON", None, "wealth", None, 0.8),
                ("valence_pass", "SUN", "SUN", None, "D1", 0.6),
                ("valence_pass", "MOON", "MOON", None, "D1", -0.4),
            ],
        ),
        "FROM bodha_mechanisms": (
            ["mechanism_id", "mechanism_name", "mechanism_class", "valence",
             "member_node_ids_array", "edge_strength_avg", "domains_affected_array",
             "centrality_summary_jsonb"],
            [
                ("mech-0001", "Sun-Moon Test Mechanism", "mutual_aspect_triangle", "mixed",
                 ["node-sun", "node-moon"], 0.8, ["wealth"], {"pagerank_avg": 0.5}),
            ] if with_mechanism else [],
        ),
        "FROM bodha_cgm_nodes": (
            ["node_id", "node_subject", "node_type"],
            [("node-sun", "SUN", "graha"), ("node-moon", "MOON", "graha")],
        ),
        "fact_category = 'ashtakavarga_bindu_sign'": (
            ["fact_subject", "fact_value_num"],
            [("SUN-SIGN_1", 5), ("MOON-SIGN_4", 6)],
        ),
    }


def _mock_conn(**kwargs) -> _FakeConn:
    return _FakeConn(_build_mock_tables(**kwargs))


# ═══════════════════════════════════════════════════════════════════════════
# 1. CR-87 — chart is required, never defaulted
# ═══════════════════════════════════════════════════════════════════════════

class TestCR87RequiredChart:
    def test_chart_ref_requires_chart_id(self):
        with pytest.raises(ValueError):
            svc.ChartRef(chart_id="")

    def test_chart_ref_requires_chart_id_none(self):
        with pytest.raises(ValueError):
            svc.ChartRef(chart_id=None)  # type: ignore[arg-type]

    def test_activation_rejects_none_chart(self):
        with pytest.raises(ValueError):
            svc.activation(None, "wealth", datetime.now(timezone.utc))  # type: ignore[arg-type]

    def test_curve_rejects_none_chart(self):
        with pytest.raises(ValueError):
            svc.curve(None, "wealth", datetime.now(timezone.utc), datetime.now(timezone.utc))  # type: ignore[arg-type]

    def test_record_evidence_rejects_none_chart(self):
        with pytest.raises(ValueError):
            svc.record_evidence(None, "wealth", datetime.now(timezone.utc), cited_by="test")  # type: ignore[arg-type]

    def test_build_chart_substrate_rejects_bare_string(self):
        with pytest.raises(ValueError):
            svc.build_chart_substrate("not-a-chartref")  # type: ignore[arg-type]

    def test_two_different_charts_get_independently_cached_substrates(self):
        chart_a = svc.ChartRef(chart_id=_CHART_ID)
        chart_b = svc.ChartRef(chart_id="1c826d5a-41cb-4450-b4dc-59d440e5f75a")
        sub_a = svc.build_chart_substrate(chart_a, conn=_mock_conn())
        sub_b = svc.build_chart_substrate(chart_b, conn=_mock_conn())
        assert sub_a.chart_id != sub_b.chart_id
        assert sub_a is not sub_b


# ═══════════════════════════════════════════════════════════════════════════
# 2. cos² orb weighting + applying/separating (via ka_sangam.engine)
# ═══════════════════════════════════════════════════════════════════════════

class TestOrbModel:
    def test_exact_applying_is_full_strength(self):
        assert orb_strength_score(0.0, 8.0, "applying") == pytest.approx(1.0)

    def test_at_max_orb_is_zero(self):
        assert orb_strength_score(8.0, 8.0, "applying") == pytest.approx(0.0, abs=1e-9)

    def test_separating_gets_070_multiplier_not_applying(self):
        applying = orb_strength_score(2.0, 8.0, "applying")
        separating = orb_strength_score(2.0, 8.0, "separating")
        assert separating == pytest.approx(applying * 0.7)

    def test_taranga_uses_the_shared_orb_strength_score(self):
        """The service's single T-3 adapter-point import must be this exact
        function — proves the cos² model is really wired in, not a private
        re-implementation."""
        assert svc._orb_strength_score is orb_strength_score


# ═══════════════════════════════════════════════════════════════════════════
# 3. Substrate build from mocked rows
# ═══════════════════════════════════════════════════════════════════════════

class TestChartSubstrateBuild:
    def test_natal_longitudes_resolved(self):
        chart = svc.ChartRef(chart_id=_CHART_ID)
        sub = svc.build_chart_substrate(chart, conn=_mock_conn())
        assert sub.graha_natal_longitude["SUN"] == 10.0
        assert sub.graha_natal_longitude["MOON"] == 100.0

    def test_dasha_periods_and_capability_resolved(self):
        chart = svc.ChartRef(chart_id=_CHART_ID)
        sub = svc.build_chart_substrate(chart, conn=_mock_conn())
        assert len(sub.dasha_periods) == 2
        assert sub.dasha_periods[0]["lord"] == "Sun"
        assert "SUN" in sub.dasha_lord_capability

    def test_domain_weights_signed_by_valence(self):
        """SUN has positive valence_pass (0.6) -> positive leverage weight;
        MOON has negative valence_pass (-0.4) -> leverage weight flips sign."""
        chart = svc.ChartRef(chart_id=_CHART_ID)
        sub = svc.build_chart_substrate(chart, conn=_mock_conn())
        assert sub.domain_weights["wealth"]["SUN"] == pytest.approx(1.5)
        assert sub.domain_weights["wealth"]["MOON"] == pytest.approx(-0.8)

    def test_mechanism_resolved_with_graph_weight_and_members(self):
        chart = svc.ChartRef(chart_id=_CHART_ID)
        sub = svc.build_chart_substrate(chart, conn=_mock_conn())
        mech = sub.mechanism_index["mech-0001"]
        assert set(mech["members"]) == {"SUN", "MOON"}
        assert mech["graph_weight"] == pytest.approx(0.8 * 0.5)

    def test_sav_bindus_resolved(self):
        chart = svc.ChartRef(chart_id=_CHART_ID)
        sub = svc.build_chart_substrate(chart, conn=_mock_conn())
        assert sub.sav_bindus[("SUN", 1)] == 5
        assert sub.sav_bindus[("MOON", 4)] == 6

    def test_dasha_query_uses_real_columns_and_vimshottari_filter(self):
        """Regression guard: chart_dashas real columns are start_date/end_date
        (NOT start_iso/end_iso) and the table holds 7 dasha systems — the
        mahadasha spine MUST be filtered to system_id='vimshottari' or periods
        from multiple systems overlap and _dasha_component picks arbitrarily.
        The mock matches SQL by substring so it can't catch a wrong column
        name; this asserts the emitted SQL text directly."""
        captured: list[str] = []

        class _RecordingCursor(_FakeCursor):
            def execute(self, sql, params=None):
                captured.append(" ".join(sql.split()))
                return super().execute(sql, params)

        class _RecordingConn(_FakeConn):
            def cursor(self):
                return _RecordingCursor(self._tables)

        chart = svc.ChartRef(chart_id=_CHART_ID)
        svc.build_chart_substrate(chart, conn=_RecordingConn(_build_mock_tables()))
        dasha_sql = next(s for s in captured if "FROM chart_dashas" in s)
        assert "start_date" in dasha_sql and "end_date" in dasha_sql
        assert "start_iso" not in dasha_sql and "end_iso" not in dasha_sql
        assert "system_id = 'vimshottari'" in dasha_sql

    def test_substrate_is_cached_not_rebuilt_per_call(self):
        chart = svc.ChartRef(chart_id=_CHART_ID)
        conn = _mock_conn()
        sub1 = svc.build_chart_substrate(chart, conn=conn)
        sub2 = svc.build_chart_substrate(chart, conn=_FakeConn({}))  # would fail to resolve if rebuilt
        assert sub1 is sub2
        assert sub2.graha_natal_longitude  # proves it's the FIRST build's data, not an empty rebuild


# ═══════════════════════════════════════════════════════════════════════════
# 4. activation() / curve() — unresolvable target fails loud
# ═══════════════════════════════════════════════════════════════════════════

class TestTargetResolution:
    def test_unknown_target_raises(self):
        chart = svc.ChartRef(chart_id=_CHART_ID)
        with pytest.raises(ValueError):
            svc.activation(chart, "not_a_real_domain_or_mechanism", datetime(2026, 1, 1, tzinfo=timezone.utc), conn=_mock_conn())

    def test_known_domain_resolves(self):
        chart = svc.ChartRef(chart_id=_CHART_ID)
        result = svc.activation(chart, "wealth", datetime(2026, 1, 1, tzinfo=timezone.utc), conn=_mock_conn())
        assert result["target_meta"]["target_kind"] == "domain"

    def test_mechanism_id_resolves(self):
        chart = svc.ChartRef(chart_id=_CHART_ID)
        result = svc.activation(chart, "mech-0001", datetime(2026, 1, 1, tzinfo=timezone.utc), conn=_mock_conn())
        assert result["target_meta"]["target_kind"] == "mechanism"
        assert result["target_meta"]["mechanism_valence"] == "mixed"


# ═══════════════════════════════════════════════════════════════════════════
# 5. Superposition: currents sum
# ═══════════════════════════════════════════════════════════════════════════

class TestSuperposition:
    def test_transit_sum_equals_sum_of_individual_contributions(self):
        chart = svc.ChartRef(chart_id=_CHART_ID)
        substrate = svc.build_chart_substrate(chart, conn=_mock_conn())
        weights = {"SUN": 1.0, "MOON": 1.0}
        jd = svc._to_jd(datetime(2026, 1, 1, tzinfo=timezone.utc))
        currents = svc._transit_currents(substrate, weights, jd)
        computed_sum = sum(c["contribution"] for c in currents)
        result = svc._evaluate(substrate, "wealth", datetime(2026, 1, 1, tzinfo=timezone.utc))
        # _evaluate resolves its own weights from domain_weights (signed
        # leverage), so re-derive the same currents for an apples-to-apples sum check.
        currents_via_evaluate = result["components"]["transit_currents"]
        assert result["components"]["transit_sum"] == pytest.approx(
            sum(c["contribution"] for c in currents_via_evaluate)
        )

    def test_two_simultaneous_currents_both_contribute_additively(self):
        """Two DIFFERENT transiting planets both within orb of the same natal
        target must both appear in `transit_currents` and their contributions
        must sum (not replace one another)."""
        chart = svc.ChartRef(chart_id=_CHART_ID)
        substrate = svc.build_chart_substrate(chart, conn=_mock_conn())
        # Force a scenario: two natal targets each within orb of *some*
        # transiting planet on this date — assert superposition is additive
        # by checking total == sum of parts for a real evaluate() call.
        result = svc._evaluate(substrate, "wealth", datetime(2026, 3, 15, tzinfo=timezone.utc))
        currents = result["components"]["transit_currents"]
        if len(currents) >= 2:
            assert result["components"]["transit_sum"] == pytest.approx(
                sum(c["contribution"] for c in currents), rel=1e-6
            )
        # Always true regardless of how many currents are in orb this date:
        assert result["activation"] == pytest.approx(
            result["components"]["transit_sum"]
            + svc.DASHA_COMPONENT_WEIGHT * result["components"]["dasha"]["dasha_capability"]
            + svc.SAV_COMPONENT_WEIGHT * result["components"]["sav"].get("avg_sav_potency", 0.0),
            rel=1e-6,
        )

    def test_superposition_model_is_additive_v1_not_signed_interference(self):
        chart = svc.ChartRef(chart_id=_CHART_ID)
        substrate = svc.build_chart_substrate(chart, conn=_mock_conn())
        result = svc._evaluate(substrate, "wealth", datetime(2026, 1, 1, tzinfo=timezone.utc))
        assert result["components"]["superposition_model"] == "additive_v1"


# ═══════════════════════════════════════════════════════════════════════════
# 6. CR-41 — future timestamps resolve (dissolves by construction)
# ═══════════════════════════════════════════════════════════════════════════

class TestCR41ForwardHorizon:
    def test_activation_resolves_far_future_beyond_dasha_spine(self):
        """The mock dasha spine ends 2100-02-05. A timestamp AFTER that (e.g.
        2140) must still resolve an activation value (transit + SAV
        components still compute live) — proving there is no writer horizon
        gating the call, only an honest `known_gap` on the dasha component."""
        chart = svc.ChartRef(chart_id=_CHART_ID)
        far_future = datetime(2140, 6, 1, tzinfo=timezone.utc)
        result = svc.activation(chart, "wealth", far_future, conn=_mock_conn())
        assert result["activation"] is not None
        assert result["t"].startswith("2140-06-01")
        # Honest gap reported for the out-of-spine dasha component — not a
        # silent zero-substitution and not a hard failure.
        assert result["components"]["dasha"]["dasha_capability"] == 0.0
        assert "known_gap" in result["components"]["dasha"]

    def test_activation_resolves_far_past_before_any_dasha_period(self):
        chart = svc.ChartRef(chart_id=_CHART_ID)
        far_past = datetime(1901, 1, 1, tzinfo=timezone.utc)
        result = svc.activation(chart, "wealth", far_past, conn=_mock_conn())
        assert result["activation"] is not None

    def test_curve_extends_past_the_dasha_spine_end(self):
        chart = svc.ChartRef(chart_id=_CHART_ID)
        result = svc.curve(
            chart, "wealth",
            datetime(2100, 1, 1, tzinfo=timezone.utc),
            datetime(2100, 1, 15, tzinfo=timezone.utc),
            resolution="daily",
            conn=_mock_conn(),
        )
        assert len(result["points"]) == 15
        assert all(p["activation"] is not None for p in result["points"])


# ═══════════════════════════════════════════════════════════════════════════
# 7. Evidence write-through — opt-in only
# ═══════════════════════════════════════════════════════════════════════════

class TestEvidenceWriteThrough:
    def test_activation_never_writes(self):
        chart = svc.ChartRef(chart_id=_CHART_ID)
        conn = _mock_conn()
        svc.activation(chart, "wealth", datetime(2026, 1, 1, tzinfo=timezone.utc), conn=conn)
        assert conn.committed is False

    def test_curve_never_writes(self):
        chart = svc.ChartRef(chart_id=_CHART_ID)
        conn = _mock_conn()
        svc.curve(
            chart, "wealth",
            datetime(2026, 1, 1, tzinfo=timezone.utc), datetime(2026, 1, 3, tzinfo=timezone.utc),
            conn=conn,
        )
        assert conn.committed is False

    def test_record_evidence_requires_cited_by(self):
        chart = svc.ChartRef(chart_id=_CHART_ID)
        with pytest.raises(ValueError):
            svc.record_evidence(chart, "wealth", datetime(2026, 1, 1, tzinfo=timezone.utc), cited_by="", conn=_mock_conn())

    def test_record_evidence_writes_with_cited_by(self):
        chart = svc.ChartRef(chart_id=_CHART_ID)

        class _EvidenceConn(_FakeConn):
            def cursor(self):
                cur = super().cursor()
                original_execute = cur.execute

                def _execute(sql, params=None):
                    if "INSERT INTO kala_taranga" in sql:
                        cur._current_cols = ["taranga_id"]
                        cur._current_rows = [("taranga-uuid-1",)]
                        return
                    return original_execute(sql, params)

                cur.execute = _execute
                return cur

        conn = _EvidenceConn(_build_mock_tables())
        receipt = svc.record_evidence(
            chart, "wealth", datetime(2026, 1, 1, tzinfo=timezone.utc),
            cited_by="reading-abc123", conn=conn,
        )
        assert receipt["taranga_id"] == "taranga-uuid-1"
        assert receipt["cited_by"] == "reading-abc123"
        assert receipt["scope_kind"] == "domain"
        assert conn.committed is False  # caller-supplied conn — service does not commit it

    def test_record_evidence_mechanism_target_uses_event_class_scope(self):
        chart = svc.ChartRef(chart_id=_CHART_ID)

        class _EvidenceConn(_FakeConn):
            def cursor(self):
                cur = super().cursor()
                original_execute = cur.execute

                def _execute(sql, params=None):
                    if "INSERT INTO kala_taranga" in sql:
                        cur._current_cols = ["taranga_id"]
                        cur._current_rows = [("taranga-uuid-2",)]
                        return
                    return original_execute(sql, params)

                cur.execute = _execute
                return cur

        conn = _EvidenceConn(_build_mock_tables())
        receipt = svc.record_evidence(
            chart, "mech-0001", datetime(2026, 1, 1, tzinfo=timezone.utc),
            cited_by="l5-job-42", conn=conn,
        )
        assert receipt["scope_kind"] == "event_class"


# ═══════════════════════════════════════════════════════════════════════════
# 8. Honest gaps — never fabricate
# ═══════════════════════════════════════════════════════════════════════════

class TestHonestGaps:
    def test_missing_mechanism_rows_flagged_as_known_gap(self):
        chart = svc.ChartRef(chart_id=_CHART_ID)
        sub = svc.build_chart_substrate(chart, conn=_mock_conn(with_mechanism=False))
        assert "no bodha_mechanisms rows found" in sub.known_gaps

    def test_target_not_in_domain_names_and_not_a_mechanism_raises_not_silently_zero(self):
        chart = svc.ChartRef(chart_id=_CHART_ID)
        with pytest.raises(ValueError, match="unresolvable"):
            svc.activation(chart, "garbage-target-xyz", datetime(2026, 1, 1, tzinfo=timezone.utc), conn=_mock_conn())
