"""A5.3 — AM-20 (ND-P1-FRAME): the P1 `dasha_lord` house DESCRIPTOR (steward M20261002T…, Stream B's
`design/P1_FRAME_ANSWER_v1_0.md`).

`house_from_frame` of a P1 transit record is the inclusive whole-sign count from the NATAL sign of the period
lord that anchors the record — resolved through Stream B's `frames` (called, not copied). It is a stored
DESCRIPTOR only: no predicate, factor, admission or channel reads it. The natal relation to H stays AM-15's
lagna count, and P1 records stay unscored (`value_mapping_undeclared`).
"""
from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path

import pytest

from pipeline.orchestrator.writers import ka_gochara_v5 as writer_mod
from services.gochara_kernel import evaluator as ev
from services.gochara_kernel import window_sweep as ws
from services.gochara_kernel.record_verifier import expected_p1_anchor, verify_p1_house_descriptor
from services.gochara_rules import frames as rules_frames

from .test_a53_inventory import CHART, CHART_ID
from .test_a53_p1_support import GEN, _t, world  # noqa: F401  (fresh AM-5 database + P1 world)

SIDECAR = Path(__file__).resolve().parents[3]
CONTEXT = {"lagna_deg": CHART["lagna_deg"], "natal": CHART["natal"]}
SIGNS = rules_frames.SIGNS


def _p1_transit_edges():
    return [e for e in ev.enumerate_edges("marriage", "P1", CHART) if e.transit]


