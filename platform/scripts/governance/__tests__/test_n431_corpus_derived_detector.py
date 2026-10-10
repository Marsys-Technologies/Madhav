"""test_n431_corpus_derived_detector.py: the REPRODUCIBILITY detector of the `corpus_derived` declaration form (SS N-431, bg_rules).

The detector re-runs a committed, sha256-pinned deterministic parser (in R2's sandbox) over the source chunks the stored rows cite, applies the declared post-processing (drop ephemeral keys, keep
rows at or above the parser's threshold constant, null a foreign key absent from its reference table, first writer wins) and compares the result with the stored rows; a bounded sample of chunks nobody
cites must yield no rule. The declaration form is R1's (`normalise_corpus_derived`, `corpus_derived_pin_problem`, `corpus_derived_na_problem`), the sandbox is R2's (`run_pinned_parser`, whose
parser is called with ONE input dict). Here the sandbox is a local FAKE of the same signature (an in-process runner that verifies the sha256 pin and loads a fake parser from tmp_path), the data reads are
an in-memory `fetch`, and the normaliser / pin check are fakes except where a test says it uses R1's real ones.

Everything is offline and starts no database, EXCEPT the tests named `test_REAL_SQL_*` (a minimal smoke of the real SQL on a disposable PostgreSQL). Per SS N-436 they are NOT run locally
(`-k "not REAL_SQL"`); they run in the CI shard that has PostgreSQL.

Part 1 value normalisation, citation, post-processing. Part 2 the pure comparison. Part 3 the SQL builders. Part 4 the detector with fakes: clean, every mutation of the data, every cap, every
runner stage, the pins. Part 5 the real fetch (psql monkeypatched). Part 6 the wiring into the cells (the engine's own `_measure_prose`). Part 7 the rollup guards. Part 8 opt-in. Part 9 the REAL
bg_rules declaration and parser end to end (offline). Part 10 REAL SQL smoke."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import pathlib
import sys
from decimal import Decimal

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401

cdd = ac._corpus_derived_mod()      # the very module object the engine loads (its Unread class is the one the real fetch raises)

PASS, FAIL, NO_DET, NA = "PASS", "FAIL", "NO_DETECTOR", "N/A"
CELLS = list(ac.NARR_CHECKS + ac.NULL_CHECKS)
FIVE = ["Narr.agree", "Narr.checkable", "Narr.fidelity_test", "Null.schema_default", "Null.blank_rows"]
AID = "bg_rules_fixture"

# ───────────────────────────── the fake parser (one input dict per chunk), pinned by hash ─────────────────────────────
PARSER_SRC = '''
import json

QUALITY_THRESHOLD_LIVE = 0.6


def extract(item):
    chunk = item["chunk"]
    text = chunk.get("content_en") or ""
    valid = set(item.get("valid_text_ids") or [])
    out = []
    for n, w in enumerate(x for x in text.split() if x.startswith("RULE:") or x.startswith("WEAK:")):
        q = 1.0 if w.startswith("RULE:") else 0.5
        if chunk["text_id"] not in valid:
            q -= 0.2
        body = w[5:]
        rid = "%s#%d" % (chunk["id"], n) if "__GLOBAL__" not in text else "g-" + body
        out.append({
            "rule_id": rid, "text_id": chunk["text_id"], "verse_ref": chunk["verse_ref"], "body": body,
            "prediction_jsonb": json.dumps({"result": body, "domain": "d"}), "confidence": q, "transit_marker": False,
            "extraction_pass_log": json.dumps([{"chunk_id": chunk["id"], "match_text": w}]), "extracted_by": "fake_v2",
            "yoga_canonical_id": ("Y9" if "YOGA9" in text else "Y1" if "YOGA1" in text else None), "_quality": q,
        })
    return out
'''
TABLE_COLS = ["rule_id", "text_id", "verse_ref", "body", "prediction_jsonb", "confidence", "transit_marker", "extraction_pass_log", "extracted_by", "yoga_canonical_id", "created_at"]
CHUNK_TEXT = {"c01": "RULE:a RULE:b", "c02": "RULE:c YOGA1", "c04": "RULE:d WEAK:w YOGA9"}      # the cited chunks; c03 and c05..c12 are uncited and empty
CHUNK_IDS = [f"c{i:02d}" for i in range(1, 13)]


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def mk_chunks(extra=None, verse_start=None):
    txt = dict(CHUNK_TEXT, **(extra or {}))
    vs = verse_start or {}
    return [dict(id=c, text_id="T1", chapter=1, verse_start=vs.get(c, i), verse_ref=f"v{c}", content_en=txt.get(c, "")) for i, c in enumerate(CHUNK_IDS, 1)]


def load_parser(path):
    spec = importlib.util.spec_from_file_location("fake_parser_n431", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.extract


@pytest.fixture()
def world(tmp_path):
    (tmp_path / "parser").mkdir()
    f = tmp_path / "parser" / "l0_fake.py"
    f.write_text(PARSER_SRC, encoding="utf-8")
    d = tmp_path / "parser" / "data.json"
    d.write_text('{"k": 1}', encoding="utf-8")
    return dict(root=tmp_path, file=f, data=d, sha=sha(PARSER_SRC), data_sha=sha('{"k": 1}'), fn=load_parser(f))


def simulate_writer(world, chunks, valid_ids=("T1",), yoga_ids=("Y1",), only=None):
    """The stored table as the real writer leaves it: chunks in (text_id, chapter, verse_start, id) order, the parser output, quality >= the threshold, the ephemeral key dropped, a foreign key
    absent from its reference table nulled, ON CONFLICT DO NOTHING (first wins); read back as to_jsonb returns it (parsed json columns)."""
    rows, seen = [], set()
    for ch in sorted(chunks, key=lambda c: (c["text_id"], c["chapter"], c["verse_start"], c["id"])):
        if only is not None and ch["id"] not in only:
            continue
        for r in world["fn"](dict(chunk=ch, valid_text_ids=sorted(valid_ids))):
            if r["_quality"] < 0.6:
                continue
            s = {k: v for k, v in r.items() if k != "_quality"}
            if s["yoga_canonical_id"] and s["yoga_canonical_id"] not in yoga_ids:
                s["yoga_canonical_id"] = None
            if s["rule_id"] in seen:
                continue
            seen.add(s["rule_id"])
            s["prediction_jsonb"] = json.loads(s["prediction_jsonb"])
            s["extraction_pass_log"] = json.loads(s["extraction_pass_log"])
            s["created_at"] = "2026-10-01T00:00:00+00:00"
            rows.append(s)
    return rows


def decl_for(world, sample=4, **over):
    """A fully NORMALISED declaration (what R1's normaliser returns), for the fake parser."""
    cd = dict(table="rules", key_columns=["rule_id"], cite_column="extraction_pass_log", cite_path=[0, "chunk_id"],
              source=dict(table="chunks", id_column="id", text_columns=["content_en"], extra_columns=["text_id", "verse_ref"], order_by=["text_id", "chapter", "verse_start"]),
              parser=dict(module_root="parser", file="parser/l0_fake.py", function="extract",
                          pinned_files=[dict(path="parser/l0_fake.py", sha256=world["sha"]), dict(path="parser/data.json", sha256=world["data_sha"])], input_shape="chunk_row_dict",
                          extra_args=[dict(name="valid_text_ids", kind="distinct_values", table="chunks", column="text_id")]),
              derived=dict(drop_keys=["_quality"], keep_when=dict(key="_quality", at_least_constant="QUALITY_THRESHOLD_LIVE"),
                           null_unless_in=[dict(column="yoga_canonical_id", table="yoga_catalog", ref_column="canonical_id")],
                           json_columns=["prediction_jsonb", "extraction_pass_log"], numeric_columns=["confidence"], duplicate_policy="first_wins"),
              ignore_columns=["created_at"], scope=dict(stored=dict(column="extracted_by", equals="fake_v2"), uncited_chunks=dict(sample=sample)), why="w", evidence="e")
    cd.update(over)
    return cd


def entry_for(world, **kw):
    return {"prose_fields": None, "corpus_derived": decl_for(world, **kw)}


def normaliser(e):
    return copy.deepcopy(e["corpus_derived"])


class FakeDB:
    """An in-memory `fetch` (the detector's data-reading layer). Hooks let a test truncate or change what an op returns."""
    def __init__(self, stored, chunks, yoga=("Y1", "Y2")):
        self.tables = {"rules": stored, "chunks": chunks, "yoga_catalog": [dict(canonical_id=y) for y in yoga]}
        self.cols = {"rules": list(TABLE_COLS), "chunks": ["id", "text_id", "chapter", "verse_start", "verse_ref", "content_en"], "yoga_catalog": ["canonical_id"]}
        self.calls, self.reqs = [], []
        self.rows_hook = self.count_hook = self.unread_on = None

    def _rows(self, req):
        rows = self.tables[req["table"]]
        f = req.get("filter")
        return [r for r in rows if r.get(f["column"]) == f["equals"]] if f else list(rows)

    def __call__(self, req):
        self.calls.append(req["op"])
        self.reqs.append(req)
        if self.unread_on == req["op"]:
            raise cdd.Unread(f"statement timeout during {req['op']}")
        t = req["table"]
        if req["op"] == "columns":
            return list(self.cols.get(t, []))
        if req["op"] == "count":
            n = len(self._rows(req))
            return self.count_hook(t, n) if self.count_hook else n
        if req["op"] == "rows":
            rows = sorted(self._rows(req), key=lambda r: tuple(str(r[c]) for c in req["order_by"]))
            page = [{c: r[c] for c in req["columns"] if c in r} for r in rows[req["offset"]:req["offset"] + req["limit"]]]
            return self.rows_hook(page, req) if self.rows_hook else page
        if req["op"] == "ids":
            oc = req.get("order_by") or []
            return [str(r[req["id_column"]]) for r in sorted(self.tables[t], key=lambda r: tuple(str(r[c]) if c not in ("chapter", "verse_start") else r[c] for c in oc) + (str(r[req["id_column"]]),))]
        if req["op"] == "chunks":
            want = set(req["ids"])
            return [{c: r[c] for c in [req["id_column"]] + list(req["columns"])} for r in sorted(self.tables[t], key=lambda r: r["id"]) if r["id"] in want]
        if req["op"] == "distinct":
            vals = sorted({str(r[req["column"]]) for r in self.tables[t] if r.get(req["column"]) is not None})
            return vals[:req["limit"] + 1]
        raise AssertionError(req)


def make_runner(world, calls=None, fail=None, loaded=None, drop_outputs=False, outputs=None):
    """The FAKE of parser_sandbox.run_pinned_parser: verifies the sha256 pins, loads the pinned file in-process and calls function(item) with ONE input dict per chunk."""
    def run(repo_root, module_root, pinned_files, file, function, inputs, *, timeout_s=120, max_output_bytes=64_000_000):
        if calls is not None:
            calls.append(dict(repo_root=repo_root, module_root=module_root, pinned=pinned_files, file=file, function=function, inputs=inputs, timeout_s=timeout_s))
        if fail:
            if fail == "raise":
                raise RuntimeError("boom")
            return {"ok": False, "error": f"{fail}: injected", "stage": fail}
        for p in pinned_files:
            if sha((pathlib.Path(repo_root) / p["path"]).read_text(encoding="utf-8")) != p["sha256"]:
                return {"ok": False, "error": f"pin_mismatch: {p['path']}", "stage": "pin"}
        fn = load_parser(pathlib.Path(repo_root) / file)
        outs = [fn(dict(i)) for i in inputs]
        if drop_outputs:
            outs = outs[:-1]
        return {"ok": True, "outputs": outputs if outputs is not None else outs, "loaded_repo_files": list(loaded if loaded is not None else [file]), "elapsed_s": 0.01,
                "assurance": "software-guarded, reviewed code only"}
    return run


def allowed_for(world):
    """The fake world's parser pair (the production allow-list names only the reviewed bg_rules adapter)."""
    return (dict(module_root="parser", file="parser/l0_fake.py", function="extract", must_pin=("parser/l0_fake.py", "parser/data.json")),)


def run_detect(world, entry=None, stored=None, chunks=None, db=None, runner=None, pin_check=None, **kw):
    kw.setdefault("allowed", allowed_for(world))
    chunks = chunks if chunks is not None else mk_chunks()
    if db is None:
        st = stored if stored is not None else simulate_writer(world, chunks)
        db = FakeDB(st, chunks)
    return cdd.detect_corpus_derived(entry or entry_for(world), fetch=db, runner=runner or make_runner(world), normaliser=normaliser, repo_root=str(world["root"]), pin_check=pin_check, **kw), db


# ═════════════════════════════ Part 1: normalisation, citation, post-processing ═════════════════════════════

@pytest.mark.parametrize("a,b,eq", [
    (None, None, True), (None, "", False), (None, 0, False), ("", [], False),
    (1, 1.0, True), (1, Decimal("1.00"), True), (0.8, Decimal("0.8"), True), (0.8, 0.80000001, False), (Decimal("0.8"), 0.9, False),
    (True, 1, False), (False, 0, False), (True, True, True),
    ([1, 2], (1, 2), True), ([1, 2], [2, 1], False), ([1], [1, 1], False), ([], [], True),
    ({"a": 1, "b": [1.0]}, {"b": [1], "a": 1}, True), ({"a": 1}, {"a": 1, "b": None}, False), ({"a": 1}, {"a": 2}, False),
    ("abc", "ABC", False), ("abc", "abc", True),
    ("A1B2C3D4-0000-4000-8000-000000000001", "a1b2c3d4-0000-4000-8000-000000000001", True),           # canonical UUIDs only
    ("[1, 2]", [1, 2], False), ('{"a": 1}', {"a": 1}, False), ("0.8", 0.8, False),                    # plain columns: no JSON-text and no numeric-text reading
    (float("nan"), float("nan"), True), (float("inf"), 1, False),
])
def test_values_equal_plain_normalisation(a, b, eq):
    assert cdd.values_equal(a, b) is eq
    assert cdd.values_equal(b, a) is eq


@pytest.mark.parametrize("a,b,eq", [
    ('{"a": 1, "b": [1]}', {"b": [1], "a": 1.0}, True), ('[1, 2]', [1, 2], True), ('[1, 2]', [1, 3], False), ("not json", [1], False), ('{"a": 1}', {"a": 2}, False),
    ('{"a": 1}', '{ "a" : 1 }', True), ('{"a": 1.0}', '{"a": 1}', True), ('"x"', "x", True), ("x", "x", True), (None, None, True), (None, "null", True),
])
def test_values_equal_json_kind_parses_text_on_either_side(a, b, eq):
    assert cdd.values_equal(a, b, "json") is eq
    assert cdd.values_equal(b, a, "json") is eq


@pytest.mark.parametrize("a,b,eq", [("0.8", 0.8, True), (Decimal("0.800"), "0.8", True), ("0.9", 0.8, False), ("abc", "abc", True), ("abc", 1, False), (None, None, True), (None, "0", False)])
def test_values_equal_numeric_kind_reads_numeric_text(a, b, eq):
    assert cdd.values_equal(a, b, "numeric") is eq


@pytest.mark.parametrize("row,path,expect", [
    ({"c": [{"chunk_id": "c01"}]}, [0, "chunk_id"], ("c01", None)),
    ({"c": '[{"pattern": "P1", "chunk_id": "c01"}]'}, [0, "chunk_id"], ("c01", None)),
    ({"c": [{"chunk_id": "c01"}]}, [1, "chunk_id"], (None, "none")), ({"c": [{"other": 1}]}, [0, "chunk_id"], (None, "none")), ({"c": []}, [0, "chunk_id"], (None, "none")),
    ({"c": None}, [0, "chunk_id"], (None, "none")), ({"c": ""}, None, (None, "none")), ({"c": "c09"}, None, ("c09", None)), ({"c": 7}, None, ("7", None)),
    ({"c": [{"chunk_id": "a'b"}]}, [0, "chunk_id"], (None, "malformed")), ({"c": [{"chunk_id": {"x": 1}}]}, [0, "chunk_id"], (None, "malformed")), ({"c": "a b"}, None, (None, "malformed")),
    ({"c": True}, None, (None, "malformed")), ({"c": "x; DROP"}, None, (None, "malformed")), ({}, [0], (None, "none")),
])
def test_cite_id_of(row, path, expect):
    assert cdd.cite_id_of(row, "c", path) == expect


def test_count_blank_leaves_walks_json_columns_and_ignores_null():
    assert cdd.count_blank_leaves({"a": "x", "b": None, "c": 0, "d": False}) == 0
    assert cdd.count_blank_leaves({"a": "", "b": "  \n", "c": "ok"}) == 2
    assert cdd.count_blank_leaves({"j": '{"a": "", "b": ["x", " "]}'}, ("j",)) == 2
    assert cdd.count_blank_leaves({"j": '{"a": ""}'}) == 0                                    # a text column is not parsed unless declared json
    assert cdd.count_blank_leaves({"j": {"a": [{"b": ""}]}}) == 1


DER = dict(key_columns=["rule_id"], cite_column="extraction_pass_log", cite_path=[0, "chunk_id"], ignore_columns=["created_at"],
           derived=dict(drop_keys=["_quality"], keep_when=dict(key="_quality", at_least_constant="Q"), null_unless_in=[dict(column="fk", table="ref", ref_column="id")],
                        json_columns=["extraction_pass_log"], numeric_columns=["confidence"], duplicate_policy="first_wins"))


def test_derive_rows_keeps_at_or_above_the_threshold_drops_keys_and_nulls_unknown_foreign_keys():
    raw = [dict(rule_id="a", _quality=0.6, fk="Y1"), dict(rule_id="b", _quality=0.59, fk="Y1"), dict(rule_id="c", _quality=1, fk="ZZ"), dict(rule_id="d", _quality=0.9, fk=None), dict(rule_id="e", _quality=0.9, fk="")]
    got = cdd.derive_rows(raw, DER, {("ref", "id"): {"Y1"}}, 0.6)
    assert [r["rule_id"] for r in got] == ["a", "c", "d", "e"] and all("_quality" not in r for r in got)
    assert [r["fk"] for r in got] == ["Y1", None, None, ""]                                    # the writer nulls a TRUTHY unknown value only
    assert cdd.derive_rows(raw, DER, {("ref", "id"): set()}, 0.6)[0]["fk"] is None
    assert raw[0]["_quality"] == 0.6                                                           # the input is not mutated


def test_derive_rows_without_a_derived_block_is_the_identity_and_refuses_malformed_rows():
    assert cdd.derive_rows([dict(a=1)], dict(key_columns=["a"])) == [dict(a=1)]
    for bad in ([dict(rule_id="a")], [dict(rule_id="a", _quality="x")], [dict(rule_id="a", _quality=True)], ["x"]):
        with pytest.raises(ValueError):
            cdd.derive_rows(bad, DER, {}, 0.6)
    with pytest.raises(ValueError):
        cdd.derive_rows([dict(rule_id="a", _quality=1)], DER, {}, None) if False else cdd.derive_rows([dict(rule_id="a")], DER, {}, 0.6)


def test_module_constant_reads_a_single_numeric_literal_by_ast():
    assert cdd.module_constant("X = 1\nQ: float = 0.6\n", "Q") == 0.6
    for src in ("Q = 0.6\nQ = 0.7\n", "Q = 'x'\n", "Q = 1 + 1\n", "other = 1\n", "Q = True\n"):
        with pytest.raises(ValueError):
            cdd.module_constant(src, "Q")


# ═════════════════════════════ Part 2: the pure comparison ═════════════════════════════

def rowx(rid, chunk, body="x", **kw):
    s = dict(rule_id=rid, body=body, confidence=0.8, extraction_pass_log=[{"chunk_id": chunk}], created_at="t1")
    s.update(kw)
    return s


def drow(rid, chunk, body="x", **kw):
    d = dict(rule_id=rid, body=body, confidence=0.8, extraction_pass_log=json.dumps([{"chunk_id": chunk}]), created_at="t2")
    d.update(kw)
    return d


def test_compare_clean_pass_ignores_ignored_columns_and_reads_declared_json_columns():
    r = cdd.compare_corpus_derived([rowx("r1", "c1"), rowx("r2", "c2")], {"c1": [drow("r1", "c1")], "c2": [drow("r2", "c2")], "c3": []}, DER)
    assert r["v"] == PASS and r["first_differences"] == [] and r["counts"]["matched"] == 2 and r["counts"]["uncited_chunks_run"] == 1 and r["difference_counts"] == {}


def test_compare_an_undeclared_json_text_column_is_not_parsed():
    d = copy.deepcopy(DER)
    d["derived"]["json_columns"] = []
    r = cdd.compare_corpus_derived([rowx("r1", "c1")], {"c1": [drow("r1", "c1")]}, d)
    assert r["v"] == FAIL and r["first_differences"][0]["columns"] == ["extraction_pass_log"]


def test_compare_hand_edited_value_fails_naming_key_and_column_but_never_the_value():
    secret = "HAND-EDITED-SENTENCE-9137"
    r = cdd.compare_corpus_derived([rowx("r1", "c1", body=secret)], {"c1": [drow("r1", "c1")]}, DER)
    assert r["v"] == FAIL
    d = r["first_differences"][0]
    assert d["kind"] == "differs" and d["key"] == {"rule_id": "r1"} and d["columns"] == ["body"] and d["chunk"] == "c1"
    assert secret not in json.dumps(r) and secret not in r["measured"]


def test_compare_names_every_differing_column_and_a_column_present_on_one_side_only():
    r = cdd.compare_corpus_derived([rowx("r1", "c1", body="y", confidence=0.9, stored_only="s")], {"c1": [drow("r1", "c1", derived_only="d")]}, DER)
    assert r["v"] == FAIL and r["first_differences"][0]["columns"] == ["body", "confidence", "derived_only", "stored_only"]


def test_compare_numeric_column_is_decimal_equal_and_a_changed_number_differs():
    assert cdd.compare_corpus_derived([rowx("r1", "c1", confidence=Decimal("0.800"))], {"c1": [drow("r1", "c1", confidence=0.8)]}, DER)["v"] == PASS
    assert cdd.compare_corpus_derived([rowx("r1", "c1", confidence=Decimal("0.801"))], {"c1": [drow("r1", "c1", confidence=0.8)]}, DER)["v"] == FAIL


def test_compare_deleted_stored_row_is_missing_stored():
    r = cdd.compare_corpus_derived([rowx("r1", "c1")], {"c1": [drow("r1", "c1"), drow("r2", "c1")]}, DER)
    assert r["v"] == FAIL and r["difference_counts"] == {"missing_stored": 1} and r["first_differences"][0]["key"] == {"rule_id": "r2"}


def test_compare_extra_stored_row_has_no_derived_counterpart():
    r = cdd.compare_corpus_derived([rowx("r1", "c1"), rowx("r9", "c1")], {"c1": [drow("r1", "c1")]}, DER)
    assert r["v"] == FAIL and r["difference_counts"] == {"extra_stored": 1} and r["first_differences"][0]["key"] == {"rule_id": "r9"}
    assert cdd.compare_corpus_derived([rowx("r1", "c1")], {"c1": []}, DER)["difference_counts"] == {"extra_stored": 1}
    assert cdd.compare_corpus_derived([rowx("r1", "c1")], {"c2": []}, DER)["difference_counts"] == {"extra_stored": 1}


def test_compare_uncited_chunk_that_yields_a_rule_fails():
    r = cdd.compare_corpus_derived([rowx("r1", "c1")], {"c1": [drow("r1", "c1")], "c7": [drow("r7", "c7")]}, DER)
    assert r["v"] == FAIL and r["difference_counts"] == {"uncited_chunk_yields_rule": 1}
    assert r["first_differences"][0]["chunk"] == "c7" and r["first_differences"][0]["key"] == {"rule_id": "r7"}


def test_compare_cited_chunk_absent_from_the_source_fails():
    r = cdd.compare_corpus_derived([rowx("r1", "c1")], {"c1": None}, DER)
    assert r["v"] == FAIL and r["difference_counts"].get("cited_chunk_absent") == 1


def test_compare_stored_row_that_cites_nothing_or_a_malformed_id_fails():
    r = cdd.compare_corpus_derived([rowx("r1", "c1", extraction_pass_log=None)], {"c1": []}, DER)
    assert r["v"] == FAIL and r["difference_counts"].get("stored_row_cites_no_chunk") == 1
    r = cdd.compare_corpus_derived([rowx("r1", "x'y")], {}, DER)
    assert r["v"] == FAIL and "stored_row_cites_no_chunk" in r["difference_counts"]


def test_compare_duplicate_stored_key_fails():
    r = cdd.compare_corpus_derived([rowx("r1", "c1"), rowx("r1", "c1", body="z")], {"c1": [drow("r1", "c1")]}, DER)
    assert r["v"] == FAIL and r["difference_counts"].get("stored_duplicate_key") == 1


def test_compare_first_writer_wins_in_the_writer_chunk_order():
    # the key g is derived from c2 and c1; the writer visits c2 first (chunk_order), so the stored row cites c2
    g1, g2 = drow("g", "c1"), drow("g", "c2")
    ok = cdd.compare_corpus_derived([rowx("g", "c2")], {"c1": [g1], "c2": [g2]}, DER, chunk_order=["c2", "c1"])
    assert ok["v"] == PASS and ok["counts"]["shadowed"] == 1
    bad = cdd.compare_corpus_derived([rowx("g", "c1")], {"c1": [g1], "c2": [g2]}, DER, chunk_order=["c2", "c1"])           # the later writer's version is stored: first-wins violated
    assert bad["v"] == FAIL and bad["first_differences"][0]["kind"] == "differs" and bad["first_differences"][0]["columns"] == ["extraction_pass_log"]
    assert cdd.compare_corpus_derived([rowx("g", "c1")], {"c1": [g1], "c2": [g2]}, DER, chunk_order=["c1", "c2"])["v"] == PASS
    assert cdd.compare_corpus_derived([rowx("g", "c1")], {"c1": [g1], "c2": [g2]}, DER)["v"] == PASS                          # default order: by id


def test_compare_a_shadowed_key_in_an_uncited_chunk_is_not_a_yield_but_a_winning_uncited_chunk_is():
    g1, g9 = drow("g", "c1"), drow("g", "c9")
    assert cdd.compare_corpus_derived([rowx("g", "c1")], {"c1": [g1], "c9": [g9]}, DER, chunk_order=["c1", "c9"])["v"] == PASS
    r = cdd.compare_corpus_derived([rowx("g", "c1")], {"c1": [g1], "c9": [g9]}, DER, chunk_order=["c9", "c1"])
    assert r["v"] == FAIL and r["first_differences"][0]["kind"] == "differs"                                                  # the uncited chunk would have written it first


def test_compare_duplicate_policy_refuse_makes_a_second_chunk_yielding_the_key_a_difference():
    d = copy.deepcopy(DER)
    d["derived"]["duplicate_policy"] = "refuse"
    r = cdd.compare_corpus_derived([rowx("g", "c1")], {"c1": [drow("g", "c1")], "c2": [drow("g", "c2")]}, d)
    assert r["v"] == FAIL and r["difference_counts"].get("derived_key_collision") == 1


def test_compare_derived_key_collision_inside_a_chunk_with_different_content_fails_identical_is_shadowed():
    r = cdd.compare_corpus_derived([rowx("r1", "c1")], {"c1": [drow("r1", "c1"), drow("r1", "c1", body="other")]}, DER)
    assert r["v"] == FAIL and r["difference_counts"].get("derived_key_collision") == 1
    r = cdd.compare_corpus_derived([rowx("r1", "c1")], {"c1": [drow("r1", "c1"), drow("r1", "c1")]}, DER)
    assert r["v"] == PASS and r["counts"]["shadowed"] == 1


def test_compare_a_blank_string_in_a_derived_row_is_a_blank_leaf_difference():
    r = cdd.compare_corpus_derived([rowx("r1", "c1", body="")], {"c1": [drow("r1", "c1", body="")]}, DER)
    assert r["v"] == FAIL and r["difference_counts"] == {"blank_leaf": 1} and r["counts"]["blank_leaves"] == 1 and r["first_differences"][0]["columns"] == ["body"]
    r = cdd.compare_corpus_derived([rowx("r1", "c1", extraction_pass_log=[{"chunk_id": "c1", "m": " "}])], {"c1": [drow("r1", "c1", extraction_pass_log=json.dumps([{"chunk_id": "c1", "m": " "}]))]}, DER)
    assert r["v"] == FAIL and r["counts"]["blank_leaves"] == 1                                    # inside a declared json column


def test_compare_composite_key_and_key_alignment_do_not_depend_on_order():
    d2 = dict(DER, key_columns=["a", "b"])
    cp = json.dumps([{"chunk_id": "c1"}])
    s = [dict(a=1, b="x", extraction_pass_log=[{"chunk_id": "c1"}], v=1), dict(a=1, b="y", extraction_pass_log=[{"chunk_id": "c1"}], v=2)]
    dv = [dict(a=1, b="y", extraction_pass_log=cp, v=2), dict(a=1.0, b="x", extraction_pass_log=cp, v=1)]
    assert cdd.compare_corpus_derived(s, {"c1": dv}, d2)["v"] == PASS


def test_compare_reports_at_most_five_differences_in_a_deterministic_order_with_total_counts():
    stored = [rowx(f"r{i}", "c1", body="edited") for i in range(9)]
    r = cdd.compare_corpus_derived(stored, {"c1": [drow(f"r{i}", "c1") for i in range(9)]}, DER)
    assert r["v"] == FAIL and len(r["first_differences"]) == 5 and r["difference_counts"] == {"differs": 9}
    assert [d["key"]["rule_id"] for d in r["first_differences"]] == ["r0", "r1", "r2", "r3", "r4"]
    assert r == cdd.compare_corpus_derived(stored, {"c1": [drow(f"r{i}", "c1") for i in reversed(range(9))]}, DER)


def test_compare_no_stored_row_is_vacuous_no_detector_never_pass():
    assert cdd.compare_corpus_derived([], {"c1": []}, DER)["v"] == NO_DET


@pytest.mark.parametrize("stored,derived", [
    ([{"body": "x"}], {"c1": []}), ([rowx("r1", "c1")], {"c1": "not a list"}), ([rowx("r1", "c1")], {"c1": [{"body": "x"}]}), ([rowx("r1", "c1")], {"c1": ["x"]}),
])
def test_compare_malformed_inputs_raise_value_error(stored, derived):
    with pytest.raises(ValueError):
        cdd.compare_corpus_derived(stored, derived, DER)


def test_sample_uncited_is_deterministic_ordered_every_kth_and_bounded():
    ids = [f"c{i:02d}" for i in range(1, 13)]
    s, total = cdd.sample_uncited(ids, {"c01", "c02", "c04"}, 4)
    assert total == 9 and s == ["c03", "c06", "c08", "c10"]
    assert cdd.sample_uncited(reversed(ids), {"c01", "c02", "c04"}, 4) == (s, total)
    assert cdd.sample_uncited(ids, set(ids), 4) == ([], 0)
    assert cdd.sample_uncited(ids, set(), 100)[0] == ids and len(cdd.sample_uncited(ids, set(), 3)[0]) == 3


# ═════════════════════════════ Part 3: the SQL builders ═════════════════════════════

def test_sql_builders_are_total_ordered_quoted_sliced_and_refuse_injection():
    assert 'ORDER BY "rule_id" LIMIT 500 OFFSET 1000' in cdd.rows_sql("sutravali_rules", ["rule_id", "body"], ["rule_id"], 500, 1000)
    assert 'ORDER BY t."rule_id"' in cdd.rows_sql("sutravali_rules", ["rule_id"], ["rule_id"], 5, 0)
    f = cdd.filter_sql(dict(column="extracted_by", equals="python_regex_v2"))
    assert f == '"extracted_by"::text = \'python_regex_v2\'' and "WHERE (" + f + ")" in cdd.rows_sql("t", ["a"], ["a"], 1, 0, f) and "WHERE (" + f + ")" in cdd.count_sql("t", None, f)
    assert cdd.sql_literal("o'k") == "'o''k'" and cdd.filter_sql(None) is None and cdd.count_sql("t") == 'SELECT to_jsonb(count(*))::text FROM "t"'
    s = cdd.chunks_sql("classical_text_chunks", "id", ["content_en", "text_id"], ["u-1", "u-2"])
    assert "IN ('u-1','u-2')" in s and "jsonb_build_object('id', s.\"id\"::text,'content_en', s.\"content_en\",'text_id', s.\"text_id\")" in s
    assert "ORDER BY x.o0, x.o1, x.i" in cdd.ids_sql("classical_text_chunks", "id", ["text_id", "chapter"]) and "ORDER BY x.i" in cdd.ids_sql("classical_text_chunks", "id")
    d = cdd.distinct_sql("classical_text_chunks", "text_id", 100)
    assert 'DISTINCT "text_id"::text AS v' in d and 'WHERE ("text_id" IS NOT NULL)' in d and "ORDER BY 1 LIMIT 101" in d
    assert "to_regclass('\"t\"')" in cdd.columns_sql("t")
    for bad in ('t"; DROP TABLE x;--', "a b", "1x", ""):
        with pytest.raises(ValueError):
            cdd.ident(bad)
    for bad in ("u'; DROP", "a b", "", "x" * 200):
        with pytest.raises(ValueError):
            cdd.chunks_sql("c", "id", [], [bad])
    for bad in ("", "a\\b", "a\nb", None, 5):
        with pytest.raises(ValueError):
            cdd.sql_literal(bad)


# ═════════════════════════════ Part 4: the detector with fakes ═════════════════════════════

def test_clean_case_passes_with_the_full_block_in_the_shape_r1_requires(world):
    calls = []
    res, db = run_detect(world, runner=make_runner(world, calls))
    assert res["v"] == PASS and res["stage"] is None, res["measured"]
    b = res["block"]
    assert b["checked"] and b["verified"] and b["v"] == PASS and b["table"] == "rules" and b["stored_rows"] == 4 == b["matched_rows"] and b["mismatches"] == 0 and b["uncited_yield"] == 0
    assert b["blank_leaves"] == 0 and b["cited_chunks"] == 3 and b["uncited_sampled"] == 4 and b["uncited_total"] == 9 and b["chunks_run"] == 7 and b["first_differences"] == []
    assert b["parser"] == dict(file="parser/l0_fake.py", function="extract", sha256=world["sha"]) and b["pinned_files"] == ["parser/l0_fake.py", "parser/data.json"] and b["loaded_repo_files"] == ["parser/l0_fake.py"]
    assert b["ignore_columns"] == ["created_at"] and b["keep_when_threshold"] == 0.6 and b["extra_args"] == ["valid_text_ids"]
    assert ac.corpus_derived_na_problem("Narr.agree", ac._na("x", ac.CORPUS_DERIVED_CAUSE) | {"corpus_derived": b}) is None             # R1's own guard accepts the block
    assert len(calls) == 1 and len(calls[0]["inputs"]) == 7 and calls[0]["file"] == "parser/l0_fake.py" and calls[0]["repo_root"] == str(world["root"]) and calls[0]["timeout_s"] == cdd.RUN_TIMEOUT_S
    assert calls[0]["pinned"] == [dict(path="parser/l0_fake.py", sha256=world["sha"]), dict(path="parser/data.json", sha256=world["data_sha"])]


def test_the_runner_gets_one_dict_per_chunk_with_the_extra_args_by_name_cited_chunks_first(world):
    calls = []
    run_detect(world, runner=make_runner(world, calls))
    items = calls[0]["inputs"]
    assert [i["chunk"]["id"] for i in items] == ["c01", "c02", "c04", "c03", "c06", "c08", "c10"]           # cited (id order), then the uncited sample (id order)
    assert set(items[0]) == {"chunk", "valid_text_ids"} and set(items[0]["chunk"]) == {"id", "content_en", "text_id", "verse_ref"} and items[0]["valid_text_ids"] == ["T1"]
    assert all(i["valid_text_ids"] == ["T1"] for i in items)


def test_the_item_layout_is_nested_and_r1s_validator_reserves_the_chunk_key_the_detector_uses(world):
    """R1's declaration text and validator and the detector agree on ONE layout: {"chunk": {chunk row}, <extra arg name>: [...]} (nested, not flat)."""
    d = normaliser(entry_for(world))
    items = cdd.build_inputs(d, mk_chunks()[:2], {"valid_text_ids": ["T1"]})
    assert ac.CORPUS_DERIVED_ITEM_CHUNK_KEY == cdd.ITEM_CHUNK_KEY == "chunk"
    assert all(set(i) == {ac.CORPUS_DERIVED_ITEM_CHUNK_KEY, "valid_text_ids"} and isinstance(i["chunk"], dict) and i["valid_text_ids"] == ["T1"] for i in items)
    assert all("content_en" in i["chunk"] and "content_en" not in i for i in items)                          # a chunk column is never a top-level key of the item
    with pytest.raises(ValueError, match="cannot be named 'chunk'"):                                           # defence in depth: an argument named like the chunk key would overwrite the chunk
        cdd.build_inputs(d, mk_chunks()[:1], {"chunk": ["x"]})
    cd = copy.deepcopy(d)
    cd["parser"]["extra_args"][0]["name"] = "chunk"
    res, _ = run_detect(world, entry=dict(prose_fields=None, corpus_derived=cd))
    assert res["v"] == NO_DET and res["stage"] == "declaration" and "cannot be named 'chunk'" in res["measured"]
    src = (HERE.parent / "asset_census.py").read_text(encoding="utf-8")
    block = src[src.index("CORPUS_DERIVED_INPUT_SHAPES = "):src.index("CORPUS_DERIVED_ARG_KINDS = ")]
    assert '{"chunk": {' in block and "nested" in block and "flat" not in block.replace("not flat", "")        # the declaration text says nested


def test_the_stored_slice_is_read_through_the_declared_filter_and_other_rows_are_not_judged(world):
    st = simulate_writer(world, mk_chunks())
    other = dict(st[0], rule_id="foreign-1", extracted_by="some_other_writer", body="not ours")
    res, db = run_detect(world, stored=st + [other])
    assert res["v"] == PASS and res["block"]["stored_rows"] == 4
    assert all(r.get("filter") == dict(column="extracted_by", equals="fake_v2") for r in db.reqs if r["table"] == "rules" and r["op"] in ("count", "rows"))
    assert all(r.get("filter") is None for r in db.reqs if r["table"] == "chunks" and r["op"] == "count")


def test_the_whole_table_is_read_when_the_scope_is_all(world):
    st = simulate_writer(world, mk_chunks())
    res, db = run_detect(world, entry=entry_for(world, scope=dict(stored="all", uncited_chunks=dict(sample=4))), stored=st + [dict(st[0], rule_id="foreign-1", extracted_by="x")])
    assert res["v"] == FAIL and res["block"]["first_differences"][0]["key"] == {"rule_id": "foreign-1"}


def test_weak_rows_below_the_threshold_are_not_stored_and_a_stored_weak_row_fails(world):
    chunks = mk_chunks()
    st = simulate_writer(world, chunks)
    assert not any(r["body"] == "w" for r in st)
    res, _ = run_detect(world, stored=st)
    assert res["v"] == PASS
    weak = dict(st[0], rule_id="c04#1", body="w")
    res, _ = run_detect(world, stored=st + [weak])
    assert res["v"] == FAIL and res["block"]["first_differences"][0]["kind"] == "extra_stored" and res["block"]["first_differences"][0]["key"] == {"rule_id": "c04#1"}


def test_foreign_key_nulling_is_reproduced_and_an_unnulled_stored_value_differs(world):
    st = simulate_writer(world, mk_chunks())
    assert [r["yoga_canonical_id"] for r in st if r["rule_id"] in ("c02#0", "c04#0")] == ["Y1", None]           # Y9 is not in the reference table
    assert run_detect(world, stored=st)[0]["v"] == PASS
    bad = copy.deepcopy(st)
    [r.update(yoga_canonical_id="Y9") for r in bad if r["rule_id"] == "c04#0"]
    res, _ = run_detect(world, stored=bad)
    assert res["v"] == FAIL and res["block"]["first_differences"][0]["columns"] == ["yoga_canonical_id"]


def test_the_ignored_timestamp_is_not_read_and_the_cite_and_key_columns_always_are(world):
    st = simulate_writer(world, mk_chunks())
    res, db = run_detect(world, stored=st)
    rows_reqs = [r for r in db.reqs if r["op"] == "rows"]
    assert rows_reqs and all("created_at" not in r["columns"] and "extraction_pass_log" in r["columns"] and "rule_id" in r["columns"] for r in rows_reqs)
    st[0]["created_at"] = "1999-01-01"
    assert run_detect(world, stored=st)[0]["v"] == PASS                                                         # an edit of the ignored timestamp is not an edit of the claim


@pytest.mark.parametrize("col,new", [("body", "HAND-EDITED"), ("confidence", 0.95), ("transit_marker", True), ("prediction_jsonb", {"result": "zz", "domain": "d"}), ("text_id", "T9"),
                                     ("verse_ref", "v99"), ("yoga_canonical_id", "Y2")])
def test_hand_edited_stored_row_fails_naming_key_and_column(world, col, new):
    st = simulate_writer(world, mk_chunks())
    st[1][col] = new
    res, _ = run_detect(world, stored=st)
    assert res["v"] == FAIL
    d = res["block"]["first_differences"][0]
    assert d["kind"] == "differs" and d["key"] == {"rule_id": st[1]["rule_id"]} and d["columns"] == [col]
    assert "HAND-EDITED" not in json.dumps(res) and res["block"]["verified"] is False and res["block"]["mismatches"] == 1
    assert ac.corpus_derived_na_problem("Narr.agree", ac._na("x", ac.CORPUS_DERIVED_CAUSE) | {"corpus_derived": res["block"]}) is not None


def test_a_stored_row_whose_cite_points_at_another_chunk_fails(world):
    st = simulate_writer(world, mk_chunks())
    st[0]["extraction_pass_log"] = [{"pattern": "x", "match_text": "RULE:a", "chunk_id": "c02"}]
    res, _ = run_detect(world, stored=st)
    assert res["v"] == FAIL and res["block"]["first_differences"][0]["columns"] == ["extraction_pass_log"] or res["v"] == FAIL


def test_deleted_stored_row_fails(world):
    st = simulate_writer(world, mk_chunks())
    gone = st.pop(1)                                                    # c01#1: chunk c01 is still cited by c01#0, so its rule is missing from the table
    res, _ = run_detect(world, stored=st)
    assert res["v"] == FAIL and res["block"]["first_differences"][0]["kind"] == "missing_stored" and res["block"]["first_differences"][0]["key"] == {"rule_id": gone["rule_id"]}
    st = simulate_writer(world, mk_chunks())
    gone = st.pop(2)                                                    # c02#0 was the ONLY row citing c02: the chunk now looks uncited, and (in the sample) yields a rule
    res, _ = run_detect(world, stored=st)
    assert res["v"] == FAIL and res["block"]["first_differences"][0]["kind"] == "uncited_chunk_yields_rule" and res["block"]["first_differences"][0]["chunk"] == "c02"
    st = simulate_writer(world, mk_chunks())
    st.pop(3)                                                           # c04#0, the only row citing c04
    res, _ = run_detect(world, stored=st, entry=entry_for(world, sample=1))                # BOUNDED SAMPLE: with a sample of 1 (c03) the deleted chunk (c04) is never looked at
    assert res["v"] == PASS and res["block"]["uncited_sampled"] == 1
    assert run_detect(world, stored=st, entry=entry_for(world, sample=100))[0]["v"] == FAIL


def test_extra_stored_row_fails(world):
    st = simulate_writer(world, mk_chunks())
    st.append(dict(st[0], rule_id="c01#99", body="invented"))
    res, _ = run_detect(world, stored=st)
    assert res["v"] == FAIL and res["block"]["first_differences"][0]["kind"] == "extra_stored" and res["block"]["first_differences"][0]["key"] == {"rule_id": "c01#99"}
    st[-1]["extraction_pass_log"] = [{"chunk_id": "c05"}]
    assert run_detect(world, stored=st)[0]["v"] == FAIL


def test_uncited_chunk_that_yields_a_rule_fails_and_a_blank_one_does_not(world):
    chunks = mk_chunks({"c06": "RULE:z"})                    # c06 is in the id-ordered sample of the nine uncited chunks
    res, _ = run_detect(world, chunks=chunks, stored=simulate_writer(world, mk_chunks()))
    assert res["v"] == FAIL and res["block"]["first_differences"][0]["kind"] == "uncited_chunk_yields_rule" and res["block"]["first_differences"][0]["chunk"] == "c06" and res["block"]["uncited_yield"] == 1
    chunks = mk_chunks({"c06": "WEAK:z"})                    # below the threshold: the parser yields it, the writer does not store it: not a yield
    assert run_detect(world, chunks=chunks, stored=simulate_writer(world, mk_chunks()))[0]["v"] == PASS


def test_a_chunk_outside_the_sample_is_not_read_so_the_sample_size_is_the_boundary(world):
    chunks = mk_chunks({"c05": "RULE:z"})                    # c05 is uncited but not in the sample of 4 (c03, c06, c08, c10)
    st = simulate_writer(world, mk_chunks())
    assert run_detect(world, chunks=chunks, stored=st)[0]["v"] == PASS
    res, _ = run_detect(world, entry=entry_for(world, sample=100), chunks=chunks, stored=st)
    assert res["v"] == FAIL and res["block"]["first_differences"][0]["chunk"] == "c05"


def test_a_stored_cite_that_does_not_resolve_is_no_detector_read(world):
    st = simulate_writer(world, mk_chunks())
    st.append(dict(st[0], rule_id="zz#0", extraction_pass_log=[{"chunk_id": "nope"}]))
    res, _ = run_detect(world, stored=st)
    assert res["v"] == NO_DET and res["stage"] == "read" and "do not resolve" in res["measured"]


def test_zero_cited_chunks_or_zero_comparisons_are_never_a_pass(world):
    st = simulate_writer(world, mk_chunks())
    for r in st:
        r["extraction_pass_log"] = []
    res, _ = run_detect(world, stored=st)
    assert res["v"] == NO_DET and res["stage"] == "read" and "zero inputs" in res["measured"]
    # a defensive second line: a comparison that matched nothing cannot be a PASS even if it found no difference
    fake = lambda *a, **k: dict(v=PASS, measured="x", first_differences=[], counts=dict(matched=0, shadowed=0, cited_chunks=1, uncited_chunks_run=0, winners=0, blank_leaves=0), difference_counts={})   # noqa: E731
    orig = cdd.compare_corpus_derived
    cdd.compare_corpus_derived = fake
    try:
        res, _ = run_detect(world)
    finally:
        cdd.compare_corpus_derived = orig
    assert res["v"] == NO_DET and "zero comparisons" in res["measured"] and res["block"]["verified"] is False


def test_the_assurance_label_is_printed_on_a_pass_and_carried_in_the_block_and_the_cells(world, monkeypatch):
    res, _ = run_detect(world)
    assert cdd.ASSURANCE == "software-guarded, reviewed code only" and cdd.ASSURANCE in res["measured"] and res["block"]["assurance"] == cdd.ASSURANCE and res["block"]["assurance_from_runner"] is True
    res, _ = run_detect(world, runner=lambda *a, **k: dict(make_runner(world)(*a, **k), assurance="custom label"))
    assert "[assurance: custom label]" in res["measured"]
    res, _ = run_detect(world, runner=lambda *a, **k: {k2: v for k2, v in make_runner(world)(*a, **k).items() if k2 != "assurance"})
    assert cdd.ASSURANCE in res["measured"] and res["block"]["assurance_from_runner"] is False                    # an older runner: the label is still printed
    got = measure_prose(world, monkeypatch)
    assert all(cdd.ASSURANCE in got[c]["measured"] for c in FIVE)


def test_only_the_reviewed_parser_pair_is_run_the_default_allow_list_refuses_anything_else(world):
    res = cdd.detect_corpus_derived(entry_for(world), fetch=FakeDB([], []), runner=make_runner(world), normaliser=normaliser, repo_root=str(world["root"]))
    assert res["v"] == NO_DET and res["stage"] == "declaration" and "not one this detector may run" in res["measured"]
    for over in (dict(function="other"), dict(file="parser/data.json"), dict(module_root="elsewhere")):
        a = dict(allowed_for(world)[0])
        a.update(over)
        res, _ = run_detect(world, allowed=(a,))
        assert res["stage"] == "declaration" and "not one this detector may run" in res["measured"], over
    a = dict(allowed_for(world)[0], must_pin=("parser/l0_fake.py", "parser/data.json", "parser/adapter.py"))
    res, _ = run_detect(world, allowed=(a,))
    assert res["stage"] == "declaration" and "does not pin" in res["measured"]
    assert run_detect(world, allowed=())[0]["stage"] == "declaration"
    assert cdd.ALLOWED_PARSERS[0]["file"] == cdd.BG_RULES_ADAPTER and cdd.BG_RULES_ADAPTER in cdd.ALLOWED_PARSERS[0]["must_pin"] and "platform/python-sidecar/brahmagyan/l0_semantic_release_v1.json" in cdd.ALLOWED_PARSERS[0]["must_pin"]


def test_the_runner_is_given_exactly_the_committed_pins_never_discovered_ones(world):
    calls = []
    run_detect(world, runner=make_runner(world, calls))
    assert calls[0]["pinned"] == entry_for(world)["corpus_derived"]["parser"]["pinned_files"]


def test_a_stored_row_without_a_cite_fails(world):
    st = simulate_writer(world, mk_chunks())
    st[0]["extraction_pass_log"] = []
    res, _ = run_detect(world, stored=st)
    assert res["v"] == FAIL and "stored_row_cites_no_chunk" in res["block"]["difference_counts"]


def test_cross_chunk_key_collision_first_writer_by_source_order_wins(world):
    chunks = mk_chunks({"c01": "__GLOBAL__ RULE:a", "c02": "__GLOBAL__ RULE:a"})       # the same rule_id g-a from both
    st = simulate_writer(world, chunks)                                                  # the writer visits c01 first (verse_start order): c01 wins
    assert [r["extraction_pass_log"][0]["chunk_id"] for r in st if r["rule_id"] == "g-a"] == ["c01"]
    res, _ = run_detect(world, stored=st, chunks=chunks)
    assert res["v"] == PASS and res["block"]["shadowed"] >= 1, res["measured"]
    chunks2 = mk_chunks({"c01": "__GLOBAL__ RULE:a", "c02": "__GLOBAL__ RULE:a"}, verse_start={"c01": 9})        # now the writer visits c02 first
    st2 = simulate_writer(world, chunks2)
    assert [r["extraction_pass_log"][0]["chunk_id"] for r in st2 if r["rule_id"] == "g-a"] == ["c02"]
    assert run_detect(world, stored=st2, chunks=chunks2)[0]["v"] == PASS
    res, _ = run_detect(world, stored=st, chunks=chunks2)                                 # the table says c01, the source order says c02: first-wins is violated
    assert res["v"] == FAIL


def test_stored_with_no_rows_is_no_detector(world):
    res, _ = run_detect(world, stored=[])
    assert res["v"] == NO_DET and res["stage"] == "read"


# ── caps: a truncated or capped read is NEVER a PASS ──

def test_row_cap_hit_is_no_detector_read(world):
    res, db = run_detect(world, caps=dict(stored_rows=3))
    assert res["v"] == NO_DET and res["stage"] == "read" and "read cap" in res["measured"] and "rows" not in db.calls


def test_byte_cap_hit_is_no_detector_read(world):
    res, _ = run_detect(world, caps=dict(stored_bytes=50))
    assert res["v"] == NO_DET and res["stage"] == "read" and "byte cap" in res["measured"]


def test_chunk_byte_cap_chunk_count_cap_id_cap_and_distinct_cap_are_no_detector(world):
    for caps in (dict(chunk_bytes=10), dict(chunks=2), dict(source_ids=5), dict(distinct=0)):
        res, _ = run_detect(world, caps=caps)
        assert res["v"] == NO_DET and res["stage"] == "read" and "not read" in res["measured"], (caps, res["measured"])


def test_a_truncated_page_stream_is_no_detector(world):
    db = FakeDB(simulate_writer(world, mk_chunks()), mk_chunks())
    db.rows_hook = lambda page, req: page[:1] if req["offset"] == 0 else page
    res, _ = run_detect(world, db=db)
    assert res["v"] == NO_DET and res["stage"] == "read"
    db.rows_hook = lambda page, req: []
    assert run_detect(world, db=db)[0]["v"] == NO_DET


def test_the_row_count_changing_during_the_read_is_no_detector(world):
    db = FakeDB(simulate_writer(world, mk_chunks()), mk_chunks())
    seq = iter([5, 6])
    db.count_hook = lambda t, n: next(seq) if t == "rules" else n
    res, _ = run_detect(world, db=db)
    assert res["v"] == NO_DET and res["stage"] == "read"


def test_a_short_id_list_and_a_lost_chunk_are_no_detector(world):
    db = FakeDB(simulate_writer(world, mk_chunks()), mk_chunks())
    res, _ = run_detect(world, db=lambda r: db(r)[:-1] if r["op"] == "ids" else db(r))
    assert res["v"] == NO_DET and res["stage"] == "read"
    res, _ = run_detect(world, db=lambda r: db(r)[1:] if r["op"] == "chunks" else db(r))
    assert res["v"] == NO_DET and res["stage"] == "read"


@pytest.mark.parametrize("op", ["columns", "count", "rows", "ids", "chunks", "distinct"])
def test_an_unread_statement_is_no_detector_read_never_pass(world, op):
    db = FakeDB(simulate_writer(world, mk_chunks()), mk_chunks())
    db.unread_on = op
    res, _ = run_detect(world, db=db)
    assert res["v"] == NO_DET and res["stage"] == "read" and "statement timeout" in res["measured"]


# ── the runner: every stage ──

@pytest.mark.parametrize("stage", ["pin", "spawn", "run", "output"])
def test_runner_failure_at_each_stage_is_no_detector_naming_the_stage(world, stage):
    res, _ = run_detect(world, runner=make_runner(world, fail=stage))
    assert res["v"] == NO_DET and res["stage"] == stage and f"stage '{stage}'" in res["measured"] and res["block"]["verified"] is False


def test_runner_exception_is_no_detector_spawn(world):
    res, _ = run_detect(world, runner=make_runner(world, fail="raise"))
    assert res["v"] == NO_DET and res["stage"] == "spawn" and "boom" in res["measured"]


def test_runner_failure_with_an_unknown_stage_or_no_answer_is_no_detector_run(world):
    for r in (lambda *a, **k: {"ok": False, "error": "weird", "stage": "???"}, lambda *a, **k: None, lambda *a, **k: {"ok": "yes"}):
        res, _ = run_detect(world, runner=r)
        assert res["v"] == NO_DET and res["stage"] == "run"


def test_loaded_repo_files_must_be_a_subset_of_the_pins_and_include_the_parser_file(world):
    res, _ = run_detect(world, runner=make_runner(world, loaded=["parser/l0_fake.py", "parser/other.py"]))
    assert res["v"] == NO_DET and res["stage"] == "loaded_files" and "other.py" in res["measured"]
    res, _ = run_detect(world, runner=make_runner(world, loaded=["parser/data.json"]))
    assert res["v"] == NO_DET and res["stage"] == "loaded_files" and "parser file" in res["measured"]
    res, _ = run_detect(world, runner=make_runner(world, loaded=[str(world["root"]) + "/parser/l0_fake.py", "./parser/data.json"]))
    assert res["v"] == PASS and res["block"]["loaded_repo_files"] == ["parser/data.json", "parser/l0_fake.py"]
    res, _ = run_detect(world, runner=lambda *a, **k: {"ok": True, "outputs": [], "elapsed_s": 0})
    assert res["v"] == NO_DET and res["stage"] == "loaded_files"


def test_wrong_number_or_shape_of_outputs_is_no_detector_output(world):
    assert run_detect(world, runner=make_runner(world, drop_outputs=True))[0]["stage"] == "output"
    assert run_detect(world, runner=make_runner(world, outputs=[[]] * 8))[0]["stage"] == "output"
    assert run_detect(world, runner=make_runner(world, outputs=["x"] * 7))[0]["stage"] == "output"
    assert run_detect(world, runner=make_runner(world, outputs=[[{"no_key": 1}]] * 7))[0]["stage"] == "output"
    assert run_detect(world, runner=make_runner(world, outputs=[[{"rule_id": "a"}]] * 7))[0]["stage"] == "output"     # keep_when key missing


# ── the pins ──

def test_a_pin_check_problem_is_no_detector_pin_before_anything_is_read_or_run(world):
    calls = []
    res, db = run_detect(world, pin_check=lambda e: "corpus_derived pinned file x changed", runner=make_runner(world, calls))
    assert res["v"] == NO_DET and res["stage"] == "pin" and "changed" in res["measured"] and db.calls == [] and calls == []


def test_a_pinned_file_or_data_file_that_changed_on_disk_is_refused_by_the_detectors_own_rehash(world):
    world["data"].write_text('{"k": 2}', encoding="utf-8")
    calls = []
    res, db = run_detect(world, runner=make_runner(world, calls))
    assert res["v"] == NO_DET and res["stage"] == "pin" and "data.json" in res["measured"] and calls == [] and db.calls == []
    world["data"].write_text('{"k": 1}', encoding="utf-8")
    world["file"].write_text(PARSER_SRC + "\n# edited after the pin\n", encoding="utf-8")
    res, _ = run_detect(world)
    assert res["v"] == NO_DET and res["stage"] == "pin" and "l0_fake.py" in res["measured"]


def test_a_missing_pinned_file_or_one_outside_the_repo_is_no_detector_pin(world):
    world["data"].unlink()
    assert run_detect(world)[0]["stage"] == "pin"
    e = entry_for(world)
    e["corpus_derived"]["parser"]["pinned_files"].append(dict(path="../outside.py", sha256="0" * 64))
    assert run_detect(world, entry=e)[0]["stage"] == "pin"


def test_a_keep_when_constant_that_is_not_a_literal_is_no_detector_pin(world):
    src = PARSER_SRC.replace("QUALITY_THRESHOLD_LIVE = 0.6", "QUALITY_THRESHOLD_LIVE = 0.5 + 0.1")
    world["file"].write_text(src, encoding="utf-8")
    e = entry_for(world)
    e["corpus_derived"]["parser"]["pinned_files"][0]["sha256"] = sha(src)
    res, _ = run_detect(world, entry=e)
    assert res["v"] == NO_DET and res["stage"] == "pin" and "keep_when constant" in res["measured"]


# ── the declaration ──

def test_declaration_problems_are_no_detector_declaration(world):
    cases = [
        entry_for(world, scope=dict(stored="all", uncited_chunks=dict(sample=0))), entry_for(world, scope=dict(stored="all")), entry_for(world, ignore_columns=["rule_id"]),
        entry_for(world, ignore_columns=["extraction_pass_log"]), entry_for(world, key_columns=[]), entry_for(world, key_columns=["nope"]), entry_for(world, table="nope"),
        entry_for(world, cite_column="nope"), entry_for(world, table='t"; DROP'), entry_for(world, scope=dict(stored=dict(column="nope", equals="x"), uncited_chunks=dict(sample=3))),
        entry_for(world, scope=dict(stored=dict(column="extracted_by", equals="a\\b"), uncited_chunks=dict(sample=3))),
        entry_for(world, parser=dict(module_root="parser", file="parser/other.py", function="extract", pinned_files=[dict(path="parser/l0_fake.py", sha256=world["sha"])])),
        entry_for(world, parser=dict(module_root="parser", file="parser/l0_fake.py", function="extract", pinned_files=[])),
        entry_for(world, parser=dict(module_root="parser", file="parser/l0_fake.py", function="extract", pinned_files=[dict(path="parser/l0_fake.py", sha256=world["sha"])], input_shape="weird")),
        entry_for(world, parser=dict(module_root="parser", file="parser/l0_fake.py", function="extract", pinned_files=[dict(path="parser/l0_fake.py", sha256=world["sha"])],
                                     extra_args=[dict(name="v", kind="subquery", table="chunks", column="text_id")])),
    ]
    for e in cases:
        res, _ = run_detect(world, entry=e)
        assert res["v"] == NO_DET and res["stage"] == "declaration", (res["measured"], e["corpus_derived"])


def test_normaliser_refusal_is_no_detector_declaration(world):
    def refuse(e):
        raise ValueError("unknown key")
    res = cdd.detect_corpus_derived(entry_for(world), fetch=FakeDB([], []), runner=make_runner(world), normaliser=refuse, repo_root=str(world["root"]))
    assert res["v"] == NO_DET and res["stage"] == "declaration" and "unknown key" in res["measured"]


# ═════════════════════════════ Part 5: the real fetch (psql monkeypatched) ═════════════════════════════

def _fake_psql(monkeypatch, answers, log):
    def run(cmds, sep, limit, width, quiet=False, label=0, verbose=False, cap=None, via_stdin=False):
        log.append(dict(sql=cmds[0], limit=limit, cap=cap))
        a = answers.pop(0) if answers else "[]"
        if isinstance(a, Exception):
            raise a
        return [[a]]
    monkeypatch.setattr(ac, "_psql_run", run)


def test_real_fetch_builds_capped_timed_chart_agnostic_sliced_reads(monkeypatch):
    log = []
    _fake_psql(monkeypatch, ['["a","b"]', "3002", '[{"rule_id":"r1","confidence":0.8}]', '["c1","c2"]', '[{"id":"c1","content_en":"x"}]', '["bphs","jaimini"]'], log)
    flt = dict(column="extracted_by", equals="python_regex_v2")
    assert ac.corpus_derived_fetch(dict(op="columns", table="sutravali_rules")) == ["a", "b"]
    assert ac.corpus_derived_fetch(dict(op="count", table="sutravali_rules", filter=flt)) == 3002
    rows = ac.corpus_derived_fetch(dict(op="rows", table="sutravali_rules", columns=["rule_id", "confidence"], order_by=["rule_id"], limit=500, offset=0, filter=flt))
    assert rows == [{"rule_id": "r1", "confidence": Decimal("0.8")}]
    assert ac.corpus_derived_fetch(dict(op="ids", table="classical_text_chunks", id_column="id", order_by=["text_id", "chapter", "verse_start"])) == ["c1", "c2"]
    assert ac.corpus_derived_fetch(dict(op="chunks", table="classical_text_chunks", id_column="id", columns=["content_en"], ids=["c1"])) == [{"id": "c1", "content_en": "x"}]
    assert ac.corpus_derived_fetch(dict(op="distinct", table="classical_text_chunks", column="text_id", limit=100)) == ["bphs", "jaimini"]
    assert all(c["cap"] == ac.CORPUS_DERIVED_STATEMENT_CAP and c["limit"] == ac.CORPUS_DERIVED_READ_TIMEOUT_S for c in log)
    assert not any("chart_id" in c["sql"] for c in log)                                              # L0 global tables: no chart predicate
    assert all(c["sql"].lstrip().upper().startswith("SELECT") for c in log)                          # read-only statements
    assert "\"extracted_by\"::text = 'python_regex_v2'" in log[1]["sql"] and "\"extracted_by\"::text = 'python_regex_v2'" in log[2]["sql"]
    assert "ORDER BY x.o0, x.o1, x.o2, x.i" in log[3]["sql"]


def test_real_fetch_applies_the_engine_read_scope_when_the_table_is_scoped(monkeypatch):
    log = []
    _fake_psql(monkeypatch, ["5", "[]"], log)
    ac.set_read_scope({"sutravali_rules": dict(where="chart_id = 'x'", label="chart")})
    try:
        ac.corpus_derived_fetch(dict(op="count", table="sutravali_rules", filter=None))
        ac.corpus_derived_fetch(dict(op="rows", table="sutravali_rules", columns=["a"], order_by=["a"], limit=1, offset=0, filter=None))
        assert all("(chart_id = 'x')" in c["sql"] for c in log)
        ac.set_read_scope({"sutravali_rules": dict(where="chart_id = 'x'", label="chart", block="NO ROWS in scope")})
        with pytest.raises(cdd.Unread, match="NO ROWS"):
            ac.corpus_derived_fetch(dict(op="count", table="sutravali_rules", filter=None))
    finally:
        ac.set_read_scope(None)


@pytest.mark.parametrize("exc,unread", [
    (ac.CheckTimeout("client-side timeout after 120s (psql killed): SELECT"), True),
    (ac.Unknown("ERROR:  canceling statement due to statement timeout"), True),
    (ac.ReadError("psql output exceeds the 33554432-byte cap; not read"), True),
    (ac.Unknown("ERROR:  permission denied for table sutravali_rules"), True),
    (ac.Unknown("psql: could not connect to server"), False),
])
def test_real_fetch_maps_timeouts_caps_and_permission_to_unread_and_lets_other_failures_error(monkeypatch, exc, unread):
    _fake_psql(monkeypatch, [exc], [])
    with pytest.raises(cdd.Unread if unread else ac.Unknown):
        ac.corpus_derived_fetch(dict(op="count", table="t", filter=None))


def test_real_fetch_unparseable_and_unknown_ops(monkeypatch):
    _fake_psql(monkeypatch, ["{not json"], [])
    with pytest.raises(cdd.Unread):
        ac.corpus_derived_fetch(dict(op="ids", table="t", id_column="id"))
    with pytest.raises(ValueError):
        ac.corpus_derived_fetch(dict(op="drop", table="t"))
    with pytest.raises(ValueError):
        ac.corpus_derived_fetch(dict(op="count", table="t", filter=dict(column="c", equals="a\\b")))


def test_detector_over_the_real_fetch_with_a_timed_out_read_is_no_detector(world, monkeypatch):
    monkeypatch.setattr(ac, "_psql_run", lambda *a, **k: (_ for _ in ()).throw(ac.CheckTimeout("client-side timeout after 120s (psql killed): x")))
    res = cdd.detect_corpus_derived(entry_for(world), fetch=ac.corpus_derived_fetch, runner=make_runner(world), normaliser=normaliser, repo_root=str(world["root"]), allowed=allowed_for(world))
    assert res["v"] == NO_DET and res["stage"] == "read"


# ═════════════════════════════ Part 6: the wiring into the cells (R1's mapping) ═════════════════════════════

CAT = dict(exists=set(), cols={}, types=None, defaults=None, udts=None, keys=None)
NARR_LINT_BEFORE = "NO_DETECTOR — prose_fields is undeclared"


def measure_prose(world, monkeypatch, entry=None, runner=None, fetch=None, stored=None, chunks=None, pin_check=None):
    chunks = chunks if chunks is not None else mk_chunks()
    db = fetch or FakeDB(stored if stored is not None else simulate_writer(world, chunks), chunks)
    monkeypatch.setattr(ac, "_cd_default_fetch", lambda: db)
    monkeypatch.setattr(ac, "_cd_default_runner", lambda: runner or make_runner(world))
    monkeypatch.setattr(ac, "_cd_default_normaliser", lambda: normaliser)
    monkeypatch.setattr(ac, "_cd_default_pin_check", lambda: pin_check or (lambda e: None))
    monkeypatch.setattr(ac, "_cd_default_allowed", lambda: allowed_for(world))
    monkeypatch.setattr(ac, "ROOT", world["root"])
    return ac._measure_prose(AID, entry or entry_for(world), dict(target_table="rules"), None, CAT, [], set(), (), set())


def test_pass_maps_five_cells_to_na_with_the_new_cause_and_leaves_narr_lint_alone(world, monkeypatch):
    got = measure_prose(world, monkeypatch)
    assert sorted(got) == sorted(CELLS)
    for c in FIVE:
        assert got[c]["v"] == NA and got[c]["cause"] == ac.CORPUS_DERIVED_CAUSE == "corpus-derived" and ac.CORPUS_DERIVED_NA_TEXT in got[c]["measured"] and "4 stored row" in got[c]["measured"]
        assert ac.corpus_derived_na_problem(c, got[c]) is None and got[c]["corpus_derived"]["verified"] is True
    assert got["Narr.lint"]["v"] == NO_DET and NARR_LINT_BEFORE in got["Narr.lint"]["measured"] and "corpus_derived" not in got["Narr.lint"]
    assert set(ac.CORPUS_DERIVED_CELL_MAP) == set(CELLS) and all(set(m) == {"PASS", "FAIL", "NO_DETECTOR"} for m in ac.CORPUS_DERIVED_CELL_MAP.values())
    assert [c for c, m in ac.CORPUS_DERIVED_CELL_MAP.items() if m["PASS"] == "N/A"] == FIVE


def test_the_release_set_equals_the_criteria_r1s_na_guard_covers(world, monkeypatch):
    assert set(FIVE) == set(ac.CORPUS_DERIVED_NA_CRITERIA) and "Narr.lint" not in ac.CORPUS_DERIVED_NA_CRITERIA


def test_fail_maps_narr_agree_to_fail_naming_key_and_column_and_the_other_five_to_no_detector(world, monkeypatch):
    st = simulate_writer(world, mk_chunks())
    st[0]["body"] = "HAND-EDITED"
    got = measure_prose(world, monkeypatch, stored=st)
    assert got["Narr.agree"]["v"] == FAIL and "differs" in got["Narr.agree"]["measured"] and "body" in got["Narr.agree"]["measured"] and st[0]["rule_id"] in got["Narr.agree"]["measured"]
    assert "HAND-EDITED" not in json.dumps(got)
    assert got["Narr.agree"]["corpus_derived"]["first_differences"][0]["columns"] == ["body"]
    for c in CELLS[1:]:
        assert got[c]["v"] == NO_DET and "unproven" in got[c]["measured"]


def test_fail_names_at_most_three_differences(world, monkeypatch):
    st = simulate_writer(world, mk_chunks())
    for r in st:
        r["body"] = "edited"
    got = measure_prose(world, monkeypatch, stored=st)
    assert got["Narr.agree"]["v"] == FAIL and got["Narr.agree"]["measured"].count("differs key=") == 3


@pytest.mark.parametrize("stage", ["pin", "spawn", "run", "output"])
def test_no_detector_maps_every_cell_to_no_detector_naming_the_stage(world, monkeypatch, stage):
    got = measure_prose(world, monkeypatch, runner=make_runner(world, fail=stage))
    for c in CELLS:
        assert got[c]["v"] == NO_DET and f"stage '{stage}'" in got[c]["measured"]


def test_a_pin_problem_or_a_read_cap_is_no_detector_on_all_six_never_a_partial_pass(world, monkeypatch):
    got = measure_prose(world, monkeypatch, pin_check=lambda e: "corpus_derived pinned file x changed")
    assert all(got[c]["v"] == NO_DET and "stage 'pin'" in got[c]["measured"] for c in CELLS)
    db = FakeDB(simulate_writer(world, mk_chunks()), mk_chunks())
    got = measure_prose(world, monkeypatch, fetch=lambda r: (_ for _ in ()).throw(cdd.Unread("statement timeout")) if r["op"] == "rows" else db(r))
    assert all(got[c]["v"] == NO_DET and "stage 'read'" in got[c]["measured"] for c in CELLS)


def test_the_detector_runs_once_per_asset_per_run_through_the_engine_memo(world, monkeypatch):
    n = []
    inner = make_runner(world)

    def counting(*a, **k):
        n.append(1)
        return inner(*a, **k)
    monkeypatch.setattr(ac, "_MEMO", {})
    measure_prose(world, monkeypatch, runner=counting)
    measure_prose(world, monkeypatch, runner=counting)
    assert len(n) == 1
    monkeypatch.setattr(ac, "_MEMO", None)
    measure_prose(world, monkeypatch, runner=counting)
    measure_prose(world, monkeypatch, runner=counting)
    assert len(n) == 3                                                                        # outside a run nothing is cached


def test_the_memoised_result_is_a_copy(world, monkeypatch):
    monkeypatch.setattr(ac, "_MEMO", {})
    a = measure_prose(world, monkeypatch)
    a["Narr.agree"]["corpus_derived"]["mismatches"] = 99
    assert measure_prose(world, monkeypatch)["Narr.agree"]["corpus_derived"]["mismatches"] == 0


# ═════════════════════════════ Part 7: the rollup guards ═════════════════════════════

@pytest.fixture()
def registered(monkeypatch):
    """What the director's single registry revision will add (R1's data constants; NOT applied in the repo)."""
    causes, rules = dict(ac.NA_CAUSES), dict(ac.NA_RULE_DECISIONS)
    for c, add in ac.CORPUS_DERIVED_NA_CAUSES.items():
        causes[c] = tuple(causes[c]) + tuple(add)
    rules.update(ac.CORPUS_DERIVED_NA_RULE_DECISIONS)
    monkeypatch.setattr(ac, "NA_CAUSES", causes)
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", rules)


def _roll(cells, facts=None):
    r = ac.rollup_asset("L0", dict(cells), facts)
    return r["Narr"], r["Null"]


def test_the_registry_is_untouched_until_the_director_bumps_it():
    assert "corpus-derived" not in sum((list(v) for v in ac.NA_CAUSES.values()), [])
    assert not any("corpus-derived" in k for k in ac.NA_RULE_DECISIONS)


def test_before_registration_the_na_is_never_honoured(world, monkeypatch):
    narr, null = _roll(measure_prose(world, monkeypatch))
    assert narr["v"] == NO_DET and null["v"] == NO_DET and "not a registered cause" in json.dumps(narr)


def test_after_registration_the_five_cells_release_and_narr_lint_keeps_the_gate_open(world, monkeypatch, registered):
    cells = measure_prose(world, monkeypatch)
    narr, null = _roll(cells)
    checks = {c["criterion"]: c for c in narr["checks"]}
    assert all(checks[c]["v"] == NA and checks[c]["rule_id"] == f"{c}#measured:corpus-derived" for c in FIVE[:3]) and checks["Narr.lint"]["v"] == NO_DET and narr["v"] == NO_DET
    assert null["v"] == NA and all(c["v"] == NA and c["rule_id"].endswith("#measured:corpus-derived") for c in null["checks"])         # Null reads N/A, never PASS
    cells["Narr.lint"] = ac._na("lint scan agrees", "lint-not-applicable") | {"lint_none": dict(applied=[], files=["x.py"], why="w", evidence="e")}
    cells["Narr.lint"] = dict(cells["Narr.lint"], v=NO_DET)
    assert _roll(cells)[0]["v"] == NO_DET


def test_without_the_verified_block_nothing_is_released(world, monkeypatch, registered):
    cells = measure_prose(world, monkeypatch)
    bare = {c: {k: v for k, v in r.items() if k != "corpus_derived"} for c, r in cells.items()}
    narr, null = _roll(bare)
    assert narr["v"] == NO_DET and null["v"] == NO_DET and all("no verified block" in c["reason"] for c in null["checks"])


@pytest.mark.parametrize("mutate", [
    lambda b: b.update(verified=False), lambda b: b.update(mismatches=1), lambda b: b.update(matched_rows=b["stored_rows"] - 1), lambda b: b.update(stored_rows=0, matched_rows=0),
    lambda b: b.update(uncited_yield=1), lambda b: b.update(blank_leaves=1), lambda b: b.update(chunks_run=0), lambda b: b["parser"].update(sha256="xyz"),
    lambda b: b.update(loaded_repo_files=["somewhere/else.py"]), lambda b: b.update(loaded_repo_files=[]), lambda b: b.pop("pinned_files"),
])
def test_a_forged_or_incomplete_block_releases_nothing(world, monkeypatch, registered, mutate):
    cells = copy.deepcopy(measure_prose(world, monkeypatch))
    for c in FIVE:
        mutate(cells[c]["corpus_derived"])
    narr, null = _roll(cells)
    assert narr["v"] == NO_DET and null["v"] == NO_DET


def test_a_coupled_narr_na_keeps_its_carr_d1_rule(world, monkeypatch, registered):
    cells = measure_prose(world, monkeypatch)
    facts = {"declared_prose_coupling": {"to": ac.PROSE_COUPLING_TO, "columns": ["body"], "covered": {"body": "effect"}}}
    narr, _ = _roll(cells, facts)
    assert narr["v"] == NO_DET and all("rests on Carr.D1 PASS (coupled)" in c["reason"] for c in narr["checks"] if c["criterion"] in FIVE)
    narr, _ = _roll(cells, {"declared_prose_coupling_missing": True})
    assert narr["v"] == NO_DET


def test_the_gap_ledger_release_rule_follows_the_same_guard(world, monkeypatch, registered):
    cells = measure_prose(world, monkeypatch)
    for c in FIVE:
        assert ac._na_released(c, cells[c]) is True
        assert ac._na_released(c, {k: v for k, v in cells[c].items() if k != "corpus_derived"}) is False
    assert ac._na_released("Narr.lint", cells["Narr.lint"]) is False


# ═════════════════════════════ Part 8: opt-in ═════════════════════════════

def test_an_asset_without_corpus_derived_measures_exactly_as_before(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("the corpus_derived detector must not be reached")
    for n in ("corpus_derived_detect", "_cd_default_fetch", "_cd_default_runner", "_cd_default_normaliser", "_cd_default_pin_check"):
        monkeypatch.setattr(ac, n, boom)
    for decl in ({"prose_fields": None}, {"prose_fields": []}, None, {}):
        got = ac._measure_prose("x", decl, dict(target_table="t"), None, CAT, [], set(), (), set())
        want = ac.prose_checks("x", decl, dict(table="t", own={}, tests=(), vocabulary=set(), counts=None, paths=[], written=None))
        assert {c: got[c]["v"] for c in CELLS} == {c: want[c]["v"] for c in CELLS}


def test_corpus_derived_beside_declared_prose_fields_does_not_override_them(world):
    e = entry_for(world)
    e["prose_fields"] = []
    assert ac.corpus_derived_applies(e) is False and ac.corpus_derived_applies({"prose_fields": None}) is False and ac.corpus_derived_applies(None) is False
    assert ac.corpus_derived_applies(entry_for(world)) is True


def test_the_detector_module_is_python_311_parseable_and_imports_nothing_that_reaches_outside():
    import ast
    src = (HERE.parent / "corpus_derived_detector.py").read_text(encoding="utf-8")
    tree = ast.parse(src, feature_version=(3, 11))
    imported = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)} | {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    assert not (imported & {"asset_census", "subprocess", "os", "socket", "psycopg2", "parser_sandbox", "importlib", "sys", "shutil"}), imported


# ═════════════════════════════ Part 9: the REAL bg_rules parser, R1's validator and R2's sandbox, end to end ═════════════════════════════
# A tmp copy of the real parser files plus the REAL committed ADAPTER (brahmagyan/n431_rules_adapter.py, which applies the writer's quality threshold itself) is pinned with R1's pin_files, normalised
# with R1's normaliser, checked with R1's pin check and run in R2's real child-interpreter sandbox. The declaration therefore carries no keep_when. No database: the data reads are the in-memory fake.
import shutil  # noqa: E402

import parser_sandbox  # noqa: E402

REAL_MODULE_ROOT = "platform/python-sidecar"
REAL_PARSER = "platform/python-sidecar/brahmagyan/l0_rules.py"
REAL_ADAPTER = cdd.BG_RULES_ADAPTER                                  # the path the default allow-list names
REAL_FILES = [REAL_PARSER, "platform/python-sidecar/brahmagyan/__init__.py", "platform/python-sidecar/brahmagyan/graha_vocabulary.py",
              "platform/python-sidecar/brahmagyan/l0_semantic_release.py", "platform/python-sidecar/brahmagyan/l0_semantic_release_v1.json"]
REAL_CHUNKS = [
    ("00000000-0000-4000-8000-000000000001", "bphs", 1, 1, "1.1", "The Sun in the tenth house gives fame and wealth to the native. Saturn in the seventh house bestows delay in marriage."),
    ("00000000-0000-4000-8000-000000000002", "bphs", 1, 2, "1.2", "The king sat in his court and the sage spoke of many things at length without rule."),
    ("00000000-0000-4000-8000-000000000003", "bphs", 2, 1, "2.1", "Jupiter in the fifth house gives sons and good fortune to the native."),
    ("00000000-0000-4000-8000-000000000004", "saravali", 1, 1, "1.1", "Mars in the first house gives courage and vigour to the native."),
    ("00000000-0000-4000-8000-000000000005", "saravali", 1, 2, "1.2", "Venus in the seventh house gives happiness in marriage."),
] + [(f"00000000-0000-4000-8000-0000000001{i:02d}", "bphs", 9, i, f"9.{i}", "Narrative text without any rule at all.") for i in range(1, 21)]


@pytest.fixture()
def real_repo(tmp_path):
    root = tmp_path / "repo"
    for rel in REAL_FILES:
        dst = root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ac.ROOT / rel, dst)
    dst = root / REAL_ADAPTER
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ac.ROOT / REAL_ADAPTER, dst)
    return root


