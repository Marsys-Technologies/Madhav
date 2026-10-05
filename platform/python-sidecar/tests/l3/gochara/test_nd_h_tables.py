"""ND-H-20261005 verifier tables (AM-H / AM-K oracles) — pure tests, no database.

The ruling's table is quoted VERBATIM below (ND-H-20261005_DECISION_BY_DELEGATE.md, "Three tiers" table, as carried into
FINAL_BUILD_SCOPE FB-35 and AM-H.4) and parsed here with this test's OWN small parser; the verifier's tables must equal
that text as data. The builder's tables are compared the same way by the FB-38 equality test once the builder side
exists (not here: nothing in this file reads builder code).
"""
from __future__ import annotations

import re

import pytest

from services.gochara_kernel import nd_h_tables as nd

RULING_TABLE = """\
| achievement_recognition | 10 | 11 DVI | 5; 1, 9 | Sun K-A; Jupiter K-A |
| business_launch | 7, 10 | — | 6 | Mercury K-A |
| financial_deception | 2, 12 | 6 DVI | 8 | Rāhu K-A; Saturn excluded |
| foreign_settlement | 12 | 4 DVI | 9, 7 (10 noted) | Rāhu K-A; Saturn excluded |
| parental_event (father, `bhavat_bhavam:9`) | 9, 2 (offsets 1, 6) | — | 8th, 12th from 9th (lagna 4, 8) | Sun K-A + K-B |
| property_acquisition | 4 | 11 DVI | 2 | Mars K-A |
| psychological_arc | 4 | — | 5, 8 | Moon K-B |
| spiritual_turn | 9, 5 | — | 12 (practice; no śloka located) | Jupiter K-A; Ketu K-A; Saturn testimony on 12th contacts only |
"""


def _ints(cell: str) -> frozenset:
    cell = re.sub(r"\([^)]*\)", "", cell)                    # parenthetical remarks carry no house of this tier
    return frozenset(int(x) for x in re.findall(r"\d+", cell))


def _parse():
    out = {}
    for line in RULING_TABLE.strip().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        cls = cells[0].split(" ")[0]
        core_cell, dvi_cell, sup_cell, kar_cell = cells[1:5]
        if cls == "parental_event":
            a, b = (int(x) for x in re.search(r"offsets (\d+), (\d+)", core_cell).groups())
            core = frozenset({nd.frame_house(9, a), nd.frame_house(9, b)})
            sup = frozenset(int(x) for x in re.search(r"lagna (\d+), (\d+)", sup_cell).groups())
        else:
            core, sup = _ints(core_cell), _ints(sup_cell)
        dvi = frozenset() if dvi_cell == "—" else _ints(dvi_cell.replace("DVI", ""))
        noted = frozenset(int(x) for x in re.findall(r"\((\d+) noted\)", sup_cell))
        names = {"Sun": "sun", "Moon": "moon", "Mars": "mars", "Mercury": "mercury", "Jupiter": "jupiter",
                 "Ketu": "ketu", "Rāhu": "rahu"}
        ka = frozenset(names[n] for n in re.findall(r"(Sun|Moon|Mars|Mercury|Jupiter|Ketu|Rāhu) K-A", kar_cell))
        kb = frozenset(names[n] for n in re.findall(r"(Sun|Moon) (?:K-A \+ )?K-B", kar_cell))
        out[cls] = dict(core=core, dvi=dvi, support=sup, noted=noted, ka=ka, kb=kb)
    return out


RULING = _parse()


def test_the_verifier_tables_equal_the_ruling_text_as_data():
    assert set(RULING) == set(nd.TIERS) == nd.EIGHT and len(nd.EIGHT) == 8
    for cls, row in RULING.items():
        t = nd.TIERS[cls]
        assert (t.core, t.dvi, t.support, t.noted) == (row["core"], row["dvi"], row["support"], row["noted"]), cls
        assert nd.KARAKA_A[cls] == row["ka"], cls
        assert ({nd.KARAKA_B_LUMINARY[cls]} if cls in nd.KARAKA_B_LUMINARY else frozenset()) >= row["kb"] \
            and (cls in nd.KARAKA_B_LUMINARY) == bool(row["kb"]), cls


def test_the_ruling_parser_itself_reads_the_cells_it_should():
    assert RULING["parental_event"]["core"] == {9, 2} and RULING["parental_event"]["support"] == {4, 8}
    assert RULING["foreign_settlement"]["support"] == {9, 7} and RULING["foreign_settlement"]["noted"] == {10}
    assert RULING["spiritual_turn"]["support"] == {12} and RULING["achievement_recognition"]["support"] == {5, 1, 9}
    assert RULING["psychological_arc"]["ka"] == frozenset() and RULING["psychological_arc"]["kb"] == {"moon"}


