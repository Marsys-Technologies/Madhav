"""MEASURING_BUILD_CONTRACT v1.0 MB-2 (T2.1, T2.2) and the steward's rulings on it: the STRETCH_SINK/1 record (exactly the contract's fields), its closed (kind, reason)
table (exactly the contract's words), the record_id recipe (the contract's text, with the reviewer's worked id as a test vector), the per-class summary with its digest,
the two distinct seam kinds (a seam REQUIRES an overlapping ledger contact), and the policy of the measuring build (EVERYTHING is recorded and nothing raises: near-miss,
unresolved, omission, invented, anomaly; every other shape keeps raising).

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
    assert u["reason"] == "extension_unsettled" and u["detail"] == "exceeds_1500_days"                  # the closed string value, not an object


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
    assert by["multi_episode_stretch"]["episode_count"] == 2 and by["multi_episode_stretch"]["reason"] == "multiple_ledger_episodes"
    assert by["station_seam"]["reason"] == "arc_index_station_inside" and by["station_seam"]["station_at"] == T0.isoformat() and by["station_seam"]["full_interval"] == st[0]["interval"]
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


def _contract_id(kind, body, relation, target, orb, lo, hi, ordinal):
    """The contract's recipe written independently from its TEXT (MB-2.2), sharing no code with `stretch_sink`: this is what a verifier does."""
    import hashlib
    import uuid
    fmt = lambda t: t.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%S+00:00")                    # noqa: E731
    canon = "stretch_sink/1" + "|" + kind + "|" + body + "|" + relation + "|" + target + "|" + ("%.3f" % orb) + "|" + fmt(lo) + "|" + fmt(hi) + "|" + str(ordinal)
    b = bytearray(hashlib.sha256(canon.encode("utf-8")).digest()[:16])
    b[6] = (b[6] & 0x0F) | 0x80
    b[8] = (b[8] & 0x3F) | 0x80
    return str(uuid.UUID(bytes=bytes(b)))


RULED = (datetime(1998, 1, 1, tzinfo=UTC), datetime(2084, 2, 5, tzinfo=UTC))


def test_the_record_id_is_the_contracts_recipe_and_equals_the_reviewers_worked_id():
    """Codex blocker 3: near_miss | venus | conjunction | point:120.0 | orb 1 | ruled horizon | ordinal 1 is 407dbb76-bd2c-8990-82fd-08a51dcf1497 (and was
    308a7c71-... under the old float interpolation)."""
    got = ss.record_id("near_miss", "venus", "conjunction", "point:120.0", 1.0, RULED, 1)
    assert got == "407dbb76-bd2c-8990-82fd-08a51dcf1497" != "308a7c71-e53c-815a-a35e-a4bfc44a10d0"
    assert got == _contract_id("near_miss", "venus", "conjunction", "point:120.0", 1.0, RULED[0], RULED[1], 1)


@pytest.mark.parametrize("kind, body, relation, target, orb, ordinal", [
    ("near_miss", "venus", "conjunction", "point:120.0", 1.0, 1), ("unresolved", "saturn", "aspect", "point:202.432028148023", 1.0, 7),
    ("omission", "jupiter", "aspect", "point:0.5", 1.0, 3), ("wrap", "mars", "conjunction", "point:359.6", 1.0, 12), ("anomaly", "mercury", "conjunction", "point:10.25", 0.5, 2)])
def test_the_record_id_equals_an_independent_implementation_of_the_contract_text(kind, body, relation, target, orb, ordinal):
    assert ss.record_id(kind, body, relation, target, orb, RULED, ordinal) == _contract_id(kind, body, relation, target, orb, RULED[0], RULED[1], ordinal)


def test_a_residence_obligation_has_orb_000_in_its_id_and_a_null_orb_in_its_record():
    got = ss.record_id("omission", "venus", "residence", "span:5", None, RULED, 2)
    assert got == _contract_id("omission", "venus", "residence", "span:5", 0.0, RULED[0], RULED[1], 2) != ss.record_id("omission", "venus", "residence", "span:5", 1.0, RULED, 2)
    iv = (T0 - DAY, T0 + DAY)
    st = [{"body": "venus", "relation": "residence", "target": "span:5", "interval": [iv[0].isoformat(), iv[1].isoformat()], "stretch_ordinal": 2, "clipped_at_horizon": [],
           "episode_count": 0, "kind": "omission", "reason": "unsupported_target"}]
    (r,) = ss.build_records(event_class="marriage", horizon=RULED, stretches=st, stations_in=lambda b, a, c: [], levels_for=lambda b, r_, t: [], orb_for=lambda rel: None,
                            body_wrapped_inside=lambda b, a, c: False)
    assert r["orb_deg"] is None and r["record_id"] == got and r["stretch_ordinal"] == 2