def _real_decl(root, sample=10):
    return dict(
        table="sutravali_rules", key_columns=["rule_id"], cite_column="extraction_pass_log", cite_path=[0, "chunk_id"],
        source=dict(table="classical_text_chunks", id_column="id", text_columns=["content_en"], extra_columns=["text_id", "verse_ref"], order_by=["text_id", "chapter", "verse_start"]),
        parser=dict(module_root=REAL_MODULE_ROOT, file=REAL_ADAPTER, function="run_chunk", pinned_files=ac.pin_files(root, REAL_FILES + [REAL_ADAPTER]), input_shape="chunk_row_dict",
                    extra_args=[dict(name="valid_text_ids", kind="distinct_values", table="classical_text_chunks", column="text_id")]),
        derived=dict(drop_keys=[],
                     null_unless_in=[dict(column="yoga_canonical_id", table="brahma_yoga_catalog", ref_column="canonical_id"),
                                     dict(column="dasha_system_id", table="brahma_dasha_systems", ref_column="canonical_id")],
                     json_columns=["antecedent_jsonb", "predicate_jsonb", "prediction_jsonb", "extraction_pass_log"], numeric_columns=["confidence", "quality_score"], duplicate_policy="first_wins"),
        ignore_columns=["created_at"], scope=dict(stored=dict(column="extracted_by", equals="python_regex_v2"), uncited_chunks=dict(sample=sample)),
        why="every sutravali_rules row of extracted_by python_regex_v2 is the output of the pinned regex parser over the classical_text_chunks row its extraction_pass_log cites (verbatim slices, templated descriptions, uuid5 ids)",
        evidence=REAL_ADAPTER + ":31")


