"""G-6 cross-check on ANALYTIC worlds (no database, no ephemeris): real `window_sweep` primitives (RecordProgram, _pieces, _objective_fn,
maximise_earliest) over closed-form member functions.  Oracles are closed-form maxima (PLAN §2.4 C-S1/C-S2/C-S7: f(t) = x + 1 - x², max 1.25 at x = ½;
two humps with the later one higher; P4 = min of the two agents' activity, not their sum).  The 'solver under test' is simply the stored value."""
import math
from datetime import datetime, timedelta, timezone

import pytest

import crosscheck as cc

ws = pytest.importorskip("services.gochara_kernel.window_sweep")
T0 = datetime(2030, 1, 1, tzinfo=timezone.utc)
HOUR = timedelta(hours=1)


def rec(rid, root, agent="jupiter", path="P3", lo=T0, hi=T0 + HOUR):
    return ws.SweepRecord(record_id=rid, root_id=root, path_id=path, rule_version="9.9.9", relation="conjunction", object_kind="point_longitude", agent=agent,
                          operator_role="scored", admission_state="admitted", supports=((lo, hi),))


def prog(r, fn):
    return ws.RecordProgram(rec=r, qualified=True, null_states=set(), reasons=[], outcomes=[ws.Outcome("fn", fn=fn, factor="activity_kernel")], channel=ws.CHANNEL_FOR)


def frac(t, lo=T0, span=HOUR):
    return (t - lo) / span


def world(fns, path="P3", agents=None):
    progs = [prog(rec(f"r{i}", f"root{i}", agent=(agents[i] if agents else "jupiter"), path=path), fn) for i, fn in enumerate(fns)]
    return cc.pieces_of(ws, progs, path, "bereavement", T0, T0 + HOUR)


RISING = lambda t: frac(t)                                   # noqa: E731
FALLING_SQ = lambda t: 1.0 - frac(t) ** 2                    # noqa: E731
HUMPS = lambda t: max(0.0, 0.5 - abs(frac(t) - 0.25) * 4) * 0.6 + max(0.0, 1.0 - abs(frac(t) - 0.75) * 8) * 0.4 + 0.0   # noqa: E731


def run(pieces, stored, peak_frac, **kw):
    return cc.check_window(ws, pieces, stored, T0 + HOUR * peak_frac, T0, T0 + HOUR, dense_max_days=1, **kw)


def kinds(r):
    return sorted({v["kind"] for v in r["violations"]})


def test_correct_interior_maximum_agrees_with_brute_force():
    # F = x + (1 - x²), max 1.25 at x = ½ (closed form)
    r = run(world([RISING, FALLING_SQ]), 1.25, 0.5)
    assert r["violations"] == [], r
    assert r["dense"]["max"] == pytest.approx(1.25, abs=1e-6) and r["sampler_max"] == pytest.approx(1.25, abs=1e-6)


def test_endpoint_only_value_is_caught_by_brute_force():
    r = run(world([RISING, FALLING_SQ]), 1.0, 0.0)                     # the endpoint-only mistake: F(0) = F(1) = 1
    assert "dense" in kinds(r) and "sampler" in kinds(r), r


def test_a_value_that_does_not_exist_is_caught():
    r = run(world([RISING, FALLING_SQ]), 1.3, 0.5)
    assert "dense" in kinds(r), r


def test_first_hump_instead_of_the_global_maximum_is_caught():
    humps = lambda t: (0.5 if abs(frac(t) - 0.25) < 0.05 else 0.0) + (0.9 if abs(frac(t) - 0.75) < 0.05 else 0.0)    # noqa: E731  step humps: 0.5 then 0.9
    r = run(world([humps]), 0.5, 0.25)
    assert "dense" in kinds(r), r
    assert run(world([humps]), 0.9, 0.75)["violations"] == []


def test_value_at_the_stored_peak_must_reproduce_the_stored_value():
    r = run(world([RISING, FALLING_SQ]), 1.25, 0.0)                    # right value, wrong instant (F(0) = 1)
    assert "recompute_inconsistent" in kinds(r), r


def test_p4_is_max_min_not_sum():
    # act_J rises, act_S falls: min(x, 1-x) has max ½ at x = ½; a SUM would store 1.0
    w = world([RISING, lambda t: 1.0 - frac(t)], path="P4", agents=["jupiter", "saturn"])
    assert run(w, 0.5, 0.5)["violations"] == []
    assert "dense" in kinds(run(w, 1.0, 0.5))


