"""test_e6_s3_alias_ldgr.py: E6 S3, REGISTRY_REVISION 12 (SS N-72 S3, N-73 (1)/(4), N-74 (b)): declared Vocab.alias and Ldgr.source_presence.

N/A is reached ONLY by a per-asset reviewed declaration (`vocab_alias.na = no_alias_class`, `ldgr_source.na = no_classical_claim`, each with a one-line
reason and checkable evidence), never by a column pattern (A5). An asset that DOES have an alias class is measured against bg_ontology (class planet:
canonical id and display name, and the ontology synonyms when an alias column is declared); an asset that makes classical claims names the column that
carries the source and the citation_state it stands on (an unsourced / refuted state can never read PASS). An undeclared asset reads exactly as before.
Offline: the three fetchers are stubbed (as S2 stubs d1_fetch_*); the REAL_SQL tests run the same SQL on the disposable Postgres (skipped only where no
PostgreSQL binaries exist)."""
from __future__ import annotations

import copy
import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import _decl_version  # noqa: E402
import test_e6_a_na_causes as na_causes  # noqa: E402
import test_e6_na_r01_03 as r13  # noqa: E402
import test_e6_s2_carriage as s2  # noqa: E402
from _disposable_pg import disposable_pg  # noqa: E402,F401  (the session fixture)

NA, NO_DET, PASS, FAIL, PARTIAL, ERRORED = ac.NA, ac.NO_DET, ac.PASS, ac.FAIL, ac.PARTIAL, ac.ERRORED
EV = "platform/scripts/governance/asset_census.py:1"          # an existing repo file: a checkable evidence pointer
LDGR, ALIAS = "Ldgr.source_presence", "Vocab.alias"

LIKE_COLS = ["synonyms", "aliases", "alias", "alt_names", "alternate_names", "other_names", "also_known_as", "Synonyms", "SYNONYMS", "Aliases", "synonym", "alias_names",
             "alias_set", "synonyms_json", "graha_synonyms", "aka", "AKA", "nicknames", "name_variants", "Alt_Name"]
PHALA_COLS = ["graha", "direction", "count_from_graha", "effect_description", "source_citation", "verse_ref", "table_version", "created_at"]
VA_NA = dict(na="no_alias_class", why="the asset stores computed degrees only; no vocabulary carries synonyms", evidence=EV)
VA_M = {"class": "planet", "vocab_column": "graha", "alias_column": "synonyms", "why": "graha names are the planet vocabulary", "evidence": EV}
VA_M_NOALIAS = {k: v for k, v in VA_M.items() if k != "alias_column"}
LS_NA = dict(na="no_classical_claim", why="pure computation over ephemeris numerics; states no classical rule", evidence=EV)


def LS_M(state="sourced", col="citation"):
    return dict(source_column=col, citation_state=state, why="the citation column names the classical verse each rule row transcribes", evidence=EV)


FORMS = [dict(canonical_id="sun", canonical_name_en="Sun", synonyms=["Surya", "Ravi", "SUN"]),
         dict(canonical_id="moon", canonical_name_en="Moon", synonyms=["Chandra", "MOON"]),
         dict(canonical_id="ketu", canonical_name_en="Ketu", synonyms=[]),
         dict(canonical_id="mer", canonical_name_en="Mercury", synonyms=["Budha"])]       # an id that is NOT its display name


def _doc(extra, aid="bg_x", version="1.8.0"):
    return dict(version=version, kind_enum=list(ac.DECLARED_KINDS), assets={aid: dict({"kind": "data"}, **extra)})


def _bad(extra, match):
    with pytest.raises(ac.DeclarationsError, match=match):
        ac.validate_declarations(_doc(extra))


def _pairs(*rows):
    """rows: (value, alias_set_or_None, n) -> the alias_fetch_values shape"""
    return [dict(v=v, a=a, n=n) for v, a, n in rows]


SPEC = {"class": "planet", "vocab_column": "graha", "alias_column": "synonyms", "table": "t"}
SPEC_NA = {**{k: v for k, v in SPEC.items() if k != "alias_column"}, "identity_only": True, "identity_only_why": "the asset stores canonical display names only"}
SPEC_PLAIN = {k: v for k, v in SPEC.items() if k != "alias_column"}          # no alias_column and no identity_only: identity alone


# ───────────────────────── the declaration validator ─────────────────────────

def test_validator_accepts_every_declared_form():
    for extra in (dict(vocab_alias=VA_NA), dict(vocab_alias=VA_M), dict(vocab_alias=VA_M_NOALIAS), dict(ldgr_source=LS_NA),
                  dict(ldgr_source=LS_M()), dict(ldgr_source=LS_M("sourced_ocr_unverified")), dict(vocab_alias=None, ldgr_source=None),
                  dict(vocab_alias=dict(VA_M, evidence="unverified:the L0 review sheet notes")), dict(ldgr_source=dict(LS_M(), evidence="unverified:the elevation brief section 4")),
                  dict(vocab_alias=dict(VA_M_NOALIAS, identity_only=True, identity_only_why="the asset stores the canonical display names only")),
                  dict(vocab_alias=dict(VA_NA, na=None, **{"class": "planet", "vocab_column": "graha"}))):
        ac.validate_declarations(_doc(extra))
    for st in ac.CITATION_STATES:
        ac.validate_declarations(_doc(dict(ldgr_source=LS_M(st))))


@pytest.mark.parametrize("va, match", [
    (dict(VA_NA, na="no_vocabulary"), "vocab_alias.na"),                                                  # not the one allowed word
    (dict(VA_NA, na="no-alias-class"), "vocab_alias.na"),                                                 # the cause slug is not the declaration word
    ({k: v for k, v in VA_NA.items() if k != "why"}, r"vocab_alias\.why"),                                # no reason
    (dict(VA_NA, why=""), r"vocab_alias\.why"), (dict(VA_NA, why="   "), r"vocab_alias\.why"),
    (dict(VA_NA, why="two\nlines"), r"vocab_alias\.why"), (dict(VA_NA, why=" padded "), r"vocab_alias\.why"),
    (dict(VA_NA, why="x" * 1201), r"vocab_alias\.why"), (dict(VA_NA, why=None), r"vocab_alias\.why"), (dict(VA_NA, why=7), r"vocab_alias\.why"),
    ({k: v for k, v in VA_NA.items() if k != "evidence"}, r"vocab_alias\.evidence"),                      # no evidence
    (dict(VA_NA, evidence=""), r"vocab_alias\.evidence"), (dict(VA_NA, evidence="unverified:"), r"vocab_alias\.evidence"),
    (dict(VA_NA, evidence="no/such/file.md:3"), r"vocab_alias\.evidence"), (dict(VA_NA, evidence="/etc/hosts"), r"vocab_alias\.evidence"),
    (dict(VA_NA, evidence="../outside.md"), r"vocab_alias\.evidence"),
    (dict(VA_NA, **{"class": "planet"}), "declares no alias class"),                                      # na together with a measured field
    (dict(VA_NA, vocab_column="graha"), "declares no alias class"),
    (dict(VA_NA, alias_column="synonyms"), "declares no alias class"),
    ({k: v for k, v in VA_M.items() if k != "class"}, "must declare na"),                                 # neither form
    (dict(VA_M, **{"class": "sign"}), "must declare na"),                                                  # a class outside ALIAS_CLASSES
    (dict(VA_M, **{"class": "Planet"}), "must declare na"),
    ({k: v for k, v in VA_M.items() if k != "vocab_column"}, r"vocab_alias\.vocab_column"),
    (dict(VA_M, vocab_column="gra ha"), r"vocab_alias\.vocab_column"), (dict(VA_M, vocab_column='g"'), r"vocab_alias\.vocab_column"),
    (dict(VA_M, vocab_column="1graha"), r"vocab_alias\.vocab_column"), (dict(VA_M, vocab_column=3), r"vocab_alias\.vocab_column"),
    (dict(VA_M, alias_column="a;b"), r"vocab_alias\.alias_column"),
    (dict(VA_M, alias_column="graha"), "must differ"),
    (dict(VA_M, extra="x"), "unknown field"),
])
def test_validator_refuses_a_malformed_vocab_alias_declaration(va, match):
    _bad(dict(vocab_alias=va), match)


@pytest.mark.parametrize("ls, match", [
    (dict(LS_NA, na="no_citation"), "ldgr_source.na"),
    ({k: v for k, v in LS_NA.items() if k != "why"}, r"ldgr_source\.why"), (dict(LS_NA, why="  "), r"ldgr_source\.why"),
    (dict(LS_NA, why="a\nb"), r"ldgr_source\.why"),
    ({k: v for k, v in LS_NA.items() if k != "evidence"}, r"ldgr_source\.evidence"), (dict(LS_NA, evidence="nowhere.md"), r"ldgr_source\.evidence"),
    (dict(LS_NA, source_column="citation"), "declares no source"), (dict(LS_NA, citation_state="sourced"), "declares no source"),
    ({k: v for k, v in LS_M().items() if k != "source_column"}, r"ldgr_source\.source_column"),
    (dict(LS_M(), source_column="a b"), r"ldgr_source\.source_column"), (dict(LS_M(), source_column=None), r"ldgr_source\.source_column"),
    ({k: v for k, v in LS_M().items() if k != "citation_state"}, r"ldgr_source\.citation_state"),
    (dict(LS_M(), citation_state="verified"), r"ldgr_source\.citation_state"), (dict(LS_M(), citation_state="SOURCED"), r"ldgr_source\.citation_state"),
    (dict(LS_M(), citation_state=None), r"ldgr_source\.citation_state"),
    (dict(LS_M(), extra=1), "unknown field"),
])
def test_validator_refuses_a_malformed_ldgr_source_declaration(ls, match):
    _bad(dict(ldgr_source=ls), match)


def test_validator_refuses_non_objects_and_a_no_classical_claim_beside_a_transcription_carriage():
    for bad in ("no_alias_class", ["na"], 7, True):
        _bad(dict(vocab_alias=bad), "must be an object")
        _bad(dict(ldgr_source=bad), "must be an object")
    car = dict(applies="D1", nature="transcription", why=s2.WHY, evidence=s2.EVID, citation_state="sourced")
    _bad(dict(ldgr_source=LS_NA, carriage=car), "contradicts a declared transcription carriage")
    ac.validate_declarations(_doc(dict(ldgr_source=LS_M(), carriage=car)))            # naming the source column beside a transcription is the consistent pair
    ac.validate_declarations(_doc(dict(ldgr_source=LS_NA, carriage=dict(applies="D3", nature="computation", why=s2.WHY, evidence=s2.EVID))))


