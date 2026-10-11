"""test_n150_declarations_schema.py: the N-150 / N-151 declarations SCHEMA (REGISTRY_REVISION 26): `source`, `prose_none`, `produced_tables`.

Pure: no database, no register, no cloud. The validator checks SHAPE only; the detectors that read these forms are separate commits. Every form is inert until an asset declares it, so the
committed declarations file must still validate unchanged (first test). Synthetic assets only."""
from __future__ import annotations

import copy
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

EV = "platform/scripts/governance/asset_census.py:1"
WHY = "the reviewed reason this declaration is true"


def _doc(entry):
    return {"version": "9.9.9", "kind_enum": list(ac.DECLARED_KINDS), "assets": {"x_asset": entry}}


def _ok(entry):
    return ac.validate_declarations(_doc(entry))["x_asset"]


def _bad(entry, match):
    with pytest.raises(ac.DeclarationsError, match=match):
        ac.validate_declarations(_doc(entry))


def _table(**kw):
    d = dict(level="table", why=WHY, evidence=EV)
    d.update(kw)
    return {"source": d}


def _row(*cols, **kw):
    d = dict(level="row", columns=list(cols), why=WHY, evidence=EV)
    d.update(kw)
    return {"source": d}


# ───────────────────────── the committed file is unchanged ─────────────────────────

RESIDUAL_PROSE_NONE = ["bg_class_lifetime_counts", "bg_class_priors", "bg_formula_constants", "bg_ghatana", "bg_gochara_citation_resolution", "bg_kota_chakra_rings", "bg_medical_mappings", "bg_nakshatra_medical", "bg_parihara_rules", "bg_prashna_rules", "bg_sign_medical", "bg_texts", "bg_vidhi_floors", "bg_vidhi_primitives"]      # residual declaration batch (POST-#3176 item 1; minus bg_dasha_systems, bg_nakshatra, bg_reference: SS audit 2026-10-06): seed-loader assets whose every text column is a source / identifier / transcription column, read N/A offline by grade_prose_none


def test_the_committed_declarations_file_validates_and_the_new_forms_are_declared_only_where_filled():
    """The L0 / L1 / L2 fills (N-151 `source`, N-150 `produced_tables`) are the only declarations of the new forms so far; `prose_none` is declared by no asset."""
    decl = ac.load_asset_declarations()
    assert decl
    for a, e in decl.items():
        if "source" in e:
            assert a.startswith(("bg_", "ga_", "bo_")) and ac.source_declaration_problem(e["source"], e, a) is None, a
        if "produced_tables" in e:
            assert a.startswith(("bg_", "ga_", "bo_")) and ac.produced_tables_problem(e) is None, a
    assert sorted(a for a, e in decl.items() if "prose_none" in e) == sorted(["bg_doshas", "bg_ephemeris", "bg_gochara_arcs", "bg_kp_sublord_division", "bg_ontology", "bg_transit_engine", "bg_yogas", "bo_laksana_rerank", "bo_samvada", "bo_drishti", *RESIDUAL_PROSE_NONE, "ga_ayurdaya", "ga_fact_identity", "ga_medical", "ga_prashna", "ga_vastu", "bg_cohort", "bg_sky_calendar", "ga_dashas", "ga_transit_anchors", "bg_concordance", "bg_text_index", "bg_muhurta_lattice", "bg_nakshatra", "bg_vastu_directions", "bg_transit_rules", "bg_dignity_reference", "bg_reference", "bg_dasha_systems", "ga_sensitive_degree"])      # E5.7 fills; + FORM-GAP (N-191, declarations 1.40.0 / 1.41.0): the assets whose only text columns are closed vocabularies or declared source / provenance columns


def test_the_new_keys_are_known_entry_keys_and_the_existing_carriage_and_vocab_alias_fields_are_kept():
    for k in ("source", "prose_none", "produced_tables", "carriage", "vocab_alias", "prose_fields"):
        assert k in ac._DECL_ENTRY_KEYS


# ───────────────────────── source: N/A forms ─────────────────────────

@pytest.mark.parametrize("form", ["no_data", "no_claims"])
def test_source_na_forms_are_accepted(form):
    _ok({"source": dict(na=form, why=WHY, evidence=EV)})


