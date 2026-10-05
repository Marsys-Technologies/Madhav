"""test_e6_c11_carr_harness.py: C1-1 (strategist ruling N-101; design /Users/Dev/suvarna-evidence/L0_WAVE/C1_CARR_DESIGN.md sections 2-3): the Carr harness.

Scope (NO pin, NO REGISTRY_REVISION change, NO verdict move anywhere):
  1. the latta-only D1 matcher is now ONE kernel of a CLOSED registry (`carriage_d1.KERNELS`); an unknown kernel id and an unknown spec field are refused, each kernel states
     its own required / optional fields; the latta's census record is BYTE-IDENTICAL to the one origin/main adb0db29d produces (a committed golden, generated from a `git archive`
     of that commit before any edit);
  2. the `row_scope` guard: rows outside a declared, closed predicate are COUNTED and cap the verdict at PARTIAL naming the count;
  3. the column ledger: every text-like column is matched, a declared constant, a declared non-claim or a prose field, else D1 cannot read PASS. It ALWAYS runs
     (no switch; column types come from pg_catalog, `unknown` types cap the verdict too): the latta has two text columns its spec never checks (table_version, source_citation), so it declares both as
     `non_claim_columns` (declarations 1.13.0) and still reads PASS, its record byte-identical (a clean ledger adds no key); removing either declaration reads PARTIAL;
  4. the D2/D3 mapping: carriage nature `derivation` maps to D3 (D2 is witness carriage), ONE definition, and a derivation carriage is never measured as D2;
  5. zero cell moves: the six saved censuses of adb0db2 re-rolled up (1143 cells), the Carr criteria / N/A rules unchanged, the registry fingerprint equal to the pin of the
     CURRENT revision (nothing here hard-codes a revision number: later pins do not break this file).
Every guard has a mutation test: a mutant that drops it makes the guard's own test fail. Mostly offline; the catalog-type and measure() tests run on the disposable Postgres."""
from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import _decl_version  # noqa: E402
import carriage_d1 as d1  # noqa: E402
import _c11_golden_cases as gc  # noqa: E402
import test_e6_1_p1_registry_rollup as p1  # noqa: E402
import test_e6_a_na_causes as na_causes  # noqa: E402
import test_e6_s3_alias_ldgr as s3  # noqa: E402
import test_e6_decl_latta as dl  # noqa: E402
from _disposable_pg import disposable_pg  # noqa: E402,F401  (the session fixture)

PASS, PARTIAL, NO_DET, NA = ac.PASS, ac.PARTIAL, ac.NO_DET, ac.NA
AID = "bg_phaladeepika_latta"
GOLDEN = HERE / "fixtures" / "c1_1_latta_d1_golden_main_adb0db29d.json"
GOLDEN_SHA256 = "623087fdc749785c449a800d12b6baa8a5e07129c8a9388006bef4e4a88ba231"
SAVED = pathlib.Path("/Users/Dev/suvarna-evidence/census_fresh/adb0db2")
SPEC, CHUNKS, ROWS = gc.inputs()                                             # the COMMITTED latta spec (declarations 1.13.0: it carries its two non_claim_columns)
BARE = {k: v for k, v in SPEC.items() if k != "non_claim_columns"}          # the spec as it was before 1.13.0: the ledger finding is measured on this one
STATE = "sourced_ocr_unverified"
V01 = "phaladeepika_vedha_v01"
# the latta table as pg_catalog reports it ({t: base type, c: typcategory, ec / et: an array's element}); the two text columns the D1 spec never checks are table_version and
# source_citation
def _f(t, c, ec=None, et=None):
    return dict(t=t, c=c, ec=ec, et=et)


TEXT_F, SMALLINT_F, TSTZ_F = _f("text", "S"), _f("int2", "N"), _f("timestamptz", "D")
TYPES = {"table_version": TEXT_F, "graha": TEXT_F, "count_from_graha": SMALLINT_F, "direction": TEXT_F, "effect_description": TEXT_F, "affliction_condition": TEXT_F,
         "source_citation": TEXT_F, "verse_ref": TEXT_F, "created_at": TSTZ_F}
KW = dict(column_types=TYPES, prose_columns=[])
NONCLAIM = copy.deepcopy(SPEC["non_claim_columns"])                           # the two the committed declaration makes, with their why and evidence
assert [x["column"] for x in NONCLAIM] == ["table_version", "source_citation"]
VEDHA = "platform/python-sidecar/brahmagyan/l0_phaladeepika_vedha.py"


def _nc(column="c", why="a real one line reason", evidence=VEDHA + ":72"):
    return {"column": column, "why": why, "evidence": evidence}
SCOPE = [{"column": "table_version", "equals": V01}]


def _spec(**over):
    s = copy.deepcopy(BARE)
    s.update(copy.deepcopy(over))
    return s


def _rows(version=V01, extra=()):
    rs = [dict(r, table_version=version) for r in copy.deepcopy(ROWS)]
    return rs + [copy.deepcopy(x) for x in extra]


def _measure(spec=None, rows=None, chunks=None, state=STATE, table=AID, **kw):
    return d1.d1_measure(spec if spec is not None else SPEC, state, copy.deepcopy(chunks if chunks is not None else CHUNKS),
                         copy.deepcopy(rows if rows is not None else ROWS), table, **kw)


def _refused(spec, match=None):
    try:
        d1.validate_spec(spec, "x")
    except d1.SpecError as exc:
        return match is None or match in str(exc)
    return False


# ───────────────────────── Part 1: the latta record is byte-identical to origin/main's ─────────────────────────

def test_the_golden_file_is_the_one_generated_from_main_and_is_pinned():
    assert hashlib.sha256(GOLDEN.read_bytes()).hexdigest() == GOLDEN_SHA256        # editing the golden is a deliberate, reviewed act
    gold = json.loads(GOLDEN.read_text(encoding="utf-8"))
    assert list(gold) == list(gc.build_cases(d1))                                   # the same cases, in the same order
    assert gold["pass"]["v"] == PASS and sum(1 for c in gold.values() if c["v"] == PARTIAL) == 6 and sum(1 for c in gold.values() if c["v"] == NO_DET) == 8


@pytest.mark.parametrize("case", list(json.loads(GOLDEN.read_text(encoding="utf-8"))))
def test_every_latta_record_is_byte_identical_to_the_main_golden(case):
    gold = json.loads(GOLDEN.read_text(encoding="utf-8"))[case]
    now = gc.build_cases(d1)[case]
    assert json.dumps(now, ensure_ascii=False, indent=1) == json.dumps(gold, ensure_ascii=False, indent=1)     # text equality: keys, key ORDER and values


def test_the_whole_golden_text_is_byte_identical():
    assert json.dumps(gc.build_cases(d1), ensure_ascii=False, indent=1) + "\n" == GOLDEN.read_text(encoding="utf-8")


def test_no_guard_key_appears_on_a_record_that_declares_no_guard():
    rec = _measure()["d1"]
    assert not {"row_scope", "rows_in_table", "out_of_scope_rows", "out_of_scope_sample", "column_ledger"} & set(rec)


@pytest.mark.skipif(not (SAVED / "census_L0.json").exists(), reason="the saved census of adb0db2 is not on this machine (CI)")
def test_the_real_saved_latta_record_has_the_same_keys_in_the_same_order_as_the_engine_now_writes():
    saved = json.loads((SAVED / "census_L0.json").read_text(encoding="utf-8"))["L0"]["assets"]
    rec = next(a for a in saved if a["asset_id"] == AID)["measurements"]["Carr.D1"]
    now = _measure(rows=ROWS)
    assert list(rec) == list(now) and list(rec["d1"]) == list(now["d1"])
    for k in ("matcher", "matching_rule", "span", "chunk_ids", "translation_only", "expected_rows", "reads", "pass_basis", "chunks_sha256", "passage_sha256", "content_sa_all_null"):
        assert rec["d1"][k] == now["d1"][k], k                                       # the saved production record's own values, not only its shape


@pytest.fixture()
def fetch(monkeypatch):
    monkeypatch.setattr(ac, "d1_fetch_chunks", lambda ids: {i: copy.deepcopy(CHUNKS[i]) for i in ids if i in CHUNKS})
    monkeypatch.setattr(ac, "d1_fetch_rows", lambda table, cols, chart=None: copy.deepcopy(ROWS))


def test_the_census_path_for_the_committed_latta_declaration_writes_the_golden_record(fetch):
    car = json.loads(ac.DECLARATIONS_PATH.read_text(encoding="utf-8"))["assets"][AID]["carriage"]
    got = ac.carriage_declared_checks(AID, car, AID, **KW)
    gold = json.loads(GOLDEN.read_text(encoding="utf-8"))["pass"]
    assert json.dumps(got["Carr.D1"], ensure_ascii=False, indent=1) == json.dumps(gold, ensure_ascii=False, indent=1)
    assert ac.d1_evidence_problem(got["Carr.D1"]) == "" and ac.rollup_asset("L0", got)["Carr"]["v"] == PASS


# ───────────────────────── Part 2: the kernel registry is closed ─────────────────────────

