"""test_n431_corpus_derived_detector.py: the REPRODUCIBILITY detector of the `corpus_derived` declaration form (SS N-431, bg_rules).

The detector re-runs a committed, sha256-pinned deterministic parser (in R2's sandbox) over the source chunks the stored rows cite and compares its output with the stored rows; a bounded sample
of chunks nobody cites must yield no rule. R1 (the declaration schema, `normalise_corpus_derived`) and R2 (`parser_sandbox.run_pinned_parser`) are NOT merged here, so every test injects small LOCAL
FAKES of the same signatures: an in-memory `fetch` (the detector's data-reading layer), an in-process runner that loads a fake parser module from tmp_path and verifies its sha256 pin, and a
normaliser. Everything is offline and starts no database, EXCEPT the tests named `test_REAL_SQL_*` (a minimal smoke of the real SQL on a disposable PostgreSQL: they are skipped by
`-k "not REAL_SQL"`, which is how the local run goes, SS N-436: they run in the CI shard that has PostgreSQL).

Part 1 value normalisation and citation. Part 2 the pure comparison. Part 3 the SQL builders. Part 4 the detector with fakes: clean, every mutation of the data, every cap, every runner stage.
Part 5 the real fetch (psql monkeypatched). Part 6 the wiring into the six cells (via the engine's own `_measure_prose`). Part 7 the rollup guards. Part 8 opt-in. Part 9 REAL SQL smoke."""
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
import corpus_derived_detector as cdd  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401

PASS, FAIL, NO_DET, NA = "PASS", "FAIL", "NO_DETECTOR", "N/A"
CELLS = list(ac.NARR_CHECKS + ac.NULL_CHECKS)
AID = "bg_rules_fixture"

# ───────────────────────────── the fake parser, pinned by hash ─────────────────────────────
PARSER_SRC = '''
import json


def extract(chunk):
    text = chunk.get("content_en") or ""
    out = []
    for n, w in enumerate(x for x in text.split() if x.startswith("RULE:")):
        rid = "%s#%d" % (chunk["id"], n) if "__GLOBAL__" not in text else "g-" + w
        out.append({
            "rule_id": rid, "text_id": chunk["text_id"], "verse_ref": chunk["verse_ref"], "body": w[5:],
            "prediction_jsonb": json.dumps({"result": w[5:], "domain": "d"}), "confidence": 0.8, "transit_marker": False,
            "extraction_pass_log": json.dumps([{"chunk_id": chunk["id"], "match_text": w}]), "created_by": "fake", "_quality": 1.0,
        })
    return out
'''
TABLE_COLS = ["rule_id", "text_id", "verse_ref", "body", "prediction_jsonb", "confidence", "transit_marker", "extraction_pass_log", "created_by", "created_at"]
CHUNK_TEXT = {"c01": "RULE:a RULE:b", "c02": "RULE:c", "c04": "RULE:d"}      # the cited chunks; c03 and c05..c12 are uncited and empty
CHUNK_IDS = [f"c{i:02d}" for i in range(1, 13)]


def sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def mk_chunks(extra=None):
    txt = dict(CHUNK_TEXT, **(extra or {}))
    return [dict(id=c, text_id="T1", verse_ref=f"v{c}", content_en=txt.get(c, "")) for c in CHUNK_IDS]


def derive(parser_fn, chunks, only):
    out = []
    for ch in chunks:
        if ch["id"] in only:
            out.extend(parser_fn(ch))
    return out


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
    return dict(root=tmp_path, file=f, sha=sha(PARSER_SRC), fn=load_parser(f))


def stored_from(world, chunks=None, cited=("c01", "c02", "c04")):
    """The stored table as the real writer would have left it: the parser output of the cited chunks, as to_jsonb returns it (parsed json columns, created_at present)."""
    rows = []
    for r in derive(world["fn"], chunks or mk_chunks(), set(cited)):
        s = {k: v for k, v in r.items() if k != "_quality"}
        s["prediction_jsonb"] = json.loads(s["prediction_jsonb"])
        s["extraction_pass_log"] = json.loads(s["extraction_pass_log"])
        s["created_at"] = "2026-10-01T00:00:00+00:00"
        rows.append(s)
    return rows


def entry_for(world, sample=4, **over):
    cd = dict(table="rules", key_columns=["rule_id"], cite_column="extraction_pass_log",
              source=dict(table="chunks", id_column="id", text_columns=["content_en"], extra_columns=["text_id", "verse_ref"]),
              parser=dict(module_root="parser", file="parser/l0_fake.py", function="extract", pinned_files=[dict(path="parser/l0_fake.py", sha256=world["sha"])], input_shape="chunk"),
              ignore_columns=["created_at", "_quality"], scope=dict(stored="all", uncited_chunks=dict(sample=sample)), why="w", evidence="e")
    cd.update(over)
    return {"prose_fields": None, "corpus_derived": cd}


class FakeDB:
    """An in-memory `fetch` (the detector's data-reading layer). `rows_hook` lets a test truncate or change what a page returns."""
    def __init__(self, stored, chunks, columns=TABLE_COLS):
        self.tables = {"rules": stored, "chunks": chunks}
        self.cols = {"rules": list(columns), "chunks": ["id", "text_id", "verse_ref", "content_en"]}
        self.calls = []
        self.rows_hook = None
        self.count_hook = None
        self.unread_on = None

    def __call__(self, req):
        self.calls.append(req["op"])
        if self.unread_on == req["op"]:
            raise cdd.Unread(f"statement timeout during {req['op']}")
        t = req["table"]
        if req["op"] == "columns":
            return list(self.cols.get(t, []))
        if req["op"] == "count":
            n = len(self.tables[t])
            return self.count_hook(t, n) if self.count_hook else n
        if req["op"] == "rows":
            rows = sorted(self.tables[t], key=lambda r: tuple(str(r[c]) for c in req["order_by"]))
            page = [{c: r[c] for c in req["columns"] if c in r} for r in rows[req["offset"]:req["offset"] + req["limit"]]]
            return self.rows_hook(page, req) if self.rows_hook else page
        if req["op"] == "ids":
            return sorted(str(r[req["id_column"]]) for r in self.tables[t])
        if req["op"] == "chunks":
            want = set(req["ids"])
            return [{c: r[c] for c in [req["id_column"]] + list(req["columns"])} for r in sorted(self.tables[t], key=lambda r: r["id"]) if r["id"] in want]
        raise AssertionError(req)


def make_runner(world, calls=None, fail=None, loaded=None, drop_outputs=False, outputs=None):
    """The FAKE of parser_sandbox.run_pinned_parser: verifies the sha256 pin, loads the pinned file in-process and runs the function over the inputs."""
    def run(repo_root, module_root, pinned_files, file, function, inputs, *, timeout_s=120, max_output_bytes=64_000_000):
        if calls is not None:
            calls.append(dict(repo_root=repo_root, module_root=module_root, pinned=pinned_files, file=file, function=function, n=len(inputs), timeout_s=timeout_s))
        if fail:
            if fail == "raise":
                raise RuntimeError("boom")
            return {"ok": False, "error": f"{fail}: injected", "stage": fail}
        p = pathlib.Path(repo_root) / file
        if sha(p.read_text(encoding="utf-8")) != {x["path"]: x["sha256"] for x in pinned_files}[file]:
            return {"ok": False, "error": "pin: sha256 mismatch", "stage": "pin"}
        fn = load_parser(p)
        outs = [fn(dict(i)) for i in inputs]
        if drop_outputs:
            outs = outs[:-1]
        return {"ok": True, "outputs": outputs if outputs is not None else outs, "loaded_repo_files": list(loaded if loaded is not None else [file]), "elapsed_s": 0.01}
    return run