def test_source_na_refuses_unknown_form_extra_fields_and_unverified_evidence():
    _bad({"source": dict(na="no_classical_claim", why=WHY, evidence=EV)}, "na must be")
    _bad({"source": dict(na="no_data", kind="K2", why=WHY, evidence=EV)}, "declares no source")
    _bad({"source": dict(na="no_data", why=WHY, evidence="unverified: somewhere in the writer")}, "unverified")
    _bad({"source": dict(na="no_data", why="n/a", evidence=EV)}, "why")


# ───────────────────────── source: table level ─────────────────────────

def test_table_level_k1_k2_k3_are_accepted():
    _ok(_table(kind="K1", citation="Brihat Parashara Hora Shastra", locus="chapter 3, verses 12-14", citation_state="sourced"))
    _ok(_table(kind="K2", decision_id="N-150"))
    _ok(_table(kind="K3", generator="bg_cohort_builder", method="seeded sampling", seed="20260101"))
    _ok(_table(kind="K3", dataset="swiss ephemeris", method="direct lookup", version="2.10"))


def test_table_level_refusals():
    _bad(_table(kind="K1", citation="BPHS", locus="ch 3"), "citation_state")                       # a citation is never assumed verified
    _bad(_table(kind="K1", citation="BPHS", citation_state="sourced"), "needs locus")
    _bad(_table(kind="K2", decision_id="ratified"), "not a decision id")                          # a bare word is not a source
    _bad(_table(kind="K2"), "needs decision_id")
    _bad(_table(kind="K3", generator="g", method="m"), "a version, a seed or a version_digest")
    _bad(_table(kind="K3", generator="g", dataset="d", method="m", seed="1"), "exactly one of generator")
    _bad(_table(kind="K3", generator="g", seed="1"), "needs method")
    _bad(_table(kind="LEDGER"), "kind K1, K2 or K3")
    _bad(_table(kind="K2", decision_id="N-1", locus="ch 1"), "not a field of a K2")
    _bad(_table(kind="K2", decision_id="N-1", columns=[{"column": "c", "kinds": ["K2"]}]), "names no columns")
    _bad(_table(kind="K1", citation="BPHS", locus="ch 3", citation_state="verified"), "citation_state")
    _bad({"source": dict(level="table", kind="K2", decision_id="N-1", evidence=EV)}, "why")
    _bad({"source": dict(level="sheet", why=WHY, evidence=EV)}, "level must be")
    _bad({"source": dict(level="table", kind="K2", decision_id="N-1", why=WHY, evidence=EV, bogus=1)}, "unknown field")


# ───────────────────────── source: row level ─────────────────────────

def test_row_level_entries_are_accepted():
    _ok(_row({"column": "citation_or_ratification", "kinds": ["K1", "K2"]}, citation_state="sourced"))
    _ok(_row({"column": "ratified_by", "kinds": ["K2"], "id_prefixes": ["N", "AR"]}))
    _ok(_row({"column": "constituent_facts_array", "kinds": ["LEDGER"]}))
    _ok(_row({"kinds": ["K3"], "generator_column": "gen", "method_column": "meth", "seed_column": "seed"}))
    _ok(_row({"column": "src", "kinds": ["K1"]}, {"column": "ratified_by", "kinds": ["K2"]}, citation_state="sourced_ocr_unverified"))


def test_row_level_refusals():
    _bad(_row({"column": "c", "kinds": ["K1"]}), "citation_state")
    _bad(_row({"column": "c", "kinds": ["K2", "LEDGER"]}), "LEDGER")
    _bad(_row({"column": "c", "kinds": ["K1", "K3"]}, citation_state="sourced"), "K3 is declared alone")
    _bad(_row({"column": "c", "kinds": ["K2", "K2"]}), "distinct")
    _bad(_row({"column": "c", "kinds": ["K9"]}), "distinct kinds")
    _bad(_row({"column": "c", "kinds": ["K1"], "id_prefixes": ["N"]}, citation_state="sourced"), "id_prefixes is only")
    _bad(_row({"column": "c", "kinds": ["K2"], "id_prefixes": ["n"]}), "upper-case")
    _bad(_row({"column": "bad col", "kinds": ["K2"]}), "identifier")
    _bad(_row({"kinds": ["K3"], "method_column": "m", "version_column": "v"}), "exactly one of generator_column")
    _bad(_row({"kinds": ["K3"], "generator_column": "g", "version_column": "v"}), "method_column")
    _bad(_row({"kinds": ["K3"], "generator_column": "g", "method_column": "m"}), "version_column or seed_column")
    _bad(_row({"kinds": ["K3"], "generator_column": "g", "method_column": "m", "seed_column": "s", "column": "c"}), "not `column`")
    _bad(_row({"column": "c", "kinds": ["K2"], "generator_column": "g"}), "belong to a K3")
    _bad(_row({"column": "c", "kinds": ["K2"]}, {"column": "c", "kinds": ["LEDGER"]}), "named twice")
    _bad(_row(), "needs `columns`")
    _bad(_row(*[{"column": f"c{i}", "kinds": ["K2"]} for i in range(ac.SOURCE_MAX_COLUMNS + 1)]), "needs `columns`")
    _bad(_row({"column": "c", "kinds": ["K2"], "bogus": 1}), "unknown field")
    _bad({"source": dict(level="row", kind="K2", columns=[{"column": "c", "kinds": ["K2"]}], why=WHY, evidence=EV)}, "table-level field")


