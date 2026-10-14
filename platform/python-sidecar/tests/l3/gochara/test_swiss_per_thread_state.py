"""C26 — Swiss Ephemeris per-thread state: cross-context equality proof.

On Linux the Swiss sidereal mode and ephemeris path are PER-THREAD C state
(macOS: process-global). A fresh thread that never called ``set_sid_mode``
computes in the default ayanamsha (Fagan/Bradley, ~0.88° off Lahiri). This
file pins the Sun's sidereal Lahiri longitude at one JD (J2000) against the
SHA-pinned .se1 corpus and requires the SAME value from the main thread, a
fresh ``threading.Thread``, a ``ThreadPoolExecutor`` worker and a
``ProcessPoolExecutor`` worker — through BOTH production seams
(``gochara_kernel.knots.calc_sidereal_lon`` and
``pipeline.transit_search._get_planet_pos``). A Linux-only mutation arm then
proves the hazard is real on the platform it guards: a raw
``calc_ut(FLG_SIDEREAL)`` in a fresh thread WITHOUT the C26 helper misses the
pinned value by ~0.88°, while the same call WITH ``prepare_swiss_thread`` in
that thread hits it.

Runs under the tests/l3/gochara conftest gate: the pinned .se1 corpus comes
from SE_EPHE_PATH, checksums verified at collection; GOCHARA_SE1_REQUIRE=1
(CI's sidecar leg, which selects all of tests/) turns an unusable corpus into
a hard failure instead of a skip.
"""
from __future__ import annotations

import os
import sys
import threading
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor

import pytest

from .conftest import EPHE_PATH, J2000_JD, assert_real_ephemeris, requires_swieph

# Measured once against the SHA-pinned corpus (sepl_18.se1
# ca1393ce…, checksums in ./conftest.py): swe.julday(2000,1,1,12.0) =
# 2451545.0, swe.calc_ut(SUN, FLG_SIDEREAL|FLG_SPEED|FLG_SWIEPH) with
# SIDM_LAHIRI. 1e-9° tolerance per the C26 brief.
PINNED_SUN_LAHIRI_LON_J2000 = 256.5156961838706
TOL_DEG = 1e-9
# Fagan/Bradley (the Swiss default ayanamsha) at the same instant — measured
# 255.63248854314455°, i.e. the hazard magnitude is ~0.883°.
EXPECTED_HAZARD_DELTA_DEG = 0.8832076407260558
# Same pinned corpus: MEAN_NODE (Rahu) Lahiri longitude 101.18742357058697°
# at J2000 → 0-based sign index 3; Lahiri ayanamsa at J2000.
PINNED_RAHU_SIGN_INDEX_J2000 = 3
PINNED_LAHIRI_AYANAMSA_J2000 = 23.85709235370888


def _sun_via_kernel(jd: float) -> float:
    from services.gochara_kernel.knots import calc_sidereal_lon

    lon, retflag = calc_sidereal_lon("Sun", jd, EPHE_PATH)
    assert retflag & 2, f"kernel did not use the Swiss backend (retflag {retflag})"
    return lon


def _sun_via_transit_search(jd: float) -> float:
    from pipeline import transit_search

    transit_search.clear_ephemeris_cache()
    import swisseph as swe

    lon, _speed = transit_search._get_planet_pos(swe, "Sun", jd)
    return lon


def _assert_matches_pinned(lon: float, where: str) -> None:
    assert abs(lon - PINNED_SUN_LAHIRI_LON_J2000) <= TOL_DEG, (
        f"{where}: Sun sidereal Lahiri longitude {lon!r} at JD {J2000_JD} differs "
        f"from the pinned {PINNED_SUN_LAHIRI_LON_J2000} by "
        f"{abs(lon - PINNED_SUN_LAHIRI_LON_J2000):.3e}° (tol {TOL_DEG})"
    )


