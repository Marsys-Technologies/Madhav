"""
test_ka_sangam_resumption.py — substep-level resumption logic (migration 436)
=============================================================================
Unit coverage (CI, no live DB) for the ka_sangam resume/replan decision helpers.

The end-to-end BYTE-IDENTICAL proof (a real interrupted-then-resumed build vs an
uninterrupted build producing identical kala_convergence scores) was run against
the live DB on chart 1c826d5a (Abhinandan) during Doctrine-Campaign Night-1 and
PASSED (3313 rows, checksum 890513b2831425fb72099252ee30b2cf, identical both ways).
These tests guard the decision logic underneath that proof against regression.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pipeline.orchestrator.writers.ka_sangam as ks


class _Cur:
    def __init__(self, ledger_rows=None):
        self._ledger_rows = ledger_rows if ledger_rows is not None else []
        self.executed: list[tuple[str, object]] = []
        self._last = ""

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        self._last = sql

    def fetchall(self):
        if "FROM build_substep_progress" in self._last:
            return list(self._ledger_rows)
        return []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


class _Conn:
    def __init__(self, ledger_rows=None):
        self.cur = _Cur(ledger_rows)

    def cursor(self, *a, **k):
        return self.cur


def _writer(pred_signal_ids=("s1", "s2", "s3"), birth_year=1984, lt_count=None):
    w = ks.KaSangamWriter()
    w._pred_dicts = [{"signal_id": s} for s in pred_signal_ids]
    w._birth_year = birth_year
    w._lt_preds = w._pred_dicts[: (lt_count if lt_count is not None else len(pred_signal_ids))]
    return w


# ── fingerprint ──────────────────────────────────────────────────────────────

class TestFingerprint:
    def test_stable_across_instances_with_same_inputs(self):
        a = _writer()._compute_build_fingerprint("chartX")
        b = _writer()._compute_build_fingerprint("chartX")
        assert a == b, "same inputs must yield the same fingerprint (resume depends on this)"

    def test_changes_with_predicate_set(self):
        a = _writer(pred_signal_ids=("s1", "s2", "s3"))._compute_build_fingerprint("chartX")
        b = _writer(pred_signal_ids=("s1", "s2", "s9"))._compute_build_fingerprint("chartX")
        assert a != b, "a changed predicate set is a different build → must replan"

    def test_changes_with_birth_year_and_chart(self):
        base = _writer()._compute_build_fingerprint("chartX")
        assert _writer(birth_year=1990)._compute_build_fingerprint("chartX") != base
        assert _writer()._compute_build_fingerprint("chartY") != base

    def test_changes_with_resume_version(self):
        base = _writer()._compute_build_fingerprint("chartX")
        orig = ks._KA_SANGAM_RESUME_VERSION
        try:
            ks._KA_SANGAM_RESUME_VERSION = orig + 1
            assert _writer()._compute_build_fingerprint("chartX") != base, \
                "bumping the resume version must invalidate in-flight ledgers"
        finally:
            ks._KA_SANGAM_RESUME_VERSION = orig


# ── ledger read (resume vs replan decision) ──────────────────────────────────

class TestLoadCompletedSubsteps:
    def test_empty_ledger_returns_none(self):
        w = _writer()
        assert w._load_completed_substeps(_Conn([]), "cid", "fp") is None

    def test_matching_fingerprint_returns_completed_keys(self):
        rows = [
            {"substep_key": "near", "build_fingerprint": "fp"},
            {"substep_key": "lifetime:0", "build_fingerprint": "fp"},
        ]
        got = _writer()._load_completed_substeps(_Conn(rows), "cid", "fp")
        assert got == {"near", "lifetime:0"}

    def test_any_mismatched_fingerprint_forces_replan_none(self):
        rows = [
            {"substep_key": "near", "build_fingerprint": "OLD"},
            {"substep_key": "lifetime:0", "build_fingerprint": "OLD"},
        ]
        assert _writer()._load_completed_substeps(_Conn(rows), "cid", "fp") is None

    def test_partial_mismatch_forces_replan_none(self):
        rows = [
            {"substep_key": "near", "build_fingerprint": "fp"},
            {"substep_key": "lifetime:0", "build_fingerprint": "OLD"},
        ]
        assert _writer()._load_completed_substeps(_Conn(rows), "cid", "fp") is None


# ── ledger write (atomic within the substep transaction) ─────────────────────

class TestRecordSubstep:
    def test_upsert_sql_and_params(self):
        w = _writer()
        w._resume_fingerprint = "fp123"
        conn = _Conn()
        w._record_substep(conn, "cid", "lifetime:7", 42)
        sql, params = conn.cur.executed[-1]
        assert "INSERT INTO build_substep_progress" in sql
        assert "ON CONFLICT (chart_id, asset_id, substep_key)" in sql
        assert params == ("cid", "lifetime:7", "fp123", 42)


# ── self-scoping of the near substep's delete ────────────────────────────────

class TestNearSelfScoping:
    def _delete_targets(self, w, conn):
        """Run just the delete block of _substep_near by monkeypatching the
        window generation to a no-op, and capture which horizon_tiers get deleted."""
        w._generate_windows = lambda **kw: []      # skip heavy compute
        w._dedup = staticmethod(lambda x: [])
        w._insert_windows = lambda cur, cid, rows, tier: 0
        w._pred_dicts = w._pred_dicts
        w._enrichment_ctx = None
        w._dks = w._gs = w._muhurta = None
        import types
        w._native_ctx = types.SimpleNamespace(moon_sign="Aries")
        w._record_substep = lambda *a, **k: None
        w._substep_near(conn, "cid", dry_run=False)
        return [sql for sql, _ in conn.cur.executed if "DELETE FROM kala_convergence" in sql]

    def test_with_lifetime_preds_does_not_bulk_delete_lifetime(self):
        w = _writer(lt_count=3)
        deletes = self._delete_targets(w, _Conn())
        joined = " ".join(deletes)
        assert "horizon_tier = 'near'" in joined
        assert "horizon_tier = 'lifetime'" not in joined, \
            "with lifetime substeps present, near must NOT wipe lifetime rows (each lifetime substep clears its own)"

    def test_without_lifetime_preds_does_bulk_delete_lifetime(self):
        w = _writer(pred_signal_ids=("s1",), lt_count=0)
        deletes = self._delete_targets(w, _Conn())
        joined = " ".join(deletes)
        assert "horizon_tier = 'near'" in joined
        assert "horizon_tier = 'lifetime'" in joined, \
            "with no lifetime substeps, near must still clear stale lifetime rows itself"