def test_validator_doc_level_field_lists_must_match_when_present():
    for key, fields in (("vocab_alias_declaration_fields", ac.VOCAB_ALIAS_DECL_FIELDS), ("ldgr_source_declaration_fields", ac.LDGR_SOURCE_DECL_FIELDS)):
        ok = _doc({})
        ok[key] = list(fields)
        ac.validate_declarations(ok)
        for broken in (list(fields[:-1]), list(fields) + ["x"], list(reversed(fields))):
            ok[key] = broken
            with pytest.raises(ac.DeclarationsError, match=key):
                ac.validate_declarations(ok)


def test_the_committed_file_declares_neither_key_beyond_the_latta_and_lists_the_fields():
    raw = json.loads(ac.DECLARATIONS_PATH.read_text(encoding="utf-8"))
    assert raw["version"] == _decl_version.CURRENT          # DECL-LATTA: bg_phaladeepika_latta is the first (and only) asset to declare them
    assert raw["vocab_alias_declaration_fields"] == list(ac.VOCAB_ALIAS_DECL_FIELDS)
    assert raw["ldgr_source_declaration_fields"] == list(ac.LDGR_SOURCE_DECL_FIELDS)
    # the per-asset review is the reviewed work: nothing is declared by pattern in this PR
    assert sorted(a for a, e in raw["assets"].items() if "vocab_alias" in e) == sorted(["bg_phaladeepika_latta", "bg_dignity_reference", "bg_transit_engine", "bg_transit_rules",
                                                                                         "bg_vastu_directions", "bg_kp_sublord_division"])      # L0-WAVE batch 2 adds five identity_only planet declarations
    assert [a for a, e in raw["assets"].items() if "ldgr_source" in e] == ["bg_phaladeepika_latta"]
    ac.load_asset_declarations()


# ───────────────────────── A5: a column pattern never produces an N/A ─────────────────────────

@pytest.mark.parametrize("crit, columns", [(ALIAS, ["id", "name"]), (LDGR, ["id", "name"]), (ALIAS, ["id", "synonyms"]), (LDGR, ["id", "source_citation"]),
                                          (LDGR, ["id", "citation", "source"]), (ALIAS, ["graha", "alt_names"])])
def test_a_column_pattern_never_makes_either_criterion_na(crit, columns):
    cell = ac.rollup_asset("L0", {}, dict(columns=columns))[crit.split(".")[0]]
    chk = next(c for c in cell["checks"] if c["criterion"] == crit)
    assert chk["v"] == NO_DET and chk["v"] != NA
    if chk["state"] == "NOT_APPLICABLE":
        assert "N/A rule undecided" in chk["reason"]
    assert cell["v"] != NA


def test_no_column_pattern_rule_is_declared_for_either_criterion_and_declaring_one_is_refused_by_the_registry_not_by_us():
    assert not [i for i in ac.NA_RULE_DECISIONS if i.endswith("#columns_any") or i.endswith("#asset_kinds")]
    assert ac.CRITERION_REGISTRY[ALIAS]["columns_any"] == (ac.ALIAS_COLUMN,)           # the pattern stays a hint; it releases nothing
    assert ac.CRITERION_REGISTRY[LDGR]["columns_any"] == ac.CITATION_COLUMNS


def test_an_undeclared_asset_emits_nothing_from_the_declared_forms():
    for va in (None, {}, dict(na=None), "x"):
        assert ac.vocab_alias_declared_check("bg_x", va, "t", ["id"]) == {}
    for ls in (None, {}, dict(na=None), "x"):
        assert ac.ldgr_source_declared_check("bg_x", ls, "t", ["id"]) == {}


def test_measure_emits_no_na_for_an_undeclared_asset_whatever_its_columns(monkeypatch, tmp_path):
    reg = {"x": na_causes._reg_row("x", "t_plain"), "y": na_causes._reg_row("y", "t_cite")}
    na_causes._stub_layer(monkeypatch, tmp_path, reg, tables={"t_plain": (["id", "name"], []), "t_cite": (["id", "source_citation"], [])})
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: {})
    ms = {a["asset_id"]: a["measurements"] for a in ac.measure("L0")["assets"]}
    assert ALIAS not in ms["x"] and LDGR not in ms["x"]                                  # no pattern, no measurement, and above all no N/A
    assert ms["y"][LDGR]["v"] == PASS and "citation_state" not in ms["y"][LDGR] and "declared" not in ms["y"][LDGR]   # the legacy count, byte as before


# ───────────────────────── the declared N/A words ─────────────────────────

def test_a_declared_no_alias_class_reads_na_by_its_cause_and_the_vocab_cell_is_then_the_identity_check():
    got = ac.vocab_alias_declared_check("bg_x", VA_NA, "t", ["id", "name"])
    rec = got[ALIAS]
    assert rec["v"] == NA and rec["cause"] == "no-alias-class" and rec["declared"] is True and VA_NA["why"] in rec["measured"] and EV in rec["measured"]
    cell = ac.rollup_asset("L0", {**got, "Vocab.identity": dict(v=PASS, measured="k")})["Vocab"]
    assert cell["v"] == PASS
    chk = next(c for c in cell["checks"] if c["criterion"] == ALIAS)
    assert chk["v"] == NA and chk["rule_id"] == "Vocab.alias#measured:no-alias-class" and "N-72" in chk["decision"]


def test_a_declared_no_classical_claim_reads_na_by_its_cause_and_releases_the_ldgr_cell():
    got = ac.ldgr_source_declared_check("bg_x", LS_NA, "t", ["id", "value"])
    rec = got[LDGR]
    assert rec["v"] == NA and rec["cause"] == "no-classical-claim" and rec["declared"] is True and LS_NA["why"] in rec["measured"]
    cell = ac.rollup_asset("L0", got)["Ldgr"]
    assert cell["v"] == NA and cell["checks"][0]["rule_id"] == "Ldgr.source_presence#measured:no-classical-claim"


def test_the_na_is_released_only_by_the_declared_rule(monkeypatch):
    got = {**ac.vocab_alias_declared_check("bg_x", VA_NA, "t", ["id"]), **ac.ldgr_source_declared_check("bg_x", LS_NA, "t", ["id"])}
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {k: v for k, v in ac.NA_RULE_DECISIONS.items() if "no-alias-class" not in k and "no-classical-claim" not in k})
    rolled = ac.rollup_asset("L0", got)
    assert rolled["Ldgr"]["v"] == NO_DET
    assert next(c for c in rolled["Vocab"]["checks"] if c["criterion"] == ALIAS)["v"] == NO_DET
    assert ac.rollup_excluded("L0", {k: v for k, v in got.items() if False}) == {}


def test_the_causes_are_registered_and_a_typo_rule_is_refused(monkeypatch):
    assert ac.NA_CAUSES[ALIAS] == ("no-alias-class",) and ac.NA_CAUSES[LDGR] == ("no-classical-claim",)
    for rid in ("Vocab.alias#measured:no-alias-claim", "Ldgr.source_presence#measured:no_classical_claim", "Vocab.alias#measured",
                "Ldgr.source_presence#measured:no-alias-class", "Vocab.alias#measured:no-classical-claim"):
        monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {**ac.NA_RULE_DECISIONS, rid: "x"})
        with pytest.raises(ValueError):
            ac.validate_na_rule_decisions()
    monkeypatch.undo()
    ac.validate_na_rule_decisions()


@pytest.mark.parametrize("cols", [["id", "synonyms"], ["synonyms"], ("graha", "synonyms", "x")])
def test_no_alias_class_is_refused_where_a_documented_alias_exists(cols):          # N-73 (4)
    rec = ac.vocab_alias_declared_check("bg_x", VA_NA, "t", cols)[ALIAS]
    assert rec["v"] == NO_DET and "cause" not in rec and rec["declaration_disagreements"][0]["field"] == "vocab_alias.na"
    assert ac.rollup_asset("L0", {ALIAS: rec})["Vocab"]["v"] == NO_DET                # the rule is declared, and still nothing is released


@pytest.mark.parametrize("col", ac.CITATION_COLUMNS)
def test_no_classical_claim_is_refused_where_the_table_carries_a_citation_column(col):
    rec = ac.ldgr_source_declared_check("bg_x", LS_NA, "t", ["id", col])[LDGR]
    assert rec["v"] == NO_DET and "cause" not in rec and rec["declaration_disagreements"][0]["field"] == "ldgr_source.na"
    assert col in rec["measured"] and ac.rollup_asset("L0", {LDGR: rec})["Ldgr"]["v"] == NO_DET


def test_a_declaration_stands_where_the_columns_are_unknown_a_service_or_a_view():
    for cols in (None, [], ()):
        assert ac.vocab_alias_declared_check("bg_x", VA_NA, None, cols)[ALIAS]["v"] == NA
        assert ac.ldgr_source_declared_check("bg_x", LS_NA, None, cols)[LDGR]["v"] == NA


def test_a_declared_na_is_never_emitted_for_the_other_criterions_word():
    assert set(ac.vocab_alias_declared_check("bg_x", VA_NA, "t", ["id"])) == {ALIAS}
    assert set(ac.ldgr_source_declared_check("bg_x", LS_NA, "t", ["id"])) == {LDGR}


# ───────────────────────── the alias detector (declared, measured form) ─────────────────────────

def test_every_value_resolving_by_canonical_id_or_display_name_passes():
    r = ac.grade_vocab_alias(SPEC_NA, FORMS, _pairs(("Sun", None, 2), ("moon", None, 1), ("  MER ", None, 1), ("mercury", None, 1)))
    assert r["v"] == PASS and r["declared"] is True and "all resolve" in r["measured"] and "not compared" in r["measured"]
    assert r["alias"]["resolved_by"] == {"canonical_id": ["  MER ", "Sun", "moon"], "canonical_name_en": ["mercury"]}
    assert r["alias"]["rows"] == 5 and r["alias"]["distinct_values"] == 4 and r["severity"] == 0.0


def test_a_canonical_id_outranks_the_display_name_when_both_match():
    forms = [dict(canonical_id="rahu", canonical_name_en="Rahu", synonyms=[])]
    r = ac.grade_vocab_alias(SPEC_NA, forms, _pairs(("Rahu", None, 1)))
    assert r["v"] == PASS and r["alias"]["resolved_by"] == {"canonical_id": ["Rahu"]}


@pytest.mark.parametrize("value, why", [("Sunn", "no match"), ("Surya", "only an ontology synonym of sun"), ("SUN ", None), ("Pluto", "no match"),
                                        (None, "NULL"), ("", "no match")])
