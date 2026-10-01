"""A5.3 window_evaluator (1/N) — chart_context + record enumeration (pure;
no DB writes in this increment).

Fixtures: the oracles' constants block (GOCHARA_TEST_ORACLES v1.4) —
lagna 12.43 Aries, the nine natal longitudes verbatim.

What this file proves:

  (a) chart_context: L1 read shape, conflicts named (never row-order picked),
      missing operands named, require_complete refuses a partial chart;
  (b) P3 enumeration: the S-03 union (house AND lord targets), O-RP-2's
      bereavement truth table (H = {Sagittarius, Capricorn, Gemini, Cancer}
      via bhavat_bhavam:9; māraka lords Saturn + Mercury testimony/D-PADMIT),
      N-14 (nodes get no aspect edges), relatives never on the moon frame
      (kgrr_relative_frame_ck);
  (c) P4 enumeration: the P3 scored edges restricted to Jupiter and Saturn
      (R3-S02 — ONE rule);
  (d) H-unknown classes enumerate ZERO edges (admission unqualified — a
      state, never an omission); birth_anchor raises (O-CF-N6);
  (e) record identity: uuid8 over records.py's canonical natural-key bytes
      (E7); unimplemented paths refuse loudly (never a silent empty grain).
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from services.gochara_kernel import chart_context as cc  # noqa: E402
from services.gochara_kernel import evaluator as ev  # noqa: E402
from services.gochara_kernel.substrate import _uuid8_of  # noqa: E402

# Oracles constants block, verbatim.
CHART = {
    "lagna_deg": 12.43,
    "natal": {
        "Sun": 291.96, "Moon": 327.06, "Mars": 198.52, "Mercury": 270.84,
        "Jupiter": 249.79, "Venus": 259.19, "Saturn": 202.43,
        "Rahu": 49.03, "Ketu": 229.03,
    },
}


# ── (a) chart_context ─────────────────────────────────────────────────────────


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return list(self._rows)


class _FakeConn:
    def __init__(self, rows=None, boom=None):
        self.rows = rows or []
        self.boom = boom
        self.sql = []

    def execute(self, sql, params=()):
        self.sql.append((sql, params))
        if self.boom:
            raise self.boom
        return _FakeResult(self.rows)


def _row(fid, subj, val):
    return (fid, subj, val)


def test_fetch_reads_nine_grahas_plus_lagna_with_fact_ids():
    rows = [_row(f"f{i}", s, 100.0 + i)
            for i, s in enumerate(cc.NATAL_SUBJECTS)]
    rows.append(_row("flagna", "LAGNA", 12.43))
    ctx = cc.fetch_chart_context(_FakeConn(rows), "chart-x")
    assert ctx["lagna_deg"] == 12.43
    assert len(ctx["natal"]) == 9
    assert ctx["natal"]["Rahu"] is not None and ctx["natal"]["Ketu"] is not None
    assert ctx["operands_missing"] == []
    assert len(ctx["source_fact_ids"]) == 10
    cc.require_complete(ctx)


def test_conflicting_values_are_named_never_picked():
    rows = [_row("f1", "SUN", 291.96), _row("f2", "SUN", 292.0),
            _row("f3", "LAGNA", 12.43)]
    ctx = cc.fetch_chart_context(_FakeConn(rows), "chart-x")
    assert "graha_position:SUN:conflict" in ctx["operands_missing"]
    assert "Sun" not in ctx["natal"]
    with pytest.raises(ValueError, match="conflict"):
        cc.require_complete(ctx)


def test_missing_operands_are_named():
    ctx = cc.fetch_chart_context(_FakeConn([]), "chart-x")
    assert "graha_position:LAGNA" in ctx["operands_missing"]
    assert "graha_position:MOON" in ctx["operands_missing"]
    with pytest.raises(ValueError):
        cc.require_complete(ctx)


def test_read_failure_is_named_never_silent():
    ctx = cc.fetch_chart_context(_FakeConn(boom=RuntimeError("down")), "chart-x")
    assert ctx["operands_missing"] == ["chart_facts:unreadable"]
    assert "error" in ctx


# ── (b) P3 enumeration ────────────────────────────────────────────────────────


def test_p3_bereavement_oracle_truth_table():
    """O-RP-2: H = {Sagittarius, Capricorn, Gemini, Cancer} via
    bhavat_bhavam:9; the māraka column names the lords of 2/7 from the 9th
    (Saturn, Mercury) as testimony — removing nothing from H."""
    edges = ev.enumerate_edges("bereavement", "P3", CHART)
    spans = {e.obj.canonical_target for e in edges
             if e.object_role == "signature_house" and e.relation == "residence"}
    assert spans == {"span:sign:sagittarius", "span:sign:capricorn",
                     "span:sign:gemini", "span:sign:cancer"}
    assert {(e.frame_kind, e.frame_arg) for e in edges} == {("bhavat_bhavam", "9")}
    assert {e.affected_person for e in edges} == {"father"}
    maraka = [e for e in edges if e.object_role == "maraka_of_house"]
    assert {e.agent for e in maraka} == {"saturn", "mercury"}
    assert all(e.operator_role == "testimony" and e.ruling_ref == "D-PADMIT"
               and not e.transit for e in maraka)


def test_p3_house_and_lord_are_both_targets():
    """S-03: union — house and lord edges coexist for the same agent."""
    edges = ev.enumerate_edges("childbirth", "P3", CHART)
    roles = {e.object_role for e in edges if e.agent == "jupiter"}
    assert "signature_house" in roles and "lord" in roles
    # childbirth H = {5} = Leo from lagna Aries; L = {Sun}; Sun's natal point
    lords = [e for e in edges if e.object_role == "lord" and e.agent == "mars"]
    assert {e.obj.canonical_target for e in lords} == {"point:291.96"}


def test_p3_nodes_cast_no_aspect():
    edges = ev.enumerate_edges("marriage", "P3", CHART)
    assert not [e for e in edges if e.agent in ("rahu", "ketu")
                and e.relation == "aspect"]
    assert [e for e in edges if e.agent in ("rahu", "ketu")
            and e.relation == "residence"]


def test_p3_relatives_never_moon_frame():
    for cls in ("bereavement", "marriage", "childbirth", "major_loss"):
        for e in ev.enumerate_edges(cls, "P3", CHART):
            assert e.affected_person == "native" or e.frame_kind != "moon"


def test_p3_citation_fields_complete_for_verse_cited():
    for e in ev.enumerate_edges("marriage", "P3", CHART):
        if e.provenance == "verse_cited":
            assert e.source_text and e.source_page  # kgrr_citation_ck
        if e.provenance == "uncited_extension":
            assert e.ruling_ref is not None         # kgrr_ruling_ck


# ── (c) P2 ────────────────────────────────────────────────────────────────────


def test_p2_scored_adverse_residence_oracle_shape():
    """O-RP-5a: Saturn in the 8th from the Aquarius Moon is a SCORED edge on
    the adverse class illness_acute (evidence FOR occurrence); gain classes
    carry nothing."""
    edges = ev.enumerate_edges("illness_acute", "P2", CHART)
    sat8 = [e for e in edges if e.agent == "saturn" and e.operator_role == "scored"]
    # Aquarius 1st … Virgo 8th (the oracle's written-out count)
    assert [e.obj.canonical_target for e in sat8] == ["span:sign:virgo"]
    assert all(e.frame_kind == "moon" and e.affected_person == "native"
               and e.relation == "residence" and e.transit for e in edges)


def test_p2_sade_sati_phase_rows_are_testimony_only():
    """O-RP-5b / RQ-5: Saturn's 12/1/2-from-Moon rows are testimony with zero
    score effect — and never a second scored row on the same object."""
    edges = ev.enumerate_edges("illness_acute", "P2", CHART)
    sat = {(e.obj.canonical_target, e.operator_role) for e in edges
           if e.agent == "saturn"}
    assert sat == {("span:sign:virgo", "scored"),       # 8th — scored
                   ("span:sign:capricorn", "testimony"),  # 12th
                   ("span:sign:aquarius", "testimony"),   # 1st
                   ("span:sign:pisces", "testimony")}     # 2nd
    assert all(e.ruling_ref == "D-PADMIT" for e in edges
               if e.operator_role == "testimony")
    # no natural-key collision: one (agent, relation, object) appears once
    keys = [(e.agent, e.relation, e.obj.canonical_target) for e in edges]
    assert len(keys) == len(set(keys))


def test_p2_adverse_residence_never_attaches_to_gain_classes():
    """O-RP-5a holds after the favourable binding: no gain-class edge is a
    member of the adverse plan (Sun/Mars/Jupiter 12/8/1, Saturn 8th) and no
    Sade-Sati testimony row attaches to a gain class."""
    adverse_plan = {("sun", h) for h in (12, 8, 1)} | {("mars", h) for h in (12, 8, 1)} \
        | {("jupiter", h) for h in (12, 8, 1)} | {("saturn", 8)}
    from services.gochara_rules.frames import Frame, nth_sign_from
    moon = Frame("moon")
    adverse_targets = {(a, nth_sign_from(moon, h, CHART).lower()) for a, h in adverse_plan}
    for cls in ("childbirth", "marriage"):
        for e in ev.enumerate_edges(cls, "P2", CHART):
            assert e.operator_role == "scored"
            assert e.provenance == "verse_cited"
            assert (e.agent, e.obj.canonical_target) not in {
                (a, f"span:sign:{s}") for a, s in adverse_targets}


def test_p2_gain_classes_enumerate_the_cited_favourable_table():
    """PG321–323 governs: every gain-class P2 edge is a verse_cited, scored
    residence on a favourable house from janma-rāśi — the #2812
    favourable_houses table, never a fabricated set. Aquarius Moon: the
    Sun's 3rd from the Moon is Aries (the oracle's written-out count)."""
    from services.gochara_rules.favourable_houses import (
        FAVOURABLE_HOUSES_FROM_MOON, favourable_houses)
    from services.gochara_rules.frames import Frame, nth_sign_from
    moon = Frame("moon")
    edges = ev.enumerate_edges("marriage", "P2", CHART)
    expected = set()
    for agent, row in FAVOURABLE_HOUSES_FROM_MOON.items():
        for h in sorted(favourable_houses(agent)):
            expected.add((agent.lower(),
                          f"span:sign:{nth_sign_from(moon, h, CHART).lower()}"))
    got = {(e.agent, e.obj.canonical_target) for e in edges}
    assert got == expected
    assert ("sun", "span:sign:aries") in got            # 3rd from Aquarius
    assert ("rahu", "span:sign:aries") in got           # śl.2: Rāhu = Sun
    assert ("ketu", "span:sign:scorpio") in got         # śl.2: Ketu = Sun, 10th
    # the 10th for the nodes is the very row brahmagyan/l0_transit.py omits —
    # the recorded L0 deviation the steward named (M20261001T084530-9b65)
    assert ("rahu", "span:sign:scorpio") in got
    assert all(e.source_page and "PG32" in e.source_page for e in edges)  # E9
    # no natural-key collision
    keys = [(e.agent, e.relation, e.obj.canonical_target) for e in edges]
    assert len(keys) == len(set(keys))


def test_p2_gain_classes_all_covered_non_adverse_empty():
    for cls, row in ev.CLASS_BY_NAME.items():
        if cls == "birth_anchor":
            continue
        if row["polarity"] == "gain":
            assert ev.enumerate_edges(cls, "P2", CHART), cls
        elif row["polarity"] not in ("adverse", "anchor"):
            assert ev.enumerate_edges(cls, "P2", CHART) == []


def test_p2_adverse_classes_all_covered():
    for cls, row in ev.CLASS_BY_NAME.items():
        if row["polarity"] == "adverse" and cls != "birth_anchor":
            assert ev.enumerate_edges(cls, "P2", CHART), cls


# ── (c2) P1 ───────────────────────────────────────────────────────────────────


def test_p1_marriage_natal_rows():
    """Aries lagna ⇒ 7th Libra: Venus ownership; Mars (198.52) and Saturn
    (202.43) occupancy — O-RR-3's natal-Saturn-as-7th-occupant target."""
    edges = ev.enumerate_edges("marriage", "P1", CHART)
    natal = [e for e in edges if not e.transit]
    own = [e for e in natal if e.relation == "ownership"]
    occ = [e for e in natal if e.relation == "occupancy"]
    assert [(e.agent, e.obj.canonical_target) for e in own] == [
        ("venus", "span:sign:libra")]
    assert {(e.agent, e.obj.canonical_target) for e in occ} == {
        ("mars", "span:sign:libra"), ("saturn", "span:sign:libra")}
    assert all(e.frame_kind == "dasha_lord" and e.operator_role == "scored"
               for e in own + occ)