def test_every_class_has_core_tiers_are_disjoint_and_houses_are_in_range():
    for cls, t in nd.TIERS.items():
        assert t.core and not (t.core & t.dvi) and not (t.core & t.support) and not (t.dvi & t.support), cls
        assert all(1 <= h <= 12 for h in t.core | t.dvi | t.support | t.noted), cls


def test_the_frame_arithmetic_for_the_father_and_the_registered_mother():
    assert [nd.frame_house(9, o) for o in (1, 6, 8, 12)] == [9, 2, 4, 8]       # ND-H: 9, 2 | lagna 4, 8
    assert nd.frame_house(4, 1) == 4 and nd.frame_house(4, 6) == 9               # mother: anchor 4, offsets {1, 6}
    assert nd.MOTHER_ROW["lagna_core"] == (4, 9) and nd.MOTHER_ROW["state"] == "unsupported"
    assert nd.TIERS["parental_event"].frame == "bhavat_bhavam:9"


# ── O-H2 / O-H3 / O-H4: what each path may read ──────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("cls", sorted(nd.EIGHT))
def test_dvi_admits_only_in_p4_and_support_never(cls):
    t = nd.TIERS[cls]
    for h in t.dvi:
        assert not nd.admits(cls, "P1", h) and not nd.admits(cls, "P3", h) and nd.admits(cls, "P4", h)
    for h in t.support | t.noted:
        assert not any(nd.admits(cls, p, h) for p in ("P1", "P3", "P4"))
        assert (h in t.support) == nd.is_testimony_house(cls, h)
    for h in t.core:
        assert all(nd.admits(cls, p, h) for p in ("P1", "P3", "P4"))
    assert nd.path_houses(cls, "P1") == nd.path_houses(cls, "P3") == t.core


def test_p2_has_no_house_reading_here():
    with pytest.raises(ValueError):
        nd.path_houses("business_launch", "P2")


def test_no_house_outside_the_table_admits():
    for cls, t in nd.TIERS.items():
        outside = set(range(1, 13)) - t.core - t.dvi
        assert not any(nd.admits(cls, p, h) for p in ("P1", "P3", "P4") for h in outside), cls


# ── O-H7: H unknown no more, and not elsewhere ───────────────────────────────────────────────────────────────────
def test_st_h_unknown_ends_for_a_class_only_at_1_2_0():
    assert nd.carried_excluded("spiritual_turn", "1.0.0") and not nd.carried_excluded("spiritual_turn", "1.2.0")
    assert not nd.carried_excluded("marriage", "1.0.0") and not nd.carried_excluded("bereavement", "1.0.0")


# ── O-H5 / class-specific K-A oracles ────────────────────────────────────────────────────────────────────────────
def test_karaka_agent_values_follow_the_table_and_saturn_is_no_kāraka_for_deception_or_foreign():
    assert nd.karaka_agent_value("financial_deception", "rahu") == "karaka"
    assert nd.karaka_agent_value("financial_deception", "saturn") == "non_karaka"
    assert nd.karaka_agent_value("financial_deception", "mercury") == "non_karaka"       # Mercury is business only
    assert nd.karaka_agent_value("business_launch", "mercury") == "karaka"
    assert nd.karaka_agent_value("foreign_settlement", "saturn") == "non_karaka"
    assert nd.karaka_agent_value("spiritual_turn", "saturn") == "non_karaka"
    assert {a for a in nd.NINE if nd.karaka_agent_value("spiritual_turn", a) == "karaka"} == {"jupiter", "ketu"}
    assert {a for a in nd.NINE if nd.karaka_agent_value("achievement_recognition", a) == "karaka"} == {"sun", "jupiter"}
    assert {a for a in nd.NINE if nd.karaka_agent_value("psychological_arc", a) == "karaka"} == set()   # Moon is K-B only
    assert nd.karaka_agent_value("marriage", "venus") is None                          # no factor outside the table


def test_saturn_annotates_only_contacts_to_the_12th_for_spiritual_turn():
    assert nd.saturn_testimony("spiritual_turn", 12)
    assert not nd.saturn_testimony("spiritual_turn", 9) and not nd.saturn_testimony("spiritual_turn", 5)
    assert not nd.saturn_testimony("financial_deception", 12)


# ── AM-K.1 / O-K1..K4: the K-B licence ───────────────────────────────────────────────────────────────────────────
def test_o_k1_father_class_saturn_within_one_degree_only_and_fast_agents_never():
    L = nd.kb_edge_licensed
    assert L("parental_event", "P3", "saturn", "conjunction", 1.0, "sun")
    assert not L("parental_event", "P3", "saturn", "conjunction", 1.4, "sun")
    assert not L("parental_event", "P3", "mars", "conjunction", 0.2, "sun")           # fast agent
    assert L("parental_event", "P3", "rahu", "conjunction", 0.5, "sun")
    assert not L("parental_event", "P3", "rahu", "aspect", 0.5, "sun")                # nodes cast no dṛṣṭi
    assert L("parental_event", "P3", "jupiter", "aspect", 0.3, "sun")
    assert not L("parental_event", "P3", "saturn", "conjunction", 0.5, "moon")        # the wrong luminary
    assert not L("parental_event", "P1", "saturn", "conjunction", 0.5, "sun")         # K-B lives in P3/P4 only


