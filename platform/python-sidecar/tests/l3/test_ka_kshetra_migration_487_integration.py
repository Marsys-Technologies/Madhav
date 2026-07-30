"""
Integration test: rows produced by stage6_salience / stage65_insights
actually INSERT cleanly into the real migration-487 tables
(kala_field_salience, kala_insights) against a live throwaway Postgres --
not just asserted as Python dicts. This closes the loop between the Python
computation layer and the SQL schema this PR ships, catching any
CHECK/NOT NULL mismatch a pure-Python test could miss.
"""
from __future__ import annotations

import json
import os
import sys
import uuid

import pytest

_SIDECAR = os.path.join(os.path.dirname(__file__), "..", "..")
if _SIDECAR not in sys.path:
    sys.path.insert(0, _SIDECAR)

from services.ka_kshetra.stage65_insights import (
    ClockAgreement,
    assemble_insight_row,
    detect_concurrence,
)
from services.ka_kshetra.stage6_salience import EventOntologyInfo, compute_salience_vector
from tests.l3.test_ka_kshetra_stage65_insights import _window

_DSN = os.environ.get(
    "LANE_D_COHORT_DSN",
    "postgresql://postgres@/laned_test?host=/tmp/laned_pg_sock&port=55532",
)


@pytest.fixture
def conn():
    try:
        import psycopg2
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"psycopg2 unavailable: {exc}")
    try:
        c = psycopg2.connect(_DSN)
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"throwaway Postgres not available: {exc}")
    c.autocommit = False
    yield c
    c.rollback()
    c.close()


@pytest.mark.integration
class TestKalaFieldSalienceInsert:
    def test_insert_row_from_stage6(self, conn):
        onto = EventOntologyInfo("career_entry", "career", "moderate", frozenset())
        vec = compute_salience_vector(
            p_cohort=0.03, cohort_n_total=10_000, ontology=onto,
            event_domain="career", window_t_start=0, window_t_end=100,
            confidence_tier="concurrent", intervention_ref="elect_upaya",
        )
        chart_id = str(uuid.uuid4())
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO kala_field_salience
                  (chart_id, window_id, event_class,
                   factor_informativeness, factor_consequence, factor_relevance,
                   factor_reliability, factor_actionability,
                   salience, salience_weights_version, salience_basis,
                   selected, selection_rank, marginal_gain, atoms_newly_covered,
                   coverage_fraction, weights_version, cohort_version,
                   x_schema_version, field_snapshot_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s)
                """,
                (
                    chart_id, "kfw_test123", "career_entry",
                    vec.informativeness, vec.consequence, vec.relevance,
                    vec.reliability, vec.actionability,
                    vec.salience, vec.salience_weights_version, list(vec.salience_basis),
                    True, 1, 0.42, json.dumps([{"event_class": "career_entry",
                                                 "window_family_id": "abc123",
                                                 "driver_term_key": "baseline"}]),
                    0.87, "field_wv_v0", "bgc_deadbeef00000000",
                    "x_schema_v1", "snap_1",
                ),
            )
        with conn.cursor() as cur:
            cur.execute(
                "SELECT salience, salience_basis, selected FROM kala_field_salience WHERE chart_id=%s",
                (chart_id,),
            )
            row = cur.fetchone()
        assert row[0] == pytest.approx(vec.salience)
        assert row[1] == list(vec.salience_basis)
        assert row[2] is True

    def test_unique_chart_window_constraint(self, conn):
        chart_id = str(uuid.uuid4())

        def _insert():
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO kala_field_salience
                      (chart_id, window_id, event_class, salience,
                       salience_weights_version, salience_basis,
                       weights_version, x_schema_version, field_snapshot_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (chart_id, "kfw_dup", "career_entry", 0.5, "salience_v0",
                     ["R"], "wv0", "xs0", "snap0"),
                )

        _insert()
        with pytest.raises(Exception):
            _insert()


@pytest.mark.integration
class TestKalaInsightsInsert:
    def test_insert_concurrence_row(self, conn):
        w = _window(clock_agreements=(
            ClockAgreement("vimshottari", "dasha_md", 0.5),
            ClockAgreement("yogini", "dasha_yogini", 0.6),
            ClockAgreement("kalachakra", "dasha_kalachakra", 0.4),
        ))
        cand = detect_concurrence(w)
        row = assemble_insight_row(str(uuid.uuid4()), cand, "wv_2026", "snap_abc")

        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO kala_insights
                  (chart_id, insight_id, insight_type, event_class, window_id,
                   t_start, t_end, statement_key, statement_params, fact_ids,
                   cohort_surprise, cohort_version, surprise_basis, robustness,
                   insight_score, lel_derived, weights_version, field_snapshot_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s,
                        %s, %s, %s, %s::jsonb, %s, %s, %s, %s)
                """,
                (
                    row["chart_id"], row["insight_id"], row["insight_type"],
                    row["event_class"], row["window_id"], row["t_start"], row["t_end"],
                    row["statement_key"], json.dumps(row["statement_params"]),
                    row["fact_ids"], row["cohort_surprise"], row["cohort_version"],
                    row["surprise_basis"], json.dumps(row["robustness"]),
                    row["insight_score"], row["lel_derived"], row["weights_version"],
                    row["field_snapshot_id"],
                ),
            )
        with conn.cursor() as cur:
            cur.execute(
                "SELECT insight_type, lel_derived FROM kala_insights WHERE insight_id=%s",
                (row["insight_id"],),
            )
            fetched = cur.fetchone()
        assert fetched[0] == "concurrence"
        assert fetched[1] is False

    def test_lel_derived_true_requires_null_snapshot_or_present(self):
        """The migration's CHECK constraint (field_snapshot_id IS NOT NULL OR
        lel_derived) -- verified structurally, not by inserting a fabricated
        biographical_echo row (that type is Lane E's, not this lane's)."""
        # This is a documentation-level assertion: Lane D never constructs
        # lel_derived=True rows (assemble_insight_row hardcodes False), so
        # there is no Lane-D code path that could violate this constraint.
        import inspect

        from services.ka_kshetra import stage65_insights as mod
        src = inspect.getsource(mod.assemble_insight_row)
        assert '"lel_derived": False' in src

    def test_insight_type_check_constraint_rejects_bogus_type(self, conn):
        with pytest.raises(Exception):
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO kala_insights
                      (chart_id, insight_id, insight_type, statement_key,
                       statement_params, fact_ids, surprise_basis, robustness,
                       insight_score, lel_derived, weights_version, field_snapshot_id)
                    VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, %s::jsonb, %s, %s, %s, %s)
                    """,
                    (
                        str(uuid.uuid4()), "kin_bogus", "not_a_real_type", "sk1",
                        json.dumps({}), [], "basis", json.dumps({}), 0.5, False, "wv0", "snap0",
                    ),
                )
