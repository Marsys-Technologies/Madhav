"""test_e6_1_declarations.py — E6.1 declarations packet (N-22 ruling; SS decisions 2026-09-30).

`asset_declarations.json` holds per asset the declared FACTS `kind`, `carriage`, `prose_fields` (+ evidence
pointers); `load_asset_declarations()` reads and validates it; `facts_for_asset(record, declarations)` merges the
declared facts under `declared_*` keys. Declarations are facts only: no criterion, N/A rule or verdict changes,
a declared kind that disagrees with the registry is REPORTED (never preferred), and an absent asset or a null
field is UNKNOWN. Offline: no database.
"""
from __future__ import annotations

import ast
import copy
import hashlib
import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import _narr_writer_checks as nw  # noqa: E402

FIXTURE = json.loads((HERE / "fixtures" / "census_cells_2026-09-30.json").read_text(encoding="utf-8"))
REGISTRY_IDS = sorted(a for assets in FIXTURE["layers"].values() for a in assets)


PEV = dict(prose_fields="writer file.py:1: composed / stores source text")   # a non-blank evidence pointer


def _doc(**assets):
    return dict(version="1.0.0", kind_enum=list(ac.DECLARED_KINDS), assets=assets)


def _write(tmp_path, doc, raw=None):
    p = tmp_path / "decl.json"
    p.write_text(raw if raw is not None else json.dumps(doc), encoding="utf-8")
    return p


def _digest(o):
    # digests, not the documents: a failing equality on multi-MB JSON makes pytest's string diff run for minutes
    return hashlib.sha256(json.dumps(o, sort_keys=True).encode()).hexdigest()


def _fixture_census():
    out = {}
    for layer, assets in FIXTURE["layers"].items():
        out[layer] = dict(layer=layer, assets=[
            dict(asset_id=aid, layer=layer, measurements={c: dict(v=v if isinstance(v, str) else v[0], measured="")
                                                          for c, v in ms.items()})
            for aid, ms in assets.items()])
    return out


# ───────────────────────── (1) the committed file ─────────────────────────

def test_committed_file_loads_and_covers_exactly_the_127_census_assets():
    decl = ac.load_asset_declarations(registry_ids=REGISTRY_IDS)
    assert len(REGISTRY_IDS) == 127
    assert sorted(decl) == REGISTRY_IDS


def test_committed_file_kinds_are_in_the_enum_and_multi_table_is_not_a_kind():
    assert ac.DECLARED_KINDS == ("data", "service", "view", "static", "rider", "probe", "user_data")
    decl = ac.load_asset_declarations()
    assert {e["kind"] for e in decl.values()} <= set(ac.DECLARED_KINDS) | {None}
    assert "multi-table" not in ac.DECLARED_KINDS and "artifact" not in ac.DECLARED_KINDS


def test_committed_file_pins_the_ruled_kinds():
    decl = ac.load_asset_declarations()
    assert decl["lel_events"]["kind"] == "user_data"          # ruling, principle 6
    assert decl["bo_samvada"]["kind"] == "view"
    assert {a for a, e in decl.items() if e["kind"] == "static"} == {"bg_gochara_citation_resolution", "bg_sarvatobhadra_grid"}
    assert {a for a, e in decl.items() if e["kind"] == "rider"} == {"bg_sign_medical", "bg_transit_engine", "bg_nakshatra_medical"}
    # the two user-table services: neither writes a table of its own (code evidence in the evidence pointer)
    assert decl["mi_abhilekha"]["kind"] == "service" and decl["mi_seva"]["kind"] == "service"
    assert "ga_strength" in decl and decl["ga_strength"]["kind"] == "data"   # multi-table is a measurement, not a kind


def test_committed_file_leaves_the_undecidable_asset_undeclared():
    assert ac.load_asset_declarations()["mi_vistara"]["kind"] is None


def test_every_non_data_declared_kind_carries_an_evidence_pointer():
    for aid, e in ac.load_asset_declarations().items():
        if e["kind"] != "data":
            assert e["evidence"] and e["evidence"]["kind"], aid
        if e["prose_fields"] is not None:
            assert e["evidence"]["prose_fields"], aid


# ───────── E6.1 narr: prose_fields ([] positive declaration, `column.$.path`, evidence on every declaration) ─────────
# SS ruling 2026-10-01: Narr (CLAUDE.md N.7) concerns GENERATED prose. null = undeclared; [] = declared "this asset's
# writer composes none" (needs evidence); a JSONB narrative is declared as `column.$.key(.key)*`.

def test_parse_prose_field_splits_a_column_from_its_json_path():
    assert ac.parse_prose_field("narrative") == ("narrative", None)
    assert ac.parse_prose_field("narrative.$.headline") == ("narrative", ("headline",))
    assert ac.parse_prose_field("falsifiability.$.confirm_observable") == ("falsifiability", ("confirm_observable",))
    assert ac.parse_prose_field("n.$.a.b_2.c") == ("n", ("a", "b_2", "c"))
    assert ac.parse_prose_field("_c1.$._k") == ("_c1", ("_k",))


@pytest.mark.parametrize("bad", ["", " ", "narrative.$", "$.x", "n.x", "n.$..x", "n.$.a b", "n.$.a[0]", "n.$.*", "n.$.1a",
                                 "1n", "n n", "n-n", "t.n", "n\n", ".n", "n.$.x\n", "n.$.$.x", "n.$.", None, 1, ["n"]])
def test_parse_prose_field_rejects_malformed_entries(bad):
    with pytest.raises(ac.DeclarationsError):
        ac.parse_prose_field(bad)


def test_parse_prose_field_accepts_an_array_element_segment_after_an_identifier_key():
    # grammar 1.6.0 (SS ruling 2026-10-01): `key[*]` = every element of the array at `key`; the path tuple carries the
    # wildcard as the token "[*]" (never a valid identifier, so it cannot collide with a JSON key)
    assert ac.parse_prose_field("d.$.a[*].b") == ("d", ("a", "[*]", "b"))
    assert ac.parse_prose_field("derivation.$.factor_ledger[*].connections[*].reason") == (
        "derivation", ("factor_ledger", "[*]", "connections", "[*]", "reason"))
    assert ac.parse_prose_field("d.$.a.b[*].c") == ("d", ("a", "b", "[*]", "c"))
    assert ac.parse_prose_field("d.$.items[*]") == ("d", ("items", "[*]"))         # an array of strings
    assert ac.parse_prose_field("d.$.a[*].b[*]") == ("d", ("a", "[*]", "b", "[*]"))
    assert ac.parse_prose_field("d.$.a.b") == ("d", ("a", "b"))                    # unchanged


@pytest.mark.parametrize("bad", [
    "d[*]", "d[*].$.a", "d.$[*].a", "d.$.[*]", "d.$.a[*][*]", "d.$.a[*][*].b", "d.$.a[0]", "d.$.a[0].b", "d.$.a[1]",
    "d.$.a[-1].b", "d.$.a[ * ].b", "d.$.a[**].b", "d.$.a[*.b", "d.$.a*].b", "d.$.a[].b", "d.$.a[*]b", "d.$.a[*]x.b",
    "d.$.a[*]..b", "d.$.a[*].", "d.$.a[*]\n", "d.$.a[*].b\n", "d.$.a.[*].b", "d.$.[*].b", "d.$.a[*] .b", "d.$.a [*].b",
    "d.$.a[\uff0a].b", "d.$.a[*]\u200b.b", "d.$.a[*].b[*", "d.$.a[n].b", "d.$.a['x'].b", "d.$.a[*:].b", "d.$.a[?(@.x)].b",
    "d.$.*.b", "d.$.a[*].*", "d.$.a[*].1b", "d.$.a[*]$.b", "d.$..a[*]", "d.$.a[*],d.$.b"])
def test_parse_prose_field_rejects_malformed_wildcards(bad):
    with pytest.raises(ac.DeclarationsError):
        ac.parse_prose_field(bad)


def test_wildcard_identifiers_keep_the_128_character_cap():
    ok = "c" * 128 + ".$." + "k" * 128 + "[*]." + "m" * 128
    assert ac.parse_prose_field(ok) == ("c" * 128, ("k" * 128, "[*]", "m" * 128))
    for bad in ("c.$." + "k" * 129 + "[*].m", "c.$.k[*]." + "m" * 129):
        with pytest.raises(ac.DeclarationsError):
            ac.parse_prose_field(bad)


def test_a_wildcard_path_overlaps_its_non_wildcard_parent_and_its_own_prefixes(tmp_path):
    for a, b in (("d.$.x", "d.$.x[*].y"), ("d.$.x[*]", "d.$.x[*].y"), ("d.$.x", "d.$.x[*]"), ("d.$.x[*].y", "d.$.x[*].y"),
                 ("d.$.x[*].y", "d.$.x"), ("d", "d.$.x[*].y"), ("D.$.X[*].y", "d.$.x"), ("d.$.x[*].y[*]", "d.$.x[*].y")):
        with pytest.raises(ac.DeclarationsError, match="overlap"):
            ac.validate_declarations(_doc(a=dict(prose_fields=[a, b], evidence=PEV)))
    # siblings under one array, different arrays, and an array vs an object of the same key are NOT overlaps
    ac.validate_declarations(_doc(a=dict(prose_fields=["d.$.x[*].y", "d.$.x[*].z", "d.$.w[*].y", "d.$.x.y", "d.$.xy[*].y",
                                                      "e.$.x[*].y"], evidence=PEV)))
    ac.validate_declarations(_doc(a=dict(prose_fields=["d.$.x[*].y", "d.$.x[*].y2"], evidence=PEV)))


def test_a_wildcard_entry_round_trips_through_the_loader_and_the_fact(tmp_path):
    doc = _doc(w=dict(prose_fields=["d.$.a[*].b", "d.$.a[*].c[*].e"], evidence=PEV))
    decl = ac.load_asset_declarations(_write(tmp_path, doc))
    assert decl["w"]["prose_fields"] == ["d.$.a[*].b", "d.$.a[*].c[*].e"]
    assert ac.facts_for_asset(dict(asset_id="w"), decl)["declared_prose_fields"] == ["d.$.a[*].b", "d.$.a[*].c[*].e"]
    for bad in ("d.$.a[0].b", "d.$.a[*][*].b"):
        with pytest.raises(ac.DeclarationsError, match="prose_fields"):
            ac.validate_declarations(_doc(w=dict(prose_fields=[bad], evidence=PEV)))


def test_the_file_version_is_1_6_0():
    assert json.loads((HERE.parent / "asset_declarations.json").read_text(encoding="utf-8"))["version"] == "1.6.0"


def test_empty_prose_list_is_a_valid_positive_declaration_distinct_from_null(tmp_path):
    doc = _doc(none=dict(prose_fields=None),
               empty=dict(prose_fields=[], evidence=dict(prose_fields="stores source text; generates none (w.py:10)")),
               some=dict(prose_fields=["a", "b"], evidence=PEV),
               paths=dict(prose_fields=["n.$.a", "n.$.b", "other", "m.$.k.l"], evidence=PEV),
               absent_field=dict(kind="data"))
    decl = ac.load_asset_declarations(_write(tmp_path, doc))
    assert decl["none"]["prose_fields"] is None
    assert decl["empty"]["prose_fields"] == [] and decl["empty"]["prose_fields"] is not None
    assert decl["absent_field"].get("prose_fields") is None
    assert decl["paths"]["prose_fields"] == ["n.$.a", "n.$.b", "other", "m.$.k.l"]
    f = {aid: ac.facts_for_asset(dict(asset_id=aid), decl) for aid in decl}
    assert "declared_prose_fields" not in f["none"] and "declared_prose_fields" not in f["absent_field"]
    assert f["empty"]["declared_prose_fields"] == [] and "declared_prose_fields" in f["empty"]
    assert f["some"]["declared_prose_fields"] == ["a", "b"]
    assert f["paths"]["declared_prose_fields"] == ["n.$.a", "n.$.b", "other", "m.$.k.l"]


@pytest.mark.parametrize("blank", ["", " ", "\t\n", "\u200b", "\u200c\u200d", "\u2060", "\ufeff", "\u180e", "\u00a0", "\u2003",
                                   "\u3000", "\u202f", "\x00", "\x7f", "\u200b \u00a0\ufeff", "\u2028", "\u2029"])
@pytest.mark.parametrize("prose", [["x"], []])
def test_blank_evidence_is_named_as_blank_not_just_rejected_for_lacking_a_path(blank, prose):
    with pytest.raises(ac.DeclarationsError, match="non-blank pointer"):
        ac.validate_declarations(_doc(a=dict(prose_fields=prose, evidence=dict(prose_fields=blank))))


def test_visible_evidence_is_not_blank():
    for ok in ("a", "w.py:1", "\u200bw.py:1\u200b", " x "):
        assert not ac._blank_text(ok)
    assert ac._blank_text("") and ac._blank_text("\u200b\u00a0")


def test_evidence_shapes_identifier_cap_and_ddl_marker_accepted():
    ok = [dict(prose_fields=["x"], evidence=dict(prose_fields="w.py:1")),
          dict(prose_fields=["x"], evidence=dict(prose_fields="platform/src/lib/a/b.ts:12 and c.tsx:3")),
          dict(prose_fields=["x"], evidence=dict(prose_fields="migrations/001_baseline.sql (line 469) and w.py:2")),
          dict(prose_fields=["x"], evidence_kind="writer", evidence=dict(prose_fields="w.py:2")),
          dict(prose_fields=[], evidence=dict(prose_fields="stores source text; generates none; w.py:10")),
          dict(prose_fields=["c" * 128, "d.$." + "k" * 128 + "." + "m" * 128], evidence=PEV),
          dict(prose_fields=["x"], evidence_kind="ddl", evidence=dict(prose_fields="TEXT in DDL (325_l2_bodha_enriched_schema.sql)")),
          dict(prose_fields=["x"], evidence_kind="ddl", evidence=dict(prose_fields="a.sql:1 and 001_b.sql")),
          dict(prose_fields=None, evidence=dict(prose_fields=None)),
          dict(prose_fields=None, evidence=None, evidence_kind=None),
          dict(prose_fields=["x"], evidence_kind=None, evidence=PEV)]
    for i, entry in enumerate(ok):
        ac.validate_declarations(_doc(**{f"a{i}": entry}))