def block_normaliser(e):
    """A fake of R1's normaliser that wants the corpus_derived BLOCK; the production adapter tries the entry first and the block on a KeyError."""
    return copy.deepcopy(e)["corpus_derived"] if "corpus_derived" in e else e


def run_detect(world, entry=None, stored=None, chunks=None, db=None, runner=None, normaliser=block_normaliser, **kw):
    chunks = chunks if chunks is not None else mk_chunks()
    db = db or FakeDB(stored if stored is not None else stored_from(world, chunks), chunks)
    runner = runner or make_runner(world)
    return cdd.detect_corpus_derived(entry or entry_for(world), fetch=db, runner=runner, normaliser=normaliser, repo_root=str(world["root"]), **kw), db


# ═════════════════════════════ Part 1: normalisation and citation ═════════════════════════════

@pytest.mark.parametrize("a,b,eq", [
    (None, None, True), (None, "", False), (None, 0, False), ("", [], False),
    (1, 1.0, True), (1, Decimal("1.00"), True), (0.8, Decimal("0.8"), True), (0.8, 0.80000001, False), (Decimal("0.8"), 0.9, False),
    (True, 1, False), (False, 0, False), (True, True, True),
    ([1, 2], (1, 2), True), ([1, 2], [2, 1], False), ([1], [1, 1], False), ([], [], True),
    ({"a": 1, "b": [1.0]}, {"b": [1], "a": 1}, True), ({"a": 1}, {"a": 1, "b": None}, False), ({"a": 1}, {"a": 2}, False),
    ('{"a": 1, "b": [1]}', {"b": [1], "a": 1.0}, True), ('[1, 2]', [1, 2], True), ('[1, 2]', [1, 3], False), ("not json", [1], False), ('{"a": 1}', {"a": 2}, False),
    ("[1]", "[1.0]", False),                                   # two TEXT values are compared as text, never parsed
    ("abc", "ABC", False), ("abc", "abc", True),
    ("A1B2C3D4-0000-4000-8000-000000000001", "a1b2c3d4-0000-4000-8000-000000000001", True),           # canonical UUIDs only
    (float("nan"), float("nan"), True), (float("inf"), 1, False),
])
def test_values_equal_normalisation(a, b, eq):
    assert cdd.values_equal(a, b) is eq
    assert cdd.values_equal(b, a) is eq


@pytest.mark.parametrize("value,ids,bad", [
    ('[{"pattern": "P1", "match_text": "x", "chunk_id": "c01"}]', ["c01"], False),
    ([{"chunk_id": "c01"}, {"chunk_id": "c02"}, {"chunk_id": "c01"}], ["c01", "c02"], False),
    ({"chunk_id": "c07"}, ["c07"], False), ("c09", ["c09"], False), (["c1", "c2"], ["c1", "c2"], False),
    (None, [], False), ("", [], False), ("[]", [], False), ([{"other": "x"}], [], False),
    ([{"chunk_id": "a'b"}], [], True), ([{"chunk_id": "x; DROP"}], [], True), ("a b", [], True),
    ([{"chunk_id": ["c1", "c2"]}], ["c1", "c2"], False), ([{"chunk_id": 5}], ["5"], False), ([{"chunk_id": {"x": 1}}], [], True),
])
def test_cited_ids(value, ids, bad):
    assert cdd.cited_ids(value) == (ids, bad)


def test_cited_ids_honours_the_declared_cite_key():
    assert cdd.cited_ids([{"src": "z1"}], "src") == (["z1"], False)
    assert cdd.cited_ids([{"chunk_id": "z1"}], "src") == ([], False)


# ═════════════════════════════ Part 2: the pure comparison ═════════════════════════════
D = dict(key_columns=["rule_id"], cite_column="extraction_pass_log", ignore_columns=["created_at", "_quality"])


def rowx(rid, chunk, body="x", **kw):
    s = dict(rule_id=rid, body=body, confidence=0.8, extraction_pass_log=[{"chunk_id": chunk}], created_at="t1")
    s.update(kw)
    return s


def drow(rid, chunk, body="x", **kw):
    d = dict(rule_id=rid, body=body, confidence=0.8, extraction_pass_log=json.dumps([{"chunk_id": chunk}]), created_at="t2", _quality=1.0)
    d.update(kw)
    return d


def test_compare_clean_pass_ignores_ignored_columns_and_normalises_json_text():
    r = cdd.compare_corpus_derived([rowx("r1", "c1"), rowx("r2", "c2")], {"c1": [drow("r1", "c1")], "c2": [drow("r2", "c2")], "c3": []}, D)
    assert r["v"] == PASS and r["first_differences"] == [] and r["counts"]["matched"] == 2 and r["counts"]["uncited_chunks_run"] == 1
    assert r["difference_counts"] == {}


def test_compare_hand_edited_value_fails_naming_key_and_column_but_never_the_value():
    secret = "HAND-EDITED-SENTENCE-9137"
    r = cdd.compare_corpus_derived([rowx("r1", "c1", body=secret)], {"c1": [drow("r1", "c1")]}, D)
    assert r["v"] == FAIL
    d = r["first_differences"][0]
    assert d["kind"] == "differs" and d["key"] == {"rule_id": "r1"} and d["columns"] == ["body"] and d["chunk"] == "c1"
    assert secret not in json.dumps(r) and secret not in r["measured"]


def test_compare_names_every_differing_column_and_a_column_present_on_one_side_only():
    r = cdd.compare_corpus_derived([rowx("r1", "c1", body="y", confidence=0.9, stored_only="s")], {"c1": [drow("r1", "c1", derived_only="d")]}, D)
    assert r["v"] == FAIL and r["first_differences"][0]["columns"] == ["body", "confidence", "derived_only", "stored_only"]


def test_compare_deleted_stored_row_is_missing_stored():
    r = cdd.compare_corpus_derived([rowx("r1", "c1")], {"c1": [drow("r1", "c1"), drow("r2", "c1")]}, D)
    assert r["v"] == FAIL and r["difference_counts"] == {"missing_stored": 1} and r["first_differences"][0]["key"] == {"rule_id": "r2"}


def test_compare_extra_stored_row_has_no_derived_counterpart():
    r = cdd.compare_corpus_derived([rowx("r1", "c1"), rowx("r9", "c1")], {"c1": [drow("r1", "c1")]}, D)
    assert r["v"] == FAIL and r["difference_counts"] == {"extra_stored": 1} and r["first_differences"][0]["key"] == {"rule_id": "r9"}


