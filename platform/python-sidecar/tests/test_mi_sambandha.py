"""
test_mi_sambandha.py — hermetic test for the F-35 earned-signal fix.

mi_sambandha's grade predicate (n = opp, the raw assignment count) granted
"empirical" on assignment count alone, with zero regard for whether any
assignment carries a scored composite_verdict ('confirmed'|'partial'|'denied' —
platform/migrations/348_mimamsa_pramana.sql:17; 'pending'/no-row are NOT scored).
This drives run() with 9 assignments to one channel, none of them scored (the
LEFT JOIN finds no mimamsa_calibration row for any of them — mirroring F-35's
live repro chart 1c826d5a, calibration_summary.total_matches=0), and asserts
the grammar row grades 'assignment_only', not 'empirical'.
"""
from __future__ import annotations

from pipeline.orchestrator.writers.mi_sambandha import MiSambandhaWriter

NATIVE_CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"

# Mirror the INSERT column list in mi_sambandha.py post-fix (§2a/§2c add
# scored_count at index 7, shifting evidence_grade from 12 to 13).
CHANNEL_ID, EVIDENCE_GRADE = 3, 13


class _FakeCursor:
    def __init__(self, conn):
        self._conn = conn
        self._result: list = []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        s = " ".join(sql.split())
        if "FROM mimamsa_manifestation_sets" in s:
            self._result = list(self._conn.mset_rows)
        else:
            self._result = []

    def fetchall(self):
        return list(self._result)

    def executemany(self, sql, params_list):
        if "INSERT INTO mimamsa_manifestation_grammar" in " ".join(sql.split()):
            self._conn.inserted_rows.extend(params_list)


class _FakeConn:
    def __init__(self, mset_rows):
        self.mset_rows = list(mset_rows)
        self.inserted_rows: list[tuple] = []

    def cursor(self, row_factory=None):
        return _FakeCursor(self)


class _FakeCtx:
    def __init__(self, chart_id, db_conn, dry_run=False):
        self.config = {"chart_id": chart_id}
        self.db_conn = db_conn
        self.dry_run = dry_run


def _unscored_assignment(i, channel_id="ch_career_verbal", domain="career"):
    # LEFT JOIN mimamsa_calibration finds no row -> both fields NULL.
    return {
        "prediction_id": f"pred_{i}",
        "channel_id": channel_id,
        "domain": domain,
        "is_literal": True,
        "composite_verdict": None,
        "manifestation_channel": None,
    }


def test_nine_unscored_assignments_do_not_earn_empirical_grade():
    """FAILS TODAY: opp=9 >= 5 -> grade='empirical' with zero scored outcomes.
    AFTER FIX: grade must be 'assignment_only' -- 'empirical' is reserved for
    >=5 SCORED (confirmed/partial/denied) outcomes, not raw assignment count."""
    rows = [_unscored_assignment(i) for i in range(9)]
    conn = _FakeConn(rows)
    ctx = _FakeCtx(NATIVE_CHART_ID, conn, dry_run=False)

    MiSambandhaWriter().run(ctx)

    grammar_row = next(r for r in conn.inserted_rows if r[CHANNEL_ID] == "ch_career_verbal")
    assert grammar_row[EVIDENCE_GRADE] == "assignment_only"


def test_five_scored_assignments_do_earn_empirical_grade():
    """Boundary/regression guard: >=5 SCORED outcomes must still grade
    'empirical' -- this fix narrows the gate, it must not break the genuine
    positive case. 3 confirmed + 2 denied = 5 scored, non-matching channel on
    the denied ones so fire_count stays low (irrelevant to the grade check)."""
    rows = (
        [{"prediction_id": f"c{i}", "channel_id": "ch_career_verbal", "domain": "career",
          "is_literal": True, "composite_verdict": "confirmed",
          "manifestation_channel": "ch_career_verbal"} for i in range(3)]
        + [{"prediction_id": f"d{i}", "channel_id": "ch_career_verbal", "domain": "career",
            "is_literal": True, "composite_verdict": "denied",
            "manifestation_channel": "ch_career_material"} for i in range(2)]
    )
    conn = _FakeConn(rows)
    ctx = _FakeCtx(NATIVE_CHART_ID, conn, dry_run=False)

    MiSambandhaWriter().run(ctx)

    grammar_row = next(r for r in conn.inserted_rows if r[CHANNEL_ID] == "ch_career_verbal")
    assert grammar_row[EVIDENCE_GRADE] == "empirical"