def _real_world(root):
    sys.path.insert(0, str(root / REAL_MODULE_ROOT))
    try:
        from brahmagyan import l0_rules as l0
    finally:
        sys.path.pop(0)
    chunks = [dict(id=i, text_id=t, chapter=c, verse_start=v, verse_ref=r, content_en=x) for i, t, c, v, r, x in REAL_CHUNKS]
    valid = sorted({c["text_id"] for c in chunks})
    stored, seen = [], set()
    for ch in sorted(chunks, key=lambda c: (c["text_id"], c["chapter"], c["verse_start"], c["id"])):       # seed_rules, simulated: quality >= LIVE, FK nulling (empty reference tables), ON CONFLICT DO NOTHING
        for r in l0.extract_rules_from_chunk({k: ch[k] for k in ("id", "text_id", "verse_ref", "content_en")}, set(valid)):
            q = r.pop("_quality")
            if q < l0.QUALITY_THRESHOLD_LIVE or r["rule_id"] in seen:
                continue
            seen.add(r["rule_id"])
            r["yoga_canonical_id"] = r["dasha_system_id"] = None
            for k in ("antecedent_jsonb", "predicate_jsonb", "prediction_jsonb", "extraction_pass_log"):
                r[k] = json.loads(r[k])
            r["created_at"] = "2026-10-01T00:00:00+00:00"
            stored.append(r)
    db = FakeDB(stored, chunks)
    db.tables.update(sutravali_rules=db.tables.pop("rules"), classical_text_chunks=db.tables.pop("chunks"), brahma_yoga_catalog=[], brahma_dasha_systems=[])
    db.cols.update(sutravali_rules=list(stored[0]), classical_text_chunks=db.cols["chunks"], brahma_yoga_catalog=["canonical_id"], brahma_dasha_systems=["canonical_id"])
    return db, stored