def test_the_registry_holds_exactly_the_latta_kernel_with_its_exact_current_required_fields():
    # C1-2 added the second kernel (paired_enumeration_v1, pinned in test_c1_2_paired_enumeration.py): the closed set is exactly these two, the latta's first and unchanged
    assert list(d1.KERNELS) == [d1.MATCHER, d1.PAIRED] == ["ordinal_count_direction_effect_v2", "paired_enumeration_v1"] and set(d1.KERNELS) == set(d1.MATCHERS)
    k = d1.KERNELS[d1.MATCHER]
    assert set(k) == set(d1.KERNEL_HOOKS) == {"spec_required", "spec_optional", "result_keys", "columns", "key_column", "matched_columns", "coverage", "validate", "span_check",
                                              "evidence_pointers", "rule_text"}
    assert d1.HARNESS_REQUIRED + k["spec_required"] and set(d1.HARNESS_REQUIRED) | set(k["spec_required"]) == {
        "matcher", "table", "chunk_ids", "span", "fields", "direction_words", "anchor_stems", "expected_rows", "effect_marker", "effect_end", "effect_frame_words",
        "effect_clauses", "effect_clauses_evidence"}                                  # the exact set validate_spec demanded before C1-1
    assert set(k["spec_optional"]) | set(d1.HARNESS_OPTIONAL) == {"extra_fields", "row_scope", "non_claim_columns"}
    assert k["rule_text"] == d1.MATCHING_RULE_TEXT[d1.MATCHER] and d1.MATCHER_FIELDS[d1.MATCHER] == ("claimant", "count", "direction", "effect") and k["key_column"](SPEC) == "graha"
    assert d1.validate_spec(copy.deepcopy(SPEC), "x") == SPEC                          # the committed latta spec validates by the same path


def _unknown_kernel_is_refused():
    return all(_refused(_spec(matcher=m), "known rule engine") for m in ("nope", "", "ordinal_count_direction_effect_v3", None, 3, ["ordinal_count_direction_effect_v2"], {"a": 1}))


def test_an_unknown_kernel_id_is_refused_by_the_validator_and_by_the_measure():
    assert _unknown_kernel_is_refused()
    assert _refused({k: v for k, v in SPEC.items() if k != "matcher"}, "missing field")
    with pytest.raises(d1.SpecError, match="closed registry"):
        d1.d1_measure(_spec(matcher="nope"), STATE, CHUNKS, ROWS, AID)
    with pytest.raises(d1.SpecError, match="closed registry"):
        d1.d1_measure({k: v for k, v in SPEC.items() if k != "matcher"}, STATE, CHUNKS, ROWS, AID)


def _unknown_and_missing_fields_are_refused():
    ok = _refused(_spec(extra=1), "unknown field(s) ['extra']") and _refused(_spec(matcher="nope", extra=1), "unknown field")
    for f in sorted(set(d1.HARNESS_REQUIRED) | set(d1.KERNELS[d1.MATCHER]["spec_required"])):
        ok = ok and _refused({k: v for k, v in SPEC.items() if k != f}, "missing field(s)")
    return ok


def test_unknown_and_missing_spec_fields_are_refused_for_the_latta_kernel():
    assert _unknown_and_missing_fields_are_refused()


def test_each_kernel_states_its_own_field_set(monkeypatch):
    """A second kernel with a DIFFERENT field set: the latta's fields are unknown to it, its own are required; the harness fields (and guards) are common."""
    fake = dict(d1.KERNELS[d1.MATCHER], spec_required=("foo",), spec_optional=("bar",), validate=lambda spec, where: None, matched_columns=lambda spec: [])
    monkeypatch.setitem(d1.KERNELS, "fake_kernel_v1", fake)
    base = dict(matcher="fake_kernel_v1", table="t", chunk_ids=["c1"], span=dict(start="s"), expected_rows=1, foo=1)
    assert d1.validate_spec(dict(base), "x") == base
    assert d1.validate_spec(dict(base, bar=2, row_scope=SCOPE, non_claim_columns=NONCLAIM[1:]), "x")      # its optional field and both harness guards
    assert _refused(dict(base, effect_clauses={}), "unknown field(s) ['effect_clauses']")              # a latta field is unknown to another kernel
    assert _refused({k: v for k, v in base.items() if k != "foo"}, "missing field(s) ['foo']")
    assert _refused(dict(base, baz=1), "unknown field(s) ['baz']")
    assert d1.KERNELS[d1.MATCHER]["spec_optional"] != fake["spec_optional"] and _refused(dict(SPEC, foo=1), "unknown field")


def test_the_declarations_file_is_at_or_past_the_version_that_carries_the_non_claims():
    parts = tuple(int(p) for p in _decl_version.CURRENT.split("."))
    assert len(parts) == 3 and parts >= (1, 13, 0)                                     # a floor, not a literal: later minors keep this test green


def test_the_kernel_id_and_rule_text_are_unchanged_so_the_declaration_and_the_record_are_untouched():
    car = json.loads(ac.DECLARATIONS_PATH.read_text(encoding="utf-8"))["assets"][AID]["carriage"]
    assert car["spec"]["matcher"] == d1.MATCHER and json.loads(ac.DECLARATIONS_PATH.read_text(encoding="utf-8"))["version"] == _decl_version.CURRENT
    assert _measure()["d1"]["matching_rule"] == d1.MATCHING_RULE_TEXT[d1.MATCHER]


# ───────────────────────── Part 3: row_scope ─────────────────────────

@pytest.mark.parametrize("scope", [
    [{"column": "table_version", "equals": V01}], [{"column": "table_version", "in": [V01, "other"]}], [{"column": "effect_description", "not_null": True}],
    [{"column": "table_version", "equals": V01}, {"column": "count_from_graha", "in": [1, 2, 3]}, {"column": "effect_description", "not_null": True}],
    [{"column": "count_from_graha", "equals": 5}]])
def test_valid_row_scopes_are_accepted(scope):
    assert d1.validate_spec(_spec(row_scope=scope), "x")["row_scope"] == scope


@pytest.mark.parametrize("scope, match", [
    ("table_version = 'x'", "list of 1..4"), ([], "list of 1..4"), ({"column": "a", "equals": "x"}, "list of 1..4"),
    ([{"column": "a", "equals": "x"}] * 5, "list of 1..4"),
    (["a"], "objects with a `column`"), ([{"equals": "x"}], "objects with a `column`"), ([{"column": "a b", "equals": "x"}], "objects with a `column`"),
    ([{"column": "a"}], "exactly one of"), ([{"column": "a", "equals": "x", "in": ["y"]}], "exactly one of"), ([{"column": "a", "like": "x%"}], "exactly one of"),
    ([{"column": "a", "equals": "x", "sql": "1=1"}], "exactly one of"), ([{"column": "a", "regex": ".*"}], "exactly one of"),
    ([{"column": "a", "equals": True}], "equals must be"), ([{"column": "a", "equals": ""}], "equals must be"), ([{"column": "a", "equals": 1.5}], "equals must be"),
    ([{"column": "a", "equals": ["x"]}], "equals must be"), ([{"column": "a", "equals": None}], "equals must be"),
    ([{"column": "a", "in": []}], "in must be"), ([{"column": "a", "in": "xy"}], "in must be"), ([{"column": "a", "in": ["x", "x"]}], "in must be"),
    ([{"column": "a", "in": [str(i) for i in range(17)]}], "in must be"), ([{"column": "a", "in": [True]}], "in must be"),
    ([{"column": "a", "not_null": False}], "not_null must be true"), ([{"column": "a", "not_null": 1}], "not_null must be true"),
    ([{"column": "a", "equals": "x"}, {"column": "a", "equals": "y"}], "two conditions")])
def test_a_row_scope_is_a_closed_predicate_everything_else_is_refused(scope, match):
    assert _refused(_spec(row_scope=scope), match)


def test_the_scope_columns_are_read_with_the_row_and_a_spec_without_a_scope_reads_the_same_columns_as_before():
    assert d1.spec_columns(SPEC) == ["graha", "count_from_graha", "direction", "effect_description", "affliction_condition", "verse_ref"]
    assert d1.spec_columns(_spec(row_scope=SCOPE)) == d1.spec_columns(SPEC) + ["table_version"]
    assert d1.spec_columns(_spec(row_scope=[{"column": "graha", "in": ["Sun"]}])) == d1.spec_columns(SPEC)       # an already-read column is not read twice


def test_scope_evaluation_equals_in_not_null_and_the_traps():
    f = d1.row_in_scope
    assert f({"a": "x"}, [{"column": "a", "equals": "x"}]) and not f({"a": "y"}, [{"column": "a", "equals": "x"}])
    assert not f({"a": "x "}, [{"column": "a", "equals": "x"}]) and not f({"a": "X"}, [{"column": "a", "equals": "x"}])               # exact, never trimmed or folded
    assert f({"a": "y"}, [{"column": "a", "in": ["x", "y"]}]) and not f({"a": "z"}, [{"column": "a", "in": ["x", "y"]}])
    assert f({"a": 1}, [{"column": "a", "equals": 1}]) and not f({"a": True}, [{"column": "a", "equals": 1}]) and not f({"a": "1"}, [{"column": "a", "equals": 1}])
    assert f({"a": 0}, [{"column": "a", "not_null": True}]) and f({"a": ""}, [{"column": "a", "not_null": True}]) and not f({"a": None}, [{"column": "a", "not_null": True}])
    assert not f({}, [{"column": "a", "not_null": True}]) and not f({}, [{"column": "a", "equals": "x"}]) and not f("not a row", [{"column": "a", "not_null": True}])
    both = [{"column": "a", "equals": "x"}, {"column": "b", "not_null": True}]
    assert f({"a": "x", "b": 1}, both) and not f({"a": "x", "b": None}, both) and not f({"a": "z", "b": 1}, both)                       # ANDed


def test_partition_with_no_scope_puts_every_row_in_scope():
    ins, outs = d1.partition_rows([{"a": 1}, "junk", None], None)
    assert [i for i, _ in ins] == [0, 1, 2] and outs == []


NOISE = dict(graha="Sun", count_from_graha=1, direction="forward", effect_description="not a latta effect at all", affliction_condition="x", verse_ref="y",
             table_version="some_other_seed_v02")


