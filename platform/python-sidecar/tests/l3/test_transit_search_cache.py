"""
tests/l3/test_transit_search_cache.py — PERF-TRIGGER-CACHE (Doctrine-Waves D-3).

Verifies the `_get_planet_pos` ephemeris memoization added to
`pipeline/transit_search.py`:
  1. Correctness: a cached call returns bit-identical output to an
     uncached swe.calc_ut call for the same (planet, jd).
  2. Boundedness: the cache is an `lru_cache` with a finite maxsize (no
     unbounded dict growth across a long build run).
  3. Speedup: a realistic 30-day / 5-aspect-degree window (the shape that
     produced the production hang in ka_sangam.py predicate 39-40 via
     services/kala_trigger/trigger.py's ~38-scans-per-window fan-out)
     shows a measured cache-hit-driven speedup.

All tests use live swisseph (pyswisseph must be installed in the venv).
No DB access required — all functions are pure computation over JD ranges.
"""
import time

import pytest
import swisseph as swe

from pipeline import transit_search as ts
from pipeline.transit_search import (
    find_aspect_events,
    find_transit_to_transit_events,
    clear_ephemeris_cache,
    ephemeris_cache_info,
    _get_planet_pos,
    _calc_ut_cached,
)


@pytest.fixture(autouse=True)
def _reset_cache():
    """Every test starts from a clean cache so hit/miss counts are legible."""
    clear_ephemeris_cache()
    yield
    clear_ephemeris_cache()


# ── Correctness ────────────────────────────────────────────────────────────

def test_cached_call_matches_direct_swe_calc_ut():
    """
    A cached `_get_planet_pos` result must be numerically IDENTICAL to what
    calling swe.calc_ut directly (bypassing the cache entirely) produces for
    the same (planet, jd) — this is a pure performance optimization, not an
    approximation.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    jd = swe.julday(2020, 3, 15, 12.0)

    # Ground truth: call swe.calc_ut directly, with zero cache involvement.
    planet_id = 6  # Saturn
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    raw_result = swe.calc_ut(jd, planet_id, flags)
    raw_lon = raw_result[0][0] % 360.0
    raw_speed = raw_result[0][3]

    # Cached path (first call = miss, populates cache).
    cached_lon, cached_speed = _get_planet_pos(swe, "Saturn", jd)

    assert cached_lon == raw_lon
    assert cached_speed == raw_speed


def test_cache_hit_returns_identical_result_to_cache_miss():
    """
    Calling `_get_planet_pos` twice for the exact same (planet, jd) must
    return bit-identical results on the second (cache-HIT) call as the first
    (cache-MISS) call — proves the memoization changes nothing about the
    returned value.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    jd = swe.julday(2021, 7, 4, 8.5)

    info_before = ephemeris_cache_info()
    lon1, speed1 = _get_planet_pos(swe, "Mars", jd)
    info_after_first = ephemeris_cache_info()
    lon2, speed2 = _get_planet_pos(swe, "Mars", jd)
    info_after_second = ephemeris_cache_info()

    assert (lon1, speed1) == (lon2, speed2)
    # First call was a genuine miss; second was a genuine hit.
    assert info_after_first.misses == info_before.misses + 1
    assert info_after_second.hits == info_after_first.hits + 1
    assert info_after_second.misses == info_after_first.misses  # no new miss


