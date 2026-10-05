"""ND-H-20261005 / ND-P2-20261005 builder rows against the REAL schema (throwaway local database).

"No migration needed" is shown here by a RUN, not by reading: the bound catalogue — including every row at
rule_version 1.2.0 — is seeded by `RuleRegistryStore.seed()` into a fresh database carrying migrations 1154/1155
verbatim, and records of each new shape (CORE span, DVI span in P4, K-B `karaka` degree point in P3 and P4) are
written through the real record store, so every CHECK, FK and trigger of 1154/1155 has its say.

It also proves ADMISSION at materialisation for the eight classes: `record_store.materialise_record_grain` now reads H,
the K-B targets and P1's relation kinds under the GRAIN'S rule_version (record_store.py: the `period_lord_relation` call
in `_p1_relation`, and `_p3_contact_house_or_lord`), so a 1.2.0 P1 and P3 record of an ND-H class is admitted while a
1.0.0 grain behaves exactly as before.

What the schema still REFUSES: a SUPPORT row — `kgrr_object_role_ck`
(migrations/1155_gochara_relationship_record.sql:537-539) has no role for a house outside H.

NOT_RUN (skip) when the disposable server is unreachable; a failure under GOCHARA_A53_REQUIRE_DB=1.
"""
from __future__ import annotations

import pytest

from services.gochara_kernel import evaluator as ev
from services.gochara_kernel import input_vector as iv
from services.gochara_kernel import record_store as rs
from services.gochara_kernel import rule_registry as rr
from services.gochara_rules import registry as reg

from .test_a53_record_store import (  # noqa: F401  (`_pg_dsn` / `pg` are the fixtures)
    CHART_ID, HORIZON, _house_from_lagna, _pg_dsn, _probe, _seed_libra_crossings, _sky_convention_id, pg,
)

V = "1.2.0"
ND_H, ND_P2 = "ND-H-20261005", "ND-P2-20261005"
NATAL = {"Sun": 291.96, "Moon": 327.06, "Mars": 198.52, "Mercury": 270.84, "Jupiter": 148.87, "Venus": 265.39,
         "Saturn": 356.74, "Rahu": 21.34, "Ketu": 201.34}
#: the fixture crossings put a body in LIBRA [day 10, day 200). Libra is the 7th from an Aries lagna (business_launch
#: CORE) and the 11th from a Sagittarius lagna (achievement_recognition DVI).
CHART_ARIES = {"lagna_deg": 12.43, "natal": dict(NATAL)}
CHART_SAGITTARIUS = {"lagna_deg": 245.0, "natal": dict(NATAL)}
CHART_TAURUS = {"lagna_deg": 45.0, "natal": dict(NATAL)}          # Libra is the 6th: business_launch SUPPORT
LIBRA = "span:7"
#: K-B point records need a REAL solved contact (kgc_exact_precision_ck refuses an unrefined synthetic bracket), so the
#: natal luminary of the test chart is put where Saturn really is in the horizon: it crosses 340° sidereal in early 2026.
KB_LAM = 340.0
CHART_KB = {"lagna_deg": 12.43, "natal": {**NATAL, "Sun": KB_LAM, "Moon": KB_LAM}}


def _seeded(conn):
    return rr.RuleRegistryStore(conn).seed()


def _rows(conn, sql, params=()):
    return conn.execute(sql, params).fetchall()


# ── 1. the registry rows at 1.2.0 pass every constraint of migration 1154 ────────────────────────────────