def test_a_value_the_vocabulary_does_not_resolve_is_named_and_fails(value, why):
    r = ac.grade_vocab_alias(SPEC_NA, FORMS, _pairs(("Sun", None, 1), (value, None, 3)))
    if value == "SUN ":                                    # 'SUN' casefolds to the canonical id 'sun': it resolves (a synonym spelled like the id is not a defect)
        assert r["v"] == PASS
        return
    assert r["v"] == FAIL and r["severity"] == 0.75
    key = "NULL" if value is None else value
    assert key in r["alias"]["unresolved"] and why in r["alias"]["unresolved"][key]["why"] and r["alias"]["unresolved"][key]["rows"] == 3
    assert "3/4 row(s)" in r["measured"] and repr(key) in r["measured"]


def test_a_value_matching_two_entities_is_ambiguous_never_resolved():
    forms = FORMS + [dict(canonical_id="sun2", canonical_name_en="sun", synonyms=[])]
    r = ac.grade_vocab_alias(SPEC_NA, forms, _pairs(("Sun", None, 1)))
    assert r["v"] == FAIL and "ambiguous" in r["alias"]["unresolved"]["Sun"]["why"]


def test_a_synonym_present_in_the_ontology_and_missing_from_the_asset_flips_the_cell():
    full = _pairs(("Sun", ["Surya", "Ravi", "SUN"], 1), ("Moon", ["Chandra", "MOON"], 1))
    assert ac.grade_vocab_alias(SPEC, FORMS, full)["v"] == PASS
    short = _pairs(("Sun", ["Surya", "SUN"], 1), ("Moon", ["Chandra", "MOON"], 1))                       # 'Ravi' is missing from the asset
    r = ac.grade_vocab_alias(SPEC, FORMS, short)
    assert r["v"] == FAIL and r["alias"]["missing_synonyms"] == {"sun": ["Ravi"]} and "Ravi" in r["measured"] and "sun" in r["measured"]
    assert r["alias"]["rows_affected"] == 1 and r["severity"] == 0.5
    # the same asset against an ontology that does not carry the synonym reads PASS again: it is the ontology's synonym that decides
    no_ravi = [dict(f, synonyms=[s for s in f["synonyms"] if s != "Ravi"]) for f in FORMS]
    assert ac.grade_vocab_alias(SPEC, no_ravi, short)["v"] == PASS
    # and the cell follows the verdict
    assert ac.rollup_asset("L0", {ALIAS: r, "Vocab.identity": dict(v=PASS, measured="k")})["Vocab"]["v"] == FAIL
    assert ac.rollup_asset("L0", {ALIAS: ac.grade_vocab_alias(SPEC, FORMS, full), "Vocab.identity": dict(v=PASS, measured="k")})["Vocab"]["v"] == PASS


# the synonym 'MOON' normalises to the entity's own display name 'Moon', which an asset row always carries: only 'Chandra' can be missing
@pytest.mark.parametrize("a, missing", [(None, ["Chandra"]), ([], ["Chandra"]), ("Chandra", []), (7, ["Chandra"]), ({"k": "Chandra"}, ["Chandra"]),
                                        ([" chandra", "moon"], []), (["Chandra", "MOON", "Soma"], []), (["MOON"], ["Chandra"]), ("chandra ", [])])
def test_the_rows_alias_set_is_read_as_a_list_of_strings_or_one_string_and_compared_normalised(a, missing):
    r = ac.grade_vocab_alias(SPEC, FORMS, _pairs(("Moon", a, 1)))
    assert (r["v"] == PASS) == (not missing)
    if missing:
        assert r["alias"]["missing_synonyms"] == {"moon": sorted(missing)}


def test_an_entity_with_no_ontology_synonym_needs_no_alias_set_and_extra_aliases_are_not_a_defect():
    assert ac.grade_vocab_alias(SPEC, FORMS, _pairs(("Ketu", None, 1)))["v"] == PASS
    assert ac.grade_vocab_alias(SPEC, FORMS, _pairs(("Sun", ["Surya", "Ravi", "SUN", "Aditya", "Bhanu"], 1)))["v"] == PASS


def test_the_asset_s_own_canonical_id_and_display_name_count_as_present_in_its_alias_set():
    forms = [dict(canonical_id="sun", canonical_name_en="Sun", synonyms=["sun", "SUN", "Sun"])]
    assert ac.grade_vocab_alias(SPEC, forms, _pairs(("Sun", None, 1)))["v"] == PASS


def test_leg_two_runs_per_row_group_so_one_short_group_fails_the_asset():
    r = ac.grade_vocab_alias(SPEC, FORMS, _pairs(("Sun", ["Surya", "Ravi", "SUN"], 5), ("Sun", ["Surya", "SUN"], 2)))
    assert r["v"] == FAIL and r["alias"]["rows_affected"] == 2 and r["alias"]["rows"] == 7


def test_empty_class_and_empty_table_are_no_detector_never_pass():
    assert ac.grade_vocab_alias(SPEC, [], _pairs(("Sun", None, 1)))["v"] == NO_DET
    assert ac.grade_vocab_alias(SPEC, FORMS, [])["v"] == NO_DET
    assert ac.grade_vocab_alias(SPEC, FORMS, _pairs(("Sun", None, 0)))["v"] == NO_DET


def test_a_failed_declared_alias_read_degrades_only_this_check(monkeypatch):
    def boom(*a, **k):
        raise ac.Unknown("connection refused")
    monkeypatch.setattr(ac, "alias_fetch_forms", boom)
    monkeypatch.setattr(ac, "alias_fetch_values", lambda *a: [])
    rec = ac.vocab_alias_declared_check("bg_x", VA_M, "t", ["graha", "synonyms"])[ALIAS]
    assert rec["v"] == ERRORED and "connection refused" in rec["measured"]


def test_the_declared_alias_check_reads_the_declared_columns_of_the_target_table(monkeypatch):
    seen = {}
    monkeypatch.setattr(ac, "alias_fetch_forms", lambda c: seen.setdefault("cls", c) and FORMS)
    monkeypatch.setattr(ac, "alias_fetch_values", lambda t, v, a=None: seen.update(args=(t, v, a)) or _pairs(("Sun", ["Surya", "Ravi", "SUN"], 1)))
    assert ac.vocab_alias_declared_check("bg_x", VA_M, "my_table", ["graha", "synonyms"])[ALIAS]["v"] == PASS
    assert seen == {"cls": "planet", "args": ("my_table", "graha", "synonyms")}


@pytest.mark.parametrize("table, cols", [(None, ["graha"]), ("t", None), ("t", [])])
def test_a_declared_alias_class_with_no_readable_table_is_no_detector(monkeypatch, table, cols):
    monkeypatch.setattr(ac, "alias_fetch_forms", lambda c: pytest.fail("no table, no read"))
    assert ac.vocab_alias_declared_check("bg_x", VA_M, table, cols)[ALIAS]["v"] == NO_DET


def test_a_declared_alias_column_the_table_does_not_carry_is_a_fail_before_any_select(monkeypatch):
    monkeypatch.setattr(ac, "alias_fetch_forms", lambda c: pytest.fail("a declaration the table cannot back is not read"))
    rec = ac.vocab_alias_declared_check("bg_x", VA_M, "t", ["graha"])[ALIAS]            # `synonyms` is not a column
    assert rec["v"] == FAIL and "synonyms" in rec["measured"]
    assert ac.vocab_alias_declared_check("bg_x", VA_M, "t", ["name", "synonyms"])[ALIAS]["v"] == FAIL    # nor `graha`


# ───────────────────────── the three SELECTs ─────────────────────────

def _capture(monkeypatch, answer):
    got = []
    monkeypatch.setattr(ac, "scalar", lambda sql: got.append(sql) or answer)
    return got


def test_the_ontology_read_is_one_read_only_select_of_the_declared_class(monkeypatch):
    got = _capture(monkeypatch, json.dumps(FORMS))
    assert ac.alias_fetch_forms("planet") == FORMS
    sql = got[0]
    assert len(got) == 1 and sql.lstrip().upper().startswith("SELECT") and f"FROM {ac.ONTOLOGY_TABLE} WHERE entity_class = 'planet'" in sql
    assert not re.search(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT)\b", sql, re.I) and ";" not in sql


@pytest.mark.parametrize("cls", ["sign", "planet'; DROP TABLE x;--", "", None, "Planet"])
def test_the_ontology_read_refuses_any_class_that_is_not_an_alias_class_before_any_sql(monkeypatch, cls):
    got = _capture(monkeypatch, "[]")
    with pytest.raises(ac.Unknown):
        ac.alias_fetch_forms(cls)
    assert got == []


def test_the_asset_value_read_groups_distinct_pairs_in_a_total_order_and_validates_identifiers(monkeypatch):
    got = _capture(monkeypatch, json.dumps([dict(v="Sun", a=["Surya"], n=3)]))
    assert ac.alias_fetch_values("t", "graha", "synonyms") == [dict(v="Sun", a=["Surya"], n=3)]
    sql = got[0]
    assert '"graha"::text AS v' in sql and 'to_jsonb("synonyms") AS a' in sql and "GROUP BY 1, 2" in sql and "ORDER BY g.v, g.a::text" in sql
    ac.alias_fetch_values("t", "graha")
    assert "GROUP BY 1)" in got[1] and 'AS a' not in got[1] and "ORDER BY g.v)" in got[1]
    for bad in (("t;", "graha", None), ("t", 'g"; DROP', None), ("t", "graha", "a b"), ("1t", "graha", None), (None, "graha", None)):
        before = len(got)
        with pytest.raises(ac.Unknown):
            ac.alias_fetch_values(*bad)
        assert len(got) == before


@pytest.mark.parametrize("fn, args", [(ac.alias_fetch_forms, ("planet",)), (ac.alias_fetch_values, ("t", "graha")), (ac.ldgr_fetch_source_stats, ("t", "c"))])
def test_every_fetcher_raises_unknown_on_an_unparseable_read(monkeypatch, fn, args):
    _capture(monkeypatch, "not json")
    with pytest.raises(ac.Unknown):
        fn(*args)


