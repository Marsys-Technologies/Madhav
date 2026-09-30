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
import re
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


def _is_sql_read(lines, lineno, token):
    """The cited line carries `token` as a SQL FROM/JOIN target (same line; or the previous non-blank line ends in
    FROM/JOIN and this line starts with the token), or (dynamic table map) quotes the token while the same file
    selects `FROM ${...}`. A comment, a provenance label or an allow-list entry is none of these."""
    line = lines[lineno - 1]
    if re.match(r"\s*(//|\*|/\*|#)", line):
        return False
    if re.search(rf"\b(FROM|JOIN)\s+(public\.)?{re.escape(token)}\b", line):
        return True
    prev = next((x for x in reversed(lines[:lineno - 1]) if x.strip()), "")
    if re.search(r"\b(FROM|JOIN)\s*$", prev) and re.match(rf"\s*(public\.)?{re.escape(token)}\b", line):
        return True
    return bool(re.search(rf"['\"]{re.escape(token)}['\"]", line)) and any("FROM ${" in x for x in lines)


def test_every_served_true_cites_a_real_non_test_read_of_its_table():
    decl = ac.load_asset_declarations()
    trues = [a for a, e in decl.items() if (e["carriage"] or {}).get("served_surface") is True]
    assert trues, "no served_surface true declared"
    for a in trues:
        e = decl[a]
        path, line = e["read_evidence"].rsplit(":", 1)
        f = REPO_ROOT / path
        assert f.is_file(), (a, path)
        assert not re.search(r"(\.test\.|/__tests__/|/tests?/|/generated/|/fixtures/|source_query_availability|mcp/db/query)", path), (a, path)
        lines = f.read_text(encoding="utf-8").splitlines()
        assert 1 <= int(line) <= len(lines), (a, path, line)
        assert _is_sql_read(lines, int(line), e["read_table"]), (a, path, line, e["read_table"], lines[int(line) - 1].strip())


def test_the_read_check_rejects_comments_labels_and_allowlists():
    src = ["// FROM t_x", "  * FROM t_x", "  provenance: { tables: ['t_x'] },", "  't_x',", "const q = `SELECT 1 FROM t_x w`", "  FROM", "    t_x a", "JOIN t_y"]
    assert [_is_sql_read(src, i, "t_x") for i in range(1, 8)] == [False, False, False, False, True, False, True]
    assert _is_sql_read(["const M = { a: 't_x' }", "sql = `SELECT * FROM ${table}`"], 1, "t_x") is True      # dynamic table map
    assert _is_sql_read(["const M = { a: 't_x' }"], 1, "t_x") is False                                          # no FROM ${} in the file
    assert _is_sql_read(["FROM t_xy"], 1, "t_x") is False                                                      # token boundary


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
    ("prose-not-list", _doc(a=dict(prose_fields="narrative"))),
    ("prose-blank", _doc(a=dict(prose_fields=["narrative", " "]))),
    ("prose-duplicate", _doc(a=dict(prose_fields=["narrative", "narrative"]))),
    ("prose-non-str", _doc(a=dict(prose_fields=[1]))),
    ("evidence-not-object", _doc(a=dict(evidence="x"))),
    ("evidence-unknown-key", _doc(a=dict(evidence=dict(other="x")))),
    ("evidence-non-str", _doc(a=dict(evidence=dict(kind=1)))),
    ("blank-asset-id", _doc(**{" ": dict(kind="data")})),
    ("dag-dependents-is-measured-not-declared", _doc(a=dict(carriage=dict(dag_dependents=True)))),
    ("prose-case-variant-duplicate", _doc(a=dict(prose_fields=["Narrative", "narrative"]))),
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
    ("read-evidence-dotdot-middle", _doc(a=dict(carriage=dict(served_surface=True), read_evidence="platform/../../etc/a.ts:12", read_table="t"))),
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
                      cross_asset_writes=None),
               z=dict(carriage=dict(served_surface=False), terminal_by_construction="written only by X; no reader by design",
                      cross_asset_writes=["t.c"], evidence=dict(cross_asset_writes="effect contract writes: [t.c]")),
               w=dict(cross_asset_writes=[], evidence=dict(cross_asset_writes="effect contract writes: []")),
               v=dict(carriage=dict(served_surface=True), read_evidence="platform/src/lib/x/[id]/route-a_b.ts:12", read_table="t_1"),
               u=dict(carriage=dict(served_surface=None), read_evidence=None, read_table=None))
    assert len(ac.validate_declarations(doc)) == len(ac.DECLARED_KINDS) + 6


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
