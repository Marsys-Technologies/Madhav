"""MB-ADDITIONS 4: the interim sink records UNRESOLVED stretches (with the reason), seams and wraps, in a structured form.

Synthetic exact curves (no ephemeris, no database): the certifier's per-stretch records, the unresolved policy, and the pure record builder. The writer's own
wiring is checked without a database by calling its record function and by the structure of the verify substep.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from services.gochara_kernel import contact_certify as cc
from services.gochara_kernel import interim_sink as sink_mod

from .test_member_geometry_seam import DAY, RAY, T0, curve, curve_graze

UTC = timezone.utc
LO, HI = T0 - 40 * DAY, T0 + 40 * DAY
TARGET = f"point:{RAY}"
ACC = 0.00027777778


def _want(fn, body="venus", relation="conjunction", target=TARGET, lo=LO, hi=HI):
    return cc.expected_intervals(fn, body, relation, target, lo, hi)


# ── the reasons ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def test_a_graze_returns_its_dict_and_no_reason_and_classify_graze_is_unchanged():
    (iv,) = _want(curve_graze)
    g, reason = cc.classify_graze_detail(curve_graze, "venus", "conjunction", TARGET, iv, LO, HI)
    assert g is not None and reason is None
    assert cc.classify_graze(curve_graze, "venus", "conjunction", TARGET, iv, LO, HI) == g


def test_every_none_of_classify_graze_names_its_reason():
    (iv,) = _want(curve)
    assert cc.classify_graze_detail(curve, "venus", "conjunction", TARGET, iv, LO, HI) == (None, cc.REASON_LEVEL_CROSSED)

    def near(body, t):                                  # the minimum is 0.003 deg from the level: inside the 18 arcsecond guard
        d = (t - T0).total_seconds() / 86400.0
        return RAY + 0.003 + 0.02 * d * d
    (iv_n,) = _want(near)
    assert cc.classify_graze_detail(near, "venus", "conjunction", TARGET, iv_n, LO, HI) == (None, cc.REASON_APPROACH_BELOW_MINIMUM)
    assert cc.classify_graze_detail(curve_graze, "venus", "residence", "span:5", (T0 - DAY, T0 + DAY), LO, HI) == (None, cc.REASON_NOT_APPLICABLE)


def test_a_clipped_stretch_whose_extension_cannot_be_settled_is_unresolved_for_that_reason(monkeypatch):
    clip_lo = T0 - 3 * DAY
    (iv,) = _want(curve_graze, lo=clip_lo)
    monkeypatch.setattr(cc, "_full_stretch", lambda *a, **k: None)
    assert cc.classify_graze_detail(curve_graze, "venus", "conjunction", TARGET, iv, clip_lo, HI) == (None, cc.REASON_EXTENSION_NOT_SETTLED)


def test_a_step_whose_no_crossing_cannot_be_proved_is_unresolved_for_that_reason(monkeypatch):
    (iv,) = _want(curve_graze)
    monkeypatch.setattr(cc, "_no_crossing_proved", lambda *a, **k: False)
    assert cc.classify_graze_detail(curve_graze, "venus", "conjunction", TARGET, iv, LO, HI) == (None, cc.REASON_CROSSING_NOT_PROVED)


def test_only_the_four_undecidable_reasons_are_unresolved_a_proven_crossing_and_a_non_point_target_are_not():
    assert set(cc.UNRESOLVED_REASONS) == {cc.REASON_EXTENSION_NOT_SETTLED, cc.REASON_CROSSING_NOT_PROVED, cc.REASON_APPROACH_BELOW_MINIMUM, cc.REASON_NO_LEVEL_IN_BAND}
    assert cc.REASON_LEVEL_CROSSED not in cc.UNRESOLVED_REASONS and cc.REASON_NOT_APPLICABLE not in cc.UNRESOLVED_REASONS


# ── the stretch sink and the policy ───────────────────────────────────────────────────────────────────────────────────────────────

def _compare(fn, want, have, policy=cc.UNRESOLVED_RAISE, graze=True):
    grazes, stretches = ([] if graze else None), []
    problems = cc.compare_contact_sets(fn, "venus", "conjunction", TARGET, want, have, LO, HI, graze_sink=grazes, stretch_sink=stretches, unresolved_policy=policy)
    return problems, grazes, stretches


def test_a_contact_a_graze_and_an_omission_are_each_recorded_with_their_class():
    (iv,) = _want(curve)
    problems, _g, st = _compare(curve, [iv], [(iv[0], iv[1], ACC)])
    assert problems == [] and [r["class"] for r in st] == ["contact"]
    problems, g, st = _compare(curve_graze, _want(curve_graze), [])
    assert problems == [] and len(g) == 1 and [r["class"] for r in st] == ["graze"] and st[0]["closest_approach_deg"] == g[0]["closest_approach_deg"]
    problems, g, st = _compare(curve, [iv], [])                                           # a crossing with no contact: a proven omission, raised
    assert problems and g == [] and [(r["class"], r["reason"]) for r in st] == [("omission", cc.REASON_LEVEL_CROSSED)]


def _near(body, t):
    d = (t - T0).total_seconds() / 86400.0
    return RAY + 0.003 + 0.02 * d * d


def test_an_unresolved_stretch_is_recorded_with_its_reason_and_still_raises_under_the_default_policy():
    (iv,) = _want(_near)
    problems, g, st = _compare(_near, [iv], [])
    assert problems and "is not in the ledger" in problems[0] and g == []
    assert [(r["class"], r["reason"]) for r in st] == [("unresolved", cc.REASON_APPROACH_BELOW_MINIMUM)]
    assert st[0]["interval"] == [iv[0].isoformat(), iv[1].isoformat()] and st[0]["clipped_at_horizon"] == []


def test_under_the_report_policy_the_measuring_build_counts_an_unresolved_stretch_and_does_not_abort_on_it():
    (iv,) = _want(_near)
    problems, _g, st = _compare(_near, [iv], [], policy=cc.UNRESOLVED_REPORT)
    assert problems == [] and [(r["class"], r["reason"]) for r in st] == [("unresolved", cc.REASON_APPROACH_BELOW_MINIMUM)]


def test_the_report_policy_never_forgives_a_proven_omission_or_a_stretch_a_ledger_contact_half_covers():
    (iv,) = _want(curve)
    problems, _g, st = _compare(curve, [iv], [], policy=cc.UNRESOLVED_REPORT)
    assert problems and st[0]["class"] == "omission"
    (ig,) = _want(curve_graze)
    half = [(ig[0], ig[0] + (ig[1] - ig[0]) / 2, ACC)]
    problems, _g, st = _compare(curve_graze, [ig], half, policy=cc.UNRESOLVED_REPORT)
    assert problems and [r["class"] for r in st] == ["contact"], "a touched stretch is a contact stretch: its mismatch is the old, raised problem"


def test_a_horizon_clipped_stretch_is_flagged_in_its_record():
    clip_lo = T0 - 3 * DAY
    (iv,) = _want(curve, lo=clip_lo)
    grazes, st = [], []
    cc.compare_contact_sets(curve, "venus", "conjunction", TARGET, [iv], [(iv[0], iv[1], ACC)], clip_lo, HI, graze_sink=grazes, stretch_sink=st)
    assert st[0]["clipped_at_horizon"] == ["start"]


def test_without_a_graze_sink_the_stretch_sink_still_counts_but_nothing_is_forgiven():
    (iv,) = _want(_near)
    stretches: list = []
    problems = cc.compare_contact_sets(_near, "venus", "conjunction", TARGET, [iv], [], LO, HI, stretch_sink=stretches, unresolved_policy=cc.UNRESOLVED_REPORT)
    assert problems, "no graze sink = no slice: the policy is irrelevant, the old behaviour"
    assert [r["class"] for r in stretches] == ["unclassified"]


def test_an_unknown_policy_is_refused():
    with pytest.raises(ValueError, match="unresolved_policy"):
        cc.compare_contact_sets(curve, "venus", "conjunction", TARGET, [], [], LO, HI, unresolved_policy="forgive")


# ── the pure record ───────────────────────────────────────────────────────────────────────────────────────────────────────────────────

def _rec(cls, body, relation, target, start, reason=None, clipped=()):
    r = {"body": body, "relation": relation, "target": target, "interval": [start.isoformat(), (start + 3 * DAY).isoformat()], "class": cls,
         "clipped_at_horizon": list(clipped)}
    if reason:
        r["reason"] = reason
    return r


def _build(stretches, grazes=(), stations=None):
    stations = stations or {}
    return sink_mod.build_record(
        event_class="marriage", generation="5.0", horizon=(LO, HI), stretches=list(stretches), grazes=list(grazes),
        stations_in=lambda b, t0, t1: [s for s in stations.get(b, []) if t0 <= datetime.fromisoformat(s) < t1],
        levels_for=lambda b, rel, tgt: sink_mod.levels_of(rel, tgt, (120.0, 240.0) if rel == "aspect" else ()),
        orb_for=lambda rel: 1.0)


def test_the_record_counts_every_stretch_by_class_and_orthogonally_the_clipped_the_seams_and_the_wraps():
    seam_station = (T0 + 4 * DAY).isoformat()
    stretches = [
        _rec("contact", "venus", "conjunction", "point:120.0", T0 + 3 * DAY),
        _rec("contact", "venus", "conjunction", "point:120.0", T0 + 3 * DAY * 0 + 10 * DAY, clipped=("start",)),
        _rec("graze", "mars", "conjunction", "point:50.0", T0),
        _rec("unresolved", "saturn", "conjunction", "point:359.6", T0 + 20 * DAY, reason=cc.REASON_CROSSING_NOT_PROVED),          # the band straddles the 0/360 cut
        _rec("unresolved", "jupiter", "conjunction", "point:80.0", T0 + 30 * DAY, reason=cc.REASON_EXTENSION_NOT_SETTLED, clipped=("end",)),
        _rec("omission", "mercury", "conjunction", "point:10.0", T0 + 35 * DAY, reason=cc.REASON_LEVEL_CROSSED),
    ]
    rec = _build(stretches, grazes=[{"body": "mars", "relation": "conjunction", "target": "point:50.0", "interval": [T0.isoformat(), (T0 + 3 * DAY).isoformat()],
                                     "closest_approach_deg": 0.3}], stations={"venus": [seam_station]})
    assert rec["schema"] == sink_mod.SINK_SCHEMA and rec["event_class"] == "marriage" and rec["generation"] == "5.0"
    c = rec["counts"]
    assert (c["stretches"], c["contact"], c["graze"], c["unresolved"], c["omission"]) == (6, 2, 1, 2, 1)
    assert (c["horizon_clipped"], c["seam"], c["wrap"]) == (2, 1, 1)
    assert [(u["body"], u["reason"]) for u in rec["unresolved"]] == [("jupiter", cc.REASON_EXTENSION_NOT_SETTLED), ("saturn", cc.REASON_CROSSING_NOT_PROVED)]
    assert [o["reason"] for o in rec["omissions"]] == [cc.REASON_LEVEL_CROSSED]
    assert rec["seams"][0]["stations"] == [seam_station] and rec["seams"][0]["body"] == "venus"
    assert rec["wraps"][0]["body"] == "saturn" and len(rec["grazes"]) == 1


def test_plain_contacts_are_counted_but_never_listed():
    rec = _build([_rec("contact", "venus", "conjunction", "point:120.0", T0 + i * 4 * DAY) for i in range(50)])
    assert rec["counts"]["contact"] == 50 and rec["unresolved"] == [] and rec["seams"] == [] and rec["wraps"] == [] and rec["grazes"] == []


def test_an_aspect_wrap_is_found_from_its_ray_levels_not_only_the_target():
    # an aspect at 120 deg to a point at 121: the ray level is 1.0, inside the orb of the cut; a conjunction at 121 is not near the cut
    wraps = _build([_rec("contact", "jupiter", "aspect", "point:121.0", T0), _rec("contact", "jupiter", "conjunction", "point:121.0", T0 + 5 * DAY)])["wraps"]
    assert [w["relation"] for w in wraps] == ["aspect"]
    assert sink_mod.band_straddles_the_cut(0.5, 1.0) and sink_mod.band_straddles_the_cut(359.2, 1.0) and not sink_mod.band_straddles_the_cut(2.5, 1.0)


def test_the_record_is_deterministic_whatever_the_input_order_and_round_trips_through_its_log_line():
    stretches = [_rec("unresolved", "saturn", "conjunction", "point:80.0", T0 + i * 5 * DAY, reason=cc.REASON_CROSSING_NOT_PROVED) for i in range(4)]
    a, b = _build(stretches), _build(list(reversed(stretches)))
    assert a == b and sink_mod.canonical_json(a) == sink_mod.canonical_json(b)
    line = "2026-10-06T00:00:00Z WARNING pipeline: " + sink_mod.log_line(a)
    assert sink_mod.parse_log_line(line) == json.loads(sink_mod.canonical_json(a)) and "\n" not in sink_mod.log_line(a)
    with pytest.raises(ValueError, match="not an interim-sink"):
        sink_mod.parse_log_line("something else")
    with pytest.raises(ValueError, match="schema"):
        sink_mod.parse_log_line(sink_mod.LOG_PREFIX + json.dumps({"schema": "x/1"}))


def test_the_levels_of_a_target_match_the_graze_classifiers_own():
    assert sink_mod.levels_of("conjunction", "point:120.0", ()) == [120.0]
    assert sink_mod.levels_of("aspect", "point:50.0", (120.0, 240.0)) == [290.0, 170.0]
    assert sink_mod.levels_of("conjunction", "span:5", ()) == []


# ── the writer's wiring (no database) ─────────────────────────────────────────────────────────────────────────────────────────────────

def test_the_writer_builds_the_record_from_the_certifiers_sinks_with_the_real_orb_and_aspect_tables(monkeypatch):
    from pipeline.orchestrator.writers import ka_gochara_v5 as w
    monkeypatch.setattr(w, "_station_instants_in", lambda body, t0, t1, ephe: [])
    stretches = [_rec("unresolved", "jupiter", "aspect", "point:121.0", T0, reason=cc.REASON_APPROACH_BELOW_MINIMUM)]
    rec = w._interim_sink_record("marriage", (LO, HI), [], stretches, "/x")
    assert rec["counts"]["unresolved"] == 1 and rec["unresolved"][0]["reason"] == cc.REASON_APPROACH_BELOW_MINIMUM
    assert rec["counts"]["wrap"] == 1, "jupiter's aspects are 120/240 from 121: the 1.0 level is inside the orb of the cut (the real tables)"


def test_the_verify_substep_logs_the_record_even_when_the_certification_raises_and_reports_only_for_the_measuring_build():
    import inspect
    from pipeline.orchestrator.writers import ka_gochara_v5 as w
    src = inspect.getsource(w.GocharaV5Writer._run_inventory_phase)
    assert "finally:" in src and "gk_interim_sink.log_line(sink_record)" in src
    assert 'slice_.run == "all_classes_full"' in src and "UNRESOLVED_REPORT" in src and "UNRESOLVED_RAISE" in src
    assert "stretch_sink=stretch_sink, unresolved_policy=policy" in src