def _scoped_partial_with_one_outside_row():
    rec = _measure(spec=_spec(row_scope=SCOPE), rows=_rows(extra=[NOISE]))
    ev = rec["d1"]
    return (rec["v"] == PARTIAL and ev["out_of_scope_rows"] == 1 and ev["rows_total"] == 8 and ev["rows_matched"] == 8 and ev["unmatched"] == []
            and ev["rows_in_table"] == 9 and ev["row_scope"] == SCOPE and ev["out_of_scope_sample"] == ["Sun"]
            and "1 row(s) lie outside the declared row_scope" in rec["measured"] and ev["row_count_ok"] is True)


def test_rows_outside_the_scope_are_counted_and_cap_the_verdict_at_partial_naming_the_count():
    assert _scoped_partial_with_one_outside_row()
    rec = _measure(spec=_spec(row_scope=SCOPE), rows=_rows(extra=[NOISE, dict(NOISE, graha="Moon"), dict(NOISE, graha="Rahu")]))
    assert rec["v"] == PARTIAL and rec["d1"]["out_of_scope_rows"] == 3 and "3 row(s) lie outside" in rec["measured"] and rec["d1"]["out_of_scope_sample"] == ["Sun", "Moon", "Rahu"]
    assert d1.scope_cap_problem(0) is None and "2 row(s)" in d1.scope_cap_problem(2)


def test_with_every_row_in_scope_a_declared_scope_changes_nothing_but_adds_its_own_keys():
    rec = _measure(spec=_spec(row_scope=SCOPE), rows=_rows())
    ev = rec["d1"]
    assert rec["v"] == PASS and ev["out_of_scope_rows"] == 0 and ev["rows_total"] == ev["rows_in_table"] == 8 and ev["out_of_scope_sample"] == [] and ev["row_scope"] == SCOPE
    plain = _measure(rows=_rows())
    assert plain["measured"] == rec["measured"] and {k: v for k, v in ev.items() if k not in ("row_scope", "rows_in_table", "out_of_scope_rows", "out_of_scope_sample")} == plain["d1"]


def test_out_of_scope_rows_do_not_count_for_duplicates_or_the_expected_row_count():
    """A shared table: another seed may hold the same claimant, and extra rows must not turn a complete in-scope set into a count miss."""
    rec = _measure(spec=_spec(row_scope=SCOPE), rows=_rows(extra=[NOISE]))
    assert rec["d1"]["unmatched"] == [] and rec["d1"]["row_count_ok"] is True and all("duplicate" not in r["failed"] for r in rec["d1"]["unmatched"])
    short = _measure(spec=_spec(row_scope=SCOPE), rows=_rows()[:-1] + [dict(NOISE, graha="Rahu")])
    assert short["v"] == PARTIAL and short["d1"]["row_count_ok"] is False and short["d1"]["out_of_scope_rows"] == 1 and "7 row(s) but 8 are declared" in short["measured"]


def test_no_row_in_scope_is_no_detector_not_pass():
    rec = _measure(spec=_spec(row_scope=SCOPE), rows=_rows(version="another_seed"))
    assert rec["v"] == NO_DET and "none of the 8 row(s)" in rec["measured"] and rec["d1"]["out_of_scope_rows"] == 8


def test_a_citation_capped_state_stays_no_detector_with_a_scope():
    assert _measure(spec=_spec(row_scope=SCOPE), rows=_rows(extra=[NOISE]), state="unsourced")["v"] == NO_DET


def test_the_evidence_check_refuses_a_pass_that_hides_an_out_of_scope_row():
    good = _measure(spec=_spec(row_scope=SCOPE), rows=_rows())
    assert ac.d1_evidence_problem(good) == ""
    forged = copy.deepcopy(good)
    forged["d1"]["out_of_scope_rows"] = 2
    assert "outside the declared row_scope" in ac.d1_evidence_problem(forged)
    no_count = copy.deepcopy(good)
    del no_count["d1"]["out_of_scope_rows"]
    assert "row_scope" in ac.d1_evidence_problem(no_count)
    boolean = copy.deepcopy(good)
    boolean["d1"]["out_of_scope_rows"] = False
    assert "row_scope" in ac.d1_evidence_problem(boolean)
    partial = _measure(spec=_spec(row_scope=SCOPE), rows=_rows(extra=[NOISE]))
    assert ac.d1_evidence_problem(partial) == ""                                      # a PARTIAL that says so is honoured
    na = {c: ac._na("the declared check is D1", "not-the-declared-carriage") for c in ("Carr.D2", "Carr.D3")}
    assert ac.rollup_asset("L0", {"Carr.D1": partial, **na})["Carr"]["v"] == PARTIAL
    assert ac.rollup_asset("L0", {"Carr.D1": good, **na})["Carr"]["v"] == PASS


def test_through_the_census_a_scoped_latta_with_an_outside_row_reads_partial(monkeypatch):
    monkeypatch.setattr(ac, "d1_fetch_chunks", lambda ids: copy.deepcopy(CHUNKS))
    monkeypatch.setattr(ac, "d1_fetch_rows", lambda t, c, chart=None: _rows(extra=[NOISE]))
    assert "table_version" in d1.spec_columns(_spec(row_scope=SCOPE))
    car = dict(applies="D1", nature="transcription", why="w", evidence="x", citation_state=STATE, spec=_spec(row_scope=SCOPE, non_claim_columns=NONCLAIM))
    got = ac.carriage_declared_checks(AID, car, AID, **KW)
    assert got["Carr.D1"]["v"] == PARTIAL and got["Carr.D1"]["d1"]["out_of_scope_rows"] == 1 and "column_ledger" not in got["Carr.D1"]["d1"]
    assert ac.rollup_asset("L0", got)["Carr"]["v"] == PARTIAL




# ───────────────────────── Part 4: the column ledger (pure) ─────────────────────────

CITEXT_F = _f("citext", "S")
FACT_CLASSES = {
    # text-like: the string and enum categories (domains arrive resolved to their base), json / xml / tsvector / "char", and arrays OF those
    "text": [TEXT_F, _f("varchar", "S"), _f("bpchar", "S"), _f("name", "S"), CITEXT_F, _f("mood", "E"), _f("jsonb", "U"), _f("json", "U"), _f("xml", "U"), _f("tsvector", "U"),
             _f("tsquery", "U"), _f("char", "Z"), _f("_text", "A", "S", "text"), _f("_varchar", "A", "S", "varchar"), _f("_citext", "A", "S", "citext"), _f("_mood", "A", "E", "mood"),
             _f("_jsonb", "A", "U", "jsonb")],
    # non-text: numbers, booleans, date / time, network, geometry, bit strings, uuid, bytea, embeddings, and arrays OF those (`integer[]` is not text)
    "nontext": [SMALLINT_F, _f("int4", "N"), _f("numeric", "N"), _f("float8", "N"), _f("bool", "B"), _f("date", "D"), TSTZ_F, _f("timestamp", "D"), _f("interval", "T"), _f("inet", "I"),
                _f("point", "G"), _f("bit", "V"), _f("uuid", "U"), _f("bytea", "U"), _f("vector", "U"), _f("_int4", "A", "N", "int4"), _f("_bool", "A", "B", "bool"),
                _f("_uuid", "A", "U", "uuid"), _f("_numeric", "A", "N", "numeric")],
    # unknown: a composite, a range, an extension type the ledger has no rule for, an array of one, a malformed fact: never silently ignored
    "unknown": [_f("pair", "C"), _f("int4range", "R"), _f("hstore", "U"), _f("ltree", "U"), _f("_pair", "A", "C", "pair"), _f("_text", "A", "S", None), None, "text", [], {}, dict(t="x")]}


@pytest.mark.parametrize("cls", list(FACT_CLASSES))
def test_column_types_are_classified_from_pg_catalog_facts(cls):
    for fact in FACT_CLASSES[cls]:
        assert d1.column_type_class(fact) == cls, fact


def _ledger(spec=None, types=None, prose=()):
    return d1.column_ledger(spec if spec is not None else BARE, types if types is not None else TYPES, prose)


def test_the_latta_table_has_two_text_columns_its_d1_spec_never_checks():
    """THE FINDING (design doc section 2 said the latta already satisfies the ledger; it does not): table_version and source_citation."""
    led = _ledger(BARE)
    assert led["text_columns"] == ["affliction_condition", "direction", "effect_description", "graha", "source_citation", "table_version", "verse_ref"]
    assert led["matched"] == ["affliction_condition", "direction", "effect_description", "graha"] and led["constants"] == ["verse_ref"]
    assert led["non_claims"] == [] and led["prose"] == [] and led["declared_absent"] == [] and led["unexamined"] == []
    assert led["uncovered"] == ["source_citation", "table_version"] and led["evaluated"] is True
    assert "count_from_graha" not in led["text_columns"] and "created_at" not in led["text_columns"]                 # smallint / timestamptz are not text-like
    assert sorted(d1.prose_coverage(SPEC)) == ["affliction_condition", "effect_description"]                         # unchanged: the Narr coupling's covered set
    committed = _ledger(SPEC)
    assert committed["uncovered"] == [] and committed["unexamined"] == [] and d1.ledger_block_is_clean(committed)
    assert committed["non_claims"] == [dict(column=x["column"], why=x["why"]) for x in sorted(NONCLAIM, key=lambda x: x["column"])]


def test_prose_declared_non_claim_or_equals_constant_classify_a_column_but_a_scope_pin_does_not():
    assert _ledger(_spec(non_claim_columns=NONCLAIM))["uncovered"] == []
    assert _ledger(_spec(non_claim_columns=NONCLAIM[1:]), prose=["table_version"])["uncovered"] == []                                       # a Narr prose field
    assert _ledger(_spec(non_claim_columns=NONCLAIM[1:], row_scope=[{"column": "table_version", "not_null": True}]))["uncovered"] == ["table_version"]
    # MEDIUM 3: a row_scope equals / in pin selects rows, it carries no why and no evidence, and its values are never compared to the passage: NO ledger credit
    for pin in ({"column": "table_version", "equals": V01}, {"column": "table_version", "in": [V01, "x"]}):
        led = _ledger(_spec(non_claim_columns=NONCLAIM[1:], row_scope=[pin]))
        assert led["uncovered"] == ["table_version"] and led["constants"] == ["verse_ref"]


