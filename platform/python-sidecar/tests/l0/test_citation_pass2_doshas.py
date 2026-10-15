"""CITATION-PASS2 (decision OS-2026-10-05-CITATIONS) — bg_doshas / bg_ontology dosha projections, tested by natural key (canonical_id).

The 53 brahma_dosha_catalog rows (and the identical 53 brahma_ontology entity_class=dosha rows) of PASS2_DECISIONS.tsv: 13 REMOVE, 7 APPLY_K1, 7 CONTENT_FIX+K1,
3 CONTENT_FIX+K2, 8 KEEP_UNVERIFIED_LABELLED, 15 LABEL_K2_MODERN. Offline: the seed list only; the census Ldgr citation rule is read through the shared Python mirror.
"""
from __future__ import annotations

import re

import pytest

from brahmagyan import citation_pass2_doshas as C
from brahmagyan import l0_doshas as L
from tests._citation_pass2_ldgr import citation_lacks_source, jsonb_citation_lacks_source

REMOVED = {f"kala_sarpa_{v}" for v in ("anant", "kulik", "vasuki", "shankhpal", "padma", "mahapadma", "takshak", "karkotak", "shankhachud", "ghatak", "vishdhar", "sheshnag")} | {"vish_dosha"}
APPLY_K1 = {"dhaiya", "sade_sati", "tara_dosha_compat", "yoni_dosha", "graha_maitri_dosha", "varna_dosha", "vashya_dosha"}
FIX_K1 = {"daridra", "mrityu_bhaga_dosha", "abhukta_mula_dosha", "gana_dosha", "mool_dosha", "nadi_dosha", "bhakoot_dosha"}
FIX_K2 = {"chandra_grahan_dosha", "kala_sarpa", "punarphoo"}
UNVERIFIED = {"kemadruma_compat_kuja", "kuja_dosha_from_moon", "shakata", "mahendra_dosha", "rajju_dosha", "stree_deergha_dosha", "vedha_dosha", "vish_kanya_dosha"}
LABEL_K2 = {"angarak", "chandal_yoga_dosha", "guru_chandal", "kala_amrita_dosha", "lagna_lord_grahan_dosha", "naga_dosha_nodes_kendra", "naga_dosha_rahu_lagna",
            "pitra_dosha_9th_lord_afflicted", "pitra_dosha_sun_12th_malefic", "pitra_dosha_sun_rahu", "pitra_dosha_sun_saturn_conjunction", "pitru_dosha",
            "shrapit_dosha", "surya_grahan_dosha", "grahan"}
# SS ruling 5 (2026-10-05): the rows whose fix says "the K2 segment carries the modern-name flag" but whose citation string had no K2 segment gain '; name is modern (OS-2026-10-05-CITATIONS)'
NAME_FLAG = {"daridra", "kemadruma_compat_kuja", "kuja_dosha_from_moon", "mrityu_bhaga_dosha", "shakata", "abhukta_mula_dosha", "gana_dosha", "mahendra_dosha", "mool_dosha", "nadi_dosha",
             "rajju_dosha", "stree_deergha_dosha", "tara_dosha_compat", "vedha_dosha", "yoni_dosha", "bhakoot_dosha", "graha_maitri_dosha", "varna_dosha", "vashya_dosha", "vish_kanya_dosha"}
EDITED = APPLY_K1 | FIX_K1 | FIX_K2 | UNVERIFIED | LABEL_K2
K2_ID = "OS-2026-10-05-CITATIONS"
BEFORE = {d["canonical_id"]: d for d in L.DOSHAS}
AFTER = {d["canonical_id"]: d for d in L.pass2_doshas()}
RENAME_OLD, RENAME_NEW = "kemadruma_compat_kuja", "kuja_dosha_from_venus"


def _after(cid):
    return AFTER[C.RENAMED_DOSHA_IDS.get(cid, cid)]


def test_decision_sets_cover_exactly_the_53_tsv_rows():
    groups = [REMOVED, APPLY_K1, FIX_K1, FIX_K2, UNVERIFIED, LABEL_K2]
    assert [len(g) for g in groups] == [13, 7, 7, 3, 8, 15]
    assert len(set().union(*groups)) == 53
    assert C.REMOVED_DOSHA_IDS == REMOVED
    assert set(C.PASS2_DOSHA_EDITS) == EDITED and len(EDITED) == 40
    assert C.RENAMED_DOSHA_IDS == {RENAME_OLD: RENAME_NEW}


