"""test_e6_1_declarations.py — E6.1 declarations packet (N-22 ruling; SS decisions 2026-09-30).

`asset_declarations.json` holds per asset the declared FACTS `kind`, `carriage`, `prose_fields` (+ evidence
pointers); `load_asset_declarations()` reads and validates it; `facts_for_asset(record, declarations)` merges the
declared facts under `declared_*` keys. Declarations are facts only: no criterion, N/A rule or verdict changes,
a declared kind that disagrees with the registry is REPORTED (never preferred), and an absent asset or a null
field is UNKNOWN. Offline: no database.
"""
from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import asset_census as ac  # noqa: E402

FIXTURE = json.loads((HERE / "fixtures" / "census_cells_2026-09-30.json").read_text(encoding="utf-8"))
REGISTRY_IDS = sorted(a for assets in FIXTURE["layers"].values() for a in assets)


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


def test_committed_file_declares_no_empty_prose_list():
    # [] would claim "no prose"; none is declared: undeclared is null (Null/Narr read NO_DETECTOR)
    assert all(e["prose_fields"] != [] for e in ac.load_asset_declarations().values())


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
    ("carriage-unknown-field", _doc(a=dict(carriage=dict(dag_dependents=True, served=True)))),
    ("carriage-int-not-bool", _doc(a=dict(carriage=dict(dag_dependents=1)))),
    ("carriage-string", _doc(a=dict(carriage=dict(served_surface="yes")))),
    ("prose-not-list", _doc(a=dict(prose_fields="narrative"))),
    ("prose-blank", _doc(a=dict(prose_fields=["narrative", " "]))),
    ("prose-duplicate", _doc(a=dict(prose_fields=["narrative", "narrative"]))),
    ("prose-non-str", _doc(a=dict(prose_fields=[1]))),
    ("evidence-not-object", _doc(a=dict(evidence="x"))),
    ("evidence-unknown-key", _doc(a=dict(evidence=dict(other="x")))),
    ("evidence-non-str", _doc(a=dict(evidence=dict(kind=1)))),
    ("blank-asset-id", _doc(**{" ": dict(kind="data")})),
]


@pytest.mark.parametrize("name,doc", BAD_DOCS, ids=[n for n, _ in BAD_DOCS])
def test_validator_rejects_malformed_documents(name, doc):
    with pytest.raises(ac.DeclarationsError):
        ac.validate_declarations(doc)


def test_validator_accepts_null_fields_and_every_enum_kind():
    doc = _doc(**{f"x{i}": dict(kind=k, carriage=None, prose_fields=None, evidence=None)
                  for i, k in enumerate(list(ac.DECLARED_KINDS) + [None])},
               y=dict(kind=None, carriage=dict(dag_dependents=None, served_surface=False), prose_fields=["a"]))
    assert len(ac.validate_declarations(doc)) == len(ac.DECLARED_KINDS) + 2


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


# ───────────────────────── (4) facts merge ─────────────────────────

DECL = {
    "svc": dict(kind="service", carriage=dict(dag_dependents=False, served_surface=False), prose_fields=None),
    "dat": dict(kind="data", carriage=dict(dag_dependents=True, served_surface=None), prose_fields=["narrative"]),
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


def test_carriage_components_and_the_derived_carries_downstream_fact():
    cases = [
        (dict(dag_dependents=True, served_surface=True), True),
        (dict(dag_dependents=True, served_surface=False), True),
        (dict(dag_dependents=False, served_surface=True), True),
        (dict(dag_dependents=False, served_surface=False), False),
        (dict(dag_dependents=False, served_surface=None), None),    # one unknown component: not derivable
        (dict(dag_dependents=None, served_surface=None), None),
        (dict(dag_dependents=True, served_surface=None), True),
    ]
    for car, want in cases:
        f = ac.declared_facts({"a": dict(carriage=car)}, "a")
        assert f.get("declared_carries_downstream") is want or (want is None and "declared_carries_downstream" not in f), car
    f = ac.declared_facts({"a": dict(carriage=dict(dag_dependents=False, served_surface=None))}, "a")
    assert f["declared_carriage"] == dict(dag_dependents=False)   # the unknown component is left out


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


def test_declared_dependents_contradicting_the_measured_blocking_radius_is_reported():
    decl = {"a": dict(carriage=dict(dag_dependents=False))}
    f = ac.facts_for_asset(dict(asset_id="a", blocking_radius=dict(direct=3)), decl)
    assert f["declaration_disagreements"] == [dict(field="carriage.dag_dependents", declared=False, measured=3)]
    assert "declaration_disagreements" not in ac.facts_for_asset(dict(asset_id="a", blocking_radius=dict(direct=0)), decl)
    assert "declaration_disagreements" not in ac.facts_for_asset(dict(asset_id="a", blocking_radius=dict(direct=None)), decl)
    assert "declaration_disagreements" not in ac.facts_for_asset(dict(asset_id="a"), decl)
    assert "declaration_disagreements" not in ac.facts_for_asset(dict(asset_id="a", blocking_radius=dict(direct=True)), decl)


def test_a_true_dependents_declaration_against_zero_measured_is_reported():
    decl = {"a": dict(carriage=dict(dag_dependents=True))}
    f = ac.facts_for_asset(dict(asset_id="a", blocking_radius=dict(direct=0)), decl)
    assert f["declaration_disagreements"][0]["declared"] is True


# ───────────────────────── (6) declarations are facts only: no verdict moves ─────────────────────────

def test_no_na_rule_is_declared_and_no_criterion_reads_a_declared_key():
    assert ac.NA_RULE_DECISIONS == {}
    facts = dict(asset_kind="service", declared_kind="static", declared_carriage=dict(dag_dependents=False, served_surface=False),
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