def test_sibling_paths_of_one_column_and_same_name_paths_of_two_columns_are_not_overlaps():
    ac.validate_declarations(_doc(a=dict(prose_fields=["n.$.a", "n.$.b", "m.$.a", "n.$.ab"], evidence=PEV)))


def test_empty_prose_list_reaches_no_criterion():
    assert ac.facts_for_asset(dict(asset_id="empty"), DECL)["declared_prose_fields"] == []
    base = dict(asset_kind="data")
    for crit in ac.CRITERION_REGISTRY:
        for layer in ac.ALL_LAYERS:
            assert (ac.criterion_applicability(crit, layer, dict(base, declared_prose_fields=[]))
                    == ac.criterion_applicability(crit, layer, base)), (crit, layer)


# Decisions recorded 2026-10-01 (evidence: /Users/Dev/suvarna-evidence/E6.1/narr_declarations_evidence.md). Each
# declaration cites the writer code (file:line) and the test re-reads that line, so a moved/edited writer fails loudly;
# the JSONB/plain columns are additionally checked structurally (AST, _narr_writer_checks.py), not by a word search.
_SC = "platform/python-sidecar/"
_WR = _SC + "pipeline/orchestrator/writers/"
_BG = _SC + "brahmagyan/"
_L = "platform/src/lib/retrieval/registry/layers/"
NARR_DECLARED = {
    "bg_doshas": [],
    "bg_remedies": ["prescription_text", "charity_action"],
    "bg_compendium_index": ["significance"],
    "ka_kala_darshana": ["narrative.$.headline", "narrative.$.context", "narrative.$.caution"],
    "ka_jivana_parva": ["narrative.$.summary"],
    "ka_bhavishya_lekha": ["narrative.$.headline", "narrative.$.probability_statement", "narrative.$.domain_context",
                           "narrative.$.caveat", "falsifiability.$.confirm_observable", "falsifiability.$.deny_observable"],
    "bo_upaya": ["prescription_detail_jsonb.$.maraka_contraindication_verdict.reason"],
    "ka_vighnakara": ["obstruction_detail.$.reason"],
    "ka_avadhi": ["dossier.$.sublord_modulation.note"],
    "ph_nimitta": ["falsifier"],
    "ph_rectification": ["judgment_flags.$.load_bearing_note", "leakage_firewall_note"],
    "mi_pariksha": ["statement"],
    "bo_pratijna": ["derivation.$.factor_ledger[*].detail", "derivation.$.denials[*].reason",
                    "derivation.$.factor_ledger[*].connections[*].reason"],
    "bg_yogas": [],
    "bg_ontology": [],
}
# declared `[]` (writer composes no NARRATION; the evidence carries the AST-backed reason). SS ruling 2026-10-01: a composed
# string is narration only if it states or grades a computed value; provenance pointers, ordinals, labels are not.
NARR_EMPTY = ("bg_doshas", "bg_yogas", "bg_ontology")
# the 13 earlier declarations were re-audited against writer code (test_e6_1_narr_reaudit.py): 11 kept with writer evidence
# (no `ddl` marker), 2 removed (null). The marker is gone from all 13.
PRIOR_REAUDIT_NULLED = {"mi_bhavisya", "ph_pramana"}
PRIOR_DDL = {"bo_anveshana", "bo_arudha", "bo_laksana", "bo_nakshatra_semantic", "bo_special_lagna", "bo_sudarshana",
             "bo_vargottama_dhana", "mi_bhavisya", "mi_darshana", "ph_muhurta", "ph_pramana", "ph_sankrama", "ph_sodhana"}
# (file, line, a substring that line must contain): the code that composes (or, for bg_doshas, loads verbatim) it, and the
# served read. The evidence text must carry `<basename>:<line>` for every cite.
NARR_CITES = {
    "bg_doshas": [(_BG + "l0_doshas.py", 1972, 'd["formation_text"]'), (_BG + "l0_doshas.py", 1973, 'd["effects_text"]'),
                  (_BG + "l0_doshas.py", 2003, '["effects_text"][:200]')],
    "bg_remedies": [(_BG + "l0_remedy_corpus.py", 247, "text = ("), (_BG + "l0_remedy_corpus.py", 309, 'f"Donate {item} on {d[\'day\']}."'),
                    (_BG + "l0_remedy_corpus.py", 2236, "prescription = (")],
    "bg_compendium_index": [(_WR + "bg_compendium_index.py", 97, 'f"{text_id} chapter {chapter_num}: {len(rows)} passage(s)"'),
                            (_WR + "bg_compendium_index.py", 109, 'f"{text_id} covers {topic_id} in {len(rows)} passage(s)"')],
    "ka_kala_darshana": [(_WR + "ka_kala_darshana.py", 107, "_build_narrative("), (_WR + "ka_kala_darshana.py", 138, "obstruction_summary, narrative"),
                         (_WR + "ka_kala_darshana.py", 234, "'headline': headline"),
                         (_L + "L3_kala/query_temporal_view.ts", 86, "obstruction_summary, narrative")],
    "ka_jivana_parva": [(_WR + "ka_jivana_parva.py", 185, "_build_parva_narrative("), (_WR + "ka_jivana_parva.py", 432, "summary = ("),
                        (_L + "L3_kala/query_life_arc.ts", 152, "narrative, source_citation")],
    "ka_bhavishya_lekha": [(_WR + "ka_bhavishya_lekha.py", 323, "_build_projection_narrative("),
                           (_WR + "ka_bhavishya_lekha.py", 317, "_build_falsifiability("),
                           (_WR + "ka_bhavishya_lekha.py", 528, "confirm = f"), (_WR + "ka_bhavishya_lekha.py", 529, "deny = f"),
                           (_L + "L3_kala/query_projections.ts", 248, "narrative,")],
    "bo_upaya": [(_WR + "bo_upaya.py", 1008, "reason = ("), (_WR + "bo_upaya.py", 1690, '"maraka_contraindication_verdict": maraka_verdict'),
                 (_L + "L2_bodha/query_remedies.ts", 404, "prescription_detail_jsonb"),
                 (_L + "L2_bodha/query_remedies.ts", 564, "marakaVerdictFrom(r['prescription_detail_jsonb'])")],
    "ka_vighnakara": [(_WR + "ka_vighnakara.py", 553, "'reason': f\"Saturn in adversarial transit window"), (_WR + "ka_vighnakara.py", 589, "'reason': ("),
                      (_WR + "ka_vighnakara.py", 644, "'reason': f\"Tithi"), (_WR + "ka_vighnakara.py", 695, "'reason': ("),
                      (_WR + "ka_vighnakara.py", 773, "'reason': ("), (_WR + "ka_vighnakara.py", 829, "'reason': f\"{planet_str} combust"),
                      (_WR + "ka_vighnakara.py", 241, "json.dumps(obs['detail'])"),
                      (_L + "L3_kala/query_obstruction_periods.ts", 80, "obstruction_detail")],
    "ka_avadhi": [(_WR + "ka_avadhi.py", 293, '"note": f"AD lord {sublord} modulates MD lord {lord}."'),
                  (_WR + "ka_avadhi.py", 303, '"dossier": json.dumps(dossier)'),
                  (_L + "L3_kala/query_dasha_dossier.ts", 92, "dossier, quality")],
    "ph_nimitta": [(_SC + "services/ph_nimitta/engine.py", 237, "def as_text"), (_SC + "services/ph_nimitta/engine.py", 552, "falsifier=sf.as_text()"),
                   (_WR + "ph_nimitta.py", 279, "a.falsifier"), (_L + "L4_phala/query_predictive_anchors.ts", 137, "falsifier, source_citation")],
    "ph_rectification": [(_SC + "services/ph_rectification/engine.py", 555, "firewall_note = ("),
                         (_WR + "ph_rectification/__init__.py", 74, 'flags["load_bearing_note"] = ('),
                         (_WR + "ph_rectification/__init__.py", 392, "[basis={basis}] {best.leakage_firewall_note}"),
                         (_L + "L4_phala/query_phala_calibration.ts", 644, "judgment_flags"),
                         (_L + "L4_phala/query_phala_calibration.ts", 646, "leakage_firewall_note")],
    "bo_pratijna": [(_WR + "bo_pratijna_v4_engine.py", 310, 'f"sign={sign_number} matches exaltation_sign"'),
                    (_WR + "bo_pratijna_v4_engine.py", 410, "naisargika-only (tatkalika unavailable)"),
                    (_WR + "bo_pratijna_v4_engine.py", 425, "naisargika({graha}->{need.sign_lord})"),
                    (_WR + "bo_pratijna_v4_engine.py", 945, '"detail": f"DATA GAP: {exc}'),
                    (_WR + "bo_pratijna_v4_engine.py", 574, "house_lord={house_lord_dig.state}"),
                    (_WR + "bo_pratijna_v4_engine.py", 624, "core lord ({core_lord_graha}) D1 house="),
                    (_WR + "bo_pratijna_v4_engine.py", 655, "core lord ({core_lord_graha}) debilitated in its own cited dusthana house"),
                    (_WR + "bo_pratijna_v4_engine.py", 679, "malefic-occupied={before_malefic}"),
                    (_WR + "bo_pratijna_v4_engine.py", 696, "adjoining core house {core_house}"),
                    (_WR + "bo_pratijna_v4_engine.py", 738, "(core lord) placed in house"),
                    (_WR + "bo_pratijna_v4_engine.py", 753, "no lord-in-house/full-contact/parivartana connection"),
                    (_WR + "bo_pratijna_v4_engine.py", 774, '"reason": "no D1 house data"'),
                    (_WR + "bo_pratijna_v4_engine.py", 1033, "return ClassScore("),
                    (_WR + "bo_pratijna.py", 407, '"factor_ledger": score.factor_ledger'),
                    (_WR + "bo_pratijna.py", 408, '"denials": score.denials'),
                    (_WR + "bo_pratijna.py", 428, '"derivation": json.dumps(derivation)'),
                    (_WR + "bo_pratijna.py", 401, '"status_mapping_rule": ('),
                    (_WR + "bo_pratijna.py", 378, '"reason": "no KaryatvaMap registered'),
                    (_L + "L2_bodha/query_pratijna.ts", 159, "derivation, formula_version")],
    "bg_yogas": [(_BG + "l0_yogas.py", 2057, 'name_en = base_name + " Yoga"'), (_BG + "l0_yogas.py", 2140, 'f"{name_en}: formation per {verse_ref}'),
                 (_BG + "l0_yogas.py", 2156, '"source_citation": f"{text_id.upper()} Ch.{chapter} ({verse_ref})"'),
                 (_BG + "l0_yogas.py", 2272, 'y["formation_text"]'), (_BG + "l0_yogas.py", 2310, 'y["significations_text"][:150]'),
                 (_L + "L0_brahmagyan/query_yoga_catalog.ts", 57, "SELECT * FROM brahma_yoga_catalog")],
    "bg_ontology": [(_BG + "l0_ontology.py", 145, 'f"nak_{nak_id:02d}_'), (_BG + "l0_ontology.py", 147, 'f"Nakshatra {nak_id}/27"'),
                    (_BG + "l0_ontology.py", 171, 'f"Sign {sign_id}/12"'), (_BG + "l0_ontology.py", 215, 'f"HOUSE_{house_num:02d}"'),
                    (_BG + "l0_ontology.py", 219, 'f"house_{house_num:02d}"'), (_BG + "l0_ontology.py", 977, 'code = f"D{n}"'),
                    (_BG + "l0_ontology.py", 981, 'f"d{n}"'), (_BG + "l0_ontology.py", 1152, 'e.get("description")'),
                    (_L + "L0_brahmagyan/resolve_entity.ts", 65, "synonyms, description, source_citation")],
    "mi_pariksha": [(_WR + "mi_pariksha.py", 251, 'f"Retrodiction probe for {event_id}'), (_WR + "mi_pariksha.py", 729, "statement = ("),
                    (_L + "L5_mimamsa/query_mimamsa_discoveries.ts", 86, "statement")],
}
# JSONB narrative paths: the builder function whose returned dict literal must carry every declared key
NARR_JSON_BUILDERS = {
    ("ka_kala_darshana", "narrative"): (_WR + "ka_kala_darshana.py", "_build_narrative"),
    ("ka_jivana_parva", "narrative"): (_WR + "ka_jivana_parva.py", "_build_parva_narrative"),
    ("ka_bhavishya_lekha", "narrative"): (_WR + "ka_bhavishya_lekha.py", "_build_projection_narrative"),
    ("ka_bhavishya_lekha", "falsifiability"): (_WR + "ka_bhavishya_lekha.py", "_build_falsifiability"),
}
# keys each builder returns that are NOT prose (measured/structured values): never declared
NARR_JSON_NON_PROSE = {
    ("ka_jivana_parva", "narrative"): {"dasha_planet", "span", "quality", "high_convergence_count", "avg_effective_score"},
    ("ka_bhavishya_lekha", "falsifiability"): {"evaluation_date", "evaluation_window_days"},
}
# (asset, JSON column) -> (writer file, INSERT table) for the tuple-bound writers checked structurally
NARR_TUPLE_TABLES = {
    ("ka_kala_darshana", "narrative"): (_WR + "ka_kala_darshana.py", "kala_darshana"),
    ("ka_jivana_parva", "narrative"): (_WR + "ka_jivana_parva.py", "kala_jivana_parva"),
    ("ka_bhavishya_lekha", "narrative"): (_WR + "ka_bhavishya_lekha.py", "kala_bhavishya"),
    ("ka_bhavishya_lekha", "falsifiability"): (_WR + "ka_bhavishya_lekha.py", "kala_bhavishya"),
}


def _decl():
    return ac.load_asset_declarations()


def _read(path):
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_the_committed_file_declares_exactly_the_narr_decisions_on_top_of_the_thirteen_prior_ones():
    decl = _decl()
    got = {a: e["prose_fields"] for a, e in decl.items() if e["prose_fields"] is not None}
    assert set(got) == (PRIOR_DDL - PRIOR_REAUDIT_NULLED) | set(NARR_DECLARED)
    for a, v in NARR_DECLARED.items():
        assert got[a] == v, a
    assert sorted(a for a, v in got.items() if v == []) == sorted(NARR_EMPTY)
    n = len(PRIOR_DDL) + len(NARR_DECLARED)
    assert len(got) == n and sum(e["prose_fields"] is None for e in decl.values()) == 127 - n