def test_ketu_derivation_unaffected_by_caching():
    """
    Ketu is derived from a (cached) Rahu lookup — confirm the derived value
    is still exactly rahu_lon + 180 mod 360, with the same speed magnitude,
    whether or not Rahu was already cached.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    jd = swe.julday(2022, 11, 2, 0.0)

    rahu_lon, rahu_speed = _get_planet_pos(swe, "Rahu", jd)
    ketu_lon, ketu_speed = _get_planet_pos(swe, "Ketu", jd)

    assert ketu_lon == pytest.approx((rahu_lon + 180.0) % 360.0, abs=1e-12)
    assert ketu_speed == rahu_speed


def test_find_aspect_events_identical_cached_vs_uncached():
    """
    End-to-end correctness proof: `find_aspect_events` over a realistic
    30-day / 5-aspect-degree window returns the SAME events whether the
    ephemeris cache is warm, cold, or entirely bypassed (raw swe.calc_ut
    on every call, mimicking the pre-cache code path).
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    start_jd = swe.julday(2023, 1, 1)
    end_jd = start_jd + 30
    aspect_degrees = [0, 60, 90, 120, 180]
    target_lon = 142.317

    # Run 1: cold cache (all misses on first touch, hits on aspect_deg reuse).
    clear_ephemeris_cache()
    events_cached = find_aspect_events(
        swe, "Saturn", target_lon, aspect_degrees, 5.0, start_jd, end_jd
    )

    # Run 2: fully bypass the cache — monkeypatch `_calc_ut_cached` to the
    # raw (undecorated) function so every call re-invokes swe.calc_ut,
    # exactly reproducing the pre-cache behavior.
    raw_calc = _calc_ut_cached.__wrapped__
    original = ts._calc_ut_cached
    ts._calc_ut_cached = raw_calc
    try:
        events_uncached = find_aspect_events(
            swe, "Saturn", target_lon, aspect_degrees, 5.0, start_jd, end_jd
        )
    finally:
        ts._calc_ut_cached = original

    assert len(events_cached) == len(events_uncached)
    for ec, eu in zip(events_cached, events_uncached):
        assert ec.event_jd == eu.event_jd
        assert ec.exact_longitude_deg == eu.exact_longitude_deg
        assert ec.orb_at_event_deg == eu.orb_at_event_deg
        assert ec.applying_separating == eu.applying_separating
        assert ec.orb_strength == eu.orb_strength
        assert ec.speed_at_event_dps == eu.speed_at_event_dps
        assert ec.sign == eu.sign
        assert ec.nakshatra == eu.nakshatra


# ── Boundedness ────────────────────────────────────────────────────────────

def test_cache_is_bounded_lru_not_unbounded_dict():
    """
    The ephemeris cache must be a bounded LRU (finite maxsize), not an
    unbounded dict — a very long multi-chart build run must not leak
    memory indefinitely.
    """
    info = ephemeris_cache_info()
    assert info.maxsize is not None
    assert info.maxsize == ts._EPHEMERIS_CACHE_MAXSIZE
    assert info.maxsize > 0


# ── Speedup ────────────────────────────────────────────────────────────────