def test_the_record_carries_exactly_the_contracts_fields_stretch_ordinal_and_station_at_included():
    _p, _g, st = _compare(curve_graze, _want(curve_graze), [], policy=cc.POLICY_SINK_ALL)
    (r,) = [x for x in _records_for(st) if x["kind"] == "near_miss"]
    assert set(r) == {"schema", "record_id", "kind", "reason", "detail", "event_class", "body", "relation", "canonical_target", "level_deg", "orb_deg", "horizon_interval",
                      "full_interval", "clipped_by_horizon", "closest_approach_deg", "closest_approach_at", "peak_activity", "episode_count", "station_at", "stretch_ordinal"}
    assert set(r) == set(ss.RECORD_FIELDS) and r["stretch_ordinal"] == 1 and r["station_at"] is None and r["record_id"] == ss.record_id(
        "near_miss", "venus", "conjunction", TARGET, 1.0, HORIZON, 1)


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


def test_the_closed_table_is_exactly_the_contracts_v1_0_mb_2_3():
    """Codex blocker 3: the words are the contract's (arc_index_station_inside, multiple_ledger_episodes) and invented / boundary_pairing_mismatch exist."""
    contract = {
        "near_miss": {"certified_positive_clearance"}, "unresolved": {"clearance_below_min_approach", "no_crossing_unproved", "extension_unsettled"},
        "omission": {"crossing_detected", "unsupported_target"}, "invented": {"ledger_contact_not_reconstructed"}, "anomaly": {"no_relevant_level", "boundary_pairing_mismatch"},
        "station_seam": {"arc_index_station_inside"}, "multi_episode_stretch": {"multiple_ledger_episodes"}, "wrap": {"ray_band_contains_wrap_cut"},
        "horizon_clipped": {"clipped_at_start", "clipped_at_end", "clipped_both"}}
    assert {k: set(v) for k, v in ss.KIND_REASONS.items()} == contract
    for outcome, (kind, reason) in cc.OUTCOME_KIND_REASON.items():
        assert reason in ss.KIND_REASONS[kind], (outcome, kind, reason)
    assert (cc.KIND_INVENTED, cc.REASON_INVENTED, cc.KIND_PAIRING, cc.REASON_PAIRING) == ("invented", "ledger_contact_not_reconstructed", "anomaly", "boundary_pairing_mismatch")


def test_a_word_outside_the_table_is_refused_unknown_kind_or_reason():
    banana = ss.LOG_PREFIX + json.dumps({"schema": "stretch_sink/1", "kind": "banana", "reason": "banana"})
    with pytest.raises(ss.StretchSinkUnparseable, match="stretch_sink_unparseable|unknown_kind_or_reason"):
        ss.parse_line(banana)
    _p, _g, st = _compare(curve_graze, _want(curve_graze), [], policy=cc.POLICY_SINK_ALL)
    (r,) = [x for x in _records_for(st) if x["kind"] == "near_miss"]
    for kind, reason in (("near_miss", "arc_index_station_inside"), ("station_seam", "arc_index_station_inside_stretch"), ("banana", "banana")):
        with pytest.raises(ss.UnknownKindOrReason, match="unknown_kind_or_reason"):
            ss.parse_line(ss.log_line({**r, "kind": kind, "reason": reason}))
    with pytest.raises(ss.StretchSinkUnparseable, match="record fields"):
        ss.parse_line(ss.log_line({k: v for k, v in r.items() if k != "stretch_ordinal"}))


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


FAR = lambda body, t: RAY + 50.0                                             # noqa: E731  (no ray level within the orb of the sampled stretch)
FEB28, MAR2 = datetime(2026, 2, 28, tzinfo=UTC), datetime(2026, 3, 2, tzinfo=UTC)


def test_an_anomaly_is_recorded_not_raised_under_sink_all_and_still_raises_under_the_default_policy():
    problems, _g, st = _compare(FAR, [(T0 - DAY, T0 + DAY)], [], policy=cc.POLICY_SINK_ALL)
    assert problems == [] and [(s["kind"], s["reason"]) for s in st] == [("anomaly", "no_relevant_level")]
    problems, _g, st = _compare(FAR, [(T0 - DAY, T0 + DAY)], [])
    assert problems and st[0]["kind"] == "anomaly"