def _real_detect(root, db, decl=None):
    return cdd.detect_corpus_derived({"prose_fields": None, "corpus_derived": decl or _real_decl(root)}, fetch=db, runner=parser_sandbox.run_pinned_parser, normaliser=ac.normalise_corpus_derived,
                                     pin_check=lambda e: ac.corpus_derived_pin_problem(e, root), repo_root=str(root))


def test_the_real_declaration_the_real_parser_and_the_real_sandbox_reproduce_a_simulated_seed_rules_table(real_repo):
    db, stored = _real_world(real_repo)
    assert len(stored) >= 4
    assert ac.corpus_derived_problem({"prose_fields": None, "corpus_derived": _real_decl(real_repo)}) is None
    res = _real_detect(real_repo, db)
    assert res["v"] == PASS, res["measured"]
    b = res["block"]
    assert b["stored_rows"] == len(stored) == b["matched_rows"] and b["uncited_sampled"] >= 1 and b["extra_args"] == ["valid_text_ids"] and b["keep_when_threshold"] is None
    assert set(b["loaded_repo_files"]) <= set(b["pinned_files"]) and REAL_ADAPTER in b["loaded_repo_files"] and REAL_FILES[0] in b["loaded_repo_files"] and b["parser"]["function"] == "run_chunk"
    assert ac.corpus_derived_na_problem("Narr.agree", ac._na("x", ac.CORPUS_DERIVED_CAUSE) | {"corpus_derived": b}) is None
    assert b["assurance"] == parser_sandbox.ASSURANCE and b["assurance_from_runner"] is True and f"[assurance: {parser_sandbox.ASSURANCE}]" in res["measured"]       # the label is the REAL sandbox's own