def test_compare_stored_row_citing_a_chunk_that_yields_nothing_or_was_not_run_is_extra():
    assert cdd.compare_corpus_derived([rowx("r1", "c1")], {"c1": []}, D)["difference_counts"] == {"extra_stored": 1}
    assert cdd.compare_corpus_derived([rowx("r1", "c1")], {"c2": []}, D)["difference_counts"] == {"extra_stored": 1}


def test_compare_uncited_chunk_that_yields_a_rule_fails():
    r = cdd.compare_corpus_derived([rowx("r1", "c1")], {"c1": [drow("r1", "c1")], "c7": [drow("r7", "c7")]}, D)
    assert r["v"] == FAIL and r["difference_counts"] == {"uncited_chunk_yields_rule": 1}
    assert r["first_differences"][0]["chunk"] == "c7" and r["first_differences"][0]["key"] == {"rule_id": "r7"}


def test_compare_cited_chunk_absent_from_the_source_fails():
    r = cdd.compare_corpus_derived([rowx("r1", "c1")], {"c1": None}, D)
    assert r["v"] == FAIL and r["difference_counts"] == {"cited_chunk_absent": 1}


def test_compare_stored_row_that_cites_nothing_or_a_malformed_id_fails():
    r = cdd.compare_corpus_derived([rowx("r1", "c1", extraction_pass_log=None)], {"c1": []}, D)
    assert r["v"] == FAIL and r["difference_counts"].get("stored_row_cites_no_chunk") == 1
    r = cdd.compare_corpus_derived([rowx("r1", "x'y")], {}, D)
    assert r["v"] == FAIL and "stored_row_cites_no_chunk" in r["difference_counts"]


def test_compare_duplicate_stored_key_fails():
    r = cdd.compare_corpus_derived([rowx("r1", "c1"), rowx("r1", "c1", body="z")], {"c1": [drow("r1", "c1")]}, D)
    assert r["v"] == FAIL and r["difference_counts"].get("stored_duplicate_key") == 1


def test_compare_cross_chunk_key_collision_is_shadowed_not_a_difference_when_the_stored_row_is_confirmed():
    # the same key derived from c1 and c2; the table keeps the first writer (c1): c2's copy is shadowed
    stored = [rowx("g", "c1")]
    r = cdd.compare_corpus_derived(stored, {"c1": [drow("g", "c1")], "c2": [drow("g", "c2", extraction_pass_log=json.dumps([{"chunk_id": "c2"}]))]}, D)
    assert r["v"] == PASS and r["counts"]["shadowed"] == 1
    # ... but not when the chunk the stored row cites no longer derives it (the row would be an extra, and is reported as one)
    r = cdd.compare_corpus_derived(stored, {"c1": [], "c2": [drow("g", "c2")]}, D)
    assert r["v"] == FAIL and r["difference_counts"] == {"extra_stored": 1}


def test_compare_derived_key_collision_inside_a_chunk_with_different_content_fails():
    r = cdd.compare_corpus_derived([rowx("r1", "c1")], {"c1": [drow("r1", "c1"), drow("r1", "c1", body="other")]}, D)
    assert r["v"] == FAIL and r["difference_counts"].get("derived_key_collision") == 1


def test_compare_composite_key_and_key_alignment_do_not_depend_on_order():
    d2 = dict(D, key_columns=["a", "b"])
    s = [dict(a=1, b="x", extraction_pass_log=[{"chunk_id": "c1"}], v=1), dict(a=1, b="y", extraction_pass_log=[{"chunk_id": "c1"}], v=2)]
    dv = [dict(a=1, b="y", extraction_pass_log=json.dumps([{"chunk_id": "c1"}]), v=2), dict(a=1.0, b="x", extraction_pass_log=json.dumps([{"chunk_id": "c1"}]), v=1)]
    assert cdd.compare_corpus_derived(s, {"c1": dv}, d2)["v"] == PASS


def test_compare_reports_at_most_five_differences_in_a_deterministic_order_with_total_counts():
    stored = [rowx(f"r{i}", "c1", body="edited") for i in range(9)]
    r = cdd.compare_corpus_derived(stored, {"c1": [drow(f"r{i}", "c1") for i in range(9)]}, D)
    assert r["v"] == FAIL and len(r["first_differences"]) == 5 and r["difference_counts"] == {"differs": 9}
    assert [d["key"]["rule_id"] for d in r["first_differences"]] == ["r0", "r1", "r2", "r3", "r4"]
    assert r == cdd.compare_corpus_derived(stored, {"c1": [drow(f"r{i}", "c1") for i in reversed(range(9))]}, D)


def test_compare_no_stored_row_is_vacuous_no_detector_never_pass():
    r = cdd.compare_corpus_derived([], {"c1": []}, D)
    assert r["v"] == NO_DET


@pytest.mark.parametrize("stored,derived", [
    ([{"body": "x"}], {"c1": []}),                                       # a stored row without its key column
    ([rowx("r1", "c1")], {"c1": "not a list"}),
    ([rowx("r1", "c1")], {"c1": [{"body": "x"}]}),                       # a derived row without its key column
    ([rowx("r1", "c1")], {"c1": ["x"]}),
])
def test_compare_malformed_inputs_raise_value_error(stored, derived):
    with pytest.raises(ValueError):
        cdd.compare_corpus_derived(stored, derived, D)


def test_sample_uncited_is_deterministic_ordered_every_kth_and_bounded():
    ids = [f"c{i:02d}" for i in range(1, 13)]
    s, total = cdd.sample_uncited(ids, {"c01", "c02", "c04"}, 4)
    assert total == 9 and s == ["c03", "c06", "c08", "c10"]
    assert cdd.sample_uncited(reversed(ids), {"c01", "c02", "c04"}, 4) == (s, total)
    assert cdd.sample_uncited(ids, set(ids), 4) == ([], 0)
    assert cdd.sample_uncited(ids, set(), 100)[0] == ids and len(cdd.sample_uncited(ids, set(), 3)[0]) == 3


# ═════════════════════════════ Part 3: the SQL builders ═════════════════════════════

def test_sql_builders_are_total_ordered_quoted_and_refuse_injection():
    assert 'ORDER BY "rule_id" LIMIT 500 OFFSET 1000' in cdd.rows_sql("sutravali_rules", ["rule_id", "body"], ["rule_id"], 500, 1000)
    assert 'ORDER BY t."rule_id"' in cdd.rows_sql("sutravali_rules", ["rule_id"], ["rule_id"], 5, 0)
    assert 'WHERE (chart_id = 1)' in cdd.rows_sql("t", ["a"], ["a"], 1, 0, "chart_id = 1")
    s = cdd.chunks_sql("classical_text_chunks", "id", ["content_en", "text_id"], ["u-1", "u-2"])
    assert "IN ('u-1','u-2')" in s and "jsonb_build_object('id', s.\"id\"::text,'content_en', s.\"content_en\",'text_id', s.\"text_id\")" in s
    assert "ORDER BY x.i" in cdd.ids_sql("classical_text_chunks", "id")
    assert "to_regclass('\"t\"')" in cdd.columns_sql("t") and cdd.count_sql("t") == 'SELECT count(*)::text FROM "t"'
    for bad in ('t"; DROP TABLE x;--', "a b", "1x", ""):
        with pytest.raises(ValueError):
            cdd.ident(bad)
    for bad in ("u'; DROP", "a b", "", "x" * 200):
        with pytest.raises(ValueError):
            cdd.chunks_sql("c", "id", [], [bad])