def test_the_thirteen_earlier_declarations_no_longer_carry_the_ddl_marker():
    decl = _decl()
    assert {a for a, e in decl.items() if e.get("evidence_kind") == "ddl"} == set()
    for a, e in decl.items():
        assert e.get("evidence_kind") == ("writer" if e["prose_fields"] is not None else None), a


def test_every_non_ddl_declared_prose_entry_carries_a_writer_path_line_pointer():
    for aid, e in _decl().items():
        if e["prose_fields"] is None:
            continue
        for f in e["prose_fields"]:
            ac.parse_prose_field(f)
        ev = e["evidence"]["prose_fields"]
        assert isinstance(ev, str) and ev.strip(), aid
        assert ac.EVIDENCE_PATH_LINE_RE.search(ev), aid


def test_bg_doshas_empty_declaration_states_its_reason_and_the_other_reference_corpora_do_not_claim_none():
    decl = _decl()
    assert "stores source text; generates none" in decl["bg_doshas"]["evidence"]["prose_fields"]
    for a in ("bg_remedies", "bg_compendium_index"):
        assert decl[a]["prose_fields"], a            # they compose text: declared fields, never []


@pytest.mark.parametrize("asset", sorted(NARR_CITES))
def test_narr_evidence_cites_lines_that_really_contain_what_it_says(asset):
    ev = _decl()[asset]["evidence"]["prose_fields"]
    for path, line, needle in NARR_CITES[asset]:
        lines = _read(path).splitlines()
        assert line <= len(lines), (path, line)
        assert needle in lines[line - 1], (path, line, lines[line - 1])
        assert f"{path.rsplit('/', 1)[1]}:{line}" in ev, (asset, path, line)


def _returned_dict_keys(path, func):
    import ast
    tree = ast.parse(_read(path))
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == func)
    rets = [n.value for n in ast.walk(fn) if isinstance(n, ast.Return) and isinstance(n.value, ast.Dict)]
    assert len(rets) == 1, (path, func)
    return {k.value for k in rets[0].keys if isinstance(k, ast.Constant)}


@pytest.mark.parametrize("asset_col", sorted(NARR_JSON_BUILDERS))
def test_declared_json_paths_are_keys_the_writer_builder_really_returns(asset_col):
    asset, col = asset_col
    path, func = NARR_JSON_BUILDERS[asset_col]
    keys = _returned_dict_keys(path, func)
    declared = {ac.parse_prose_field(f)[1] for f in _decl()[asset]["prose_fields"]
                if ac.parse_prose_field(f)[0] == col}
    assert declared and all(len(p) == 1 for p in declared)
    declared_keys = {p[0] for p in declared}
    assert declared_keys <= keys, (declared_keys - keys)
    # every returned key is either declared prose or explicitly recorded as non-prose: a new key must be decided
    assert keys == declared_keys | NARR_JSON_NON_PROSE.get(asset_col, set()), keys ^ declared_keys


# ── structural checks (AST): the INSERT binds the declared column to the builder's output, not to a literal ──

@pytest.mark.parametrize("asset_col", sorted(NARR_TUPLE_TABLES))
def test_json_column_is_bound_by_the_insert_to_the_builders_output(asset_col):
    path, table = NARR_TUPLE_TABLES[asset_col]
    assert nw.check_tuple_json_from_builder(_read(path), table, asset_col[1], NARR_JSON_BUILDERS[asset_col][1]) == []


@pytest.mark.parametrize("asset_col", sorted(NARR_JSON_BUILDERS))
def test_every_declared_json_key_is_composed_by_code_in_the_builder(asset_col):
    import ast
    asset, col = asset_col
    path, func = NARR_JSON_BUILDERS[asset_col]
    tree = ast.parse(_read(path))
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == func)
    roots = [r.value for r in ast.walk(fn) if isinstance(r, ast.Return)]
    for f in _decl()[asset]["prose_fields"]:
        c, p = ac.parse_prose_field(f)
        if c == col:
            rep = nw.composed_report(ast.Module(body=[fn], type_ignores=[]), roots, p)
            assert rep and all(composed for _, composed in rep), (f, rep)


def test_bg_doshas_empty_claim_no_string_building_on_the_bound_columns():
    src = _read(_BG + "l0_doshas.py")
    assert nw.no_string_building_in_bound_params(src, "seed_doshas") == []
    assert nw.module_level_composition(src, "DOSHAS") == []
    w = _read(_WR + "bg_doshas.py")
    assert "seed_doshas(" in w and "f\"" not in w.split("def run", 1)[1].split("return WriterResult", 1)[0]


def test_bg_doshas_checker_kills_the_concatenation_mutant():
    src = _read(_BG + "l0_doshas.py")
    old = '                    d["effects_text"],\n'
    assert src.count(old) == 1
    mutant = src.replace(old, '                    d["effects_text"] + " Note: " + d["name_en"],\n')
    assert nw.no_string_building_in_bound_params(mutant, "seed_doshas")
    for bad in ('f"{d[\'effects_text\']} x"', 'd["effects_text"] % ()', '" ".join([d["effects_text"]])',
                'd["effects_text"].format()', 'str(d["effects_text"])'):
        assert nw.no_string_building_in_bound_params(src.replace(old, f"                    {bad},\n"), "seed_doshas"), bad


_INSERT_RENAMES = {     # (asset, column) -> (text inside the writer's INSERT column list, the same text with the column renamed)
    ("ka_kala_darshana", "narrative"): ("obstruction_summary, narrative, source_citation", "obstruction_summary, narrativ, source_citation"),
    ("ka_jivana_parva", "narrative"): ("narrative, high_convergence_count", "narrativ, high_convergence_count"),
    ("ka_bhavishya_lekha", "narrative"): ("\n                    falsifiability, source_chain, narrative,", "\n                    falsifiability, source_chain, narrativ,"),
    ("ka_bhavishya_lekha", "falsifiability"): ("\n                    falsifiability, source_chain, narrative,", "\n                    falsifiabilit, source_chain, narrative,"),
}
_BOUND_NAMES = {"narrative": ("narrative", "ad_narrative", "pd_narrative", "proj_narrative"), "falsifiability": ("falsifiability",)}


def test_checker_tuple_length_and_placeholder_width_problems():
    assert nw.check_tuple_json_from_builder(_SYNTH.replace("(1, json.dumps(n), 3)", "(1, json.dumps(n))"), "t", "narrative", "build")
    assert nw.check_tuple_json_from_builder(_SYNTH.replace("(1, json.dumps(n), 3)", "(1, json.dumps(n), 3, 4)"), "t", "narrative", "build")
    wide = _SYNTH.replace("(a, narrative, c)", "(a, narrative)").replace("VALUES (%s, %s, %s)", "VALUES (f(%s, %s), %s)").replace(
        "(1, json.dumps(n), 3)", "(1, 2, json.dumps(n))")
    assert nw.check_tuple_json_from_builder(wide, "t", "narrative", "build") == []      # narrative sits after a 2-wide expression
    assert any("placeholders" in p for p in nw.check_tuple_json_from_builder(wide, "t", "a", "build"))


def test_no_string_building_checker_reports_every_kind_and_module_corpus_checker_reports_mutation():
    base = ("import json\nDOSHAS = [{'a': 'x'}]\n"
            "def seed(conn, d):\n    with conn.cursor() as cur:\n        cur.execute(\"INSERT INTO t (a) VALUES (%s)\", (PARAM,))\n")
    assert nw.no_string_building_in_bound_params(base.replace("PARAM", 'd["a"][:5] if d else None'), "seed") == []
    for bad in ('d["a"] + "x"', 'f"{d}"', '"%s" % d["a"]', '"".join([d["a"]])', 'str(d["a"])', 'd["a"].upper()', "[x for x in d]", "(lambda: 1)()"):
        assert nw.no_string_building_in_bound_params(base.replace("PARAM", bad), "seed"), bad
    assert nw.no_string_building_in_bound_params(base.replace("(PARAM,)", "d"), "seed")          # params not a literal tuple
    assert nw.no_string_building_in_bound_params(base.replace("INSERT INTO", "DELETE FROM"), "seed")   # no INSERT seen
    assert nw.no_string_building_in_bound_params(base, "missing")
    assert nw.module_level_composition(base, "DOSHAS") == []
    for bad in ("DOSHAS.append({})", "DOSHAS += [{}]", "DOSHAS = []", "DOSHAS.extend([])", "DOSHAS.pop()"):
        assert nw.module_level_composition(base + bad + "\n", "DOSHAS"), bad
    for lit in ("[{'a': f'{1}'}]", "[{'a': 'x' + 'y'}]", "[{'a': 'x'.format()}]", "[{'a': ''.join([])}]", "[{'a': 'x' % ()}]"):
        assert nw.module_level_composition(base.replace("[{'a': 'x'}]", lit), "DOSHAS"), lit
    assert nw.module_level_composition("X = 1\n", "DOSHAS")


@pytest.mark.parametrize("asset_col", sorted(NARR_TUPLE_TABLES))
def test_bound_value_checker_kills_the_literal_and_rename_mutants(asset_col):
    asset, col = asset_col
    path, table = NARR_TUPLE_TABLES[asset_col]
    src, builder = _read(path), NARR_JSON_BUILDERS[asset_col][1]
    literal = src
    for n in _BOUND_NAMES[col]:
        literal = literal.replace(f"json.dumps({n}),", "json.dumps({}),")
    assert literal != src
    assert nw.check_tuple_json_from_builder(literal, table, col, builder), "json.dumps({}) must be caught"
    old, new = _INSERT_RENAMES[asset_col]
    assert src.count(old) == 1
    assert nw.check_tuple_json_from_builder(src.replace(old, new), table, col, builder), "renamed INSERT column must be caught"


_SYNTH = """import json
SQL = '''INSERT INTO t (a, narrative, c) VALUES (%s, %s, %s)'''
def run(conn):
    rows = []
    n = build(1)
    rows.append((1, json.dumps(n), 3))
    conn.executemany(SQL, rows)
def build(x):
    return {"k": f"v{x}"}
"""


def test_checker_helpers_on_synthetic_writers():
    good = _SYNTH
    assert nw.check_tuple_json_from_builder(good, "t", "narrative", "build") == []
    for name, bad in (("literal", good.replace("json.dumps(n)", "json.dumps({})")),
                      ("other builder", good.replace("n = build(1)", "n = other(1)")),
                      ("renamed column", good.replace("narrative, c", "narrativ, c")),
                      ("placeholder count", good.replace("VALUES (%s, %s, %s)", "VALUES (%s, %s)")),
                      ("star-arg before", good.replace("(1, json", "(*x, json")),
                      ("not appended to rows", good.replace("rows.append", "other.append")),
                      ("not executed", good.replace("conn.executemany(", "conn.fetch(")),
                      ("wrong table", good.replace("INTO t ", "INTO u "))):
        assert nw.check_tuple_json_from_builder(bad, "t", "narrative", "build"), name
    # SQL comments with parentheses and a function-valued first expression do not shift the column position
    commented = good.replace("VALUES (%s, %s, %s)", "VALUES (-- (x), it's\n f(%s, %s), %s, %s, %s)").replace(
        "(a, narrative, c)", "(a, b, narrative, c)").replace("(1, json", "(1, 1, 2, json")
    assert nw.check_tuple_json_from_builder(commented, "t", "narrative", "build") == []
    # a list filled from a loop over `rows` (the bhavishya shape) is followed; one that is not is a problem
    looped = good.replace("    conn.executemany(SQL, rows)", "    new_rows = []\n    for r in rows:\n        new_rows.append(r)\n    conn.executemany(SQL, new_rows)")
    assert "new_rows)" in looped
    assert nw.check_tuple_json_from_builder(looped, "t", "narrative", "build") == []
    unrelated = looped.replace("new_rows.append(r)", "new_rows.append((9, 9, 9))")
    assert nw.check_tuple_json_from_builder(unrelated, "t", "narrative", "build") != []


def _tree_of(path):
    import ast
    return ast.parse(_read(path))


def _composed_lines(rep):
    return sorted(ln for ln, c in rep if c), sorted(ln for ln, c in rep if not c)


def test_bo_upaya_maraka_reason_is_bound_into_the_prescription_json_and_composed():
    import ast
    src = _read(_WR + "bo_upaya.py")
    problems, vals = nw.named_bound_values(src, "bodha_rm_remedy_prescriptions", "prescription_detail_jsonb")
    assert problems == [] and len(vals) == 1
    roots = [nw.json_dumps_argument(v) for v in vals]
    assert all(r is not None for r in roots)
    composed, constant = _composed_lines(nw.composed_report(ast.parse(src), roots, ("maraka_contraindication_verdict", "reason")))
    assert composed == [1023] and constant == [989]      # the fact-missing branch is a fixed string, the verdict branches compose


def test_ka_vighnakara_every_detector_reason_is_composed_except_the_two_constant_stubs():
    import ast
    src = _read(_WR + "ka_vighnakara.py")
    assert nw.check_tuple_json_not_literal(src, "kala_obstruction", "obstruction_detail") == []
    tree = ast.parse(src)
    roots = [v for d in ast.walk(tree) if isinstance(d, ast.Dict) for k, v in zip(d.keys, d.values)
             if isinstance(k, ast.Constant) and k.value == "detail"]
    composed, constant = _composed_lines(nw.composed_report(tree, roots, ("reason",)))
    assert composed == [553, 589, 644, 695, 773, 829] and constant == [674, 730]


def test_ka_avadhi_sublord_note_is_bound_into_the_dossier_json_and_composed():
    import ast
    src = _read(_WR + "ka_avadhi.py")
    problems, vals = nw.named_bound_values(src, "kala_avadhi", "dossier")
    assert problems == [] and len(vals) == 1
    roots = [nw.json_dumps_argument(v) for v in vals]
    assert nw.composed_report(ast.parse(src), roots, ("sublord_modulation", "note")) == [(293, True)]


def test_ph_nimitta_falsifier_is_bound_to_the_anchor_and_composed_by_as_text():
    import ast
    problems, vals = nw.bound_values(_read(_WR + "ph_nimitta.py"), "phala_anchors", "falsifier")
    assert problems == [] and [ast.unparse(v) for v in vals] == ["a.falsifier"]
    tree = _tree_of(_SC + "services/ph_nimitta/engine.py")
    fn = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "as_text")
    assert any(nw.is_composed(tree, r.value) for r in ast.walk(fn) if isinstance(r, ast.Return))
    assert any(isinstance(k, ast.keyword) and k.arg == "falsifier" and isinstance(k.value, ast.Call)
               and isinstance(k.value.func, ast.Attribute) and k.value.func.attr == "as_text" for k in ast.walk(tree))