def test_the_detectors_fallback_assurance_label_is_the_sandboxs_label_and_a_failed_real_run_carries_one_too(real_repo):
    assert cdd.ASSURANCE == parser_sandbox.ASSURANCE
    r = parser_sandbox.run_pinned_parser(str(real_repo), REAL_MODULE_ROOT, [], REAL_ADAPTER, "run_chunk", [])
    assert r["ok"] is False and r["assurance"] == parser_sandbox.ASSURANCE


@pytest.mark.parametrize("mutate,kind", [
    (lambda st: st[0].update(confidence=0.5), "differs"),
    (lambda st: st[1]["predicate_jsonb"].update(description="HAND-EDITED description"), "differs"),
    (lambda st: st.pop(0), "missing_stored"),
    (lambda st: st.append(dict(st[0], rule_id="00000000-0000-5000-8000-0000000000aa")), "extra_stored"),
])
def test_the_real_pipeline_sees_every_mutation_of_the_stored_rows(real_repo, mutate, kind):
    db, stored = _real_world(real_repo)
    mutate(db.tables["sutravali_rules"])
    res = _real_detect(real_repo, db)
    assert res["v"] == FAIL and res["block"]["first_differences"][0]["kind"] == kind and "HAND-EDITED" not in json.dumps(res)


