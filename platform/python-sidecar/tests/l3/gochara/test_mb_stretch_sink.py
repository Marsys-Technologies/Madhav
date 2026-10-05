"""MEASURING_BUILD_CONTRACT MB-2 (T2.1, T2.2) and the steward's rulings on it: the STRETCH_SINK/1 record, its closed (kind, reason) table, stable record ids, the per-class
summary with its digest, the two distinct seam kinds, and the policy of the measuring build (near-miss, unresolved and omission are SUNK and the build continues;
every other shape keeps raising).

Synthetic exact curves (no ephemeris, no database): one stub `position_at` per reason row, fed to the real certifier.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone

import pytest

from services.gochara_kernel import contact_certify as cc
from services.gochara_kernel import stretch_sink as ss

from .test_member_geometry_seam import DAY, RAY, T0, curve, curve_graze

UTC = timezone.utc
LO, HI = T0 - 40 * DAY, T0 + 40 * DAY
HORIZON = (LO, HI)
TARGET = f"point:{RAY}"
ACC = 0.00027777778


def _want(fn, body="venus", relation="conjunction", target=TARGET, lo=LO, hi=HI):
    return cc.expected_intervals(fn, body, relation, target, lo, hi)


def _near(body, t):                                     # the minimum is only 0.003 deg from the level: inside the 18 arcsecond guard
    d = (t - T0).total_seconds() / 86400.0
    return RAY + 0.003 + 0.02 * d * d


def _compare(fn, want, have, policy=cc.POLICY_RAISE, body="venus", relation="conjunction", target=TARGET, lo=LO, hi=HI, graze=True):
    grazes, stretches = ([] if graze else None), []
    problems = cc.compare_contact_sets(fn, body, relation, target, want, have, lo, hi, graze_sink=grazes, stretch_sink=stretches, sink_policy=policy)
    return problems, grazes, stretches


# ── the six None cases of classify_graze are separated, with their reasons (AST P1-6) ──────────────────────────────────────────────────

def test_classify_graze_names_the_reason_of_every_none_and_classify_graze_is_unchanged():
    (iv,) = _want(curve_graze)
    g, reason = cc.classify_graze_detail(curve_graze, "venus", "conjunction", TARGET, iv, LO, HI)
    assert g is not None and reason is None and cc.classify_graze(curve_graze, "venus", "conjunction", TARGET, iv, LO, HI) == g
    (iv_c,) = _want(curve)
    assert cc.classify_graze_detail(curve, "venus", "conjunction", TARGET, iv_c, LO, HI) == (None, cc.REASON_LEVEL_CROSSED)
    (iv_n,) = _want(_near)
    assert cc.classify_graze_detail(_near, "venus", "conjunction", TARGET, iv_n, LO, HI) == (None, cc.REASON_APPROACH_BELOW_MINIMUM)
    assert cc.classify_graze_detail(curve_graze, "venus", "residence", "span:5", (T0 - DAY, T0 + DAY), LO, HI) == (None, cc.REASON_NOT_APPLICABLE)
    far = lambda body, t: RAY + 50.0                                         # noqa: E731  (no ray level within the orb of the sampled stretch)
    assert cc.classify_graze_detail(far, "venus", "conjunction", TARGET, (T0 - DAY, T0 + DAY), LO, HI) == (None, cc.REASON_NO_LEVEL_IN_BAND)


def test_extension_unsettled_and_no_crossing_unproved_are_reached_with_their_details(monkeypatch):
    clip_lo = T0 - 3 * DAY
    (iv,) = _want(curve_graze, lo=clip_lo)
    monkeypatch.setattr(cc, "_full_stretch", lambda *a, **k: None)
    assert cc.classify_graze_detail(curve_graze, "venus", "conjunction", TARGET, iv, clip_lo, HI) == (None, cc.REASON_EXTENSION_NOT_SETTLED)
    monkeypatch.undo()
    (iv2,) = _want(curve_graze)
    monkeypatch.setattr(cc, "_no_crossing_proved", lambda *a, **k: False)
    assert cc.classify_graze_detail(curve_graze, "venus", "conjunction", TARGET, iv2, LO, HI) == (None, cc.REASON_CROSSING_NOT_PROVED)


def test_the_extension_detail_distinguishes_an_ambiguous_extension_from_one_that_exceeds_1500_days(monkeypatch):
    clip_lo = T0 - 3 * DAY
    long_band = lambda body, t: RAY + 0.3                                    # noqa: E731  (in band forever: never exits within 1500 days)
    assert cc._full_stretch(long_band, "venus", [RAY], 1.0, clip_lo, clip_lo + 6 * DAY, clip_lo, HI) is None and cc._full_stretch.last_detail == "exceeds_1500_days"
    monkeypatch.setattr(cc.cr, "band_intervals", lambda *a, **k: [(clip_lo - DAY, clip_lo + 4 * DAY), (clip_lo + DAY, clip_lo + 9 * DAY)])     # two stretches overlap it
    assert cc._full_stretch(curve_graze, "venus", [RAY], 1.0, clip_lo, clip_lo + 6 * DAY, clip_lo, HI) is None and cc._full_stretch.last_detail == "ambiguous_extension"


# ── T2.1: one stretch per reason row, each with kind and reason, and a record_id that does not depend on input order ───────────────────

def _records_for(stretches, stations=(), episodes=None, wrapped=False, horizon=HORIZON):
    return ss.build_records(
        event_class="marriage", horizon=horizon, stretches=stretches,
        stations_in=lambda b, t0, t1: [s.isoformat() for s in stations if t0 <= s < t1],
        levels_for=lambda b, rel, tgt: ss.levels_of(rel, tgt, (120.0, 240.0) if rel == "aspect" else ()),
        orb_for=lambda rel: 1.0, body_wrapped_inside=lambda b, t0, t1: wrapped)


def _one(fn, **kw):
    problems, grazes, stretches = _compare(fn, kw.pop("want", None) or _want(fn), kw.pop("have", []), **kw)
    return problems, grazes, stretches


@pytest.mark.parametrize("name, fn, want_kw, expect", [
    ("near_miss", curve_graze, {}, ("near_miss", "certified_positive_clearance")),
    ("clearance_below_min", _near, {}, ("unresolved", "clearance_below_min_approach")),
    ("omission_crossing", curve, {}, ("omission", "crossing_detected")),
])
def test_each_certified_outcome_becomes_its_closed_kind_and_reason(name, fn, want_kw, expect):
    _p, _g, st = _one(fn, policy=cc.POLICY_SINK_ALL)
    recs = _records_for(st)
    assert [(r["kind"], r["reason"]) for r in recs if r["kind"] in ss.CAUSE_KINDS] == [expect]
    r = [x for x in recs if x["kind"] in ss.CAUSE_KINDS][0]
    assert r["schema"] == "stretch_sink/1" and r["event_class"] == "marriage" and r["body"] == "venus" and r["canonical_target"] == TARGET and r["orb_deg"] == 1.0
    assert r["horizon_interval"][0] == st[0]["interval"][0] and r["record_id"] and set(r) >= {"level_deg", "full_interval", "clipped_by_horizon", "closest_approach_deg",
                                                                                           "closest_approach_at", "peak_activity", "episode_count", "detail"}


def test_the_near_miss_record_carries_the_certified_approach_and_the_unresolved_ones_do_not():
    _p, g, st = _one(curve_graze, policy=cc.POLICY_SINK_ALL)
    (r,) = [x for x in _records_for(st) if x["kind"] == "near_miss"]
    assert abs(r["closest_approach_deg"] - 0.3) < 0.01 and r["closest_approach_at"] and abs(r["peak_activity"] - 0.7) < 0.01 and r["level_deg"] == RAY
    _p, _g, st2 = _one(_near, policy=cc.POLICY_SINK_ALL)
    (u,) = [x for x in _records_for(st2) if x["kind"] == "unresolved"]
    assert u["closest_approach_deg"] is None and u["peak_activity"] is None


def test_no_crossing_unproved_and_extension_unsettled_are_unresolved_and_carry_their_reason_and_detail(monkeypatch):
    (iv,) = _want(curve_graze)
    monkeypatch.setattr(cc, "_no_crossing_proved", lambda *a, **k: False)
    _p, _g, st = _compare(curve_graze, [iv], [], policy=cc.POLICY_SINK_ALL)
    assert [(r["kind"], r["reason"]) for r in _records_for(st) if r["kind"] in ss.CAUSE_KINDS] == [("unresolved", "no_crossing_unproved")]
    monkeypatch.undo()
    clip_lo = T0 - 3 * DAY
    (ivc,) = _want(curve_graze, lo=clip_lo)
    monkeypatch.setattr(cc, "_full_stretch", lambda *a, **k: None)
    cc._full_stretch.last_detail = "exceeds_1500_days"
    _p, _g, st = _compare(curve_graze, [ivc], [], policy=cc.POLICY_SINK_ALL, lo=clip_lo)
    (u,) = [r for r in _records_for(st, horizon=(clip_lo, HI)) if r["kind"] == "unresolved"]
    assert u["reason"] == "extension_unsettled" and u["detail"] == {"extension": "exceeds_1500_days"}


def test_a_span_target_with_no_ledger_contact_is_an_omission_unsupported_target_and_no_relevant_level_is_an_anomaly():
    iv = (T0 - DAY, T0 + DAY)
    _p, _g, st = _compare(curve_graze, [iv], [], policy=cc.POLICY_SINK_ALL, relation="residence", target="span:5")
    assert [(r["kind"], r["reason"]) for r in _records_for(st) if r["kind"] in ss.CAUSE_KINDS] == [("omission", "unsupported_target")]
    far = lambda body, t: RAY + 50.0                                         # noqa: E731
    _p, _g, st2 = _compare(far, [iv], [], policy=cc.POLICY_SINK_ALL)
    assert [(r["kind"], r["reason"]) for r in _records_for(st2) if r["kind"] in ss.CAUSE_KINDS] == [("anomaly", "no_relevant_level")]


def test_a_stretch_straddling_the_horizon_edge_that_resolves_is_a_near_miss_and_a_horizon_clipped_record():
    clip_lo = T0 - 3 * DAY
    (iv,) = _want(curve_graze, lo=clip_lo)
    _p, _g, st = _compare(curve_graze, [iv], [], policy=cc.POLICY_SINK_ALL, lo=clip_lo)
    kinds = {(r["kind"], r["reason"]) for r in _records_for(st, horizon=(clip_lo, HI))}
    assert ("near_miss", "certified_positive_clearance") in kinds and ("horizon_clipped", "clipped_at_start") in kinds


def test_a_ledger_covered_stretch_is_a_contact_and_yields_no_cause_record_but_can_yield_seam_wrap_and_clipping_records():
    (iv,) = _want(curve)
    _p, _g, st = _compare(curve, [iv], [(iv[0], iv[1], ACC)], policy=cc.POLICY_SINK_ALL)
    assert [s["kind"] for s in st] == ["contact"] and st[0]["episode_count"] == 1 and st[0]["stretch_ordinal"] == 1
    assert _records_for(st) == []


def test_two_ledger_episodes_inside_one_stretch_is_a_multi_episode_stretch_and_a_station_inside_is_a_station_seam_two_distinct_kinds():
    (iv,) = _want(curve)
    mid = iv[0] + (iv[1] - iv[0]) / 2
    have = [(iv[0], mid + timedelta(hours=1), ACC), (mid - timedelta(hours=1), iv[1], ACC)]
    _p, _g, st = _compare(curve, [iv], have, policy=cc.POLICY_SINK_ALL)
    assert st[0]["episode_count"] == 2
    recs = _records_for(st, stations=[T0])
    kinds = sorted(r["kind"] for r in recs)
    assert kinds == ["multi_episode_stretch", "station_seam"], "both facts are recorded and neither replaces the other"
    by = {r["kind"]: r for r in recs}
    assert by["multi_episode_stretch"]["episode_count"] == 2 and by["station_seam"]["detail"] == {"stations": [T0.isoformat()]}
    assert len({r["record_id"] for r in recs}) == 2, "each record has its own id"


def test_a_ray_band_containing_the_0_360_cut_is_a_wrap_record_with_body_wrapped_inside_in_its_detail():
    iv = (T0, T0 + 3 * DAY)
    st = [{"body": "saturn", "relation": "conjunction", "target": "point:359.6", "interval": [iv[0].isoformat(), iv[1].isoformat()], "stretch_ordinal": 1,
           "clipped_at_horizon": [], "episode_count": 1, "kind": "contact", "reason": None}]
    (r,) = _records_for(st, wrapped=True)
    assert (r["kind"], r["reason"], r["detail"]) == ("wrap", "ray_band_contains_wrap_cut", {"body_wrapped_inside": True}) and r["level_deg"] == 359.6
    assert _records_for(st, wrapped=False)[0]["detail"] == {"body_wrapped_inside": False}
    st[0]["target"] = "point:120.0"
    assert _records_for(st) == []


def test_clipped_at_end_and_clipped_both():
    base = {"body": "venus", "relation": "conjunction", "target": TARGET, "interval": [LO.isoformat(), HI.isoformat()], "stretch_ordinal": 1, "episode_count": 1,
            "kind": "contact", "reason": None}
    assert [r["reason"] for r in _records_for([{**base, "clipped_at_horizon": ["end"]}])] == ["clipped_at_end"]
    assert [r["reason"] for r in _records_for([{**base, "clipped_at_horizon": ["start", "end"]}])] == ["clipped_both"]


# ── record ids: stable under input order and sub-second jitter, unique per kind, horizon-relative ────────────────────────────────────

def test_record_ids_do_not_change_when_the_obligations_and_intervals_are_fed_in_reverse_order_and_each_kind_has_its_own():
    wants = {"graze": (curve_graze, _want(curve_graze)), "near": (_near, _want(_near))}
    sts = []
    for fn, want in wants.values():
        sts += _compare(fn, want, [], policy=cc.POLICY_SINK_ALL)[2]
    a, b = _records_for(sts), _records_for(list(reversed(sts)))
    assert a == b and [r["record_id"] for r in a] == [r["record_id"] for r in b]
    assert len({r["record_id"] for r in a}) == len(a)


def test_a_sub_second_jitter_of_the_interval_does_not_move_the_id_but_a_different_ordinal_or_horizon_does():
    st = _compare(curve_graze, _want(curve_graze), [], policy=cc.POLICY_SINK_ALL)[2]
    jittered = [dict(st[0], interval=[(datetime.fromisoformat(st[0]["interval"][0]) + timedelta(seconds=0.4)).isoformat(), st[0]["interval"][1]])]
    assert _records_for(st)[0]["record_id"] == _records_for(jittered)[0]["record_id"]
    assert _records_for([dict(st[0], stretch_ordinal=2)])[0]["record_id"] != _records_for(st)[0]["record_id"]
    assert _records_for(st, horizon=(LO, HI + DAY))[0]["record_id"] != _records_for(st)[0]["record_id"]


def test_the_record_id_is_the_uuid8_of_the_contracts_key():
    from services.gochara_kernel.substrate import _uuid8_of
    key = f"stretch_sink/1|near_miss|venus|conjunction|{TARGET}|1.0|{LO.isoformat()}|{HI.isoformat()}|1"
    assert ss.record_id("near_miss", "venus", "conjunction", TARGET, 1.0, HORIZON, 1) == str(_uuid8_of(key.encode()))


# ── T2.2: the log line parses back, the summary digest equals sha256 of the sorted ids ───────────────────────────────────────────────

def test_the_log_line_parses_back_to_the_record_and_the_summary_digest_is_the_sha256_of_the_sorted_ids():
    import hashlib
    sts = _compare(curve_graze, _want(curve_graze), [], policy=cc.POLICY_SINK_ALL)[2] + _compare(_near, _want(_near), [], policy=cc.POLICY_SINK_ALL)[2]
    recs = _records_for(sts)
    for r in recs:
        line = "2026-10-06T00:00:00Z WARNING x: " + ss.log_line(r)
        assert ss.parse_line(line) == json.loads(ss.canonical_json(r)) and "\n" not in ss.log_line(r)
    summ = ss.summary("marriage", "5.0", HORIZON, recs, sts)
    assert summ["schema"] == "stretch_sink_summary/1" and summ["records"] == len(recs) and summ["stretches"] == 2
    assert summ["record_ids_digest"] == hashlib.sha256("\n".join(sorted(r["record_id"] for r in recs)).encode()).hexdigest()
    assert summ["counts_by_kind_reason"] == {"near_miss/certified_positive_clearance": 1, "unresolved/clearance_below_min_approach": 1}
    assert ss.parse_line(ss.summary_line(summ)) == json.loads(ss.canonical_json(summ))
    ss.check_summary(summ, recs)
    with pytest.raises(ss.StretchSinkUnparseable, match="stretch_sink_summary_digest_mismatch"):
        ss.check_summary(summ, recs[:1])


def test_a_line_that_is_not_the_schema_is_refused_by_name():
    for bad in ("something else", ss.LOG_PREFIX + "{not json", ss.LOG_PREFIX + json.dumps({"schema": "x/1"}), ss.SUMMARY_PREFIX + json.dumps({"schema": "stretch_sink/1"})):
        with pytest.raises(ss.StretchSinkUnparseable, match="stretch_sink_unparseable"):
            ss.parse_line(bad)


def test_the_closed_table_is_exactly_the_contracts_plus_the_two_seam_kinds():
    assert ss.KIND_REASONS == {
        "near_miss": ("certified_positive_clearance",), "unresolved": ("clearance_below_min_approach", "extension_unsettled", "no_crossing_unproved"),
        "omission": ("crossing_detected", "unsupported_target"), "anomaly": ("no_relevant_level",), "station_seam": ("arc_index_station_inside_stretch",),
        "multi_episode_stretch": ("two_or_more_ledger_episodes",), "wrap": ("ray_band_contains_wrap_cut",),
        "horizon_clipped": ("clipped_at_start", "clipped_at_end", "clipped_both")}
    for outcome, (kind, reason) in cc.OUTCOME_KIND_REASON.items():
        assert reason in ss.KIND_REASONS[kind], (outcome, kind, reason)


# ── the policy boundary (steward 4(f) / OS-6), both sides ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("fn, kind", [(curve_graze, "near_miss"), (_near, "unresolved"), (curve, "omission")])
def test_under_sink_all_a_near_miss_an_unresolved_stretch_and_an_omission_are_sunk_and_the_class_continues(fn, kind):
    problems, _g, st = _compare(fn, _want(fn), [], policy=cc.POLICY_SINK_ALL)
    assert problems == [] and [s["kind"] for s in st] == [kind]


def test_under_the_default_policy_only_the_near_miss_is_not_raised_unresolved_and_omission_still_raise():
    assert _compare(curve_graze, _want(curve_graze), [])[0] == []
    for fn in (_near, curve):
        problems, _g, st = _compare(fn, _want(fn), [])
        assert problems and "is not in the ledger" in problems[0] and st[0]["kind"] in ("unresolved", "omission")


def test_an_anomaly_and_a_stretch_a_ledger_contact_touches_but_does_not_match_still_raise_under_sink_all():
    far = lambda body, t: RAY + 50.0                                         # noqa: E731
    problems, _g, st = _compare(far, [(T0 - DAY, T0 + DAY)], [], policy=cc.POLICY_SINK_ALL)
    assert problems and st[0]["kind"] == "anomaly", "the ruling names near-misses, unresolved stretches and omissions only"
    (iv,) = _want(curve_graze)
    problems, _g, st = _compare(curve_graze, [iv], [(iv[0], iv[0] + (iv[1] - iv[0]) / 2, ACC)], policy=cc.POLICY_SINK_ALL)
    assert problems and [s["kind"] for s in st] == ["contact"]


def test_without_a_graze_sink_nothing_is_forgiven_whatever_the_policy_and_the_stretches_are_still_counted():
    problems, _g, st = _compare(_near, _want(_near), [], policy=cc.POLICY_SINK_ALL, graze=False)
    assert problems and [s["kind"] for s in st] == ["unclassified"]          # no validated slice, no classification: the stretch is only counted


def test_an_unknown_policy_is_refused():
    with pytest.raises(ValueError, match="sink_policy"):
        cc.compare_contact_sets(curve, "venus", "conjunction", TARGET, [], [], LO, HI, sink_policy="forgive")


# ── the writer's wiring (no database) ────────────────────────────────────────────────────────────────────────────────────────────────

def test_the_writer_selects_sink_all_for_all_classes_full_only_and_logs_the_records_and_the_summary_even_when_the_certification_raises():
    import inspect
    from pipeline.orchestrator.writers import ka_gochara_v5 as w
    src = inspect.getsource(w.GocharaV5Writer._run_inventory_phase)
    assert "finally:" in src and "_emit_stretch_sink(" in src
    assert 'slice_.run == "all_classes_full"' in src and "POLICY_SINK_ALL" in src and "POLICY_RAISE" in src
    assert "stretch_sink=stretch_sink, sink_policy=policy" in src and "certifier_omissions_present=" in src


def test_the_writer_logs_one_line_per_record_at_the_contracts_levels_and_one_summary_line_per_class(monkeypatch, caplog):
    from pipeline.orchestrator.writers import ka_gochara_v5 as w
    monkeypatch.setattr(w, "_station_instants_in", lambda body, t0, t1, ephe: [T0.isoformat()] if t0 <= T0 < t1 else [])
    sts = _compare(curve_graze, _want(curve_graze), [], policy=cc.POLICY_SINK_ALL)[2] + _compare(curve, _want(curve), [(_want(curve)[0][0], _want(curve)[0][1], ACC)])[2]
    with caplog.at_level(logging.INFO):
        summary = w._emit_stretch_sink("marriage", HORIZON, sts, lambda b, t: 10.0, "/x")
    lines = [r for r in caplog.records if r.message.startswith(("STRETCH_SINK/1 ", "STRETCH_SINK_SUMMARY/1 "))]
    parsed = [(r.levelno, ss.parse_line(r.message)) for r in lines]
    recs = [p for _lv, p in parsed if p["schema"] == "stretch_sink/1"]
    assert {r["kind"] for r in recs} == {"near_miss", "station_seam"} and all(lv == (logging.WARNING if p["kind"] in ss.WARNING_KINDS else logging.INFO) for lv, p in parsed if p["schema"] == "stretch_sink/1")
    assert parsed[-1][1]["schema"] == "stretch_sink_summary/1" and parsed[-1][1] == json.loads(ss.canonical_json(summary))
    ss.check_summary(summary, recs)