def test_p1_node_dispositor_testimony_rows():
    edges = ev.enumerate_edges("marriage", "P1", CHART)
    nodes = [e for e in edges if e.relation == "dispositorship"]
    # Rahu 49.03 Taurus → Venus; Ketu 229.03 Scorpio → Mars
    assert {(e.agent, e.obj.body, e.obj.canonical_target) for e in nodes} == {
        ("rahu", "venus", "span:sign:taurus"),
        ("ketu", "mars", "span:sign:scorpio")}
    assert all(e.operator_role == "testimony" and e.ruling_ref == "D-PADMIT"
               for e in nodes)


def test_p1_no_unruled_relation_rows():
    """D3: non-node dispositorship / association rows are absent (uncited,
    no ruling_ref — kgrr_ruling_ck)."""
    for cls in ("marriage", "bereavement", "illness_acute"):
        assert not [e for e in ev.enumerate_edges(cls, "P1", CHART)
                    if e.relation == "association"]


def test_p1_transit_edges_cover_the_cited_dignity_signs():
    edges = ev.enumerate_edges("career_entry", "P1", CHART)
    transit = {(e.agent, e.obj.canonical_target) for e in edges if e.transit}
    # every graha's own + exaltation + debility signs are present
    assert ("saturn", "span:sign:libra") in transit      # exaltation
    assert ("saturn", "span:sign:capricorn") in transit  # own
    assert ("saturn", "span:sign:aries") in transit      # debility
    # Sun and Jupiter ride EVERY graha's exaltation sign (śl.34-38)
    for sign in ("aries", "taurus", "capricorn", "virgo", "cancer",
                 "pisces", "libra"):
        assert ("sun", f"span:sign:{sign}") in transit
        assert ("jupiter", f"span:sign:{sign}") in transit
    # nodes carry no cited transit residence content
    assert not {a for a, _ in transit} & {"rahu", "ketu"}
    assert all(e.object_role == "period_lord" for e in edges if e.transit)