def test_the_real_declaration_with_a_missing_pin_is_refused_by_the_allow_list_before_anything_runs(real_repo):
    db, stored = _real_world(real_repo)
    decl = _real_decl(real_repo)
    decl["parser"]["pinned_files"] = [p for p in decl["parser"]["pinned_files"] if not p["path"].endswith("l0_semantic_release_v1.json")]
    res = _real_detect(real_repo, db, decl)
    assert res["v"] == NO_DET and res["stage"] == "declaration" and "l0_semantic_release_v1.json" in res["measured"]


def test_the_real_pipeline_sees_an_uncited_chunk_that_yields(real_repo):
    db, stored = _real_world(real_repo)
    uncited = [c for c in db.tables["classical_text_chunks"] if c["content_en"].startswith("Narrative")][0]
    uncited["content_en"] = "Mars in the tenth house gives power and fame to the native."
    res = _real_detect(real_repo, db, _real_decl(real_repo, sample=1000))
    assert res["v"] == FAIL and res["block"]["uncited_yield"] >= 1


def test_a_changed_real_parser_or_data_file_is_refused_at_the_pin(real_repo):
    db, stored = _real_world(real_repo)
    decl = _real_decl(real_repo)
    (real_repo / REAL_FILES[4]).write_text((real_repo / REAL_FILES[4]).read_text(encoding="utf-8") + " ", encoding="utf-8")
    res = _real_detect(real_repo, db, decl)
    assert res["v"] == NO_DET and res["stage"] == "pin" and "l0_semantic_release_v1.json" in res["measured"]