def test_o_k2_p4_admits_through_k_b_for_jupiter_and_saturn_only():
    L = nd.kb_edge_licensed
    assert L("parental_event", "P4", "saturn", "conjunction", 0.5, "sun")
    assert L("parental_event", "P4", "jupiter", "aspect", 0.5, "sun")
    assert not L("parental_event", "P4", "rahu", "conjunction", 0.5, "sun")
    assert not L("parental_event", "P4", "ketu", "conjunction", 0.5, "sun")


def test_psychological_arc_takes_the_moon_and_o_k3_other_classes_have_no_k_b_edge():
    assert nd.kb_edge_licensed("psychological_arc", "P3", "saturn", "conjunction", 0.9, "moon")
    assert not nd.kb_edge_licensed("psychological_arc", "P3", "saturn", "conjunction", 0.9, "sun")
    for cls in ("achievement_recognition", "business_launch", "financial_deception", "foreign_settlement",
                "property_acquisition", "spiritual_turn", "marriage"):
        assert nd.kb_edge_set(cls) == frozenset(), cls
        assert not nd.kb_edge_licensed(cls, "P3", "saturn", "conjunction", 0.1, "sun")


def test_o_k4_father_bereavement_takes_natal_sun_under_nd_p2_with_the_same_licence():
    assert nd.KB_SOURCE["bereavement"] == nd.RULING_P2 and nd.KB_SOURCE["parental_event"] == nd.RULING_H
    L = nd.kb_edge_licensed
    assert L("bereavement", "P3", "saturn", "conjunction", 1.0, "sun")
    assert not L("bereavement", "P3", "rahu", "aspect", 0.5, "sun")
    assert L("bereavement", "P4", "jupiter", "conjunction", 0.5, "sun") and not L("bereavement", "P4", "ketu", "conjunction", 0.5, "sun")


def test_the_k_b_edge_set_is_exactly_the_licence_table():
    e = nd.kb_edge_set("parental_event")
    assert e == frozenset({("P3", "jupiter", "conjunction"), ("P3", "jupiter", "aspect"),
                           ("P3", "saturn", "conjunction"), ("P3", "saturn", "aspect"),
                           ("P3", "rahu", "conjunction"), ("P3", "ketu", "conjunction"),
                           ("P4", "jupiter", "conjunction"), ("P4", "jupiter", "aspect"),
                           ("P4", "saturn", "conjunction"), ("P4", "saturn", "aspect")})
    assert nd.kb_edge_set("bereavement") == e == nd.kb_edge_set("psychological_arc")
    assert nd.BAND_DEG == 1.0                                                           # not ND-H's 5 degrees


# ── person resolution and P2 ─────────────────────────────────────────────────────────────────────────────────────
def test_the_mother_never_resolves_as_the_father_and_p2_emits_no_parental_row():
    assert nd.resolve_person("parental_event", "father") == nd.resolve_person("parental_event", None) == "father"
    with pytest.raises(nd.PersonUnresolved, match="unsupported"):
        nd.resolve_person("parental_event", "mother")
    with pytest.raises(nd.PersonUnresolved, match="unknown_person"):
        nd.resolve_person("parental_event", "uncle")
    with pytest.raises(nd.PersonUnresolved):
        nd.resolve_person("marriage", "father")
    assert "parental_event" in nd.P2_EMITS_NO_ROW and "psychological_arc" in nd.P2_EMITS_NO_ROW


# ── FB-41: the 40 percent guard ──────────────────────────────────────────────────────────────────────────────────
def test_the_forty_percent_guard_reverts_only_a_class_with_a_dvi_member_and_only_strictly_above():
    assert nd.dvi_reverts_to_support("achievement_recognition", 0.44)                 # ND-H quoted 44%
    assert not nd.dvi_reverts_to_support("achievement_recognition", 0.40)             # exactly the band does not exceed it
    assert not nd.dvi_reverts_to_support("property_acquisition", 0.39)
    assert nd.dvi_reverts_to_support("financial_deception", 0.37 + 0.04)
    assert not nd.dvi_reverts_to_support("business_launch", 0.99)                     # no DVI member: nothing to revert
    assert not nd.dvi_reverts_to_support("marriage", 0.99)
    assert {c for c, t in nd.TIERS.items() if t.dvi} == {"achievement_recognition", "financial_deception",
                                                        "foreign_settlement", "property_acquisition"}