def test_an_invented_ledger_contact_with_no_reconstructed_stretch_is_recorded_and_the_class_continues():
    """Codex blocker 2, the reviewer's reproduced input: Venus conjunction point:120.0, constant longitude 180 deg, NO reconstructed intervals, a ledger contact
    [2026-02-28, 2026-03-02). Under sink_all the result used to be an invented-contact PROBLEM and ZERO stretch records, then the certification raised."""
    const = lambda body, t: 180.0                                            # noqa: E731
    assert _want(const) == []
    problems, _g, st = _compare(const, [], [(FEB28, MAR2, ACC)], policy=cc.POLICY_SINK_ALL)
    assert problems == [] and [(s["kind"], s["reason"]) for s in st] == [("invented", "ledger_contact_not_reconstructed")]
    assert st[0]["interval"] == [FEB28.isoformat(), MAR2.isoformat()] and st[0]["stretch_ordinal"] == 1 and st[0]["episode_count"] == 1
    (r,) = _records_for(st)
    assert (r["kind"], r["reason"]) == ("invented", "ledger_contact_not_reconstructed") and r["horizon_interval"] == [FEB28.isoformat(), MAR2.isoformat()]
    assert r["full_interval"] is None and r["station_at"] is None and r["stretch_ordinal"] == 1
    assert r["record_id"] == _contract_id("invented", "venus", "conjunction", TARGET, 1.0, LO, HI, 1)
    problems, _g, st = _compare(const, [], [(FEB28, MAR2, ACC)])               # the default policy is unchanged: the same input RAISES
    assert problems and "invented" in problems[0]


def test_an_invented_contacts_ordinal_is_one_plus_the_reconstructed_stretches_that_start_strictly_earlier():
    (iv,) = _want(curve_graze)
    later = (iv[1] + 5 * DAY, iv[1] + 6 * DAY)
    _p, _g, st = _compare(curve_graze, [iv], [(later[0], later[1], ACC)], policy=cc.POLICY_SINK_ALL)
    inv = [s for s in st if s["kind"] == "invented"]
    assert len(inv) == 1 and inv[0]["stretch_ordinal"] == 2, "the one reconstructed stretch starts earlier, so the invented contact ranks second"
    assert [s["kind"] for s in st if s["kind"] != "invented"] == ["near_miss"]


def test_a_ledger_episode_covering_half_a_reconstructed_stretch_is_recorded_not_raised_and_is_not_a_plain_contact():
    """Codex blocker 2: such a stretch used to be classified `contact` and then raised. Now: a boundary_pairing_mismatch on the stretch (detail the two counts) and an
    invented record for the half-interval the ledger holds; nothing raises; no `contact` is counted for it."""
    (iv,) = _want(curve_graze)
    half = (iv[0], iv[0] + (iv[1] - iv[0]) / 2, ACC)
    problems, _g, st = _compare(curve_graze, [iv], [half], policy=cc.POLICY_SINK_ALL)
    assert problems == []
    assert sorted((s["kind"], s["reason"]) for s in st) == [("anomaly", "boundary_pairing_mismatch"), ("invented", "ledger_contact_not_reconstructed")]
    pair = [s for s in st if s["kind"] == "anomaly"][0]
    assert pair["detail"] == {"reconstructed": 1, "ledger_union": 1} and pair["stretch_ordinal"] == 1 and pair["episode_count"] == 1
    assert not [s for s in st if s["kind"] == "contact"]
    recs = _records_for(st)
    assert {(r["kind"], r["reason"]) for r in recs} >= {("anomaly", "boundary_pairing_mismatch"), ("invented", "ledger_contact_not_reconstructed")}
    problems, _g, st = _compare(curve_graze, [iv], [half])                      # the default policy still raises it
    assert problems and [s["kind"] for s in st] == ["contact"]


def test_no_difference_the_two_way_comparison_can_find_escapes_a_record_under_sink_all():
    """The property: under sink_all `problems` is always empty AND every disagreement leaves at least one record that is not a plain contact."""
    (iv,) = _want(curve_graze)
    cases = {"matching": [(iv[0], iv[1], ACC)], "half": [(iv[0], iv[0] + (iv[1] - iv[0]) / 2, ACC)], "shifted": [(iv[0] + 2 * DAY, iv[1] + 2 * DAY, ACC)],
             "extra": [(iv[0], iv[1], ACC), (iv[1] + 3 * DAY, iv[1] + 4 * DAY, ACC)], "none": []}
    for name, have in cases.items():
        problems, _g, st = _compare(curve_graze, [iv], have, policy=cc.POLICY_SINK_ALL)
        assert problems == [], name
        if name == "matching":
            assert [s["kind"] for s in st] == ["contact"]
        else:
            assert any(s["kind"] != "contact" for s in st), name