def test_source_beside_the_older_ldgr_source_is_refused():
    e = _table(kind="K2", decision_id="N-150")
    e["ldgr_source"] = dict(source_column="c", citation_state="sourced", why=WHY, evidence=EV)
    _bad(e, "not both")


# ───────────────────────── prose_none ─────────────────────────

def _pn(closed=None, **kw):
    d = dict(why=WHY, closed_columns=[] if closed is None else closed)
    d.update(kw)
    return {"prose_fields": [], "evidence": {"prose_fields": EV}, "prose_none": d}


def _cc(**kw):
    d = dict(column="graha", values=["Sun", "Moon"], why="graha is a closed label set of the nine grahas")
    d.update(kw)
    return d


def test_prose_none_accepts_the_declared_none_forms():
    _ok(_pn())
    _ok(_pn([_cc(), _cc(column="blob", values=None, no_string_leaves=True), _cc(table="other_t", column="graha")]))


def test_prose_none_refusals():
    _bad({"prose_fields": None, "prose_none": dict(why=WHY, closed_columns=[])}, "qualifies a declared prose_fields")
    _bad({"prose_fields": ["narrative"], "evidence": {"prose_fields": EV}, "prose_none": dict(why=WHY, closed_columns=[])}, "qualifies a declared prose_fields")
    _bad(_pn(why="x"), "why")
    _bad(_pn([_cc(values=None)]), "exactly one of values")
    _bad(_pn([_cc(no_string_leaves=True)]), "exactly one of values")
    _bad(_pn([_cc(values=None, no_string_leaves=False)]), "no_string_leaves must be true")
    _bad(_pn([_cc(values=[])]), "values must be")
    _bad(_pn([_cc(values=["a", "a"])]), "values must be")
    _bad(_pn([_cc(values=[" "])]), "values must be")
    _bad(_pn([_cc(), _cc()]), "listed twice")
    _bad(_pn([_cc(column="bad col")]), "identifier")
    _bad(_pn([_cc(table="bad t")]), "table must be")
    _bad(_pn([_cc(why="n/a")]), "why")
    _bad(_pn([_cc(bogus=1)]), "unknown field")
    _bad(_pn(closed=[_cc(column=f"c{i}") for i in range(ac.PROSE_NONE_MAX_COLUMNS + 1)]), "closed_columns must be")
    _bad({**_pn(), "prose_none": dict(why=WHY)}, "closed_columns must be")
    _bad({**_pn(), "prose_none": "none"}, "must be an object")
    _bad({**_pn(), "prose_none": dict(why=WHY, closed_columns=[], bogus=1)}, "unknown field")


def test_prose_none_is_refused_beside_a_prose_coupling():
    e = _pn()
    e["prose_coupling"] = dict(to="carriage_d1", columns=["c"], why="transcription checked by D1", evidence=EV)
    _bad(e, "prose_coupling|not both")


# ───────────────────────── produced_tables ─────────────────────────

def test_produced_tables_accepts_a_declared_set_and_exposes_it_as_a_fact():
    e = _ok({"produced_tables": [dict(table="chart_dashas"), dict(table="chart_facts", filter=dict(column="fact_category", equals="dasha_scope_cap"), why="the dasha scope cap rows it writes")]})
    assert ac.declared_produced_tables(e) == [dict(table="chart_dashas", filter=None), dict(table="chart_facts", filter=dict(column="fact_category", equals="dasha_scope_cap"))]
    facts = ac.declared_facts({"x_asset": e}, "x_asset")
    assert facts["declared_produced_tables"] == ac.declared_produced_tables(e)
    assert ac.produced_tables_extra(e, ["chart_dashas", "chart_facts", "chart_extra"]) == ["chart_extra"]      # an undeclared extra table is named, never tolerated
    assert ac.produced_tables_extra(e, ["chart_dashas"]) == []


