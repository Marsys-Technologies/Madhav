"""Finite synthetic source/bind regressions; SQL execution is a separate seam."""
from __future__ import annotations

import pytest

from brahmagyan.verification_vocab import is_verified
from .test_msr_single_pass_boundary import WRITERS, load_detector, load_projection

EXPECTED_RANKS = {
    "two_pass_verified": 3, "classical_match": 2, "single_pass": 1, "pass": 2,
    "documented_approximation": 1, "single": 1, "divergent_flagged": 0,
}


def _bound_model(ranks, signal, facts):
    """Model the SQL's recognized maximum, not an executed-SQL claim."""
    if signal == "divergent_flagged":
        return 1
    recognized = [ranks[f] for f in facts if f in ranks]
    return int(bool(recognized) and ranks.get(signal, -1) > max(recognized))


@pytest.mark.parametrize(("signal", "facts", "expected"), [
    ("single", ["single_pass"], 0),
    ("single_pass", ["single"], 0),
    ("single_pass", ["single_pass"], 0),
    ("single", ["single"], 0),
    ("classical_match", ["single_pass"], 1),
    ("classical_match", ["single"], 1),
    ("pass", ["single_pass"], 1),
    ("two_pass_verified", ["single_pass"], 1),
    ("single", ["single_pass", "classical_match"], 0),
    ("single_pass", ["single", "two_pass_verified"], 0),
    ("classical_match", ["single_pass", "single", "classical_match"], 0),
    ("two_pass_verified", ["single_pass", "single", "classical_match"], 1),
    ("classical_match", ["single_pass", "single_pass", "fixture_unknown"], 1),
    ("single_pass", ["divergent_flagged"], 1),
    ("documented_approximation", ["single_pass"], 0),
    ("divergent_flagged", ["two_pass_verified"], 1),
    ("fixture_unknown", ["single_pass"], 0),
    (None, ["single_pass"], 0),
    ("single_pass", [], 0),
    ("single_pass", [None, "fixture_unknown"], 0),
    ("classical_match", ["fixture_unknown", "single_pass"], 1),
])
def test_bound_shared_rank_model_has_exact_spelling_independent_results(signal, facts, expected):
    scope = load_detector(WRITERS / "bo_pramana_mapa.py")
    ranks = dict(scope["_VERIFICATION_TIER_RANKS"])
    assert ranks == EXPECTED_RANKS
    assert _bound_model(ranks, signal, facts) == expected


@pytest.mark.parametrize("spelling", ["single", "single_pass"])
def test_new_annotation_and_raw_historical_fact_share_unverified_rank(spelling):
    project = load_projection(WRITERS / "bo_laksana.py")
    row = project({"fact_id": "fixture-fact", "fact_category": "fixture-category",
                   "fact_key": "fixture-key", "verification_pass_status": spelling,
                   "fact_value_jsonb": {}}, valid_fact_ids={"fixture-fact"})
    scope = load_detector(WRITERS / "bo_pramana_mapa.py")
    ranks = dict(scope["_VERIFICATION_TIER_RANKS"])
    assert row["verification_pass_status"] == "single"
    assert row["epistemic_tier"] == spelling
    assert ranks[spelling] == ranks[row["verification_pass_status"]] == 1
    assert not is_verified(spelling) and not is_verified(row["verification_pass_status"])


def test_consumer_uses_one_shared_rank_map_and_preserves_query_bind_order():
    scope = load_detector(WRITERS / "bo_pramana_mapa.py")
    sql = scope["_TIER_INVERSION_SQL"]
    assert sql.count("unnest(%s::text[], %s::int[])") == 1
    assert sql.count("LEFT JOIN rank_map fr ON fr.status = cf.verification_pass_status") == 1
    assert sql.count("LEFT JOIN rank_map sr ON sr.status = s.verification_pass_status") == 1
    assert "max(COALESCE(fr.rk, -1))" in sql
    assert "f.resolved_facts > 0" in sql and "f.max_fact_rk >= 0" in sql
    assert "verification_pass_status IS DISTINCT FROM 'divergent_flagged'" in sql


@pytest.mark.parametrize("failure_call", [1, 2])
def test_sql_failure_is_unevaluable_not_zero(failure_call):
    scope = load_detector(WRITERS / "bo_pramana_mapa.py")

    class FailingConnection:
        calls = 0

        def execute(self, sql, params):
            self.calls += 1
            if self.calls == failure_call:
                raise RuntimeError("synthetic-sql-refusal")
            return self

        def fetchone(self):
            return (0,)

    result = scope["count_divergent_signals"](FailingConnection(), "fixture-chart")
    assert result["count"] is None
    assert result["error"] == "synthetic-sql-refusal"


def test_explicit_and_inversion_terms_remain_separate_and_add_once():
    scope = load_detector(WRITERS / "bo_pramana_mapa.py")

    class Connection:
        def __init__(self):
            self.calls = []

        def execute(self, sql, params):
            self.calls.append((sql, params))
            return self

        def fetchone(self):
            return (2 if len(self.calls) == 1 else 3,)

    conn = Connection()
    result = scope["count_divergent_signals"](conn, "fixture-chart")
    assert result["count"] == 5 and result["error"] is None
    assert result["terms"]["explicitly_stamped_divergent"] == 2
    assert result["terms"]["l1_verification_tier_inversion"] == 3
    assert conn.calls == [
        (scope["_EXPLICIT_DIVERGENT_SQL"], ["fixture-chart"]),
        (scope["_TIER_INVERSION_SQL"], [list(EXPECTED_RANKS), list(EXPECTED_RANKS.values()), "fixture-chart"]),
    ]