def test_the_source_stats_read_lists_the_placeholders_and_the_key_sample(monkeypatch):
    got = _capture(monkeypatch, json.dumps(dict(rows=4, lacking=1, sample=[dict(rule_id="r1")])))
    assert ac.ldgr_fetch_source_stats("t", "citation", ["rule_id"])["lacking"] == 1
    sql = got[0]
    assert sql.lstrip().upper().startswith("SELECT") and '"citation" IS NULL' in sql and "regexp_replace(" in sql and "ORDER BY \"rule_id\" LIMIT 5" in sql
    assert "'not traced'" in sql and "'source unidentified'" in sql
    assert not re.search(r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|TRUNCATE|GRANT)\b", sql, re.I)
    ac.ldgr_fetch_source_stats("t", "citation", [])
    assert "'[]'::jsonb" in got[1] and "ORDER BY" not in got[1]
    assert all("'" not in x and '"' not in x for x in ac.LDGR_PLACEHOLDERS) and "not traced" in ac.LDGR_PLACEHOLDERS
    for bad in (("t;", "c", []), ("t", "c d", []), ("t", "c", ['k"']), (None, "c", []), ("t", "c", [], "numeric"), ("t", "c", [], None)):
        with pytest.raises(ac.Unknown):
            ac.ldgr_fetch_source_stats(*bad)
    _capture(monkeypatch, json.dumps(dict(rows="4", lacking=1)))
    with pytest.raises(ac.Unknown):
        ac.ldgr_fetch_source_stats("t", "c")


# ───────────────────────── the Ldgr detector (declared, measured form) ─────────────────────────

def _stats(rows, lacking, sample=()):
    return dict(rows=rows, lacking=lacking, sample=list(sample))


def test_ldgr_every_row_naming_a_source_passes_and_the_record_carries_the_declared_state():
    r = ac.grade_ldgr_source(LS_M("sourced_ocr_unverified"), _stats(8, 0), "t")
    assert r["v"] == PASS and r["citation_state"] == "sourced_ocr_unverified" and r["declared"] is True and "8/8" in r["measured"]
    assert "citation_state sourced_ocr_unverified" in r["measured"] and r["ldgr"] == dict(source_column="citation", rows=8, lacking=0, sample=[])


def test_ldgr_some_rows_lacking_a_source_is_partial_and_the_verdict_says_which_rows():
    r = ac.grade_ldgr_source(LS_M(), _stats(4, 2, [dict(rule_id="r2"), dict(rule_id="r3")]), "t")
    assert r["v"] == PARTIAL and "2/4" in r["measured"] and '"r2"' in r["measured"] and '"r3"' in r["measured"] and "first 5" not in r["measured"]
    big = ac.grade_ldgr_source(LS_M(), _stats(40, 9, [dict(rule_id=f"r{i}") for i in range(5)]), "t")
    assert big["v"] == PARTIAL and "(first 5)" in big["measured"]
    assert "row identity unavailable" in ac.grade_ldgr_source(LS_M(), _stats(4, 1), "t")["measured"]


def test_ldgr_no_row_naming_a_source_fails_and_an_empty_table_is_vacuous():
    assert ac.grade_ldgr_source(LS_M(), _stats(4, 4), "t")["v"] == FAIL
    r = ac.grade_ldgr_source(LS_M(), _stats(0, 0), "t")
    assert r["v"] == NO_DET and "vacuous" in r["measured"] and r["citation_state"] == "sourced"


def test_ldgr_a_declared_column_the_table_does_not_carry_fails_before_any_select(monkeypatch):
    monkeypatch.setattr(ac, "ldgr_fetch_source_stats", lambda *a, **k: pytest.fail("not read"))
    rec = ac.ldgr_source_declared_check("bg_x", LS_M(col="nope"), "t", ["id", "citation"])[LDGR]
    assert rec["v"] == FAIL and "nope" in rec["measured"] and rec["citation_state"] == "sourced"
    for table, cols in ((None, ["citation"]), ("t", None), ("t", [])):
        assert ac.ldgr_source_declared_check("bg_x", LS_M(), table, cols)[LDGR]["v"] == NO_DET


def test_ldgr_the_read_uses_the_declared_column_and_the_first_non_surrogate_key(monkeypatch):
    seen = []
    monkeypatch.setattr(ac, "ldgr_fetch_column_type", lambda t, c: "text")
    monkeypatch.setattr(ac, "ldgr_fetch_source_stats", lambda t, c, k=(), kind="text": seen.append((t, c, list(k))) or _stats(2, 0))
    ac.ldgr_source_declared_check("x", LS_M(col="citation"), "t", ["id", "rule_id", "citation"], [["id"], ["rule_id", "ayanamsha"]])
    ac.ldgr_source_declared_check("x", LS_M(col="citation"), "t", ["id", "citation"], [["id"]])
    ac.ldgr_source_declared_check("x", LS_M(col="citation"), "t", ["a", "citation"], [])
    assert seen == [("t", "citation", ["rule_id", "ayanamsha"]), ("t", "citation", ["id"]), ("t", "citation", [])]


def test_ldgr_a_failed_read_degrades_only_this_check_and_keeps_the_state(monkeypatch):
    def boom(*a, **k):
        raise ac.Unknown("connection refused")
    monkeypatch.setattr(ac, "ldgr_fetch_column_type", lambda t, c: "text")
    monkeypatch.setattr(ac, "ldgr_fetch_source_stats", boom)
    rec = ac.ldgr_source_declared_check("x", LS_M("sourced_ocr_unverified"), "t", ["citation"])[LDGR]
    assert rec["v"] == ERRORED and rec["citation_state"] == "sourced_ocr_unverified"


def _ldgr(v, state, **kw):
    return {LDGR: dict(v=v, measured="m", citation_state=state, declared=True, **kw)}


@pytest.mark.parametrize("state", ["unsourced", "refuted"])
@pytest.mark.parametrize("v", [PASS, PARTIAL])
def test_an_unsourced_or_refuted_state_can_never_read_pass_or_partial(state, v):
    cell = ac.rollup_asset("L0", _ldgr(v, state))["Ldgr"]
    assert cell["v"] == NO_DET and cell["v"] not in (PASS, PARTIAL)
    chk = cell["checks"][0]
    assert chk["v"] == NO_DET and chk["citation_state"] == state and state in chk["reason"] and "never a PASS" in chk["reason"]


@pytest.mark.parametrize("state", ["unsourced", "refuted"])
def test_a_populated_column_with_an_unsourced_state_end_to_end_never_passes(state):
    rec = ac.grade_ldgr_source(LS_M(state), _stats(8, 0), "t")           # every row populated, the claim is not sourced
    assert rec["v"] == NO_DET and "never a PASS" in rec["measured"] and rec["citation_state"] == state      # M1: the RAW record is capped, not only the rollup
    assert ac.rollup_asset("L0", {LDGR: rec})["Ldgr"]["v"] == NO_DET
    part = ac.grade_ldgr_source(LS_M(state), _stats(8, 4, [dict(k=1)]), "t")
    assert part["v"] == NO_DET and ac.rollup_asset("L0", {LDGR: part})["Ldgr"]["v"] == NO_DET
    assert ac.grade_ldgr_source(LS_M(state), _stats(8, 8), "t")["v"] == FAIL                              # nothing populated: a real defect, still a FAIL
    assert ac.grade_ldgr_source(LS_M(state), _stats(0, 0), "t")["v"] == NO_DET


@pytest.mark.parametrize("state", ["unsourced", "refuted"])
def test_a_failing_declared_ldgr_stays_a_fail_whatever_the_state(state):
    assert ac.rollup_asset("L0", _ldgr(FAIL, state))["Ldgr"]["v"] == FAIL


@pytest.mark.parametrize("state", ["sourced", "sourced_ocr_unverified"])
@pytest.mark.parametrize("v", [PASS, PARTIAL])
def test_a_sourced_state_reads_as_measured_and_the_cell_check_carries_it(state, v):
    cell = ac.rollup_asset("L0", _ldgr(v, state))["Ldgr"]
    assert cell["v"] == v and cell["checks"][0]["citation_state"] == state and cell["checks"][0]["reason"] == "measured"


@pytest.mark.parametrize("bad", ["maybe", "", "SOURCED", 5, True, ["sourced"]])
def test_a_state_outside_the_vocabulary_or_missing_on_a_declared_record_is_not_honoured(bad):
    assert ac.rollup_asset("L0", _ldgr(PASS, bad))["Ldgr"]["v"] == NO_DET
    assert ac.rollup_asset("L0", {LDGR: dict(v=PASS, measured="m", declared=True)})["Ldgr"]["v"] == NO_DET


def test_an_undeclared_legacy_ldgr_record_without_a_state_reads_as_before():
    cell = ac.rollup_asset("L0", {LDGR: dict(v=PASS, measured="source_citation populated on 8/8 rows")})["Ldgr"]
    assert cell["v"] == PASS and "citation_state" not in cell["checks"][0]
    assert ac.rollup_asset("L0", {LDGR: dict(v=PARTIAL, measured="x")})["Ldgr"]["v"] == PARTIAL


def test_the_legacy_pattern_measurement_is_skipped_for_a_declaring_asset_and_unchanged_for_the_rest(monkeypatch, tmp_path):
    reg = {"x": na_causes._reg_row("x", "t_decl"), "y": na_causes._reg_row("y", "t_old")}
    na_causes._stub_layer(monkeypatch, tmp_path, reg, tables={"t_decl": (["id", "citation", "source_citation", "synonyms"], []),
                                                              "t_old": (["id", "source_citation", "synonyms"], [])})
    decl = {"x": dict(kind="data", vocab_alias=dict(VA_NA, evidence=EV), ldgr_source=LS_M("sourced_ocr_unverified", col="citation"))}
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: decl)
    legacy_alias = []
    monkeypatch.setattr(ac, "alias_census", lambda t, c: legacy_alias.append(t) or (dict(g=dict(rows=3, no_alias=0)) if "synonyms" in c else None))
    queries = []
    base = ac.scalar
    monkeypatch.setattr(ac, "scalar", lambda sql: queries.append(sql) or base(sql))
    monkeypatch.setattr(ac, "ldgr_fetch_column_type", lambda t, c: "text")
    monkeypatch.setattr(ac, "ldgr_fetch_source_stats", lambda t, c, k=(), kind="text": dict(rows=48, lacking=0, sample=[]))
    ms = {a["asset_id"]: a["measurements"] for a in ac.measure("L0")["assets"]}
    assert legacy_alias == ["t_old"]                                                                       # the declaring asset never ran the synonyms census
    # x: a column the pattern does not know ('citation'), measured with its declared state; the legacy IS NOT NULL count never ran for x
    assert ms["x"][LDGR]["v"] == PASS and ms["x"][LDGR]["citation_state"] == "sourced_ocr_unverified" and ms["x"][LDGR]["declared"] is True
    assert ms["x"][ALIAS]["v"] == NO_DET and "declaration_disagreements" in ms["x"][ALIAS]                   # no_alias_class beside a `synonyms` column: refused
    assert ms["y"][ALIAS]["v"] == PASS and "declared" not in ms["y"][ALIAS]
    assert ms["y"][LDGR]["v"] == PASS and "citation_state" not in ms["y"][LDGR] and "declared" not in ms["y"][LDGR]
    assert sum("IS NOT NULL" in q for q in queries) == 1                                                    # only y's legacy count