def _editorial_pin_does_not_launder_a_text_column():
    """The reviewer's repro: the latta spec plus a scope pinning an extra text column to a value never compared to the passage."""
    types = dict(TYPES, editorial_claim=TEXT_F)
    spec = dict(SPEC, row_scope=[{"column": "editorial_claim", "in": ["Unmatched editorial prophecy"]}])
    d1.validate_spec(spec, "x")
    rec = _measure(spec=spec, rows=[dict(r, editorial_claim="Unmatched editorial prophecy") for r in _rows()], ledger=dict(columns=types, prose_columns=[]))
    return rec["v"] == PARTIAL and rec["d1"]["column_ledger"]["uncovered"] == ["editorial_claim"] and "editorial_claim" in rec["measured"]


def test_a_scope_pin_on_an_extra_text_column_reads_partial_not_pass():
    assert _editorial_pin_does_not_launder_a_text_column()


def test_a_non_claim_may_cover_a_scope_pinned_column_it_is_a_separate_declaration_with_its_own_why():
    spec = _spec(row_scope=SCOPE, non_claim_columns=NONCLAIM)
    assert d1.validate_spec(spec, "x") and _ledger(spec)["uncovered"] == []


def _ledger_blocks_pass():
    rec = _measure(spec=BARE, rows=_rows(), ledger=dict(columns=TYPES, prose_columns=[]))
    ev = rec["d1"]
    return (rec["v"] == PARTIAL and ev["column_ledger"]["uncovered"] == ["source_citation", "table_version"] and ev["unmatched"] == [] and ev["row_count_ok"] is True
            and "column ledger: text column(s) source_citation, table_version are neither matched" in rec["measured"])


def test_an_unclassified_text_column_means_no_pass():
    assert _ledger_blocks_pass()
    assert d1.ledger_cap_problem(None) is None and d1.ledger_cap_problem(dict(uncovered=[], declared_absent=[], unexamined=[])) is None


def test_with_every_text_column_classified_the_ledger_passes_and_a_clean_ledger_adds_no_key():
    rec = _measure(spec=SPEC, rows=_rows(), ledger=dict(columns=TYPES, prose_columns=[]))
    assert rec["v"] == PASS and "column_ledger" not in rec["d1"]
    assert json.dumps(rec, sort_keys=False) == json.dumps(_measure(spec=SPEC, rows=_rows()), sort_keys=False)          # byte-identical to the record with no ledger requested
    assert ac.d1_evidence_problem(rec) == ""


def _unexamined_types_cap_the_verdict():
    """HIGH 1: a column of a type the ledger has no rule for is not silently ignored: PARTIAL naming it, recorded in the block."""
    types = dict(TYPES, odd=_f("pair", "C"))
    rec = _measure(spec=SPEC, rows=_rows(), ledger=dict(columns=types, prose_columns=[]))
    blk = rec["d1"].get("column_ledger", {})
    return (rec["v"] == PARTIAL and blk.get("unexamined") == ["odd"] and blk.get("uncovered") == [] and "odd" in rec["measured"] and "cannot class" in rec["measured"]
            and ac.d1_evidence_problem(dict(rec, v=PASS)) != "")


def test_an_unexaminable_column_type_caps_the_verdict_and_is_recorded_in_the_block():
    assert _unexamined_types_cap_the_verdict()
    types = dict(TYPES, odd=_f("pair", "C"))
    assert _ledger(SPEC, types)["unexamined"] == ["odd"] and not d1.ledger_block_is_clean(_ledger(SPEC, types))
    assert _ledger(_spec(non_claim_columns=NONCLAIM + [_nc("odd", "odd is the composite pair column of the table")]), types)["unexamined"] == []     # classified otherwise: covered
    assert _ledger(SPEC, types, prose=["odd"])["unexamined"] == []
    for bad in ("text", None, {}):                                                         # a malformed fact is unknown, never "no columns" and never text-free
        assert _ledger(SPEC, dict(TYPES, odd=bad))["unexamined"] == ["odd"]


def test_a_declared_column_the_table_does_not_have_blocks_pass_the_declaration_and_the_table_disagree():
    spec = _spec(non_claim_columns=NONCLAIM + [_nc("no_such_column", "no_such_column is a stale declaration naming a column that was dropped")])
    rec = _measure(spec=spec, rows=_rows(), ledger=dict(columns=TYPES))
    assert rec["v"] == PARTIAL and rec["d1"]["column_ledger"]["declared_absent"] == ["no_such_column"] and "does not have" in rec["measured"]
    assert [x["column"] for x in rec["d1"]["column_ledger"]["non_claims"]] == ["source_citation", "table_version"]                  # listed under declared_absent only


def test_an_unreadable_column_catalog_is_no_detector_never_pass_and_a_capped_citation_wins():
    for cols in (None, {}):
        rec = _measure(spec=SPEC, rows=_rows(), ledger=dict(columns=cols))
        assert rec["v"] == NO_DET and "column types could not be read" in rec["measured"] and "column_ledger" not in rec["d1"]
    refuted = _measure(spec=BARE, rows=_rows(), ledger=dict(columns=TYPES), state="refuted")
    assert refuted["v"] == NO_DET and "citation_state" in refuted["measured"] and refuted["d1"]["column_ledger"]["uncovered"]


@pytest.mark.parametrize("nc, match", [
    ("table_version", "list of 1..16"), ([], "list of 1..16"), ([_nc()] * 17, "list of 1..16"),
    (["c"], "{column, why, evidence}"), ([{"column": "c"}], "{column, why, evidence}"), ([{"column": "c", "why": "a real one line reason"}], "{column, why, evidence}"),
    ([{"column": "c", "reason": "a real one line reason", "evidence": "x.py:1"}], "{column, why, evidence}"),
    ([dict(_nc(), extra=1)], "{column, why, evidence}"), ([_nc("c c")], "{column, why, evidence}"),
    ([_nc(why="n/a")], "real one-line reason"), ([_nc(why="two words only")], "real one-line reason"), ([_nc(why="a real reason\nsecond line here")], "real one-line reason"),
    ([_nc(why=None)], "real one-line reason"), ([_nc(why="x " * 201)], "real one-line reason"),
    ([_nc(evidence="")], "evidence must be"), ([_nc(evidence=None)], "evidence must be"), ([_nc(evidence="a.py:1\nb.py:2")], "evidence must be"),
    ([_nc(), _nc()], "twice"),
    ([_nc("graha")], "classified once"), ([_nc("verse_ref")], "classified once"), ([_nc("affliction_condition")], "classified once")])
def test_non_claim_columns_need_a_why_and_evidence_and_may_not_reclassify_a_matched_or_constant_column(nc, match):
    assert _refused(_spec(non_claim_columns=nc), match)


def _doc_with(nc):
    d = json.loads(ac.DECLARATIONS_PATH.read_text(encoding="utf-8"))
    d["assets"][AID]["carriage"]["spec"]["non_claim_columns"] = nc
    return d


GENERIC_WHY = "this is only a label for the row, honest and harmless to the passage"


def test_the_declaration_validator_applies_the_s3_rules_and_makes_a_non_claim_name_its_column():
    assert ac.validate_declarations(_doc_with(copy.deepcopy(NONCLAIM)))
    for nc, match in [([_nc("table_version", "TBD placeholder text for later"), NONCLAIM[1]], "placeholder word"),
                      ([_nc("table_version", "short one"), NONCLAIM[1]], "real one-line reason"),
                      ([dict(NONCLAIM[0], evidence="unverified:recorded somewhere else"), NONCLAIM[1]], "may not be `unverified:`"),
                      ([dict(NONCLAIM[0], evidence="platform/does/not/exist.py:1"), NONCLAIM[1]], "not an existing repo-relative file"),
                      ([dict(NONCLAIM[0], evidence=VEDHA + ":99999"), NONCLAIM[1]], "names line 99999"),
                      ([dict(NONCLAIM[0], evidence="../outside.py:1"), NONCLAIM[1]], "not an existing repo-relative file")]:
        with pytest.raises(ac.DeclarationsError, match=match):
            ac.validate_declarations(_doc_with(nc))
    # MEDIUM 4: a generic why with an UNRELATED evidence line does not declare a column a label: the why or the evidence line must name the column (whole token, any case)
    unrelated = dict(column="table_version", why=GENERIC_WHY, evidence=VEDHA + ":1")
    with pytest.raises(ac.DeclarationsError, match="names the column 'table_version'"):
        ac.validate_declarations(_doc_with([unrelated, NONCLAIM[1]]))
    with pytest.raises(ac.DeclarationsError, match="names the column"):                                      # naming a DIFFERENT column is not naming this one
        ac.validate_declarations(_doc_with([dict(unrelated, why="source_citation is only a label for the row, honest and harmless"), NONCLAIM[1]]))
    with pytest.raises(ac.DeclarationsError, match="names the column"):                                      # a whole token: a longer identifier does not count
        ac.validate_declarations(_doc_with([dict(unrelated, why="old_table_version_v2 is only a label for the row, honest"), NONCLAIM[1]]))
    assert ac.validate_declarations(_doc_with([dict(unrelated, evidence=VEDHA + ":72"), NONCLAIM[1]]))        # the evidence line (TABLE_VERSION = ...) names it, any case
    assert ac.validate_declarations(_doc_with([dict(unrelated, why="TABLE_VERSION is only a label for the row, honest and harmless"), NONCLAIM[1]]))