def test_row_counts_79_to_66_and_the_three_projections_share_one_list():
    assert len(BEFORE) == 79 and len(AFTER) == 66
    assert 79 - len(REMOVED) == 66


def test_removed_absent_rename_present_nothing_else_moves():
    assert not (REMOVED & set(AFTER))
    assert set(BEFORE) - set(AFTER) == REMOVED | {RENAME_OLD}
    assert set(AFTER) - set(BEFORE) == {RENAME_NEW}


def test_untouched_rows_are_identical():
    for cid, row in AFTER.items():
        if cid in EDITED or cid == RENAME_NEW:
            continue
        assert row == BEFORE[cid], cid
    assert len([c for c in AFTER if c not in EDITED and c != RENAME_NEW]) == 66 - 40


def test_overlay_does_not_mutate_the_authored_rows():
    again = C.apply_pass2_doshas(L.DOSHAS)
    assert again == L.pass2_doshas()
    assert {d["canonical_id"] for d in L.DOSHAS} == set(BEFORE) and len(L.DOSHAS) == 79      # the authored list is never rebound or mutated


def test_overlay_raises_when_a_decided_key_is_missing():
    rows = [d for d in L.DOSHAS if d["canonical_id"] != "rajju_dosha"]
    with pytest.raises(RuntimeError, match="rajju_dosha"):
        C.apply_pass2_doshas(rows)


# ---- citations --------------------------------------------------------------------------------------------------------

K1_LOCUS = re.compile(r"^PG\d+:C\d+")
CORPUS_TEXTS = {"phaladeepika", "bphs", "muhurta_chintamani", "jataka_parijata", "saravali"}


@pytest.mark.parametrize("cid", sorted(EDITED))
def test_classical_citations_are_structured_and_name_a_source(cid):
    row = _after(cid)
    cites = row["classical_citations"]
    assert cites and not jsonb_citation_lacks_source(cites), cid
    assert not citation_lacks_source(row["source_citation"]), cid                 # the ontology text column
    assert "classical_tradition" not in str(cites) and "classical tradition (Jyotish)" not in row["source_citation"]
    for c in cites:
        assert c["kind"] in ("K1", "K2", "K1_UNVERIFIED", "K1_ANALOGUE"), (cid, c["kind"])
        if c["kind"] in ("K1", "K1_ANALOGUE"):
            assert c["text_id"] in CORPUS_TEXTS and K1_LOCUS.match(c["locus"]) and c["human_locus"].strip() and c["excerpt"].strip(), (cid, c)
        if c["kind"] == "K1_ANALOGUE":
            assert c["relation"] == "classical analogue, not the source of this rule"
        if c["kind"] == "K2":
            assert c["decision_id"] == K2_ID and c["label"] == "modern practice / project judgment"
        if c["kind"] == "K1_UNVERIFIED":
            assert c["claimed_text"].strip()


@pytest.mark.parametrize("cid", sorted(EDITED))
def test_json_array_and_ontology_text_carry_the_same_segments(cid):
    row = _after(cid)
    segs = row["source_citation"].split(" ; ")
    kinds = [re.match(r"^(K1_ANALOGUE|K1_UNVERIFIED|K1|K2|NAME COLLISION|name is modern)", s).group(1) for s in segs]
    kinds = ["K2" if k == "name is modern" else k for k in kinds]                 # SS ruling 5: the appended '; name is modern (OS-2026-10-05-CITATIONS)' segment is the K2 name flag
    assert [k for k in kinds if k != "NAME COLLISION"] == [c["kind"] for c in row["classical_citations"]]
    assert kinds.count("NAME COLLISION") == sum(1 for c in row["classical_citations"] if "name_collision" in c)