def test_an_undeclared_produced_set_is_unknown_not_empty():
    assert ac.declared_produced_tables({}) is None
    assert ac.produced_tables_extra({}, ["t"]) is None
    assert "declared_produced_tables" not in ac.declared_facts({"x_asset": {"kind": "data"}}, "x_asset")


def test_produced_tables_refusals():
    _bad({"produced_tables": []}, "list of 1 to")
    _bad({"produced_tables": "chart_dashas"}, "list of 1 to")
    _bad({"produced_tables": [dict(table="bad t")]}, "table must be")
    _bad({"produced_tables": [dict(table="t", filter=dict(column="c"))]}, "filter must be")
    _bad({"produced_tables": [dict(table="t", filter=dict(column="c", equals=" "))]}, "filter must be")
    _bad({"produced_tables": [dict(table="t"), dict(table="t")]}, "listed twice")
    _bad({"produced_tables": [dict(table="t", bogus=1)]}, "unknown field")
    _bad({"produced_tables": [dict(table="t", why="n/a")]}, "why")
    _bad({"produced_tables": [dict(table=f"t{i}") for i in range(ac.PRODUCED_MAX_TABLES + 1)]}, "list of 1 to")
    assert ac.produced_tables_extra({"produced_tables": [dict(table="t")]}, ["t", "u"]) == ["u"]


def test_the_doc_level_field_lists_are_checked_when_present():
    doc = _doc({})
    doc["source_declaration_fields"] = list(ac.SOURCE_DECL_FIELDS)
    ac.validate_declarations(copy.deepcopy(doc))
    doc["source_declaration_fields"] = ["na"]
    with pytest.raises(ac.DeclarationsError, match="source_declaration_fields"):
        ac.validate_declarations(doc)
    json.dumps(ac.SOURCE_DECL_FIELDS)


# ───────────────────────── a placeholder is no source (review MED) ─────────────────────────

@pytest.mark.parametrize("v", ["TBD", "tbd", "TODO", "none", "n/a", "N/A", "xxx", "tbc", "TBC", "?", "-", "unsourced", "UNSOURCED - no doctrine", "classical_tradition", "Classical Tradition"])
def test_k1_citation_and_locus_refuse_placeholders(v):
    _bad(_table(kind="K1", citation=v, locus="ch 3", citation_state="sourced"), "citation")
    _bad(_table(kind="K1", citation="BPHS", locus=v, citation_state="sourced"), "locus")


@pytest.mark.parametrize("v", ["TBD", "todo", "none", "n/a", "xxx", "tbc", "?", "unsourced"])
def test_k3_fields_refuse_placeholders(v):
    base = dict(kind="K3", generator="bg_cohort_builder", method="seeded sampling", version="2.10")
    for f in ("generator", "method", "version"):
        _bad(_table(**{**base, f: v}), f)
    _bad(_table(kind="K3", dataset=v, method="lookup", seed="1"), "dataset")
    _bad(_table(kind="K3", generator="g", method="m", seed=v), "seed")
    _bad(_table(kind="K3", generator=v, method=v, version="0"), "generator")                         # the reviewer's case: placeholder generator and method beside version 0


@pytest.mark.parametrize("v", ["TBD-0", "TODO1", "N-0", "XXX-000", "none-1", "TBD-1", "tbc-4", "NA-2", "N-", "ratified", "N", "1", "n/a-1"])
def test_k2_decision_id_refuses_placeholders_and_a_zero_number(v):
    _bad(_table(kind="K2", decision_id=v), "decision_id")


@pytest.mark.parametrize("v", ["N-150", "D-4", "F-2", "N-72a", "AR-12", "N150"])
def test_k2_real_decision_ids_are_accepted(v):
    _ok(_table(kind="K2", decision_id=v))


def test_a_produced_filter_value_refuses_a_placeholder():
    for v in ("TBD", "none", "?", "n/a"):
        _bad({"produced_tables": [dict(table="t", filter=dict(column="c", equals=v))]}, "filter must be")
    _ok({"produced_tables": [dict(table="t", filter=dict(column="c", equals="dasha_scope_cap"))]})


