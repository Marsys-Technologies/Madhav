"""ND-H-20261005 — BUILDER side (three-tier H and kārakas for the eight classes, rule_version 1.2.0).

The EXPECTED tables below are transcribed from the DECISION TEXT
(`decisions/ND-H-20261005_DECISION_BY_DELEGATE.md`, the table and items 1–5, with ERRATA 1), never from the
implementation constant: a test that read `registry.ND_H_ROWS` to build its expectation would prove nothing.

Pure: no database, no ephemeris. The chart is the oracle stub chart (GOCHARA_TEST_ORACLES_v1_4 constants).
"""
from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json

import pytest

from services.gochara_eval import density
from services.gochara_kernel import evaluator as ev
from services.gochara_kernel import inventory as inv
from services.gochara_kernel import rule_registry as rr
from services.gochara_kernel import window_sweep as ws
from services.gochara_rules import registry as reg
from services.gochara_rules.frames import SIGN_LORDS, SIGNS

V = "1.2.0"
RULING = "ND-H-20261005"
CHART = {"lagna_deg": 12.43,
         "natal": {"Sun": 291.96, "Moon": 327.06, "Mars": 198.52, "Mercury": 270.84, "Jupiter": 249.79,
                   "Venus": 259.19, "Saturn": 202.43, "Rahu": 49.03, "Ketu": 229.03},
         "day_birth": True, "paksha": "Shukla"}

