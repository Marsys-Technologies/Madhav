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


def test_a_horizon_clipped_interval_is_not_classified_because_the_crossing_may_lie_outside_it():
    clip_lo = T0 - 3 * DAY                                           # the in-band stretch is cut by the horizon: classification is refused
    (iv,) = _want(curve_graze, lo=clip_lo)
    assert iv[0] == clip_lo and cc.classify_graze(curve_graze, "venus", "conjunction", TARGET, iv, clip_lo, HI) is None


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