def test_produced_tables_extra_never_drops_a_non_string_observed_name():
    e = {"produced_tables": [dict(table="t")]}
    assert ac.produced_tables_extra(e, ["t", None, 5, ("t",)]) == sorted(["None", "5", "('t',)"])
    assert ac.produced_tables_extra(e, ["t"]) == []


# ───────────────────────── provenance_columns (N-156 F4) ─────────────────────────

def test_provenance_columns_are_accepted_on_a_measured_source_and_refused_elsewhere():
    _ok(_table(kind="K2", decision_id="N-150", provenance_columns=["source_ref", "content_sha256"]))
    _ok(_row({"column": "src", "kinds": ["K2"]}, provenance_columns=["content_sha256"]))
    _bad(_table(kind="K2", decision_id="N-150", provenance_columns=[]), "provenance_columns")
    _bad(_table(kind="K2", decision_id="N-150", provenance_columns=["a", "a"]), "provenance_columns")
    _bad(_table(kind="K2", decision_id="N-150", provenance_columns=["bad col"]), "provenance_columns")
    _bad(_table(kind="K2", decision_id="N-150", provenance_columns="source_ref"), "provenance_columns")
    _bad(_table(kind="K2", decision_id="N-150", provenance_columns=[f"c{i}" for i in range(ac.SOURCE_MAX_COLUMNS + 1)]), "provenance_columns")
    _bad({"source": dict(na="no_data", why=WHY, evidence=EV, provenance_columns=["a"])}, "declares no source")


# ───────────────────────── LEDGER path / resolves_to, except_when, K3 version_digest (SS-accepted shapes) ─────────────────────────

DIG = "a" * 64


def test_ledger_entries_accept_a_json_path_and_a_resolution_target():
    _ok(_row({"column": "constituent_refs_jsonb", "kinds": ["LEDGER"], "path": "$.signal_ids", "resolves_to": "bodha_msr_signals.signal_id"}))
    _ok(_row({"column": "derivation", "kinds": ["LEDGER"], "path": "$.factor_ledger[*]", "resolves_to": "chart_facts.fact_id"}))
    _ok(_row({"column": "facts", "kinds": ["LEDGER"]}))
    _ok(_row({"column": "derivation", "kinds": ["LEDGER"], "path": "$.a.b[*].c"}))


@pytest.mark.parametrize("bad,why", [
    (dict(path="signal_ids"), "JSON path"), (dict(path="$"), "JSON path"), (dict(path="$.a[0]"), "JSON path"), (dict(path="$.a[*][*]"), "JSON path"), (dict(path="$.a b"), "JSON path"),
    (dict(path="$.a'; DROP"), "JSON path"), (dict(resolves_to="chart_facts.id"), "resolves_to"), (dict(resolves_to="other.signal_id"), "resolves_to"),
])
def test_ledger_path_and_target_refusals(bad, why):
    _bad(_row({"column": "c", "kinds": ["LEDGER"], **bad}), why)


def test_path_and_resolves_to_are_for_ledger_entries_only():
    _bad(_row({"column": "c", "kinds": ["K2"], "path": "$.a"}), "belong to a LEDGER")
    _bad(_row({"column": "c", "kinds": ["K1"], "resolves_to": "chart_facts.fact_id"}, citation_state="sourced"), "belong to a LEDGER")


def test_except_when_is_a_declared_row_filter_on_any_entry():
    _ok(_row({"column": "derivation_chain", "kinds": ["K1"], "except_when": {"column": "grounding_tier", "equals": "pratyaksa"}}, citation_state="sourced"))
    _ok(_row({"column": "facts", "kinds": ["LEDGER"], "except_when": {"column": "tier", "equals": "x"}}))
    for bad in ({"column": "t"}, {"equals": "x"}, {"column": "t", "equals": " "}, {"column": "t", "equals": "a\\b"}, {"column": "bad col", "equals": "x"}, {"column": "t", "equals": "x", "z": 1}, "t=x", {"column": "t", "equals": "x" * 201}):
        _bad(_row({"column": "c", "kinds": ["K2"], "except_when": bad}), "except_when")
    _bad(_row({"column": "c", "kinds": ["K2"], "except_when": {"column": "c", "equals": "x"}}), "own source column")