def test_measure_emits_the_declared_na_for_an_asset_without_a_production_table(monkeypatch, tmp_path):
    reg = {"svc": na_causes._reg_row("svc", None, asset_kind="service"), "ghost": na_causes._reg_row("ghost", "no_such_table")}
    na_causes._stub_layer(monkeypatch, tmp_path, reg, tables={})
    decl = {"svc": dict(kind="service", vocab_alias=VA_NA, ldgr_source=LS_NA), "ghost": dict(kind="data", vocab_alias=VA_M, ldgr_source=LS_M())}
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: decl)
    monkeypatch.setattr(ac, "alias_fetch_forms", lambda c: pytest.fail("no table, no read"))
    ms = {a["asset_id"]: a["measurements"] for a in ac.measure("L0")["assets"]}
    assert ms["svc"][ALIAS]["v"] == NA and ms["svc"][ALIAS]["cause"] == "no-alias-class"
    assert ms["svc"][LDGR]["v"] == NA and ms["svc"][LDGR]["cause"] == "no-classical-claim"
    assert ms["ghost"][ALIAS]["v"] == NO_DET and ms["ghost"][LDGR]["v"] == NO_DET                            # measured forms need a table
    rolled = ac.rollup_census(ac.measure("L0"))
    assert rolled["svc"]["Ldgr"]["v"] == NA


# ───────────────────────── adversarial review: M1 the raw record, the gap ledger and the rollup agree ─────────────────────────

def _gap_ctrl(monkeypatch, tmp_path, crit):
    monkeypatch.setattr(ac, "CTRL", tmp_path)
    row = dict(asset="bg_x", gap_id=f"bg_x-{crit}", kind="gap", criterion=crit, what="w", change="", detector="d", owner="asset_census",
               gate="this asset's certification", state="OPEN", ts="t0")
    (tmp_path / "asset_gaps.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    return lambda: [json.loads(x) for x in (tmp_path / "asset_gaps.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]


@pytest.mark.parametrize("state", ["unsourced", "refuted"])
@pytest.mark.parametrize("stats", [_stats(8, 0), _stats(8, 3, [dict(k=1)])])
def test_an_unsourced_or_refuted_declared_ldgr_record_does_not_close_an_open_gap(monkeypatch, tmp_path, state, stats):
    read = _gap_ctrl(monkeypatch, tmp_path, LDGR)
    rec = ac.grade_ldgr_source(LS_M(state), stats, "t")
    assert rec["v"] == NO_DET                                                       # the RAW record, not only the rollup
    census = dict(layer="L0", assets=[dict(asset_id="bg_x", measurements={LDGR: rec})])
    assert ac.emit_gaps(census)[2] == 0 and read()[0]["state"] == "OPEN"


@pytest.mark.parametrize("state", ["sourced", "sourced_ocr_unverified"])
def test_a_sourced_declared_ldgr_pass_closes_an_open_gap(monkeypatch, tmp_path, state):
    read = _gap_ctrl(monkeypatch, tmp_path, LDGR)
    rec = ac.grade_ldgr_source(LS_M(state), _stats(8, 0), "t")
    assert rec["v"] == PASS
    census = dict(layer="L0", assets=[dict(asset_id="bg_x", measurements={LDGR: rec})])
    assert ac.emit_gaps(census)[2] == 1 and read()[-1]["state"] == "CLOSED"


def test_the_citation_cap_is_one_rule_shared_by_both_detectors_the_rollup_and_the_writer():
    import carriage_d1 as d1_mod
    import nikasha_certify as nc_mod
    assert ac.CITATION_CAPPED_STATES == d1_mod.CITATION_CAPPED_STATES == nc_mod.CITATION_PASS_REFUSED == ("unsourced", "refuted")
    assert set(ac.CITATION_CAPPED_STATES) == set(ac.CITATION_STATES) - {"sourced", "sourced_ocr_unverified"}
    assert nc_mod.CITATION_CAPPED == ("Carr.D1", "Ldgr.source_presence")
    # the detector side, both criteria, same state: never a PASS/PARTIAL
    for state in ac.CITATION_CAPPED_STATES:
        assert ac.grade_ldgr_source(LS_M(state), _stats(8, 0), "t")["v"] == NO_DET
        rec = d1_mod.d1_measure(s2.SPEC, state, s2.CHUNKS, s2.ROWS, "bg_phaladeepika_latta")
        assert rec["v"] == NO_DET


def test_one_row_lacking_a_source_is_partial_and_names_it():
    r = ac.grade_ldgr_source(LS_M(), _stats(4, 1, [dict(rule_id="r9")]), "t")
    assert r["v"] == PARTIAL and "3/4" in r["measured"] and '"r9"' in r["measured"]


# ───────────────────────── M3: the placeholder detector on a real Postgres ─────────────────────────

def _lit(v):
    """An E'' literal with every non-alphanumeric character as a \\uXXXX escape: exact bytes whatever the client does with them."""
    return "NULL" if v is None else "E'" + "".join(c if c.isalnum() and c.isascii() else (f"\\u{ord(c):04x}" if ord(c) <= 0xFFFF else f"\\U{ord(c):08x}") for c in v) + "'"


LACKING_TEXT = ["", " ", "   ", "\t", "\n", "\r", "\r\n", "\u00a0", "\u200b", "\u200b\u200b", "\ufeff", "\u2028", "\u3000", "\u2003", "-", "--", "\u2014", "\u2013", "\u2012",
                "\u2212", ".", "..", "...", "\u2026", "?", "??", "{}", "[]", '""', "''", "()", "n.a.", "N.A.", "N/A", "N/A.", "n/a", "NA", "nil", "Nil.", "not available",
                "Not Available.", "no source", "No Source", "not traced", "Not Traced", "not traced yet", "  not   traced  ", "\tnot traced\n", "- not traced -", "pending",
                "Pending...", "TBD", "TBD.", "tbd", "TBA", "todo", "nan", "NaN", "none", "None.", "(none)", "null", "NULL", "unknown", "Unknown", "unsourced", "untraced",
                "source unidentified", "missing", "0", "false", "not\u00a0traced", "not\u00a0\u00a0traced", "n\u00ad/a", "\u00ad", "\u00ad\u00ad", "no\u00adne", "\uff2e\uff2f\uff2e\uff25", "\uff4e\uff0f\uff41", "\uff34\uff22\uff24", "\u2800", "\u2800\u2800", "\u3164", "\u115f\u1160",
                "\u034f", "\u061c", "\U000e0001\U000e0041", "\U000e007f", "\u0964", "\u0964\u0964", "\u0965", "\u200bn/a\u200b", "\ufffc", "\u0001", "\u0007\u001f", "\u007f", "@", "+-+", "\u0001 \u0002", "\u200bnot traced\u200b", "\u00a0n/a\u00a0"]
SOURCED_TEXT = ["Phaladipika 26.42", "BPHS 3.12", "PG338-339", "Sloka 42", "Surya Siddhanta 1.1", "a", "x.1", "Brihat Parashara Hora Shastra",
                "\u092c\u0943\u0939\u0924\u094d\u092a\u093e\u0930\u093e\u0936\u0930 3.12", "\u092c\u0943\u0939\u0924\u094d", "not traced in the printed edition; see BPHS 3.12",
                "1.1", "none other than Parashara (BPHS 1.1)", "BPHS 3.12 (pending verification)",
                "\u0967\u0968\u0969", "\u0905\u0927\u094d\u092f\u093e\u092f", "Adh.XXVI PG338-339 Sloka 42-44", "\u0905\u0927\u094d\u092f\u093e\u092f \u0968\u096c\u0964", "\u092c\u0943\u0939\u0924\u094d\u0964 \u0967\u0964\u0967"]


def _utf8(pg):
    return True


def _table(rows, ddl):
    return [f"CREATE TEMP TABLE s_t (k int PRIMARY KEY, c {ddl}) ON COMMIT DROP;",
            "INSERT INTO s_t VALUES " + ",".join(f"({i},{_lit(v) if not isinstance(v, tuple) else v[0]})" for i, v in enumerate(rows, 1)) + ";"]


def _lacking_ks(monkeypatch, pg, rows, ddl, kind):
    _real(monkeypatch, pg, _table(rows, ddl))
    if ac.psql("SHOW server_encoding")[0][0].upper() != "UTF8":
        pytest.skip("the disposable cluster is not UTF8: the Unicode escapes in the placeholder patterns need a UTF8 database (production is)")
    out = ac.psql(f"SELECT k FROM s_t WHERE {ac._ldgr_lacking('c', kind)} ORDER BY k")
    return [int(r[0]) for r in out]


def test_REAL_SQL_every_leak_the_review_probed_counts_as_lacking_a_source_and_real_citations_do_not(monkeypatch, disposable_pg):
    rows = LACKING_TEXT + SOURCED_TEXT + [None]
    got = _lacking_ks(monkeypatch, disposable_pg, rows, "text", "text")
    want = [i for i, v in enumerate(rows, 1) if v is None or v in LACKING_TEXT]
    assert got == want, [rows[k - 1] for k in sorted(set(got) ^ set(want))]


def test_REAL_SQL_varchar_and_the_text_array_elements_are_inspected(monkeypatch, disposable_pg):
    got = _lacking_ks(monkeypatch, disposable_pg, ["BPHS 1.1", " ", "not traced", "N/A."], "varchar(40)", "text")
    assert got == [2, 3, 4]
    arrs = [("ARRAY['BPHS 1.1']",), ("ARRAY['']",), ("ARRAY['not traced']",), ("ARRAY['BPHS 1.1','']",), ("ARRAY[]::text[]",), ("NULL",),
            ("ARRAY[NULL]::text[]",), ("ARRAY['BPHS 1.1','not traced']",), ("ARRAY['BPHS 1.1','BPHS 1.2']",), ("ARRAY[E'\\u200b']",), ("ARRAY['n.a.']",),
            ("ARRAY[E'\\u00ad']",), ("ARRAY['BPHS 1.1',E'n\\u00ad/a']",), ("ARRAY[E'\\uff2e\\uff2f\\uff2e\\uff25']",), ("ARRAY['BPHS',E'\\u2800']",), ("ARRAY[E'\\u0967\\u0968']",),
            ("ARRAY[E'\\u0905\\u0927\\u094d\\u092f\\u093e\\u092f',E'Adh.XXVI']",)]
    assert _lacking_ks(monkeypatch, disposable_pg, arrs, "text[]", "array") == [2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14, 15]


