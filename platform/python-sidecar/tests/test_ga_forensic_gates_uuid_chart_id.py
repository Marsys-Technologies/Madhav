"""Every ga_* FORENSIC gate RUNS when chart_id is a real ``uuid.UUID`` (REHEARSAL-LINUX P1 follow-up).

Defect: on the real orchestrator path ``ctx.config['chart_id']`` is a ``uuid.UUID`` (psycopg decodes the
``build_runs.chart_id`` uuid column). Every ``chart_id == CANONICAL_CHART_ID`` gate compared that UUID with a ``str``
constant, which is always False, so the native-anchored FORENSIC gate was SKIPPED while the writers still reported
``forensic_pass = True``. The fix is ``str(chart_id)`` at the adapter AND at each gate site (the adapter files are not part of
a writer's code digest, so the gate site carries its own conversion).

For EVERY gate (positions, panchanga, strength, structural x2, sensitive x2, vargas, dashas x3, tajaka, vichara, yoga x2,
nakshatra, transit_anchors) these tests drive the real code with a uuid.UUID, a str (parity) and a non-canonical chart:

* canonical + correct anchors: the gate EXECUTES (log line ``FORENSIC gate <asset> executed passed=True chart=canonical``
  plus, where a gate function exists, a spy on it) and the run proceeds past it;
* canonical + an ALTERED anchor: the run fails the way the code always did (raises, or ``FORENSIC_FAIL`` for ga_vargas) and logs
  ``passed=False``;
* non-canonical: the gate is skipped silently (nothing at INFO, the run is not halted by the altered anchor).

Two gates assert NOTHING (ga_vichara, and ga_yoga's early guard): their line is ``executed assertion=none`` and never
``passed=True`` (CLAUDE.md N.8, SS ruling); they have dedicated tests and no stored/returned pass flag.

``via='writer'`` calls the writer entry point directly (so it fails if the gate-site ``str()`` is reverted);
``via='adapter'`` drives the REAL registered orchestrator adapter with the UUID in ``ctx.config`` (so it fails if BOTH the
adapter and gate-site ``str()`` are reverted); the dedicated ``test_adapter_hands_the_writer_a_str`` tests fail if only the
adapter conversion is reverted. No birth data: charts are synthetic dicts carrying only the FORENSIC *anchor* values.
"""
from __future__ import annotations

import logging
import pathlib
import sys
import uuid
from datetime import date
from typing import Any, Callable

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from ga_writers import ga_dashas_writer as gdw  # noqa: E402
from ga_writers import ga_panchanga_writer as gpaw  # noqa: E402
from ga_writers import ga_positions_writer as gpw  # noqa: E402
from ga_writers import ga_sensitive_writer as gsew  # noqa: E402
from ga_writers import ga_strength_writer as gstw  # noqa: E402
from ga_writers import ga_structural_writer as gstrw  # noqa: E402
from ga_writers import ga_tajaka_writer as gtw  # noqa: E402
from ga_writers import ga_vargas_writer as gvw  # noqa: E402
from ga_writers import ga_vichara_writer as gvichw  # noqa: E402
from ga_writers import ga_yoga_writer as gyw  # noqa: E402
from pipeline.orchestrator.writers import (  # noqa: E402
    ContextSpec, SubStep, discover_all, get_writer,
)
from pipeline.orchestrator.writers import ga_nakshatra as gnak  # noqa: E402
from pipeline.orchestrator.writers import ga_transit_anchors as gta  # noqa: E402

CANON = "482012f1-710e-4a25-994a-93821f5871aa"        # a chart id, not a birth detail
CANON_UUID = uuid.UUID(CANON)
OTHER_UUID = uuid.UUID("aaaaaaaa-1111-4222-8333-000000000009")
AYA = "lahiri_chitrapaksha"
BUILD_ID = "build-forensic-gates"
# Synthetic, arbitrary: never the native's. Only the writers' `if not birth_params` guards read it here.
BIRTH = {
    "datetime_iso": "2011-02-06T11:00:00", "latitude_deg": 23.26, "longitude_deg": 77.41,
    "tz_offset_hours": 5.5, "place_name": "synthetic", "subject_label": "syn",
}


class _Stop(Exception):
    """Raised by a stub placed right AFTER a gate: 'the run got past the gate'."""