def test_the_whole_bound_catalogue_seeds_and_every_1_2_0_row_is_stored_as_declared(pg):
    counts = _seeded(pg)
    assert counts["paths"] == len(rr.BOUND_PATH_REFS) == 8 and counts["seals"] == 8
    assert counts["factors"] == len(rr.BOUND_FACTOR_REFS)
    stored = {(p, v): (prov, role, ruling, score) for p, v, prov, role, ruling, score in _rows(
        pg, "SELECT path_id, rule_version, provenance, operator_role, ruling_ref, score_rule"
            " FROM public.ka_gochara_rule_path")}
    digest = reg.h_table_sha256(V)
    for pid in ("P1", "P3", "P4"):
        prov, role, ruling, score = stored[(pid, V)]
        assert (prov, role, ruling) == ("uncited_extension", "scored", ND_H)
        assert f"sha256:{digest}" in score                       # H pinned in a column the registry digest covers
    assert {k for k in stored if k[1] == V} == {("P1", V), ("P3", V), ("P4", V)}
    assert sorted(_rows(pg, "SELECT path_id FROM public.ka_gochara_rule_path_seal WHERE rule_version = %s", (V,))) == [
        ("P1",), ("P3",), ("P4",)]
    # the K-A factor row and its membership on the three 1.2.0 paths only
    (factor,) = _rows(pg, "SELECT function, null_state, direction, calibration_status, doctrine_ordering,"
                          " range_lower, range_upper, units FROM public.ka_gochara_factor"
                          " WHERE factor_id = 'karaka_agent' AND rule_version = %s", (V,))
    assert factor == ("categorical_ordered", "omit", "higher_stronger", "uncalibrated_default",
                      ["non_karaka", "karaka"], 0.0, 1.0, "unitless")
    assert sorted(_rows(pg, "SELECT path_id, rule_version FROM public.ka_gochara_rule_path_soft_factor"
                            " WHERE factor_id = 'karaka_agent'")) == [("P1", V), ("P3", V), ("P4", V)]
    # idempotent: a second seed reuses every row, nothing diverges
    again = _seeded(pg)
    assert again["paths"] == again["factors"] == again["seals"] == again["soft_factors"] == 0 and again["reused"] > 0


def test_the_p4_role_inventory_carries_karaka_at_1_2_0_only_and_the_sealed_1_0_0_row_is_untouched(pg):
    """The outside review's point: `_PATH_ROLES["P4"]` (rule_registry.py) has no `karaka` role. True for the 1.0.0 row —
    and the 1.2.0 row declares its own inventory (`_PATH_ROLES_AT`), stored and accepted by `ka_gochara_object_selector_ok`."""
    _seeded(pg)
    roles = {v: {s["object_role"] for s in sel} for v, sel in _rows(
        pg, "SELECT rule_version, object_selector FROM public.ka_gochara_rule_path WHERE path_id = 'P4'")}
    assert roles == {"1.0.0": {"signature_house", "lord"}, V: {"signature_house", "lord", "karaka"}}
    assert rr._PATH_ROLES["P4"] == ("signature_house", "lord")
    p3 = {v: {s["object_role"] for s in sel} for v, sel in _rows(
        pg, "SELECT rule_version, object_selector FROM public.ka_gochara_rule_path WHERE path_id = 'P3'")}
    assert "karaka" in p3["1.0.0"] and "karaka" in p3[V]


def test_the_registry_digest_covers_the_1_2_0_rows_and_moves_with_the_bound_set(pg):
    _seeded(pg)
    refs = list(rr.bound_path_refs())
    payload = iv.registry_payload(pg, refs)
    assert [list(r) for r in sorted(refs)] == sorted(payload["census"])
    assert {(p["path_id"], p["rule_version"]) for p in payload["paths"]} == set(refs)
    assert ("karaka_agent", V) in {(f["factor_id"], f["rule_version"]) for f in payload["factors"]}
    without = [r for r in refs if r[1] != V]
    assert iv.registry_digest_of(payload) != iv.registry_digest_of(iv.registry_payload(pg, without, census_override=[list(r) for r in without]))


# ── 2. records of the new shapes pass every constraint of migration 1155 ─────────────────────────────────

def _coverage_and_grain(conn, *, event_class, path_id, chart, edges, generation, bodies=("Saturn", "Jupiter"), **grain_kw):
    _seeded(conn)
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        sky_cid = _sky_convention_id(conn)
        for body in bodies:
            _seed_libra_crossings(conn, sky_cid, body)
    store = rs.RecordStore(conn)
    kala_cid = store.ensure_kala_convention()
    probe = _probe([(10, 200)])
    class_edges = [e for pid in ("P1", "P2", "P3", "P4")
                   for e in ev.enumerate_edges(event_class, pid, chart, rule_version=rr.selected_path_version(event_class, pid))]
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        rs.write_class_coverage(
            store, chart_id=CHART_ID, generation=generation, event_class=event_class, class_edges=class_edges,
            horizon=HORIZON, position_at=probe, sky_convention_id=sky_cid, kala_convention_id=kala_cid,
            build_id="test-build-ndh", arc_index_available=bool(grain_kw.get("arc_index_for")))
    with conn.transaction():
        conn.execute("SELECT public.ka_gochara_lock_chart(%s::uuid)", (CHART_ID,))
        counts = rs.materialise_record_grain(
            store, chart_id=CHART_ID, generation=generation, event_class=event_class, path_id=path_id, edges=edges,
            horizon=HORIZON, position_at=probe, house_for=_house_from_lagna(chart["lagna_deg"]),
            sky_convention_id=sky_cid, source_fact_ids=["fact-1"], chart=chart, **grain_kw)
    rows = conn.execute(
        "SELECT r.agent, r.relation, r.object_role, r.object_kind, r.rule_version, r.provenance, r.operator_role,"
        " r.ruling_ref, r.admission_state, p.predicate_id, p.result"
        " FROM public.ka_gochara_relationship_record r"
        " LEFT JOIN public.ka_gochara_record_prerequisite p USING (record_id)"
        " WHERE r.generation = %s AND r.event_class = %s AND r.path_id = %s ORDER BY r.agent, r.relation",
        (generation, event_class, path_id)).fetchall()
    return counts, rows


