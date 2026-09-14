"""DP-SD-017 BHAV-P0: identity/history-safe ka_bhavishya_lekha refresh."""
from __future__ import annotations

from copy import deepcopy
from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from pipeline.orchestrator.writers.ka_bhavishya_lekha import KaBhavishyaLekhaWriter


CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
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


def _existing_row(
    *, row_id=41, signal_id=SIGNAL_ID, peak_date=PEAK_DATE,
    outcome_recorded=False, outcome_notes=None,
):
    return {
        "id": row_id,
        "signal_id": signal_id,
        "peak_date": peak_date,
        "outcome_recorded": outcome_recorded,
        "outcome_notes": outcome_notes,
        "projection_rank": 99,
    }


class _StrictCursor:
    """SQL-aware cursor that rejects every statement not modeled by the test."""

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
        params = tuple(params or ())
        self.conn.sql.append((statement, params))

        if statement == "SET LOCAL statement_timeout = 0":
            return
        if statement.startswith(
            "SELECT id, signal_id, peak_date, outcome_recorded, outcome_notes "
            "FROM kala_bhavishya"
        ):
            assert params == (CHART_ID,)
            assert statement.endswith("ORDER BY id FOR UPDATE")
            self._rows = deepcopy(self.conn.rows)
            return
        if statement.startswith("SELECT 1 FROM information_schema.columns"):
            self._one = (1,)
            return
        if "FROM kala_darshana kd" in statement:
            assert params[0] == CHART_ID
            self._rows = deepcopy(self.conn.candidates)
            return
        if statement.startswith("SELECT signal_id, signal_type_id FROM bodha_msr_signals"):
            self._rows = [
                {"signal_id": row["signal_id"], "signal_type_id": "raja_yoga"}
                for row in self.conn.candidates
                if row["signal_id"] is not None
            ]
            return
        if statement == "SELECT to_regclass('phala_anchors') IS NOT NULL AS present":
            self._one = {"present": self.conn.phala_table_exists}
            return
        if statement.startswith("SELECT bhavishya_id FROM phala_anchors"):
            requested = set(params)
            self._rows = [
                {"bhavishya_id": row_id}
                for row_id in sorted(self.conn.phala_refs & requested)
            ][:10]
            return
        if statement.startswith("DELETE FROM kala_bhavishya"):
            assert params[0] == CHART_ID
            stale_ids = set(params[1:])
            assert not (stale_ids & self.conn.phala_refs), "writer attempted referenced-row delete"
            self.conn.rows = [row for row in self.conn.rows if row["id"] not in stale_ids]
            return
        raise AssertionError(f"unmodeled execute SQL: {statement}")

    def executemany(self, sql, param_rows):
        statement = " ".join(sql.split())
        param_rows = list(param_rows)
        self.conn.sql.append((statement, tuple(param_rows)))

        if statement.startswith("UPDATE kala_bhavishya SET projection_rank"):
            for values in param_rows:
                assert len(values) == 17
                chart_id, row_id = values[-2:]
                assert chart_id == CHART_ID
                row = next(row for row in self.conn.rows if row["id"] == row_id)
                row.update({
                    "projection_rank": values[0],
                    "signal_id": values[7],
                    "peak_date": date.fromisoformat(values[3]),
                    "outcome_recorded": values[12],
                    "outcome_notes": values[13],
                })
            return
        if statement.startswith("INSERT INTO kala_bhavishya"):
            if self.conn.fail_insert:
                raise RuntimeError("injected insert failure")
            for values in param_rows:
                assert len(values) == 16
                self.conn.next_id += 1
                self.conn.rows.append({
                    "id": self.conn.next_id,
                    "projection_rank": values[1],
                    "signal_id": values[8],
                    "peak_date": date.fromisoformat(values[4]),
                    "outcome_recorded": values[13],
                    "outcome_notes": values[14],
                })
            return
        raise AssertionError(f"unmodeled executemany SQL: {statement}")

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._one


class _StrictConnection:
    def __init__(
        self, *, rows=None, candidates=None, phala_refs=None, phala_table_exists=True,
        fail_insert=False,
    ):
        self.rows = deepcopy(list(rows or []))
        self.original_rows = deepcopy(self.rows)
        self.candidates = deepcopy(list(candidates or []))
        self.phala_refs = set(phala_refs or set())
        self.phala_table_exists = phala_table_exists
        self.fail_insert = fail_insert
        self.next_id = max((row["id"] for row in self.rows), default=100)
        self.sql = []
        self.commit_calls = 0
        self.rollback_calls = 0

    def cursor(self, **_kwargs):
        return _StrictCursor(self)

    def commit(self):
        self.commit_calls += 1

    def rollback(self):
        self.rollback_calls += 1
        self.rows = deepcopy(self.original_rows)


def _run(conn):
    ctx = SimpleNamespace(db_conn=conn, config={"chart_id": CHART_ID})
    return KaBhavishyaLekhaWriter().run(ctx)


def _write_sql(conn):
    return [
        sql for sql, _params in conn.sql
        if sql.startswith(("DELETE ", "INSERT ", "UPDATE "))
    ]