# ═════════════════════════════ Part 4: the detector with fakes ═════════════════════════════

def test_clean_case_passes_with_the_full_block(world):
    calls = []
    res, db = run_detect(world, runner=make_runner(world, calls))
    assert res["v"] == PASS and res["stage"] is None, res["measured"]
    b = res["block"]
    assert b["checked"] and b["verified"] and b["v"] == PASS and b["rows_rederived"] == 4 and b["cited_chunks"] == 3 and b["differences"] == 0 and b["first_differences"] == []
    assert b["uncited_sampled"] == 4 and b["uncited_total"] == 9 and b["table"] == "rules" and b["ignore_columns"] == ["created_at", "_quality"]
    assert b["parser"]["pinned_files"] == [dict(path="parser/l0_fake.py", sha256=world["sha"])] and b["parser"]["function"] == "extract"
    assert ac.corpus_derived_block_problem(b) is None
    assert len(calls) == 1 and calls[0]["n"] == 7 and calls[0]["file"] == "parser/l0_fake.py" and calls[0]["repo_root"] == str(world["root"]) and calls[0]["timeout_s"] == cdd.RUN_TIMEOUT_S
    assert "created_at" not in json.dumps([c for c in db.calls])                                   # (only op names are recorded)


def test_the_ignored_column_is_not_even_read(world):
    seen = []
    db = FakeDB(stored_from(world), mk_chunks())
    orig = db.__call__

    def spy(req):
        if req["op"] == "rows":
            seen.append(list(req["columns"]))
        return orig(req)
    res, _ = run_detect(world, db=spy and db)
    db2 = FakeDB(stored_from(world), mk_chunks())
    cdd.detect_corpus_derived(entry_for(world), fetch=lambda r: (seen.append(list(r["columns"])) if r["op"] == "rows" else None) or db2(r), runner=make_runner(world), normaliser=block_normaliser, repo_root=str(world["root"]))
    assert seen and all("created_at" not in c and "extraction_pass_log" in c and "rule_id" in c for c in seen)


def test_the_cite_column_is_read_and_compared_even_if_it_is_declared_ignored(world):
    e = entry_for(world, ignore_columns=["created_at", "_quality", "extraction_pass_log"])
    seen = []
    db = FakeDB(stored_from(world), mk_chunks())
    res = cdd.detect_corpus_derived(e, fetch=lambda r: (seen.append(list(r["columns"])) if r["op"] == "rows" else None) or db(r), runner=make_runner(world), normaliser=block_normaliser, repo_root=str(world["root"]))
    assert res["v"] == PASS and all("extraction_pass_log" in c for c in seen)


@pytest.mark.parametrize("col,new", [("body", "HAND-EDITED"), ("confidence", 0.95), ("transit_marker", True), ("prediction_jsonb", {"result": "zz", "domain": "d"}), ("text_id", "T9"), ("created_by", "human")])
def test_hand_edited_stored_row_fails_naming_key_and_column(world, col, new):
    st = stored_from(world)
    st[1][col] = new
    res, _ = run_detect(world, stored=st)
    assert res["v"] == FAIL
    d = res["block"]["first_differences"][0]
    assert d["kind"] == "differs" and d["key"] == {"rule_id": st[1]["rule_id"]} and d["columns"] == [col]
    assert "HAND-EDITED" not in json.dumps(res) and res["block"]["verified"] is False
    assert ac.corpus_derived_block_problem(res["block"]) is not None


def test_edit_of_an_ignored_column_is_not_detected_by_design(world):
    st = stored_from(world)
    st[0]["created_at"] = "1999-01-01"
    assert run_detect(world, stored=st)[0]["v"] == PASS


def test_deleted_stored_row_fails(world):
    st = stored_from(world)
    gone = st.pop(2)
    res, _ = run_detect(world, stored=st)
    assert res["v"] == FAIL and res["block"]["first_differences"][0]["kind"] == "missing_stored" and res["block"]["first_differences"][0]["key"] == {"rule_id": gone["rule_id"]}


def test_extra_stored_row_fails(world):
    st = stored_from(world)
    st.append(dict(st[0], rule_id="c01#99", body="invented"))
    res, _ = run_detect(world, stored=st)
    assert res["v"] == FAIL and res["block"]["first_differences"][0]["kind"] == "extra_stored" and res["block"]["first_differences"][0]["key"] == {"rule_id": "c01#99"}


def test_extra_stored_row_citing_an_unrelated_chunk_that_yields_nothing_fails(world):
    st = stored_from(world)
    st.append(dict(st[0], rule_id="c05#0", extraction_pass_log=[{"chunk_id": "c05"}]))
    res, _ = run_detect(world, stored=st)
    assert res["v"] == FAIL and res["block"]["first_differences"][0]["kind"] == "extra_stored"


def test_uncited_chunk_that_yields_a_rule_fails(world):
    chunks = mk_chunks({"c06": "RULE:z"})                    # c06 is in the id-ordered sample of the nine uncited chunks
    db = FakeDB(stored_from(world, mk_chunks()), chunks)
    res, _ = run_detect(world, chunks=chunks, db=db)
    assert res["v"] == FAIL and res["block"]["first_differences"][0]["kind"] == "uncited_chunk_yields_rule" and res["block"]["first_differences"][0]["chunk"] == "c06"


def test_a_chunk_outside_the_sample_is_not_read_so_the_sample_size_is_the_boundary(world):
    chunks = mk_chunks({"c05": "RULE:z"})                    # c05 is uncited but not in the sample of 4 (c03, c06, c08, c10)
    db = FakeDB(stored_from(world, mk_chunks()), chunks)
    assert run_detect(world, chunks=chunks, db=db)[0]["v"] == PASS
    res, _ = run_detect(world, entry=entry_for(world, sample=100), chunks=chunks, db=db)
    assert res["v"] == FAIL and res["block"]["first_differences"][0]["chunk"] == "c05"


def test_stored_row_citing_a_chunk_that_is_not_in_the_source_fails(world):
    st = stored_from(world)
    st.append(dict(st[0], rule_id="zz#0", extraction_pass_log=[{"chunk_id": "nope"}]))
    res, _ = run_detect(world, stored=st)
    assert res["v"] == FAIL and "cited_chunk_absent" in res["block"]["first_differences"][0]["kind"]


def test_cross_chunk_key_collision_first_writer_wins_is_shadowed(world):
    chunks = mk_chunks({"c01": "__GLOBAL__ RULE:a", "c02": "__GLOBAL__ RULE:a"})       # the same rule_id g-RULE:a from both
    st = stored_from(world, chunks, cited=("c01",))                                       # the table kept the first writer (c01) only
    res, _ = run_detect(world, stored=st, chunks=chunks)
    assert res["v"] == FAIL                                                              # c02 is UNCITED here: its rule is stored under c01, hence shadowed...
    # (c02 is cited by nobody: shadowed derivation of a stored key is not a difference, but c02's text also carries no other rule; the verdict must be PASS)
    st2 = stored_from(world, chunks, cited=("c01", "c04"))
    res2, _ = run_detect(world, entry=entry_for(world, sample=100), stored=st2, chunks=chunks)
    assert res2["v"] == PASS and res2["block"]["shadowed"] >= 1, res2["measured"]


