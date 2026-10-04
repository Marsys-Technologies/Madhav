"""
test_build_fact_identity_index_script.py — the standalone G-IDX script's
control flow around the corrected check (S-L1 rehearsal P3): the rows==parsed
detector, the dry-run NOT_EVALUATED rule, and `--check` roll-back + exit 4.

No database: a tiny in-memory fake stands in for the psycopg connection and
the two tables, executing only the statements the script issues.
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

import pytest

psycopg = pytest.importorskip("psycopg")

_SCRIPT = pathlib.Path(__file__).resolve().parents[1] / "scripts" / "build_fact_identity_index.py"
_spec = importlib.util.spec_from_file_location("build_fact_identity_index_under_test", _SCRIPT)
script = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(script)

CHART = "482012f1-710e-4a25-994a-93821f5871aa"


class _Cur:
    def __init__(self, conn):
        self.conn = conn
        self._rows = []
        self.rowcount = -1

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=()):
        s = " ".join(sql.split())
        if s.startswith("SELECT fact_id, fact_category"):
            self._rows = list(self.conn.facts)
        elif s.startswith("DELETE FROM chart_fact_identity"):
            self.rowcount = len(self.conn.identity)
            self.conn.identity = []
        elif s.startswith("SELECT count(*) FROM chart_fact_identity"):
            self._rows = [(len(self.conn.identity),)]
        else:  # pragma: no cover
            raise AssertionError(f"unexpected SQL: {s}")

    def executemany(self, sql, seq):
        assert sql.lstrip().startswith("INSERT INTO chart_fact_identity")
        self.conn.identity.extend(seq)

    def fetchmany(self, n):
        out, self._rows = self._rows[:n], self._rows[n:]
        return out

    def fetchone(self):
        return self._rows[0]


class FakeConn:
    def __init__(self, facts, identity=0):
        self.facts = facts
        self.identity = [{"stale": i} for i in range(identity)]
        self.committed = False
        self.rolled_back = False

    def cursor(self, **_kw):
        return _Cur(self)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _facts(*, with_gap: bool):
    rows = [
        ("f1", "ashtakavarga_bindu_contributor", "SUN-CONTRIBUTOR_SUN-SIGN_1", "bindus", None),
        ("f2", "ashtakavarga_bindu_sign", "SUN-SIGN_1", "bindus", None),
        ("f3", "sensitive_point_gulika_mandi", "YAMAKANTAKA", "sign", None),
        ("f4", "panchanga_special_yoga_combinations", "YOGA_PANCHAKA", "combination_name", None),
        ("f5", "dasha_scope_cap", "PRANA_DASHA", "level_5_not_computed", None),
    ]
    if with_gap:
        rows.append(("f6", "brand_new_category", "NEVER_SEEN_SUBJECT", "k", None))
    return rows


def test_summary_counts_and_rows_detector_real_run():
    conn = FakeConn(_facts(with_gap=False), identity=1205)
    s = script.build_index_for_chart(conn, CHART)
    assert (s["total_facts"], s["parsed"], s["identity_free"], s["gap"]) == (5, 2, 3, 0)
    assert s["deleted_prior_rows"] == 1205
    assert s["rows_in_table"] == 2 == len(conn.identity)
    assert s["identity_free_reasons"] == {"special_point_or_aggregate_marker": 2, "scope_cap_sentinel": 1}


def test_dry_run_does_not_write_and_rows_check_is_not_evaluated():
    conn = FakeConn(_facts(with_gap=False), identity=1205)
    s = script.build_index_for_chart(conn, CHART, dry_run=True)
    assert s["rows_in_table"] is None and len(conn.identity) == 1205
    res = script.check_identity_index(s, exact_reasons=False)
    assert [i.name for i in res.not_evaluated] == ["rows_equal_parsed"]
    assert res.failed == []


def test_unknown_category_row_is_counted_as_gap_with_example():
    conn = FakeConn(_facts(with_gap=True))
    s = script.build_index_for_chart(conn, CHART)
    assert s["gap"] == 1 and s["identity_free"] == 3
    assert s["gap_examples"] == {("brand_new_category", "k"): "NEVER_SEEN_SUBJECT"}


def _run_main(monkeypatch, conn, *argv):
    monkeypatch.setenv("DATABASE_URL", "postgresql://fake")
    monkeypatch.setattr(psycopg, "connect", lambda dsn: conn)
    monkeypatch.setattr(sys, "argv", ["build_fact_identity_index.py", "--chart-id", CHART, *argv])
    return script.main()


def test_check_flag_fails_with_exit_4_and_rolls_back_on_a_gap(monkeypatch, capsys):
    conn = FakeConn(_facts(with_gap=True))
    rc = _run_main(monkeypatch, conn, "--check", "--reasons-mode", "subset")
    out = capsys.readouterr().out
    assert rc == 4
    assert conn.rolled_back and not conn.committed
    assert "CHECK: FAIL (gap_within_limit, coverage_of_identity_bearing)" in out


def test_without_check_flag_a_failed_check_is_reported_but_not_fatal(monkeypatch, capsys):
    conn = FakeConn(_facts(with_gap=True))
    rc = _run_main(monkeypatch, conn, "--reasons-mode", "subset")
    out = capsys.readouterr().out
    assert rc == 0 and conn.committed
    assert "NOT fatal without --check" in out


def test_check_flag_passes_and_commits_on_a_clean_chart(monkeypatch, capsys):
    conn = FakeConn(_facts(with_gap=False))
    rc = _run_main(monkeypatch, conn, "--check", "--reasons-mode", "subset")
    out = capsys.readouterr().out
    assert rc == 0 and conn.committed and not conn.rolled_back
    assert "CHECK: PASS" in out


def test_dry_run_with_check_never_commits_and_reports_not_evaluated(monkeypatch, capsys):
    conn = FakeConn(_facts(with_gap=False))
    rc = _run_main(monkeypatch, conn, "--dry-run", "--check", "--reasons-mode", "subset")
    out = capsys.readouterr().out
    assert rc == 0 and conn.rolled_back and not conn.committed
    assert "CHECK: NOT_EVALUATED (rows_equal_parsed)" in out