def test_an_unpinned_helper_the_parser_loads_is_refused_naming_the_files(real_repo):
    db, stored = _real_world(real_repo)
    decl = _real_decl(real_repo)
    decl["parser"]["pinned_files"] = [p for p in decl["parser"]["pinned_files"] if not p["path"].endswith("graha_vocabulary.py")]
    relaxed = (dict(module_root=REAL_MODULE_ROOT, file=REAL_ADAPTER, function="run_chunk", must_pin=(REAL_ADAPTER,)),)       # the allow-list would refuse first; here the SANDBOX is what is tested
    res = cdd.detect_corpus_derived({"prose_fields": None, "corpus_derived": decl}, fetch=db, runner=parser_sandbox.run_pinned_parser, normaliser=ac.normalise_corpus_derived, pin_check=None, repo_root=str(real_repo), allowed=relaxed)
    assert res["v"] == NO_DET and res["stage"] == "run" and "unpinned_import" in res["measured"] and "graha_vocabulary.py" in res["measured"]


# ── the committed ADAPTER (brahmagyan/n431_rules_adapter.run_chunk) ──

def _import_real_module(root, dotted):
    sys.path.insert(0, str(root / REAL_MODULE_ROOT))
    try:
        import importlib
        return importlib.import_module(dotted)
    finally:
        sys.path.pop(0)


def _load_adapter_from(root, name="n431_adapter_under_test"):
    _import_real_module(root, "brahmagyan.l0_rules")                              # the adapter's own import; cached in sys.modules like in _real_world
    spec = importlib.util.spec_from_file_location(name, root / REAL_ADAPTER)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _chunk_dicts():
    return [dict(id=i, text_id=t, chapter=c, verse_start=v, verse_ref=r, content_en=x) for i, t, c, v, r, x in REAL_CHUNKS]


def test_the_adapter_runs_through_the_real_sandbox_on_a_pinned_copy_and_returns_plain_json_rows_without_the_ephemeral_key(real_repo):
    pins = ac.pin_files(real_repo, REAL_FILES + [REAL_ADAPTER])
    chunk = _chunk_dicts()[0]                                                      # "The Sun in the tenth house ... Saturn in the seventh house ..."
    items = [dict(chunk=chunk, valid_text_ids=["bphs", "saravali"]), dict(chunk=_chunk_dicts()[1], valid_text_ids=["bphs", "saravali"]), dict(chunk=dict(chunk, text_id="unknown"), valid_text_ids=["bphs"])]
    r1 = parser_sandbox.run_pinned_parser(str(real_repo), REAL_MODULE_ROOT, pins, REAL_ADAPTER, "run_chunk", items)
    assert r1["ok"] is True, r1
    assert set(r1["loaded_repo_files"]) <= {p["path"] for p in pins} and REAL_ADAPTER in r1["loaded_repo_files"] and REAL_PARSER in r1["loaded_repo_files"]
    rows = r1["outputs"][0]
    assert rows and r1["outputs"][1] == []                                         # a narrative chunk yields nothing
    assert all("_quality" not in x and x["extracted_by"] == "python_regex_v2" and x["confidence"] >= 0.6 and x["confidence"] == x["quality_score"] for x in rows)
    assert all(set(x) == {"rule_id", "text_id", "verse_ref", "antecedent_jsonb", "predicate_jsonb", "prediction_jsonb", "confidence", "extracted_by", "extraction_pass_log", "quality_score",
                          "yoga_canonical_id", "dasha_system_id", "transit_marker"} for x in rows)
    assert all(isinstance(json.loads(x[c]), (list, dict)) for x in rows for c in ("antecedent_jsonb", "predicate_jsonb", "prediction_jsonb", "extraction_pass_log"))
    assert json.loads(rows[0]["extraction_pass_log"])[0]["chunk_id"] == chunk["id"]
    assert r1["outputs"][2] and all(x["confidence"] < 1.0 for x in r1["outputs"][2])        # an unknown text_id scores lower (criterion 5) but, above the threshold, is still kept
    r2 = parser_sandbox.run_pinned_parser(str(real_repo), REAL_MODULE_ROOT, pins, REAL_ADAPTER, "run_chunk", items)
    assert parser_sandbox.canonical_json(r1["outputs"]) == parser_sandbox.canonical_json(r2["outputs"])           # deterministic
    direct = _import_real_module(real_repo, "brahmagyan.l0_rules")
    assert [x["rule_id"] for x in rows] == [x["rule_id"] for x in direct.extract_rules_from_chunk(chunk, {"bphs", "saravali"}) if x["_quality"] >= direct.QUALITY_THRESHOLD_LIVE]


