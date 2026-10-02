"""A5.3 — AM-21 + part 2 (Codex round 8, R8-3): the P1 record's period ANCHOR.

A P1 transit record is licensed by the running periods of ONE lord at ONE level — its anchor — and that lord is NOT
always the transiting agent (Phaladīpikā XX.38: the Sun entering another graha's exaltation sign delivers the BHUKTI
lord's fruit). One physical contact can therefore be several records (role aliases sharing one `contact_id`):
the Sun in Libra is the Sun's own debilitation sign (anchor Sun) AND Saturn's exaltation sign (anchor Saturn at AD).

Oracle O-PP-5 (Stream B's literal): the Sun in Libra over a span that overlaps both a Saturn AD and a Sun AD gives TWO
records with one contact_id, anchors (Sun, AD) and (Saturn, AD), supports = span ∩ D(Sun, AD) and span ∩ D(Saturn, AD).
Everything runs on the real applied schema (… + 1233) with the L1 tables stubbed.
"""
from __future__ import annotations

import uuid

import pytest

from services.gochara_kernel import evaluator as ev
from services.gochara_kernel import record_verifier as rv
from services.gochara_kernel.dasha_read import LEVEL_N, make_period_rows_for

from .test_a53_inventory import CHART, CHART_ID
from .test_a53_p1_support import GEN, _supports, _t, world  # noqa: F401

SUN_AD = ("sun", "ad")
SAT_AD = ("saturn", "ad")


def _records(conn):
    return conn.execute(
        "SELECT r.record_id::text, r.agent, r.period_anchor_lord, r.period_anchor_level, r.contact_id::text,"
        " r.temporal_support_intervals FROM public.ka_gochara_relationship_record r"
        " WHERE r.path_id = 'P1' ORDER BY r.period_anchor_lord, r.period_anchor_level").fetchall()


def _sun_in_libra(w):
    """Sun AD [01-01, 01-20), Saturn AD [01-20, 02-05); the Sun is in Libra [01-10, 02-20)."""
    w.set_lord_periods([("sun", 2, _t(1, 1), _t(1, 20)), ("saturn", 2, _t(1, 20), _t(2, 5))])
    w.boot()
    w.seed("sun", [(180.0, _t(1, 10)), (210.0, _t(2, 20))])
    span = lambda t: _t(1, 10) <= t < _t(2, 20)                              # noqa: E731
    w.grain("sun", span, anchors=[SUN_AD, SAT_AD])               # one grain, both readings of the one contact


# ── enumeration ──────────────────────────────────────────────────────────────────────────────────────

def test_the_sun_in_libra_is_two_readings_with_two_anchors():
    anchors = sorted((e.period_anchor_lord, e.period_anchor_level)
                     for e in ev.enumerate_edges("marriage", "P1", CHART)
                     if e.transit and e.agent == "sun" and e.relation == "residence"
                     and e.obj.canonical_target == "span:7")
    assert anchors == [("saturn", "ad"), ("sun", "ad"), ("sun", "md"), ("sun", "pd")]


def test_only_p1_transit_edges_carry_an_anchor_and_the_natural_key_includes_it():
    edges = ev.enumerate_edges("marriage", "P1", CHART)
    transit = [e for e in edges if e.transit]
    assert transit and all(e.period_anchor_lord and e.period_anchor_level in ("md", "ad", "pd") for e in transit)
    assert all(e.period_anchor_lord is None for e in edges if not e.transit)
    for path in ("P2", "P3", "P4"):
        assert all(e.period_anchor_lord is None for e in ev.enumerate_edges("marriage", path, CHART))
    keys = {e.natural_key for e in transit}
    assert len(keys) == len(transit)                                  # the anchor makes every reading distinct


# ── O-PP-5 ───────────────────────────────────────────────────────────────────────────────────────────

def test_o_pp_5_two_records_one_contact_two_anchors_two_supports(world):
    w = world
    _sun_in_libra(w)
    rows = _records(w.conn)
    assert [(r[2], r[3]) for r in rows] == [SAT_AD, SUN_AD]
    assert len({r[0] for r in rows}) == 2                             # two records ...
    assert len({r[4] for r in rows}) == 1 and rows[0][4] is not None  # ... ONE physical contact (role aliases)
    got = {(r[2], r[3]): [(x.lower, x.upper) for x in r[5]] for r in rows}
    assert got[SUN_AD] == [(_t(1, 10), _t(1, 20))]                    # span ∩ D(Sun, AD)
    assert got[SAT_AD] == [(_t(1, 20), _t(2, 5))]                     # span ∩ D(Saturn, AD)
    assert rv.verify_p1_support(w.conn, chart_id=CHART_ID, generation=GEN, event_class="marriage") == {
        "records": 2, "restricted": 2}