def test_k3_accepts_a_code_digest_as_its_version():
    _ok(_table(kind="K3", generator="ga_transit_anchors", method="direct transcription", version_digest={"file": "platform/scripts/governance/carriage_d1.py", "sha256": DIG}))
    _bad(_table(kind="K3", generator="g", method="m"), "version_digest")
    for vd in ({"file": "x.py"}, {"file": "x.py", "sha256": "A" * 64}, {"file": "x.py", "sha256": "a" * 63}, {"file": "/etc/passwd", "sha256": DIG}, {"file": "../x.py", "sha256": DIG},
               {"file": "", "sha256": DIG}, "x.py", {"file": "x.py", "sha256": DIG, "z": 1}):
        _bad(_table(kind="K3", generator="g", method="m", version_digest=vd), "version_digest")
    _bad(_table(kind="K2", decision_id="N-150", version_digest={"file": "x.py", "sha256": DIG}), "K3 source")
    _bad(_row({"column": "c", "kinds": ["K2"]}, version_digest={"file": "x.py", "sha256": DIG}), "table-level")


def test_the_committed_declarations_file_loads_and_every_doc_level_field_list_equals_its_code_constant():
    """Guard (E5.7): a schema commit that extends a *_DECL_FIELDS tuple must update the doc-level `<name>_declaration_fields` list in the same commit, or the file stops loading."""
    import json
    ac.load_asset_declarations()
    raw = json.loads(ac.DECLARATIONS_PATH.read_text(encoding="utf-8"))
    pairs = {"source_declaration_fields": ac.SOURCE_DECL_FIELDS, "source_column_declaration_fields": ac.SOURCE_COLUMN_FIELDS,
             "prose_none_declaration_fields": ac.PROSE_NONE_DECL_FIELDS, "prose_none_column_declaration_fields": ac.PROSE_NONE_COLUMN_FIELDS,
             "produced_table_declaration_fields": ac.PRODUCED_TABLE_FIELDS}
    for k, v in pairs.items():
        assert raw[k] == list(v), k


def test_every_prose_none_transcription_and_identifier_pointer_names_its_column_review_low_6():
    """A transcription / identifier entry says WHERE the column is written; its evidence line (+-3 lines) must mention the column, never a module docstring or an unrelated line."""
    import re
    bad = []
    for a, e in ac.load_asset_declarations().items():
        pn = e.get("prose_none")
        if not pn:
            continue
        for key in ("transcription_columns", "identifier_columns"):
            for t in pn.get(key) or []:
                f, l = t["evidence"].rsplit(":", 1)
                lines = (ac.ROOT / f).read_text(encoding="utf-8", errors="replace").splitlines()
                win = " ".join(lines[max(0, int(l) - 4):int(l) + 3])
                if not re.search(r"\b" + re.escape(t["column"]) + r"\b", win):
                    bad.append((a, key, t["column"], t["evidence"]))
    assert bad == [], bad[:5]


def test_a_check_closed_column_is_declared_closed_not_a_transcription_review_low_6():
    pn = ac.load_asset_declarations()["bg_parihara_rules"]["prose_none"]
    assert "extraction_context" not in {t["column"] for t in pn["transcription_columns"]}
    cc = [c for c in pn["closed_columns"] if c["column"] == "extraction_context"]
    assert len(cc) == 1 and cc[0]["values"] == ["mula_sutra_citation", "translator_gloss_in_narrative"] and cc[0]["table"] == "bg_parihara_rules"
    assert "migrations/524_bg_parihara_rules_muhurta_extraction_context.sql" in cc[0]["why"]
    sql = (ac.ROOT / "platform/supabase/migrations/524_bg_parihara_rules_muhurta_extraction_context.sql").read_text(encoding="utf-8")
    assert "'mula_sutra_citation', 'translator_gloss_in_narrative'" in sql                  # the values are the CHECK constraint's own


def test_bg_ghatana_and_bg_yogas_judge_only_the_columns_their_writer_writes_review_low_6():
    decl = ac.load_asset_declarations()
    for a, gone in (("bg_ghatana", {"evidence_requirements", "kill_switch_criteria", "matching_rules"}), ("bg_yogas", {"result_class", "strength_formula_ref", "bhanga_rules_jsonb"})):
        pn = decl[a]["prose_none"]
        assert pn.get("column_scope") == "written" and not (gone & {t["column"] for t in pn["transcription_columns"]}), a