def test_ph_rectification_firewall_note_and_load_bearing_note_are_bound_and_composed():
    import ast
    w = _WR + "ph_rectification/__init__.py"
    src = _read(w)
    tree = ast.parse(src)
    problems, vals = nw.bound_values(src, "phala_rectification_best", "leakage_firewall_note")
    assert problems == [] and len(vals) == 1 and isinstance(vals[0], ast.JoinedStr)
    assert "best.leakage_firewall_note" in ast.unparse(vals[0])
    problems, vals = nw.bound_values(src, "phala_rectification_best", "judgment_flags")
    assert problems == [] and len(vals) == 1 and nw.json_dumps_argument(vals[0]).id == "flags"
    assert any(nw._called_name(v) == "_apply_discrimination_gate" for v in nw._assign_values(tree, "flags"))
    gate = next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "_apply_discrimination_gate")
    stores = [a for a in ast.walk(gate) if isinstance(a, ast.Assign) and any(
        isinstance(t, ast.Subscript) and isinstance(t.slice, ast.Constant) and t.slice.value == "load_bearing_note" for t in a.targets)]
    assert len(stores) == 1 and nw.is_composed(tree, stores[0].value)
    eng = _tree_of(_SC + "services/ph_rectification/engine.py")
    assert any(nw.is_composed(eng, v) for v in nw._assign_values(eng, "firewall_note"))
    assert any(isinstance(k, ast.keyword) and k.arg == "leakage_firewall_note" and isinstance(k.value, ast.Name)
               and k.value.id == "firewall_note" for k in ast.walk(eng))


def test_mi_pariksha_statement_is_composed_in_both_substeps_and_bound_to_the_discoveries_insert():
    import ast
    src = _read(_WR + "mi_pariksha.py")
    tree = ast.parse(src)
    problems, vals = nw.bound_values(src, "mimamsa_discoveries", "statement", expect_statements=2)
    assert problems == [] and len(vals) == 2
    assert all(nw.is_composed(tree, v) for v in vals)


# ── bo_pratijna `derivation` `[*]` paths (grammar 1.6.0): the engine composes the ledger strings, the writer binds them ──

_PJ_W, _PJ_E = _WR + "bo_pratijna.py", _WR + "bo_pratijna_v4_engine.py"
# path -> (engine class whose constructor argument is the string, composed line set, constant line set), all in _PJ_E
PRATIJNA_COMPOSED = {
    "derivation.$.factor_ledger[*].detail": ("DignityResult", "detail",
                                              [310, 313, 334, 337, 340, 410, 417, 425, 945], [318, 348, 894, 972]),
    "derivation.$.denials[*].reason": ("DenialResult", "reason",
                                        [574, 588, 595, 624, 634, 640, 647, 655, 679, 690, 696], [568, 618]),
    "derivation.$.factor_ledger[*].connections[*].reason": ("DusthanaConnection", "reason", [738, 743, 745, 751, 753], []),
}


def _pj():
    import ast
    w, e = _read(_PJ_W), _read(_PJ_E)
    wt, et = ast.parse(w), ast.parse(e)
    problems, vals = nw.named_bound_values(w, "bodha_pratijna", "derivation")
    assert problems == [] and len(vals) == 2
    roots = [nw.json_dumps_argument(v) for v in vals]
    assert all(r is not None for r in roots)
    scored = [d for r in roots if isinstance(r, ast.Name) for d in nw.dict_nodes(wt, r)]
    assert len(scored) == 1
    score_class = next(n for n in ast.walk(et) if isinstance(n, ast.FunctionDef) and n.name == "score_class")
    return wt, et, scored, score_class


def _ledger_dicts(et, scored, key, scope):
    """the element dict literals of the ledger `derivation[key]` ends up as: the writer stores `score.<key>`, the engine
    binds ClassScore(<key>=...) (a list/comprehension literal or a Name filled by `.append({...})`)"""
    import ast
    vals = nw.dict_key_values(scored, key)
    assert [ast.unparse(v) for v in vals] == [f"score.{key}"], key
    ctor = [v for _, v in nw.constructor_values(et, "ClassScore", key) if v is not None]
    assert len(ctor) == 1, key
    out = nw.list_element_dicts(et, ctor[0], scope)
    assert out, key
    return out


def _pratijna_leaf_report(path):
    import ast
    wt, et, scored, sc = _pj()
    cls, field, _, _ = PRATIJNA_COMPOSED[path]
    col, segs = ac.parse_prose_field(path)
    assert col == "derivation" and segs[1] == "[*]" and segs[-1] == field
    dicts = _ledger_dicts(et, scored, segs[0], sc)
    if len(segs) == 5:                       # factor_ledger[*].connections[*].reason
        assert segs[2] == "connections" and segs[3] == "[*]"
        inner = nw.dict_key_values(dicts, "connections")
        assert len(inner) == 1
        dicts = nw.list_element_dicts(et, inner[0], sc)
    else:
        assert len(segs) == 3
    leaves = nw.dict_key_values(dicts, field)
    assert leaves
    return nw.terminal_strings(et, leaves, {field: cls})


@pytest.mark.parametrize("path", sorted(PRATIJNA_COMPOSED))
def test_bo_pratijna_ledger_strings_are_composed_by_the_engine_and_bound_into_derivation(path):
    rep = _pratijna_leaf_report(path)
    _, _, composed, constant = PRATIJNA_COMPOSED[path]
    assert all(c is not None for _, c in rep), rep                   # every constructor binds the field
    assert [ln for ln, c in rep if c] == composed and [ln for ln, c in rep if not c] == constant, rep


def test_bo_pratijna_ledger_dict_keys_are_all_decided_and_only_the_declared_leaves_are_prose():
    import ast
    wt, et, scored, sc = _pj()
    fl = _ledger_dicts(et, scored, "factor_ledger", sc)
    den = _ledger_dicts(et, scored, "denials", sc)
    conn = nw.list_element_dicts(et, nw.dict_key_values(fl, "connections")[0], sc)
    keys = lambda ds: {k.value for d in ds for k in d.keys if isinstance(k, ast.Constant)}
    assert keys(fl) == {"slot", "house", "lord", "graha", "varga", "varga_sign", "keywords", "dignity_state", "band",
                        "weight", "contribution", "detail", "connections"}
    assert keys(den) == {"config_id", "fired", "deduction", "reason"}
    assert keys(conn) == {"house", "connected", "reason"}
    # nothing else in a ledger element is built by string composition (a new composed key must be decided)
    for ds in (fl, den, conn):
        assert nw.composed_keys(et, ds) <= {"detail"}, nw.composed_keys(et, ds)


def test_bo_pratijna_the_static_strings_stay_undeclared_because_they_are_constants():
    import ast
    wt, et, scored, sc = _pj()
    # condition_ledger[*].reason (engine :774) is one fixed string; so are status_mapping_rule and the no_evidence reason
    assert '"reason": "no D1 house data"' in _read(_PJ_E).splitlines()[773]
    cond = [d for d in ast.walk(et) if isinstance(d, ast.Dict)
            and any(isinstance(k, ast.Constant) and k.value == "malefic" for k in d.keys)]
    reasons = nw.dict_key_values(cond, "reason")
    assert reasons and all(isinstance(v, ast.Constant) and isinstance(v.value, str) for v in reasons)
    _, vals = nw.named_bound_values(_read(_PJ_W), "bodha_pratijna", "derivation")
    every = [d for v in vals for d in nw.dict_nodes(wt, nw.json_dumps_argument(v))]
    assert len(every) == 2
    for key, n in (("status_mapping_rule", 1), ("reason", 1)):
        got = nw.dict_key_values(every, key)
        assert len(got) == n and all(isinstance(v, ast.Constant) and isinstance(v.value, str) for v in got), key
    assert not any(f.startswith("derivation.$.") and f.split("$.")[1].split("[")[0] in ("condition_ledger", "status_mapping_rule", "reason")
                   for f in (_decl()["bo_pratijna"]["prose_fields"] or []))


def test_bo_pratijna_declared_paths_are_exactly_the_ones_the_engine_checks_cover():
    assert sorted(_decl()["bo_pratijna"]["prose_fields"]) == sorted(PRATIJNA_COMPOSED)
    assert sorted(NARR_DECLARED["bo_pratijna"]) == sorted(PRATIJNA_COMPOSED)


_ARRAY_SYNTH = """
from dataclasses import dataclass
@dataclass(frozen=True)
class Res:
    a: int
    b: str
    c: str
@dataclass
class Out:
    ledger: list
    note: list
def build(x):
    ledger = []
    r = Res(1, f"b{x}", "const")
    ledger.append({"k": r.b, "n": 1, "plain": "x" + str(x)})
    ledger.append({"k": "fixed"})
    return Out(ledger=ledger, note=[{"t": q.c} for q in [r]])
def other():
    return Res(a=2, c="c2", b=str(3))
def star(z):
    return Res(*z), Res(1)
"""


def test_array_leaf_helpers_follow_constructors_lists_appends_and_comprehensions():
    import ast
    t = ast.parse(_ARRAY_SYNTH)
    u = lambda v: None if v is None else ast.unparse(v)
    assert nw.dataclass_fields(t, "Res") == ["a", "b", "c"] and nw.dataclass_fields(t, "Nope") is None
    assert nw.dataclass_fields(ast.parse("class A: pass\nclass A: pass"), "A") is None             # ambiguous
    # keyword and positional binding; a call that does not bind the field (star-arg first / too few args) is (lineno, None)
    assert [(ln, u(v)) for ln, v in nw.constructor_values(t, "Res", "b")] == [(14, "f'b{x}'"), (19, "str(3)"), (21, None), (21, None)]
    assert [(ln, u(v)) for ln, v in nw.constructor_values(t, "Res", "c")] == [(14, "'const'"), (19, "'c2'"), (21, None), (21, None)]
    assert [(ln, u(v)) for ln, v in nw.constructor_values(t, "Res", "a")] == [(14, "1"), (19, "2"), (21, None), (21, "1")]
    assert nw.constructor_values(t, "Res", "zz") == [] and nw.constructor_values(t, "Nope", "b") == []
    fn = {n.name: n for n in ast.walk(t) if isinstance(n, ast.FunctionDef)}
    led = nw.constructor_values(t, "Out", "ledger")[0][1]
    dicts = nw.list_element_dicts(t, led, fn["build"])
    assert len(dicts) == 2 and {k.value for d in dicts for k in d.keys} == {"k", "n", "plain"}     # the two .append({...}) dicts
    note = nw.constructor_values(t, "Out", "note")[0][1]
    assert len(nw.list_element_dicts(t, note, fn["build"])) == 1                                   # comprehension element
    lit = ast.parse("[{'a': 1}, 2, {'b': 3}]").body[0].value
    assert len(nw.list_element_dicts(t, lit)) == 2                                                 # non-dict elements skipped
    assert nw.list_element_dicts(t, ast.parse("foo()").body[0].value) == []
    assert nw.list_element_dicts(t, led, fn["other"]) == []                                        # scope is honoured
    # terminal strings: an attribute read is followed to every constructor call (deduplicated), other exprs report themselves
    attr = ast.parse("r.b").body[0].value
    rep = nw.terminal_strings(t, [attr, attr], {"b": "Res"})
    assert rep == [(14, True), (19, False), (21, None)], rep
    assert nw.terminal_strings(t, [ast.parse("v.b").body[0].value], {"zz": "Res"}) == [(1, False)]   # attr not mapped -> itself
    assert nw.terminal_strings(t, nw.dict_key_values(dicts, "plain"), {"b": "Res"}) == [(15, True)]
    assert nw.composed_keys(t, dicts) == {"k", "plain"}           # "k": r.b follows `r` to its f-string; "n" and the constant do not


# ── bg_yogas / bg_ontology `[]` (SS ruling 2026-10-01: provenance pointers, ordinals and labels are not narration) ──

_YOGAS = _BG + "l0_yogas.py"
_ONTO = _BG + "l0_ontology.py"
# the text-building expressions of l0_yogas.py whose value is STORED in a bound column: a label, a provenance pointer
YOGAS_BOUND_TEXT = {
    "base_name + ' Yoga'": "name_en label (base name + the word Yoga)",
    "lex_name + ' Yoga'": "detected-name label from the lexicon",
    "f'{name_en}: formation per {verse_ref} ({text_id} Ch.{chapter})'": "formation_text fallback: provenance pointer",
    "f'{text_id.upper()} Ch.{chapter} ({verse_ref})'": "source_citation: provenance",
}
YOGAS_ERROR_PREFIXES = ("bg_yogas ", "invalid yoga source chunk identifier")


def _ancestors(node):
    while node is not None:
        node = getattr(node, "_parent", None)
        if node is not None:
            yield node


def _has_str_const(n):
    return any(isinstance(x, (ast.Constant, ast.JoinedStr)) and (isinstance(x, ast.JoinedStr) or isinstance(x.value, str))
               for x in ast.walk(n))


def test_bg_yogas_every_text_building_expression_is_a_bound_label_or_pointer_or_not_stored():
    tree = nw._parents(ast.parse(_read(_YOGAS)))
    fam = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "seed_yoga_families")
    seed = _read(_WR + "bg_yogas.py")
    assert "seed_yoga_families" not in seed and "seed_yogas(" in seed                # the writer never reaches the families seeder
    assert "seed_yoga_families" not in ast.unparse(next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "seed_yogas"))
    bound, unexplained = set(), []
    specs = {id(v.format_spec) for v in ast.walk(tree) if isinstance(v, ast.FormattedValue) and v.format_spec is not None}
    for n in ast.walk(tree):
        if fam.lineno <= getattr(n, "lineno", 0) <= fam.end_lineno:
            continue
        kind = ("fstr" if isinstance(n, ast.JoinedStr) and id(n) not in specs else
                "binop" if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Mod)) else
                n.func.attr if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr in ("format", "join") else None)
        if kind is None:
            continue
        u = ast.unparse(n)
        if u in YOGAS_BOUND_TEXT:
            bound.add(u)
        elif "re.escape" in u or u.startswith("name + ' '"):
            pass                                                                    # regex pattern / matching-only text, never stored
        elif kind == "fstr" and any(isinstance(a, ast.Raise) for a in _ancestors(n)) and any(
                isinstance(v, ast.Constant) and v.value.startswith(YOGAS_ERROR_PREFIXES) for v in n.values[:1]):
            pass                                                                    # raised error text
        elif kind == "binop" and not _has_str_const(n):
            pass                                                                    # arithmetic / list concatenation
        else:
            unexplained.append((n.lineno, u))
    assert unexplained == []
    assert bound == set(YOGAS_BOUND_TEXT)