def test_the_role_aliases_are_counted_as_one_contact_not_two(world):
    w = world
    _sun_in_libra(w)
    assert w.conn.execute("SELECT count(DISTINCT contact_id) FROM public.ka_gochara_relationship_record"
                          " WHERE path_id = 'P1'").fetchone()[0] == 1


def test_mutation_one_record_anchored_on_the_agent_only_fails_the_anchor_verifier(world):
    """Only the Sun's own reading is stored: the contact is also Saturn's exaltation sign, so the verifier's own
    derivation expects the (Saturn, AD) reading too."""
    w = world
    w.set_lord_periods([("sun", 2, _t(1, 1), _t(1, 20)), ("saturn", 2, _t(1, 20), _t(2, 5))])
    w.boot()
    w.seed("sun", [(180.0, _t(1, 10)), (210.0, _t(2, 20))])
    w.grain("sun", lambda t: _t(1, 10) <= t < _t(2, 20), anchor=SUN_AD)
    with pytest.raises(RuntimeError, match="P1 anchor verification failed"):
        rv.verify_p1_anchors(w.conn, chart_id=CHART_ID, generation=GEN, event_class="marriage")


def test_the_anchor_verifier_accepts_the_full_set_and_refuses_an_invented_anchor(world):
    w = world
    w.set_lord_periods([("sun", 2, _t(1, 1), _t(1, 20)), ("saturn", 2, _t(1, 20), _t(2, 5))])
    w.boot()
    w.seed("sun", [(180.0, _t(1, 10)), (210.0, _t(2, 20))])
    span = lambda t: _t(1, 10) <= t < _t(2, 20)                              # noqa: E731
    w.grain("sun", span, anchors=[SUN_AD, SAT_AD, ("sun", "md"), ("sun", "pd")])
    assert rv.verify_p1_anchors(w.conn, chart_id=CHART_ID, generation=GEN, event_class="marriage") == {
        "contacts": 1}
    # a wrong level on an existing reading: Saturn's XX.38 reading is an AD reading, never MD
    w.conn.execute("UPDATE public.ka_gochara_relationship_record SET period_anchor_level = 'md'"
                   " WHERE period_anchor_lord = 'saturn'")
    with pytest.raises(RuntimeError, match="P1 anchor verification failed"):
        rv.verify_p1_anchors(w.conn, chart_id=CHART_ID, generation=GEN, event_class="marriage")


def test_mutation_domain_taken_from_the_agents_periods_for_the_xx38_reading_fails_the_support_verifier(world):
    """The (Saturn, AD) record's support is rewritten to what the AGENT's (Sun's) AD would give: the verifier
    derives D(Saturn, AD) from the stored anchor, so it refuses."""
    w = world
    _sun_in_libra(w)
    w.conn.execute("UPDATE public.ka_gochara_relationship_record SET temporal_support_intervals ="
                   " ARRAY[tstzrange(%s, %s, '[)')]"
                   " WHERE period_anchor_lord = 'saturn'", (_t(1, 10), _t(1, 20)))
    with pytest.raises(RuntimeError, match="P1 support verification failed"):
        rv.verify_p1_support(w.conn, chart_id=CHART_ID, generation=GEN, event_class="marriage")


def test_o_pp_4_an_anchor_with_no_running_rows_is_unrestricted_and_unknown(world):
    """(a) the anchor lord has no periods at that level in the pinned rows ⇒ unknown, the contact span unrestricted
    (an unknown prerequisite is NOT admitted as running, and not invented either)."""
    w = world
    w.set_lord_periods([("sun", 2, _t(1, 1), _t(1, 20))])              # no Saturn rows at all
    w.boot()
    w.seed("sun", [(180.0, _t(1, 10)), (210.0, _t(2, 20))])
    w.grain("sun", lambda t: _t(1, 10) <= t < _t(2, 20), anchor=SAT_AD)
    (row,) = _records(w.conn)
    assert [(x.lower, x.upper) for x in row[5]] == [(_t(1, 10), _t(2, 20))]
    res = w.conn.execute("SELECT p.result FROM public.ka_gochara_record_prerequisite p WHERE p.predicate_id ="
                         " 'period_running_at'").fetchall()
    assert [r[0] for r in res] == ["unknown"]