@requires_swieph
def test_sun_lahiri_longitude_identical_across_thread_contexts(monkeypatch):
    """Every computing context must produce the pinned value through both seams."""
    assert_real_ephemeris()
    # transit_search._resolved_ephemeris_path honours SWE_EPHE_PATH; export it
    # so ProcessPoolExecutor children (spawn re-imports the module and reads the
    # inherited environment) resolve the same pinned corpus.
    monkeypatch.setenv("SWE_EPHE_PATH", EPHE_PATH)

    # 1. Main thread, both seams.
    _assert_matches_pinned(_sun_via_kernel(J2000_JD), "main thread / calc_sidereal_lon")
    _assert_matches_pinned(
        _sun_via_transit_search(J2000_JD), "main thread / _get_planet_pos"
    )

    # 2. A fresh threading.Thread (the orchestrator-pool shape, runner.py:682).
    results: dict[str, float] = {}

    def _thread_worker():
        results["kernel"] = _sun_via_kernel(J2000_JD)
        results["ts"] = _sun_via_transit_search(J2000_JD)

    t = threading.Thread(target=_thread_worker)
    t.start()
    t.join(timeout=60)
    assert not t.is_alive()
    _assert_matches_pinned(results["kernel"], "threading.Thread / calc_sidereal_lon")
    _assert_matches_pinned(results["ts"], "threading.Thread / _get_planet_pos")

    # 3. ThreadPoolExecutor worker.
    with ThreadPoolExecutor(max_workers=1) as pool:
        _assert_matches_pinned(
            pool.submit(_sun_via_kernel, J2000_JD).result(timeout=60),
            "ThreadPoolExecutor / calc_sidereal_lon",
        )
        _assert_matches_pinned(
            pool.submit(_sun_via_transit_search, J2000_JD).result(timeout=60),
            "ThreadPoolExecutor / _get_planet_pos",
        )

    # 4. ProcessPoolExecutor worker (fresh process: no inherited mode, path or
    # lru_cache — both seams must establish their own state).
    with ProcessPoolExecutor(max_workers=1) as pool:
        _assert_matches_pinned(
            pool.submit(_sun_via_kernel, J2000_JD).result(timeout=120),
            "ProcessPoolExecutor / calc_sidereal_lon",
        )
        _assert_matches_pinned(
            pool.submit(_sun_via_transit_search, J2000_JD).result(timeout=120),
            "ProcessPoolExecutor / _get_planet_pos",
        )


def _raw_sidereal_sun_unprepared(jd: float, ephe_path: str) -> float:
    """Raw calc_ut(FLG_SIDEREAL) with ONLY the path set — no sid-mode call.

    Simulates the pre-C26 fragile pattern in a fresh thread: on Linux the
    sidereal mode of this thread is the Swiss default (Fagan/Bradley)."""
    import swisseph as swe

    swe.set_ephe_path(ephe_path)
    out, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)
    return float(out[0])


def _prepared_sidereal_sun(jd: float, ephe_path: str) -> float:
    """The same raw calc, but the thread prepares its own state first (C26)."""
    import swisseph as swe

    from panchang_engine.swiss_thread_scope import prepare_swiss_thread

    prepare_swiss_thread(ephe_path, swe.SIDM_LAHIRI)
    out, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)
    return float(out[0])


@requires_swieph
@pytest.mark.skipif(
    sys.platform != "linux",
    reason="Swiss sidereal mode is per-thread on Linux only (macOS is "
    "process-global); the hazard this arm proves cannot occur here",
)
def test_linux_fresh_thread_without_prepare_misses_by_default_ayanamsha():
    """Mutation arm: prove the per-thread hazard exists on the guarded platform."""
    assert_real_ephemeris()

    with ThreadPoolExecutor(max_workers=1) as pool:
        unprepared = pool.submit(
            _raw_sidereal_sun_unprepared, J2000_JD, EPHE_PATH
        ).result(timeout=60)
    delta = abs(unprepared - PINNED_SUN_LAHIRI_LON_J2000)
    assert delta > 0.5, (
        f"expected the unprepared fresh thread to miss the pinned Lahiri value "
        f"by ~{EXPECTED_HAZARD_DELTA_DEG}° (default Fagan/Bradley ayanamsha); "
        f"got delta {delta}° — the per-thread hazard did NOT manifest, so this "
        "guard's premise must be re-examined"
    )
    assert abs(delta - EXPECTED_HAZARD_DELTA_DEG) < 0.01, (
        f"hazard delta {delta}° is not the expected ~{EXPECTED_HAZARD_DELTA_DEG}° "
        "(Fagan/Bradley vs Lahiri at J2000) — a different defect is at play"
    )

    # Same fresh-thread shape WITH the C26 helper: pinned value restored.
    with ThreadPoolExecutor(max_workers=1) as pool:
        prepared = pool.submit(_prepared_sidereal_sun, J2000_JD, EPHE_PATH).result(
            timeout=60
        )
    _assert_matches_pinned(prepared, "fresh thread with prepare_swiss_thread")