class _RecConn:
    def __init__(self) -> None:
        self.statements: list[tuple[str, tuple]] = []

    def cursor(self, *a, **k):
        return self

    def execute(self, sql, *args, **kwargs):
        self.statements.append((sql, args))
        return self

    def fetchall(self):
        return []

    def fetchone(self):
        return None

    def commit(self):
        pass

    def rollback(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _ctx(asset, chart_id, *, dry_run=False, conn=None) -> ContextSpec:
    return ContextSpec(asset_id=asset, build_id=BUILD_ID, db_conn=conn or _RecConn(),
                       config={"chart_id": chart_id, "birth_params": dict(BIRTH)}, dry_run=dry_run)


def _chart(good: bool) -> dict:
    """Synthetic chart_output carrying exactly the three anchors forensic_gate reads (Sun sign, Moon nakshatra, Lagna sign)."""
    return {
        "grahas": [
            {"name": "Sun", "sign": "Capricorn" if good else "Cancer"},
            {"name": "Moon", "sign": "Aquarius", "nakshatra": "Purva Bhadrapada" if good else "Ashwini",
             "nakshatra_id": 25 if good else 1},
        ],
        "ascendant": {"sign": "Aries" if good else "Taurus"},
        "provenance": {"jd_ut": 2450000.5},
    }


class _N:
    def __init__(self, name):
        self.name = name


def _pi(good: bool):
    """Synthetic PanchangaInstant: the five anchors panchanga_forensic_gate reads."""
    class PI:
        tithi = _N("Shukla Tritiya" if good else "Krishna Panchami")
        vara = _N("Ravivara" if good else "Somavara")
        yoga = _N("Shiva" if good else "Vishkambha")
        karana = _N("Garaja" if good else "Bava")
        nakshatra = _N("Purva Bhadrapada" if good else "Ashwini")
    return PI()


class Result:
    def __init__(self) -> None:
        self.exc: BaseException | None = None
        self.past_gate = False
        self.summary: Any = None
        self.gate_calls = 0

    @property
    def failed(self) -> bool:
        if self.exc is not None:
            return True
        return isinstance(self.summary, dict) and self.summary.get("status") == "FORENSIC_FAIL"


def _spy(monkeypatch, module, name, result: Result) -> None:
    real = getattr(module, name)

    def wrapper(*a, **k):
        result.gate_calls += 1
        return real(*a, **k)

    monkeypatch.setattr(module, name, wrapper)


def _stop(*a, **k):
    raise _Stop()


def _drive(result: Result, fn: Callable[[], Any]) -> Result:
    try:
        result.summary = fn()
    except _Stop:
        result.past_gate = True
    except BaseException as exc:  # noqa: BLE001 - the test classifies it
        result.exc = exc
    else:
        result.past_gate = True
    return result


# ── runners: (monkeypatch, chart_id, good, via) -> Result ─────────────────────────────────────────
# `via` is 'writer' (call the writer entry point) or 'adapter' (real registered adapter, UUID in ctx.config).

def r_positions(mp, chart_id, good, via):
    res = Result()
    mp.setattr(gpw, "compute_chart", lambda inputs, ayanamsha_id: _chart(good))
    mp.setattr(gpw, "_build_position_rows", lambda *a, **k: [])
    mp.setattr(gpw, "_build_chalit_rows", lambda *a, **k: [])
    mp.setattr(gpw, "_insert_chart_facts_rows", lambda conn, rows: 0)
    _spy(mp, gpw, "forensic_gate", res)
    if via == "writer":
        return _drive(res, lambda: gpw.build_ga_positions(chart_id, BUILD_ID, conn=_RecConn(), birth_params=dict(BIRTH)))
    discover_all()
    return _drive(res, lambda: get_writer("ga_positions")().run(_ctx("ga_positions", chart_id)))


def r_panchanga(mp, chart_id, good, via):
    import panchang_engine
    res = Result()
    mp.setattr(panchang_engine, "panchanga_instant", lambda *a, **k: _pi(good))
    mp.setattr(gpaw, "_emit_tithi", _stop)
    _spy(mp, gpaw, "panchanga_forensic_gate", res)
    if via == "writer":
        return _drive(res, lambda: gpaw.build_ga_panchanga(chart_id, BUILD_ID, conn=_RecConn(), birth_params=dict(BIRTH)))
    discover_all()
    return _drive(res, lambda: get_writer("ga_panchanga")().run(_ctx("ga_panchanga", chart_id)))


def r_strength(mp, chart_id, good, via):
    res = Result()
    mp.setattr(gstw, "compute_chart", lambda inputs, ayanamsha_id: _chart(good))
    mp.setattr(gstw, "_derive_shadbala_from_positions", _stop)
    _spy(mp, gstw, "forensic_gate", res)
    if via == "writer":
        return _drive(res, lambda: gstw.build_ga_strength(chart_id, BUILD_ID, conn=_RecConn(), birth_params=dict(BIRTH)))
    discover_all()
    return _drive(res, lambda: get_writer("ga_strength")().run(_ctx("ga_strength", chart_id)))


def r_structural_substep(mp, chart_id, good, via):
    res = Result()
    mp.setattr(gstrw, "compute_chart", lambda inputs, ayanamsha_id: _chart(good))
    mp.setattr(gstrw, "_validate_chart_output_complete", lambda co: None)
    mp.setattr(gstrw, "_load_yoga_catalog", _stop)
    _spy(mp, gstrw, "forensic_gate", res)
    if via == "writer":
        return _drive(res, lambda: gstrw.build_ga_structural_substep(
            chart_id, BUILD_ID, AYA, _RecConn(), birth_params=dict(BIRTH)))
    discover_all()
    return _drive(res, lambda: get_writer("ga_structural")().run_substep(
        _ctx("ga_structural", chart_id), SubStep(key=f"ayanamsha_{AYA}")))


def r_structural_full(mp, chart_id, good, via):
    res = Result()
    mp.setattr(gstrw, "compute_chart", lambda inputs, ayanamsha_id: _chart(good))
    mp.setattr(gstrw, "_validate_chart_output_complete", lambda co: None)
    mp.setattr(gstrw, "_load_yoga_catalog", lambda conn: [])
    mp.setattr(gstrw, "_load_dosha_catalog", lambda conn: [])
    mp.setattr(gstrw, "_build_aspect_rows", _stop)
    _spy(mp, gstrw, "forensic_gate", res)
    return _drive(res, lambda: gstrw.build_ga_structural(
        chart_id, BUILD_ID, conn=_RecConn(), birth_params=dict(BIRTH), skip_upstream_check=True))


def r_sensitive_aya(mp, chart_id, good, via):
    res = Result()
    mp.setattr(gsew, "compute_chart", lambda inputs, ayanamsha_id: _chart(good))
    mp.setattr(gsew, "check_prerequisites", lambda conn=None: {})
    mp.setattr(gsew, "_load_l0_refs", lambda conn: None)
    mp.setattr(gsew, "_SIGN_LORDS", {"x": 1}, raising=False)
    mp.setattr(gsew, "_NAK_LORDS", {"x": 1}, raising=False)
    _spy(mp, gsew, "forensic_gate", res)
    # Past the gate the builder reads graha longitudes; the synthetic chart has none -> its own ValueError == "got past the gate".
    def run():
        try:
            if via == "writer":
                return gsew.build_ga_sensitive_for_ayanamsha(
                    AYA, "lahiri", chart_id, BUILD_ID, _RecConn(), dict(BIRTH), {}, "eng")
            discover_all()
            return get_writer("ga_sensitive")().run_substep(
                _ctx("ga_sensitive", chart_id), SubStep(key=f"ayanamsha:{AYA}"))
        except ValueError as exc:
            if "longitude missing" in str(exc):
                raise _Stop() from exc
            raise
    return _drive(res, run)


def r_sensitive_preflight(mp, chart_id, good, via):
    res = Result()
    mp.setattr(gsew, "compute_chart", lambda inputs, ayanamsha_id: _chart(good))
    mp.setattr(gsew, "check_prerequisites", _stop)
    _spy(mp, gsew, "forensic_gate", res)

    def run():
        out = gsew.build_ga_sensitive(chart_id, BUILD_ID, conn=_RecConn(), birth_params=dict(BIRTH))
        if out.get("status") == "FAIL":      # the gate's RuntimeError is reported as a FAIL summary by this entry point
            raise RuntimeError(out.get("forensic_failure"))
        return out
    return _drive(res, run)


def r_vargas(mp, chart_id, good, via):
    res = Result()
    d1 = {"Sun": {"sign": "Capricorn" if good else "Cancer"}, "Lagna": {"sign": "Aries" if good else "Taurus"}}
    mp.setattr(gvw, "_compute_varga_positions", lambda *a, **k: ({"D1": d1}, {}))
    mp.setattr(gvw, "_read_jaimini_karakas", _stop)
    mp.setattr(gvw, "_write_halt_log", lambda *a, **k: None)
    # F-A2: the writer reads the live unique-index definition before it writes; this test is about the FORENSIC gate, not the index grain
    # (the index-grain guard has its own tests in ga_writers/__tests__/test_ga_vargas_key_widening.py), so the recording conn need not answer it.
    mp.setattr(gvw, "assert_unique_key_grain", lambda conn: None)
    if via == "writer":
        return _drive(res, lambda: gvw.build_ga_vargas(
            chart_id, BUILD_ID, conn=_RecConn(), birth_params=dict(BIRTH), ayanamsha_subset=[AYA]))
    discover_all()
    return _drive(res, lambda: get_writer("ga_vargas")().run_substep(_ctx("ga_vargas", chart_id), SubStep(key=AYA)))


def _dashas_stubs(mp, moon_sid):
    mp.setattr(gdw, "_load_nakshatra_lords_l0", lambda conn: None)
    mp.setattr(gdw, "_activate_natal_context", lambda *a, **k: None)
    mp.setattr(gdw, "_activate_karaka_roles", lambda *a, **k: None)
    mp.setattr(gdw, "_get_moon_position", lambda aya, birth: (moon_sid, 2450000.5))
    mp.setattr(gdw, "compute_vimshottari", _stop)


def r_dashas_build_system(mp, chart_id, good, via):
    res = Result()
    _dashas_stubs(mp, 325.0 if good else 100.0)        # 325 deg sidereal = Purva Bhadrapada; 100 deg = Ashlesha
    _spy(mp, gdw, "_assert_forensic_vimshottari", res)
    if via == "writer":
        return _drive(res, lambda: gdw.build_system("vimshottari", AYA, chart_id, BUILD_ID, conn=_RecConn(), birth_params=dict(BIRTH)))
    discover_all()
    return _drive(res, lambda: get_writer("ga_dashas")().run_substep(_ctx("ga_dashas", chart_id), SubStep(key=f"vimshottari:{AYA}")))


def r_dashas_verify(mp, chart_id, good, via):
    """_verify_vimshottari Pass 2: the period covering the native birth date must be Jupiter's. One L1 row spanning all
    dates, so no birth date is needed in this test."""
    res = Result()
    rows = [{"level_n": 1, "start_date": date.min, "end_date": date.max,
             "lord_graha": "Jupiter" if good else "Saturn", "duration_days": 6000}]
    return _drive(res, lambda: gdw._verify_vimshottari(rows, 325.0, chart_id))


def r_dashas_compute(mp, chart_id, good, via):
    """compute_vimshottari: the Moon-nakshatra starting lord must be Jupiter. Built, not stubbed, to the first row."""
    res = Result()
    mp.setattr(gdw, "_find_cycle_start_for_window", _stop)      # first call after the gate
    return _drive(res, lambda: gdw.compute_vimshottari(325.0 if good else 100.0, 2450000.5, AYA, chart_id, BUILD_ID))


def r_tajaka(mp, chart_id, good, via):
    res = Result()
    mp.setattr(gtw, "CANONICAL_AYANAMSHAS", {AYA: "lahiri"})
    mp.setattr(gtw, "compute_chart", lambda inputs, ayanamsha_id: {"grahas": [{"name": "Sun", "longitude": 10.0}]})
    mp.setattr(gtw, "replace_prior_tajik_varsha", lambda conn, rows: 0)
    mp.setattr(gtw, "_insert_rows", lambda conn, rows: len(rows))

    def compute_one(conn, cid, aya, adapter, v, natal, natal_sun, build_id, birth=None):
        return {"_muntha_sign": gtw.FORENSIC_MUNTHA_SIGN if good else "Cancer",
                "_muntha_house_from_natal": gtw.FORENSIC_MUNTHA_HOUSE,
                "_muntha_lord": gtw.FORENSIC_MUNTHA_LORD,
                "verification_pass_status": "single", "ephemeris_audit_jsonb": {}}
    mp.setattr(gtw, "_compute_one", compute_one)
    v = gtw.FORENSIC_VARSHA_YEAR
    if via == "writer":
        return _drive(res, lambda: gtw.build_ga_tajaka(
            chart_id, BUILD_ID, conn=_RecConn(), birth_params=dict(BIRTH), reference_year=2012, min_varsha=v, max_varsha=v))
    discover_all()
    mp.setattr(gtw, "_effective_reference_year", lambda ry: 2012)
    mp.setattr(gtw, "build_ga_tajaka", (lambda real: lambda *a, **k: real(*a, **{**k, "min_varsha": v, "max_varsha": v}))(gtw.build_ga_tajaka))
    return _drive(res, lambda: get_writer("ga_tajaka")().run(_ctx("ga_tajaka", chart_id)))


def r_vichara(mp, chart_id, good, via):
    """ga_vichara's 'gate' is a log-only branch (no anchor is asserted anywhere in this writer)."""
    res = Result()
    if via == "writer":
        return _drive(res, lambda: gvichw.build_ga_vichara_substep(chart_id, BUILD_ID, AYA, _RecConn(), dry_run=True))
    discover_all()
    return _drive(res, lambda: get_writer("ga_vichara")().run_substep(
        _ctx("ga_vichara", chart_id, dry_run=True), SubStep(key=f"ayanamsha_{AYA}")))


def _yoga_stubs(mp, fired: int):
    mp.setattr(gyw, "_load_chart_facts", lambda conn, cid, aya: [{"x": 1}])
    mp.setattr(gyw, "_load_yoga_catalog", lambda conn: [{"canonical_id": "x"}])
    mp.setattr(gyw, "_load_yoga_families", lambda conn: {})
    mp.setattr(gyw, "_load_shadbala_map", lambda conn, cid, aya: {})
    mp.setattr(gyw, "ChartState", lambda facts: object())
    mp.setattr(gyw, "_d1_positions_from_state", lambda st: {})
    mp.setattr(gyw, "_load_d9_positions", lambda conn, cid, aya: {})
    mp.setattr(gyw, "_load_special_states", lambda facts: {})
    mp.setattr(gyw, "_delete_prior_yoga_firings", lambda conn, cid, aya: 0)
    mp.setattr(gyw, "_evaluate_yoga", lambda yoga, state: None)
    mp.setattr(gyw, "_build_nbry_firing", lambda *a, **k: 0)
    mp.setattr(gyw, "DETECTOR_INSERT_IDS", ())
    mp.setattr(gyw, "_build_karakamsha_firings", lambda *a, **k: fired)


def r_yoga_assert(mp, chart_id, good, via):
    """ga_yoga's real assertion: the native must fire >=1 yoga (0 == missing chart_facts input)."""
    res = Result()
    _yoga_stubs(mp, 3 if good else 0)
    _spy(mp, gyw, "_forensic_assert", res)
    if via == "writer":
        return _drive(res, lambda: gyw.build_ga_yoga_substep(chart_id, BUILD_ID, AYA, _RecConn()))
    discover_all()
    return _drive(res, lambda: get_writer("ga_yoga")().run_substep(_ctx("ga_yoga", chart_id), SubStep(key=f"ayanamsha_{AYA}")))


def r_nakshatra(mp, chart_id, good, via):
    res = Result()
    mp.setattr(gnak, "compute_chart", lambda inputs, ayanamsha_id: _chart(good))
    mp.setattr(gnak, "emit_nakshatra_join", _stop)
    _spy(mp, gnak, "_forensic_gate", res)
    if via == "writer":
        return _drive(res, lambda: gnak._run_ayanamsha_pass(
            _ctx("ga_nakshatra", chart_id), AYA, "lahiri", {}, {}, chart_id, dict(BIRTH)))
    discover_all()
    mp.setattr(gnak, "_check_bg_nakshatra_present", lambda conn: True)
    mp.setattr(gnak, "_fetch_bg_nakshatra", lambda conn: ({}, {}))
    mp.setattr(gnak, "load_kp_divisions", lambda conn: [])
    mp.setattr(gnak, "_fetch_sign_lords", lambda conn: {})
    return _drive(res, lambda: get_writer("ga_nakshatra")().run_substep(
        _ctx("ga_nakshatra", chart_id), SubStep(key=f"ayanamsha:{AYA}")))


class _TaCur:
    """Cursor for ga_transit_anchors: one graha_position row set (Moon nakshatra good/bad), STOP at the DELETE."""
    def __init__(self, good):
        self.good = good
        self._rows: list = []

    def __enter__(self):
        return self

    def __exit__(self, *e):
        return False

    def execute(self, sql, params=None):
        if sql.lstrip().upper().startswith("DELETE"):
            raise _Stop()
        self._rows = []
        if "FROM chart_facts" in sql:
            subjects = gta._SUBJECT_TO_GRAHA
            for subject, graha in subjects.items():
                nak = "Purva Bhadrapada" if (graha != "moon" or self.good) else "Ashwini"
                self._rows += [(subject, "sign", "Aquarius", None),
                               (subject, "longitude_sidereal", None, 300.0),
                               (subject, "nakshatra", nak, None)]

    def fetchall(self):
        return self._rows


class _TaConn:
    def __init__(self, good):
        self.good = good

    def cursor(self, *a, **k):
        return _TaCur(self.good)


def r_transit_anchors(mp, chart_id, good, via):
    res = Result()
    discover_all()
    ctx = ContextSpec(asset_id="ga_transit_anchors", build_id=BUILD_ID, db_conn=_TaConn(good),
                      config={"chart_id": chart_id, "birth_params": dict(BIRTH)})
    return _drive(res, lambda: get_writer("ga_transit_anchors")().run_substep(ctx, SubStep(key=f"ayanamsha_{AYA}")))


ALL = "adapter writer".split()
ADAPTER_ONLY = ["adapter"]
WRITER_ONLY = ["writer"]

#: asset (log name), runner, vias, whether an altered anchor exists / makes the run fail, has a gate-function spy
GATES: list[tuple[str, str, Callable, list[str], bool, bool]] = [
    # id,                  log asset,           runner,                 vias,          anchor-asserting, spy
    ("positions",          "ga_positions",      r_positions,            ALL,           True,  True),
    ("panchanga",          "ga_panchanga",      r_panchanga,            ALL,           True,  True),
    ("strength",           "ga_strength",       r_strength,             ALL,           True,  True),
    ("structural_substep", "ga_structural",     r_structural_substep,   ALL,           True,  True),
    ("structural_full",    "ga_structural",     r_structural_full,      WRITER_ONLY,   True,  True),
    ("sensitive_aya",      "ga_sensitive",      r_sensitive_aya,        ALL,           True,  True),
    ("sensitive_preflight", "ga_sensitive preflight", r_sensitive_preflight, WRITER_ONLY, True, True),
    ("vargas",             "ga_vargas",         r_vargas,               ALL,           True,  False),
    ("dashas_build_system", "ga_dashas",        r_dashas_build_system,  ALL,           True,  True),
    ("dashas_verify",      None,                r_dashas_verify,        WRITER_ONLY,   True,  False),
    ("dashas_compute",     None,                r_dashas_compute,       WRITER_ONLY,   True,  False),
    ("tajaka",             "ga_tajaka",         r_tajaka,               ALL,           True,  False),
    # vichara asserts nothing: its log line is `assertion=none`, never `passed=True`, so the generic passed=True/False log
    # checks are off for it (asset=None) and the dedicated assertion=none tests below own its log contract.
    ("vichara",            None,                r_vichara,              ALL,           False, False),
    ("yoga_assert",        "ga_yoga",           r_yoga_assert,          ALL,           True,  True),
    ("nakshatra",          "ga_nakshatra",      r_nakshatra,            ALL,           True,  True),
    ("transit_anchors",    "ga_transit_anchors", r_transit_anchors,     ADAPTER_ONLY,  True,  False),
]

_CASES = [(g, via) for g in GATES for via in g[3]]
_IDS = [f"{g[0]}-{via}" for g, via in _CASES]


def _executed(caplog, asset, passed) -> list[str]:
    want = f"FORENSIC gate {asset} executed passed={passed} chart=canonical"
    return [r.getMessage() for r in caplog.records if r.getMessage().startswith(want)]


def _any_executed(caplog, asset) -> list[str]:
    return [r.getMessage() for r in caplog.records
            if r.levelno >= logging.INFO and r.getMessage().startswith(f"FORENSIC gate {asset} executed")]


@pytest.mark.parametrize("chart_kind", ["uuid", "str"])
@pytest.mark.parametrize("case", _CASES, ids=_IDS)
def test_gate_executes_and_passes_on_correct_anchors(case, chart_kind, monkeypatch, caplog):
    (_gid, asset, runner, _vias, _anchors, has_spy), via = case
    caplog.set_level(logging.DEBUG)
    chart_id = CANON_UUID if chart_kind == "uuid" else CANON
    res = runner(monkeypatch, chart_id, True, via)
    assert res.exc is None, f"correct anchors must not fail the run: {res.exc!r}"
    assert res.past_gate, "the run must proceed past the gate"
    if has_spy:
        assert res.gate_calls >= 1, "the gate function never ran -> the gate was SKIPPED for this chart_id"
    if asset is not None:
        lines = _executed(caplog, asset, True)
        assert lines, (f"no 'FORENSIC gate {asset} executed passed=True chart=canonical' line; got "
                       f"{[r.getMessage() for r in caplog.records if 'FORENSIC gate' in r.getMessage()]}")


@pytest.mark.parametrize("chart_kind", ["uuid", "str"])
@pytest.mark.parametrize("case", [c for c in _CASES if c[0][4]], ids=[i for c, i in zip(_CASES, _IDS) if c[0][4]])
def test_gate_fails_the_run_on_an_altered_anchor(case, chart_kind, monkeypatch, caplog):
    (_gid, asset, runner, _vias, _anchors, has_spy), via = case
    caplog.set_level(logging.DEBUG)
    chart_id = CANON_UUID if chart_kind == "uuid" else CANON
    res = runner(monkeypatch, chart_id, False, via)
    assert res.failed, "an altered FORENSIC anchor on the canonical chart must fail the run (the gate was skipped)"
    assert not res.past_gate or res.summary is not None   # a halt, not a fall-through
    if has_spy:
        assert res.gate_calls >= 1
    if asset is not None:
        assert _executed(caplog, asset, False), "the failing gate must log 'executed passed=False'"
        assert not _executed(caplog, asset, True)


@pytest.mark.parametrize("case", _CASES, ids=_IDS)
def test_non_canonical_chart_skips_the_gate_silently(case, monkeypatch, caplog):
    """No change for other charts: the altered anchor is NOT asserted and nothing is logged at INFO or above."""
    (_gid, asset, runner, _vias, _anchors, has_spy), via = case
    caplog.set_level(logging.DEBUG)
    res = runner(monkeypatch, OTHER_UUID, False, via)
    assert res.exc is None and not res.failed, f"non-canonical charts are not gated: {res.exc!r}"
    assert res.past_gate
    if has_spy:
        assert res.gate_calls == 0
    if asset is not None:
        assert not _any_executed(caplog, asset), "no 'executed' line for a skipped gate"
        noisy = [r.getMessage() for r in caplog.records
                 if r.levelno >= logging.INFO and r.getMessage().startswith("FORENSIC gate")]
        assert noisy == [], f"skipped gate must be silent at INFO+, got {noisy}"


# ── the adapter-level half of the fix ───────────────────────────────────────────────────────────────

def _adapter_receives(monkeypatch, asset, patch_target, attr, call):
    """Spy on the writer entry point an adapter calls and return the chart_id it was handed."""
    handed: list[Any] = []
    real = getattr(patch_target, attr)

    def spy(*a, **k):
        cid = k.get("chart_id", a[0] if a else None)
        handed.append(cid)
        raise _Stop()
    monkeypatch.setattr(patch_target, attr, spy)
    discover_all()
    try:
        call()
    except _Stop:
        pass
    assert real is not None
    return handed


@pytest.mark.parametrize("asset,module,attr,call", [
    ("ga_positions", gpw, "build_ga_positions", lambda: get_writer("ga_positions")().run(_ctx("ga_positions", CANON_UUID))),
    ("ga_panchanga", gpaw, "build_ga_panchanga", lambda: get_writer("ga_panchanga")().run(_ctx("ga_panchanga", CANON_UUID))),
    ("ga_strength", gstw, "build_ga_strength", lambda: get_writer("ga_strength")().run(_ctx("ga_strength", CANON_UUID))),
    ("ga_structural", gstrw, "build_ga_structural_substep",
     lambda: get_writer("ga_structural")().run_substep(_ctx("ga_structural", CANON_UUID), SubStep(key=f"ayanamsha_{AYA}"))),
    ("ga_sensitive", gsew, "build_ga_sensitive_for_ayanamsha",
     lambda: _run_sensitive_adapter()),
    ("ga_vargas", gvw, "build_ga_vargas",
     lambda: get_writer("ga_vargas")().run_substep(_ctx("ga_vargas", CANON_UUID), SubStep(key=AYA))),
    ("ga_vichara", gvichw, "build_ga_vichara_substep",
     lambda: get_writer("ga_vichara")().run_substep(_ctx("ga_vichara", CANON_UUID), SubStep(key=f"ayanamsha_{AYA}"))),
    ("ga_yoga", gyw, "build_ga_yoga_substep",
     lambda: get_writer("ga_yoga")().run_substep(_ctx("ga_yoga", CANON_UUID), SubStep(key=f"ayanamsha_{AYA}"))),
], ids=lambda v: v if isinstance(v, str) else "")
def test_adapter_hands_the_writer_a_str(asset, module, attr, call, monkeypatch):
    """Adapter boundary: the writer receives str(UUID), the canonical text form (so the gate compares str with str)."""
    monkeypatch.setattr(gsew, "get_ga_sensitive_context", lambda birth_params, conn=None: ({}, "eng"), raising=False)
    handed = _adapter_receives(monkeypatch, asset, module, attr, call)
    assert handed == [CANON], f"{asset}: adapter handed {handed!r}"
    assert type(handed[0]) is str


def _run_sensitive_adapter():
    # the adapter imports get_ga_sensitive_context from the writer module at call time
    return get_writer("ga_sensitive")().run_substep(_ctx("ga_sensitive", CANON_UUID), SubStep(key=f"ayanamsha:{AYA}"))


def test_adapter_nakshatra_gate_runs_on_the_str_the_adapter_hands_over(monkeypatch):
    seen: list[Any] = []

    def spy(ctx, canonical_id, adapter_id, nak_rows, pada_rows, chart_id, birth_params, **kw):
        seen.append(chart_id)
        raise _Stop()
    monkeypatch.setattr(gnak, "_run_ayanamsha_pass", spy)
    monkeypatch.setattr(gnak, "_check_bg_nakshatra_present", lambda conn: True)
    monkeypatch.setattr(gnak, "_fetch_bg_nakshatra", lambda conn: ({}, {}))
    monkeypatch.setattr(gnak, "load_kp_divisions", lambda conn: [])
    monkeypatch.setattr(gnak, "_fetch_sign_lords", lambda conn: {})
    discover_all()
    with pytest.raises(_Stop):
        get_writer("ga_nakshatra")().run_substep(_ctx("ga_nakshatra", CANON_UUID), SubStep(key=f"ayanamsha:{AYA}"))
    assert seen == [CANON] and type(seen[0]) is str


# ── log-line format + the two sites that previously only logged ───────────────────────────────────────

def r_yoga_guard(mp, chart_id, good, via):
    """ga_yoga's EARLY guard (before dry_run): only logs, asserts nothing. dry_run returns right after it, so the real
    post-insert `_forensic_assert` gate never runs here and cannot contribute a `passed=` line."""
    res = Result()
    _spy(mp, gyw, "_forensic_assert", res)
    if via == "writer":
        return _drive(res, lambda: gyw.build_ga_yoga_substep(chart_id, BUILD_ID, AYA, _RecConn(), dry_run=True))
    discover_all()
    return _drive(res, lambda: get_writer("ga_yoga")().run_substep(
        _ctx("ga_yoga", chart_id, dry_run=True), SubStep(key=f"ayanamsha_{AYA}")))


#: the two gates that assert nothing (SS ruling, CLAUDE.md N.8): (asset, runner)
NO_ASSERTION_GATES = [("ga_vichara", r_vichara), ("ga_yoga", r_yoga_guard)]
_NA_CASES = [(a, r, v) for a, r in NO_ASSERTION_GATES for v in ALL]
_NA_IDS = [f"{a}-{v}" for a, _r, v in _NA_CASES]


def _gate_msgs(caplog, asset) -> list[tuple[int, str]]:
    return [(r.levelno, r.getMessage()) for r in caplog.records if r.getMessage().startswith(f"FORENSIC gate {asset} ")]


@pytest.mark.parametrize("chart_kind", ["uuid", "str"])
@pytest.mark.parametrize("asset,runner,via", _NA_CASES, ids=_NA_IDS)
def test_no_assertion_gate_says_assertion_none_never_passed(asset, runner, via, chart_kind, monkeypatch, caplog):
    """A gate that asserts nothing must never read as passed (CLAUDE.md N.8)."""
    caplog.set_level(logging.DEBUG)
    chart_id = CANON_UUID if chart_kind == "uuid" else CANON
    res = runner(monkeypatch, chart_id, True, via)
    assert res.exc is None and res.past_gate
    msgs = _gate_msgs(caplog, asset)
    assert msgs == [(logging.INFO, f"FORENSIC gate {asset} executed assertion=none chart=canonical")], msgs
    assert not any("passed=" in m for _lvl, m in msgs)
    assert not any("passed=True" in r.getMessage() for r in caplog.records), "nothing may claim passed=True"
    assert res.gate_calls == 0, "the (real) post-insert yoga assertion must not run in this path"


@pytest.mark.parametrize("asset,runner,via", _NA_CASES, ids=_NA_IDS)
def test_no_assertion_gate_returns_and_stores_no_pass_flag(asset, runner, via, monkeypatch):
    """No stored/returned pass signal: the builder returns a plain row count, the adapter's WriterResult carries no
    forensic/pass field and no truthy forensic-ish value (None / absent is the only allowed state)."""
    import dataclasses
    box: dict[str, Any] = {}
    conn = _RecConn()
    monkeypatch.setattr(gyw, "_forensic_assert", lambda *a, **k: box.setdefault("assert_called", True))
    if via == "writer":
        fn = gvichw.build_ga_vichara_substep if asset == "ga_vichara" else gyw.build_ga_yoga_substep
        out = fn(CANON_UUID, BUILD_ID, AYA, conn, dry_run=True)
        assert type(out) is int and out == 0
    else:
        discover_all()
        out = get_writer(asset)().run_substep(_ctx(asset, CANON_UUID, dry_run=True, conn=conn), SubStep(key=f"ayanamsha_{AYA}"))
        fields = dataclasses.asdict(out)
        assert set(fields) == {"asset_id", "rows_inserted", "rows_updated", "rows_skipped", "duration_seconds", "notes"}
        assert not any(k for k in fields if "forensic" in k or "pass" in k)
        assert "forensic" not in str(fields["notes"]).lower() and "pass" not in str(fields["notes"]).lower()
    assert "assert_called" not in box
    stored = [sql for sql, _a in conn.statements if "forensic" in str(sql).lower()]
    assert stored == [], "no row/column/dict key may store a forensic pass signal"


@pytest.mark.parametrize("asset,runner,via", _NA_CASES, ids=_NA_IDS)
def test_no_assertion_gate_non_canonical_unchanged_silent_skip(asset, runner, via, monkeypatch, caplog):
    caplog.set_level(logging.DEBUG)
    res = runner(monkeypatch, OTHER_UUID, False, via)
    assert res.exc is None and not res.failed and res.past_gate
    assert [m for lvl, m in _gate_msgs(caplog, asset) if lvl >= logging.INFO] == []
    assert not any("assertion=none" in r.getMessage() and r.levelno >= logging.INFO for r in caplog.records)


def test_real_yoga_assertion_still_reports_passed_true_distinct_from_the_none_guard(monkeypatch, caplog):
    """The yoga post-insert gate is a REAL assertion: it still says passed=True; the early guard says assertion=none."""
    caplog.set_level(logging.INFO)
    res = r_yoga_assert(monkeypatch, CANON_UUID, True, "writer")
    assert res.exc is None and res.gate_calls == 1
    msgs = [m for _l, m in _gate_msgs(caplog, "ga_yoga")]
    assert "FORENSIC gate ga_yoga executed assertion=none chart=canonical" in msgs
    assert any(m.startswith("FORENSIC gate ga_yoga executed passed=True chart=canonical") for m in msgs)


def test_gate_log_line_format_is_exactly_the_documented_one(monkeypatch, caplog):
    caplog.set_level(logging.INFO)
    r_panchanga(monkeypatch, CANON_UUID, True, "writer")
    assert [r.getMessage() for r in caplog.records if r.getMessage().startswith("FORENSIC gate ga_panchanga")] == [
        "FORENSIC gate ga_panchanga executed passed=True chart=canonical"]


# ── _verify_vimshottari's verdict is a table/constant check, never the two-pass tier ──────────────────
# DASHA_TIER_CHECK P2 / CLAUDE.md N.8: nothing in _verify_vimshottari is a second implementation (the duration loop ends in a
# bare `pass`; the native-anchor check compares ONE stored row to the constant "Jupiter" and bypasses two_pass_verdict). Its
# verdict for the native is therefore CLASSICAL_MATCH. The stored vimshottari tier is NOT this value (it comes from
# _apply_vimshottari_independent_verification), so no column depends on it; it reaches only logs + the returned summary.

def _vim_l1_rows(lord: str) -> list[dict]:
    return [{"level_n": 1, "start_date": date.min, "end_date": date.max, "lord_graha": lord, "duration_days": 6000}]


@pytest.mark.parametrize("chart_id", [CANON_UUID, CANON], ids=["uuid", "str"])
def test_verify_vimshottari_native_verdict_is_classical_match_not_two_pass(chart_id):
    verdict = gdw._verify_vimshottari(_vim_l1_rows("Jupiter"), 325.0, chart_id)
    assert verdict == "classical_match" == gdw.CLASSICAL_MATCH
    assert verdict != "two_pass_verified"


@pytest.mark.parametrize("chart_id", [CANON_UUID, CANON], ids=["uuid", "str"])
def test_verify_vimshottari_wrong_native_anchor_still_halts(chart_id):
    with pytest.raises(ValueError, match="FORENSIC HALT"):
        gdw._verify_vimshottari(_vim_l1_rows("Saturn"), 325.0, chart_id)


def test_verify_vimshottari_non_native_chart_is_unverified_default_and_ungated():
    assert gdw._verify_vimshottari(_vim_l1_rows("Saturn"), 100.0, OTHER_UUID) == "single" == gdw.UNVERIFIED_DEFAULT