def test_true_empty_state_is_successful_and_mutation_free():
    conn = _StrictConnection(rows=[], candidates=[])

    result = _run(conn)

    assert result.rows_inserted == 0
    assert "no existing projections" in result.notes
    assert _write_sql(conn) == []


def test_empty_candidates_with_existing_rows_fail_instead_of_serving_stale_success():
    conn = _StrictConnection(rows=[_existing_row()], candidates=[])

    with pytest.raises(RuntimeError, match="candidate plan is empty"):
        _run(conn)

    assert [row["id"] for row in conn.rows] == [41]
    assert _write_sql(conn) == []


def test_matching_projection_updates_in_place_and_preserves_id_outcome_and_fk():
    conn = _StrictConnection(
        rows=[_existing_row(outcome_recorded=True, outcome_notes="confirmed")],
        candidates=[_darshana_row()],
        phala_refs={41},
    )

    result = _run(conn)

    assert result.rows_inserted == 1
    assert len(conn.rows) == 1
    assert conn.rows[0] == {
        "id": 41,
        "projection_rank": 1,
        "signal_id": SIGNAL_ID,
        "peak_date": PEAK_DATE,
        "outcome_recorded": True,
        "outcome_notes": "confirmed",
    }
    assert len(_write_sql(conn)) == 1
    assert _write_sql(conn)[0].startswith("UPDATE kala_bhavishya")
    assert conn.phala_refs == {41}
    assert conn.commit_calls == conn.rollback_calls == 0


def test_duplicate_candidate_identity_is_rejected_even_without_history():
    conn = _StrictConnection(
        candidates=[
            _darshana_row(convergence_id="conv-1"),
            _darshana_row(convergence_id="conv-2"),
        ],
    )

    with pytest.raises(RuntimeError, match="duplicate candidate"):
        _run(conn)

    assert _write_sql(conn) == []


def test_duplicate_existing_identity_is_rejected_before_candidate_reads_or_writes():
    conn = _StrictConnection(
        rows=[_existing_row(row_id=41), _existing_row(row_id=42)],
        candidates=[_darshana_row()],
    )

    with pytest.raises(RuntimeError, match="duplicate existing projection history"):
        _run(conn)

    assert _write_sql(conn) == []
    assert not any("FROM kala_darshana kd" in sql for sql, _ in conn.sql)


def test_unmatched_recorded_history_fails_before_any_write():
    old_peak = PEAK_DATE - timedelta(days=30)
    conn = _StrictConnection(
        rows=[
            _existing_row(
                peak_date=old_peak,
                outcome_recorded=True,
                outcome_notes="observed",
            )
        ],
        candidates=[_darshana_row()],
    )

    with pytest.raises(RuntimeError, match="unmatched keys"):
        _run(conn)

    assert _write_sql(conn) == []
    assert conn.rows[0]["id"] == 41


def test_unmatched_phala_referenced_row_fails_before_delete_and_keeps_provenance():
    conn = _StrictConnection(
        rows=[_existing_row(peak_date=PEAK_DATE - timedelta(days=30))],
        candidates=[_darshana_row()],
        phala_refs={41},
    )

    with pytest.raises(RuntimeError, match="null accepted provenance"):
        _run(conn)

    assert _write_sql(conn) == []
    assert conn.rows[0]["id"] == 41
    assert conn.phala_refs == {41}


def test_unreferenced_unrecorded_stale_row_is_deleted_and_new_identity_inserted():
    conn = _StrictConnection(
        rows=[_existing_row(row_id=41, peak_date=PEAK_DATE - timedelta(days=30))],
        candidates=[_darshana_row()],
    )

    result = _run(conn)

    assert result.rows_inserted == 1
    assert len(conn.rows) == 1
    assert conn.rows[0]["id"] != 41
    writes = _write_sql(conn)
    assert writes[0].startswith("DELETE FROM kala_bhavishya WHERE chart_id")
    assert writes[1].startswith("INSERT INTO kala_bhavishya")


def test_insert_failure_is_left_for_caller_transaction_rollback():
    original = _existing_row(row_id=41, peak_date=PEAK_DATE - timedelta(days=30))
    conn = _StrictConnection(
        rows=[original],
        candidates=[_darshana_row()],
        fail_insert=True,
    )

    with pytest.raises(RuntimeError, match="injected insert failure"):
        _run(conn)

    assert conn.rows == []  # stale-row DELETE occurred in the still-open transaction
    assert conn.commit_calls == conn.rollback_calls == 0

    conn.rollback()
    assert conn.rows == [original]
    assert conn.rollback_calls == 1


def test_existing_rows_are_locked_before_downstream_reference_preflight():
    conn = _StrictConnection(
        rows=[_existing_row(peak_date=PEAK_DATE - timedelta(days=30))],
        candidates=[_darshana_row()],
    )

    _run(conn)

    lock_index = next(i for i, (sql, _) in enumerate(conn.sql) if sql.endswith("FOR UPDATE"))
    ref_probe_index = next(
        i for i, (sql, _) in enumerate(conn.sql) if "to_regclass('phala_anchors')" in sql
    )
    delete_index = next(i for i, (sql, _) in enumerate(conn.sql) if sql.startswith("DELETE "))
    assert lock_index < ref_probe_index < delete_index