def test_the_committed_latta_non_claims_are_real_declarations():
    car = LATTA_CAR
    assert [x["column"] for x in car["spec"]["non_claim_columns"]] == ["table_version", "source_citation"]
    for x in car["spec"]["non_claim_columns"]:
        assert ac._s3_text_problem(x["why"], min_chars=15, min_words=3) is None and ac._s3_evidence_problem(x["evidence"], allow_unverified=False) is None
        assert ac._non_claim_names_column_problem(x) is None and x["evidence"].startswith(VEDHA + ":")
    tv, sc = (x["evidence"] for x in car["spec"]["non_claim_columns"])
    lines = (ac.ROOT / VEDHA).read_text(encoding="utf-8").splitlines()
    assert lines[int(tv.rsplit(":", 1)[1]) - 1].startswith("TABLE_VERSION = ") and lines[int(sc.rsplit(":", 1)[1]) - 1].startswith("_CITATION_PG339")
    assert "table_version" in [c["column"] for c in json.loads(ac.DECLARATIONS_PATH.read_text(encoding="utf-8"))["assets"][AID]["null_convention"]["constants"]]
    assert json.loads(ac.DECLARATIONS_PATH.read_text(encoding="utf-8"))["assets"][AID]["ldgr_source"]["source_column"] == "verse_ref"          # what source_citation's why says it is NOT


def test_the_evidence_check_refuses_a_pass_with_an_unclassified_column_in_its_ledger():
    good = _measure(spec=SPEC, rows=_rows(), ledger=dict(columns=TYPES))
    assert good["v"] == PASS and ac.d1_evidence_problem(good) == ""
    for blk in (dict(evaluated=True, uncovered=["source_citation"], declared_absent=[], unexamined=[]), dict(evaluated=True, uncovered=[], declared_absent=["x"], unexamined=[]),
                dict(evaluated=True, uncovered=[], declared_absent=[], unexamined=["odd"])):
        forged = copy.deepcopy(good)
        forged["d1"]["column_ledger"] = blk
        assert "column ledger" in ac.d1_evidence_problem(forged), blk
    clean = dict(evaluated=True, uncovered=[], declared_absent=[], unexamined=[])
    assert ac.d1_evidence_problem(dict(good, d1=dict(good["d1"], column_ledger=clean))) == ""                                  # a clean block is fine
    for junk in (None, [], "ok", {"uncovered": []}, {"evaluated": False, "uncovered": [], "declared_absent": [], "unexamined": []}, dict(clean, unexamined=None)):
        bad = copy.deepcopy(good)
        bad["d1"]["column_ledger"] = junk
        assert "column ledger" in ac.d1_evidence_problem(bad), junk
    partial = _measure(spec=BARE, rows=_rows(), ledger=dict(columns=TYPES))
    assert partial["v"] == PARTIAL and ac.d1_evidence_problem(partial) == ""                                           # a PARTIAL naming the columns is honoured


# ───────────────────────── Part 5: the census wiring (the ledger always runs) ─────────────────────────

LATTA_CAR = json.loads(ac.DECLARATIONS_PATH.read_text(encoding="utf-8"))["assets"][AID]["carriage"]


def _latta_d1(car=None, types=TYPES, prose=()):
    return ac.carriage_declared_checks(AID, car if car is not None else LATTA_CAR, AID, column_types=types, prose_columns=list(prose))


def _without(*cols):
    car = copy.deepcopy(LATTA_CAR)
    kept = [x for x in car["spec"]["non_claim_columns"] if x["column"] not in cols]
    if kept:
        car["spec"]["non_claim_columns"] = kept
    else:
        del car["spec"]["non_claim_columns"]
    return car


def test_the_column_types_and_prose_columns_are_required_arguments_there_is_no_off_switch():
    assert not hasattr(ac, "CARR_COLUMN_LEDGER_ENFORCED") and not hasattr(ac, "_LEDGER_NOT_SUPPLIED")
    with pytest.raises(TypeError):
        ac.carriage_declared_checks(AID, LATTA_CAR, AID)
    with pytest.raises(TypeError):
        ac.carriage_declared_checks(AID, LATTA_CAR, AID, prose_columns=[])
    with pytest.raises(TypeError):
        ac.carriage_declared_checks(AID, LATTA_CAR, AID, column_types=TYPES)


def test_the_latta_reads_pass_and_its_record_is_byte_identical_to_the_main_golden(fetch):
    got = _latta_d1()
    gold = json.loads(GOLDEN.read_text(encoding="utf-8"))["pass"]
    assert got["Carr.D1"]["v"] == PASS and "column_ledger" not in got["Carr.D1"]["d1"]
    assert json.dumps(got["Carr.D1"], ensure_ascii=False, indent=1) == json.dumps(gold, ensure_ascii=False, indent=1)
    assert ac.rollup_asset("L0", got)["Carr"]["v"] == PASS and ac.d1_evidence_problem(got["Carr.D1"]) == ""


@pytest.mark.parametrize("dropped, named", [(("table_version",), ["table_version"]), (("source_citation",), ["source_citation"]),
                                            (("table_version", "source_citation"), ["source_citation", "table_version"])])
def test_removing_either_non_claim_declaration_reads_partial_naming_the_column(fetch, dropped, named):
    got = _latta_d1(_without(*dropped))["Carr.D1"]
    assert got["v"] == PARTIAL and got["d1"]["column_ledger"]["uncovered"] == named and got["d1"]["unmatched"] == []
    assert f"text column(s) {', '.join(named)} are neither matched" in got["measured"]
    assert ac.rollup_asset("L0", _latta_d1(_without(*dropped)))["Carr"]["v"] == PARTIAL


def test_an_unreadable_catalog_reads_no_detector_through_the_census_never_pass(fetch):
    assert _latta_d1(types=None)["Carr.D1"]["v"] == NO_DET and "column types could not be read" in _latta_d1(types=None)["Carr.D1"]["measured"]
    assert _latta_d1(types={})["Carr.D1"]["v"] == NO_DET


def _prose_columns_classify():
    """M25: the asset's declared Narr prose columns reach the ledger: the same bare spec reads PASS when source_citation / table_version are declared prose, PARTIAL when not."""
    car = _without("table_version", "source_citation")
    with_prose = _latta_d1(car, prose=["table_version", "source_citation"])["Carr.D1"]
    without = _latta_d1(car, prose=[])["Carr.D1"]
    return with_prose["v"] == PASS and without["v"] == PARTIAL and without["d1"]["column_ledger"]["uncovered"] == ["source_citation", "table_version"]


def test_the_prose_columns_the_asset_declares_classify_a_text_column(fetch):
    assert _prose_columns_classify()


def test_the_ledger_inputs_measure_hands_to_the_census(monkeypatch):
    calls = []

    def fake_fetch(table):
        calls.append(table)
        return dict(TYPES)
    monkeypatch.setattr(ac, "carriage_fetch_column_types", fake_fetch)
    entry = dict(carriage=LATTA_CAR, prose_fields=["source_citation", "narrative.$.a[*].b", "source_citation"])
    assert ac._carriage_ledger_inputs(entry, AID) == (TYPES, ["source_citation", "narrative"]) and calls == [AID]
    for e, tbl in ((None, AID), ({}, AID), ({"carriage": None}, AID), (dict(carriage=dict(LATTA_CAR, applies="D3")), AID), (dict(carriage=LATTA_CAR), "another_table"),
                   (dict(carriage=LATTA_CAR), None), (dict(carriage=dict(LATTA_CAR, spec=None)), AID)):
        calls.clear()
        assert ac._carriage_ledger_inputs(e, tbl)[0] is None and calls == []                  # nothing is read for an asset the ledger does not apply to
    monkeypatch.setattr(ac, "carriage_fetch_column_types", lambda t: (_ for _ in ()).throw(ac.Unknown("catalog down")))
    assert ac._carriage_ledger_inputs(entry, AID) == (None, ["source_citation", "narrative"])   # unreadable is None (NO_DETECTOR downstream), never "no columns"
    assert ac._carriage_prose_columns(None) == [] and ac._carriage_prose_columns([]) == [] and ac._carriage_prose_columns(["narrative", "bad col"]) == ["narrative"]


def _measure_asset(monkeypatch, tmp_path, facts, prose_fields=None, fetch_raises=False):
    """measure() on a stub layer holding the latta as a registry asset: the real glue (measure -> _carriage_ledger_inputs -> carriage_declared_checks -> d1_measure)."""
    reg = {"x": na_causes._reg_row("x", AID), "y": na_causes._reg_row("y")}
    entry = dict(kind="data", carriage=LATTA_CAR)
    if prose_fields is not None:
        entry["prose_fields"] = prose_fields
    na_causes._stub_layer(monkeypatch, tmp_path, reg, tables={AID: (sorted(facts), [])})
    monkeypatch.setattr(ac, "load_asset_declarations", lambda *a, **k: {"x": entry})
    monkeypatch.setattr(ac, "d1_fetch_chunks", lambda ids: {i: copy.deepcopy(CHUNKS[i]) for i in ids if i in CHUNKS})
    monkeypatch.setattr(ac, "d1_fetch_rows", lambda t, c, chart=None: copy.deepcopy(ROWS))
    if fetch_raises:
        monkeypatch.setattr(ac, "carriage_fetch_column_types", lambda t: (_ for _ in ()).throw(ac.Unknown("catalog down")))
    else:
        monkeypatch.setattr(ac, "carriage_fetch_column_types", lambda t: copy.deepcopy(facts))
    return {a["asset_id"]: a["measurements"] for a in ac.measure("L0")["assets"]}