def test_the_adapter_applies_the_writers_quality_threshold_itself_and_passes_the_pinned_arguments(real_repo, monkeypatch):
    ad = _load_adapter_from(real_repo)
    seen = []

    def fake(chunk, valid, *rest, **kw):
        seen.append((chunk, valid, rest, kw))
        for q in (0.59, 0.6, 0.8, 0.4):
            yield dict(rule_id=f"r{q}", _quality=q, confidence=q)

    monkeypatch.setattr(ad, "extract_rules_from_chunk", fake)
    out = ad.run_chunk(dict(chunk=dict(id="i", text_id="t", verse_ref="v", content_en="x", chapter=3, extra="dropped"), valid_text_ids=["t", "u"]))
    assert [r["rule_id"] for r in out] == ["r0.6", "r0.8"] and all("_quality" not in r for r in out)       # at the threshold is kept, below is not
    assert seen == [(dict(id="i", text_id="t", verse_ref="v", content_en="x"), {"t", "u"}, (), {})]            # the four keys seed_rules selects, a SET of valid ids, no counters
    assert ad.QUALITY_THRESHOLD_LIVE == _import_real_module(real_repo, "brahmagyan.l0_rules").QUALITY_THRESHOLD_LIVE == 0.6
    with pytest.raises(KeyError):
        ad.run_chunk(dict(chunk=dict(id="i", text_id="t", verse_ref="v"), valid_text_ids=[]))                  # a chunk without its text is an error, never an empty yield


class _WriterCursor:
    def __init__(self, conn):
        self.c, self.rowcount, self.pending, self.stream = conn, 0, None, []

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        c = self.c
        if "INSERT INTO sutravali_rules" in sql:
            c.inserts.append(params)
            rid = params[0]
            self.rowcount = 0 if rid in c.seen else 1
            c.seen.add(rid)
        elif "information_schema.tables" in sql:
            self.pending = [{"count": 1}]
        elif "SELECT COUNT(*) FROM classical_text_chunks" in sql:
            self.pending = [{"count": len(c.chunks)}]
        elif "SELECT DISTINCT text_id" in sql:
            self.pending = [{"text_id": t} for t in sorted({x["text_id"] for x in c.chunks})]
        elif "brahma_dasha_systems" in sql:
            self.pending = [{"canonical_id": x} for x in c.dasha]
        elif "brahma_yoga_catalog" in sql:
            self.pending = [{"canonical_id": x} for x in c.yoga]
        elif "FROM classical_text_chunks" in sql and "ORDER BY text_id, chapter, verse_start" in sql:
            self.stream = [dict(x) for x in sorted(c.chunks, key=lambda x: (x["text_id"], x["chapter"], x["verse_start"]))]
        elif sql.startswith("DELETE FROM sutravali_rules"):
            pass
        else:
            raise AssertionError(sql)

    def fetchone(self):
        return self.pending[0]

    def fetchall(self):
        return list(self.pending)

    def fetchmany(self, n):
        out, self.stream = self.stream[:n], self.stream[n:]
        return out


class _WriterConn:
    def __init__(self, chunks, yoga=(), dasha=()):
        self.chunks, self.yoga, self.dasha, self.inserts, self.seen = chunks, list(yoga), list(dasha), [], set()

    def cursor(self):
        return _WriterCursor(self)

    def commit(self):
        pass


INSERT_COLUMNS = ["rule_id", "text_id", "verse_ref", "antecedent_jsonb", "predicate_jsonb", "prediction_jsonb", "confidence", "extracted_by", "extraction_pass_log", "quality_score",
                  "yoga_canonical_id", "dasha_system_id", "transit_marker"]


@pytest.mark.parametrize("yoga,dasha", [((), ()), (("gajakesari",), ())])
def test_the_adapter_rows_equal_what_seed_rules_itself_inserts_once_the_censuss_post_processing_is_applied(real_repo, yoga, dasha):
    """The ground truth is the REAL writer: seed_rules is run on a fake connection that records the INSERT parameters; the adapter rows, after the declared first-wins and FK nulling, equal them."""
    l0 = _import_real_module(real_repo, "brahmagyan.l0_rules")
    chunks = _chunk_dicts()
    chunks.append(dict(id="00000000-0000-4000-8000-000000000999", text_id="bphs", chapter=1, verse_start=1, verse_ref="1.1", content_en=REAL_CHUNKS[0][5]))    # same rule text again: a ON CONFLICT DO NOTHING duplicate
    chunks.append(dict(id="00000000-0000-4000-8000-000000000998", text_id="bphs", chapter=3, verse_start=1, verse_ref="3.1",
                       content_en="Jupiter in the fifth house gives sons and good fortune to the native, as in Gajakesari Yoga."))                     # a rule that names a yoga: the FK nulling is exercised
    conn = _WriterConn(chunks, yoga=yoga, dasha=dasha)
    l0.seed_rules(conn)
    kept = {}
    for p in conn.inserts:
        kept.setdefault(p[0], dict(zip(INSERT_COLUMNS, p[:13])))                    # the rows the table ends with: first insert of a rule_id wins
    ad = _load_adapter_from(real_repo)
    valid = sorted({c["text_id"] for c in chunks})
    mine, seen = [], set()
    for ch in sorted(chunks, key=lambda c: (c["text_id"], c["chapter"], c["verse_start"])):
        for r in ad.run_chunk(dict(chunk=ch, valid_text_ids=valid)):
            if r["rule_id"] in seen:
                continue
            seen.add(r["rule_id"])
            for col, ok in (("yoga_canonical_id", yoga), ("dasha_system_id", dasha)):
                if r[col] and r[col] not in ok:
                    r[col] = None                                                   # what derived.null_unless_in does
            mine.append(r)
    assert len(mine) >= 4 and len(conn.inserts) > len(kept)                                   # the duplicate chunk really produced a conflicting insert
    assert [r["rule_id"] for r in mine] == list(kept) and any(r["yoga_canonical_id"] for r in mine) == bool(yoga)
    assert all(r == kept[r["rule_id"]] for r in mine)


def test_the_sandbox_failure_codes_all_read_no_detector_with_the_code_in_the_text(world):
    for code, stage in (("pin_missing", "pin"), ("pin_mismatch", "pin"), ("unpinned_import", "run"), ("spawn_failed", "spawn"), ("timeout", "run"), ("nonzero_exit", "run"), ("bad_output", "output"),
                        ("output_too_large", "output"), ("parser_raised", "run"), ("network_attempt", "run"), ("write_attempt", "run"), ("spawn_attempt", "run")):
        assert code in parser_sandbox.ERROR_CODES
        res, _ = run_detect(world, runner=lambda *a, _c=code, _s=stage, **k: {"ok": False, "error": f"{_c}: index=0 type=ValueError", "stage": _s})
        assert res["v"] == NO_DET and res["stage"] == stage and code in res["measured"], (code, res["measured"])


# ═════════════════════════════ Part 10: REAL SQL smoke (CI shard with PostgreSQL; NOT run locally, SS N-436) ═════════════════════════════

@pytest.fixture()
def pgdb(monkeypatch, disposable_pg):
    import _formgap_support as fs
    point_psql_at(disposable_pg, monkeypatch)
    fs.drop_tables(disposable_pg, "rules", "chunks", "yoga_catalog")
    fs.psql(disposable_pg, "CREATE TABLE chunks (id uuid PRIMARY KEY, text_id text, chapter int, verse_start int, verse_ref text, content_en text)")
    fs.psql(disposable_pg, "CREATE TABLE yoga_catalog (canonical_id text)")
    fs.psql(disposable_pg, "INSERT INTO yoga_catalog VALUES ('Y1'), ('Y2')")
    fs.psql(disposable_pg, "CREATE TABLE rules (rule_id text PRIMARY KEY, text_id text, verse_ref text, body text, prediction_jsonb jsonb, confidence numeric, transit_marker boolean, "
                           "extraction_pass_log jsonb, extracted_by text, yoga_canonical_id text, created_at timestamptz DEFAULT now())")
    yield disposable_pg, fs
    fs.drop_tables(disposable_pg, "rules", "chunks", "yoga_catalog")


def _uuid(i):
    return f"00000000-0000-4000-8000-{i:012d}"


def _load_pg(pg, fs, world):
    chunks = [dict(c, id=_uuid(int(c["id"][1:]))) for c in mk_chunks()]
    for c in chunks:
        fs.psql(pg, f"INSERT INTO chunks VALUES ('{c['id']}', '{c['text_id']}', {c['chapter']}, {c['verse_start']}, '{c['verse_ref']}', '{c['content_en']}')")
    for r in simulate_writer(world, chunks):
        fs.psql(pg, "INSERT INTO rules (rule_id, text_id, verse_ref, body, prediction_jsonb, confidence, transit_marker, extraction_pass_log, extracted_by, yoga_canonical_id) VALUES "
                    f"('{r['rule_id']}', '{r['text_id']}', '{r['verse_ref']}', '{r['body']}', '{json.dumps(r['prediction_jsonb'])}', {r['confidence']}, {str(r['transit_marker']).lower()}, "
                    f"'{json.dumps(r['extraction_pass_log'])}', '{r['extracted_by']}', {'NULL' if r['yoga_canonical_id'] is None else repr(r['yoga_canonical_id'])})")
    fs.psql(pg, "INSERT INTO rules (rule_id, text_id, verse_ref, body, extracted_by, extraction_pass_log) VALUES ('foreign', 'T1', 'v', 'not ours', 'other_writer', '[]')")
    return chunks


def test_REAL_SQL_smoke_the_real_reads_reproduce_a_clean_table_and_see_a_hand_edit(pgdb, world):
    pg, fs = pgdb
    _load_pg(pg, fs, world)
    kw = dict(fetch=ac.corpus_derived_fetch, runner=make_runner(world), normaliser=normaliser, repo_root=str(world["root"]), allowed=allowed_for(world))
    res = cdd.detect_corpus_derived(entry_for(world), **kw)
    assert res["v"] == PASS, res["measured"]
    assert res["block"]["stored_rows"] == 4 and res["block"]["cited_chunks"] == 3
    fs.psql(pg, "UPDATE rules SET body = 'HAND-EDITED' WHERE rule_id LIKE '%#1'")
    res = cdd.detect_corpus_derived(entry_for(world), **kw)
    assert res["v"] == FAIL and res["block"]["first_differences"][0]["columns"] == ["body"] and "HAND-EDITED" not in json.dumps(res)
    fs.psql(pg, "DELETE FROM rules WHERE rule_id LIKE '%#1'")
    assert cdd.detect_corpus_derived(entry_for(world), **kw)["v"] == FAIL


def test_REAL_SQL_smoke_columns_ids_chunks_distinct_and_the_slice(pgdb, world):
    pg, fs = pgdb
    _load_pg(pg, fs, world)
    assert ac.corpus_derived_fetch(dict(op="columns", table="rules"))[:2] == ["rule_id", "text_id"]
    assert ac.corpus_derived_fetch(dict(op="columns", table="nope")) == []
    assert ac.corpus_derived_fetch(dict(op="count", table="chunks", filter=None)) == 12
    assert ac.corpus_derived_fetch(dict(op="count", table="rules", filter=dict(column="extracted_by", equals="fake_v2"))) == 4
    assert ac.corpus_derived_fetch(dict(op="count", table="rules", filter=None)) == 5
    ids = ac.corpus_derived_fetch(dict(op="ids", table="chunks", id_column="id", order_by=["text_id", "chapter", "verse_start"]))
    assert ids == sorted(ids) and len(ids) == 12
    got = ac.corpus_derived_fetch(dict(op="chunks", table="chunks", id_column="id", columns=["content_en"], ids=[_uuid(1), _uuid(99)]))
    assert got == [dict(id=_uuid(1), content_en="RULE:a RULE:b")]
    rows = ac.corpus_derived_fetch(dict(op="rows", table="rules", columns=["rule_id", "confidence", "prediction_jsonb"], order_by=["rule_id"], limit=2, offset=1, filter=dict(column="extracted_by", equals="fake_v2")))
    assert len(rows) == 2 and isinstance(rows[0]["prediction_jsonb"], dict) and rows[0]["confidence"] == Decimal("1.0")
    assert ac.corpus_derived_fetch(dict(op="distinct", table="chunks", column="text_id", limit=10)) == ["T1"]