def test_bg_yogas_bound_fstrings_interpolate_only_pointer_names_read_from_the_chunk_row():
    tree = ast.parse(_read(_YOGAS))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "extract_yogas_from_corpus")
    fstrs = {ast.unparse(n): n for n in ast.walk(fn) if isinstance(n, ast.JoinedStr)}
    fmt = fstrs["f'{name_en}: formation per {verse_ref} ({text_id} Ch.{chapter})'"]
    assert nw.fstring_interpolations(fmt) == [("name_en", False), ("verse_ref", False), ("text_id", False), ("chapter", False)]
    cit = fstrs["f'{text_id.upper()} Ch.{chapter} ({verse_ref})'"]
    assert nw.fstring_interpolations(cit) == [("text_id.upper()", False), ("chapter", False), ("verse_ref", False)]   # no spec/conversion
    for name, col in (("text_id", "text_id"), ("chapter", "chapter"), ("verse_ref", "verse_ref")):
        assert [ast.unparse(v) for v in nw._assign_values(fn, name)] == [f"row['{col}']"], name      # read verbatim from classical_text_chunks
    assert {ast.unparse(v) for v in nw._assign_values(fn, "name_en")} == {
        "base_name + ' Yoga' if not raw_name.lower().endswith('yoga') else raw_name", "name_en.strip()"}
    ft = [a for a in nw._assign_values(fn, "formation_text")]
    assert len(ft) == 1 and isinstance(ft[0], ast.IfExp) and ast.unparse(ft[0].orelse) in fstrs     # the f-string is only the fallback
    assert ast.unparse(ft[0].body) == "raw_clause"
    sig = {ast.unparse(v) for v in nw._assign_values(fn, "sig_text")}
    assert sig == {"''", "rm.group(0).strip()[:300]", "raw_clause[:200] if raw_clause else name_en"}


def test_bg_yogas_insert_params_only_read_values_and_the_corpora_build_no_text():
    src = _read(_YOGAS)
    assert nw.no_string_building_in_bound_params(src, "seed_yogas", extra_calls=("_yoga_synonyms", "_yoga_citation")) == []
    tree = ast.parse(src)
    for name in ("_yoga_synonyms", "_yoga_citation", "_snake", "_first_sentence"):
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
        inv = nw.composed_inventory(fn)
        assert [u for _, _, u in inv if "m.start()" not in u] == [], (name, inv)       # _first_sentence: an index +1 only
    for corpus in ("YOGAS_CORE", "DETECTOR_YOGAS", "SARAVALI_YOGA_LOOKUP"):
        assert nw.module_level_composition(src, corpus) == [], corpus


def test_bg_yogas_checker_kills_a_narration_mutant_in_the_bound_text_and_the_insert():
    src = _read(_YOGAS)
    mutant = src.replace('f"{name_en}: formation per {verse_ref} ({text_id} Ch.{chapter})"',
                         'f"{name_en}: formation per {verse_ref}, strength {len(raw_clause) / 10:.1f}"')
    assert mutant != src
    fn = next(n for n in ast.parse(mutant).body if isinstance(n, ast.FunctionDef) and n.name == "extract_yogas_from_corpus")
    assert ("len(raw_clause) / 10", True) in [i for n in ast.walk(fn) if isinstance(n, ast.JoinedStr)
                                              for i in nw.fstring_interpolations(n)]
    old = '                    y["significations_text"][:150],\n'
    assert src.count(old) == 1
    assert nw.no_string_building_in_bound_params(
        src.replace(old, '                    f"{y[\'significations_text\'][:150]} (score {len(y)})",\n'), "seed_yogas",
        extra_calls=("_yoga_synonyms", "_yoga_citation"))


_ONTO_EXPLAINED = {
    "f\"nak_{nak_id:02d}_{name_en.lower().replace(' ', '_')}\"": "nakshatra canonical_id (identifier)",
    "f'HOUSE_{house_num:02d}'": "house storage-code synonym", "f'HOUSE_{house_num}'": "house storage-code synonym",
    "f'H{house_num}'": "house storage-code synonym", "f'house_{house_num:02d}'": "house canonical_id (identifier)",
    "synonyms + [c for c in storage_codes if c not in synonyms]": "synonym list concatenation",
    "f'D{n}'": "varga code", "[code] + extra_synonyms": "synonym list concatenation", "f'd{n}'": "varga canonical_id (identifier)",
    "by_class.get(e['entity_class'], 0) + 1": "counter", "changed + deleted": "counter",
}
_ONTO_DESCRIPTIONS = {"f'Nakshatra {nak_id}/27'": ("nak_id", "NAK_DATA", 27), "f'Sign {sign_id}/12'": ("sign_id", "SIGN_DATA", 12)}


def test_bg_ontology_every_text_building_expression_is_an_identifier_synonym_counter_sql_or_ordinal_description():
    tree = ast.parse(_read(_ONTO))
    rest = []
    for ln, kind, u in nw.composed_inventory(tree):
        if u in _ONTO_EXPLAINED or u in _ONTO_DESCRIPTIONS:
            continue
        rest.append((ln, kind, u))
    # what remains is exactly the INSERT statement's f-string (its constant parts are SQL; only the constant conflict clause is
    # interpolated) and the DELETE-scoping key f-string (a comprehension feeding `owned_canonical_keys`, never stored)
    assert [k for _, k, _ in rest] == ["fstr", "fstr"], rest
    sql_fs, key_fs = rest
    assert "INSERT INTO brahma_ontology" in sql_fs[2] and "{conflict_clause}" in sql_fs[2]
    assert key_fs[2].startswith("f\"{e['entity_class']}")
    assert {u for _, _, u in nw.composed_inventory(tree)} >= set(_ONTO_DESCRIPTIONS) | set(_ONTO_EXPLAINED)    # none of the pins is stale


def test_bg_ontology_the_only_composed_descriptions_are_ordinal_labels_of_fixed_lists():
    tree = ast.parse(_read(_ONTO))
    calls = [c for c in ast.walk(tree) if isinstance(c, ast.Call) and isinstance(c.func, ast.Name) and c.func.id == "_e"]
    composed = []
    for c in calls:
        desc = c.args[5] if len(c.args) > 5 else next((k.value for k in c.keywords if k.arg == "description"), None)
        if desc is not None and nw.is_composed(tree, desc):
            composed.append(desc)
    assert sorted(ast.unparse(d) for d in composed) == sorted(_ONTO_DESCRIPTIONS)
    for d in composed:
        var, data, n = _ONTO_DESCRIPTIONS[ast.unparse(d)]
        assert nw.fstring_interpolations(d) == [(var, False)]                          # a bare loop index, no value shaping
        (lst,) = nw._assign_values(tree, data)
        firsts = [e.elts[0].value for e in lst.elts]
        assert firsts == list(range(1, n + 1)) and len(lst.elts) == n                  # ordinals 1..N of a fixed literal list
        loops = [f for f in ast.walk(tree) if isinstance(f, ast.For) and isinstance(f.iter, ast.Name) and f.iter.id == data]
        assert len(loops) == 1 and var in {t.id for t in ast.walk(loops[0].target) if isinstance(t, ast.Name)}
    # _e_varga passes its description parameter straight through and every caller tuple carries a literal string there
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_e_varga")
    assert [ast.unparse(v) for v in nw.dict_key_values(nw.dict_nodes(tree, fn.body[-1].value), "description")] == ["description"]
    (vd,) = nw._assign_values(tree, "VARGA_DATA")
    assert all(isinstance(t.elts[4], ast.Constant) and isinstance(t.elts[4].value, str) for t in vd.elts)


def test_bg_ontology_insert_params_only_read_values():
    assert nw.no_string_building_in_bound_params(_read(_ONTO), "seed_ontology") == []
    old = '                e["synonyms"], e.get("description"),\n'
    src = _read(_ONTO)
    assert src.count(old) == 1
    assert nw.no_string_building_in_bound_params(src.replace(old, '                e["synonyms"], f"{e.get(\'description\')}!",\n'), "seed_ontology")


NULLED_SERVED = sorted("""bg_gochara_arcs bg_vidhi_floors bg_vidhi_primitives bg_kota_chakra_rings bg_kp_sublord_division
    bg_reference bo_grounding mi_seva mi_vistara bg_cohort bg_concordance ka_kshetra mi_jivanaghatana
    bg_sarvatobhadra_grid bg_vedha_malefic_scale bg_phaladeepika_latta mi_sankalpa
    bo_samskara bg_ephemeris_engine bg_panchanga ka_dasha_kala ka_graha_sancara ka_muhurta_seva ka_tulana""".split())


def test_committed_file_declares_no_negative_served_surface_and_nulls_the_unproven_ones():
    # a negative scan is not proof (CLAUDE.md N.8 / N.7.6): no asset is declared `served_surface: false`, and the 24
    # assets whose only evidence was a negative scan / a comment / a provenance label / an unavailable stub are null
    decl = ac.load_asset_declarations()
    vals = {a: (e["carriage"] or {}).get("served_surface") for a, e in decl.items()}
    assert [a for a, v in vals.items() if v is False] == []
    assert sorted(a for a in NULLED_SERVED if vals[a] is not None) == []
    assert sum(v is True for v in vals.values()) == 103 and sum(v is None for v in vals.values()) == 24


RECHECKED_TRUE = """bg_ghatana bg_gochara_citation_resolution bg_nakshatra bg_prashna_rules bg_rules ga_prashna
    ka_gochara_resonance lel_events mi_bhara""".split()


def test_the_nine_rechecked_true_values_cite_a_real_file_line_read_and_mi_sankalpa_is_null():
    # follow-up: declared true against Dens N/A (a scanner gap) must carry a cited real non-test read
    decl = ac.load_asset_declarations()
    for a in RECHECKED_TRUE:
        assert decl[a]["carriage"]["served_surface"] is True, a
        ev = decl[a]["evidence"]["carriage"]
        assert re.search(r"[\w/]+\.ts:\d+", ev) and "scanner gap" in ev, a
        assert "allow-list" not in ev.split("(real")[0], a
    assert decl["mi_sankalpa"]["carriage"]["served_surface"] is None
    assert "no real served read" in decl["mi_sankalpa"]["evidence"]["carriage"]


REPO_ROOT = HERE.parents[3]


def _is_code_comment(line):
    return bool(re.match(r"\s*(//|\*|/\*|#|--)", line))


def _sql_context(lines, lineno):
    """A non-comment SELECT/EXISTS within the 40 lines up to and including the cited one: a prose mention of
    `from <table>` in a description string has none."""
    return any(re.search(r"\b(SELECT|EXISTS)\b", x, re.I) and not _is_code_comment(x) for x in lines[max(0, lineno - 40):lineno])


def _is_sql_read(lines, lineno, token, kind=None):
    """The cited line reads `token` (case-insensitive FROM/JOIN, same line; or the previous NON-comment line ends in
    FROM/JOIN and this line starts with the token) inside a SQL context. A comment, `--` SQL comment, DELETE FROM,
    provenance label, allow-list entry or prose/string-only mention is none of these. kind == "table_map" (a
    dynamic `FROM ${table}` select): the cited line must be a `key: 'token',` entry of a map in a file that selects
    `FROM ${...}`; the quoted token elsewhere is not enough."""
    line = lines[lineno - 1]
    if _is_code_comment(line) or re.search(r"\bDELETE\s+FROM\b", line, re.I):
        return False
    tok = re.escape(token)
    if kind == "table_map":
        return bool(re.fullmatch(rf"\s*[A-Za-z_][A-Za-z0-9_]*\s*:\s*['\"]{tok}['\"]\s*,?\s*(//.*)?", line)) and any(
            re.search(r"\bFROM\s+\$\{", x) and not _is_code_comment(x) for x in lines)
    if not _sql_context(lines, lineno):
        return False
    if re.search(rf"\b(FROM|JOIN)\s+(public\.)?{tok}\b", line, re.I):
        return True
    prev = next((x for x in reversed(lines[:lineno - 1]) if x.strip()), "")
    return (not _is_code_comment(prev) and bool(re.search(r"\b(FROM|JOIN)\s*$", prev, re.I))
            and not re.search(r"\bDELETE\s+FROM\s*$", prev, re.I)
            and bool(re.match(rf"\s*(public\.)?{tok}\b", line, re.I)))


_TRUES = sorted(a for a, e in ac.load_asset_declarations().items() if (e["carriage"] or {}).get("served_surface") is True)


def test_there_are_served_true_declarations_and_each_is_checked_below():
    assert len(_TRUES) == 103


@pytest.mark.parametrize("asset", _TRUES)
def test_every_served_true_cites_a_real_non_test_read_of_its_table(asset):
    e = ac.load_asset_declarations()[asset]
    path, line = e["read_evidence"].rsplit(":", 1)
    assert re.fullmatch(r"(platform|platform-mcp)/src/.+\.tsx?", path), path          # served TypeScript only
    assert not ac._READ_EVIDENCE_EXCLUDED_RE.search(path), path
    f = REPO_ROOT / path
    assert f.is_file(), path
    lines = f.read_text(encoding="utf-8").splitlines()
    assert 1 <= int(line) <= len(lines), (path, line)
    assert _is_sql_read(lines, int(line), e["read_table"], e["read_kind"]), (path, line, e["read_table"], lines[int(line) - 1].strip())


