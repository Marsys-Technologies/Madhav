"""An ephemeris-BACKEND failure fails the ga_sensitive build; it is never floored (SS ruling 2026-10-03).

A missing ``SE_EPHE_PATH`` / non-``swieph`` backend (``SwissBackendError``), a JD outside the .se1
corpus window (``OutOfCorpusRangeError``) and an unchecked window (``WindowUncheckedError``) mean the
INFRASTRUCTURE cannot compute -- not "this value is not defined".  Before this fix
``pyjhora_adapter.special_lagnas.compute_special_lagnas`` caught every per-lagna error into an
``{"error": ...}`` entry and ``ga_sensitive`` turned each into a FLOORED special_lagna row (the
SPECIAL_LAGNA_AYA_CHECK "fail-closed side effect").  ``floored`` stays reserved for genuine
"requires external computation / not defined" cases, which this file pins separately.

Real, not mocked away: the backend-unset / out-of-corpus tests run the REAL adapter (real
``with_sidereal_mode`` -> real ``ensure_swiss_backend``); only the "other exception" and the
"WindowUncheckedError" cases patch a PyJHora call (the latter cannot arise inside the adapter by
construction -- it is raised by the writer decorator -- so the tuple's membership is what is pinned).
DB-free: a recording fake ``conn``; ``_insert_rows`` is replaced by a sentinel that fails the test if
it is ever called.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.parent))

from jhora import utils  # noqa: E402
from jhora.panchanga import drik  # noqa: E402

from brahmagyan.verification_tiers import FLOORED  # noqa: E402
from ga_writers import ga_sensitive_writer as W  # noqa: E402
from panchang_engine.swiss_backend import (  # noqa: E402
    OutOfCorpusRangeError,
    SwissBackendError,
    WindowUncheckedError,
)
from pyjhora_adapter import special_lagnas as sl  # noqa: E402
from pyjhora_adapter._swiss_thread_scope import BACKEND_FAILURE_ERRORS  # noqa: E402

# Synthetic birth (not the native chart): the adapter-level tests need only a valid date/place.
LAT, LON, TZ = 23.26, 77.41, 5.5
DOB = drik.Date(2011, 2, 6)
TOB = (11, 0, 0)
JD = utils.julian_day_number(DOB, TOB)

_BIRTH = {
    "datetime_iso": "2011-02-06T11:00:00",
    "latitude_deg": LAT,
    "longitude_deg": LON,
    "tz_offset_hours": TZ,
}
CHART_ID = "test-chart-backend-failure"  # NOT the canonical id -> FORENSIC gate is skipped
AYA_KEY = "lahiri_chitrapaksha"
BUILD_ID = "backend-failure-build"

_DELEGATED = ("bhava_lagna", "hora_lagna", "ghati_lagna", "vighati_lagna", "varnada_lagna")


@pytest.fixture()
def backend_unset(monkeypatch):
    monkeypatch.delenv("SE_EPHE_PATH", raising=False)


class _RecordingConn:
    """A fake ``ctx.db_conn``: records every call; the writer must never reach it."""

    def __init__(self):
        self.calls: list[str] = []

    def __getattr__(self, name):  # pragma: no cover - only hit on a violation
        def _rec(*a, **k):
            self.calls.append(name)
            raise AssertionError(f"ga_sensitive touched the DB connection ({name}) after a backend failure")
        return _rec


@pytest.fixture()
def no_insert(monkeypatch):
    """``_insert_rows`` is the only row sink of the writer: assert it is never called."""
    calls: list[tuple] = []

    def _sentinel(*a, **k):
        calls.append((a, k))
        raise AssertionError("ga_sensitive reached _insert_rows: rows would have been written")

    monkeypatch.setattr(W, "_insert_rows", _sentinel)
    return calls


# ── adapter: compute_special_lagnas ───────────────────────────────────────────


def test_backend_unset_compute_special_lagnas_raises_swiss_backend_error(backend_unset):
    with pytest.raises(SwissBackendError, match="SE_EPHE_PATH"):
        sl.compute_special_lagnas(JD, DOB, TOB, "lahiri", lat=LAT, lon=LON, tz=TZ)


def test_out_of_corpus_jd_raises_out_of_corpus_range_error():
    far = drik.Date(2500, 1, 1)  # beyond the 2400-01-01 corpus edge
    jd_far = utils.julian_day_number(far, TOB)
    with pytest.raises(OutOfCorpusRangeError):
        sl.compute_special_lagnas(jd_far, far, TOB, "lahiri", lat=LAT, lon=LON, tz=TZ)


@pytest.mark.parametrize("exc", [SwissBackendError("x"), OutOfCorpusRangeError("x"), WindowUncheckedError("x")],
                         ids=lambda e: type(e).__name__)
@pytest.mark.parametrize("target", ["indu_lagna", "sree_lagna", "kunda_lagna"])
def test_every_backend_error_class_propagates_from_a_delegated_lagna(monkeypatch, exc, target):
    """The delegated (unguarded-by-helper) lagnas go through the same handler: all three classes
    propagate, wherever in the batch they surface."""
    def _boom(*a, **k):
        raise exc

    monkeypatch.setattr(sl.drik, target, _boom)
    with pytest.raises(type(exc)):
        sl.compute_special_lagnas(JD, DOB, TOB, "lahiri", lat=LAT, lon=LON, tz=TZ)


def test_varnada_handler_propagates_backend_error(monkeypatch):
    def _boom(*a, **k):
        raise SwissBackendError("backend gone")

    monkeypatch.setattr(sl, "_varnada_lagna_bv_raman", _boom)
    with pytest.raises(SwissBackendError):
        sl.compute_special_lagnas(JD, DOB, TOB, "lahiri", lat=LAT, lon=LON, tz=TZ)


def test_backend_failure_tuple_covers_all_three_classes():
    assert set(BACKEND_FAILURE_ERRORS) == {SwissBackendError, OutOfCorpusRangeError, WindowUncheckedError}
    # a plain computation error is NOT one of them (it must keep degrading per lagna)
    assert not issubclass(ValueError, BACKEND_FAILURE_ERRORS)
    assert not issubclass(ZeroDivisionError, BACKEND_FAILURE_ERRORS)


# ── genuine "not defined" still degrades per lagna and floors ─────────────────


def test_genuine_not_defined_error_still_yields_an_error_entry_and_a_floored_row(monkeypatch):
    def _undefined(*a, **k):
        raise ValueError("indu_lagna undefined for this chart")

    monkeypatch.setattr(sl.drik, "indu_lagna", _undefined)
    out = sl.compute_special_lagnas(JD, DOB, TOB, "lahiri", lat=LAT, lon=LON, tz=TZ)
    assert "error" in out["indu_lagna"] and "indu_lagna failed" in out["indu_lagna"]["error"]
    # the other lagnas are unaffected (per-lagna isolation is intact)
    for k in _DELEGATED:
        assert "longitude_deg" in out[k], k

    rows = W._build_special_lagnas_rows(
        {"special_lagnas": out}, {"LAGNA": 10.0}, CHART_ID, AYA_KEY, BUILD_ID, "test-eng", {},
    )
    indu = [r for r in rows if r["fact_subject"] == "INDU_LAGNA"]
    assert len(indu) == 1
    assert indu[0]["verification_pass_status"] == FLOORED
    assert indu[0]["fact_value_num"] is None
    assert "[EXTERNAL_COMPUTATION_REQUIRED]" in indu[0]["formula_provenance_text"]
    # and the computed ones are real rows, not floored
    assert any(r["fact_subject"] == "BHAVA_LAGNA" and r["fact_value_num"] is not None for r in rows)


# ── ga_sensitive: the real per-ayanamsha builder, backend unset ───────────────


def test_orchestrator_substep_with_backend_unset_raises_and_writes_nothing(backend_unset, monkeypatch, no_insert):
    """The orchestrator path (``build_ga_sensitive_for_ayanamsha``): REAL ``compute_chart`` against the
    REAL adapter with ``SE_EPHE_PATH`` unset -> ``SwissBackendError`` propagates; no row is written and
    the connection is never touched."""
    monkeypatch.setattr(W, "_SIGN_LORDS", {"Aries": "Mars"})
    monkeypatch.setattr(W, "_NAK_LORDS", ["Ketu"])
    conn = _RecordingConn()
    with pytest.raises(SwissBackendError):
        W.build_ga_sensitive_for_ayanamsha(
            ayanamsha_key=AYA_KEY, ayanamsha_id="lahiri", chart_id=CHART_ID, build_id=BUILD_ID,
            conn=conn, birth_params=dict(_BIRTH), prereqs={}, eng_ver="test-eng",
        )
    assert no_insert == []
    assert conn.calls == []


def test_row_builder_with_backend_unset_raises_instead_of_returning_floored_rows(backend_unset, monkeypatch):
    monkeypatch.setattr(W, "_SIGN_LORDS", {"Aries": "Mars"})
    monkeypatch.setattr(W, "_NAK_LORDS", ["Ketu"])
    with pytest.raises(SwissBackendError):
        W._build_all_sensitive_rows_for_ayanamsha(
            ayanamsha_key=AYA_KEY, ayanamsha_id="lahiri", chart_id=CHART_ID, build_id=BUILD_ID,
            eng_ver="test-eng", birth_params=dict(_BIRTH), prereqs={}, halt_log_path="HALT.md",
        )


def test_legacy_full_build_with_backend_unset_raises_not_a_forensic_gate_summary(backend_unset, monkeypatch,
                                                                               no_insert):
    """``build_ga_sensitive`` (legacy CLI entry): ``SwissBackendError`` is a ``RuntimeError``; it used to be
    reported as "GA5 FORENSIC gate FAIL" (and halt-logged as one).  It now raises."""
    conn = _RecordingConn()
    with pytest.raises(SwissBackendError):
        W.build_ga_sensitive(chart_id=CHART_ID, build_id=BUILD_ID, conn=conn, birth_params=dict(_BIRTH))
    assert no_insert == []
    assert conn.calls == []


def test_legacy_full_build_per_ayanamsha_loop_propagates_backend_error(monkeypatch, no_insert):
    """The per-ayanamsha ``except Exception`` of ``build_ga_sensitive`` used to record a FAIL summary for a
    backend failure; it propagates now (the preflight passes: backend is fine until the builder runs)."""
    monkeypatch.setattr(W, "compute_chart", lambda inputs, ayanamsha_id: {})
    monkeypatch.setattr(W, "check_prerequisites", lambda conn=None: {"G14_SAHAM": True, "G44_NADI": False,
                                                                     "G41_LAL_KITAB": False})
    monkeypatch.setattr(W, "_load_l0_refs", lambda conn: None)

    def _builder(**kw):
        raise OutOfCorpusRangeError("JD outside the corpus window")

    monkeypatch.setattr(W, "_build_all_sensitive_rows_for_ayanamsha", _builder)
    conn = _RecordingConn()
    with pytest.raises(OutOfCorpusRangeError):
        W.build_ga_sensitive(chart_id=CHART_ID, build_id=BUILD_ID, conn=conn, birth_params=dict(_BIRTH))
    assert no_insert == []


def test_value_error_in_per_ayanamsha_loop_still_halts_with_a_summary(monkeypatch, no_insert):
    """Behaviour unchanged for every non-backend error: a ValueError is still a HALT summary."""
    monkeypatch.setattr(W, "compute_chart", lambda inputs, ayanamsha_id: {})
    monkeypatch.setattr(W, "check_prerequisites", lambda conn=None: {"G14_SAHAM": True, "G44_NADI": False,
                                                                     "G41_LAL_KITAB": False})
    monkeypatch.setattr(W, "_load_l0_refs", lambda conn: None)

    def _builder(**kw):
        raise ValueError("a genuine validation halt")

    monkeypatch.setattr(W, "_build_all_sensitive_rows_for_ayanamsha", _builder)
    summary = W.build_ga_sensitive(chart_id=CHART_ID, build_id=BUILD_ID, conn=_RecordingConn(),
                                   birth_params=dict(_BIRTH))
    assert summary["status"] == "HALT"
    assert no_insert == []


# ── with the backend correct, special lagnas are real values (behaviour identical) ──


def test_backend_correct_gives_real_special_lagnas_and_no_floored_rows():
    import os

    if not os.environ.get("SE_EPHE_PATH", "").strip():
        pytest.skip("no .se1 corpus configured (SE_EPHE_PATH); the fail-closed tests above cover that case")
    out = sl.compute_special_lagnas(JD, DOB, TOB, "lahiri", lat=LAT, lon=LON, tz=TZ)
    for name, entry in out.items():
        assert "error" not in entry, (name, entry)
    rows = W._build_special_lagnas_rows(
        {"special_lagnas": out}, {"LAGNA": 10.0}, CHART_ID, AYA_KEY, BUILD_ID, "test-eng", {},
    )
    assert rows and not [r for r in rows if r["verification_pass_status"] == FLOORED]
