"""GRAZE-INTERIM (steward, 2026-10-05): under a VALIDATED test-slice marker the in-build contact-geometry certification REPORTS in-band intervals that
contain no exact crossing (grazes) instead of raising; every other certification failure still raises; without a marker nothing changes.

THE FINDING: on the native's chart, Jupiter's retrograde loop of 2003-12 to 2004-01 stays inside the 1 degree band of the aspect ray 145.39 (natal point
265.39 minus 120 degrees) for 39 days and never reaches it (peak at 144.994, closest approach 0.396 degrees). The builder mints a point contact only around an
EXACT ROOT of the ray level (`solve_point_edges` -> `find_roots`), so no contact exists; `contact_certify` reconstructs every in-band interval and refuses:
'expected contact [2003-12-15, 2004-01-23) is not in the ledger'. A full build, and run 2 of the small test (marriage, full horizon), fail at `verify:marriage`.
The choice between minting graze contacts, ignoring them or requiring an exact crossing is the OWNER's (decisions/G11_GRAZE_CONTACT_OPTIONS_v1_0.md); this interim only
lets an unsealed, never-served test slice complete and MEASURE how many grazes exist. Tests: synthetic exact curves, the real sky, and the writer's own switch."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from services.gochara_kernel import contact_certify as cc

from .test_a55_replace_chain import template  # noqa: F401
from .test_member_geometry_seam import DAY, RAY, T0, curve, curve_graze

UTC = timezone.utc
LO, HI = T0 - 40 * DAY, T0 + 40 * DAY
TARGET = f"point:{RAY}"
ACC = 0.00027777778


def _want(fn, **kw):
    return cc.expected_intervals(fn, "venus", "conjunction", TARGET, kw.get("lo", LO), kw.get("hi", HI))


# ── the classifier ──────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_a_graze_is_classified_with_its_closest_approach_and_peak_activity():
    (iv,) = _want(curve_graze)
    g = cc.classify_graze(curve_graze, "venus", "conjunction", TARGET, iv, LO, HI)
    assert g and abs(g["closest_approach_deg"] - 0.3) < 0.01 and abs(g["peak_activity"] - 0.7) < 0.01
    assert g["body"] == "venus" and g["relation"] == "conjunction" and g["target"] == TARGET and g["level_deg"] == RAY
    assert abs((datetime.fromisoformat(g["closest_approach_at"]) - T0).total_seconds()) < 7200        # at the station, the closest approach


def test_an_interval_in_which_the_ray_level_is_reached_is_never_a_graze():
    (iv,) = _want(curve)
    assert cc.classify_graze(curve, "venus", "conjunction", TARGET, iv, LO, HI) is None


def test_the_sign_test_alone_rejects_a_crossing_even_with_the_approach_guard_switched_off(monkeypatch):
    """The sign change is what tells a crossing from a graze; the 18 arcsecond guard is a second, independent safety. Switch the guard off: the crossing is still refused."""
    monkeypatch.setattr(cc, "GRAZE_MIN_APPROACH_DEG", 0.0)
    (iv,) = _want(curve)
    assert cc.classify_graze(curve, "venus", "conjunction", TARGET, iv, LO, HI) is None
    (iv_g,) = _want(curve_graze)
    assert cc.classify_graze(curve_graze, "venus", "conjunction", TARGET, iv_g, LO, HI) is not None      # and the graze is still classified


def test_a_near_miss_the_builder_should_have_minted_is_not_a_graze():
    def near(body, t):                                              # the minimum is only 0.003 degrees from the level: within the 18 arcsecond guard
        d = (t - T0).total_seconds() / 86400.0
        return RAY + 0.003 + 0.02 * d * d
    (iv,) = _want(near)
    assert cc.classify_graze(near, "venus", "conjunction", TARGET, iv, LO, HI) is None


def test_a_horizon_clipped_interval_whose_crossing_lies_outside_the_horizon_is_not_a_graze():
    """The interim refused every clipped interval; VERIFIER-CODEX-3 item 2 replaced that with the whole-stretch decision (see the codex3 tests below). What must NOT change: a
    clipped piece with no crossing inside it whose WHOLE stretch does cross the ray (the builder mints a clipped contact) is not a graze."""
    clip_lo = T0 + 6 * DAY
    (iv,) = _want(curve, lo=clip_lo)
    assert iv[0] == clip_lo and cc.classify_graze(curve, "venus", "conjunction", TARGET, iv, clip_lo, HI) is None


def test_a_span_target_is_never_a_graze():
    assert cc.classify_graze(curve_graze, "venus", "residence", "span:5", (T0 - DAY, T0 + DAY), LO, HI) is None


# ── certification: reported under a sink, raised without one, every other failure still raised ─────────────────────────────

def test_with_a_sink_a_graze_is_reported_and_does_not_raise():
    want = _want(curve_graze)
    sink: list = []
    assert cc.compare_contact_sets(curve_graze, "venus", "conjunction", TARGET, want, [], LO, HI, graze_sink=sink) == []
    assert len(sink) == 1 and sink[0]["interval"][0] == want[0][0].isoformat()


def test_without_a_sink_a_graze_still_raises_exactly_as_before():
    problems = cc.compare_contact_sets(curve_graze, "venus", "conjunction", TARGET, _want(curve_graze), [], LO, HI)
    assert problems and "is not in the ledger" in problems[0]


def test_a_non_graze_omission_still_raises_under_a_sink():
    sink: list = []
    problems = cc.compare_contact_sets(curve, "venus", "conjunction", TARGET, _want(curve), [], LO, HI, graze_sink=sink)
    assert problems and "is not in the ledger" in problems[0] and sink == []


def test_a_graze_overlapped_by_a_ledger_contact_is_not_reclassified_and_still_raises():
    (iv,) = _want(curve_graze)
    have = [(iv[0], iv[0] + (iv[1] - iv[0]) / 2, ACC)]              # a ledger contact covers half of the in-band interval: a different omission
    sink: list = []
    problems = cc.compare_contact_sets(curve_graze, "venus", "conjunction", TARGET, [iv], have, LO, HI, graze_sink=sink)
    assert problems and sink == []


def test_a_truncated_crossing_contact_still_raises_under_a_sink():
    (iv,) = _want(curve)
    have = [(iv[0], iv[1] - 3 * DAY, ACC)]
    sink: list = []
    assert cc.compare_contact_sets(curve, "venus", "conjunction", TARGET, [iv], have, LO, HI, graze_sink=sink) and sink == []


# ── the real sky: the native's Jupiter graze of 2003-12 to 2004-01 ─────────────────────────────────────────────────────────

def test_the_real_jupiter_graze_is_found_on_the_real_ephemeris_and_reported_with_its_numbers():
    import swisseph as swe
    from services.gochara_kernel.knots import calc_sidereal_lon
    from .conftest import EPHE_PATH, assert_real_ephemeris
    assert_real_ephemeris()
    jd0 = 2440587.5

    def real(body, t):
        lon, flag = calc_sidereal_lon(body.title(), t.timestamp() / 86400.0 + jd0, EPHE_PATH)
        assert flag & 2
        return lon
    lo, hi = datetime(2003, 10, 1, tzinfo=UTC), datetime(2004, 3, 1, tzinfo=UTC)
    target = "point:265.39"
    want = cc.expected_intervals(real, "jupiter", "aspect", target, lo, hi)
    sink: list = []
    problems = cc.compare_contact_sets(real, "jupiter", "aspect", target, want, [], lo, hi, graze_sink=sink)
    assert problems == [] and len(sink) == 1, (problems, sink)
    g = sink[0]
    assert abs(g["level_deg"] - 145.39) < 1e-6 and abs(g["closest_approach_deg"] - 0.396) < 0.01 and abs(g["peak_activity"] - 0.604) < 0.01
    start, end = (datetime.fromisoformat(x) for x in g["interval"])
    assert start.date().isoformat() == "2003-12-15" and end.date().isoformat() == "2004-01-23"                 # 39 days
    assert cc.compare_contact_sets(real, "jupiter", "aspect", target, want, [], lo, hi)                          # and WITHOUT a sink it still raises


# ── the writer's switch: a sink ONLY under a validated test-slice marker ───────────────────────────────────────────────────

def _spy(monkeypatch, fake_graze=None):
    from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
    seen = {}
    real = writer_mod.gk_contact_certify.certify_contact_geometry

    def spy(conn, **kw):
        seen["sink"] = kw.get("graze_sink", "absent")
        out = real(conn, **kw)
        if fake_graze is not None and kw.get("graze_sink") is not None:
            kw["graze_sink"].append(fake_graze)
            out = {**out, "grazes": list(kw["graze_sink"])}
        return out
    monkeypatch.setattr(writer_mod.gk_contact_certify, "certify_contact_geometry", spy)
    return seen


FAKE = {"body": "jupiter", "relation": "aspect", "target": "point:265.39", "level_deg": 145.39, "interval": ["2003-12-15T00:00:00+00:00", "2004-01-23T00:00:00+00:00"],
        "closest_approach_deg": 0.396, "closest_approach_at": "2004-01-03T00:00:00+00:00", "peak_activity": 0.604}


def test_the_writer_hands_the_certifier_a_sink_only_under_a_validated_test_slice_marker(template, monkeypatch):
    from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
    from .test_a55_replace_chain import FULLL, _World
    from .test_c46_slice_transitions import _SliceWorld
    from .test_p1_exclusion_h_unknown import _class_chain
    seen = _spy(monkeypatch, fake_graze=FAKE)
    full = _World(template)
    try:
        full.step(writer_mod.MANIFEST_SUBSTEP, FULLL)
        full.step(writer_mod.SNAPSHOT_SUBSTEP, FULLL)
        _class_chain(full, "marriage")                               # no marker: the sink is None and the notes carry no graze text
        assert seen["sink"] is None
    finally:
        full.close()
    sliced = _SliceWorld(template)
    try:
        rid = sliced.run_id(sliced.marker_for(FULLL))
        sliced.step_as(writer_mod.MANIFEST_SUBSTEP, rid)
        sliced.step_as(writer_mod.SNAPSHOT_SUBSTEP, rid)
        sliced.step_as("inventory:marriage", rid)
        sliced.step_as("coverage:marriage", rid)
        for p in writer_mod.RECORD_PATHS:
            sliced.step_as(f"record:marriage:{p}", rid)
        for p in writer_mod.WINDOW_PATHS:
            sliced.step_as(f"window:marriage:{p}", rid)
        result = sliced.step_as("verify:marriage", rid)
        assert isinstance(seen["sink"], list)                        # a sink under the validated marker
        assert "GRAZES REPORTED, NOT RAISED (validated test slice; 1)" in result.notes and "jupiter aspect point:265.39" in result.notes
        assert "closest 0.396 deg" in result.notes and "peak activity 0.604" in result.notes
    finally:
        sliced.close()


# ── VERIFIER-R2-GO: the verify outcome reaches the run log (the runner never reads notes) ────────────────────────────────────

def test_the_verify_log_helper_is_info_normally_and_warning_on_unverified_and_returns_the_result_unchanged(caplog):
    import logging
    from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
    WriterResult = writer_mod.WriterResult
    ok = WriterResult(asset_id=writer_mod.ASSET_ID, rows_inserted=1, notes="verify marriage: inventory + ledger digests independently reproduced")
    bad = WriterResult(asset_id=writer_mod.ASSET_ID, rows_inserted=0, notes="verify business_launch: UNVERIFIED — no derivation (no verification row)")
    with caplog.at_level(logging.INFO, logger=writer_mod.logger.name):
        assert writer_mod._log_verify_outcome("verify:marriage", ok) is ok
        assert writer_mod._log_verify_outcome("verify:business_launch", bad) is bad
    by_level = {r.levelno: r.getMessage() for r in caplog.records}
    assert logging.INFO in by_level and "verify:marriage" in by_level[logging.INFO]
    assert logging.WARNING in by_level and "UNVERIFIED" in by_level[logging.WARNING] and "verify:business_launch" in by_level[logging.WARNING]


def test_an_unverifiable_class_is_logged_at_warning_from_the_real_verify_substep_and_the_run_still_completes(template, monkeypatch, caplog):
    """The writer does not RAISE for a class the verifier cannot derive (that is a designed limit: the class cannot seal; raising would fail the
    whole replayed build over one class): it completes with an UNVERIFIED note, and now ALSO logs it at WARNING so the steward can see it."""
    import logging
    from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
    from services.gochara_kernel import inventory_verifier as inv_v
    from .test_a55_replace_chain import FULLL
    from .test_c46_slice_transitions import _SliceWorld

    def refuse(*a, **k):
        raise inv_v.Unverifiable("synthetic: no independent derivation of this path")
    monkeypatch.setattr(writer_mod.gk_verifier, "rederive_inventory_digest", refuse)
    sliced = _SliceWorld(template)
    try:
        rid = sliced.run_id(sliced.marker_for(FULLL))
        sliced.step_as(writer_mod.MANIFEST_SUBSTEP, rid)
        sliced.step_as(writer_mod.SNAPSHOT_SUBSTEP, rid)
        sliced.step_as("inventory:marriage", rid)
        with caplog.at_level(logging.INFO, logger=writer_mod.logger.name):
            result = sliced.step_as("verify:marriage", rid)
        assert "UNVERIFIED" in result.notes and result.rows_inserted == 0
        warned = [r for r in caplog.records if r.levelno == logging.WARNING and "verify:marriage" in r.getMessage()]
        assert warned and "UNVERIFIED" in warned[0].getMessage()
    finally:
        sliced.close()


# ── VERIFIER-CODEX-2 item 1: "no exact crossing" is PROVED against the speed bound, never inferred from hourly samples ─────────────────────────

def _dip(m: float, a: float = 0.0125, v: float = 1.0):
    """A smooth curve within the Venus speed bound (slope <= v degrees/day, bound 1.6) whose minimum is m degrees from the ray: m < 0 crosses the ray twice, about 16 minutes
    either side of T0 for m = -0.002 (a hyperbola: lambda = RAY + m + sqrt(a^2 + (v s)^2) - a)."""
    def f(body, t):
        s = (t - T0).total_seconds() / 86400.0
        return (RAY + m + ((a * a + (v * s) ** 2) ** 0.5 - a)) % 360.0
    return f


def test_codex2_item1_a_double_crossing_inside_one_sampling_interval_is_not_a_graze():
    """Codex's counterexample: hourly samples all sit 0.009+ degrees above the ray (a sample-only classifier calls it a graze and drops both contacts) while the
    curve crosses the ray twice between two samples. With the proof the pair |d0| + |d1| does not clear the movement bound, the step is bisected, the crossing found."""
    f = _dip(-0.002)
    (iv,) = cc.expected_intervals(f, "venus", "conjunction", TARGET, LO, HI)
    a, b = iv
    n = max(3, int((b - a).total_seconds() // 3600.0) + 2)
    d = [f("venus", a + (b - a) * k / (n - 1)) - RAY for k in range(n)]
    assert min(d) > cc.GRAZE_MIN_APPROACH_DEG and max(d) > 0, "setup: every hourly sample is clear of the ray, so a sample-only test sees a graze"
    assert min(f("venus", T0 + timedelta(minutes=m)) - RAY for m in range(-30, 31)) < 0, "setup: the ray IS crossed between two samples"
    assert cc.classify_graze(f, "venus", "conjunction", TARGET, iv, LO, HI) is None
    sink: list = []
    problems = cc.compare_contact_sets(f, "venus", "conjunction", TARGET, [iv], [], LO, HI, graze_sink=sink)
    assert problems and "is not in the ledger" in problems[0] and sink == []                        # under a slice marker too: the omission raises


def test_codex2_item1_a_true_graze_that_needs_refinement_is_still_classified():
    """Clearance 0.02 degrees: the hourly pair |d0| + |d1| = 0.04 does NOT clear Venus's 0.0667 degrees/hour, so the proof bisects (225 s steps, bound 0.0042) and succeeds."""
    def graze(body, t):
        s = (t - T0).total_seconds() / 86400.0
        return (RAY + 0.02 + 0.02 * s * s) % 360.0
    (iv,) = cc.expected_intervals(graze, "venus", "conjunction", TARGET, LO, HI)
    calls = {"n": 0}

    def counting(body, t):
        calls["n"] += 1
        return graze(body, t)
    g = cc.classify_graze(counting, "venus", "conjunction", TARGET, iv, LO, HI)
    assert g and abs(g["closest_approach_deg"] - 0.02) < 0.001
    n_hourly = max(3, int((iv[1] - iv[0]).total_seconds() // 3600.0) + 2)
    assert calls["n"] > n_hourly, "the proof refined the sampling beyond the hourly grid"


def test_codex2_item1_the_proof_helper_clears_only_with_the_movement_bound_and_fails_at_the_floor():
    f = _dip(0.02)
    t0, t1 = T0 - timedelta(minutes=30), T0 + timedelta(minutes=30)
    d = lambda t: ((f("venus", t) - RAY + 180.0) % 360.0) - 180.0
    assert cc._no_crossing_proved(f, "venus", RAY, t0, d(t0), t1, d(t1))
    crossing = _dip(-0.002)                                                       # same endpoints, a double crossing between them: bisected, found, False
    assert not cc._no_crossing_proved(crossing, "venus", RAY, t0, ((crossing("venus", t0) - RAY + 180) % 360) - 180, t1, ((crossing("venus", t1) - RAY + 180) % 360) - 180)
    # a clearance that cannot beat even the floor step's movement bound is unprovable: False, never True by default
    tiny = _dip(1e-9, a=1e-9)
    assert not cc._no_crossing_proved(tiny, "venus", RAY, t0, ((tiny("venus", t0) - RAY + 180) % 360) - 180, t1, ((tiny("venus", t1) - RAY + 180) % 360) - 180)


# ── VERIFIER-CODEX-3 item 2: a graze CLIPPED by the horizon is decided from the WHOLE stretch, followed beyond the edge ──────────────────────

from datetime import timedelta as _td                                     # noqa: E402

def _clipped(f, h_lo, h_hi):
    (iv,) = cc.expected_intervals(f, "venus", "conjunction", TARGET, h_lo, h_hi)
    return iv


def test_codex3_item2_a_graze_clipped_at_the_horizon_start_is_classified_from_the_whole_stretch():
    h_lo, h_hi = T0 - 3 * DAY, T0 + 60 * DAY
    iv = _clipped(curve_graze, h_lo, h_hi)
    assert iv[0] == h_lo                                                    # clipped: the in-band stretch began before the horizon
    g = cc.classify_graze(curve_graze, "venus", "conjunction", TARGET, iv, h_lo, h_hi)
    assert g and g["clipped_by_horizon"] == ["start"] and abs(g["closest_approach_deg"] - 0.3) < 0.01
    assert datetime.fromisoformat(g["interval"][0]) < h_lo - 2 * DAY      # the reported interval is the WHOLE stretch, the horizon part is separate
    assert datetime.fromisoformat(g["horizon_interval"][0]) == h_lo


def test_codex3_item2_a_graze_clipped_at_the_horizon_end_is_classified_too():
    h_lo, h_hi = T0 - 60 * DAY, T0 + 3 * DAY
    iv = _clipped(curve_graze, h_lo, h_hi)
    g = cc.classify_graze(curve_graze, "venus", "conjunction", TARGET, iv, h_lo, h_hi)
    assert g and g["clipped_by_horizon"] == ["end"]


def test_codex3_item2_a_clipped_stretch_whose_crossing_lies_OUTSIDE_the_horizon_is_not_a_graze():
    """`curve` crosses the ray at -5 d and +5 d. A horizon starting at +6 d sees an in-band piece with no crossing in it, but the builder mints a clipped contact
    for the whole stretch: its absence is a real omission, so the classifier must say NOT a graze (the omission raises)."""
    h_lo, h_hi = T0 + 6 * DAY, T0 + 60 * DAY
    iv = _clipped(curve, h_lo, h_hi)
    assert iv[0] == h_lo
    assert cc.classify_graze(curve, "venus", "conjunction", TARGET, iv, h_lo, h_hi) is None
    sink: list = []
    problems = cc.compare_contact_sets(curve, "venus", "conjunction", TARGET, [iv], [], h_lo, h_hi, graze_sink=sink)
    assert problems and "is not in the ledger" in problems[0] and sink == []


def test_codex3_item2_a_long_stretch_is_followed_until_its_ends_are_interior_to_the_window():
    """A stretch about 118 days each side of its minimum: the first 60-day extension window still touches the stretch's end, so the window doubles."""
    def slow(body, t):
        d = (t - T0).total_seconds() / 86400.0
        return (RAY + 0.3 + 0.00005 * d * d) % 360.0
    h_lo, h_hi = T0 - 10 * DAY, T0 + 400 * DAY
    iv = _clipped(slow, h_lo, h_hi)
    assert iv[0] == h_lo
    g = cc.classify_graze(slow, "venus", "conjunction", TARGET, iv, h_lo, h_hi)
    assert g and g["clipped_by_horizon"] == ["start"]
    assert abs((datetime.fromisoformat(g["interval"][0]) - T0).total_seconds() / 86400.0 + 118.3) < 0.5


def test_codex3_item2_a_crossing_before_the_builders_arc_domain_is_still_an_omission_not_a_graze():
    """The ephemeris reaches before the builder's domain: a stretch cut at the horizon start whose crossing lies outside the horizon is judged from the whole stretch
    (crossing found => not a graze), exactly as for any other horizon edge."""
    h_lo, h_hi = T0 + 6 * DAY, T0 + 60 * DAY                                 # `curve` crosses at +-5 d: the crossing is before the horizon
    iv = _clipped(curve, h_lo, h_hi)
    assert cc.classify_graze(curve, "venus", "conjunction", TARGET, iv, h_lo, h_hi) is None


def test_codex3_item2_the_clipped_stretch_must_also_PASS_the_speed_bound_proof():
    """The proof covers the stretch beyond the horizon too: a double crossing hidden OUTSIDE the horizon (inside the extension) is found."""
    f = _dip(-0.002)
    h_lo, h_hi = T0 + 2 * td_hours(0), T0 + 60 * DAY                      # horizon starts exactly at the dip: the crossings at +-16 min straddle the start
    h_lo = T0 - timedelta(minutes=5)
    iv = _clipped(f, h_lo, h_hi)
    assert iv[0] == h_lo
    assert cc.classify_graze(f, "venus", "conjunction", TARGET, iv, h_lo, h_hi) is None


def td_hours(h):
    return _td(hours=h)


def test_codex3_item2_the_real_jupiter_graze_over_calendar_2004_is_a_clipped_graze_with_the_whole_stretch():
    """Codex's example (the test database's stub chart: Jupiter aspect to 265.39): no contact for Jan 1 to Jan 23 over calendar 2004; the whole stretch is
    2003-12-15 to 2004-01-23 and the ray level is never reached."""
    from services.gochara_kernel.knots import calc_sidereal_lon
    from .conftest import EPHE_PATH, assert_real_ephemeris
    assert_real_ephemeris()
    jd0 = 2440587.5

    def real(body, t):
        lon, flag = calc_sidereal_lon(body.title(), t.timestamp() / 86400.0 + jd0, EPHE_PATH)
        assert flag & 2
        return lon
    h_lo, h_hi = datetime(2004, 1, 1, tzinfo=UTC), datetime(2005, 1, 1, tzinfo=UTC)
    target = "point:265.39"
    want = [iv for iv in cc.expected_intervals(real, "jupiter", "aspect", target, h_lo, h_hi) if iv[0] < datetime(2004, 3, 1, tzinfo=UTC)]     # the July 2004 stretch is a real contact
    assert len(want) == 1 and want[0][0] == h_lo
    sink: list = []
    problems = cc.compare_contact_sets(real, "jupiter", "aspect", target, want, [], h_lo, h_hi, graze_sink=sink)
    assert problems == [] and len(sink) == 1, (problems, sink)
    g = sink[0]
    assert g["clipped_by_horizon"] == ["start"] and g["interval"][0].startswith("2003-12-15") and g["interval"][1].startswith("2004-01-23")
    assert g["horizon_interval"][0].startswith("2004-01-01")
    assert cc.compare_contact_sets(real, "jupiter", "aspect", target, want, [], h_lo, h_hi)                                   # without a sink it still raises