def test_the_read_check_rejects_comments_labels_allowlists_deletes_and_prose():
    src = ["// FROM t_x", "  * FROM t_x", "  provenance: { tables: ['t_x'] },", "  't_x',", "const q = `SELECT 1 FROM t_x w`", "  FROM", "    t_x a", "JOIN t_y"]
    assert [_is_sql_read(src, i, "t_x") for i in range(1, 8)] == [False, False, False, False, True, False, True]
    sel = "const q = `SELECT a FROM t_y`"
    assert _is_sql_read([sel, "DELETE FROM t_x WHERE a"], 2, "t_x") is False
    assert _is_sql_read([sel, "delete  from t_x"], 2, "t_x") is False
    assert _is_sql_read([sel, "-- SELECT * FROM t_x"], 2, "t_x") is False
    assert _is_sql_read([sel, "  -- FROM t_x"], 2, "t_x") is False
    assert _is_sql_read([sel, "// FROM", "t_x a"], 3, "t_x") is False                      # FROM is on a preceding comment line
    assert _is_sql_read([sel, "DELETE FROM", "  t_x"], 3, "t_x") is False
    assert _is_sql_read(["'Retrieve the rows from t_x for a chart.'"], 1, "t_x") is False   # prose-only, no SQL context
    assert _is_sql_read(["description: 'rows from t_x (16 rows)',", "x: 1"], 1, "t_x") is False
    assert _is_sql_read([sel, "select * from T_X c"], 2, "t_x") is True                      # case-insensitive
    assert _is_sql_read(["x = `SELECT *", "  FROM t_x`"], 2, "t_x") is True
    assert _is_sql_read(["FROM t_xy", sel], 1, "t_x") is False                               # token boundary


def test_the_dynamic_table_map_branch_needs_a_map_entry_and_the_table_map_kind():
    m = ["const M = {", "  chart_summary: 't_x',", "}", "sql = `SELECT * FROM ${table}`"]
    assert _is_sql_read(m, 2, "t_x", "table_map") is True
    assert _is_sql_read(m, 2, "t_x") is False                                               # not declared a table_map
    assert _is_sql_read(["  chart_summary: 't_x',"], 1, "t_x", "table_map") is False        # no FROM ${} in the file
    assert _is_sql_read(["x = f('t_x')", "sql = `SELECT * FROM ${table}`"], 1, "t_x", "table_map") is False   # not a map entry
    assert _is_sql_read(["  // a: 't_x',", "sql = `SELECT * FROM ${table}`"], 1, "t_x", "table_map") is False
    assert _is_sql_read(["  a: 'other',", "sql = `SELECT * FROM ${table}`"], 1, "t_x", "table_map") is False


@pytest.mark.parametrize("path", [
    "platform/src/a/__tests__/x.ts", "platform/src/a.spec.ts", "platform/src/a.test.tsx", "platform/src/__mocks__/a.ts",
    "platform/src/lib/e2e/a.ts", "platform/src/tests/a.ts", "platform/src/test/a.ts", "platform/src/generated/a.ts",
    "platform/src/fixtures/a.ts", "platform/src/lib/source_query_availability.ts", "platform/src/app/api/mcp/db/query/route.ts",
    "platform-mcp/src/tests/a.ts", "platform-mcp/src/a.spec.tsx"])
def test_the_path_exclusion_catches_test_mock_generated_and_allowlist_paths(path):
    assert ac._READ_EVIDENCE_EXCLUDED_RE.search(path)
    with pytest.raises(ac.DeclarationsError):
        ac.validate_declarations(_doc(a=dict(carriage=dict(served_surface=True), read_evidence=path + ":12", read_table="t")))


def test_the_path_exclusion_does_not_catch_served_capability_paths():
    for ok in ("platform/src/lib/retrieval/registry/layers/L2_bodha/query_signals.ts", "platform-mcp/src/tools/register_p1_reference.ts",
               "platform/src/lib/contest/a.ts", "platform/src/lib/latest/a.ts", "platform/src/lib/testing_not/a.ts"):
        assert not ac._READ_EVIDENCE_EXCLUDED_RE.search(ok), ok


def test_committed_read_evidence_repoints_and_kinds():
    decl = ac.load_asset_declarations()
    L = "platform/src/lib/retrieval/registry/layers/"
    want = {
        "bo_sangati": L + "L2_bodha/query_domain_reading.ts:821",
        "ka_gochara": "platform-mcp/src/tools/retrieval/register_gochara_windows.ts:1809",
        "mi_bhavisya": L + "L5_mimamsa/query_predictions.ts:138",
        "ph_nimitta": L + "L4_phala/query_predictive_anchors.ts:139",
        "mi_darshana": L + "L5_mimamsa/query_insights.ts:225",
        "mi_bhara": "platform-mcp/src/lib/kala_envelope.ts:556",
        "bg_dignity_reference": "platform-mcp/src/tools/register_p1_reference.ts:373",
        "bg_ghatana": L + "L5_mimamsa/lel_intake_checklist.ts:248",
    }
    for a, ev in want.items():
        assert decl[a]["read_evidence"] == ev, a
    assert decl["bg_dignity_reference"]["read_table"] == "bg_dignity_reference"
    assert decl["bg_ghatana"]["read_table"] == "brahma_event_ontology"
    kinds = {a: e["read_kind"] for a, e in decl.items() if e["read_kind"] is not None}
    assert kinds == {"ka_gochara_resonance": "coverage", "bo_laksana_rerank": "projection", "bo_cdlm_summary": "table_map"}
    assert not any(e["read_evidence"].endswith(".py") or ".py:" in e["read_evidence"] for e in decl.values() if e["read_evidence"])


def test_committed_file_declares_no_dag_dependents_anywhere():
    # dag_dependents is MEASURED (blocking_radius), never declared: a declared copy of a measurement is circular and
    # was wrong for bg_gochara_arcs (ka_gochara reads it with no registry depends_on edge)
    assert "dag_dependents" not in ac.CARRIAGE_FIELDS
    raw = json.loads(ac.DECLARATIONS_PATH.read_text(encoding="utf-8"))
    assert raw["carriage_fields"] == ["served_surface"]
    for aid, e in raw["assets"].items():
        assert "dag_dependents" not in (e["carriage"] or {}), aid


def test_committed_file_cross_asset_writes_only_where_evidenced():
    decl = ac.load_asset_declarations()
    assert decl["mi_abhilekha"]["cross_asset_writes"] == ["mimamsa_predictions.lifecycle_status"]
    assert decl["mi_seva"]["cross_asset_writes"] == []
    assert sorted(a for a, e in decl.items() if e["cross_asset_writes"] is not None) == ["mi_abhilekha", "mi_seva"]
    for a in ("mi_abhilekha", "mi_seva"):
        assert decl[a]["kind"] == "service" and decl[a]["evidence"]["cross_asset_writes"]


def test_committed_file_declares_no_terminal_by_construction_yet():
    assert all(e["terminal_by_construction"] is None for e in ac.load_asset_declarations().values())


def test_committed_file_does_not_declare_the_two_census_excluded_t0_assets():
    decl = ac.load_asset_declarations()
    assert "ka_gochara_sweep" not in decl and "ka_gochara_v3_century_materialize" not in decl


# ───────────────────────── (2) schema / validator ─────────────────────────