def test_decision_classes_carry_the_expected_citation_kinds():
    for cid in APPLY_K1 | FIX_K1:
        assert _after(cid)["classical_citations"][0]["kind"] == "K1", cid
    for cid in UNVERIFIED:
        kinds = [c["kind"] for c in _after(cid)["classical_citations"]]
        assert kinds == (["K1_UNVERIFIED", "K2"] if cid in NAME_FLAG else ["K1_UNVERIFIED"]), cid
    for cid in LABEL_K2 | FIX_K2:
        assert _after(cid)["classical_citations"][0]["kind"] == "K2", cid
    assert [c["kind"] for c in _after("pitra_dosha_sun_12th_malefic")["classical_citations"]] == ["K2", "K1_ANALOGUE", "K1_ANALOGUE"]
    assert [c["kind"] for c in _after("mrityu_bhaga_dosha")["classical_citations"]] == ["K1", "K1_UNVERIFIED", "K2"]
    assert [c["kind"] for c in _after("dhaiya")["classical_citations"]] == ["K1", "K2"]


# ---- school -----------------------------------------------------------------------------------------------------------

def test_school_modern_only_where_the_doctrine_is_modern():
    modern = {"angarak", "chandal_yoga_dosha", "chandra_grahan_dosha", "guru_chandal", "kala_amrita_dosha", "kala_sarpa", "lagna_lord_grahan_dosha", "naga_dosha_nodes_kendra",
              "naga_dosha_rahu_lagna", "pitra_dosha_9th_lord_afflicted", "pitra_dosha_sun_12th_malefic", "pitra_dosha_sun_rahu", "pitra_dosha_sun_saturn_conjunction",
              "pitru_dosha", "punarphoo", "shrapit_dosha", "surya_grahan_dosha", "grahan"}
    assert len(modern) == 18
    for cid, row in AFTER.items():
        assert row["school"] == ("modern" if cid in modern else "parashari"), cid
    assert _after("sade_sati")["school"] == "parashari" and _after("dhaiya")["school"] == "parashari"       # decision record 3.5


# ---- content corrections ----------------------------------------------------------------------------------------------

def test_kala_sarpa_carries_the_twelve_names_and_no_variant_rows_remain():
    names = AFTER["kala_sarpa"]["formation_rule_jsonb"]["variant_names_by_rahu_house"]
    assert names == {"1": "Anant", "2": "Kulik", "3": "Vasuki", "4": "Shankhpal", "5": "Padma", "6": "Mahapadma", "7": "Takshak", "8": "Karkotak", "9": "Shankhachud",
                     "10": "Ghatak", "11": "Vishdhar", "12": "Sheshnag"}
    assert AFTER["kala_sarpa"]["formation_rule_jsonb"]["requires"] == BEFORE["kala_sarpa"]["formation_rule_jsonb"]["requires"]
    assert not [c for c in AFTER if c.startswith("kala_sarpa_")]


def test_punarphoo_absorbs_vish_dosha():
    p = AFTER["punarphoo"]
    assert p["name_en"] == 'Moon–Saturn conjunction/aspect (Punarphoo; popularly "Vish dosha")' and p["name_sa"] == "Candra-Śani-yuti (Punarphū)"
    assert p["ontology_synonyms"] == ["vish_dosha", "Vish Dosha", "Punarphoo", "Chandra-Shani yuti"]
    assert p["effects_text"] == BEFORE["punarphoo"]["effects_text"] and p["formation_rule_jsonb"] == BEFORE["punarphoo"]["formation_rule_jsonb"]
    assert "vish_dosha" not in AFTER
    assert "NAME COLLISION" in p["source_citation"] and any("name_collision" in c for c in p["classical_citations"])
    assert [d for d in AFTER.values() if d.get("ontology_synonyms")] == [p]


def test_kemadruma_compat_kuja_is_renamed():
    n = AFTER[RENAME_NEW]
    assert RENAME_OLD not in AFTER and n["name_sa"] == "Śukrāt Kuja-doṣa" and n["name_en"] == BEFORE[RENAME_OLD]["name_en"]
    assert n["formation_rule_jsonb"] == BEFORE[RENAME_OLD]["formation_rule_jsonb"] and n["school"] == "parashari"
    assert [c["kind"] for c in n["classical_citations"]] == ["K1_UNVERIFIED", "K2"]


def test_chandra_grahan_formation_is_the_well_formed_shape():
    assert AFTER["chandra_grahan_dosha"]["formation_rule_jsonb"] == {"conjunction": [["Moon", "Rahu"], ["Moon", "Ketu"]]}      # one spelling family (migration 1361)
    assert "or" not in AFTER["chandra_grahan_dosha"]["formation_rule_jsonb"]