def test_the_obligation_level_pairing_anomaly_has_the_whole_horizon_and_ordinal_one(monkeypatch):
    """Every stretch and ledger interval agrees with one on the other side, yet the sequences do not pair up (here: the pairing predicate is forced): ONE
    obligation-level anomaly over the inventory horizon."""
    (iv,) = _want(curve)
    monkeypatch.setattr(cc.bm, "intervals_agree", lambda *a, **k: True)
    two = [(iv[0], iv[0] + DAY, ACC), (iv[0] + 3 * DAY, iv[1], ACC)]
    problems, _g, st = _compare(curve, [iv], two, policy=cc.POLICY_SINK_ALL)
    assert problems == []
    (pair,) = [s for s in st if s["kind"] == "anomaly"]
    assert pair["interval"] == [LO.isoformat(), HI.isoformat()] and pair["stretch_ordinal"] == 1 and pair["detail"] == {"reconstructed": 1, "ledger_union": 2}
    recs = _records_for(st)
    assert sorted(r["kind"] for r in recs) == ["anomaly", "multi_episode_stretch"], "the anomaly is the obligation's; the multi-episode record is the real stretch's own"
    (a,) = [r for r in recs if r["kind"] == "anomaly"]
    assert a["horizon_interval"] == [LO.isoformat(), HI.isoformat()] and a["stretch_ordinal"] == 1 and a["station_at"] is None and a["clipped_by_horizon"] == []


def test_environment_faults_still_raise_under_every_policy_before_any_comparison():
    with pytest.raises(cc.cr.GeometryUnavailable, match="no ephemeris position source"):
        cc.certify_contact_geometry(None, chart_id="c", generation="5.0", event_class="marriage", position_at=None, stretch_sink=[], sink_policy=cc.POLICY_SINK_ALL)


def test_sink_all_without_a_stretch_sink_is_refused_nothing_may_be_sunk_without_a_record():
    with pytest.raises(ValueError, match="needs a stretch_sink"):
        cc.compare_contact_sets(curve, "venus", "conjunction", TARGET, [], [], LO, HI, sink_policy=cc.POLICY_SINK_ALL)


def test_without_a_graze_sink_the_default_policy_forgives_nothing_and_counts_the_stretches_while_sink_all_records_them():
    problems, _g, st = _compare(_near, _want(_near), [], graze=False)
    assert problems and [s["kind"] for s in st] == ["unclassified"]          # no validated slice, no classification: the stretch is only counted
    problems, _g, st = _compare(_near, _want(_near), [], policy=cc.POLICY_SINK_ALL, graze=False)
    assert problems == [] and [s["kind"] for s in st] == ["unresolved"]      # the measuring build classifies and records


# ── blocker 4: a station seam needs an overlapping ledger contact and carries station_at and full_interval ─────────────────────────

def test_a_stretch_with_no_ledger_contact_is_never_a_station_seam():
    """Codex blocker 4, the reviewer's reproduced input: longitude 120.3 + 0.02 d^2 (d = days from 2026-03-01), target 120, NO ledger contacts, a station at the minimum.
    The output used to contain a near_miss AND a station_seam with episode_count=0, full_interval=null and no station_at."""
    _p, _g, st = _compare(curve_graze, _want(curve_graze), [], policy=cc.POLICY_SINK_ALL)
    assert st[0]["episode_count"] == 0
    recs = _records_for(st, stations=[T0])
    assert [r["kind"] for r in recs] == ["near_miss"], "the station is inside the stretch but no contact overlaps it: not a seam"


def test_a_stretch_a_ledger_contact_overlaps_with_a_station_inside_is_a_seam_with_station_at_and_full_interval():
    (iv,) = _want(curve)
    _p, _g, st = _compare(curve, [iv], [(iv[0], iv[1], ACC)], policy=cc.POLICY_SINK_ALL)
    (seam,) = [r for r in _records_for(st, stations=[T0]) if r["kind"] == "station_seam"]
    assert seam["reason"] == "arc_index_station_inside" and seam["station_at"] == T0.isoformat() and seam["full_interval"] == [iv[0].isoformat(), iv[1].isoformat()]
    assert seam["episode_count"] == 1 and seam["horizon_interval"] == [iv[0].isoformat(), iv[1].isoformat()] and seam["stretch_ordinal"] == 1
    assert _records_for(st, stations=[T0 + 200 * DAY]) == [], "a station outside the stretch is no seam"
    two = sorted(_records_for(st, stations=[T0 + DAY, T0 - DAY]), key=lambda r: r["kind"])
    assert [r["station_at"] for r in two] == [(T0 - DAY).isoformat()], "with several stations the earliest is `station_at`"


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
