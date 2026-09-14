"""DP-SD-017 BHAV-P0: destructive rebuild safety for ka_bhavishya_lekha."""
from __future__ import annotations

from copy import deepcopy
from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from pipeline.orchestrator.writers.ka_bhavishya_lekha import KaBhavishyaLekhaWriter


CHART_ID = "chart-bhavishya-p0"
SIGNAL_ID = "11111111-1111-4111-8111-111111111111"
PEAK_DATE = date.today() + timedelta(days=365)


def _darshana_row(*, signal_id=SIGNAL_ID, peak_date=PEAK_DATE, convergence_id="conv-1"):
    return {
        "convergence_id": convergence_id,
        "signal_id": signal_id,
        "net_label": "auspicious_strong",
        "effective_score": 0.78,
        "peak_date": peak_date,
        "window_start": peak_date - timedelta(days=14),
        "window_end": peak_date + timedelta(days=14),
        "narrative": "candidate",
        "obstruction_summary": None,
        "confidence_label": "high",
        "rarity_years": 12.0,
        "mode": "vimshottari",
        "tier_basis": "relative_uncalibrated",
        "domain": "career",
    }


def _outcome(*, signal_id=SIGNAL_ID, peak_date=PEAK_DATE, notes="observed"):
    return {
        "signal_id": signal_id,
        "peak_date": peak_date,
        "outcome_recorded": True,
        "outcome_notes": notes,
    }


class _Cursor:
    def __init__(self, conn):
        self.conn = conn
        self._rows = []
        self._one = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=None):
        statement = " ".join(sql.split())
        self.conn.sql.append(statement)
        if "SELECT signal_id, peak_date, outcome_recorded, outcome_notes" in statement:
            self._rows = deepcopy(self.conn.outcomes)
        elif "FROM information_schema.columns" in statement:
            self._one = (1,)
        elif "FROM kala_darshana kd" in statement:
            self._rows = deepcopy(self.conn.candidates)
        elif "FROM bodha_msr_signals" in statement:
            self._rows = [
                {"signal_id": row["signal_id"], "signal_type_id": "raja_yoga"}
                for row in self.conn.candidates
                if row["signal_id"] is not None
            ]
        elif statement.startswith("DELETE FROM kala_bhavishya"):
            self.conn.working_rows = []

    def executemany(self, sql, rows):
        statement = " ".join(sql.split())
        self.conn.sql.append(statement)
        if self.conn.fail_insert:
            raise RuntimeError("injected insert failure")
        self.conn.inserted_rows = list(rows)
        self.conn.working_rows = deepcopy(self.conn.inserted_rows)

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._one


class _Connection:
    """Tiny transaction-shaped fake; rollback remains owned by the writer's caller."""

    def __init__(self, *, outcomes=None, candidates=None, fail_insert=False):
        self.outcomes = list(outcomes or [])
        self.candidates = list(candidates or [])
        self.fail_insert = fail_insert
        self.sql = []
        self.inserted_rows = []
        self.original_rows = [{"existing": "projection"}]
        self.working_rows = deepcopy(self.original_rows)
        self.commit_calls = 0
        self.rollback_calls = 0

    def cursor(self, **_kwargs):
        return _Cursor(self)

    def commit(self):
        self.commit_calls += 1

    def rollback(self):
        self.rollback_calls += 1
        self.working_rows = deepcopy(self.original_rows)


def _run(conn):
    ctx = SimpleNamespace(db_conn=conn, config={"chart_id": CHART_ID})
    return KaBhavishyaLekhaWriter().run(ctx)


def _dml(conn):
    return [sql for sql in conn.sql if sql.startswith(("DELETE ", "INSERT ", "UPDATE "))]


def test_empty_candidate_plan_is_mutation_free_and_keeps_existing_history():
    conn = _Connection(outcomes=[_outcome()], candidates=[])

    result = _run(conn)

    assert result.rows_inserted == 0
    assert _dml(conn) == []
    assert conn.working_rows == conn.original_rows
    assert conn.commit_calls == conn.rollback_calls == 0


def test_valid_nonempty_plan_preserves_outcome_then_replaces_in_sql_order():
    conn = _Connection(outcomes=[_outcome(notes="confirmed")], candidates=[_darshana_row()])

    result = _run(conn)

    assert result.rows_inserted == 1
    assert _dml(conn)[0].startswith("DELETE FROM kala_bhavishya")
    assert _dml(conn)[1].startswith("INSERT INTO kala_bhavishya")
    assert conn.inserted_rows[0][13:15] == (True, "confirmed")
    history_read = next(i for i, sql in enumerate(conn.sql) if "outcome_recorded" in sql)
    candidate_read = next(i for i, sql in enumerate(conn.sql) if "FROM kala_darshana kd" in sql)
    delete = next(i for i, sql in enumerate(conn.sql) if sql.startswith("DELETE "))
    assert history_read < candidate_read < delete
    assert conn.commit_calls == conn.rollback_calls == 0


def test_unmatched_history_fails_before_delete():
    missing_peak = PEAK_DATE + timedelta(days=30)
    conn = _Connection(
        outcomes=[_outcome(peak_date=missing_peak)],
        candidates=[_darshana_row()],
    )

    with pytest.raises(RuntimeError, match="unmatched keys"):
        _run(conn)

    assert _dml(conn) == []
    assert conn.working_rows == conn.original_rows


def test_duplicate_recorded_history_identity_fails_before_delete():
    conn = _Connection(
        outcomes=[_outcome(notes="first"), _outcome(notes="second")],
        candidates=[_darshana_row()],
    )

    with pytest.raises(RuntimeError, match="duplicate recorded outcome history"):
        _run(conn)

    assert _dml(conn) == []


def test_multiple_candidates_for_recorded_identity_fail_before_delete():
    conn = _Connection(
        outcomes=[_outcome()],
        candidates=[
            _darshana_row(convergence_id="conv-1"),
            _darshana_row(convergence_id="conv-2"),
        ],
    )

    with pytest.raises(RuntimeError, match="ambiguous keys"):
        _run(conn)

    assert _dml(conn) == []


def test_insert_failure_propagates_and_caller_rollback_restores_prior_rows():
    conn = _Connection(candidates=[_darshana_row()], fail_insert=True)

    with pytest.raises(RuntimeError, match="injected insert failure"):
        _run(conn)

    assert _dml(conn)[0].startswith("DELETE FROM kala_bhavishya")
    assert conn.working_rows == []
    assert conn.commit_calls == conn.rollback_calls == 0

    # The orchestrator owns the transaction. The writer leaves the error and transaction intact
    # so that its caller can roll back the DELETE together with the failed INSERT.
    conn.rollback()
    assert conn.working_rows == conn.original_rows
    assert conn.rollback_calls == 1