def test_daridra_is_the_bphs_ch42_rule_without_the_unsourced_one():
    d = AFTER["daridra"]
    assert [list(x)[:1] for x in d["formation_rule_jsonb"]["any_of"]] == [["lagna_lord_in_house"], ["lagna_lord_in_house"], ["lagna_or_moon_with"], ["lagna_lord_with_malefic_in_house"]]
    assert "11th lord" not in d["formation_text"] and "11th lord" not in str(d["formation_rule_jsonb"])
    assert d["severity_grades"] == {"severe": "any BPHS Ch.42 combination present (the text gives no gradation)"}
    assert len(d["cancellation_conditions"]["bhanga"]) == 1 and "K2" in d["cancellation_conditions"]["bhanga"][0]


def test_mrityu_bhaga_formation_text_splits_moon_from_planet_table():
    t = AFTER["mrityu_bhaga_dosha"]["formation_text"]
    assert "26,12,13,25,24,11,26,14,13,25,5,12" in t and "not verified in our library" in t


def test_abhukta_mula_window_and_gana_nadi_bhakoot_mool_corrections():
    a = AFTER["abhukta_mula_dosha"]
    assert a["formation_rule_jsonb"]["window"] == {"jyeshtha_last_ghatis": {"bphs_ch92_s5": 6, "mc_v54_narada": 5}, "mula_first_ghatis": 8}
    assert a["cancellation_conditions"] == {"mitigation": ["śānti after the 12th day (BPHS Ch.93 §3-4)"]}
    g = AFTER["gana_dosha"]
    assert "worst when Deva-bride" not in g["formation_text"] and set(g["severity_grades"]) == {"severe", "moderate", "mild", "none"}
    assert g["formation_rule_jsonb"]["points"] == {"same_gana": 6, "deva_manushya": 5, "deva_or_manushya_with_rakshasa": 0}
    n = AFTER["nadi_dosha"]
    assert set(n["formation_rule_jsonb"]["nadi_lists_mc_v34"]) == {"adya", "madhya", "antya"}
    assert all(len(v) == 9 for v in n["formation_rule_jsonb"]["nadi_lists_mc_v34"].values())
    assert set(n["severity_grades"]) == {"severe", "moderate"} and len(n["cancellation_conditions"]["bhanga"]) == 3
    b = AFTER["bhakoot_dosha"]
    assert list(b["formation_rule_jsonb"]["rashi_distance"]) == ["6-8", "5-9", "2-12"] and len(b["cancellation_conditions"]["bhanga"]) == 5
    assert "nāḍī-śuddhi must hold in every case" in b["cancellation_conditions"]["note"]
    m = AFTER["mool_dosha"]
    assert "27th-day" in m["effects_text"] and "is not in the texts" in m["effects_text"] and m["severity_grades"]["mula_pada"]["1"] == "father"
    assert m["severity_grades"]["mild"].endswith("(K2 project grading)")


# ---- ontology / reference projections (derived by seed_doshas from the one list) ---------------------------------------

def test_ontology_projection_inherits_the_dosha_rows_name_description_and_source():
    for cid, d in AFTER.items():
        desc = d["effects_text"][:200] if d.get("effects_text") else None
        assert desc is None or len(desc) <= 200
        assert d.get("source_citation")                                    # the ontology text column is present on every row, edited or not
    for cid in EDITED:
        d = _after(cid)
        assert d["source_citation"].startswith(("K1 — ", "K2 — ", "K1_UNVERIFIED — ")), cid



def test_name_is_modern_segment_is_appended_to_exactly_the_20_rows_k1_part_intact():
    assert len(NAME_FLAG) == 20 and NAME_FLAG <= EDITED
    suffix = " ; name is modern (OS-2026-10-05-CITATIONS)"
    for cid in EDITED:
        row = _after(cid)
        has = row["source_citation"].endswith(suffix)
        assert has == (cid in NAME_FLAG), cid
        if has:
            body = row["source_citation"][: -len(suffix)]
            assert not citation_lacks_source(body) and body.startswith(("K1 — ", "K1_UNVERIFIED — ")), cid      # the K1 / K1_UNVERIFIED part is intact and first
            last = row["classical_citations"][-1]
            assert last == {"kind": "K2", "decision_id": K2_ID, "label": "modern practice / project judgment", "note": "name is modern"}, cid
            assert row["classical_citations"][0]["kind"] in ("K1", "K1_UNVERIFIED")