def _natal_idx(graha: str) -> int:
    return int(CHART["natal"][graha.title()] // 30)


# ── the enumerator carries the anchoring period lord ─────────────────────────────────────────────────

def test_every_p1_transit_edge_names_its_anchoring_period_lord_and_no_other_edge_does():
    edges = ev.enumerate_edges("marriage", "P1", CHART)
    transit = [e for e in edges if e.transit]
    assert transit and all(e.period_lord for e in transit)
    assert all(e.period_lord is None for e in edges if not e.transit)
    for path in ("P2", "P3", "P4", "P5"):
        assert all(e.period_lord is None for e in ev.enumerate_edges("marriage", path, CHART))
    # the DB's `dasha_lord` frame has NO arg (ka_gochara_frame_ok): the anchor never rides the frame
    assert all((e.frame_kind, e.frame_arg) == ("dasha_lord", None) for e in edges)


def test_the_anchor_is_the_agent_for_its_own_signs_and_the_exaltation_owner_for_the_sun_jupiter_forms():
    by = {(e.agent, int(e.obj.canonical_target.split(":")[1])): e.period_lord for e in _p1_transit_edges()}
    assert by[("sun", 10)] == "mars"            # Capricorn = Mars's exaltation sign; the Sun transits it (XX.38)
    assert by[("jupiter", 1)] == "sun"          # Aries = the Sun's exaltation sign
    assert by[("jupiter", 7)] == "saturn"       # Libra = Saturn's exaltation sign
    assert by[("saturn", 10)] == "saturn"       # Saturn's own sign (XX.37)
    assert by[("venus", 7)] == "venus"
    assert by[("sun", 7)] == "sun"              # both readings apply (Sun's debilitation / Saturn's exaltation)
    # ... and the enumerator agrees with the VERIFIER's own table for every edge it emits
    for (agent, sign), lord in by.items():
        assert lord == expected_p1_anchor(agent, sign - 1), (agent, sign)


def test_the_period_lord_is_not_a_natural_key_field_so_record_identity_is_unchanged():
    e = _p1_transit_edges()[0]
    kw = dict(chart_id="c", generation="5.0", contact_id="x", prerequisites=[], source_text=e.source_text)
    assert e.natural_key(**kw) == replace(e, period_lord="saturn").natural_key(**kw)
    assert "period_lord" not in ev.NATURAL_KEY_FIELDS


# ── the resolver ─────────────────────────────────────────────────────────────────────────────────────

def test_the_dasha_lord_house_is_the_inclusive_count_from_the_period_lords_natal_sign():
    house_for = writer_mod._house_resolver(CONTEXT)
    seen = 0
    for e in _p1_transit_edges():
        sign_no = int(e.obj.canonical_target.split(":")[1])
        want = (sign_no - 1 - _natal_idx(e.period_lord)) % 12 + 1          # independent arithmetic
        assert house_for(e, SIGNS[sign_no - 1].lower()) == want, (e.agent, sign_no, e.period_lord)
        seen += 1
    assert seen == 31
    sun_in_capricorn = next(e for e in _p1_transit_edges()
                            if e.agent == "sun" and e.obj.canonical_target == "span:10")
    # the Sun transits Capricorn; the anchor is MARS (bhukti lord), natal Mars in Libra ⇒ the 4th from it
    assert house_for(sun_in_capricorn, "capricorn") == 4
    # the resolver is Stream B's `frames` (called, not copied)
    assert house_for(sun_in_capricorn, "capricorn") == rules_frames.house_of(
        9 * 30.0 + 15.0, rules_frames.Frame("dasha_lord", "Mars"), CONTEXT)


def test_an_edge_with_no_anchor_or_an_anchor_without_a_natal_position_is_not_minted():
    house_for = writer_mod._house_resolver(CONTEXT)
    e = _p1_transit_edges()[0]
    assert house_for(replace(e, period_lord=None), "libra") is None
    assert house_for(replace(e, period_lord="pluto"), "libra") is None


def test_the_other_frames_are_unchanged_the_natal_relation_stays_am15_lagna():
    house_for = writer_mod._house_resolver(CONTEXT)
    lagna_idx = int(CHART["lagna_deg"] // 30)
    p3 = next(e for e in ev.enumerate_edges("marriage", "P3", CHART) if e.transit)
    assert (p3.frame_kind, house_for(p3, "libra")) == ("lagna", (6 - lagna_idx) % 12 + 1)
    moon = next(e for e in ev.enumerate_edges("marriage", "P2", CHART) if e.transit)
    assert (moon.frame_kind, house_for(moon, "libra")) == ("moon", (6 - _natal_idx("moon")) % 12 + 1)


# ── nothing reads the descriptor ─────────────────────────────────────────────────────────────────────

def test_no_rule_module_and_no_p1_code_path_mentions_the_descriptor():
    rules = [p for p in (SIDECAR / "services" / "gochara_rules").glob("*.py")
             if "house_from_frame" in p.read_text()]
    assert rules == [], f"rule modules must not read the descriptor: {rules}"
    allowed = {"record_store.py", "window_store.py", "window_verifier.py", "window_sweep.py",
               "record_verifier.py"}
    users = {p.name for p in (SIDECAR / "services" / "gochara_kernel").glob("*.py")
             if "house_from_frame" in p.read_text()}
    assert users <= allowed, users - allowed
    # in the sweep the descriptor feeds exactly one thing: P2's Moon-frame direction (never P1)
    lines = [ln.strip() for ln in (SIDECAR / "services/gochara_kernel/window_sweep.py").read_text().splitlines()
             if "rec.house_from_frame" in ln]
    assert lines == ["return channel_for(p2_direction(rec.agent, rec.house_from_frame), event_class)"]


def _sweep_rec(house):
    from datetime import datetime, timezone
    d = lambda day: datetime(2025, 1, 1, tzinfo=timezone.utc).replace(day=day)       # noqa: E731
    return ws.SweepRecord(
        record_id="p1", root_id="r", path_id="P1", rule_version="1.0.0", relation="residence",
        object_kind="house_span", agent="venus", operator_role="scored", admission_state="admitted",
        supports=((d(2), d(20)),), canonical_target="span:7", house_from_frame=house,
        longitude_at=lambda t: 190.0)


def test_a_p1_window_does_not_depend_on_the_descriptor_at_all():
    rows = lambda p, v: ws.registry_factor_rows("P1", "1.0.0")                       # noqa: E731
    outs = []
    for house in range(1, 13):
        drafts, excluded = ws.draft_windows("marriage", [_sweep_rec(house)], rows)
        outs.append((drafts, excluded))
    assert all(o == outs[0] for o in outs[1:])
    (w,), _ = outs[0]
    assert w.score is None and w.severity is None                    # P1 stays unscored (value mapping undeclared)
    assert "value_mapping_undeclared" in str(w.unresolved)


def _dump(conn):
    """Everything a record stores EXCEPT the descriptor itself."""
    recs = conn.execute(
        "SELECT record_id::text, admission_state, temporal_support_state, temporal_support_intervals::text,"
        " evidence_for_occurrence, evidence_against_occurrence, outcome_valence_for_native, severity,"
        " frame_kind, frame_arg FROM public.ka_gochara_relationship_record WHERE path_id = 'P1'"
        " ORDER BY record_id").fetchall()
    pre = conn.execute(
        "SELECT p.record_id::text, p.ordinal, p.predicate_id, p.predicate_rule_version, p.result"
        " FROM public.ka_gochara_record_prerequisite p JOIN public.ka_gochara_relationship_record r"
        " ON r.record_id = p.record_id WHERE r.path_id = 'P1' ORDER BY 1, 2").fetchall()
    return recs, pre


def _houses(conn):
    return [r[0] for r in conn.execute(
        "SELECT house_from_frame FROM public.ka_gochara_relationship_record WHERE path_id = 'P1'"
        " ORDER BY record_id").fetchall()]


def _venus_libra(w):
    w.set_periods([(2, _t(1, 1), _t(2, 1))])
    w.boot()
    w.seed("venus", [(180.0, _t(1, 10)), (210.0, _t(2, 20))])


def test_changing_the_descriptor_changes_nothing_else_a_record_stores_or_admits(world):
    w = world
    _venus_libra(w)
    real = writer_mod._house_resolver(CONTEXT)
    w.grain("venus", lambda t: _t(1, 10) <= t < _t(2, 20), house_for=real)
    base, base_houses = _dump(w.conn), _houses(w.conn)
    assert base_houses == [11]                                        # Venus in Libra, from natal Venus (Sagittarius)
    for shift in (1, 5, 11):
        w.grain("venus", lambda t: _t(1, 10) <= t < _t(2, 20),
                house_for=lambda e, s, _s=shift: (real(e, s) + _s - 1) % 12 + 1)
        assert _houses(w.conn) != base_houses                         # the descriptor DID change ...
        assert _dump(w.conn) == base                                  # ... and nothing else did
    assert all(r[4] is None and r[5] is None and r[7] is None for r in base[0])   # unscored: NULL, never 0.0
    assert {r[8:10] for r in base[0]} == {("dasha_lord", None)}


# ── the independent verifier ─────────────────────────────────────────────────────────────────────────

def _facts_for_snapshot(w):
    """The AM-5 world's snapshot binds stub L1 facts; the verifier reads the natal positions from them."""
    return w.conn.execute(
        "SELECT fact_subject, fact_value_num FROM public.chart_facts WHERE fact_subject IN ('VEN','LAGNA')"
    ).fetchall()


def test_the_verifier_rederives_the_descriptor_from_its_own_table_and_catches_a_wrong_one(world):
    w = world
    _venus_libra(w)
    w.grain("venus", lambda t: _t(1, 10) <= t < _t(2, 20), house_for=writer_mod._house_resolver(CONTEXT))
    natal = dict(_facts_for_snapshot(w))
    assert int(float(natal["VEN"]) // 30) == _natal_idx("venus")      # the stub L1 facts ARE the fixture chart
    assert verify_p1_house_descriptor(w.conn, chart_id=CHART_ID, generation=GEN,
                                      event_class="marriage") == {"records": 1}
    # a descriptor counted from the LAGNA (the rejected option (a)) is caught
    lagna = int(CHART["lagna_deg"] // 30)
    w.grain("venus", lambda t: _t(1, 10) <= t < _t(2, 20),
            house_for=lambda e, s: (SIGNS.index(s.title()) - lagna) % 12 + 1)
    with pytest.raises(RuntimeError, match="house-descriptor verification failed"):
        verify_p1_house_descriptor(w.conn, chart_id=CHART_ID, generation=GEN, event_class="marriage")


def test_the_writer_substep_mints_p1_transit_records_with_the_descriptor_and_verifies_it(world):
    w = world
    _venus_libra(w)
    res = w.step("record:marriage:P1")
    assert res.rows_inserted > 0, res.notes
    houses = _houses(w.conn)
    assert houses and all(1 <= h <= 12 for h in houses)
    verify_p1_house_descriptor(w.conn, chart_id=CHART_ID, generation=GEN, event_class="marriage")