def test_long_windows_are_checked_against_the_legacy_sampler_only():
    w = world([RISING, FALLING_SQ])
    r = cc.check_window(ws, w, 1.0, T0, T0, T0 + HOUR, dense_max_days=0.0001)        # window longer than the dense limit
    assert "dense" not in r and "sampler" in kinds(r), r
    r2 = cc.check_window(ws, w, 1.25, T0 + HOUR * 0.5, T0, T0 + HOUR, dense_max_days=0.0001)
    assert "dense" not in r2 and r2["violations"] == []


def test_an_unknown_objective_is_never_read_as_agreement():
    r = run(world([lambda t: None if frac(t) > 0.9 else 0.5]), 0.5, 0.0)
    assert r["violations"] and "recompute_inconsistent" in kinds(r), r


def test_a_dense_scan_that_hits_its_deadline_is_a_violation_not_a_pass():
    import time
    r = run(world([RISING, FALLING_SQ]), 1.25, 0.5, deadline=time.time() - 1)
    assert "dense" in kinds(r) or "timeout" in kinds(r)


def test_constant_pieces_are_exact_and_cheap():
    step = lambda t: 0.25 if frac(t) < 0.5 else 0.75            # noqa: E731  not flagged constant: a plain function -> dense on the grid
    r = run(world([step]), 0.75, 0.5)
    assert r["violations"] == [], r


def test_mixed_piece_detection():
    assert cc.window_is_mixed(world([RISING, lambda t: 1.0 - frac(t)]))                 # a rising and a falling term concurrent
    assert not cc.window_is_mixed(world([RISING, lambda t: frac(t) ** 2]))              # two rising terms
    assert cc.window_is_mixed(world([lambda t: 1.0 - 4 * (frac(t) - 0.5) ** 2]))        # a single term with an interior crest


def test_sample_size_is_ceiling_of_the_rate_and_selection_is_deterministic():
    assert cc.sample_size(0.03, 1294) == 39 and cc.sample_size(0.03, 100) == 3 and cc.sample_size(0.03, 0) == 0
    ids = [f"w{i:04d}" for i in range(500)]
    a, b = cc.random_sample(ids, 0.03, 7), cc.random_sample(list(reversed(ids)), 0.03, 7)
    assert a == b and len(a) == 15 and a != cc.random_sample(ids, 0.03, 8)


def test_aggregate_names_every_violation_and_counts_what_was_checked():
    sel = {"seed": 1, "random": ["a", "b"], "top_mixed": ["b", "c"]}
    res = {"a": {"violations": [], "dense": {"max": 1}}, "b": {"violations": [{"kind": "dense", "detail": "x"}], "dense": {"max": 1}, "mixed": True},
           "c": {"violations": [{"kind": "sampler", "detail": "y"}, {"kind": "recompute_inconsistent", "detail": "z"}]}}
    out = cc.aggregate(sel, res, 100, 0.03)
    assert out["sampled"] == 2 and out["top_mixed_checked"] == 2 and out["dense"]["windows"] == 2
    assert len(out["dense_violations"]) == 1 and len(out["sampler_violations"]) == 1 and len(out["recompute_inconsistent"]) == 1


def test_adapter_mismatch_is_named():
    class Fake:
        pass
    with pytest.raises(cc.AdapterMismatch):
        cc.check_adapter(Fake())
    cc.check_adapter(ws)


def test_a_narrow_crest_between_grid_points_is_refined_not_misread():
    # tent of half-width 10 s with its crest at 1800.5 s: the 1-second grid sees at most 0.95; the true (and stored) maximum is 1.0 — only the golden-section
    # refinement inside the grid bracket agrees with it (PLAN §2.4 C-S1's narrow-peak world; the legacy sampler's blind spot)
    tent = lambda t: max(0.0, 1.0 - abs((t - T0).total_seconds() - 1800.5) / 10.0)      # noqa: E731
    w = world([tent])
    r = cc.check_window(ws, w, 1.0, T0 + timedelta(seconds=1800.5), T0, T0 + HOUR, dense_max_days=1)
    assert r["violations"] == [], r
    assert r["dense"]["max"] == pytest.approx(1.0, abs=1e-6)
    r2 = cc.check_window(ws, w, 0.95, T0 + timedelta(seconds=1800), T0, T0 + HOUR, dense_max_days=1)       # a solver that stops at the grid value 0.95
    assert "dense" in kinds(r2), r2