def _measure_feeds_the_ledger(monkeypatch, tmp_path):
    """HIGH 2: measure() itself hands the catalog's column facts to the ledger: clean latta PASS, an extra unclassified text column PARTIAL, an unreadable catalog NO_DETECTOR."""
    ok = _measure_asset(monkeypatch, tmp_path, TYPES)["x"]["Carr.D1"]
    extra = _measure_asset(monkeypatch, tmp_path, dict(TYPES, editorial_claim=CITEXT_F))["x"]["Carr.D1"]
    down = _measure_asset(monkeypatch, tmp_path, TYPES, fetch_raises=True)["x"]["Carr.D1"]
    return (ok["v"] == PASS and extra["v"] == PARTIAL and extra["d1"]["column_ledger"]["uncovered"] == ["editorial_claim"]
            and down["v"] == NO_DET and "column types could not be read" in down["measured"])


def test_measure_feeds_the_column_ledger_clean_pass_unclassified_partial_unreadable_no_detector(monkeypatch, tmp_path):
    assert _measure_feeds_the_ledger(monkeypatch, tmp_path)
    ms = _measure_asset(monkeypatch, tmp_path, TYPES)
    assert not [k for k in ms["y"] if k.startswith("Carr.")]                               # an undeclared asset reads as before


def test_measure_hands_the_declared_prose_fields_to_the_ledger(monkeypatch, tmp_path):
    types = dict(TYPES, extra_note=TEXT_F)
    assert _measure_asset(monkeypatch, tmp_path, types, prose_fields=[])["x"]["Carr.D1"]["v"] == PARTIAL
    assert _measure_asset(monkeypatch, tmp_path, types, prose_fields=["extra_note"])["x"]["Carr.D1"]["v"] == PASS


# ── REAL pg_catalog: the types information_schema hides ──

PG_TYPES = [("citext", "citext", "'x'", "text"), ("mood", "mood", "'x'", "text"), ("dtext", "dtext", "'x'", "text"), ("dcit", "dcit", "'x'", "text"),
            ("name", "name", "'x'", "text"), ("xml", "xml", "'<a>x</a>'", "text"), ("tsvector", "tsvector", "'x'", "text"), ('"char"', '"char"', "'x'", "text"),
            ("text[]", "text[]", "ARRAY['x']", "text"), ("jsonb", "jsonb", "'\"x\"'::jsonb", "text"), ("mood[]", "mood[]", "ARRAY['x']::mood[]", "text"),
            ("varchar(9)", "varchar(9)", "'x'", "text"), ("bpchar", "bpchar", "'x'", "text"),
            ("int", "int", "5", "nontext"), ("int[]", "int[]", "ARRAY[1]", "nontext"), ("numeric", "numeric", "1.5", "nontext"), ("boolean[]", "boolean[]", "ARRAY[true]", "nontext"),
            ("uuid", "uuid", "gen_random_uuid()", "nontext"), ("inet", "inet", "'10.0.0.1'", "nontext")]
TYPE_SETUP = ["CREATE EXTENSION IF NOT EXISTS citext;", "CREATE TYPE mood AS ENUM ('x', 'y');", "CREATE DOMAIN dtext AS text;", "CREATE DOMAIN dcit AS citext;"]


def test_REAL_pg_catalog_facts_resolve_citext_enums_domains_name_xml_tsvector_char_and_arrays(monkeypatch, disposable_pg):
    cols = ", ".join(f"c{i} {decl}" for i, (_n, decl, _v, _c) in enumerate(PG_TYPES))
    s3._real(monkeypatch, disposable_pg, TYPE_SETUP + [f"CREATE TEMP TABLE tt ({cols}) ON COMMIT DROP;"])
    facts = ac.carriage_fetch_column_types("tt")
    assert sorted(facts) == sorted(f"c{i}" for i in range(len(PG_TYPES)))
    for i, (name, _decl, _v, cls) in enumerate(PG_TYPES):
        assert d1.column_type_class(facts[f"c{i}"]) == cls, (name, facts[f"c{i}"])
    assert facts["c3"]["t"] == "citext" and facts["c2"]["t"] == "text"                              # a domain is resolved to its base type
    assert facts["c8"]["c"] == "A" and facts["c8"]["et"] == "text" and facts["c14"]["et"] == "int4"     # an array to its element
    with pytest.raises(ac.Unknown):
        ac.carriage_fetch_column_types("no_such_table")
    for bad in ("t;DROP", 'a"b', "", None):
        with pytest.raises(ac.Unknown):
            ac.carriage_fetch_column_types(bad)


@pytest.mark.parametrize("name, decl, value, cls", PG_TYPES)
def test_REAL_an_extra_unmatched_column_of_every_type_reads_partial_when_text_like_and_pass_when_not(monkeypatch, disposable_pg, name, decl, value, cls):
    """HIGH 1, end to end through the census path on the real latta DDL: before this, citext / enum / domain / name / xml / tsvector / "char" columns read PASS."""
    s3._real(monkeypatch, disposable_pg, TYPE_SETUP + dl._setup() + [f"ALTER TABLE {AID} ADD COLUMN editorial_claim {decl};", f"UPDATE {AID} SET editorial_claim = {value};"])
    got = ac.carriage_declared_checks(AID, LATTA_CAR, AID, column_types=ac.carriage_fetch_column_types(AID), prose_columns=[])["Carr.D1"]
    if cls == "text":
        assert got["v"] == PARTIAL and got["d1"]["column_ledger"]["uncovered"] == ["editorial_claim"], (name, got["v"], got["measured"][:200])
    else:
        assert got["v"] == PASS and "column_ledger" not in got["d1"], (name, got["v"], got["measured"][:200])


def test_REAL_the_unmodified_latta_ddl_reads_pass_through_the_real_catalog_and_the_golden_record_is_reproduced(monkeypatch, disposable_pg):
    s3._real(monkeypatch, disposable_pg, dl._setup())
    types = ac.carriage_fetch_column_types(AID)
    assert sorted(types) == sorted(TYPES)
    types_in, prose = ac._carriage_ledger_inputs(dict(kind="data", carriage=LATTA_CAR, prose_fields=[]), AID)
    assert types_in == types and prose == []
    got = ac.carriage_declared_checks(AID, LATTA_CAR, AID, column_types=types_in, prose_columns=prose)["Carr.D1"]
    assert got["v"] == PASS and "column_ledger" not in got["d1"]
    removed = ac.carriage_declared_checks(AID, _without("source_citation"), AID, column_types=types_in, prose_columns=prose)["Carr.D1"]
    assert removed["v"] == PARTIAL and removed["d1"]["column_ledger"]["uncovered"] == ["source_citation"]


# ───────────────────────── Part 6: kernels are generic: a second kernel needs no latta fields ─────────────────────────

def _stub_row(row, seg, spec):
    return dict(ok=row.get("a") in ("one", "two"))


def _stub_kernel(**over):
    k = dict(spec_required=("cols",), spec_optional=(), result_keys=frozenset({"ok"}), columns=lambda spec: list(spec["cols"]), key_column=lambda spec: spec["cols"][0],
             matched_columns=lambda spec: list(spec["cols"]), coverage=lambda spec: {spec["cols"][1]: "ok"}, validate=lambda spec, where: None, span_check=lambda spec, seg: None,
             evidence_pointers=lambda spec, where: [(f"{where}.proof", "CLAUDE.md:1", " (existence only)")], rule_text="the stub rule")
    k.update(over)
    return k


def _stub_spec(**over):
    return dict(matcher="stub_kernel_v1", table=AID, chunk_ids=list(SPEC["chunk_ids"]), span=dict(SPEC["span"]), expected_rows=2, cols=["a", "b"], **over)


def test_a_second_kernel_with_none_of_the_latta_fields_validates_reads_measures_and_classifies(monkeypatch):
    monkeypatch.setitem(d1.KERNELS, "stub_kernel_v1", _stub_kernel())
    monkeypatch.setitem(d1.MATCHERS, "stub_kernel_v1", _stub_row)
    spec = _stub_spec(row_scope=[{"column": "b", "not_null": True}])
    assert d1.validate_spec(spec, "x") == spec and d1.spec_columns(spec) == ["a", "b"] and d1.prose_coverage(spec) == {"b": "ok"}
    rows = [dict(a="one", b="x"), dict(a="two", b="y"), dict(a="three", b=None)]
    rec = d1.d1_measure(spec, STATE, copy.deepcopy(CHUNKS), rows, AID, ledger=dict(columns=dict(a=TEXT_F, b=TEXT_F), prose_columns=[]))
    assert rec["v"] == PARTIAL and rec["d1"]["matching_rule"] == "the stub rule" and rec["d1"]["rows_total"] == 2 and rec["d1"]["out_of_scope_rows"] == 1
    assert rec["d1"]["rows"][0]["row"] == "one"                                                       # labels come from the kernel's key_column
    clean = d1.d1_measure(_stub_spec(), STATE, copy.deepcopy(CHUNKS), rows[:2], AID, ledger=dict(columns=dict(a=TEXT_F, b=TEXT_F), prose_columns=[]))
    assert clean["v"] == PASS and "column_ledger" not in clean["d1"]
    extra = d1.d1_measure(_stub_spec(), STATE, copy.deepcopy(CHUNKS), rows[:2], AID, ledger=dict(columns=dict(a=TEXT_F, b=TEXT_F, c=TEXT_F), prose_columns=[]))
    assert extra["v"] == PARTIAL and extra["d1"]["column_ledger"]["uncovered"] == ["c"]