def test_stored_with_no_rows_is_no_detector(world):
    res, _ = run_detect(world, stored=[])
    assert res["v"] == NO_DET and res["stage"] == "read"


# ── caps: a truncated or capped read is NEVER a PASS ──

def test_row_cap_hit_is_no_detector_read(world):
    res, db = run_detect(world, caps=dict(stored_rows=3))
    assert res["v"] == NO_DET and res["stage"] == "read" and "read cap" in res["measured"] and "rows" not in db.calls[3:]


def test_byte_cap_hit_is_no_detector_read(world):
    res, _ = run_detect(world, caps=dict(stored_bytes=50))
    assert res["v"] == NO_DET and res["stage"] == "read" and "byte cap" in res["measured"]


def test_chunk_byte_cap_and_chunk_count_cap_and_id_cap_are_no_detector(world):
    for caps in (dict(chunk_bytes=10), dict(chunks=2), dict(source_ids=5)):
        res, _ = run_detect(world, caps=caps)
        assert res["v"] == NO_DET and res["stage"] == "read" and "not read" in res["measured"], (caps, res["measured"])


def test_a_truncated_page_stream_is_no_detector(world):
    db = FakeDB(stored_from(world), mk_chunks())
    db.rows_hook = lambda page, req: page[:1] if req["offset"] == 0 else page          # only 1 of the 4 rows arrives on page one (page size 500: the loop ends after it)
    res, _ = run_detect(world, db=db)
    assert res["v"] == NO_DET and res["stage"] == "read"


def test_an_empty_page_before_the_count_is_reached_is_no_detector(world):
    db = FakeDB(stored_from(world), mk_chunks())
    db.rows_hook = lambda page, req: []
    assert run_detect(world, db=db)[0]["v"] == NO_DET


def test_the_row_count_changing_during_the_read_is_no_detector(world):
    db = FakeDB(stored_from(world), mk_chunks())
    seq = iter([4, 5])
    db.count_hook = lambda t, n: next(seq) if t == "rules" else n
    res, _ = run_detect(world, db=db)
    assert res["v"] == NO_DET and res["stage"] == "read"


def test_a_short_id_list_and_a_lost_chunk_are_no_detector(world):
    db = FakeDB(stored_from(world), mk_chunks())
    orig = db.__call__
    db2 = lambda r: orig(r)[:-1] if r["op"] == "ids" else orig(r)         # noqa: E731
    res, _ = run_detect(world, db=db2)
    assert res["v"] == NO_DET and res["stage"] == "read"
    res, _ = run_detect(world, db=lambda r: orig(r)[1:] if r["op"] == "chunks" else orig(r))
    assert res["v"] == NO_DET and res["stage"] == "read"


@pytest.mark.parametrize("op", ["columns", "count", "rows", "ids", "chunks"])
def test_an_unread_statement_is_no_detector_read_never_pass(world, op):
    db = FakeDB(stored_from(world), mk_chunks())
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


def test_runner_failure_with_an_unknown_stage_is_no_detector_run(world):
    res, _ = run_detect(world, runner=lambda *a, **k: {"ok": False, "error": "weird", "stage": "???"})
    assert res["v"] == NO_DET and res["stage"] == "run"


def test_a_pinned_file_that_changed_on_disk_is_refused_by_the_runner_pin(world):
    world["file"].write_text(PARSER_SRC + "\n# edited after the pin\n", encoding="utf-8")
    res, _ = run_detect(world)
    assert res["v"] == NO_DET and res["stage"] == "pin"


def test_loaded_repo_files_must_be_a_subset_of_the_pinned_files(world):
    res, _ = run_detect(world, runner=make_runner(world, loaded=["parser/l0_fake.py", "parser/other.py"]))
    assert res["v"] == NO_DET and res["stage"] == "loaded_files" and "other.py" in res["measured"]
    res, _ = run_detect(world, runner=make_runner(world, loaded=[]))
    assert res["v"] == PASS                                                              # a subset (even empty) is fine
    res, _ = run_detect(world, runner=make_runner(world, loaded=[str(world["root"]) + "/parser/l0_fake.py", "./parser/l0_fake.py"]))
    assert res["v"] == PASS                                                              # absolute and ./ spellings of a pinned file
    res, _ = run_detect(world, runner=lambda *a, **k: {"ok": True, "outputs": [], "elapsed_s": 0})
    assert res["v"] == NO_DET and res["stage"] == "loaded_files"


def test_wrong_number_or_shape_of_outputs_is_no_detector_output(world):
    assert run_detect(world, runner=make_runner(world, drop_outputs=True))[0]["stage"] == "output"
    assert run_detect(world, runner=make_runner(world, outputs=[[]] * 7 + [[]]))[0]["stage"] == "output"
    assert run_detect(world, runner=make_runner(world, outputs=["x"] * 7))[0]["stage"] == "output"
    assert run_detect(world, runner=make_runner(world, outputs=[[{"no_key": 1}]] * 7))[0]["stage"] == "output"
    assert run_detect(world, runner=lambda *a, **k: None)[0]["stage"] == "run"


def test_the_runner_receives_the_declared_pins_and_a_chunk_dict_per_input(world):
    seen = {}

    def run(repo_root, module_root, pinned_files, file, function, inputs, **kw):
        seen.update(inputs=inputs, pinned=pinned_files, module_root=module_root, kw=kw)
        return make_runner(world)(repo_root, module_root, pinned_files, file, function, inputs, **kw)
    assert run_detect(world, runner=run)[0]["v"] == PASS
    assert seen["module_root"] == "parser" and seen["pinned"] == [dict(path="parser/l0_fake.py", sha256=world["sha"])]
    assert [i["id"] for i in seen["inputs"]] == ["c01", "c02", "c04", "c03", "c06", "c08", "c10"]           # cited (id order), then the uncited sample (id order)
    assert set(seen["inputs"][0]) == {"id", "content_en", "text_id", "verse_ref"}


# ── the declaration ──

def test_declaration_problems_are_no_detector_declaration(world):
    cases = [
        entry_for(world, sample=0), entry_for(world, sample=None), entry_for(world, ignore_columns=["rule_id"]), entry_for(world, key_columns=[]), entry_for(world, key_columns=["nope"]),
        entry_for(world, table="nope"), entry_for(world, cite_column="nope"), entry_for(world, table='t"; DROP'),
        entry_for(world, parser=dict(module_root="parser", file="parser/other.py", function="extract", pinned_files=[dict(path="parser/l0_fake.py", sha256=world["sha"])])),
        entry_for(world, parser=dict(module_root="parser", file="parser/l0_fake.py", function="extract", pinned_files=[], input_shape="chunk")),
        entry_for(world, parser=dict(module_root="parser", file="parser/l0_fake.py", function="extract", pinned_files=[dict(path="parser/l0_fake.py", sha256=world["sha"])], input_shape="weird")),
        entry_for(world, scope=dict(stored="sample", uncited_chunks=dict(sample=3))),
    ]
    for e in cases:
        res, _ = run_detect(world, entry=e)
        assert res["v"] == NO_DET and res["stage"] == "declaration", (res["measured"], e["corpus_derived"])