JSON_CASES = [
    ('"BPHS 1.1"', False), ('""', True), ('"not traced"', True), ('["BPHS 1.1"]', False), ('[""]', True), ('["BPHS","  "]', True), ("[]", True), ("{}", True),
    ("null", True), ("5", True), ("true", True), ('{"src":"BPHS"}', False), ('[["a"]]', False), (None, True), ('["BPHS","N/A"]', True), ('[{"src":"x"}]', False),
    ("[{}]", True), ('["a",1]', True),
    # MED-1: an object / array is a source only if some STRING LEAF passes the text test
    ('{"source":"not traced"}', True), ('{"source":""}', True), ('{"a":null}', True), ('{"a":{}}', True), ('[{"src":"n/a"}]', True),
    ('{"a":{"b":{"c":"BPHS 1.1"}}}', False), ('{"a":{"b":{"c":"n/a"}}}', True), ('{"a":["not traced","BPHS 1.1"]}', False), ('{"n":5,"b":true}', True),
    ('[{"src":"BPHS"},{"src":"TBD"}]', True), ('[["not traced"]]', True), ('{"s":"\\u00ad"}', True), ('[{"src":"\\uff2e\\uff2f\\uff2e\\uff25"}]', True),
    ('{"src":"\\u0967\\u0968\\u0969"}', False), ('{"src":"  "}', True), ('{"a":[{"b":""},{"c":"\\u200b"}]}', True), ('{"a":[{"b":""},{"c":"Sloka 42"}]}', False),
    ('{"src":"not\\u00a0traced"}', True), ('[{"a":{}},{"b":"BPHS"}]', True), ('{"src":["",""]}', True), ('{"src":[]}', True), ('{"src":{"x":[null,false,0]}}', True)]


def test_REAL_SQL_json_and_jsonb_values_scalars_arrays_objects_and_nested_leaves_are_inspected(monkeypatch, disposable_pg):
    rows = [(f"'{v}'" if v is not None else "NULL",) for v, _ in JSON_CASES]
    want = [i for i, (_, lack) in enumerate(JSON_CASES, 1) if lack]
    for ddl in ("jsonb", "json"):
        got = _lacking_ks(monkeypatch, disposable_pg, rows, ddl, "json")
        assert got == want, (ddl, [JSON_CASES[k - 1][0] for k in sorted(set(got) ^ set(want))])


def test_REAL_SQL_the_column_type_decides_what_can_carry_a_source(monkeypatch, disposable_pg):
    _real(monkeypatch, disposable_pg, ["CREATE TEMP TABLE ty_t (a text, b varchar(40), c char(5), d text[], e jsonb, f json, g boolean, h integer, i date, j numeric, k varchar(9)[]) ON COMMIT DROP;"])
    got = {c: (ac.ldgr_fetch_column_type("ty_t", c), ac.ldgr_column_kind(ac.ldgr_fetch_column_type("ty_t", c))) for c in "abcdefghijk"}
    assert got["a"] == ("text", "text") and got["b"][1] == "text" and got["c"][1] == "text" and got["d"] == ("text[]", "array")
    assert got["e"] == ("jsonb", "json") and got["f"] == ("json", "json") and got["k"][1] == "array"
    assert [got[c][1] for c in "ghij"] == [None, None, None, None]
    assert ac.ldgr_fetch_column_type("ty_t", "nope") == "" and ac.ldgr_column_kind("") is None and ac.ldgr_column_kind(None) is None


@pytest.mark.parametrize("ddl, val", [("boolean", "false"), ("boolean", "true"), ("integer", "0"), ("integer", "7"), ("numeric", "1.5"), ("date", "'2020-01-01'")])
def test_REAL_SQL_a_boolean_integer_or_date_source_column_is_no_detector_never_pass(monkeypatch, disposable_pg, ddl, val):
    _real(monkeypatch, disposable_pg, [f"CREATE TEMP TABLE b_t (k int, c {ddl}) ON COMMIT DROP;", f"INSERT INTO b_t VALUES (1,{val}),(2,{val});"])
    rec = ac.ldgr_source_declared_check("x", LS_M(col="c"), "b_t", ["k", "c"], [["k"]])[LDGR]
    assert rec["v"] == NO_DET and ddl.split("(")[0] in rec["measured"] and "only text" in rec["measured"] and rec["citation_state"] == "sourced"
    assert ac.rollup_asset("L0", {LDGR: rec})["Ldgr"]["v"] == NO_DET


def test_REAL_SQL_the_whole_declared_ldgr_check_with_the_leaks_and_the_sample_cap_of_five(monkeypatch, disposable_pg):
    rows = ["BPHS 1.1", "\t", "N/A.", "\u200b", "-", "pending", "TBD.", "nan", "BPHS 1.2"]
    _real(monkeypatch, disposable_pg, _table(rows, "text"))
    rec = ac.ldgr_source_declared_check("x", LS_M(col="c"), "s_t", ["k", "c"], [["k"]])[LDGR]
    assert rec["v"] == PARTIAL and rec["ldgr"]["rows"] == 9 and rec["ldgr"]["lacking"] == 7
    assert [x["k"] for x in rec["ldgr"]["sample"]] == [2, 3, 4, 5, 6] and len(rec["ldgr"]["sample"]) == 5 and "(first 5)" in rec["measured"]    # the cap is pinned
    _real(monkeypatch, disposable_pg, _table(["-"], "text"))
    assert ac.ldgr_source_declared_check("x", LS_M(col="c"), "s_t", ["k", "c"], [["k"]])[LDGR]["v"] == FAIL


def test_regression_the_nbsp_internal_collapse_the_soft_hyphen_and_the_fullwidth_forms_are_in_the_probe_list():
    for must in ("not\u00a0traced", "n\u00ad/a", "\uff2e\uff2f\uff2e\uff25", "\uff4e\uff0f\uff41", "\u2800", "\u3164", "\u115f\u1160", "\u034f", "\u061c", "\U000e0001\U000e0041", "\u0964"):
        assert must in LACKING_TEXT, must
    for must in ("\u0967\u0968\u0969", "\u0905\u0927\u094d\u092f\u093e\u092f", "Adh.XXVI PG338-339 Sloka 42-44"):
        assert must in SOURCED_TEXT, must


@pytest.mark.parametrize("cols, like", [(LIKE_COLS, LIKE_COLS), (PHALA_COLS, []), (["id", "name", "analysis", "valias", "aka_x"], ["valias"]), ([], []), (None, [])])
def test_the_alias_like_column_check_is_case_insensitive_and_token_based_and_leaves_a_phaladeepika_shaped_table_alone(cols, like):
    assert sorted(ac.alias_like_columns(cols)) == sorted(like)


@pytest.mark.parametrize("like", LIKE_COLS)
def test_every_alias_like_spelling_blocks_na_and_identity_only_and_a_phaladeepika_table_does_not(monkeypatch, like):
    assert ac.vocab_alias_declared_check("bg_x", VA_NA, "t", ["id", like])[ALIAS]["v"] == NO_DET
    ident = dict(VA_M_NOALIAS, identity_only=True, identity_only_why="the asset stores the canonical display names only")
    monkeypatch.setattr(ac, "alias_fetch_forms", lambda c: pytest.fail("not read"))
    assert ac.vocab_alias_declared_check("bg_x", ident, "t", ["graha", like])[ALIAS]["v"] == NO_DET
    monkeypatch.undo()
    assert ac.vocab_alias_declared_check("bg_x", VA_NA, "t", PHALA_COLS)[ALIAS]["v"] == NA
    monkeypatch.setattr(ac, "alias_fetch_forms", lambda c: FORMS)
    monkeypatch.setattr(ac, "alias_fetch_values", lambda t, v, a=None: _pairs(("Sun", None, 1)))
    assert ac.vocab_alias_declared_check("bg_x", ident, "t", PHALA_COLS)[ALIAS]["v"] == PASS


# ───────────────────────── M4: Vocab.alias without an alias column is identity only ─────────────────────────

def test_an_alias_declaration_without_an_alias_column_reads_partial_unless_identity_only_is_declared():
    r = ac.grade_vocab_alias(SPEC_PLAIN, FORMS, _pairs(("Sun", None, 1), ("Moon", None, 1)))
    assert r["v"] == PARTIAL and "identity only" in r["measured"] and "completeness leg" in r["measured"] and "identity_only: true" in r["measured"]
    ok = ac.grade_vocab_alias(SPEC_NA, FORMS, _pairs(("Sun", None, 1), ("Moon", None, 1)))
    assert ok["v"] == PASS and "identity_only declared" in ok["measured"] and "canonical display names" in ok["measured"]
    assert ac.grade_vocab_alias(SPEC_PLAIN, FORMS, _pairs(("Pluto", None, 1)))["v"] == FAIL            # an unresolved value still fails
    assert ac.grade_vocab_alias(SPEC, FORMS, _pairs(("Sun", ["Surya", "Ravi", "SUN"], 1)))["v"] == PASS    # with the alias column the full leg runs
    cell = ac.rollup_asset("L0", {ALIAS: r, "Vocab.identity": dict(v=PASS, measured="k")})["Vocab"]
    assert cell["v"] == PARTIAL


def test_bg_phaladeepika_latta_shaped_asset_reaches_pass_only_through_the_explicit_identity_only_word(monkeypatch):
    names = ["Sun", "Moon", "Mercury", "Ketu"]                                                          # the canonical display names, no alias column
    monkeypatch.setattr(ac, "alias_fetch_forms", lambda c: FORMS)
    monkeypatch.setattr(ac, "alias_fetch_values", lambda t, v, a=None: _pairs(*((n, None, 1) for n in names)))
    cols = ["graha", "direction", "count_from_graha"]
    plain = ac.vocab_alias_declared_check("bg_phaladeepika_latta", VA_M_NOALIAS, "bg_phaladeepika_latta", cols)[ALIAS]
    assert plain["v"] == PARTIAL
    ident = dict(VA_M_NOALIAS, identity_only=True, identity_only_why="graha stores the canonical display names, no alias set is carried")
    ac.validate_declarations(_doc(dict(vocab_alias=ident)))
    rec = ac.vocab_alias_declared_check("bg_phaladeepika_latta", ident, "bg_phaladeepika_latta", cols)[ALIAS]
    assert rec["v"] == PASS and "identity_only declared" in rec["measured"]