def test_a_second_kernel_reaches_the_declarations_validator_through_its_own_evidence_pointers(monkeypatch):
    d1c = ac._carriage_d1()                                          # the census loads its own copy of the engine by file path: patch THAT one
    monkeypatch.setitem(d1c.KERNELS, "stub_kernel_v1", _stub_kernel())
    monkeypatch.setitem(d1c.MATCHERS, "stub_kernel_v1", _stub_row)
    car = dict(applies="D1", nature="transcription", why=LATTA_CAR["why"], evidence=LATTA_CAR["evidence"], citation_state=STATE, spec=_stub_spec())
    ac.validate_carriage_declaration("w", car, {})
    monkeypatch.setitem(d1c.KERNELS, "stub_kernel_v1", _stub_kernel(evidence_pointers=lambda spec, where: [(f"{where}.proof", "no/such/file.md", "")]))
    with pytest.raises(ac.DeclarationsError, match="proof 'no/such/file.md' is not an existing repo-relative file"):
        ac.validate_carriage_declaration("w", car, {})


@pytest.mark.parametrize("hook", list(d1.KERNEL_HOOKS))
def test_a_kernel_lacking_a_hook_is_a_spec_error_never_a_key_error(monkeypatch, hook):
    k = _stub_kernel()
    del k[hook]
    for mod in (d1, ac._carriage_d1()):                              # the test's engine and the census's own copy
        monkeypatch.setitem(mod.KERNELS, "stub_kernel_v1", k)
        monkeypatch.setitem(mod.MATCHERS, "stub_kernel_v1", _stub_row)
    spec = _stub_spec()
    rows = [dict(a="one", b="x"), dict(a="two", b="y")]
    car = dict(applies="D1", nature="transcription", why=LATTA_CAR["why"], evidence=LATTA_CAR["evidence"], citation_state=STATE, spec=spec)
    for call in (lambda: d1._kernel_of(spec), lambda: d1.validate_spec(spec, "x"), lambda: d1.spec_columns(spec), lambda: d1.prose_coverage(spec),
                 lambda: d1.d1_measure(spec, STATE, copy.deepcopy(CHUNKS), rows, AID), lambda: d1.column_ledger(spec, dict(a=TEXT_F))):
        with pytest.raises(d1.SpecError):
            call()
    with pytest.raises(ac.DeclarationsError):
        ac.validate_carriage_declaration("w", car, {})
    with pytest.raises(d1.SpecError, match="lacks the required hook"):
        d1._kernel_of(spec)


def test_the_kernel_and_row_function_registries_cannot_drift(monkeypatch):
    assert set(d1.KERNELS) == set(d1.MATCHERS)
    monkeypatch.setitem(d1.KERNELS, "stub_kernel_v1", _stub_kernel())                                  # a kernel with no row function
    with pytest.raises(d1.SpecError, match="the two registries drifted"):
        d1.d1_measure(_stub_spec(), STATE, copy.deepcopy(CHUNKS), [dict(a="one", b="x")], AID)
    assert d1.d1_measure.__module__ and set(d1.KERNELS) - set(d1.MATCHERS) == {"stub_kernel_v1"}


# ───────────────────────── Part 7: D2 is witness carriage, derivation maps to D3 ─────────────────────────

CAR_BASE = dict(why="the rows are re-derived from another asset's stored facts", evidence="00_ARCHITECTURE/briefs/suvarna/layers/L0/assets/bg_phaladeepika_latta_ELEVATION_BRIEF_v1_0.md")


def _doc(car):
    return dict(version="1.7.0", kind_enum=list(ac.DECLARED_KINDS), assets={AID: {"kind": "data", "carriage": car}})


def _mapping_is_right():
    return (ac.CARRIAGE_NATURE_CHECK == {"transcription": "D1", "computation": "D3", "derivation": "D3", "single_derivation": "D3", "unverified_transcription": "D1", "not_a_transcription": "D1"}
            and "D2" not in ac.CARRIAGE_NATURE_CHECK.values())


def test_derivation_maps_to_d3_and_no_nature_maps_to_d2():
    assert _mapping_is_right()
    assert ac.validate_declarations(_doc(dict(CAR_BASE, applies="D3", nature="derivation")))
    for nature in ("transcription", "computation", "derivation", "single_derivation", "unverified_transcription", "not_a_transcription"):
        for applies in ("D1", "D2", "D3"):
            if applies == ac.CARRIAGE_NATURE_CHECK[nature]:
                continue
            car = dict(CAR_BASE, applies=applies, nature=nature, **({"citation_state": "sourced"} if nature == "transcription" else {}))
            with pytest.raises(ac.DeclarationsError, match="requires applies"):
                ac.validate_declarations(_doc(car))
    with pytest.raises(ac.DeclarationsError, match="D2 is witness carriage"):
        ac.validate_declarations(_doc(dict(CAR_BASE, applies="D2", nature="derivation")))


def test_a_declared_derivation_carriage_is_never_measured_as_d2():
    got = ac.carriage_declared_checks("x", dict(CAR_BASE, applies="D3", nature="derivation"), None, column_types=None, prose_columns=[])
    assert got["Carr.D3"]["v"] == NO_DET and "D3 is declared (nature derivation) but without a `spec`" in got["Carr.D3"]["measured"] and got["Carr.D3"]["declared_carriage"] == dict(applies="D3", nature="derivation")
    assert got["Carr.D1"]["v"] == NA and got["Carr.D2"]["v"] == NA and got["Carr.D1"]["cause"] == got["Carr.D2"]["cause"] == "not-the-declared-carriage"
    assert ac.rollup_asset("L0", got)["Carr"]["v"] == NO_DET and ac.CRITERION_REGISTRY["Carr.D3"]["detector"] != "NONE"       # N-156: D3 is a real detector now; a spec-less declaration still reads NO_DETECTOR


def test_the_registry_still_defines_d2_as_witness_carriage_and_is_unchanged():
    assert "two independent witnesses of the same fact" in ac.CRITERION_REGISTRY["Carr.D2"]["applicability"]
    assert (ac.CRITERION_REGISTRY["Carr.D1"]["revision"], ac.CRITERION_REGISTRY["Carr.D2"]["revision"], ac.CRITERION_REGISTRY["Carr.D3"]["revision"]) == (4, 2, 2)           # N-156: D1 rev 3 (rev 4 for C8), D2 rev 2 (text), D3 rev 2 (detector lifted)
    assert ac.CRITERION_REGISTRY["Carr.D2"]["detector"] == "NONE"


def test_no_committed_declaration_uses_nature_derivation_so_no_cell_can_move():
    decl = json.loads(ac.DECLARATIONS_PATH.read_text(encoding="utf-8"))["assets"]
    natures = {a: e["carriage"]["nature"] for a, e in decl.items() if isinstance(e.get("carriage"), dict) and e["carriage"].get("nature")}
    assert "derivation" not in natures.values()
    # N-156: the 82 L0-L2 assets all declare; the four with a spec are measured, the rest declare a ceiling
    measured = {a: n for a, n in natures.items() if n in ("transcription", "computation")}
    assert measured == {"bg_phaladeepika_latta": "transcription", "bg_vedha_malefic_scale": "transcription", "ga_positions": "computation", "bg_sky_calendar": "computation"} and len(natures) == 82 and set(natures.values()) <= {"transcription", "computation", *ac.CEILING_NATURES, ac.NOT_A_TRANSCRIPTION}


def test_the_nature_to_check_map_has_one_definition_no_other_consumer_re_implements_it():
    root = HERE.parents[3]
    for rel in ("platform/scripts/governance/nikasha_certify.py", "00_ARCHITECTURE/control/asset_elevation_tracker.py", "platform/scripts/governance/carriage_d1.py"):
        src = (root / rel).read_text(encoding="utf-8")
        assert "CARRIAGE_NATURE_CHECK" not in src and '"derivation": "D' not in src and "'derivation': 'D" not in src, rel
    census = (root / "platform/scripts/governance/asset_census.py").read_text(encoding="utf-8")
    assert census.count('"derivation": "D') == 1 and census.count("CARRIAGE_NATURE_CHECK = {") == 1


# ───────────────────────── Part 8: a mutation test per guard ─────────────────────────
# Each guard's own check body is run with the guard REMOVED (a mutant); it must then FAIL, so the test above has teeth.

def _killed(behaviour):
    """True when `behaviour()` (a guard's own check, returning True when the guard holds) fails: it returns False or raises an assertion."""
    try:
        return not behaviour()
    except (AssertionError, KeyError, TypeError, d1.SpecError):
        return True


def test_the_unmutated_guards_hold_so_the_mutants_below_are_meaningful(monkeypatch, tmp_path):
    assert _unknown_kernel_is_refused() and _unknown_and_missing_fields_are_refused() and _scoped_partial_with_one_outside_row() and _ledger_blocks_pass() and _mapping_is_right()
    assert _editorial_pin_does_not_launder_a_text_column() and _unexamined_types_cap_the_verdict() and _measure_feeds_the_ledger(monkeypatch, tmp_path)


def test_mutant_kernel_lookup_that_accepts_any_id_is_caught(monkeypatch):
    monkeypatch.setattr(d1, "_kernel", lambda name: d1.KERNELS[d1.MATCHER])             # the registry is no longer closed
    assert _killed(_unknown_kernel_is_refused)


def test_mutant_spec_field_check_that_allows_unknown_and_missing_fields_is_caught(monkeypatch):
    monkeypatch.setattr(d1, "_spec_field_problem", lambda spec, where: None)
    assert _killed(_unknown_and_missing_fields_are_refused)


def test_mutant_partition_that_ignores_the_scope_is_caught(monkeypatch):
    monkeypatch.setattr(d1, "partition_rows", lambda rows, scope: (list(enumerate(rows)), []))
    assert _killed(_scoped_partial_with_one_outside_row)


