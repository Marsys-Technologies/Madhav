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

def test_the_committed_declarations_file_still_validates_and_declares_none_of_the_new_forms():
    decl = ac.load_asset_declarations()
    assert decl
    assert not [a for a, e in decl.items() if any(k in e for k in ("source", "prose_none", "produced_tables"))]


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
    _bad(_table(kind="K3", generator="g", method="m"), "version or a seed")
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