@pytest.mark.parametrize("like", LIKE_COLS)
def test_a_measured_declaration_without_an_alias_column_is_refused_beside_an_alias_like_column(monkeypatch, like):
    monkeypatch.setattr(ac, "alias_fetch_forms", lambda c: pytest.fail("not read"))
    for va in (VA_M_NOALIAS, dict(VA_M_NOALIAS, identity_only=True, identity_only_why="the asset stores the canonical display names only")):
        rec = ac.vocab_alias_declared_check("bg_x", va, "t", ["graha", like])[ALIAS]
        assert rec["v"] == NO_DET and rec["declaration_disagreements"][0]["field"] == "vocab_alias.alias_column" and like in rec["measured"]


@pytest.mark.parametrize("like", LIKE_COLS)
def test_no_alias_class_is_refused_beside_any_alias_like_column(like):
    rec = ac.vocab_alias_declared_check("bg_x", VA_NA, "t", ["id", like])[ALIAS]
    assert rec["v"] == NO_DET and "cause" not in rec


@pytest.mark.parametrize("extra, match", [
    (dict(identity_only=True, identity_only_why="the asset stores the canonical display names only", alias_column="synonyms"), "contradicts a declared alias_column"),
    (dict(identity_only=True), "identity_only_why"),
    (dict(identity_only=True, identity_only_why="TBD"), "identity_only_why"),
    (dict(identity_only=True, identity_only_why="too short"), "identity_only_why"),
    (dict(identity_only=False, identity_only_why="the asset stores the canonical display names only"), "identity_only must be true"),
    (dict(identity_only="yes", identity_only_why="the asset stores the canonical display names only"), "identity_only must be true"),
    (dict(identity_only_why="the asset stores the canonical display names only"), "only for identity_only true"),
])
def test_validator_identity_only_discipline(extra, match):
    base = dict(VA_M_NOALIAS if "alias_column" not in extra else VA_M, **extra)
    _bad(dict(vocab_alias=base), match)


def test_na_form_refuses_identity_only_fields():
    _bad(dict(vocab_alias=dict(VA_NA, identity_only=True, identity_only_why="the asset stores the canonical display names only")), "declares no alias class")


# ───────────────────────── M5: declaration quality ─────────────────────────

BAD_WHY = ["TBD", ".", "tbd tbd tbd", "too short", "a b c", "this is a todo for later review", "n/a for this asset in general", "pending a real reason here",
           "line one\rline two is longer", "line one\u2028line two is longer", "line one\u2029line two is longer", "line one\u0085line two longer", "zero\u200bwidth joiner here ok",
           "tab\there is not a visible line", " ".join(["word"] * 241), " leading space is not allowed here", "trailing space is not allowed here ", "placeholder text goes right here"]


@pytest.mark.parametrize("why", BAD_WHY)
@pytest.mark.parametrize("key, base", [("vocab_alias", VA_NA), ("vocab_alias", VA_M), ("ldgr_source", LS_NA), ("ldgr_source", LS_M())])
def test_a_placeholder_or_multiline_or_too_short_reason_is_refused_for_every_s3_form(key, base, why):
    _bad({key: dict(base, why=why)}, rf"{key}\.why")


@pytest.mark.parametrize("ev", ["platform/scripts/governance/asset_census.py:99999999", "platform/scripts/governance/asset_census.py:0",
                                "platform/scripts/governance/asset_census.py:-1", "unverified:x", "unverified:TBD", "unverified:todo later", "unverified:n/a", "unverified:short",
                                "unverified:" + "x" * 9, "unverified:one-word-only-long", "unverified:\u200b\u200b\u200b\u200b\u200b\u200b\u200b\u200b\u200b\u200b\u200b",
                                "unverified:line one\nline two longer", "platform/scripts/governance/asset_census.py\u200b:1"])
def test_evidence_must_be_a_real_line_or_a_real_description(ev):
    for key, base in (("vocab_alias", VA_M), ("ldgr_source", LS_M())):
        _bad({key: dict(base, evidence=ev)}, rf"{key}\.evidence")


def test_evidence_line_numbers_are_held_to_the_files_real_line_count():
    n = len((ac.ROOT / "platform/scripts/governance/asset_census.py").read_bytes().splitlines())
    ac.validate_declarations(_doc(dict(ldgr_source=dict(LS_M(), evidence=f"platform/scripts/governance/asset_census.py:{n}"))))
    _bad(dict(ldgr_source=dict(LS_M(), evidence=f"platform/scripts/governance/asset_census.py:{n + 1}")), "line")
    ac.validate_declarations(_doc(dict(ldgr_source=dict(LS_M(), evidence="platform/scripts/governance/asset_census.py"))))     # a bare file is fine


@pytest.mark.parametrize("key, base", [("vocab_alias", VA_NA), ("ldgr_source", LS_NA)])
def test_an_na_release_may_not_rest_on_unverified_evidence(key, base):
    _bad({key: dict(base, evidence="unverified:the L0 review sheet notes")}, "may not be `unverified:`")
    ac.validate_declarations(_doc({key: dict(base)}))
    for measured in (VA_M, LS_M()):                                          # a measured declaration may still say what it could not verify
        k = "vocab_alias" if measured is VA_M else "ldgr_source"
        ac.validate_declarations(_doc({k: dict(measured, evidence="unverified:the L0 review sheet notes")}))


def test_the_why_length_cap_is_exactly_1200_and_the_alias_like_list_is_pinned():
    ok = " ".join(["word"] * 240)
    assert len(ok) <= 1200
    ac.validate_declarations(_doc(dict(ldgr_source=dict(LS_M(), why=ok))))
    assert ac.ALIAS_LIKE_TOKENS == ("synonym", "alias", "alt_name", "alternate_name", "other_name", "also_known", "nickname", "name_variant") and ac.ALIAS_LIKE_EXACT == ("aka",)


def test_the_s2_carriage_validator_now_takes_the_s3_text_rules():
    """E6.1 follow-up (S2 strictness): the carriage `why` / `evidence` are held to S3's rules (this test pinned the opposite while S3 merged: a one-letter why was accepted)."""
    ac.validate_declarations(_doc(dict(carriage=dict(applies="D3", nature="computation", why=s2.WHY, evidence=s2.EVID))))
    for bad_why in ("w", "TBD later on", "n/a"):
        with pytest.raises(ac.DeclarationsError, match=r"carriage\.why"):
            ac.validate_declarations(_doc(dict(carriage=dict(applies="D3", nature="computation", why=bad_why, evidence=s2.EVID))))


# ───────────────────────── LOW: malformed declarations, unknown columns, carriage guards ─────────────────────────

@pytest.mark.parametrize("va", [dict(**{"class": "planet"}), dict(**{"class": "planet", "vocab_column": 7}), dict(**{"class": "sign", "vocab_column": "g"}),
                                dict(na="bogus", why="x", evidence="y"), dict(na="no_alias_class")])
def test_a_malformed_alias_declaration_that_reaches_the_check_is_no_detector_not_an_exception(va, monkeypatch):
    monkeypatch.setattr(ac, "alias_fetch_forms", lambda c: pytest.fail("not read"))
    rec = ac.vocab_alias_declared_check("bg_x", va, "t", ["graha", "synonyms"])[ALIAS]
    assert rec["v"] == NO_DET and "malformed" in rec["measured"]


@pytest.mark.parametrize("ls", [dict(source_column="c"), dict(source_column="c", citation_state="verified"), dict(source_column=7, citation_state="sourced"),
                                dict(na="bogus", why="x", evidence="y"), dict(na="no_classical_claim")])
def test_a_malformed_ldgr_declaration_that_reaches_the_check_is_no_detector_not_an_exception(ls, monkeypatch):
    monkeypatch.setattr(ac, "ldgr_fetch_source_stats", lambda *a, **k: pytest.fail("not read"))
    rec = ac.ldgr_source_declared_check("bg_x", ls, "t", ["c"])[LDGR]
    assert rec["v"] == NO_DET and "malformed" in rec["measured"]


def test_unknown_columns_of_a_declared_target_table_are_no_detector_and_only_no_table_at_all_passes_the_na_through():
    for cols in (None, [], ()):
        assert ac.vocab_alias_declared_check("bg_x", VA_NA, "a_view", cols)[ALIAS]["v"] == NO_DET
        assert ac.ldgr_source_declared_check("bg_x", LS_NA, "a_view", cols)[LDGR]["v"] == NO_DET
        assert ac.vocab_alias_declared_check("bg_x", VA_NA, None, cols)[ALIAS]["v"] == NA          # a service: no table, nothing to contradict
        assert ac.ldgr_source_declared_check("bg_x", LS_NA, None, cols)[LDGR]["v"] == NA
    rec = ac.vocab_alias_declared_check("bg_x", VA_NA, "a_view", None)[ALIAS]
    assert "cause" not in rec and ac.rollup_asset("L0", {ALIAS: rec})["Vocab"]["v"] == NO_DET


@pytest.mark.parametrize("nature, extra", [("derivation", dict(applies="D3")), ("ratified_judgment", dict(ruling="N-73"))])
def test_no_classical_claim_is_refused_beside_a_derivation_or_ratified_judgment_carriage(nature, extra):
    car = dict(nature=nature, why=s2.WHY, evidence=s2.EVID, **extra)
    _bad(dict(ldgr_source=LS_NA, carriage=car), f"contradicts a declared {nature} carriage")


def test_measure_reads_a_declared_na_on_a_view_or_an_absent_table_as_no_detector(monkeypatch, tmp_path):
    reg = {"v": na_causes._reg_row("v", "a_view"), "g": na_causes._reg_row("g", "absent_t")}
    na_causes._stub_layer(monkeypatch, tmp_path, reg, tables={"a_view": ([], [])})
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: {a_: dict(kind="data", vocab_alias=VA_NA, ldgr_source=LS_NA) for a_ in reg})
    for fn in ("alias_fetch_forms", "alias_fetch_values", "ldgr_fetch_column_type", "ldgr_fetch_source_stats"):
        monkeypatch.setattr(ac, fn, lambda *a, **k: pytest.fail("no table, no read"))
    ms = {a["asset_id"]: a["measurements"] for a in ac.measure("L0")["assets"]}
    for aid in ("v", "g"):
        assert ms[aid][ALIAS]["v"] == NO_DET and ms[aid][LDGR]["v"] == NO_DET


