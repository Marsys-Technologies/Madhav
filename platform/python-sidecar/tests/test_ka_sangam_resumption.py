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
import types
from datetime import date

import pytest

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


# ── D-3 T-6: apply_trigger_suppression — TRIGGER wired at ADMITTED 0.2/0.2 ───
#
# Proves the writer-level TRIGGER composition (services.kala_trigger.trigger.
# compute_trigger_currents + compose_with_ka_sangam, called from THIS file's
# apply_trigger_suppression) actually uses the ADMIT-lane-winning 0.2/0.2
# weights on a real window dict shape (as produced by mode_a_search/
# mode_b_sweep), not services.kala_trigger.trigger's own 0.5/0.6 defaults.

class _FakeGocharaMalefic:
    """Reports a strong (0-deg orb, applying) Saturn hit ONLY when queried at
    the exact mechanism longitude (100.0) — the strongest possible
    malefic_transit_over_mechanism current in isolation, deliberately NOT
    also firing papa_kartari_sandwich's before/after-sign-center queries
    (70.0 / 130.0), so the suppressive math below is the single-current case
    this test's hand-computed expectation assumes."""

    def find_aspects(self, transit_planet, target_lon, aspect_degrees, orb, start_jd, end_jd):
        if transit_planet != "Saturn" or round(target_lon, 1) != 100.0:
            return []
        ev = types.SimpleNamespace(
            orb_at_event_deg=0.0, applying_separating="applying", extra={"aspect_deg": 0},
        )
        return [ev]


class TestApplyTriggerSuppression:
    def _window(self, convergence_score=0.8):
        return {
            "convergence_score": convergence_score,
            "window_start": date(2024, 5, 15),
            "window_end": date(2024, 6, 15),
            "constituent_factors": {
                "planet": "Jupiter",
                "sign": "Taurus",
                "signature_class": "DIGNITY",
            },
        }

    def test_no_gochara_service_is_a_safe_noop(self):
        windows = [self._window()]
        out = ks.apply_trigger_suppression(
            windows, chart_id="cid", target_lon=100.0, gochara_service=None,
            vedha_rules=None, moon_sign_idx=3,
        )
        assert out[0]["convergence_score"] == pytest.approx(0.8)
        assert "trigger_weights_used" not in out[0]["constituent_factors"]

    def test_admitted_weights_actually_reach_the_composed_score(self):
        """THE wiring proof: a real malefic hit lowers the window's SERVED
        convergence_score by exactly the admitted-weight suppressive amount
        (-0.2), not the module's own -0.6 default."""
        windows = [self._window(convergence_score=0.8)]
        out = ks.apply_trigger_suppression(
            windows, chart_id="cid", target_lon=100.0,
            gochara_service=_FakeGocharaMalefic(),
            vedha_rules=None, moon_sign_idx=3,
        )
        cf = out[0]["constituent_factors"]
        assert cf["trigger_weights_used"]["suppressive"] == ks.TRIGGER_ADMITTED_SUPPRESSIVE_WEIGHTS
        assert cf["trigger_weights_used"]["additive"] == ks.TRIGGER_ADMITTED_ADDITIVE_WEIGHTS
        assert cf["convergence_score_pre_trigger"] == pytest.approx(0.8)
        # suppressive = -(1 - (1 - 0.2*1.0)) = -0.2 at the ADMITTED weight
        assert cf["trigger_suppressive_applied"] == pytest.approx(-0.2, abs=1e-4)
        assert out[0]["convergence_score"] == pytest.approx(0.6, abs=1e-4)  # 0.8 + (-0.2)
        # Explicitly NOT the module's own 0.6 default, which would have produced 0.2.
        assert out[0]["convergence_score"] != pytest.approx(0.2, abs=1e-4)

    def test_missing_window_dates_skipped_safely(self):
        windows = [{"convergence_score": 0.5, "constituent_factors": {}}]
        out = ks.apply_trigger_suppression(
            windows, chart_id="cid", target_lon=100.0,
            gochara_service=_FakeGocharaMalefic(),
            vedha_rules=None, moon_sign_idx=3,
        )
        assert out[0]["convergence_score"] == pytest.approx(0.5)