def test_normaliser_refusal_is_no_detector_declaration(world):
    def refuse(e):
        raise ValueError("unknown key")
    res, _ = run_detect(world, normaliser=refuse)
    assert res["v"] == NO_DET and res["stage"] == "declaration" and "unknown key" in res["measured"]


def test_production_normaliser_adapter_tries_the_entry_then_the_block():
    e = {"corpus_derived": {"k": 1}}
    assert ac.corpus_derived_normalise(e, lambda x: dict(x["corpus_derived"])) == {"k": 1}          # wants the entry
    assert ac.corpus_derived_normalise(e, lambda x: dict(x, seen=1) if "k" in x else (_ for _ in ()).throw(KeyError("k"))) == {"k": 1, "seen": 1}     # wants the block
    with pytest.raises(KeyError):
        ac.corpus_derived_normalise({}, lambda x: x["nope"])


# ═════════════════════════════ Part 5: the real fetch (psql monkeypatched) ═════════════════════════════

def _fake_psql(monkeypatch, answers, log):
    def run(cmds, sep, limit, width, quiet=False, label=0, verbose=False, cap=None, via_stdin=False):
        log.append(dict(sql=cmds[0], limit=limit, cap=cap))
        a = answers.pop(0) if answers else "[]"
        if isinstance(a, Exception):
            raise a
        return [[a]]
    monkeypatch.setattr(ac, "_psql_run", run)


def test_real_fetch_builds_capped_timed_chart_agnostic_reads(monkeypatch):
    log = []
    _fake_psql(monkeypatch, ['["a","b"]', "3002", '[{"rule_id":"r1","confidence":0.8}]', '["c1","c2"]', '[{"id":"c1","content_en":"x"}]'], log)
    assert ac.corpus_derived_fetch(dict(op="columns", table="sutravali_rules")) == ["a", "b"]
    assert ac.corpus_derived_fetch(dict(op="count", table="sutravali_rules")) == 3002
    rows = ac.corpus_derived_fetch(dict(op="rows", table="sutravali_rules", columns=["rule_id", "confidence"], order_by=["rule_id"], limit=500, offset=0))
    assert rows == [{"rule_id": "r1", "confidence": Decimal("0.8")}]
    assert ac.corpus_derived_fetch(dict(op="ids", table="classical_text_chunks", id_column="id")) == ["c1", "c2"]
    assert ac.corpus_derived_fetch(dict(op="chunks", table="classical_text_chunks", id_column="id", columns=["content_en"], ids=["c1"])) == [{"id": "c1", "content_en": "x"}]
    assert all(c["cap"] == ac.CORPUS_DERIVED_STATEMENT_CAP and c["limit"] == ac.CORPUS_DERIVED_READ_TIMEOUT_S for c in log)
    assert not any("chart_id" in c["sql"] for c in log)                                              # L0 global tables: no chart predicate
    assert all(c["sql"].lstrip().upper().startswith("SELECT") for c in log)                          # read-only statements


def test_real_fetch_applies_the_engine_read_scope_when_the_table_is_scoped(monkeypatch):
    log = []
    _fake_psql(monkeypatch, ["5", "[]"], log)
    ac.set_read_scope({"sutravali_rules": dict(where="chart_id = 'x'", label="chart")})
    try:
        ac.corpus_derived_fetch(dict(op="count", table="sutravali_rules"))
        ac.corpus_derived_fetch(dict(op="rows", table="sutravali_rules", columns=["a"], order_by=["a"], limit=1, offset=0))
        assert all("(chart_id = 'x')" in c["sql"] for c in log)
        ac.set_read_scope({"sutravali_rules": dict(where="chart_id = 'x'", label="chart", block="NO ROWS in scope")})
        with pytest.raises(cdd.Unread, match="NO ROWS"):
            ac.corpus_derived_fetch(dict(op="count", table="sutravali_rules"))
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
    if unread:
        with pytest.raises(cdd.Unread):
            ac.corpus_derived_fetch(dict(op="count", table="t"))
    else:
        with pytest.raises(ac.Unknown):
            ac.corpus_derived_fetch(dict(op="count", table="t"))


def test_real_fetch_unparseable_and_unknown_ops(monkeypatch):
    _fake_psql(monkeypatch, ["{not json"], [])
    with pytest.raises(cdd.Unread):
        ac.corpus_derived_fetch(dict(op="ids", table="t", id_column="id"))
    with pytest.raises(ValueError):
        ac.corpus_derived_fetch(dict(op="drop", table="t"))


def test_detector_over_the_real_fetch_with_a_timed_out_read_is_no_detector(world, monkeypatch):
    _fake_psql(monkeypatch, [["a"], ac.CheckTimeout("client-side timeout after 120s")], [])
    monkeypatch.setattr(ac, "_psql_run", lambda *a, **k: (_ for _ in ()).throw(ac.CheckTimeout("client-side timeout after 120s (psql killed): x")))
    res = cdd.detect_corpus_derived(entry_for(world), fetch=ac.corpus_derived_fetch, runner=make_runner(world), normaliser=block_normaliser, repo_root=str(world["root"]))
    assert res["v"] == NO_DET and res["stage"] == "read"


# ═════════════════════════════ Part 6: the wiring into the six cells ═════════════════════════════

CAT = dict(exists=set(), cols={}, types=None, defaults=None, udts=None, keys=None)


def measure_prose(world, monkeypatch, entry=None, runner=None, fetch=None, stored=None, chunks=None):
    chunks = chunks if chunks is not None else mk_chunks()
    db = fetch or FakeDB(stored if stored is not None else stored_from(world, chunks), chunks)
    monkeypatch.setattr(ac, "_cd_default_fetch", lambda: db)
    monkeypatch.setattr(ac, "_cd_default_runner", lambda: runner or make_runner(world))
    monkeypatch.setattr(ac, "_cd_default_normaliser", lambda: block_normaliser)
    monkeypatch.setattr(ac, "ROOT", world["root"])
    return ac._measure_prose(AID, entry or entry_for(world), dict(target_table="rules"), None, CAT, [], set(), (), set())


def test_pass_maps_narr_to_na_with_the_new_cause_and_null_to_pass(world, monkeypatch):
    got = measure_prose(world, monkeypatch)
    assert sorted(got) == sorted(CELLS)
    for c in ac.NARR_CHECKS:
        assert got[c]["v"] == NA and got[c]["cause"] == ac.CORPUS_DERIVED_NA_CAUSE == "corpus-derived-reproduced" and ac.CORPUS_DERIVED_NA_TEXT in got[c]["measured"]
        assert ac.corpus_derived_na_problem(c, got[c]) is None
    for c in ac.NULL_CHECKS:
        assert got[c]["v"] == PASS and "reproducib" in got[c]["measured"] and "4 stored row" in got[c]["measured"] and "3 cited chunk" in got[c]["measured"]
    assert all(got[c]["corpus_derived"]["verified"] is True for c in CELLS)
    assert ac.CORPUS_DERIVED_CELL_MAP.keys() == set(CELLS) and all(set(m) == {"PASS", "FAIL", "NO_DETECTOR"} for m in ac.CORPUS_DERIVED_CELL_MAP.values())


