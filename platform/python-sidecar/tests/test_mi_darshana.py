"""
test_mi_darshana.py — hermetic tests for the L5 Mīmāṃsā insight-retrieval writer.

Focus: the confidence-interval computation in `_substep_insight_units` must not
choke on DB numeric values. `observed_rate` and `brier_score` arrive as
`decimal.Decimal` for a calibrated chart (the native); Abhinandan's were NULL,
so they fell through to a float default and masked a `Decimal - float` TypeError
at build time. These tests feed a `Decimal` observed value through a fake conn
(no real DB) and assert: no TypeError, correct float conf_lo/conf_hi bounds, and
JSON-serializable provenance. The NULL/None path is kept for regression cover.
"""
from __future__ import annotations

from decimal import Decimal

from pipeline.orchestrator.writers.mi_darshana import MiDarshanaWriter

NATIVE_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"


# ── DB-path fakes (model only the queries _substep_insight_units issues) ──────

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
        if "information_schema.tables" in s:
            # Section-5 bodha tables absent → verdict_object branch skipped.
            self._result = []
        elif "FROM mimamsa_reliability" in s:
            self._result = list(self._conn.reliability_rows)
        elif "FROM mimamsa_manifestation_grammar" in s:
            self._result = []
        elif "FROM mimamsa_discoveries" in s:
            self._result = []
        elif "FROM mimamsa_load_bearing" in s:
            self._result = []
        else:
            self._result = []

    def fetchall(self):
        return list(self._result)

    def fetchone(self):
        return self._result[0] if self._result else None

    def executemany(self, sql, params_list):
        if "INSERT INTO mimamsa_insight_units" in " ".join(sql.split()):
            self._conn.inserted_rows.extend(params_list)


class _FakeConn:
    def __init__(self, reliability_rows):
        self.reliability_rows = list(reliability_rows)
        self.inserted_rows: list[tuple] = []

    def cursor(self, row_factory=None):
        return _FakeCursor(self)


def _run(reliability_rows):
    conn = _FakeConn(reliability_rows)
    writer = MiDarshanaWriter()
    result = writer._substep_insight_units(conn, NATIVE_CHART_ID, t0=0.0)
    return conn, result


# Insert-tuple column offsets (mirror the INSERT column list in the writer).
STATEMENT, RANK_CONSEQUENCE, CONFIDENCE_BAND = 6, 7, 8
PROVENANCE_CHAIN = 14


def _calibrated_row(observed, brier, n=5):
    return {
        "stratum_key": "career|near|high",
        "predicted_prob_bin": "0.7-0.8",
        "observed_rate": observed,
        "n": n,
        "brier_score": brier,
        "evidence_grade": "empirical",
        "held_out_validity": True,
    }


# ── tests ─────────────────────────────────────────────────────────────────────

def test_decimal_observed_no_typeerror_and_correct_bounds():
    """The native path: observed_rate + brier_score are Decimal. Must not raise
    and must produce correct float confidence bounds."""
    import json

    conn, result = _run([_calibrated_row(Decimal("0.73"), Decimal("0.12"))])

    assert result.rows_inserted == 1
    row = conn.inserted_rows[0]
    # conf_lo = 0.73 - 0.1 = 0.63 ; conf_hi = 0.73 + 0.1 = 0.83
    assert row[CONFIDENCE_BAND] == "[0.63,0.83)"
    assert row[RANK_CONSEQUENCE] == 0.73
    assert isinstance(row[RANK_CONSEQUENCE], float)
    # provenance JSON must be serializable and carry a float (not Decimal) brier
    prov = json.loads(row[PROVENANCE_CHAIN])
    assert prov["brier"] == 0.12
    assert isinstance(prov["brier"], float)
    assert "73.0%" in row[STATEMENT]


def test_decimal_clamps_at_upper_bound():
    """High observed rate clamps conf_hi at 1.0 without Decimal arithmetic."""
    conn, _ = _run([_calibrated_row(Decimal("0.95"), Decimal("0.05"))])
    row = conn.inserted_rows[0]
    # conf_lo = 0.85 ; conf_hi = min(1.0, 1.05) = 1.0
    assert row[CONFIDENCE_BAND] == "[0.85,1.0)"


def test_none_observed_falls_back_to_default():
    """Regression cover for the pre-existing (Abhinandan) NULL path."""
    import json

    conn, result = _run([_calibrated_row(None, None)])

    assert result.rows_inserted == 1
    row = conn.inserted_rows[0]
    # obs defaults to 0.5 → conf_lo 0.4, conf_hi 0.6
    assert row[CONFIDENCE_BAND] == "[0.4,0.6)"
    assert row[RANK_CONSEQUENCE] == 0.5
    prov = json.loads(row[PROVENANCE_CHAIN])
    assert prov["brier"] is None
    assert "insufficient events" in row[STATEMENT]


def test_low_n_stratum_skipped():
    """n < 2 strata produce no insight unit (no rows, clean return)."""
    conn, result = _run([_calibrated_row(Decimal("0.73"), Decimal("0.12"), n=1)])
    assert result.rows_inserted == 0
    assert conn.inserted_rows == []