def test_o_pp_4_disjoint_pieces_are_kept_and_never_bridged(world):
    """(b) two Sun ADs with a gap inside the contact: two pieces, the gap excluded."""
    w = world
    w.set_lord_periods([("sun", 2, _t(1, 1), _t(1, 15)), ("sun", 2, _t(1, 25), _t(2, 5))])
    w.boot()
    w.seed("sun", [(180.0, _t(1, 10)), (210.0, _t(2, 20))])
    w.grain("sun", lambda t: _t(1, 10) <= t < _t(2, 20), anchor=SUN_AD)
    assert _supports(w.conn) == [[(_t(1, 10), _t(1, 15)), (_t(1, 25), _t(2, 5))]]
    rv.verify_p1_support(w.conn, chart_id=CHART_ID, generation=GEN, event_class="marriage")


def test_o_pp_4_the_level_is_part_of_the_domain(world):
    """(c) a Sun PD is not a Sun AD: the (Sun, AD) reading ignores it, the (Sun, PD) reading uses it."""
    w = world
    w.set_lord_periods([("sun", 2, _t(1, 1), _t(1, 15)), ("sun", 3, _t(1, 28), _t(2, 2))])
    w.boot()
    w.seed("sun", [(180.0, _t(1, 10)), (210.0, _t(2, 20))])
    span = lambda t: _t(1, 10) <= t < _t(2, 20)                              # noqa: E731
    w.grain("sun", span, anchors=[SUN_AD, ("sun", "pd")])
    got = {(r[2], r[3]): [(x.lower, x.upper) for x in r[5]] for r in _records(w.conn)}
    assert got[SUN_AD] == [(_t(1, 10), _t(1, 15))]
    assert got[("sun", "pd")] == [(_t(1, 28), _t(2, 2))]
    rv.verify_p1_support(w.conn, chart_id=CHART_ID, generation=GEN, event_class="marriage")


def test_o_pp_4_an_instant_judged_prerequisite_is_not_a_domain(world):
    """(d) the support is a half-open INTERVAL domain: a period that only touches the contact at its endpoint
    contributes nothing (a running period ending exactly at the ingress is not running during it)."""
    w = world
    w.set_lord_periods([("sun", 2, _t(1, 1), _t(1, 10))])             # ends exactly when the contact starts
    w.boot()
    w.seed("sun", [(180.0, _t(1, 10)), (210.0, _t(2, 20))])
    w.grain("sun", lambda t: _t(1, 10) <= t < _t(2, 20), anchor=SUN_AD)
    (row,) = _records(w.conn)
    assert list(row[5]) == []
    res = w.conn.execute("SELECT p.result FROM public.ka_gochara_record_prerequisite p WHERE p.predicate_id ="
                         " 'period_running_at'").fetchall()
    assert [r[0] for r in res] == ["false"]


# ── level-aware reads + 1233 ─────────────────────────────────────────────────────────────────────────

def test_rows_for_filters_by_level(world):
    w = world
    w.set_lord_periods([("sun", 2, _t(1, 1), _t(1, 20)), ("sun", 3, _t(1, 5), _t(1, 8))])
    w.boot()
    rows_for, _ = make_period_rows_for(w.conn, CHART_ID)
    span = lambda lvl: [(r["start_iso"], r["end_iso"]) for r in rows_for("sun", lvl)]   # noqa: E731
    assert span("ad") == [(_t(1, 1), _t(1, 20))] and span("pd") == [(_t(1, 5), _t(1, 8))]
    assert LEVEL_N == {"md": 1, "ad": 2, "pd": 3}
    assert len(span(None)) == len(span("md")) + 2                    # the legacy union: every level


def test_1233_checks_hold_on_the_real_schema(world):
    """Pair / vocabulary / set-exactly-for-P1 — the migration's own CHECKs (bounded, not doctrine)."""
    import psycopg
    w = world
    _sun_in_libra(w)
    for sql in ("UPDATE public.ka_gochara_relationship_record SET period_anchor_level = NULL",
                "UPDATE public.ka_gochara_relationship_record SET period_anchor_lord = 'Sun'",
                "UPDATE public.ka_gochara_relationship_record SET period_anchor_level = 'xd'"):
        with pytest.raises(psycopg.errors.CheckViolation):
            w.conn.execute(sql)