def test_fail_maps_every_cell_to_fail_with_the_first_differences(world, monkeypatch):
    st = stored_from(world)
    st[0]["body"] = "HAND-EDITED"
    got = measure_prose(world, monkeypatch, stored=st)
    for c in CELLS:
        assert got[c]["v"] == FAIL and "differs" in got[c]["measured"] and "body" in got[c]["measured"] and "HAND-EDITED" not in got[c]["measured"]
        assert got[c]["corpus_derived"]["first_differences"][0]["columns"] == ["body"]


@pytest.mark.parametrize("stage", ["pin", "spawn", "run", "output"])
def test_no_detector_maps_every_cell_to_no_detector_naming_the_stage(world, monkeypatch, stage):
    got = measure_prose(world, monkeypatch, runner=make_runner(world, fail=stage))
    for c in CELLS:
        assert got[c]["v"] == NO_DET and f"stage '{stage}'" in got[c]["measured"]


def test_a_read_cap_is_no_detector_on_every_cell_not_a_partial_pass(world, monkeypatch):
    db = FakeDB(stored_from(world), mk_chunks())
    orig = db.__call__
    got = measure_prose(world, monkeypatch, fetch=lambda r: (_ for _ in ()).throw(cdd.Unread("statement timeout")) if r["op"] == "rows" else orig(r))
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
    a["Null.blank_rows"]["corpus_derived"]["differences"] = 99
    assert measure_prose(world, monkeypatch)["Null.blank_rows"]["corpus_derived"]["differences"] == 0


# ═════════════════════════════ Part 7: the rollup guards ═════════════════════════════

@pytest.fixture()
def registered(monkeypatch):
    """What the director's single registry revision will add (NOT applied in the repo): the cause and the four rules."""
    causes = dict(ac.NA_CAUSES)
    rules = dict(ac.NA_RULE_DECISIONS)
    for c in ac.NARR_CHECKS:
        causes[c] = tuple(causes[c]) + ("corpus-derived-reproduced",)
        rules[f"{c}#measured:corpus-derived-reproduced"] = "SS N-431 (test stand-in for the proposed decision text)"
    monkeypatch.setattr(ac, "NA_CAUSES", causes)
    monkeypatch.setattr(ac, "NA_RULE_DECISIONS", rules)


def _cells(world, monkeypatch, **kw):
    return measure_prose(world, monkeypatch, **kw)


def _roll(cells, facts=None):
    r = ac.rollup_asset("L0", dict(cells), facts)
    return r["Narr"], r["Null"]


def test_the_registry_is_untouched_until_the_director_bumps_it():
    assert "corpus-derived-reproduced" not in sum((list(v) for v in ac.NA_CAUSES.values()), [])
    assert not any("corpus-derived" in k for k in ac.NA_RULE_DECISIONS)


def test_before_registration_the_narr_na_is_never_honoured(world, monkeypatch):
    narr, _ = _roll(_cells(world, monkeypatch))
    assert narr["v"] == NO_DET and "not a registered cause" in json.dumps(narr)


def test_after_registration_narr_is_na_and_null_lifts_to_pass(world, monkeypatch, registered):
    narr, null = _roll(_cells(world, monkeypatch))
    assert narr["v"] == NA and all(c["rule_id"] == f"{c['criterion']}#measured:corpus-derived-reproduced" for c in narr["checks"])
    assert null["v"] == PASS and all(c.get("null_corpus_derived_verified") for c in null["checks"])


def test_without_the_verified_block_nothing_is_released_or_lifted(world, monkeypatch, registered):
    cells = _cells(world, monkeypatch)
    bare = {c: {k: v for k, v in r.items() if k != "corpus_derived"} for c, r in cells.items()}
    narr, null = _roll(bare)
    assert narr["v"] == NO_DET and all("verified reproducibility block" in c["reason"] for c in narr["checks"])
    assert null["v"] == PARTIAL if False else null["v"] == "PARTIAL"                          # the Null cap stays: PARTIAL, never PASS


@pytest.mark.parametrize("mutate", [
    lambda b: b.update(verified=False), lambda b: b.update(v=FAIL), lambda b: b.update(differences=1), lambda b: b.update(first_differences=[{"kind": "x"}]),
    lambda b: b.update(rows_rederived=0), lambda b: b.update(cited_chunks=0), lambda b: b.update(uncited_sampled=0), lambda b: b["parser"].update(pinned_files=[]),
    lambda b: b["parser"]["pinned_files"][0].update(sha256="xyz"), lambda b: b.update(table=""), lambda b: b.pop("checked"),
])
def test_a_forged_or_incomplete_block_releases_nothing(world, monkeypatch, registered, mutate):
    cells = copy.deepcopy(_cells(world, monkeypatch))
    for c in CELLS:
        mutate(cells[c]["corpus_derived"])
    narr, null = _roll(cells)
    assert narr["v"] == NO_DET and null["v"] != PASS


def test_the_two_null_records_must_agree_on_table_and_parser(world, monkeypatch, registered):
    cells = copy.deepcopy(_cells(world, monkeypatch))
    cells["Null.blank_rows"]["corpus_derived"]["table"] = "other"
    assert _roll(cells)[1]["v"] != PASS
    cells = copy.deepcopy(_cells(world, monkeypatch))
    cells["Null.blank_rows"]["corpus_derived"]["parser"]["pinned_files"][0]["sha256"] = "0" * 64
    assert _roll(cells)[1]["v"] != PASS


def test_a_basis_or_inconclusive_flag_blocks_the_lift(world, monkeypatch, registered):
    cells = copy.deepcopy(_cells(world, monkeypatch))
    cells["Null.schema_default"]["inconclusive"] = True
    assert _roll(cells)[1]["v"] != PASS
    cells = copy.deepcopy(_cells(world, monkeypatch))
    cells["Null.schema_default"]["basis"] = "declaration"
    assert _roll(cells)[1]["v"] != PASS


def test_a_coupled_narr_na_keeps_its_carr_d1_rule(world, monkeypatch, registered):
    cells = _cells(world, monkeypatch)
    facts = {"declared_prose_coupling": {"to": ac.PROSE_COUPLING_TO, "columns": ["body"], "covered": {"body": "effect"}}}
    narr, _ = _roll(cells, facts)
    assert narr["v"] == NO_DET and all("rests on Carr.D1 PASS (coupled)" in c["reason"] for c in narr["checks"])
    narr, _ = _roll(cells, {"declared_prose_coupling_missing": True})
    assert narr["v"] == NO_DET


def test_the_gap_ledger_release_rule_follows_the_same_guard(world, monkeypatch, registered):
    cells = _cells(world, monkeypatch)
    assert ac._na_released("Narr.agree", cells["Narr.agree"]) is True
    forged = {k: v for k, v in cells["Narr.agree"].items() if k != "corpus_derived"}
    assert ac._na_released("Narr.agree", forged) is False