def test_p1_h_unknown_class_enumerates_empty():
    assert ev.enumerate_edges("spiritual_turn", "P1", CHART) == []


# ── (d) P4 ────────────────────────────────────────────────────────────────────


def test_p4_is_p3_scored_edges_restricted_to_jupiter_and_saturn():
    p3 = [e for e in ev.enumerate_edges("bereavement", "P3", CHART)
          if e.agent in ("jupiter", "saturn") and e.operator_role == "scored"]
    p4 = ev.enumerate_edges("bereavement", "P4", CHART)
    assert p3 == p4
    assert {e.agent for e in p4} <= {"jupiter", "saturn"}
    assert all(e.operator_role == "scored" for e in p4)


# ── (d) honesty of empty and excluded grains ──────────────────────────────────


def test_h_unknown_class_enumerates_zero_edges():
    assert ev.enumerate_edges("spiritual_turn", "P3", CHART) == []
    assert ev.enumerate_edges("spiritual_turn", "P4", CHART) == []


def test_birth_anchor_refused():
    with pytest.raises(ValueError, match="O-CF-N6"):
        ev.enumerate_edges("birth_anchor", "P3", CHART)


def test_unimplemented_paths_refuse_loudly():
    for path in ("P5",):
        with pytest.raises(NotImplementedError, match=path):
            ev.enumerate_edges("marriage", path, CHART)
    with pytest.raises(ValueError):
        ev.enumerate_edges("marriage", "P9", CHART)


# ── (e) record identity (E7) ──────────────────────────────────────────────────


def test_record_uuid_is_uuid8_over_the_canonical_natural_key():
    edge = ev.enumerate_edges("marriage", "P3", CHART)[0]
    key = edge.natural_key(chart_id="c", generation="5.0", contact_id=None,
                           prerequisites=[["p3_contact_house_or_lord", "1.0.0"]],
                           source_text=edge.source_text)
    rid = ev.record_uuid(key)
    assert rid.version == 8
    # deterministic
    assert rid == ev.record_uuid(key)
    # any natural-key change moves the id
    key2 = dict(key, agent="venus")
    assert ev.record_uuid(key2) != rid