def test_the_declared_ldgr_check_checks_the_table_exists_in_the_measure_wiring(monkeypatch, tmp_path):
    reg = {"ghost": na_causes._reg_row("ghost", "absent_t")}
    na_causes._stub_layer(monkeypatch, tmp_path, reg, tables={})
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: {"ghost": dict(kind="data", ldgr_source=LS_M(), vocab_alias=VA_M)})
    for fn in ("alias_fetch_forms", "alias_fetch_values", "ldgr_fetch_column_type", "ldgr_fetch_source_stats"):
        monkeypatch.setattr(ac, fn, lambda *a, **k: pytest.fail("a table absent from production is never read"))
    ms = ac.measure("L0")["assets"][0]["measurements"]
    assert ms[LDGR]["v"] == NO_DET and ms[ALIAS]["v"] == NO_DET and ms[LDGR]["citation_state"] == "sourced"


# ───────────────────────── pin 12 ─────────────────────────

def test_revision_12_pins_the_s3_content():
    assert ac.REGISTRY_REVISION >= 12
    assert ac.CRITERION_REGISTRY[ALIAS]["revision"] == 2 and ac.CRITERION_REGISTRY[LDGR]["revision"] == 4      # 3 at the S3 merge (pin 12), 4 at pin 24 (C2(ii))
    assert r13.S3_IDS <= set(ac.NA_RULE_DECISIONS) and r13.S3_IDS <= r13.DECLARED_IDS
    for rid in r13.S3_IDS:
        why = ac.NA_RULE_DECISIONS[rid]
        assert "N-72" in why and "N-73" in why and "A5" in why                      # the ruling it rests on, and that a column pattern stays refused


def test_the_fingerprint_moves_with_each_s3_part(monkeypatch):
    fp = ac.registry_fingerprint()
    for rid in r13.S3_IDS:
        monkeypatch.setattr(ac, "NA_RULE_DECISIONS", {k: v for k, v in ac.NA_RULE_DECISIONS.items() if k != rid})
        assert ac.registry_fingerprint() != fp
        monkeypatch.undo()
    monkeypatch.setattr(ac, "NA_CAUSES", {**ac.NA_CAUSES, ALIAS: ()})
    assert ac.registry_fingerprint() != fp
    monkeypatch.undo()
    monkeypatch.setattr(ac, "CRITERION_REGISTRY", {**ac.CRITERION_REGISTRY, LDGR: dict(ac.CRITERION_REGISTRY[LDGR], revision=2)})
    assert ac.registry_fingerprint() != fp


# ───────────────────────── the cells this changes today (saved census, read only) ─────────────────────────

SAVED = pathlib.Path("/Users/Dev/suvarna-evidence/census_fresh/1e5781a")


@pytest.mark.skipif(not (SAVED / "census_L0.json").exists(), reason="the saved baseline census is not on this machine (CI)")
def test_on_the_saved_census_and_the_committed_declarations_no_vocab_or_ldgr_verdict_moves():
    """No asset declares either key in the committed file, so the 254 Vocab/Ldgr cells keep their pre-S3 verdicts."""
    from collections import Counter
    decl = ac.load_asset_declarations()
    vocab, ldgr, moved = Counter(), Counter(), []
    for L in ("L0", "L1", "L2", "L3", "L4", "L5"):
        d = json.loads((SAVED / f"census_{L}.json").read_text(encoding="utf-8"))
        saved = d["rollup"]["layers"][L]
        now = ac.rollup_census(d[L], {a["asset_id"]: ac.facts_for_asset(a, decl) for a in d[L]["assets"]})
        for aid, cells in now.items():
            for g, c in (("Vocab", vocab), ("Ldgr", ldgr)):
                c[cells[g]["v"]] += 1
                if cells[g]["v"] != saved[aid][g]["v"]:
                    moved.append((aid, g, saved[aid][g]["v"], cells[g]["v"]))
    assert moved == []
    assert dict(vocab) == {"FAIL": 1, "NO_DETECTOR": 126} and dict(ldgr) == {"PASS": 70, "PARTIAL": 1, "NO_DETECTOR": 56}


# ───────────────────────── REAL SQL: the same statements on a disposable Postgres ─────────────────────────

def _real(monkeypatch, pg, setup):
    import subprocess
    pre = list(setup)

    def fake_psql(sql, sep="\x1f", timeout=None):
        script = "BEGIN;\n" + "\n".join(pre) + f"\n{sql};\nROLLBACK;\n"
        p = subprocess.run([str(pg.bin_dir / "psql"), pg.url, "-tAX", "-q", "-F", sep, "-v", "ON_ERROR_STOP=1", "-f", "-"], input=script,
                           capture_output=True, text=True, timeout=30)
        if p.returncode != 0:
            raise ac.Unknown((p.stderr.strip().splitlines() or ["psql failed"])[0])
        return s2._psql_lines(p.stdout, sep)
    monkeypatch.setattr(ac, "psql", fake_psql)


ONTOLOGY_SQL = ["CREATE TEMP TABLE brahma_ontology (entity_class text, canonical_id text, canonical_name_en text, synonyms text[]) ON COMMIT DROP;",
                "INSERT INTO brahma_ontology VALUES ('planet','sun','Sun',ARRAY['Surya','Ravi','SUN']),('planet','moon','Moon',ARRAY['Chandra','MOON']),"
                "('planet','ketu','Ketu',ARRAY[]::text[]),('sign','aries','Aries',ARRAY['Mesha']);"]


def test_REAL_SQL_the_alias_reads_and_the_whole_declared_alias_check_run_end_to_end(monkeypatch, disposable_pg):
    _real(monkeypatch, disposable_pg, ONTOLOGY_SQL + [
        "CREATE TEMP TABLE asset_t (graha text, synonyms text[]) ON COMMIT DROP;",
        "INSERT INTO asset_t VALUES ('Sun',ARRAY['Surya','Ravi','SUN']),('Sun',ARRAY['Surya','Ravi','SUN']),('Moon',ARRAY['Chandra','MOON']),('Ketu',NULL);"])
    forms = ac.alias_fetch_forms("planet")
    assert [f["canonical_id"] for f in forms] == ["ketu", "moon", "sun"] and forms[2]["synonyms"] == ["Surya", "Ravi", "SUN"]     # the class filter holds
    pairs = ac.alias_fetch_values("asset_t", "graha", "synonyms")
    assert sorted((p["v"], p["n"]) for p in pairs) == [("Ketu", 1), ("Moon", 1), ("Sun", 2)]
    assert ac.vocab_alias_declared_check("bg_x", VA_M, "asset_t", ["graha", "synonyms"])[ALIAS]["v"] == PASS


def test_REAL_SQL_a_synonym_in_the_ontology_missing_from_the_asset_flips_the_cell(monkeypatch, disposable_pg):
    _real(monkeypatch, disposable_pg, ONTOLOGY_SQL + [
        "CREATE TEMP TABLE asset_t (graha text, synonyms text[]) ON COMMIT DROP;",
        "INSERT INTO asset_t VALUES ('Sun',ARRAY['Surya','SUN']),('Moon',ARRAY['Chandra','MOON']);"])
    rec = ac.vocab_alias_declared_check("bg_x", VA_M, "asset_t", ["graha", "synonyms"])[ALIAS]
    assert rec["v"] == FAIL and rec["alias"]["missing_synonyms"] == {"sun": ["Ravi"]}
    assert ac.vocab_alias_declared_check("bg_x", VA_M_NOALIAS, "asset_t", ["graha", "synonyms"])[ALIAS]["v"] == NO_DET   # M4: beside a synonyms column an alias_column must be declared


def test_REAL_SQL_an_unresolved_vocabulary_value_fails_and_a_jsonb_alias_column_is_read(monkeypatch, disposable_pg):
    _real(monkeypatch, disposable_pg, ONTOLOGY_SQL + [
        "CREATE TEMP TABLE asset_t (graha text, synonyms jsonb) ON COMMIT DROP;",
        "INSERT INTO asset_t VALUES ('Sun','[\"Surya\",\"Ravi\",\"SUN\"]'),('Pluto','[]');"])
    rec = ac.vocab_alias_declared_check("bg_x", VA_M, "asset_t", ["graha", "synonyms"])[ALIAS]
    assert rec["v"] == FAIL and list(rec["alias"]["unresolved"]) == ["Pluto"] and rec["alias"]["missing_synonyms"] == {}


def test_REAL_SQL_the_source_stats_count_null_blank_and_not_traced_as_lacking_and_name_the_rows(monkeypatch, disposable_pg):
    _real(monkeypatch, disposable_pg, [
        "CREATE TEMP TABLE rules_t (rule_id text PRIMARY KEY, citation text) ON COMMIT DROP;",
        "INSERT INTO rules_t VALUES ('r1','Phaladipika 26.42'),('r2',NULL),('r3','   '),('r4','Not Traced'),('r5',' none '),('r6','BPHS 3.12');"])
    st = ac.ldgr_fetch_source_stats("rules_t", "citation", ["rule_id"])
    assert (st["rows"], st["lacking"]) == (6, 4) and [s["rule_id"] for s in st["sample"]] == ["r2", "r3", "r4", "r5"]
    rec = ac.ldgr_source_declared_check("bg_x", LS_M("sourced"), "rules_t", ["rule_id", "citation"], [["rule_id"]])[LDGR]
    assert rec["v"] == PARTIAL and '"r4"' in rec["measured"] and rec["citation_state"] == "sourced"
    assert ac.rollup_asset("L0", {LDGR: rec})["Ldgr"]["v"] == PARTIAL
    unsrc = ac.ldgr_source_declared_check("bg_x", LS_M("unsourced"), "rules_t", ["rule_id", "citation"], [["rule_id"]])[LDGR]
    assert ac.rollup_asset("L0", {LDGR: unsrc})["Ldgr"]["v"] == NO_DET


def test_REAL_SQL_a_fully_sourced_column_passes_and_a_text_array_or_jsonb_source_is_read(monkeypatch, disposable_pg):
    _real(monkeypatch, disposable_pg, [
        "CREATE TEMP TABLE a_t (k int, c text[]) ON COMMIT DROP;", "INSERT INTO a_t VALUES (1,ARRAY['BPHS 1.1']),(2,ARRAY['BPHS 1.2']);",
        "CREATE TEMP TABLE b_t (k int, c jsonb) ON COMMIT DROP;", "INSERT INTO b_t VALUES (1,'[\"BPHS 1.1\"]'),(2,'[]'),(3,NULL);"])
    assert ac.ldgr_source_declared_check("x", LS_M(col="c"), "a_t", ["k", "c"], [])[LDGR]["v"] == PASS
    r = ac.ldgr_source_declared_check("x", LS_M(col="c"), "b_t", ["k", "c"], [["k"]])[LDGR]
    assert r["v"] == PARTIAL and [s["k"] for s in r["ldgr"]["sample"]] == [2, 3]
