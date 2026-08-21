"""
test_mi_pariksha_discovery_scored.py — F-143 write-path cover.

`mimamsa_discoveries.n_support` for an emergent_law row is `len(credits)`: the number
of mimamsa_attribution rows for a (signal_id, dimension) pair. An attribution row is an
ASSIGNMENT of analytic credit for one prediction↔event match — and mi_pramana writes a
calibration row for EVERY window overlap, including matches whose verdict is UNRESOLVED
(observation window not elapsed; the adjudication can still flip) or FALSE_ALARM (control
window). Downstream, mi_darshana graded `n_support >= 5` as 'empirical'.

These tests pin the write-path half of the fix: the discovery substep must record the
outcome-adjudicated subset (`evidence_refs.n_scored_matches`) separately from the raw
assignment count, so mi_darshana has a real quantity to grade on instead of a proxy.
"""
from __future__ import annotations

import json

from pipeline.orchestrator.writers.mi_pariksha import MiParikshaWriter

NATIVE_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"


class _FakeCursor:
    def __init__(self, conn):
        self._conn = conn
        self._result = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        if "FROM mimamsa_attribution a" in s:
            self._conn.attribution_sql = s
            self._result = list(self._conn.attribution_rows)
        elif s.startswith("DELETE"):
            self._result = []
        else:
            self._result = []

    def fetchall(self):
        return list(self._result)

    def fetchone(self):
        return self._result[0] if self._result else None

    def executemany(self, sql, params_list):
        if "INSERT INTO mimamsa_discoveries" in " ".join(sql.split()):
            self._conn.inserted_rows.extend(params_list)


class _FakeConn:
    def __init__(self, attribution_rows):
        self.attribution_rows = list(attribution_rows)
        self.inserted_rows: list[tuple] = []
        self.attribution_sql = ""

    def cursor(self, row_factory=None):
        return _FakeCursor(self)


def _att(match_id, verdict, credit=0.4, signal_id="sig1", dimension="timing"):
    return {
        "signal_id": signal_id,
        "family_id": "fam1",
        "dimension": dimension,
        "credit_blame": credit,
        "match_id": match_id,
        "composite_verdict": verdict,
    }


def _run(attribution_rows):
    conn = _FakeConn(attribution_rows)
    writer = MiParikshaWriter()
    result = writer._substep_discovery(conn, NATIVE_CHART_ID, t0=0.0)
    return conn, result


# Insert-tuple offsets mirror the INSERT column list in _substep_discovery.
STATEMENT, EVIDENCE_REFS, STRENGTH, N_SUPPORT = 3, 4, 5, 6


def _refs(row):
    return json.loads(row[EVIDENCE_REFS])


def test_scored_count_excludes_unresolved_and_false_alarm_matches():
    """The production shape: many assignments, few adjudicated outcomes."""
    rows = (
        [_att(f"m{i}", "UNRESOLVED") for i in range(8)]
        + [_att("mc", "FALSE_ALARM")]
        + [_att("ma", "CONFIRMED"), _att("mb", "PARTIAL"), _att("md", "REFUTED")]
    )
    conn, result = _run(rows)

    assert result.rows_inserted == 1
    row = conn.inserted_rows[0]
    refs = _refs(row)
    assert row[N_SUPPORT] == 12, "n_support keeps its established meaning: assignment rows"
    assert refs["n"] == 12
    assert refs["n_distinct_matches"] == 12
    assert refs["n_scored_matches"] == 3, "only CONFIRMED/PARTIAL/REFUTED are adjudicated"


def test_scored_matches_are_deduplicated_by_match_id():
    """A signal appearing twice in one match's driving_signals yields two attribution
    rows for the same match — evidence of one outcome, not two."""
    conn, _ = _run([_att("m1", "CONFIRMED"), _att("m1", "CONFIRMED"), _att("m2", "PARTIAL")])
    refs = _refs(conn.inserted_rows[0])
    assert refs["n"] == 3
    assert refs["n_distinct_matches"] == 2
    assert refs["n_scored_matches"] == 2


def test_no_adjudicated_matches_reports_zero_not_absent():
    """An honest zero, so the downstream grader can tell 'measured, none' apart from
    'never measured' (which is what a missing key means)."""
    conn, _ = _run([_att(f"m{i}", "UNRESOLVED") for i in range(6)])
    refs = _refs(conn.inserted_rows[0])
    assert refs["n_scored_matches"] == 0
    assert refs["n"] == 6


def test_statement_does_not_present_assignment_count_as_observations():
    """§N.7: 'n=41' read as 41 observations. The statement must name what the counts are."""
    conn, _ = _run([_att(f"m{i}", "CONFIRMED") for i in range(5)])
    statement = conn.inserted_rows[0][STATEMENT]
    assert "attribution assignments" in statement
    assert "outcome-adjudicated" in statement
    assert "n=5" not in statement


def test_verdict_case_and_null_are_handled():
    """composite_verdict is written UPPERCASE by mi_pramana._verdict_v2; a lowercase or
    NULL value (LEFT JOIN miss) must not be silently counted as adjudicated evidence —
    lowercase is normalized, NULL is excluded."""
    conn, _ = _run([
        _att("m1", "confirmed"), _att("m2", None), _att("m3", "PARTIAL"), _att("m4", "UNRESOLVED"),
    ])
    refs = _refs(conn.inserted_rows[0])
    assert refs["n_scored_matches"] == 2


def test_discovery_selection_is_deterministically_ordered():
    """The 20-row cap used to keep whichever groups an unordered scan yielded first."""
    conn, _ = _run([_att("m1", "CONFIRMED")] * 3)
    assert "ORDER BY a.signal_id, a.dimension, a.match_id" in conn.attribution_sql


def test_evidence_refs_discloses_n_support_semantics():
    conn, _ = _run([_att(f"m{i}", "CONFIRMED") for i in range(5)])
    refs = _refs(conn.inserted_rows[0])
    assert "NOT independently scored outcomes" in refs["n_support_semantics"]
    assert refs["adjudicated_verdicts"] == ["CONFIRMED", "PARTIAL", "REFUTED"]
