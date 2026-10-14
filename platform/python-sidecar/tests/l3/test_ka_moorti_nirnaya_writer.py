"""Writer-shell tests for ka_moorti_nirnaya — the DB-touching orchestration
around the pure logic tested in test_ka_moorti_nirnaya.py. Uses a minimal
FakeConn/FakeCursor (no real Postgres) — mirrors the FakeConn pattern already
used by test_ka_kota_chakra_writer.py / test_ka_sudarshana_varsha_writer.py so
the B.10 honest-empty paths are verified without requiring a live DB in CI.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from services.ka_moorti_nirnaya.writer import (
    _fetch_janma_nakshatra_idx,
    _fetch_moorti_table,
)


class _FakeCursorOne:
    def __init__(self, fetchone_result=None):
        self._fetchone_result = fetchone_result

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self.last_sql = sql
        self.last_params = params

    def fetchone(self):
        return self._fetchone_result


class _FakeConnOne:
    def __init__(self, fetchone_result=None):
        self._fetchone_result = fetchone_result

    def cursor(self, row_factory=None):
        return _FakeCursorOne(self._fetchone_result)



# DB9 (2026-08-08): these fixtures previously supplied TUPLE rows, e.g.
# fetchone_result=("fact123", None). Production does not produce tuple rows --
# the orchestrator connection is created with row_factory=psycopg.rows.dict_row
# (pipeline/orchestrator/db.py), so every cursor yields DICT rows. The helpers
# under test indexed positionally (row[1]) and therefore raised KeyError: 1 in
# production while these tests stayed green, because the fixture fed the code a
# row shape production never emits. A detector that cannot see the real input is
# not a detector (CLAUDE.md N.8). Fixtures now supply dict rows, as production does.

class TestFetchJanmaNakshatraIdx:
    def test_missing_fact_returns_none(self):
        conn = _FakeConnOne(fetchone_result=None)
        assert _fetch_janma_nakshatra_idx(conn, "chart-x") is None

    def test_null_value_returns_none(self):
        conn = _FakeConnOne(fetchone_result={"fact_id": "fact123", "fact_value_num": None})
        assert _fetch_janma_nakshatra_idx(conn, "chart-x") is None

    def test_present_fact_derives_nakshatra_idx(self):
        # Moon longitude_sidereal = 327.055230133129 -> nak_idx 24 (Purva
        # Bhadrapada), the exact FORENSIC-anchored value for chart 482012f1
        # (CLAUDE.md §B) — same fixture value test_ka_kota_chakra_writer.py uses.
        conn = _FakeConnOne(fetchone_result={"fact_id": "7cf5902c6bd63146", "fact_value_num": 327.055230133129})
        result = _fetch_janma_nakshatra_idx(conn, "482012f1-710e-4a25-994a-93821f5871aa")
        assert result == (24, "7cf5902c6bd63146")


class _FakeCursorAll:
    def __init__(self, fetchall_result):
        self._fetchall_result = fetchall_result

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        pass

    def fetchall(self):
        return self._fetchall_result


class _FakeConnAll:
    def __init__(self, fetchall_result):
        self._fetchall_result = fetchall_result

    def cursor(self, row_factory=None):
        return _FakeCursorAll(self._fetchall_result)


class TestFetchMoortiTable:
    def test_empty_table_returns_empty_dict(self):
        conn = _FakeConnAll([])
        assert _fetch_moorti_table(conn) == {}

    def test_rows_keyed_by_nakshatra_offset(self):
        conn = _FakeConnAll([
            {"nakshatra_offset": 1, "moorti_name": "swarna", "quality_tier": 1,
             "phala_brief": "brief-1", "classical_citation": "Phaladeepika Ch.26 §moorti-nirnaya; BPHS Ch.28"},
            {"nakshatra_offset": 4, "moorti_name": "loha", "quality_tier": 4,
             "phala_brief": "brief-4", "classical_citation": "Phaladeepika Ch.26 §moorti-nirnaya; BPHS Ch.28"},
        ])
        table = _fetch_moorti_table(conn)
        assert set(table.keys()) == {1, 4}
        assert table[1]["moorti_name"] == "swarna"
        assert table[4]["quality_tier"] == 4
        assert table[4]["classical_citation"] == "Phaladeepika Ch.26 §moorti-nirnaya; BPHS Ch.28"


# ── A5.4 (steward M20261001T182640-dded) — the ingress-root solver method is
# RECORDED, and only the kernel's backend-unavailable error triggers the
# spline fallback (§N.8: a degraded result must be distinguishable from a
# verified one). These tests drive the REAL _build_kernel_arcs / run() through
# the real kernel (arcs, contacts, swiss_bisect); only the single Swiss seam
# (calc_sidereal_lon) is replaced by a deterministic linear body, so the
# kernel's own backend gate (retflag & 2 / & 4 → EphemerisBackendError) is what
# decides the outcome — the rule is never re-implemented in the test.

from datetime import date, timedelta
from types import SimpleNamespace

import pytest

from services.gochara_kernel import contacts as kernel_contacts
from services.gochara_kernel.overlays import date_to_jd
from services.ka_moorti_nirnaya import writer as moorti_writer
from services.ka_moorti_nirnaya.logic import MOORTI_GRAHAS

_DAY0 = date(2026, 1, 1)
_RATE_DEG_PER_DAY = 0.98
_SWIEPH_RETFLAG = 2    # retflag & 2 — the SWIEPH gate passes
_MOSHIER_RETFLAG = 4   # retflag & 4 — the kernel must raise EphemerisBackendError


def _daily(start_lon: float, days: int = 12) -> list[tuple[date, float]]:
    return [
        (_DAY0 + timedelta(days=i), (start_lon + _RATE_DEG_PER_DAY * i) % 360.0)
        for i in range(days)
    ]


def _linear_backend(start_lon: float, retflag: int):
    jd0 = date_to_jd(_DAY0)

    def _calc(body, jd, ephe_path):  # same signature as knots.calc_sidereal_lon
        return (start_lon + _RATE_DEG_PER_DAY * (jd - jd0)) % 360.0, retflag

    return _calc


class _Boom(Exception):
    pass


class TestIngressSolverMethodRecorded:
    def test_swiss_available_records_swiss_refined(self, monkeypatch):
        monkeypatch.setattr(kernel_contacts, "calc_sidereal_lon", _linear_backend(28.5, _SWIEPH_RETFLAG))
        _idx, roots, solver = moorti_writer._build_kernel_arcs({"Sun": _daily(28.5)}, ("Sun",))
        assert roots["Sun"], "28.5°→40° must cross the 30° sign boundary"
        assert solver["Sun"] == {"method": "swiss_refined", "backend": "swieph"}
        assert "ingress_solver=Sun:swiss_refined|swieph;ingress_solver_degraded=0" == \
            moorti_writer._solver_notes(solver)

    def test_backend_unavailable_falls_back_and_the_fallback_is_recorded(self, monkeypatch):
        monkeypatch.setattr(kernel_contacts, "calc_sidereal_lon", _linear_backend(28.5, _MOSHIER_RETFLAG))
        _idx, roots, solver = moorti_writer._build_kernel_arcs({"Sun": _daily(28.5)}, ("Sun",))
        assert roots["Sun"], "the kernel's spline roots must still stand"
        assert all(r.exact_jd == r.spline_exact_jd for r in roots["Sun"]), \
            "unrefined means exact_jd IS the spline root"
        assert solver["Sun"] == {
            "method": "spline_unrefined", "backend": "moshier(retflag=4)",
        }
        notes = moorti_writer._solver_notes(solver)
        assert "Sun:spline_unrefined|moshier(retflag=4)" in notes
        assert "ingress_solver_degraded=1" in notes

    @pytest.mark.parametrize("exc", [RuntimeError("not a backend error"), KeyError("k"), _Boom("x")])
    def test_unrelated_exception_is_not_swallowed(self, monkeypatch, exc):
        def _raise(body, jd, ephe_path):
            raise exc

        monkeypatch.setattr(kernel_contacts, "calc_sidereal_lon", _raise)
        with pytest.raises(type(exc)):
            moorti_writer._build_kernel_arcs({"Sun": _daily(28.5)}, ("Sun",))

    def test_body_without_an_ingress_root_claims_no_method(self, monkeypatch):
        # 5°→16°: no sign boundary in range, Swiss is never probed — the record
        # must not claim a refined (or degraded) solve that never happened,
        # even though the backend would have failed.
        monkeypatch.setattr(kernel_contacts, "calc_sidereal_lon", _linear_backend(5.0, _MOSHIER_RETFLAG))
        _idx, roots, solver = moorti_writer._build_kernel_arcs({"Sun": _daily(5.0)}, ("Sun",))
        assert roots["Sun"] == []
        assert solver["Sun"] == {"method": "no_ingress_roots", "backend": "not_probed"}

    def test_run_surfaces_the_recorded_fallback_in_the_writer_result(self, monkeypatch):
        horizon_end = _DAY0 + timedelta(days=11)
        bodies = MOORTI_GRAHAS + ("Moon",)
        monkeypatch.setattr(kernel_contacts, "calc_sidereal_lon", _linear_backend(28.5, _MOSHIER_RETFLAG))
        monkeypatch.setattr(moorti_writer, "_fetch_janma_nakshatra_idx", lambda conn, cid: (24, "fact-x"))
        monkeypatch.setattr(
            moorti_writer, "_fetch_moorti_table",
            lambda conn: {
                k: {"moorti_name": f"m{k}", "quality_tier": 1, "phala_brief": "b",
                    "classical_citation": "c"} for k in range(1, 28)
            },
        )
        monkeypatch.setattr(moorti_writer, "_compute_ayanamsha_offset", lambda today: 0.0)
        monkeypatch.setattr(
            moorti_writer, "_fetch_daily_sidereal_by_body",
            lambda conn, hs, he, offset, bs: {b: _daily(28.5) for b in bs},
        )
        # Step 3 §4: the fingerprint's node-series and L1 components — stubbed
        # (their own live-DB behaviour is covered by the step-3 fingerprint
        # suite); this test's subject is the solver-method recording.
        monkeypatch.setattr(
            moorti_writer, "node_series_identity",
            lambda conn: {"mode": "true", "n_rows": 2, "digest": "d" * 64})
        monkeypatch.setattr(
            moorti_writer, "l1_operand_identity",
            lambda conn, cid, ay, ops: {"operands": [], "digest": "e" * 64})

        class _Cur:
            def __enter__(self): return self
            def __exit__(self, *a): return False
            def execute(self, *a, **k): pass
            def executemany(self, *a, **k): pass

        class _Conn:
            def cursor(self, *a, **k): return _Cur()

        ctx = SimpleNamespace(
            db_conn=_Conn(), dry_run=False,
            config={"chart_id": "482012f1-710e-4a25-994a-93821f5871aa",
                    "horizon_start": _DAY0, "horizon_end": horizon_end},
        )
        result = moorti_writer.KaMoortiNirnayaWriter().run(ctx)
        assert result.rows_inserted > 0
        # Rahu/Ketu never reach the Swiss backend (their series is the TRUE node, the
        # kernel's objective the MEAN node) — they are recorded under their own reason,
        # not as backend-degraded; every other body is the backend failure under test
        assert f"ingress_solver_degraded={len(bodies) - 2}" in result.notes
        assert "ingress_solver_node_convention_unrefined=2" in result.notes
        assert "Rahu:spline_unrefined|not_probed|node_convention_mismatch(series=true,kernel=mean)" \
            in result.notes
        assert "Sun:spline_unrefined|moshier(retflag=4)" in result.notes
        assert "kernel_instant_graded_spline_unrefined=" in result.notes