BAD_DOCS = [
    ("not-an-object", [1, 2]),
    ("no-version", dict(kind_enum=list(ac.DECLARED_KINDS), assets={})),
    ("blank-version", dict(version=" ", kind_enum=list(ac.DECLARED_KINDS), assets={})),
    ("enum-mismatch", dict(version="1", kind_enum=["data", "service"], assets={})),
    ("enum-reordered-extra", dict(version="1", kind_enum=list(ac.DECLARED_KINDS) + ["multi-table"], assets={})),
    ("assets-not-object", dict(version="1", kind_enum=list(ac.DECLARED_KINDS), assets=[])),
    ("entry-not-object", _doc(a="service")),
    ("unknown-field", _doc(a=dict(kind="data", applicability="x"))),
    ("kind-not-in-enum", _doc(a=dict(kind="multi-table"))),
    ("kind-artifact", _doc(a=dict(kind="artifact"))),
    ("kind-wrong-type", _doc(a=dict(kind=3))),
    ("carriage-not-object", _doc(a=dict(carriage=True))),
    ("carriage-unknown-field", _doc(a=dict(carriage=dict(served_surface=True, served=True)))),
    ("carriage-int-not-bool", _doc(a=dict(carriage=dict(served_surface=1)))),
    ("carriage-string", _doc(a=dict(carriage=dict(served_surface="yes")))),
    ("prose-not-list", _doc(a=dict(prose_fields="narrative", evidence=PEV))),
    ("prose-string-of-distinct-letters", _doc(a=dict(prose_fields="abc", evidence=PEV))),
    ("prose-dict-not-list", _doc(a=dict(prose_fields=dict(a="b"), evidence=PEV))),
    ("prose-tuple-like-nested-list", _doc(a=dict(prose_fields=[["a"]], evidence=PEV))),
    ("prose-blank", _doc(a=dict(prose_fields=["narrative", " "], evidence=PEV))),
    ("prose-duplicate", _doc(a=dict(prose_fields=["narrative", "narrative"], evidence=PEV))),
    ("prose-non-str", _doc(a=dict(prose_fields=[1], evidence=PEV))),
    ("evidence-not-object", _doc(a=dict(evidence="x"))),
    ("evidence-unknown-key", _doc(a=dict(evidence=dict(other="x")))),
    ("evidence-non-str", _doc(a=dict(evidence=dict(kind=1)))),
    ("blank-asset-id", _doc(**{" ": dict(kind="data")})),
    ("dag-dependents-is-measured-not-declared", _doc(a=dict(carriage=dict(dag_dependents=True)))),
    ("prose-case-variant-duplicate", _doc(a=dict(prose_fields=["Narrative", "narrative"], evidence=PEV))),
    # E6.1 narr: every declared prose_fields (including the positive empty list) carries an evidence pointer
    ("prose-declared-without-evidence", _doc(a=dict(prose_fields=["narrative"]))),
    ("prose-empty-declared-without-evidence", _doc(a=dict(prose_fields=[]))),
    ("prose-declared-evidence-null-object", _doc(a=dict(prose_fields=["narrative"], evidence=None))),
    ("prose-declared-evidence-pointer-null", _doc(a=dict(prose_fields=["narrative"], evidence=dict(prose_fields=None)))),
    ("prose-declared-evidence-pointer-blank", _doc(a=dict(prose_fields=["narrative"], evidence=dict(prose_fields="  ")))),
    ("prose-empty-evidence-pointer-blank", _doc(a=dict(prose_fields=[], evidence=dict(prose_fields="")))),
    ("prose-evidence-only-on-other-key", _doc(a=dict(prose_fields=[], evidence=dict(kind="x")))),
    # E6.1 narr: `column` or `column.$.key(.key)*`; a column name must look like a column name
    ("prose-path-no-key", _doc(a=dict(prose_fields=["narrative.$"], evidence=PEV))),
    ("prose-path-trailing-dot", _doc(a=dict(prose_fields=["narrative.$."], evidence=PEV))),
    ("prose-path-no-column", _doc(a=dict(prose_fields=["$.headline"], evidence=PEV))),
    ("prose-path-no-root-marker", _doc(a=dict(prose_fields=["narrative.headline"], evidence=PEV))),
    ("prose-path-empty-segment", _doc(a=dict(prose_fields=["narrative.$..headline"], evidence=PEV))),
    ("prose-path-trailing-segment-dot", _doc(a=dict(prose_fields=["narrative.$.a."], evidence=PEV))),
    ("prose-path-space-in-key", _doc(a=dict(prose_fields=["narrative.$.head line"], evidence=PEV))),
    ("prose-path-array-index", _doc(a=dict(prose_fields=["narrative.$.items[0]"], evidence=PEV))),
    ("prose-path-wildcard", _doc(a=dict(prose_fields=["narrative.$.*"], evidence=PEV))),
    ("prose-path-digit-key", _doc(a=dict(prose_fields=["narrative.$.1a"], evidence=PEV))),
    ("prose-path-trailing-newline", _doc(a=dict(prose_fields=["narrative.$.headline\n"], evidence=PEV))),
    ("prose-path-leading-dot", _doc(a=dict(prose_fields=[".narrative.$.headline"], evidence=PEV))),
    ("prose-path-double-root", _doc(a=dict(prose_fields=["narrative.$.$.headline"], evidence=PEV))),
    ("prose-column-digit-first", _doc(a=dict(prose_fields=["1narrative"], evidence=PEV))),
    ("prose-column-space", _doc(a=dict(prose_fields=["narr ative"], evidence=PEV))),
    ("prose-column-dash", _doc(a=dict(prose_fields=["narr-ative"], evidence=PEV))),
    ("prose-column-dotted-table-prefix", _doc(a=dict(prose_fields=["t.narrative"], evidence=PEV))),
    ("prose-column-trailing-newline", _doc(a=dict(prose_fields=["narrative\n"], evidence=PEV))),
    ("prose-path-case-variant-duplicate", _doc(a=dict(prose_fields=["n.$.headline", "N.$.Headline"], evidence=PEV))),
    ("prose-path-exact-duplicate", _doc(a=dict(prose_fields=["n.$.headline", "n.$.headline"], evidence=PEV))),
    ("prose-column-and-its-own-path", _doc(a=dict(prose_fields=["narrative", "narrative.$.headline"], evidence=PEV))),
    ("prose-path-and-its-column", _doc(a=dict(prose_fields=["narrative.$.headline", "narrative"], evidence=PEV))),
    ("prose-path-and-its-own-subpath", _doc(a=dict(prose_fields=["n.$.a", "n.$.a.b"], evidence=PEV))),
    ("prose-subpath-and-its-parent-path", _doc(a=dict(prose_fields=["n.$.a.b", "n.$.a"], evidence=PEV))),
    ("prose-non-adjacent-path-overlap", _doc(a=dict(prose_fields=["n.$.a", "x", "n.$.a.b"], evidence=PEV))),
    ("prose-non-adjacent-column-and-path", _doc(a=dict(prose_fields=["n", "x", "y", "N.$.a"], evidence=PEV))),
    ("prose-non-adjacent-duplicate", _doc(a=dict(prose_fields=["x", "y", "z", "x"], evidence=PEV))),
    # review 2026-10-01: evidence blank after stripping invisible characters, no writer path:line, orphan, kind, length
    ("evidence-zero-width-space", _doc(a=dict(prose_fields=["x"], evidence=dict(prose_fields="\u200b")))),
    ("evidence-invisible-mix", _doc(a=dict(prose_fields=[], evidence=dict(prose_fields="\u200b\u00a0\u2060 \u3000")))),
    ("evidence-bom", _doc(a=dict(prose_fields=["x"], evidence=dict(prose_fields="\ufeff")))),
    ("evidence-mongolian-vowel-separator", _doc(a=dict(prose_fields=["x"], evidence=dict(prose_fields="\u180e")))),
    ("evidence-control-char", _doc(a=dict(prose_fields=["x"], evidence=dict(prose_fields="\x00\x01")))),
    ("evidence-non-str", _doc(a=dict(prose_fields=["x"], evidence=dict(prose_fields=["w.py:1"])))),
    ("evidence-no-path-line", _doc(a=dict(prose_fields=[], evidence=dict(prose_fields="stores source text; generates none")))),
    ("evidence-path-without-line", _doc(a=dict(prose_fields=["x"], evidence=dict(prose_fields="writers/w.py composes it")))),
    ("evidence-line-zero", _doc(a=dict(prose_fields=["x"], evidence=dict(prose_fields="w.py:0")))),
    ("evidence-non-code-extension", _doc(a=dict(prose_fields=["x"], evidence=dict(prose_fields="notes.txt:3")))),
    ("evidence-ddl-wording-without-kind", _doc(a=dict(prose_fields=["x"], evidence=dict(prose_fields="TEXT in DDL (325_l2_bodha_enriched_schema.sql)")))),
    ("orphan-evidence-on-null-prose", _doc(a=dict(prose_fields=None, evidence=dict(prose_fields="w.py:1")))),
    ("orphan-evidence-on-absent-prose", _doc(a=dict(evidence=dict(prose_fields="w.py:1")))),
    ("orphan-evidence-blank-string-on-null-prose", _doc(a=dict(prose_fields=None, evidence=dict(prose_fields="")))),
    ("evidence-kind-unknown", _doc(a=dict(prose_fields=["x"], evidence_kind="sql", evidence=dict(prose_fields="325_a.sql")))),
    ("evidence-kind-non-str", _doc(a=dict(prose_fields=["x"], evidence_kind=1, evidence=dict(prose_fields="325_a.sql")))),
    ("evidence-kind-uppercase", _doc(a=dict(prose_fields=["x"], evidence_kind="DDL", evidence=dict(prose_fields="325_a.sql")))),
    ("evidence-kind-on-null-prose", _doc(a=dict(prose_fields=None, evidence_kind="ddl"))),
    ("evidence-kind-on-empty-prose", _doc(a=dict(prose_fields=[], evidence_kind="ddl", evidence=dict(prose_fields="325_a.sql")))),
    ("evidence-kind-ddl-without-migration-file", _doc(a=dict(prose_fields=["x"], evidence_kind="ddl", evidence=dict(prose_fields="the column in the schema")))),
    ("column-longer-than-128", _doc(a=dict(prose_fields=["c" * 129], evidence=PEV))),
    ("path-column-longer-than-128", _doc(a=dict(prose_fields=["c" * 129 + ".$.k"], evidence=PEV))),
    ("path-key-longer-than-128", _doc(a=dict(prose_fields=["n.$." + "k" * 129], evidence=PEV))),
    ("path-inner-key-longer-than-128", _doc(a=dict(prose_fields=["n.$.a." + "k" * 129 + ".b"], evidence=PEV))),
    ("terminal-blank", _doc(a=dict(terminal_by_construction=" "))),
    ("terminal-non-str", _doc(a=dict(terminal_by_construction=True))),
    ("terminal-contradicts-served-true", _doc(a=dict(terminal_by_construction="no reader by design",
                                                     carriage=dict(served_surface=True),
                                                     read_evidence="platform/src/a.ts:12", read_table="t"))),
    ("cross-writes-not-list", _doc(a=dict(cross_asset_writes="t.c", evidence=dict(cross_asset_writes="p")))),
    ("cross-writes-non-str", _doc(a=dict(cross_asset_writes=[1], evidence=dict(cross_asset_writes="p")))),
    ("cross-writes-not-table-dot-column", _doc(a=dict(cross_asset_writes=["justatable"], evidence=dict(cross_asset_writes="p")))),
    ("cross-writes-three-parts", _doc(a=dict(cross_asset_writes=["s.t.c"], evidence=dict(cross_asset_writes="p")))),
    ("cross-writes-duplicate", _doc(a=dict(cross_asset_writes=["t.c", "t.c"], evidence=dict(cross_asset_writes="p")))),
    ("cross-writes-case-variant-duplicate", _doc(a=dict(cross_asset_writes=["t.c", "T.C"], evidence=dict(cross_asset_writes="p")))),
    ("cross-writes-declared-without-evidence", _doc(a=dict(cross_asset_writes=["t.c"]))),
    ("cross-writes-empty-declared-without-evidence", _doc(a=dict(cross_asset_writes=[]))),
    ("cross-writes-trailing-newline", _doc(a=dict(cross_asset_writes=["t.c\n"], evidence=dict(cross_asset_writes="p")))),
    ("served-true-without-read-evidence", _doc(a=dict(carriage=dict(served_surface=True)))),
    ("served-true-read-evidence-null", _doc(a=dict(carriage=dict(served_surface=True), read_evidence=None, read_table="t"))),
    ("served-true-without-read-table", _doc(a=dict(carriage=dict(served_surface=True), read_evidence="platform/src/a.ts:12"))),
    ("read-evidence-no-line", _doc(a=dict(carriage=dict(served_surface=True), read_evidence="platform/src/a.ts", read_table="t"))),
    ("read-evidence-line-zero", _doc(a=dict(carriage=dict(served_surface=True), read_evidence="platform/src/a.ts:0", read_table="t"))),
    ("read-evidence-prose", _doc(a=dict(carriage=dict(served_surface=True), read_evidence="see the route handler", read_table="t"))),
    ("read-evidence-trailing-newline", _doc(a=dict(carriage=dict(served_surface=True), read_evidence="platform/src/a.ts:12\n", read_table="t"))),
    ("read-evidence-absolute-path", _doc(a=dict(carriage=dict(served_surface=True), read_evidence="/etc/a.ts:12", read_table="t"))),
    ("read-evidence-parent-path", _doc(a=dict(carriage=dict(served_surface=True), read_evidence="../a.ts:12", read_table="t"))),
    ("read-evidence-dotdot-middle", _doc(a=dict(carriage=dict(served_surface=True), read_evidence="platform/src/../../etc/a.ts:12", read_table="t"))),
    ("read-evidence-python-path", _doc(a=dict(carriage=dict(served_surface=True), read_evidence="platform/python-sidecar/a.py:12", read_table="t"))),
    ("read-evidence-outside-served-src", _doc(a=dict(carriage=dict(served_surface=True), read_evidence="platform/scripts/a.ts:12", read_table="t"))),
    ("read-evidence-python-under-src", _doc(a=dict(carriage=dict(served_surface=True), read_evidence="platform/src/a.py:12", read_table="t"))),
    ("read-evidence-only-with-null-served", _doc(a=dict(carriage=dict(served_surface=None), read_evidence="platform/src/a.ts:12"))),
    ("read-evidence-md-path", _doc(a=dict(carriage=dict(served_surface=True), read_evidence="platform/src/a.md:12", read_table="t"))),
    ("read-kind-unknown", _doc(a=dict(carriage=dict(served_surface=True), read_evidence="platform/src/a.ts:12", read_table="t", read_kind="row-ish"))),
    ("read-kind-without-served-true", _doc(a=dict(carriage=dict(served_surface=None), read_kind="coverage"))),
    ("read-kind-non-str", _doc(a=dict(carriage=dict(served_surface=True), read_evidence="platform/src/a.ts:12", read_table="t", read_kind=1))),
    ("read-evidence-non-str", _doc(a=dict(carriage=dict(served_surface=True), read_evidence=12, read_table="t"))),
    ("read-table-not-identifier", _doc(a=dict(carriage=dict(served_surface=True), read_evidence="platform/src/a.ts:12", read_table="a b"))),
    ("read-table-trailing-newline", _doc(a=dict(carriage=dict(served_surface=True), read_evidence="platform/src/a.ts:12", read_table="t\n"))),
    ("read-evidence-with-null-served", _doc(a=dict(carriage=dict(served_surface=None), read_evidence="platform/src/a.ts:12", read_table="t"))),
    ("read-evidence-with-false-served", _doc(a=dict(carriage=dict(served_surface=False), read_evidence="platform/src/a.ts:12", read_table="t"))),
    ("read-evidence-without-carriage", _doc(a=dict(read_evidence="platform/src/a.ts:12", read_table="t"))),
    ("read-table-without-evidence", _doc(a=dict(read_table="t"))),
]


@pytest.mark.parametrize("name,doc", BAD_DOCS, ids=[n for n, _ in BAD_DOCS])
def test_validator_rejects_malformed_documents(name, doc):
    with pytest.raises(ac.DeclarationsError):
        ac.validate_declarations(doc)


def test_validator_accepts_null_fields_and_every_enum_kind():
    doc = _doc(**{f"x{i}": dict(kind=k, carriage=None, prose_fields=None, evidence=None)
                  for i, k in enumerate(list(ac.DECLARED_KINDS) + [None])},
               y=dict(kind=None, carriage=dict(served_surface=None), prose_fields=["a"], terminal_by_construction=None,
                      cross_asset_writes=None, evidence=PEV),
               z=dict(carriage=dict(served_surface=False), terminal_by_construction="written only by X; no reader by design",
                      cross_asset_writes=["t.c"], evidence=dict(cross_asset_writes="effect contract writes: [t.c]")),
               w=dict(cross_asset_writes=[], evidence=dict(cross_asset_writes="effect contract writes: []")),
               v=dict(carriage=dict(served_surface=True), read_evidence="platform/src/lib/x/[id]/route-a_b.ts:12", read_table="t_1"),
               v2=dict(carriage=dict(served_surface=True), read_evidence="platform-mcp/src/lib/x.tsx:1", read_table="t_1",
                       read_kind="coverage"),
               u=dict(carriage=dict(served_surface=None), read_evidence=None, read_table=None))
    assert len(ac.validate_declarations(doc)) == len(ac.DECLARED_KINDS) + 7


def test_validator_checks_asset_ids_against_the_registry_set_only_when_supplied():
    doc = _doc(known=dict(kind="data"), typo=dict(kind="data"))
    assert set(ac.validate_declarations(doc)) == {"known", "typo"}
    with pytest.raises(ac.DeclarationsError, match="typo"):
        ac.validate_declarations(doc, registry_ids=["known"])
    assert set(ac.validate_declarations(doc, registry_ids=["known", "typo", "more"])) == {"known", "typo"}


# ───────────────────────── (3) reader ─────────────────────────

def test_reader_raises_a_clear_error_on_a_missing_file(tmp_path):
    with pytest.raises(ac.DeclarationsError, match="cannot read"):
        ac.load_asset_declarations(tmp_path / "nope.json")


def test_reader_raises_a_clear_error_on_invalid_json(tmp_path):
    with pytest.raises(ac.DeclarationsError, match="not valid JSON"):
        ac.load_asset_declarations(_write(tmp_path, None, raw="{ not json"))


def test_reader_rejects_a_duplicate_asset_key(tmp_path):
    raw = ('{"version":"1","kind_enum":' + json.dumps(list(ac.DECLARED_KINDS)) +
           ',"assets":{"a":{"kind":"data"},"a":{"kind":"service"}}}')
    with pytest.raises(ac.DeclarationsError, match="duplicate key"):
        ac.load_asset_declarations(_write(tmp_path, None, raw=raw))


def test_reader_is_pure_and_repeatable(tmp_path):
    p = _write(tmp_path, _doc(a=dict(kind="service")))
    before = p.read_bytes()
    a, b = ac.load_asset_declarations(p), ac.load_asset_declarations(p)
    assert a == b and a is not b
    assert p.read_bytes() == before


def test_reader_returns_nulls_as_nulls_not_values(tmp_path):
    decl = ac.load_asset_declarations(_write(tmp_path, _doc(a=dict(kind=None, carriage=None, prose_fields=None))))
    assert decl["a"]["kind"] is None and decl["a"]["carriage"] is None and decl["a"]["prose_fields"] is None
    assert "absent" not in decl


def test_reader_validates_ids_against_the_supplied_registry_set(tmp_path):
    p = _write(tmp_path, _doc(a=dict(kind="data")))
    with pytest.raises(ac.DeclarationsError):
        ac.load_asset_declarations(p, registry_ids=["b"])


def test_reader_wraps_undecodable_bytes(tmp_path):
    p = tmp_path / "decl.json"
    p.write_bytes(b'{"version": "\xff\xfe"}')
    with pytest.raises(ac.DeclarationsError, match="cannot read"):
        ac.load_asset_declarations(p)


def test_reader_wraps_a_recursion_error_from_deep_nesting(tmp_path):
    p = tmp_path / "decl.json"
    p.write_text("[" * 200000 + "]" * 200000, encoding="utf-8")
    with pytest.raises(ac.DeclarationsError, match="nested|recursion|deep"):
        ac.load_asset_declarations(p)


@pytest.mark.parametrize("bad", ["abc", {"a": 1}, 3, b"a", object()], ids=["str", "dict", "int", "bytes", "object"])
def test_reader_rejects_a_non_list_registry_ids(tmp_path, bad):
    p = _write(tmp_path, _doc(a=dict(kind="data")))
    with pytest.raises(ac.DeclarationsError, match="registry_ids"):
        ac.load_asset_declarations(p, registry_ids=bad)
    with pytest.raises(ac.DeclarationsError, match="registry_ids"):
        ac.validate_declarations(_doc(a=dict(kind="data")), registry_ids=bad)


def test_reader_wraps_a_5000_digit_integer_value_error(tmp_path):
    raw = '{"version": "1", "kind_enum": ' + json.dumps(list(ac.DECLARED_KINDS)) + ', "assets": {}, "x": ' + "9" * 5000 + "}"
    with pytest.raises(ac.DeclarationsError):
        ac.load_asset_declarations(_write(tmp_path, None, raw=raw))


def test_reader_wraps_a_nul_byte_in_the_path():
    with pytest.raises(ac.DeclarationsError, match="cannot read"):
        ac.load_asset_declarations("decl\x00.json")


def test_reader_rejects_non_string_registry_id_members(tmp_path):
    with pytest.raises(ac.DeclarationsError, match="registry_ids"):
        ac.validate_declarations(_doc(a=dict(kind="data")), registry_ids=["a", 3])