def test_other_causes_and_criteria_are_untouched_by_the_guards():
    assert ac.corpus_derived_na_problem("Narr.agree", ac._na("x", "no-prose")) is None
    assert ac.corpus_derived_na_problem("Carr.D1", ac._na("x", "corpus-derived-reproduced")) is None
    assert ac.corpus_derived_na_problem("Narr.agree", dict(v=PASS)) is None
    assert ac.corpus_derived_null_earned("Narr.agree", dict(v=PASS), {}) is False


# ═════════════════════════════ Part 8: opt-in ═════════════════════════════

def test_an_asset_without_corpus_derived_measures_exactly_as_before(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("the corpus_derived detector must not be reached")
    for n in ("corpus_derived_detect", "_cd_default_fetch", "_cd_default_runner", "_cd_default_normaliser"):
        monkeypatch.setattr(ac, n, boom)
    for decl in ({"prose_fields": None}, {"prose_fields": []}, None, {}):
        got = ac._measure_prose("x", decl, dict(target_table="t"), None, CAT, [], set(), (), set())
        want = ac.prose_checks("x", decl, dict(table="t", own={}, tests=(), vocabulary=set(), counts=None, paths=[], written=None))
        assert {c: got[c]["v"] for c in CELLS} == {c: want[c]["v"] for c in CELLS}


def test_corpus_derived_beside_declared_prose_fields_does_not_override_them(world, monkeypatch):
    monkeypatch.setattr(ac, "corpus_derived_detect", lambda *a, **k: (_ for _ in ()).throw(AssertionError("must not run")))
    e = entry_for(world)
    e["prose_fields"] = []
    assert ac.corpus_derived_applies(e) is False
    assert ac.corpus_derived_applies({"prose_fields": None}) is False and ac.corpus_derived_applies(None) is False


def test_the_unavailable_collaborators_read_no_detector_not_pass(world, monkeypatch):
    monkeypatch.setattr(ac, "_cd_default_fetch", lambda: FakeDB(stored_from(world), mk_chunks()))
    monkeypatch.setattr(ac, "ROOT", world["root"])
    monkeypatch.delitem(ac.__dict__, "normalise_corpus_derived", raising=False)
    got = ac._measure_prose(AID, entry_for(world), dict(target_table="rules"), None, CAT, [], set(), (), set())
    assert all(got[c]["v"] == NO_DET and "stage 'declaration'" in got[c]["measured"] for c in CELLS)


def test_the_detector_module_is_pure_and_python_311_parseable():
    import ast
    src = (HERE.parent / "corpus_derived_detector.py").read_text(encoding="utf-8")
    tree = ast.parse(src, feature_version=(3, 11))
    imported = {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)} | {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    assert not (imported & {"asset_census", "subprocess", "os", "socket", "psycopg2", "parser_sandbox"}), imported


# ═════════════════════════════ Part 9: REAL SQL smoke (CI shard with PostgreSQL; NOT run locally, SS N-436) ═════════════════════════════

@pytest.fixture()
def pgdb(monkeypatch, disposable_pg):
    import _formgap_support as fs
    point_psql_at(disposable_pg, monkeypatch)
    fs.drop_tables(disposable_pg, "rules", "chunks")
    fs.psql(disposable_pg, "CREATE TABLE chunks (id uuid PRIMARY KEY, text_id text, verse_ref text, content_en text)")
    fs.psql(disposable_pg, "CREATE TABLE rules (rule_id text PRIMARY KEY, text_id text, verse_ref text, body text, prediction_jsonb jsonb, confidence numeric, transit_marker boolean, "
                           "extraction_pass_log jsonb, created_by text, created_at timestamptz DEFAULT now())")
    yield disposable_pg, fs
    fs.drop_tables(disposable_pg, "rules", "chunks")


def _uuid(i):
    return f"00000000-0000-4000-8000-{i:012d}"


def _load_pg(pg, fs, world):
    chunks = [dict(c, id=_uuid(int(c["id"][1:]))) for c in mk_chunks()]
    for c in chunks:
        fs.psql(pg, f"INSERT INTO chunks VALUES ('{c['id']}', '{c['text_id']}', '{c['verse_ref']}', '{c['content_en']}')")
    for r in derive(world["fn"], chunks, {_uuid(1), _uuid(2), _uuid(4)}):
        fs.psql(pg, "INSERT INTO rules (rule_id, text_id, verse_ref, body, prediction_jsonb, confidence, transit_marker, extraction_pass_log, created_by) VALUES "
                    f"('{r['rule_id']}', '{r['text_id']}', '{r['verse_ref']}', '{r['body']}', '{r['prediction_jsonb']}', {r['confidence']}, {str(r['transit_marker']).lower()}, "
                    f"'{r['extraction_pass_log']}', '{r['created_by']}')")
    return chunks


def test_REAL_SQL_smoke_the_real_reads_reproduce_a_clean_table_and_see_a_hand_edit(pgdb, world):
    pg, fs = pgdb
    _load_pg(pg, fs, world)
    kw = dict(fetch=ac.corpus_derived_fetch, runner=make_runner(world), normaliser=block_normaliser, repo_root=str(world["root"]))
    res = cdd.detect_corpus_derived(entry_for(world), **kw)
    assert res["v"] == PASS, res["measured"]
    assert res["block"]["rows_rederived"] == 4 and res["block"]["cited_chunks"] == 3
    fs.psql(pg, "UPDATE rules SET body = 'HAND-EDITED' WHERE rule_id LIKE '%#1'")
    res = cdd.detect_corpus_derived(entry_for(world), **kw)
    assert res["v"] == FAIL and res["block"]["first_differences"][0]["columns"] == ["body"] and "HAND-EDITED" not in json.dumps(res)
    fs.psql(pg, "DELETE FROM rules WHERE rule_id LIKE '%#1'")
    assert cdd.detect_corpus_derived(entry_for(world), **kw)["v"] == FAIL


def test_REAL_SQL_smoke_columns_ids_chunks_and_the_read_only_statements(pgdb, world):
    pg, fs = pgdb
    _load_pg(pg, fs, world)
    assert ac.corpus_derived_fetch(dict(op="columns", table="rules"))[:2] == ["rule_id", "text_id"]
    assert ac.corpus_derived_fetch(dict(op="columns", table="nope")) == []
    assert ac.corpus_derived_fetch(dict(op="count", table="chunks")) == 12
    ids = ac.corpus_derived_fetch(dict(op="ids", table="chunks", id_column="id"))
    assert ids == sorted(ids) and len(ids) == 12
    got = ac.corpus_derived_fetch(dict(op="chunks", table="chunks", id_column="id", columns=["content_en"], ids=[_uuid(1), _uuid(99)]))
    assert got == [dict(id=_uuid(1), content_en="RULE:a RULE:b")]
    rows = ac.corpus_derived_fetch(dict(op="rows", table="rules", columns=["rule_id", "confidence", "prediction_jsonb"], order_by=["rule_id"], limit=2, offset=1))
    assert len(rows) == 2 and isinstance(rows[0]["prediction_jsonb"], dict) and rows[0]["confidence"] == Decimal("0.8")