def _span_edges(event_class, path_id, chart, agents):
    out = [e for e in ev.enumerate_edges(event_class, path_id, chart, rule_version=V)
           if e.transit and e.relation == "residence" and e.agent in agents and e.obj.canonical_target == LIBRA]
    assert len(out) == len(agents), out
    return out


def _core_p3_run(conn, generation):
    (edge,) = _span_edges("business_launch", "P3", CHART_ARIES, ("saturn",))
    assert (edge.tier, edge.provenance, edge.ruling_ref) == ("core", "uncited_extension", ND_H)
    return _coverage_and_grain(conn, event_class="business_launch", path_id="P3", chart=CHART_ARIES, edges=[edge],
                               generation=generation, bodies=("Saturn",))


def test_a_core_p3_record_of_an_nd_h_class_is_accepted_by_the_1155_constraints(pg):
    counts, rows = _core_p3_run(pg, "5.3")
    assert counts["records"] == 1 and counts["contacts"] == 1
    (row,) = rows
    assert row[:8] == ("saturn", "residence", "signature_house", "house_span", V, "uncited_extension", "scored", ND_H)
    assert row[9] == "p3_contact_house_or_lord"                  # the 1.2.0 path's declared prerequisite was written


def test_a_core_p3_record_of_an_nd_h_class_is_admitted_at_materialisation(pg):
    """The review's P1-1: at the DEFAULT H version this prerequisite was `unknown` and the record never admitted."""
    counts, rows = _core_p3_run(pg, "5.4")
    assert counts["p3_enumeration_defects"] == 0
    assert [(r[8], r[9], r[10]) for r in rows] == [("admitted", "p3_contact_house_or_lord", "true")]


def _p1_run(conn, *, event_class, agent, chart, generation, dasha_rows):
    """ONE committed P1 grain at the class's selected version: `agent` through Libra under its OWN antardaśā."""
    version = rr.selected_path_version(event_class, "P1")
    (edge,) = [e for e in ev.enumerate_edges(event_class, "P1", chart, rule_version=version)
               if e.transit and e.relation == "residence" and e.agent == agent and e.obj.canonical_target == LIBRA
               and (e.period_anchor_lord, e.period_anchor_level) == (agent, "ad")]
    counts, rows = _coverage_and_grain(
        conn, event_class=event_class, path_id="P1", chart=chart, edges=[edge], generation=generation,
        bodies=(agent.title(),), dasha_rows_for=lambda a, level=None: dasha_rows.get(a, []))
    return edge, counts, {r[9]: r[10] for r in rows}, {r[8] for r in rows}


def _running(agent):
    from .test_a53_record_store import DAY, T0
    return {agent: [{"start_iso": T0, "end_iso": T0 + 300 * DAY}]}


def test_a_p1_record_of_an_nd_h_class_is_admitted_through_a_cited_relation_kind(pg):
    """business_launch, Aries lagna: Libra is the 7th (CORE) and Venus OWNS it — ownership of H at 1.2.0."""
    edge, counts, results, states = _p1_run(pg, event_class="business_launch", agent="venus", chart=CHART_ARIES,
                                            generation="6.4", dasha_rows=_running("venus"))
    assert (edge.rule_version, edge.provenance, edge.ruling_ref) == (V, "uncited_extension", ND_H)
    assert counts["records"] == 1
    assert results == {"period_running_at": "true", "natal_bhava_relationship": "true", "transit_relation": "true"}
    assert states == {"admitted"}