def test_reader_accepts_a_list_tuple_set_or_frozenset_of_registry_ids():
    doc = _doc(a=dict(kind="data"))
    for ids in (["a"], ("a",), {"a"}, frozenset({"a"})):
        assert set(ac.validate_declarations(doc, registry_ids=ids)) == {"a"}


# ───────────────────────── (4) facts merge ─────────────────────────

DECL = {
    "svc": dict(kind="service", carriage=dict(served_surface=False), prose_fields=None),
    "dat": dict(kind="data", carriage=dict(served_surface=None), prose_fields=["narrative"]),
    "unk": dict(kind=None, carriage=None, prose_fields=None),
    "empty": dict(kind="data", carriage=None, prose_fields=[]),
}


def test_without_declarations_the_facts_are_exactly_the_measured_facts():
    rec = dict(asset_id="svc", target_columns=["a"], asset_kind="service", count_sql_declared=False)
    assert ac.facts_for_asset(rec) == ac.facts_for_asset(rec, None) == ac.facts_for_asset(rec, {})
    assert ac.facts_for_asset(rec) == dict(columns=["a"], asset_kind="service", count_sql_declared=False)


def test_declared_facts_merge_under_their_own_keys_and_never_overwrite_asset_kind():
    f = ac.facts_for_asset(dict(asset_id="svc", asset_kind="service"), DECL)
    assert f["asset_kind"] == "service" and f["declared_kind"] == "service"
    g = ac.facts_for_asset(dict(asset_id="svc", asset_kind="data"), DECL)
    assert g["asset_kind"] == "data" and g["declared_kind"] == "service"     # the measured value is not replaced


def test_absent_asset_and_null_fields_are_unknown_never_values():
    assert ac.facts_for_asset(dict(asset_id="ghost", asset_kind="data"), DECL) == dict(asset_kind="data")
    f = ac.facts_for_asset(dict(asset_id="unk"), DECL)
    assert f == {}                                              # no declared_* key at all
    assert ac.facts_for_asset(dict(), DECL) == {}               # a record with no asset_id cannot match
    assert ac.facts_for_asset("not a record", DECL) == {}


def test_carries_downstream_is_true_only_from_a_positive_served_surface():
    f = ac.declared_facts({"a": dict(carriage=dict(served_surface=True))}, "a")
    assert f["declared_carries_downstream"] is True and f["declared_carriage"] == dict(served_surface=True)


def test_carries_downstream_is_never_derived_from_negatives():
    # two negatives (a false served_surface, a zero measured dependent count) are a negative scan, not proof
    for car in (None, dict(served_surface=None), dict(served_surface=False)):
        f = ac.declared_facts({"a": dict(carriage=car)}, "a", measured_dependents=0, measured_served="N/A")
        assert "declared_carries_downstream" not in f, car
    f = ac.declared_facts({"a": dict(carriage=dict(served_surface=False))}, "a")
    assert f["declared_carriage"] == dict(served_surface=False) and "declared_carries_downstream" not in f


def test_carries_downstream_is_false_only_with_a_terminal_by_construction_pointer():
    ptr = "writes kala_x only; reader exists by design nowhere (effect contract writes: [])"
    f = ac.declared_facts({"a": dict(carriage=None, terminal_by_construction=ptr)}, "a")
    assert f["declared_carries_downstream"] is False and f["declared_terminal_by_construction"] == ptr
    g = ac.declared_facts({"a": dict(terminal_by_construction=ptr, carriage=dict(served_surface=False))}, "a")
    assert g["declared_carries_downstream"] is False
    for bad in (None, "", "   ", True, 1):
        assert "declared_carries_downstream" not in ac.declared_facts({"a": dict(terminal_by_construction=bad)}, "a"), bad
    # an (unvalidated) doc that also says served_surface true: the positive component wins, never False
    h = ac.declared_facts({"a": dict(terminal_by_construction=ptr, carriage=dict(served_surface=True))}, "a")
    assert h["declared_carries_downstream"] is True


def test_dag_dependents_is_not_a_declared_carriage_component():
    f = ac.declared_facts({"a": dict(carriage=dict(dag_dependents=True, served_surface=True))}, "a")
    assert f["declared_carriage"] == dict(served_surface=True)        # a stale/unvalidated key is ignored, never merged


def test_cross_asset_writes_is_exposed_as_declared_and_an_empty_list_is_declared():
    d = {"a": dict(cross_asset_writes=["t.c"]), "b": dict(cross_asset_writes=[]), "c": dict(cross_asset_writes=None)}
    assert ac.declared_facts(d, "a")["declared_cross_asset_writes"] == ["t.c"]
    assert ac.declared_facts(d, "b")["declared_cross_asset_writes"] == []
    assert "declared_cross_asset_writes" not in ac.declared_facts(d, "c")
    assert "declared_cross_asset_writes" not in ac.declared_facts({"x": dict(kind="service")}, "x")
    f = ac.declared_facts(d, "a"); f["declared_cross_asset_writes"].append("z.z")
    assert d["a"]["cross_asset_writes"] == ["t.c"]                      # a copy


def test_prose_fields_null_is_undeclared_but_an_explicit_empty_list_is_declared():
    assert "declared_prose_fields" not in ac.facts_for_asset(dict(asset_id="svc"), DECL)
    assert ac.facts_for_asset(dict(asset_id="dat"), DECL)["declared_prose_fields"] == ["narrative"]
    assert ac.facts_for_asset(dict(asset_id="empty"), DECL)["declared_prose_fields"] == []


def test_merged_prose_list_is_a_copy():
    f = ac.declared_facts(DECL, "dat")
    f["declared_prose_fields"].append("x")
    assert DECL["dat"]["prose_fields"] == ["narrative"]


# ───────────────────────── (5) disagreement reporting ─────────────────────────

def test_declared_kind_disagreeing_with_the_registry_is_reported_not_preferred():
    f = ac.facts_for_asset(dict(asset_id="svc", asset_kind="data"), DECL)
    assert f["declaration_disagreements"] == [dict(field="kind", declared="service", registry="data")]
    g = ac.facts_for_asset(dict(asset_id="dat", asset_kind="service"), DECL)
    assert dict(field="kind", declared="data", registry="service") in g["declaration_disagreements"]
    assert g["asset_kind"] == "service"


def test_agreement_and_unknown_registry_kind_report_nothing():
    assert "declaration_disagreements" not in ac.facts_for_asset(dict(asset_id="svc", asset_kind="service"), DECL)
    assert "declaration_disagreements" not in ac.facts_for_asset(dict(asset_id="svc"), DECL)          # registry kind unknown
    assert "declaration_disagreements" not in ac.facts_for_asset(dict(asset_id="svc", asset_kind=" "), DECL)


def test_the_artifact_registry_kind_is_not_compared():
    # registry `artifact` maps to the declaration file per asset (SS): no disagreement is invented
    decl = {"a": dict(kind="data")}
    assert "declaration_disagreements" not in ac.facts_for_asset(dict(asset_id="a", asset_kind="artifact"), decl)


def test_refinements_of_data_are_reported_too():
    decl = {"a": dict(kind="view")}
    assert ac.facts_for_asset(dict(asset_id="a", asset_kind="data"), decl)["declaration_disagreements"] == [
        dict(field="kind", declared="view", registry="data")]


def _rec(aid, served=None, direct=None, kind=None):
    r = dict(asset_id=aid)
    if served is not None:
        r["measurements"] = {"Dens.served": dict(v=served, measured="")}
    if direct is not None:
        r["blocking_radius"] = dict(direct=direct)
    if kind is not None:
        r["asset_kind"] = kind
    return r


def test_declared_served_false_against_a_measured_dens_pass_or_fail_is_reported():
    decl = {"a": dict(carriage=dict(served_surface=False))}
    for v in ("PASS", "FAIL", "PARTIAL"):
        f = ac.facts_for_asset(_rec("a", served=v), decl)
        assert f["declaration_disagreements"] == [dict(field="carriage.served_surface", declared=False, measured=v)], v
    for v in ("N/A", "NO_DETECTOR"):
        assert "declaration_disagreements" not in ac.facts_for_asset(_rec("a", served=v), decl), v


def test_declared_served_true_against_a_measured_dens_na_is_reported():
    decl = {"a": dict(carriage=dict(served_surface=True))}
    f = ac.facts_for_asset(_rec("a", served="N/A"), decl)
    assert f["declaration_disagreements"] == [dict(field="carriage.served_surface", declared=True, measured="N/A")]
    for v in ("PASS", "FAIL", "PARTIAL", "NO_DETECTOR"):
        assert "declaration_disagreements" not in ac.facts_for_asset(_rec("a", served=v), decl), v


def test_declared_read_evidence_is_exposed_as_a_fact_when_declared():
    d = {"a": dict(carriage=dict(served_surface=True), read_evidence="platform/src/a.ts:12", read_table="t"),
         "b": dict(carriage=dict(served_surface=None), read_evidence=None, read_table=None)}
    f = ac.declared_facts(d, "a")
    assert f["declared_read_evidence"] == "platform/src/a.ts:12" and f["declared_read_table"] == "t"
    g = ac.declared_facts(d, "b")
    assert "declared_read_evidence" not in g and "declared_read_table" not in g
    k = ac.declared_facts({"a": dict(carriage=dict(served_surface=True), read_evidence="platform/src/a.ts:12", read_table="t",
                                     read_kind="coverage")}, "a")
    assert k["declared_read_kind"] == "coverage" and "declared_read_kind" not in f
    bogus = ac.declared_facts({"a": dict(carriage=dict(served_surface=True), read_evidence="platform/src/a.ts:12", read_table="t",
                                         read_kind="bogus")}, "a")
    assert "declared_read_kind" not in bogus and bogus["declared_read_evidence"] == "platform/src/a.ts:12"
    h = ac.declared_facts({"c": dict(read_evidence="platform/src/a.ts:12", read_table=None)}, "c")      # an unpaired (unvalidated) pointer
    assert "declared_read_evidence" not in h and "declared_read_table" not in h


def test_served_surface_disagreement_needs_the_measurement_and_a_declared_value():
    t, f_, n = ({"a": dict(carriage=dict(served_surface=x))} for x in (True, False, None))
    for decl in (t, f_):
        assert "declaration_disagreements" not in ac.facts_for_asset(dict(asset_id="a"), decl)             # no measurements
        assert "declaration_disagreements" not in ac.facts_for_asset(dict(asset_id="a", measurements={}), decl)
        assert "declaration_disagreements" not in ac.facts_for_asset(dict(asset_id="a", measurements="x"), decl)
        assert "declaration_disagreements" not in ac.facts_for_asset(dict(asset_id="a", measurements={"Dens.served": "PASS"}), decl)
        assert "declaration_disagreements" not in ac.facts_for_asset(dict(asset_id="a", measurements={"Dens.served": dict(v=None)}), decl)
    for v in ("PASS", "FAIL", "N/A"):
        assert "declaration_disagreements" not in ac.facts_for_asset(_rec("a", served=v), n)               # unknown declared


def test_declared_dag_dependents_is_gone_so_no_dependents_disagreement_can_exist():
    decl = {"a": dict(carriage=dict(served_surface=True))}
    f = ac.facts_for_asset(_rec("a", direct=0, served="PASS"), decl)
    assert "declaration_disagreements" not in f


def test_terminal_by_construction_against_a_measured_dependent_is_reported():
    decl = {"a": dict(terminal_by_construction="no reader by design")}
    f = ac.facts_for_asset(_rec("a", direct=2), decl)
    assert f["declaration_disagreements"] == [dict(field="terminal_by_construction", declared="no reader by design", measured_dependents=2)]
    assert "declaration_disagreements" not in ac.facts_for_asset(_rec("a", direct=0), decl)
    assert "declaration_disagreements" not in ac.facts_for_asset(dict(asset_id="a"), decl)
    assert "declaration_disagreements" not in ac.facts_for_asset(dict(asset_id="a", blocking_radius=dict(direct=True)), decl)


# ───────────────────────── (6) declarations are facts only: no verdict moves ─────────────────────────

def test_no_na_rule_is_declared_and_no_criterion_reads_a_declared_key():
    assert ac.NA_RULE_DECISIONS == {}
    facts = dict(asset_kind="service", declared_kind="static", declared_carriage=dict(served_surface=False),
                 declared_carries_downstream=False, declared_prose_fields=[])
    base = dict(asset_kind="service")
    for crit in ac.CRITERION_REGISTRY:
        for layer in ac.ALL_LAYERS:
            assert ac.criterion_applicability(crit, layer, facts) == ac.criterion_applicability(crit, layer, base), (crit, layer)


def test_rollup_is_identical_with_and_without_the_committed_declarations():
    decl = ac.load_asset_declarations(registry_ids=REGISTRY_IDS)
    for layer, c in _fixture_census().items():
        with_decl = ac.rollup_census(c, {a["asset_id"]: ac.facts_for_asset(a, decl) for a in c["assets"]})
        without = ac.rollup_census(c, {a["asset_id"]: ac.facts_for_asset(a) for a in c["assets"]})
        assert _digest(with_decl) == _digest(without), layer


def test_build_rollup_output_default_equals_explicitly_no_declarations():
    cs = _fixture_census()
    a = ac.build_rollup_output(copy.deepcopy(cs))
    b = ac.build_rollup_output(copy.deepcopy(cs), declarations={})
    assert _digest(a) == _digest(b)


def test_full_layer_rollup_rejects_a_declared_id_outside_the_census(tmp_path, monkeypatch):
    p = _write(tmp_path, _doc(lel_events=dict(kind="user_data"), not_an_asset=dict(kind="data")))
    monkeypatch.setattr(ac, "DECLARATIONS_PATH", p)
    with pytest.raises(ac.DeclarationsError, match="not_an_asset"):
        ac.build_rollup_output(_fixture_census())


def test_partial_layer_rollup_does_not_id_check(tmp_path, monkeypatch):
    p = _write(tmp_path, _doc(not_an_asset=dict(kind="data")))
    monkeypatch.setattr(ac, "DECLARATIONS_PATH", p)
    cs = _fixture_census()
    ac.build_rollup_output({"L0": cs["L0"]})          # a one-layer run cannot know the whole registry set


def test_a_malformed_default_file_fails_the_rollup_loudly(tmp_path, monkeypatch):
    monkeypatch.setattr(ac, "DECLARATIONS_PATH", _write(tmp_path, None, raw="[]"))
    with pytest.raises(ac.DeclarationsError):
        ac.build_rollup_output(_fixture_census())