def test_mutant_scope_cap_that_never_caps_is_caught(monkeypatch):
    monkeypatch.setattr(d1, "scope_cap_problem", lambda n: None)
    assert _killed(_scoped_partial_with_one_outside_row)
    rec = _measure(spec=_spec(row_scope=SCOPE), rows=_rows(extra=[NOISE]))
    assert rec["v"] == PASS and rec["d1"]["out_of_scope_rows"] == 1                       # what the mutant lets through: a PASS that counted an outside row
    assert "outside the declared row_scope" in ac.d1_evidence_problem(rec)                # ... which the census-side check still refuses (second line of defence)


def test_mutant_scope_predicate_that_matches_everything_is_caught(monkeypatch):
    monkeypatch.setattr(d1, "row_in_scope", lambda row, scope: True)
    assert _killed(_scoped_partial_with_one_outside_row)


def test_mutant_column_ledger_that_reports_clean_is_caught(monkeypatch):
    orig = d1.column_ledger
    monkeypatch.setattr(d1, "column_ledger", lambda spec, types, prose=(): dict(orig(spec, types, prose), uncovered=[], unexamined=[]))
    assert _killed(_ledger_blocks_pass) and _killed(_unexamined_types_cap_the_verdict)


def test_mutant_ledger_cap_that_never_caps_is_caught(monkeypatch):
    monkeypatch.setattr(d1, "ledger_cap_problem", lambda block: None)
    assert _killed(_ledger_blocks_pass) and _killed(_unexamined_types_cap_the_verdict)
    rec = _measure(spec=BARE, rows=_rows(), ledger=dict(columns=TYPES))
    assert rec["v"] == PASS and "column ledger" in ac.d1_evidence_problem(rec)            # second line of defence: the census-side check refuses the forged PASS


def test_mutant_text_classifier_that_sees_no_text_is_caught(monkeypatch):
    monkeypatch.setattr(d1, "column_type_class", lambda fact: "nontext")
    assert _killed(_ledger_blocks_pass)


def test_mutant_classifier_that_calls_every_unfamiliar_type_non_text_is_caught(monkeypatch):
    """M26: `unexamined` computed but ignored (the reviewer's mutant): the unexamined columns must cap the verdict."""
    orig = d1.column_ledger
    monkeypatch.setattr(d1, "column_ledger", lambda spec, types, prose=(): dict(orig(spec, types, prose), unexamined=[]))
    assert _killed(_unexamined_types_cap_the_verdict)


def test_mutant_scope_pin_credited_as_a_constant_is_caught(monkeypatch):
    monkeypatch.setattr(d1, "_constant_columns", lambda spec: list(dict.fromkeys(
        [ef["column"] for ef in spec.get("extra_fields", []) if ef.get("kind") == "equals"] + [c["column"] for c in spec.get("row_scope") or [] if "equals" in c or "in" in c])))
    assert _killed(_editorial_pin_does_not_launder_a_text_column)


def test_mutant_prose_columns_dropped_before_the_ledger_is_caught(monkeypatch, fetch):
    """M25: carriage_declared_checks drops the asset's prose columns."""
    d1c = ac._carriage_d1()
    orig = d1c.d1_measure
    monkeypatch.setattr(d1c, "d1_measure", lambda *a, ledger=None, **k: orig(*a, ledger=dict(ledger, prose_columns=[]), **k))
    assert _killed(_prose_columns_classify)


def test_mutant_measure_that_hands_the_ledger_no_column_types_is_caught(monkeypatch, tmp_path):
    """M34 (HIGH 2): measure() stops feeding the ledger. Its test must fail: the clean latta would read NO_DETECTOR."""
    monkeypatch.setattr(ac, "_carriage_ledger_inputs", lambda entry, tbl: (None, []))
    assert _killed(lambda: _measure_feeds_the_ledger(monkeypatch, tmp_path))


def test_mutant_evidence_check_that_ignores_the_new_guards_is_caught(monkeypatch):
    forged_scope = _measure(spec=_spec(row_scope=SCOPE), rows=_rows())
    forged_scope["d1"]["out_of_scope_rows"] = 1
    forged_ledger = _measure(spec=SPEC, rows=_rows(), ledger=dict(columns=TYPES))
    forged_ledger["d1"]["column_ledger"] = dict(evaluated=True, uncovered=["table_version"], declared_absent=[], unexamined=[])
    assert ac.d1_evidence_problem(forged_scope) and ac.d1_evidence_problem(forged_ledger)
    orig = ac.d1_evidence_problem

    def mutant(meas):
        m = copy.deepcopy(meas)
        for k in ("row_scope", "out_of_scope_rows", "column_ledger"):
            m["d1"].pop(k, None)
        return orig(m)
    monkeypatch.setattr(ac, "d1_evidence_problem", mutant)
    assert not ac.d1_evidence_problem(forged_scope) and not ac.d1_evidence_problem(forged_ledger)       # the mutant honours both forgeries: the tests above fail on it


def test_mutant_nature_map_that_sends_derivation_to_d2_is_caught(monkeypatch):
    monkeypatch.setitem(ac.CARRIAGE_NATURE_CHECK, "derivation", "D2")
    assert _killed(_mapping_is_right)
    with pytest.raises(ac.DeclarationsError):
        ac.validate_declarations(_doc(dict(CAR_BASE, applies="D3", nature="derivation")))      # the mutant refuses the correct declaration and accepts the stale one


def test_mutant_non_claim_naming_check_removed_is_caught(monkeypatch):
    monkeypatch.setattr(ac, "_non_claim_names_column_problem", lambda x: None)
    unrelated = dict(column="table_version", why=GENERIC_WHY, evidence=VEDHA + ":1")
    assert ac.validate_declarations(_doc_with([unrelated, NONCLAIM[1]]))                       # the mutant lets a generic why with an unrelated line declare a column a label


# ───────────────────────── Part 9: zero cell moves, the registry's Carr part did not change ─────────────────────────

CARR_REGISTRY_GOLDEN = HERE / "fixtures" / "n156_carr_registry_golden.json"          # re-generated by N-156 (the Carr gate changed on purpose; the c1_1 golden of main 26777ecb8 stays committed as history)


def _carr_registry(mod):
    """The Carr part of the registry exactly as the golden extracted it from origin/main (26777ecb8, REGISTRY_REVISION 16): criteria, N/A causes, N/A rules, the check list."""
    reg = {k: {kk: (list(vv) if isinstance(vv, tuple) else vv) for kk, vv in v.items()} for k, v in mod.CRITERION_REGISTRY.items() if k.startswith("Carr.")}
    return json.loads(json.dumps(dict(criteria=reg, na_causes={k: list(v) for k, v in mod.NA_CAUSES.items() if k.startswith("Carr.")},
                                      na_rules={k: v for k, v in mod.NA_RULE_DECISIONS.items() if k.startswith("Carr.")},
                                      na_rule_decisions_note=sorted(k for k in mod.NA_RULE_DECISIONS if k.startswith("Carr.")), carr_d_checks=list(mod.CARR_D_CHECKS),
                                      retired=sorted(k for k in getattr(mod, "RETIRED_CRITERIA", {}) if k.startswith("Carr."))), sort_keys=True, default=str))


def test_the_carr_criteria_and_na_rules_are_exactly_as_main_had_them():
    """The Carr part of the registry is exactly the committed N-156 golden (C1-1 changed none of it; N-156 changed D1 rev 3, D2 rev 2, D3 rev 2 + detector, three causes and three rules, on purpose)."""
    gold = json.loads(CARR_REGISTRY_GOLDEN.read_text(encoding="utf-8"))
    assert _carr_registry(ac) == json.loads(json.dumps(gold, sort_keys=True))


def test_the_registry_fingerprint_equals_the_pin_of_the_current_revision():
    assert ac.REGISTRY_REVISION in p1.PINNED_FINGERPRINTS and ac.REGISTRY_REVISION == max(p1.PINNED_FINGERPRINTS)
    assert ac.registry_fingerprint() == p1.PINNED_FINGERPRINTS[ac.REGISTRY_REVISION]


@pytest.mark.skipif(not (SAVED / "census_L0.json").exists(), reason="the saved censuses of adb0db2 are not on this machine (CI)")
def test_on_the_six_saved_censuses_of_adb0db2_no_carr_cell_moves_and_no_cell_while_the_revision_is_the_saved_one():
    decl = ac.load_asset_declarations()
    moved, n, carr, checks = [], 0, 0, 0
    for L in ("L0", "L1", "L2", "L3", "L4", "L5"):
        d = json.loads((SAVED / f"census_{L}.json").read_text(encoding="utf-8"))
        saved_rev = d[L]["registry_revision"]
        assert saved_rev in p1.PINNED_FINGERPRINTS and d[L]["registry_fingerprint"] == p1.PINNED_FINGERPRINTS[saved_rev]          # the saved census is the pinned registry of ITS revision
        same_registry = saved_rev == ac.REGISTRY_REVISION                    # later pins legitimately move other gates' cells: then only the Carr gate is compared
        saved = d["rollup"]["layers"][L]
        now = ac.rollup_census(d[L], {a["asset_id"]: ac.facts_for_asset(a, decl) for a in d[L]["assets"]})
        for aid, cells in now.items():
            for g, c in cells.items():
                n += 1
                if not (same_registry or g == "Carr"):
                    continue
                carr += g == "Carr"
                mine = [(k["criterion"], k["v"]) for k in c["checks"]]
                theirs = [(k["criterion"], k["v"]) for k in saved[aid][g]["checks"]]
                checks += len(mine)
                if c["v"] != saved[aid][g]["v"] or mine != theirs:
                    moved.append((aid, g, saved[aid][g]["v"], c["v"]))
    assert n == 1143 and carr == 127 * 1 and moved == [] and checks >= carr