def test_benchmark_cache_speedup_realistic_window():
    """
    Benchmark: a 30-day window, 5 aspect degrees, Saturn (the slow-planet
    step=1.0day case, same as predicate 39's TRIGGER suppression scans) —
    the shape that produced the production hang. Compares wall-clock time
    of the cached path vs. an ephemeris-cache-bypassed path (raw swe.calc_ut
    on every lookup, exactly the pre-fix behavior), and reports the observed
    cache hit rate. Not a strict pass/fail on wall-clock ratio (CI timing is
    noisy) — asserts the DETERMINISTIC signal (cache hits actually occurred,
    proving the intra-call aspect_degrees redundancy is real) and prints the
    real numbers for the record.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    start_jd = swe.julday(2024, 1, 1)
    end_jd = start_jd + 30
    aspect_degrees = [0, 60, 90, 120, 180]
    target_lon = 88.123
    planet = "Saturn"

    # ── Uncached (cache bypassed entirely, mirrors pre-fix behavior) ──
    raw_calc = _calc_ut_cached.__wrapped__
    original = ts._calc_ut_cached
    ts._calc_ut_cached = raw_calc
    try:
        t0 = time.perf_counter()
        events_uncached = find_aspect_events(
            swe, planet, target_lon, aspect_degrees, 5.0, start_jd, end_jd
        )
        t_uncached = time.perf_counter() - t0
    finally:
        ts._calc_ut_cached = original

    # ── Cached, cold start (single call — captures intra-call reuse
    #    across the 5 aspect_degrees, which all re-walk the identical
    #    start_jd/step jd sequence) ──
    clear_ephemeris_cache()
    t0 = time.perf_counter()
    events_cached_cold = find_aspect_events(
        swe, planet, target_lon, aspect_degrees, 5.0, start_jd, end_jd
    )
    t_cached_cold = time.perf_counter() - t0
    info_cold = ephemeris_cache_info()

    # ── Cached, warm (second call, same window — mirrors the
    #    compute_trigger_currents() fan-out where ~38 calls share one
    #    window) ──
    t0 = time.perf_counter()
    events_cached_warm = find_aspect_events(
        swe, planet, target_lon, aspect_degrees, 5.0, start_jd, end_jd
    )
    t_cached_warm = time.perf_counter() - t0
    info_warm = ephemeris_cache_info()

    # Correctness holds across all three runs.
    assert len(events_uncached) == len(events_cached_cold) == len(events_cached_warm)

    print(
        "\n[PERF-TRIGGER-CACHE benchmark] 30-day window, 5 aspect degrees, "
        f"planet={planet}\n"
        f"  uncached (cache bypassed):       {t_uncached*1000:.2f} ms\n"
        f"  cached, cold (1st call):         {t_cached_cold*1000:.2f} ms "
        f"(hits={info_cold.hits}, misses={info_cold.misses})\n"
        f"  cached, warm (2nd call, "
        f"same window):  {t_cached_warm*1000:.2f} ms "
        f"(hits={info_warm.hits}, misses={info_warm.misses})\n"
        f"  cold-cache speedup vs uncached:  {t_uncached / max(t_cached_cold, 1e-9):.2f}x\n"
        f"  warm-cache speedup vs uncached:  {t_uncached / max(t_cached_warm, 1e-9):.2f}x\n"
    )

    # Deterministic assertions (not timing-flake-prone):
    # (a) the cold-cache single call already produced real hits — the
    #     5-aspect-degree fan-out shares the same jd sequence per planet.
    assert info_cold.hits > 0
    # (b) the warm call (same window, second invocation) is served almost
    #     entirely from cache — zero NEW misses.
    assert info_warm.misses == info_cold.misses


def test_benchmark_shared_window_across_multiple_calls():
    """
    Benchmark approximating `compute_trigger_currents`' actual pattern:
    multiple independent find_aspect_events / find_transit_to_transit_events
    calls for DIFFERENT planets sharing the SAME window
    (w_jd_start, w_jd_end) — the exact shape of the 38-scans-per-window
    TRIGGER fan-out. Demonstrates cross-call cache reuse when a planet
    (e.g. Saturn, used in both malefic and guru_shani checks) recurs across
    calls against the same window.
    """
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    start_jd = swe.julday(2025, 6, 1)
    end_jd = start_jd + 30
    aspect_degrees = [0, 60, 90, 120, 180]

    clear_ephemeris_cache()

    t0 = time.perf_counter()
    # Mirrors _malefic_transit_over_mechanism's loop over the 4 malefics,
    # each checked against the mechanism longitude, all sharing the window.
    for target_lon in (10.0, 130.0, 250.0):  # 3 distinct target points, e.g.
        # mechanism_lon, before_lon, after_lon in _papa_kartari_sandwich shape
        for planet in ("Saturn", "Mars", "Rahu", "Ketu"):
            find_aspect_events(
                swe, planet, target_lon, aspect_degrees, 5.0, start_jd, end_jd
            )
    # guru_shani_double_transit: Jupiter + Saturn against one more target.
    for planet in ("Jupiter", "Saturn"):
        find_aspect_events(
            swe, planet, 200.0, aspect_degrees, 5.0, start_jd, end_jd
        )
    t_total = time.perf_counter() - t0
    info = ephemeris_cache_info()

    print(
        "\n[PERF-TRIGGER-CACHE benchmark] shared-window multi-call fan-out "
        f"(mirrors compute_trigger_currents' pattern):\n"
        f"  total wall time:  {t_total*1000:.2f} ms\n"
        f"  cache hits:       {info.hits}\n"
        f"  cache misses:     {info.misses}\n"
        f"  hit rate:         {info.hits / max(info.hits + info.misses, 1):.1%}\n"
    )

    # Saturn recurs across 2 of the call groups sharing the same window --
    # its second appearance (guru_shani check) should be served largely
    # from cache, so the aggregate hit rate must be well above zero.
    assert info.hits > 0