# ── the ruling's table, as LAGNA houses (decision text: "opens a window" / "condition" / "support-only") ──
# parental_event: "9, 2 (offsets 1, 6)" and "8th, 12th from 9th (lagna 4, 8)". foreign_settlement: "9, 7 (10 noted)"
# — the 10th is noted, not a member.
RULED_TIERS = {
    "achievement_recognition": {"core": (10,), "dvi": (11,), "support": (1, 5, 9)},
    "business_launch": {"core": (7, 10), "dvi": (), "support": (6,)},
    "financial_deception": {"core": (2, 12), "dvi": (6,), "support": (8,)},
    "foreign_settlement": {"core": (12,), "dvi": (4,), "support": (7, 9)},
    "parental_event": {"core": (2, 9), "dvi": (), "support": (4, 8)},
    "property_acquisition": {"core": (4,), "dvi": (11,), "support": (2,)},
    "psychological_arc": {"core": (4,), "dvi": (), "support": (5, 8)},
    "spiritual_turn": {"core": (5, 9), "dvi": (), "support": (12,)},
}
# kārakas (role): K-A rank, K-B luminary admission. Saturn is excluded for deception and foreign and is NOT a
# scored kāraka for spiritual_turn; Mercury is not added to deception; psychological_arc has Moon K-B ONLY.
RULED_KARAKAS = {
    "achievement_recognition": {"Sun": {"K-A"}, "Jupiter": {"K-A"}},
    "business_launch": {"Mercury": {"K-A"}},
    "financial_deception": {"Rahu": {"K-A"}},
    "foreign_settlement": {"Rahu": {"K-A"}},
    "parental_event": {"Sun": {"K-A", "K-B"}},
    "property_acquisition": {"Mars": {"K-A"}},
    "psychological_arc": {"Moon": {"K-B"}},
    "spiritual_turn": {"Jupiter": {"K-A"}, "Ketu": {"K-A"}},
}
EIGHT = sorted(RULED_TIERS)
OTHERS = sorted(set(reg.CLASS_BY_NAME) - set(EIGHT) - {"birth_anchor"})
LAGNA_SIGN_INDEX = int(CHART["lagna_deg"] // 30)


def sign_of_house(h: int) -> str:
    return SIGNS[(LAGNA_SIGN_INDEX + h - 1) % 12]


def span(h: int) -> str:
    return ev._span_target(sign_of_house(h))


def edges(cls: str, path: str, version: str = V):
    return ev.enumerate_edges(cls, path, CHART, "conv", rule_version=version)


def span_targets(es) -> set[str]:
    return {e.obj.canonical_target for e in es if e.object_kind == "house_span" and e.object_role == "signature_house"}


# ── 1. the tier table equals the ruling's table ──────────────────────────────────────────────────────────

def test_the_eight_classes_are_exactly_the_rulings_eight():
    assert sorted(reg.ND_H_CLASSES) == EIGHT


@pytest.mark.parametrize("cls", EIGHT)
def test_the_tier_table_equals_the_ruling(cls):
    assert reg.tier_table_lagna(V)[cls] == RULED_TIERS[cls]


@pytest.mark.parametrize("cls", EIGHT)
def test_the_karaka_roles_equal_the_ruling(cls):
    got = {k["karaka"]: set(k["roles"]) for k in reg.karaka_set(cls, V)["karakas"]}
    assert got == RULED_KARAKAS[cls]


@pytest.mark.parametrize("cls", EIGHT)
def test_every_row_is_stamped_uncited_extension_scored_under_the_ruling(cls):
    row = reg.nd_h_row(cls, V)
    assert (row["rule_version"], row["provenance"], row["operator_role"], row["ruling_ref"]) == (
        V, "uncited_extension", "scored", RULING)
    assert row["sources"], "premise loci ride in `sources`"
    for k in row["karakas"]:
        assert (k["provenance"], k["ruling_ref"]) == ("uncited_extension", RULING)


def test_errata_1_is_applied_to_the_premise_loci():
    """ERRATA 1: Mars 'House' is UK PG125:C1, Mercury 'Commerce' PG125:C2; BPHS 15.14 is not cited for property."""
    by = {c: {k["karaka"]: k["citation"]["locator"] for k in reg.nd_h_row(c, V)["karakas"]} for c in EIGHT}
    assert by["property_acquisition"]["Mars"] == "PG125:C1"
    assert by["business_launch"]["Mercury"] == "PG125:C2"
    assert not any("15.14" in s for s in reg.nd_h_row("property_acquisition", V)["sources"])
    assert not any("PG562" in s for c in EIGHT for s in reg.nd_h_row(c, V)["sources"])


# ── 2. CORE is H for P1 / P3 / P4; every edge carries its row's stamp ────────────────────────────────────

@pytest.mark.parametrize("cls", EIGHT)
def test_h_is_the_core_tier_in_p1_p3_and_p4(cls):
    core = {span(h) for h in RULED_TIERS[cls]["core"]}
    dvi = {span(h) for h in RULED_TIERS[cls]["dvi"]}
    assert span_targets(edges(cls, "P3")) == core
    assert span_targets(edges(cls, "P1")) == core           # ownership / occupancy rows name CORE houses only
    assert span_targets(edges(cls, "P4")) == core | dvi
    assert {e.agent for e in edges(cls, "P4")} == {"jupiter", "saturn"}
    assert {e.agent for e in edges(cls, "P3")} >= {"sun", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"}


@pytest.mark.parametrize("cls", EIGHT)
@pytest.mark.parametrize("path", ["P1", "P3", "P4"])
def test_scored_edges_carry_the_rulings_stamp_never_verse_cited(cls, path):
    es = edges(cls, path)
    assert es
    scored = [e for e in es if e.operator_role == "scored"]
    assert scored and all((e.provenance, e.ruling_ref, e.rule_version) == ("uncited_extension", RULING, V)
                          for e in scored)
    assert not [e for e in es if e.provenance == "verse_cited"]
    # testimony rows keep their OWN rulings (PD level, node dispositor) — never restamped
    assert {e.ruling_ref for e in es if e.operator_role == "testimony"} <= {"ST-P1-PD-TESTIMONY-20261002", "D-PADMIT"}


def test_parental_event_is_the_father_row_in_the_ninth_house_frame():
    for path in ("P3", "P4"):
        es = edges("parental_event", path)
        assert {(e.affected_person, e.frame_kind, e.frame_arg) for e in es} == {("father", "bhavat_bhavam", "9")}
    assert {e.affected_person for e in edges("parental_event", "P1")} == {"father"}


def test_a_mother_tagged_event_fails_to_resolve_and_never_resolves_as_father():
    assert reg.parental_person_row("father")["anchor_house"] == 9
    mother = reg.PARENTAL_PERSON_ROWS["mother"]
    assert (mother["state"], mother["anchor_house"], mother["core_offsets"]) == ("unsupported", 4, (1, 6))
    assert mother["karakas"] == (("Moon", ("K-A", "K-B")),)
    with pytest.raises(reg.UnsupportedPerson):
        reg.parental_person_row("mother")
    with pytest.raises(reg.UnsupportedPerson):
        reg.parental_person_row("sibling")


# ── 3. NEGATIVE CONTROLS: DVI admits nothing in P1 or P3 ─────────────────────────────────────────────────

DVI_CLASSES = [c for c in EIGHT if RULED_TIERS[c]["dvi"]]


def test_the_dvi_classes_are_the_rulings_four():
    assert DVI_CLASSES == ["achievement_recognition", "financial_deception", "foreign_settlement",
                           "property_acquisition"]


@pytest.mark.parametrize("cls", DVI_CLASSES)
@pytest.mark.parametrize("path", ["P1", "P3"])
def test_dvi_admits_nothing_in_p1_or_p3(cls, path, monkeypatch):
    """Two independent readings. (a) no P1/P3 edge is a DVI edge or targets a DVI house span; (b) MUTATION: deleting
    the DVI member from the row leaves P1 and P3 byte-identical — while it DOES change P4 (so the control is live)."""
    es = edges(cls, path)
    dvi_spans = {span(h) for h in RULED_TIERS[cls]["dvi"]}
    assert not [e for e in es if e.tier == "dvi"]
    # the class-relationship edges (H and its lords). P1's `period_lord` transit forms are class-INDEPENDENT (a
    # graha's own / exaltation / debility signs, XX.34-38) and name any sign — they are not H members.
    assert not [e for e in es if e.object_role in ("signature_house", "lord", "karaka")
                and e.obj.canonical_target in dvi_spans]
    before, p4_before = repr(es), repr(edges(cls, "P4"))
    rows = copy.deepcopy(reg.ND_H_ROWS)
    rows[cls]["dvi"] = ()
    monkeypatch.setattr(reg, "ND_H_ROWS", rows)
    assert repr(edges(cls, path)) == before
    assert repr(edges(cls, "P4")) != p4_before


@pytest.mark.parametrize("cls", DVI_CLASSES)
def test_dvi_counts_in_p4_for_jupiter_and_saturn_on_the_house_or_its_lord(cls):
    dvi = [e for e in edges(cls, "P4") if e.tier == "dvi"]
    assert {e.agent for e in dvi} == {"jupiter", "saturn"}
    (h,) = RULED_TIERS[cls]["dvi"]
    lord_point = ev._point_target(CHART["natal"][SIGN_LORDS[sign_of_house(h)]])
    assert {(e.object_role, e.obj.canonical_target) for e in dvi} == {("signature_house", span(h)), ("lord", lord_point)}
    assert all((e.operator_role, e.ruling_ref) == ("scored", RULING) for e in dvi)


def test_the_enumerator_refuses_dvi_for_any_agent_but_jupiter_and_saturn():
    with pytest.raises(ValueError):
        ev.enumerate_p3_edges("property_acquisition", CHART, "conv", rule_version=V, dvi_agents=("Mars",))


@pytest.mark.parametrize("cls", EIGHT)
def test_support_members_are_outside_h_and_never_stored_edges(cls):
    support = {span(h) for h in RULED_TIERS[cls]["support"]}
    for path in ("P1", "P3", "P4"):
        assert not span_targets(edges(cls, path)) & support
        assert not [e for e in edges(cls, path) if e.tier == "support"]
    notes = ev.support_annotation_edges(cls, CHART, "conv", rule_version=V)
    assert {e.obj.canonical_target for e in notes} == support
    assert {(e.operator_role, e.tier, e.object_role) for e in notes} == {("testimony", "support", "support_house")}


# ── 4. K-A never admits; K-B admits for the two luminaries only ──────────────────────────────────────────

@pytest.mark.parametrize("cls", EIGHT)
def test_k_a_never_admits_removing_every_rank_karaka_changes_no_edge(cls, monkeypatch):
    before = {p: repr(edges(cls, p)) for p in ("P1", "P3", "P4")}
    rows = copy.deepcopy(reg.ND_H_ROWS)
    for name in rows:
        rows[name]["karakas"] = tuple({**k, "roles": tuple(r for r in k["roles"] if r != "K-A")}
                                      for k in rows[name]["karakas"])
    monkeypatch.setattr(reg, "ND_H_ROWS", rows)
    assert {p: repr(edges(cls, p)) for p in ("P1", "P3", "P4")} == before


def test_the_karaka_agent_factor_is_a_rank_category_that_takes_no_part_in_the_product():
    row = reg.FACTORS[("karaka_agent", V)]
    assert (row["function"], row["categories"], row["calibration_status"], row["null_state"]) == (
        "categorical_ordered", ["karaka", "non_karaka"], "uncalibrated_default", "omit")
    assert "value_mapping" not in row
    outcome = ws.categorical_factor(row)
    assert (outcome.kind, outcome.null_state) == ("missing", ws.OMIT)
    program = ws.RecordProgram(rec=None, qualified=True, null_states=set(), reasons=[], outcomes=[outcome])
    assert program.value_at(dt.datetime(2000, 1, 1, tzinfo=dt.timezone.utc)) == 1.0     # neither zeroes nor scales
    assert program.constant == 1.0
    for pid in ("P1", "P3", "P4"):
        assert ("karaka_agent", V) in [tuple(r) for r in reg.RULE_PATHS[(pid, V)]["soft_factors"]]
        assert ("karaka_agent", V) not in [tuple(r) for r in reg.RULE_PATHS[(pid, "1.0.0")]["soft_factors"]]


def test_the_rank_category_follows_the_ruled_karakas_and_nothing_else():
    for cls in EIGHT:
        for agent in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"):
            want = "karaka" if "K-A" in RULED_KARAKAS[cls].get(agent, ()) else "non_karaka"
            assert reg.karaka_category(cls, agent, V) == want, (cls, agent)
    # Saturn: excluded for deception and foreign, not a scored kāraka for the spiritual turn
    for cls in ("financial_deception", "foreign_settlement", "spiritual_turn"):
        assert reg.karaka_category(cls, "Saturn", V) == "non_karaka"
    assert reg.karaka_category("financial_deception", "Mercury", V) == "non_karaka"
    # before ND-H no class has a rank kāraka (the cited Adh. II sets grant no role)
    assert reg.karaka_category("achievement_recognition", "Sun", "1.0.0") == "non_karaka"


def test_k_b_edges_exist_for_the_two_luminaries_only():
    # (father-bereavement's natal-Sun target is ND-P2 rule 3 — a different ruling, tested in its own section)
    sun, moon = ev._point_target(CHART["natal"]["Sun"]), ev._point_target(CHART["natal"]["Moon"])
    want = {"parental_event": sun, "psychological_arc": moon}
    for cls in EIGHT:
        for path in ("P3", "P4"):
            kb = [e for e in edges(cls, path) if e.object_role == "karaka"]
            if cls not in want:
                assert kb == [], (cls, path)
                continue
            assert {e.obj.canonical_target for e in kb} == {want[cls]}
            assert {e.object_kind for e in kb} == {"degree_point"}
            got = {(e.agent, e.relation) for e in kb}
            slow = {("jupiter", "conjunction"), ("jupiter", "aspect"), ("saturn", "conjunction"), ("saturn", "aspect")}
            nodes = {("rahu", "conjunction"), ("ketu", "conjunction")}
            assert got == (slow | nodes if path == "P3" else slow)        # P4's infl() is Jupiter and Saturn
            assert all((e.operator_role, e.ruling_ref) == ("scored", RULING) for e in kb)
        assert not [e for e in edges(cls, "P1") if e.object_role == "karaka"]     # K-B is P3 and P4's infl() only


def test_a_non_luminary_or_node_karaka_can_never_be_given_k_b():
    for graha in ("Mercury", "Mars", "Jupiter", "Saturn", "Rahu", "Ketu"):
        with pytest.raises(ValueError):
            reg._nd_karaka(graha, "PG1:C1", "x", "K-B")
    # and the enumerator's own filter: a K-B role smuggled onto a non-luminary row yields no edge
    assert reg.kb_luminaries("spiritual_turn", V) == frozenset()
    assert reg.kb_luminaries("parental_event", V) == {"Sun"} and reg.kb_luminaries("psychological_arc", V) == {"Moon"}


def test_the_karaka_row_helper_no_longer_hardcodes_source_or_provenance():
    cited = reg._karaka_row("Venus", "PG49:C1", 6, "wife/marriage")
    assert cited == {"karaka": "Venus", "provenance": "verse_cited",
                     "citation": {"text": "phaladeepika", "locator": "PG49:C1", "sloka": 6}, "note": "wife/marriage"}
    ruled = reg._karaka_row("Rahu", "PG131:C1", None, "x", text="uttara_kalamrita",
                            provenance="uncited_extension", ruling_ref=RULING, roles=("K-A",))
    assert (ruled["citation"]["text"], ruled["provenance"], ruled["ruling_ref"]) == (
        "uttara_kalamrita", "uncited_extension", RULING)
    with pytest.raises(ValueError):
        reg._karaka_row("Rahu", "PG131:C1", None, "x", provenance="uncited_extension")      # no ruling_ref
    with pytest.raises(ValueError):
        reg._karaka_row("Venus", None, None, "x")                                           # cited, no citation


# ── 5. every OTHER class is byte-identical; pre-ND-H versions are still reproducible ─────────────────────

def _stored_rows(classes, versions):
    out = []
    for cls in sorted(classes):
        for path in ("P1", "P2", "P3", "P4", "P5"):
            for version in versions:
                if (path, version) not in reg.RULE_PATHS:
                    continue
                for e in ev.enumerate_edges(cls, path, CHART, "conv", rule_version=version):
                    key = e.natural_key(chart_id="c", generation="g", contact_id=None, prerequisites=[],
                                        source_text=e.source_text)
                    out.append([key, e.object_kind, e.provenance, e.operator_role, e.ruling_ref, e.source_page,
                                e.transit])
    return out


def _digest(rows) -> str:
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


#: GOLDEN, produced on the PRE-CHANGE tree (origin/main 091362f31, `git archive` of services/gochara_rules +
#: services/gochara_kernel, this same function): every stored-row field of every enumerated edge — the record's
#: natural key (which carries rule_version, frame, person, object id, role, source_text) plus kind, provenance,
#: role, ruling, page — for the 18 other classes on P1–P5 at 1.0.0 and 1.1.0.
GOLDEN_OTHERS = (8987, "370f3f1379e64d76338848cfb72caace0b292eb6318f0749254e2a5665c6a842")
#: the same for the eight classes at 1.0.0 / 1.1.0 (their P2 and P5 rows; P1/P3/P4 are empty: H unknown there)
GOLDEN_EIGHT_PRE_ND_H = (1892, "879ef79f4e5e03fcbe6aa408632ee081388bca404162f154e1abe4c0a5e78ec4")


def test_every_other_class_is_byte_identical_at_the_stored_row_level():
    rows = _stored_rows(OTHERS, ("1.0.0", "1.1.0"))
    assert (len(rows), _digest(rows)) == GOLDEN_OTHERS


def test_the_eight_classes_are_still_reproducible_under_the_pre_nd_h_versions(monkeypatch):
    # a PRE-ND-H generation runs under the pre-ND-H SELECTION (no class override): P2's parental_event rows included
    monkeypatch.setattr(rr, "CLASS_SELECTION_OVERRIDES", {})
    rows = _stored_rows(EIGHT, ("1.0.0", "1.1.0"))
    assert (len(rows), _digest(rows)) == GOLDEN_EIGHT_PRE_ND_H
    for cls in EIGHT:
        for version in ("1.0.0", "1.1.0"):
            assert reg.signature_houses(cls, CHART, version) is None          # H unknown there, as before
            for path in ("P1", "P3", "P4"):
                if (path, version) in reg.RULE_PATHS:
                    assert ev.enumerate_edges(cls, path, CHART, "conv", rule_version=version) == []


def test_the_default_h_argument_is_still_the_1_0_0_table():
    assert reg.signature_houses("spiritual_turn", CHART) is None
    assert reg.signature_houses("marriage", CHART) == reg.signature_houses("marriage", CHART, V)
    with pytest.raises(ValueError):
        reg.signature_houses("marriage", CHART, "9.9.9")                      # no H table: never a silent fallback


def test_the_tier_field_is_not_part_of_a_records_identity():
    e = edges("property_acquisition", "P4")[0]
    key = dict(chart_id="c", generation="g", contact_id=None, prerequisites=[], source_text=e.source_text)
    assert e.natural_key(**key) == ev.replace(e, tier=None).natural_key(**key)


# ── 6. selection, binding, and H pinned to the generation ────────────────────────────────────────────────

def test_1_2_0_is_bound_and_selected_for_the_eight_classes_only():
    for pid in ("P1", "P3", "P4"):
        assert (pid, V) in rr.bound_path_refs()
    assert ("P2", V) not in rr.bound_path_refs() and ("P5", V) not in rr.bound_path_refs()
    for cls in EIGHT:
        assert rr.selected_versions_for(cls) == {"P1": V, "P2": "1.0.0", "P3": V, "P4": V, "P5": "1.0.0"}
    for cls in OTHERS:
        if cls == "bereavement":          # ND-P2 rule 3: P3 and P4 only (its own tests below)
            continue
        assert set(rr.selected_versions_for(cls).values()) == {"1.0.0"}
    rr._membership_consistent()
    assert ("karaka_agent", V) in rr.BOUND_FACTOR_REFS
    assert not [r for r in rr.BOUND_PATH_REFS + rr.BOUND_FACTOR_REFS if r[1] == "1.1.0"]      # 1.1.0 stays unbound


def test_the_bound_1_2_0_rows_carry_the_rulings_stamp_and_the_pre_existing_rows_are_unchanged():
    by = {(r["path_id"], r["rule_version"]): r for r in rr.path_rows()}
    for pid in ("P1", "P3", "P4"):
        row = by[(pid, V)]
        assert (row["provenance"], row["operator_role"], row["ruling_ref"]) == ("uncited_extension", "scored", RULING)
    # a sealed row's object_selector is not changed by 1.2.0's K-B role
    assert {s["object_role"] for s in by[("P4", "1.0.0")]["object_selector"]} == {"signature_house", "lord"}
    assert {s["object_role"] for s in by[("P4", V)]["object_selector"]} == {"signature_house", "lord", "karaka"}
    factor = {(r["factor_id"], r["rule_version"]): r for r in rr.factor_rows()}[("karaka_agent", V)]
    assert (factor["null_state"], factor["direction"], factor["doctrine_ordering"]) == (
        "omit", "higher_stronger", ["non_karaka", "karaka"])


def test_h_is_versioned_and_its_digest_is_pinned_into_the_1_2_0_path_rows(monkeypatch):
    digest = reg.h_table_sha256(V)
    # the table is KEYED by rule_version (the label is inside the digest); 1.0.0 and 1.1.0 read the same content
    assert reg.h_table("1.0.0")["classes"] == reg.h_table("1.1.0")["classes"] != reg.h_table(V)["classes"]
    assert len({reg.h_table_sha256(v) for v in ("1.0.0", "1.1.0", V)}) == 3
    for pid in ("P1", "P3", "P4"):
        row = {(r["path_id"], r["rule_version"]): r for r in rr.path_rows()}[(pid, V)]
        assert f"sha256:{digest}" in row["score_rule"]              # a column the registry digest covers
        assert "sha256:" not in reg.RULE_PATHS[(pid, "1.0.0")]["score_rule"]
    table = reg.h_table(V)["classes"]
    assert table["birth_anchor"] == {"state": "excluded"} and table["marriage"]["state"] == "cited"
    assert reg.h_table("1.0.0")["classes"]["spiritual_turn"] == {"state": "unknown"}
    # the digest MOVES when a tier member moves (a DVI member reverted to SUPPORT is a different H)
    rows = copy.deepcopy(reg.ND_H_ROWS)
    rows["property_acquisition"]["dvi"], rows["property_acquisition"]["support"] = (), (2, 11)
    monkeypatch.setattr(reg, "ND_H_ROWS", rows)
    assert reg.h_table_sha256(V) != digest


def _plan(cls):
    lo = dt.datetime(2000, 1, 1, tzinfo=dt.timezone.utc)
    hi = dt.datetime(2001, 1, 1, tzinfo=dt.timezone.utc)
    p5, h_unknown = inv.standing_exclusions()
    rows = [inv.DashaRow("md", 1, "saturn", lo, hi), inv.DashaRow("ad", 2, "jupiter", lo, hi),
            inv.DashaRow("pd", 3, "mars", lo, hi)]
    plan = inv.plan_class_inventory(
        event_class=cls, chart=CHART, horizon=(lo, hi), sealed_paths=rr.bound_path_refs(),
        capability=inv.SearchCapability(position_probe=True, arc_index=True, aspect_span_solver=True),
        selected_versions=rr.selected_versions_for(cls), path_exclusions=p5, h_unknown_exclusion=h_unknown,
        dasha_rows=rows)
    return {(p.path_id, p.rule_version): p for p in plan.pins}


@pytest.mark.parametrize("cls", EIGHT)
def test_an_nd_h_class_plans_1_2_0_included_and_1_0_0_superseded_for_that_class(cls):
    pins = _plan(cls)
    for pid in ("P1", "P3", "P4"):
        assert pins[(pid, V)].disposition == "included" and pins[(pid, V)].obligations
        old = pins[(pid, "1.0.0")]
        assert (old.disposition, old.exclusion_reason, old.basis, old.ruling_ref) == (
            "excluded", "superseded_by_version", f"ruling:{RULING}", None)
    # no P1/P3 obligation targets a DVI house span
    dvi = {span(h) for h in RULED_TIERS[cls]["dvi"]}
    for pid in ("P1", "P3"):
        assert not [o for o in pins[(pid, V)].obligations
                    if o.object_role in ("signature_house", "lord", "karaka") and o.target in dvi]


def test_a_class_outside_the_eight_plans_exactly_as_before_and_accounts_1_2_0_as_not_applicable():
    pins = _plan("marriage")
    for pid in ("P1", "P3", "P4"):
        assert pins[(pid, "1.0.0")].disposition == "included"
        new = pins[(pid, V)]
        assert (new.disposition, new.exclusion_reason, new.basis, new.ruling_ref) == (
            "excluded", "not_applicable_to_class", f"ruling:{RULING}", None)
    want = {o.canonical_bytes for p in ("P3", "P4")
            for o in map(inv.obligation_of_edge, ev.enumerate_edges("marriage", p, CHART, rule_version="1.0.0"))}
    assert {o.canonical_bytes for p in ("P3", "P4") for o in pins[(p, "1.0.0")].obligations} == want


def test_p2_emits_no_parental_event_row_once_the_class_runs_under_its_nd_h_rows():
    assert ev.enumerate_edges("parental_event", "P2", CHART, "conv", rule_version="1.0.0") == []
    assert ev.ephemeral_tier_edges("parental_event", "P2", CHART, "conv", rule_version="1.0.0") == []
    assert ev.enumerate_edges("financial_deception", "P2", CHART, "conv", rule_version="1.0.0")
    pin = _plan("parental_event")[("P2", "1.0.0")]
    assert (pin.disposition, pin.exclusion_reason, pin.basis) == (
        "excluded", "not_applicable_to_class", f"ruling:{RULING}")
    assert _plan("financial_deception")[("P2", "1.0.0")].disposition == "included"     # the other adverse class keeps P2


# ── 7. the admitted-day share and the 40% DVI guard, computed by the scorer ──────────────────────────────

def _span(cls, path, lo, hi, **kw):
    return density.AdmittedSpan(cls, path, dt.date.fromisoformat(lo), dt.date.fromisoformat(hi), **kw)


HORIZON = (dt.date(2001, 1, 1), dt.date(2001, 4, 10))            # 100 days


def test_the_share_is_days_with_an_admitted_span_over_days_in_the_horizon_per_class_and_series():
    spans = [
        _span("property_acquisition", "P3", "2001-01-01", "2001-01-10", agent="mars"),
        _span("property_acquisition", "P3", "2001-01-06", "2001-01-20", agent="saturn"),
        _span("property_acquisition", "P4", "2001-02-01", "2001-02-25"),
        _span("property_acquisition", "P4", "2001-02-01", "2001-02-05", series="P4_no_dvi"),
        _span("property_acquisition", "P1", "2000-12-01", "2001-01-02"),                   # clipped to the horizon
    ]
    rep = density.admitted_day_share_report(spans, HORIZON, dvi_members={"property_acquisition": [11]})
    got = rep["classes"]["property_acquisition"]
    assert rep["horizon_days"] == 100
    assert got["admitted_day_share"] == {"P1": 0.02, "P2": 0.0, "P3": 0.20, "P3_fast": 0.10, "P3_slow": 0.15,
                                         "P4": 0.25, "P4_no_dvi": 0.05, "kb_only": 0.0, "union": 0.45}
    assert got["dvi_guard"]["exceeds_band"] is False and got["dvi_guard"]["revert_dvi_to_support_next_generation"] == []


def test_a_series_that_was_not_supplied_is_null_never_zero():
    rep = density.admitted_day_share_report([_span("business_launch", "P3", "2001-01-01", "2001-01-10")], HORIZON)
    got = rep["classes"]["business_launch"]
    assert got["admitted_day_share"]["P4_no_dvi"] is None and got["admitted_day_share"]["P3_fast"] is None
    assert got["not_supplied"] == ["P3_fast", "P3_slow", "P4_no_dvi"]


def test_the_k_b_contribution_is_days_admitted_only_through_a_luminary_target():
    spans = [_span("psychological_arc", "P3", "2001-01-01", "2001-01-10", agent="saturn", via_kb=True),
             _span("psychological_arc", "P3", "2001-01-08", "2001-01-12", agent="mars")]
    got = density.admitted_day_share_report(spans, HORIZON)["classes"]["psychological_arc"]
    assert got["admitted_days"]["kb_only"] == 7 and got["admitted_days"]["union"] == 12


@pytest.mark.parametrize("p4_days, reverts", [(40, []), (41, [11])])
def test_the_dvi_guard_fires_strictly_above_the_40_percent_band_and_names_the_next_generation(p4_days, reverts):
    hi = (HORIZON[0] + dt.timedelta(days=p4_days - 1)).isoformat()
    spans = [_span("achievement_recognition", "P4", "2001-01-01", hi)]
    rep = density.admitted_day_share_report(spans, HORIZON, dvi_members={"achievement_recognition": [11]})
    guard = rep["classes"]["achievement_recognition"]["dvi_guard"]
    assert guard["p4_alone_share"] == p4_days / 100 and guard["band_upper"] == 0.40
    assert guard["revert_dvi_to_support_next_generation"] == reverts
    assert guard["applies_to"] == "next_generation" and guard["ruling_ref"] == RULING
    assert rep["dvi_reversions_next_generation"] == ({"achievement_recognition": [11]} if reverts else {})


def test_a_class_with_no_dvi_member_has_nothing_to_revert_even_above_the_band():
    spans = [_span("parental_event", "P4", "2001-01-01", "2001-03-31")]
    guard = density.admitted_day_share_report(spans, HORIZON)["classes"]["parental_event"]["dvi_guard"]
    assert guard["exceeds_band"] is True and guard["revert_dvi_to_support_next_generation"] == []


def test_the_guard_reports_and_edits_nothing():
    before = (copy.deepcopy(reg.ND_H_ROWS), reg.h_table_sha256(V))
    spans = [_span("property_acquisition", "P4", "2001-01-01", "2001-04-10")]
    rep = density.admitted_day_share_report(spans, HORIZON, dvi_members={"property_acquisition": [11]})
    assert rep["dvi_reversions_next_generation"] == {"property_acquisition": [11]}
    assert (reg.ND_H_ROWS, reg.h_table_sha256(V)) == before
    assert reg.tier_table_lagna(V)["property_acquisition"]["dvi"] == (11,)          # this generation keeps its DVI


def test_the_scorer_reads_the_dvi_members_of_the_generations_own_h_table():
    dvi = {c: list(t["dvi"]) for c, t in reg.tier_table_lagna(V).items() if t["dvi"]}
    assert dvi == {c: list(RULED_TIERS[c]["dvi"]) for c in DVI_CLASSES}


# ── 8. ND-P2-20261005 rule 3: natal Sun as a target for FATHER-BEREAVEMENT ───────────────────────────────
# Transcribed from the decision text (rule 3): "for the father-specific bereavement class, natal Sun is a derived
# target under ruling provenance. In P3, Jupiter and Saturn by conjunction or aspect, Rahu and Ketu by conjunction;
# in P4, Jupiter and Saturn only. The band is the built 1-degree point band ... Houses and maraka testimony
# unchanged."
P2_RULING = "ND-P2-20261005"
RULE3_P3 = {("jupiter", "conjunction"), ("jupiter", "aspect"), ("saturn", "conjunction"), ("saturn", "aspect"),
            ("rahu", "conjunction"), ("ketu", "conjunction")}
RULE3_P4 = {("jupiter", "conjunction"), ("jupiter", "aspect"), ("saturn", "conjunction"), ("saturn", "aspect")}


def test_rule_3_natal_sun_is_a_target_for_father_bereavement_with_the_k_b_agent_table():
    sun = ev._point_target(CHART["natal"]["Sun"])
    for path, want in (("P3", RULE3_P3), ("P4", RULE3_P4)):
        kb = [e for e in edges("bereavement", path) if e.object_role == "karaka"]
        assert {(e.agent, e.relation) for e in kb} == want
        assert {(e.obj.canonical_target, e.object_kind, e.affected_person, e.frame_kind, e.frame_arg) for e in kb} == {
            (sun, "degree_point", "father", "bhavat_bhavam", "9")}
        assert {(e.provenance, e.operator_role, e.ruling_ref, e.rule_version) for e in kb} == {
            ("uncited_extension", "scored", P2_RULING, V)}
        assert all("ND-P2-20261005" in e.source_text and e.source_page is None for e in kb)
    # the oracle of FB-45: a Rāhu ASPECT produces none (nodes cast no dṛṣṭi); no fast agent ever
    assert not [e for e in edges("bereavement", "P3") if e.object_role == "karaka"
                and (e.agent in ("sun", "moon", "mars", "mercury", "venus") or (e.agent in ("rahu", "ketu") and e.relation == "aspect"))]


def test_rule_3_leaves_houses_and_maraka_testimony_unchanged():
    """Everything but the natal-Sun edges is the 1.0.0 enumeration with only the version label moved."""
    for path in ("P3", "P4"):
        new = [e for e in edges("bereavement", path) if e.object_role != "karaka"]
        old = edges("bereavement", path, "1.0.0")
        assert [ev.replace(e, rule_version="1.0.0") for e in new] == old
        assert {e.tier for e in new} == {None}                               # no ND-H tier: its H stays the cited table
    assert reg.signature_houses("bereavement", CHART, V) == reg.signature_houses("bereavement", CHART, "1.0.0")
    assert reg.nd_h_row("bereavement", V) is None and "bereavement" not in reg.ND_H_CLASSES
    marakas = [e for e in edges("bereavement", "P3") if e.object_role == "maraka_of_house"]
    assert marakas and {(e.operator_role, e.ruling_ref) for e in marakas} == {("testimony", "D-PADMIT")}


def test_rule_3_reaches_p3_and_p4_only_and_no_other_class(monkeypatch):
    assert rr.selected_versions_for("bereavement") == {"P1": "1.0.0", "P2": "1.0.0", "P3": V, "P4": V, "P5": "1.0.0"}
    assert not [e for e in edges("bereavement", "P1") if e.object_role == "karaka"]
    assert reg.kb_targets("bereavement", "1.0.0") == ()                       # nothing before 1.2.0
    for cls in OTHERS:
        if cls != "bereavement":
            assert reg.kb_targets(cls, V) == ()
    # MUTATION: without the rule-3 row the bereavement enumeration has no karaka edge (the control is live)
    monkeypatch.setattr(reg, "ND_P2_KB_TARGETS", {})
    assert not [e for e in edges("bereavement", "P3") if e.object_role == "karaka"]


def test_rule_3_carries_no_orb_the_band_is_the_built_one_degree_convention():
    """The enumerator emits a degree-point target and nothing else; the band is the contact engine's convention
    (ND-P2 rule 3: the built 1-degree point band, not admission.py's 5-degree helper default)."""
    from services.gochara_kernel import convention
    for e in (x for x in edges("bereavement", "P3") if x.object_role == "karaka"):
        assert e.obj.canonical_target.startswith("point:") and not hasattr(e, "orb_deg")
    assert convention.ORB_TABLE["orb_conj_slow"]["orb_max_deg"] == 1.0
    assert convention.ORB_TABLE["orb_drishti_slow"]["orb_max_deg"] == 1.0


def test_rule_3_inventory_bereavement_p3_p4_included_at_1_2_0_and_1_0_0_superseded_under_nd_p2():
    pins = _plan("bereavement")
    for pid in ("P3", "P4"):
        assert pins[(pid, V)].disposition == "included"
        assert [o for o in pins[(pid, V)].obligations if o.object_role == "karaka"]
        old = pins[(pid, "1.0.0")]
        assert (old.disposition, old.exclusion_reason, old.basis) == (
            "excluded", "superseded_by_version", f"ruling:{P2_RULING}")
    assert pins[("P1", "1.0.0")].disposition == "included"
    assert (pins[("P1", V)].disposition, pins[("P1", V)].exclusion_reason) == ("excluded", "not_applicable_to_class")
    assert pins[("P2", "1.0.0")].disposition == "included"                   # P2 for bereavement is untouched


def test_rule_3_target_is_pinned_in_the_versioned_h_table():
    assert reg.h_table(V)["classes"]["bereavement"]["kb_targets"] == [["Sun", P2_RULING]]
    assert "kb_targets" not in reg.h_table("1.0.0")["classes"]["bereavement"]