def test_a_p1_record_is_admitted_by_karakatva_alone_nd_p2_rule_4(pg):
    """parental_event (father), Aries lagna: H = Sagittarius, Taurus. The natal Sun (Capricorn) neither occupies nor
    owns H and has no dispositor relation — without rule 4 its relation is `none` (a real false). The Sun is the class
    kāraka, so as the AD anchor lord it satisfies prerequisite (2): the Sun through Libra under its own AD is ADMITTED."""
    from services.gochara_rules import permission as perm
    saved = reg.KARAKATVA_P1_CLASSES
    reg.KARAKATVA_P1_CLASSES = frozenset()
    try:
        assert perm.period_lord_relation("Sun", "parental_event", CHART_ARIES, rule_version=V)["relation"] == "none"
    finally:
        reg.KARAKATVA_P1_CLASSES = saved
    _edge, counts, results, states = _p1_run(pg, event_class="parental_event", agent="sun", chart=CHART_ARIES,
                                             generation="6.5", dasha_rows=_running("sun"))
    assert counts["records"] == 1 and results["natal_bhava_relationship"] == "true" and states == {"admitted"}


def test_a_1_0_0_grain_behaves_exactly_as_before(pg):
    """The controls of the version threading. (a) marriage P1 at 1.0.0: Saturn has no natal relation to marriage — a
    real false, as before (and Saturn is no marriage kāraka at any version). (b) marriage P3 at 1.0.0 is admitted as
    before. (c) an ND-H class's 1.0.0 grains enumerate nothing, so nothing can be admitted under the old H."""
    _edge, _counts, results, states = _p1_run(pg, event_class="marriage", agent="saturn", chart=CHART_ARIES,
                                              generation="6.6", dasha_rows=_running("saturn"))
    assert results["natal_bhava_relationship"] == "false" and states == {"not_admitted"}
    (edge,) = [e for e in ev.enumerate_edges("marriage", "P3", CHART_ARIES, rule_version="1.0.0")
               if e.transit and e.relation == "residence" and e.agent == "saturn" and e.obj.canonical_target == LIBRA]
    _c, rows = _coverage_and_grain(pg, event_class="marriage", path_id="P3", chart=CHART_ARIES, edges=[edge],
                                   generation="6.7", bodies=("Saturn",))
    assert [(r[4], r[5], r[8], r[10]) for r in rows] == [("1.0.0", "verse_cited", "admitted", "true")]
    for path in ("P1", "P3", "P4"):
        assert ev.enumerate_edges("business_launch", path, CHART_ARIES, rule_version="1.0.0") == []


def test_dvi_p4_records_are_accepted_and_admitted_by_the_double_transit_prerequisite(pg):
    """Libra is the 11th from a Sagittarius lagna — achievement_recognition's DVI member. P4's one prerequisite
    (`p4_double_transit`) does not read H, so the pair is ADMITTED end to end on the real schema."""
    edges = _span_edges("achievement_recognition", "P4", CHART_SAGITTARIUS, ("jupiter", "saturn"))
    assert {e.tier for e in edges} == {"dvi"}
    assert LIBRA not in {e.obj.canonical_target for e in ev.enumerate_edges(
        "achievement_recognition", "P3", CHART_SAGITTARIUS, rule_version=V) if e.object_role == "signature_house"}
    counts, rows = _coverage_and_grain(pg, event_class="achievement_recognition", path_id="P4",
                                       chart=CHART_SAGITTARIUS, edges=edges, generation="5.5")
    assert counts["records"] == 2
    assert [(r[0], r[2], r[4], r[5], r[7], r[8], r[9], r[10]) for r in rows] == [
        ("jupiter", "signature_house", V, "uncited_extension", ND_H, "admitted", "p4_double_transit", "true"),
        ("saturn", "signature_house", V, "uncited_extension", ND_H, "admitted", "p4_double_transit", "true")]


def _kb_edges(event_class, path_id, agents, luminary):
    target = ev._point_target(KB_LAM)
    out = [e for e in ev.enumerate_edges(event_class, path_id, CHART_KB, rule_version=V)
           if e.object_role == "karaka" and e.relation == "conjunction" and e.agent in agents]
    assert len(out) == len(agents) and {e.obj.canonical_target for e in out} == {target}
    return out