def _w30_rahu_sign(jd: float) -> int:
    """The fixed gochara_v3 W3.0 site, real swe, minimal context (no targets:
    contributions empty, modifier 1.0 — we assert the computed Rahu sign)."""
    from types import SimpleNamespace

    import swisseph as swe

    from services.gochara_v3.mechanisms import w30_nodal_drishti as w30

    ctx = SimpleNamespace(
        chart_id="c26-thread-probe",
        natal_facts=SimpleNamespace(),
        resonance_targets=(),
    )
    result = w30.compute(ctx, jd, swe=swe, enabled=True)
    assert not result.skipped, f"w30 skipped: {result.skip_reason}"
    assert result.rahu_sign is not None
    return result.rahu_sign


def _engine_site_runs(jd: float) -> None:
    """The fixed gochara_v3 engine site: _evaluate_single_from_context with a
    minimal pre-fetched context (empty rows — PROMISE/PERMISSION neutral; the
    :768 Moon tara-bala calc_ut runs unconditionally inside it)."""
    from types import SimpleNamespace

    import swisseph as swe

    from services.gochara_v3 import engine

    ctx = SimpleNamespace(
        chart_id="c26-thread-probe",
        event_class="career",
        resonance_targets=(),
        promise=0.0,
        promise_detail={},
        dasha_periods=(),
        relevant_grahas=frozenset(),
        relevant_signs=frozenset(),
        temporal_shape="point",
        valence="neutral",
        is_adverse=False,
        beta_e=0.45,
        weight_by_target_ref={},
        natal_facts=None,
        av_gate_rows=(),
        sade_sati_phases=(),
        vedha_rows=(),
        malefic_scale=(),
        kakshya_boundaries=(),
        bindu_contributor_rows=(),
        bindu_sign_rows=(),
    )
    engine._evaluate_single_from_context(swe, ctx, jd, [])


@requires_swieph
def test_reused_thread_contaminated_with_other_mode_still_yields_lahiri(monkeypatch):
    """Suvarṇa audit (1): orchestrator pool threads are REUSED (max 4), so a
    missing setter yields the LAST ayanamsha left on that thread, not only the
    library default. One worker thread is contaminated with Fagan/Bradley;
    every production path must then still produce the pinned LAHIRI reference,
    and must leave the thread's own mode at Lahiri."""
    assert_real_ephemeris()
    monkeypatch.setenv("SWE_EPHE_PATH", EPHE_PATH)
    import swisseph as swe

    # Lahiri ayanamsa reference for this corpus, measured on the main thread.
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayan_lahiri = swe.get_ayanamsa_ut(J2000_JD)
    assert abs(ayan_lahiri - PINNED_LAHIRI_AYANAMSA_J2000) <= TOL_DEG

    box: dict = {}

    def _worker():
        # Contaminate THIS thread: path set, but a WRONG sidereal mode left
        # behind — the reused-pool-thread shape.
        swe.set_ephe_path(EPHE_PATH)
        swe.set_sid_mode(swe.SIDM_FAGAN_BRADLEY)
        box["contaminated_sun"] = float(
            swe.calc_ut(J2000_JD, swe.SUN, swe.FLG_SIDEREAL)[0][0]
        )
        # Every production path, on this contaminated thread:
        box["kernel"] = _sun_via_kernel(J2000_JD)
        box["ts"] = _sun_via_transit_search(J2000_JD)
        box["w30_rahu_sign"] = _w30_rahu_sign(J2000_JD)
        _engine_site_runs(J2000_JD)
        box["ayan_after"] = swe.get_ayanamsa_ut(J2000_JD)

    t = threading.Thread(target=_worker)
    t.start()
    t.join(timeout=120)
    assert not t.is_alive()

    # The contamination was real (else this arm proves nothing).
    assert (
        abs(box["contaminated_sun"] - PINNED_SUN_LAHIRI_LON_J2000) > 0.5
    ), "Fagan/Bradley contamination did not take effect on the worker thread"

    _assert_matches_pinned(box["kernel"], "contaminated thread / calc_sidereal_lon")
    _assert_matches_pinned(box["ts"], "contaminated thread / _get_planet_pos")
    assert box["w30_rahu_sign"] == PINNED_RAHU_SIGN_INDEX_J2000, (
        f"contaminated thread / w30_nodal_drishti.compute: rahu_sign "
        f"{box['w30_rahu_sign']} != pinned {PINNED_RAHU_SIGN_INDEX_J2000}"
    )
    # Both fixed gochara_v3 sites prepare their own thread: after the engine
    # call the thread's mode is Lahiri, not the contaminated Fagan/Bradley.
    assert abs(box["ayan_after"] - ayan_lahiri) <= TOL_DEG, (
        f"after the fixed gochara_v3 sites ran, the worker thread's ayanamsha "
        f"is {box['ayan_after']!r}, not the Lahiri {ayan_lahiri!r} — a site "
        "left the contaminated mode in place"
    )