def _real_saturn_index():
    """The REAL Saturn arc index over the substrate domain (pinned .se1 corpus) — NOT_RUN without it."""
    from tests.l3.gochara import conftest as _c
    if _c._PROBLEMS:
        pytest.skip(f"NOT_RUN: .se1 ephemeris files: {_c._PROBLEMS}")
    from services.gochara_kernel import arcs as gk_arcs
    from services.gochara_kernel.knots import sample_knots
    from services.gochara_kernel.substrate import SUBSTRATE_DOMAIN_END, SUBSTRATE_DOMAIN_START
    ks = sample_knots("Saturn", SUBSTRATE_DOMAIN_START.date(), SUBSTRATE_DOMAIN_END.date(), _c.EPHE_PATH)
    idx = gk_arcs.build_arc_index("Saturn", ks.knot_jds, ks.longitudes_deg)
    return dict(arc_index_for=lambda body: idx, ephe_path=_c.EPHE_PATH, refine=True)


KB_GENERATIONS = {"psychological_arc": "6.1", "parental_event": "6.2", "bereavement": "6.3"}


@pytest.mark.parametrize("event_class, luminary, ruling", [
    ("psychological_arc", "Moon", ND_H), ("parental_event", "Sun", ND_H), ("bereavement", "Sun", ND_P2)])
def test_a_k_b_karaka_record_in_p4_is_accepted_by_the_1155_constraints(pg, event_class, luminary, ruling):
    """`object_role karaka` on a `degree_point` in P4 at 1.2.0 — a REAL Saturn conjunction with the natal luminary —
    is accepted by kgrr_object_role_ck / kgrr_object_kind_ck / the P4@1.2.0 path FK / kgrr_ruling_ck. Only Saturn is in
    the grain (Jupiter is nowhere near that longitude in the horizon), so `p4_double_transit` is an honest `unknown`:
    this test proves ACCEPTANCE by the schema; P4's prerequisite does not read the role (record_store.py:1470-1481)."""
    edges = _kb_edges(event_class, "P4", ("saturn",), luminary)
    counts, rows = _coverage_and_grain(pg, event_class=event_class, path_id="P4", chart=CHART_KB, edges=edges,
                                       generation=KB_GENERATIONS[event_class], bodies=(), **_real_saturn_index())
    assert counts["records"] >= 1 and counts["records"] == counts["contacts"]
    assert {r[:8] for r in rows} == {
        ("saturn", "conjunction", "karaka", "degree_point", V, "uncited_extension", "scored", ruling)}
    assert {(r[9], r[10]) for r in rows} == {("p4_double_transit", "unknown")}
    assert counts["p3_enumeration_defects"] == 0


def _kb_p3_run(conn, generation):
    edges = _kb_edges("psychological_arc", "P3", ("saturn",), "Moon")
    return _coverage_and_grain(conn, event_class="psychological_arc", path_id="P3", chart=CHART_KB, edges=edges,
                               generation=generation, bodies=(), **_real_saturn_index())


def test_a_k_b_karaka_record_in_p3_is_accepted_by_the_1155_constraints(pg):
    counts, rows = _kb_p3_run(pg, "5.6")
    assert counts["records"] >= 1
    assert {r[:8] for r in rows} == {
        ("saturn", "conjunction", "karaka", "degree_point", V, "uncited_extension", "scored", ND_H)}


def test_a_k_b_karaka_record_in_p3_is_admitted_at_materialisation(pg):
    counts, rows = _kb_p3_run(pg, "5.7")
    assert rows and {(r[8], r[10]) for r in rows} == {("admitted", "true")} and counts["p3_enumeration_defects"] == 0


# ── 3. what the schema REFUSES: a SUPPORT row has no role ────────────────────────────────────────────────

def test_a_support_row_is_refused_by_kgrr_object_role_ck(pg):
    """The blocker, by a run: `support_house` (the honest name of a house OUTSIDE H) is not in the closed role list of
    migrations/1155_gochara_relationship_record.sql:537-539. Nothing else about the row is refused first."""
    import psycopg
    (edge,) = [e for e in ev.support_annotation_edges("business_launch", CHART_TAURUS, rule_version=V)
               if e.relation == "residence" and e.agent == "saturn" and e.obj.canonical_target == LIBRA]
    assert (edge.object_role, edge.operator_role, edge.tier) == ("support_house", "testimony", "support")
    with pytest.raises(psycopg.errors.CheckViolation) as exc:
        _coverage_and_grain(pg, event_class="business_launch", path_id="P3", chart=CHART_TAURUS, edges=[edge],
                            generation="5.8", bodies=("Saturn",))
    assert "kgrr_object_role_ck" in str(exc.value)
