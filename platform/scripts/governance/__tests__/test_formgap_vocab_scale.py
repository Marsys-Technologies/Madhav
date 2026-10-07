"""test_formgap_vocab_scale.py: FORM-GAP forms 2 and 3 (SS N-191): the closed-vocabulary cap and the json leaf-pattern cap SCALE with the real count, and a vocabulary may be named by reference to its committed constant.

bg_concordance.topic_canonical_name and classical_text_chunks.topic_tag hold 481 reference_topic_tags values (the old fixed cap was 300); bg_muhurta_lattice.detail holds 26 string-bearing keys (the old
fixed cap was 8 leaf patterns). The bound is stated: values_cap(n) = min(max(ceil(n * 1.25), 300), 5000), leaf_pattern_cap(n) = min(max(ceil(n * 1.25), 8), 64). The declared list size is still validated
(1..5000 distinct strings; 1..64 patterns); the live read is bounded by the same cap (`SELECT DISTINCT ... LIMIT cap + 1`: more is not a closed vocabulary); `values_from` resolves a vocabulary from the committed
literal by AST (no code is run) and the live values must all be inside it.
"""
from __future__ import annotations

import pathlib
import sys
import textwrap

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import _formgap_support as fs  # noqa: E402
import prose_forms as pf  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401
from _formgap_support import NA, FAIL, NO_DET, CELLS  # noqa: E402

TAGS = [f"topic_{i:03d}" for i in range(481)] + ["Career — timing"]
TYPES = {"id": "integer", "topic": "text"}


def _cc(values=None, **kw):
    d = dict(column="topic", why="the topic names are the reference_topic_tags values the writer reads from the table", values=values)
    d.update(kw)
    return {k: v for k, v in d.items() if v is not None}


def _decl(*closed, **kw):
    return {"prose_fields": [], "evidence": {"prose_fields": fs.EV}, "prose_none": dict(why=fs.WHY, closed_columns=list(closed), **kw)}


# ───────────────────────────── the stated bounds ─────────────────────────────

def test_the_two_scaled_caps_and_their_stated_bounds():
    assert (pf.VALUES_BASE_CAP, pf.VALUES_HARD_CAP, pf.VALUES_HEADROOM) == (300, 5000, 1.25)
    assert (pf.LEAF_PATTERNS_BASE_CAP, pf.LEAF_PATTERNS_HARD_CAP, pf.LEAF_PATTERNS_HEADROOM) == (8, 64, 1.25)
    for n, want in ((1, 300), (10, 300), (240, 300), (241, 302), (481, 602), (482, 603), (4000, 5000), (5000, 5000), (9000, 5000)):
        assert pf.values_cap(n) == want, n
    for n, want in ((1, 8), (6, 8), (7, 9), (8, 10), (28, 35), (51, 64), (64, 64), (200, 64)):
        assert pf.leaf_pattern_cap(n) == want, n
    assert pf.values_cap(481) >= 481 and pf.leaf_pattern_cap(28) >= 28                           # the cap always holds what was declared
    assert ac.PROSE_NONE_MAX_VALUES == pf.VALUES_HARD_CAP and ac.PROSE_NONE_MAX_LEAF_PATTERNS == pf.LEAF_PATTERNS_HARD_CAP


# ───────────────────────────── the validator ─────────────────────────────

def test_a_481_value_vocabulary_is_a_sound_declaration_and_the_declared_size_is_still_bounded():
    assert ac.prose_none_problem(_decl(_cc(TAGS))) is None
    assert ac.prose_none_problem(_decl(_cc([f"v{i}" for i in range(pf.VALUES_HARD_CAP)]))) is None
    got = ac.prose_none_problem(_decl(_cc([f"v{i}" for i in range(pf.VALUES_HARD_CAP + 1)])))
    assert got and f"1 to {pf.VALUES_HARD_CAP}" in got
    for bad in ([], ["a", "a"], ["a", "  "], ["a", 3], ["x" * 201], ["a\\b"], ["a\nb"]):
        assert ac.prose_none_problem(_decl(_cc(bad))) is not None, bad


@pytest.mark.parametrize("vf,ok", [
    (dict(file="platform/python-sidecar/brahmagyan/l0_reference.py", constant="_PLANETS9"), True),
    (dict(file="platform/python-sidecar/brahmagyan/l0_reference.py", constant="X", field="name"), True),
    (dict(file="platform/python-sidecar/brahmagyan/l0_reference.py", constant="X", field=2), True),
    (dict(file="platform/scripts/governance/asset_census.py", constant="X"), False),            # only committed sidecar source
    (dict(file="platform/python-sidecar/../x.py", constant="X"), False),
    (dict(file="platform/python-sidecar/x.txt", constant="X"), False),
    (dict(file="platform/python-sidecar/x.py", constant="X y"), False),
    (dict(file="platform/python-sidecar/x.py", constant="X", field=-1), False),
    (dict(file="platform/python-sidecar/x.py", constant="X", field=True), False),
    (dict(file="platform/python-sidecar/x.py"), False),
    (dict(file="platform/python-sidecar/x.py", constant="X", extra=1), False),
    ("platform/python-sidecar/x.py", False),
])
def test_values_from_shape(vf, ok):
    got = ac.prose_none_problem(_decl(_cc(None, values_from=vf)))
    assert (got is None) is ok, got


def test_exactly_one_closing_form_per_column():
    vf = dict(file="platform/python-sidecar/brahmagyan/l0_reference.py", constant="_PLANETS9")
    for extra in (dict(values=["a"]), dict(no_string_leaves=True), dict(json_leaf_patterns=[dict(path="$.a", kind="iso8601_date")])):
        got = ac.prose_none_problem(_decl(dict(_cc(None, values_from=vf), **extra)))
        assert got and "exactly one of" in got, extra


def _jlp(n):
    return dict(column="detail", why="every string leaf of the record sits at one of the declared keys", json_leaf_patterns=[dict(path=f"$.k{i}", values=["x"]) for i in range(n)])


def test_the_leaf_pattern_bound_is_64_declared_paths():
    assert ac.prose_none_problem(_decl(_jlp(28))) is None and ac.prose_none_problem(_decl(_jlp(64))) is None
    got = ac.prose_none_problem(_decl(_jlp(65)))
    assert got and "1 to 64" in got
    d = _decl(dict(_jlp(2), json_leaf_patterns=[dict(path="$.a", values=[f"v{i}" for i in range(301)])]))
    assert "closed vocabulary" in ac.prose_none_problem(d)                                       # ONE path's vocabulary stays small (300)


# ───────────────────────────── the SQL: a big vocabulary is hashed, the small one is byte for byte as before ─────────────────────────────

def test_a_small_vocabulary_keeps_its_sql_byte_for_byte_and_a_big_one_is_a_hashed_membership_test():
    small = ac.prose_none_outside_sql("t", "topic", "text", dict(column="topic", values=["Sun", "Moon"]), None)
    assert small == 'SELECT count(*)::text FROM "t" WHERE "topic" IS NOT NULL AND "topic"::text <> ALL(ARRAY[\'Sun\',\'Moon\']::text[])'
    at = ac.prose_none_outside_sql("t", "topic", "text", dict(column="topic", values=[f"v{i}" for i in range(300)]), None)
    assert "<> ALL(" in at and "NOT (" not in at                                                  # 300 is still the old form
    big = ac.prose_none_outside_sql("t", "topic", "text", dict(column="topic", values=TAGS), None)
    assert 'NOT ("topic"::text = ANY(ARRAY[' in big and "<> ALL(" not in big
    for kind in ("array", "json"):
        sql = ac.prose_none_existence_sql("t", "topic", kind, dict(column="topic", values=TAGS), None)
        assert "NOT (" in sql and "= ANY(ARRAY[" in sql and "<> ALL(" not in sql, kind


def test_the_distinct_read_is_bounded_by_the_scaled_cap():
    sql = ac.distinct_values_sql("t", "topic", pf.values_cap(481), None)
    assert "SELECT DISTINCT" in sql and f"LIMIT {pf.values_cap(481) + 1}) s" in sql and "ORDER BY" not in sql.upper() and "count(" not in sql


# ───────────────────────────── real SQL: the old and the hashed form give the same verdict ─────────────────────────────

@pytest.fixture()
def db(monkeypatch, disposable_pg):
    point_psql_at(disposable_pg, monkeypatch)
    fs.drop_tables(disposable_pg, "formgap_topics")
    fs.psql(disposable_pg, "CREATE TABLE formgap_topics (id serial PRIMARY KEY, chart_id uuid, topic text, topics text[], doc jsonb)")
    yield disposable_pg
    fs.drop_tables(disposable_pg, "formgap_topics")


def _ins(pg, topic, chart=fs.CHART_A, topics="NULL", doc="NULL"):
    t = "NULL" if topic is None else "'" + topic.replace("'", "''") + "'"
    fs.psql(pg, f"INSERT INTO formgap_topics (chart_id, topic, topics, doc) VALUES ('{chart}', {t}, {topics}, {doc})")


@pytest.mark.parametrize("n", [5, 300, 301, 481])
def test_REAL_SQL_the_exact_and_the_existence_verdicts_agree_at_every_size(db, n):
    vals = [f"topic_{i:03d}" for i in range(n)]
    for v in vals[:: max(1, n // 7)] + [None]:
        _ins(db, v)
    entry = dict(column="topic", values=vals)
    assert int(ac.scalar(ac.prose_none_outside_sql("formgap_topics", "topic", "text", entry))) == 0
    assert ac.prose_none_fetch_existence("formgap_topics", "topic", "text", entry)["violating"] is False
    _ins(db, "a stray sentence about the Sun")
    assert int(ac.scalar(ac.prose_none_outside_sql("formgap_topics", "topic", "text", entry))) == 1
    got = ac.prose_none_fetch_existence("formgap_topics", "topic", "text", entry)
    assert got["violating"] is True and got["sample"] == ["a stray sentence about the Sun"]


def test_REAL_SQL_the_hashed_form_covers_array_and_json_columns_with_a_quote_and_a_dash(db):
    vals = [f"t{i}" for i in range(400)] + ["it's", "Career — timing"]
    _ins(db, None, topics="ARRAY['t1','it''s']", doc="'{\"k\":\"Career — timing\",\"n\":3}'::jsonb")
    for kind, col in (("array", "topics"), ("json", "doc")):
        e = dict(column=col, values=vals)
        assert int(ac.scalar(ac.prose_none_outside_sql("formgap_topics", col, kind, e))) == 0, kind
    _ins(db, None, topics="ARRAY['t1','zzz']", doc="'{\"k\":\"zzz\"}'::jsonb")
    for kind, col in (("array", "topics"), ("json", "doc")):
        e = dict(column=col, values=vals)
        assert int(ac.scalar(ac.prose_none_outside_sql("formgap_topics", col, kind, e))) == 1, kind
        assert ac.prose_none_fetch_existence("formgap_topics", col, kind, e)["violating"] is True


def _muhurta_patterns():
    """26 closed string keys and two open timestamp leaves: the shape of bg_muhurta_lattice.detail (28 patterns > the old cap of 8)."""
    pats = [dict(path=f"$.key{i:02d}", values=[f"w{i}a", f"w{i}b"]) for i in range(26)]
    pats += [dict(path="$.anga_true_end_utc", kind="iso8601_timestamp"), dict(path="$.graha_positions_at", kind="iso8601_timestamp")]
    return pats


def test_REAL_SQL_28_leaf_patterns_close_the_record_and_a_stray_leaf_or_a_wrong_timestamp_is_outside(db):
    pats = _muhurta_patterns()
    entry = dict(column="doc", json_leaf_patterns=pats)
    assert ac.prose_none_problem(_decl(dict(entry, why="the record's string leaves are the declared keys"))) is None
    import json
    clean = {"key00": "w0a", "key25": "w25b", "n": 3, "anga_true_end_utc": "2026-10-07T01:15:00+00:00", "graha_positions_at": "2026-10-07T01:15:00+00:00", "nested": {"a": 1}}
    _ins(db, None, doc=f"'{json.dumps(clean)}'::jsonb")
    assert int(ac.scalar(ac.prose_none_outside_sql("formgap_topics", "doc", "json", entry))) == 0
    for mutation in (dict(clean, key03="a sentence about Mars"),                                  # a stray string leaf
                     dict(clean, key00="w0z"),                                                    # a declared key outside its vocabulary
                     dict(clean, anga_true_end_utc="the end of the tithi"),                       # a timestamp key holding prose
                     dict(clean, extra_key="w0a")):                                               # a value of the vocabulary at an undeclared key
        fs.psql(db, "DELETE FROM formgap_topics")
        _ins(db, None, doc=f"'{json.dumps(mutation)}'::jsonb")
        assert int(ac.scalar(ac.prose_none_outside_sql("formgap_topics", "doc", "json", entry))) == 1, mutation
        assert ac.prose_none_fetch_existence("formgap_topics", "doc", "json", entry)["violating"] is True


# ───────────────────────────── values_from (resolved by AST from the committed constant) ─────────────────────────────

@pytest.fixture()
def src(tmp_path, monkeypatch):
    monkeypatch.setattr(ac, "ROOT", tmp_path)
    d = tmp_path / "platform" / "python-sidecar" / "brahmagyan"
    d.mkdir(parents=True)

    def write(body, name="vocab.py"):
        (d / name).write_text(textwrap.dedent(body), encoding="utf-8")
        return f"platform/python-sidecar/brahmagyan/{name}"
    return write


def _spec(rel, const="TAGS", **kw):
    return dict(file=rel, constant=const, **kw)


@pytest.mark.parametrize("body,const,field,want", [
    ('TAGS = ("b", "a", "a")', "TAGS", None, ["a", "b"]),
    ('TAGS = ["x", "y"]', "TAGS", None, ["x", "y"]),
    ('TAGS = {"x", "y"}', "TAGS", None, ["x", "y"]),
    ('TAGS = frozenset({"x", "y"})', "TAGS", None, ["x", "y"]),
    ('TAGS = {"x": 1, "y": 2}', "TAGS", None, ["x", "y"]),                                          # a dict: its keys
    ('TAGS = [{"id": "x", "n": 1}, {"id": "y", "n": 2}]', "TAGS", "id", ["x", "y"]),
    ('TAGS = [("x", 1), ("y", 2)]', "TAGS", 0, ["x", "y"]),
    ('TAGS: list = ["x", "y"]', "TAGS", None, ["x", "y"]),
    ('TAGS = ("a" "b", "c")', "TAGS", None, ["ab", "c"]),                                           # implicit concatenation folds in the parser
    ('TAGS = sorted({"y", "x"})', "TAGS", None, ["x", "y"]),
])
def test_values_from_resolves_a_plain_literal_without_running_code(src, body, const, field, want):
    rel = src(body)
    assert pf.resolve_values_from(ac.ROOT, _spec(rel, const, **({"field": field} if field is not None else {}))) == want


@pytest.mark.parametrize("body,why", [
    ('TAGS = [f"t{i}" for i in range(3)]', "not a plain literal"),
    ('NAME = "x"\nTAGS = [NAME]', "not a plain literal"),
    ('TAGS = ["a"]\nTAGS = ["b"]', "assigned 2 time"),
    ('TAGS = []\nTAGS = [x for x in "ab"]', "assigned 2 time"),
    ('OTHER = ["a"]', "assigned 0 time"),
    ('TAGS = [1, 2]', "not a string"),
    ('TAGS = []', "holds no value"),
    ('TAGS = ["a", " "]', "cannot be a closed-vocabulary value"),
    ('TAGS = ["a\\\\b"]', "cannot be a closed-vocabulary value"),
    ('TAGS = "a string"', "is a str"),
    ('TAGS = (open("x"))', "not a plain literal"),
    ('TAGS = syntax error here', "cannot be parsed"),
])
def test_values_from_refuses_what_it_cannot_read_exactly(src, body, why):
    rel = src(body)
    with pytest.raises(ValueError, match=why):
        pf.resolve_values_from(ac.ROOT, _spec(rel))


def test_values_from_refuses_a_missing_file_and_a_path_outside_the_repo(src, tmp_path):
    with pytest.raises(ValueError, match="does not exist"):
        pf.resolve_values_from(ac.ROOT, _spec("platform/python-sidecar/brahmagyan/none.py"))
    outside = tmp_path.parent / "elsewhere"
    outside.mkdir(exist_ok=True)
    (outside / "v.py").write_text('TAGS = ["a"]')
    link = tmp_path / "platform" / "python-sidecar" / "link.py"
    link.symlink_to(outside / "v.py")
    with pytest.raises(ValueError, match="outside the repository"):
        pf.resolve_values_from(ac.ROOT, _spec("platform/python-sidecar/link.py"))


def test_values_from_refuses_more_than_the_hard_cap(src):
    rel = src("TAGS = [" + ",".join(repr(f"v{i}") for i in range(pf.VALUES_HARD_CAP + 1)) + "]")
    with pytest.raises(ValueError, match="the bound is 5000"):
        pf.resolve_values_from(ac.ROOT, _spec(rel))


def test_the_resolved_set_stands_in_for_the_values_in_the_measure_glue_and_an_unresolvable_one_is_left_out(src):
    ok = src('TAGS = ["x", "y"]', "ok.py")
    bad = src('TAGS = [f"t{i}" for i in range(2)]', "bad.py")
    pn = dict(why=fs.WHY, closed_columns=[dict(column="a", why="r" * 20, values_from=_spec(ok)), dict(column="b", why="r" * 20, values_from=_spec(bad)), dict(column="c", why="r" * 20, values=["z"])])
    eff, errors, info = ac.formgap_resolve_values_from(pn)
    assert [c["column"] for c in eff["closed_columns"]] == ["a", "c"] and eff["closed_columns"][0]["values"] == ["x", "y"]
    assert list(errors) == [(None, "b")] and "not a plain literal" in errors[(None, "b")] and info[(None, "a")]["count"] == 2


# ───────────────────────────── the detector: end to end on a disposable database ─────────────────────────────

AID = "x_vocab_asset"


def _measure(pg, monkeypatch, decl, scope=None):
    # a real writer file gives the scope its units; what it WRITES is stood in below (the closure is about the table of this test)
    point_psql_at(pg, monkeypatch)
    monkeypatch.setattr(ac, "written_columns", lambda units, tables: {"formgap_topics": {"topic", "topics", "doc"}})        # what the scan of a writer of this table would find
    cat = ac.catalog(["formgap_topics"])
    vocab = ac.prose_vocabulary({AID: decl}, {AID: {"formgap_topics"}})
    ac.set_read_scope(scope or {})
    try:
        return ac._measure_prose(AID, decl, dict(target_table="formgap_topics"), ["ga_transit_anchors.py"], cat, [], {}, (), vocab)
    finally:
        ac.set_read_scope(None)


def _vocab_decl(values=None, **kw):
    cols = [dict(column="topic", why="the topic names are the reference_topic_tags values", **({"values": values} if values is not None else kw)),
            dict(column="topics", why="the topic list holds only reference_topic_tags values", values=values or ["a"]),
            dict(column="doc", why="the record holds no string leaf", no_string_leaves=True)]
    return {"prose_fields": [], "evidence": {"prose_fields": fs.EV}, "prose_none": dict(why=fs.WHY, closed_columns=cols)}


def test_REAL_SQL_a_481_value_vocabulary_reads_na_with_the_scaled_read_in_the_block(db, monkeypatch):
    for v in TAGS[::40]:
        _ins(db, v)
    got = _measure(db, monkeypatch, (_vocab_decl(TAGS)))
    fs.all_na(got)
    sc = got["Narr.agree"]["prose_none"]["forms"]["scaled_vocabulary"]
    assert sc == [dict(table="formgap_topics", column="topic", verified=True, distinct=len(TAGS[::40]), cap=pf.values_cap(len(TAGS)), declared=len(TAGS))]
    assert "scaled_vocabulary" in got["Narr.agree"]["measured"]


def test_REAL_SQL_MUTATION_a_value_outside_the_big_vocabulary_is_a_FAIL_named(db, monkeypatch):
    _ins(db, TAGS[0])
    _ins(db, "an unlisted free sentence")
    got = _measure(db, monkeypatch, (_vocab_decl(TAGS)))
    assert got["Narr.agree"]["v"] == FAIL and "formgap_topics.topic" in got["Narr.agree"]["measured"]


def test_REAL_SQL_MUTATION_more_distinct_values_than_the_cap_is_not_a_closed_vocabulary(db, monkeypatch, tmp_path):
    """The declared vocabulary is 5 values (cap 300); the table holds 301 distinct values: the row-level read already fails, and the DISTINCT read names the cap."""
    vals = [f"v{i}" for i in range(5)]
    for i in range(301):
        _ins(db, f"extra_{i}")
    got = _measure(db, monkeypatch, (_vocab_decl(vals)))
    assert got["Narr.agree"]["v"] == FAIL and "row(s) hold text outside the declared closed vocabulary" in got["Narr.agree"]["measured"]
    # the pure grader, for a vocabulary big enough to take the DISTINCT path
    g = ac.grade_distinct(TAGS, dict(values=[f"x{i}" for i in range(pf.values_cap(len(TAGS)) + 1)], cap=pf.values_cap(len(TAGS)), declared=len(TAGS)))
    assert g["state"] == "wrong" and f"more than {pf.values_cap(len(TAGS))} distinct values" in g["text"] and "not a closed vocabulary" in g["text"]
    g = ac.grade_distinct(TAGS, dict(values=["zzz"], cap=602, declared=482))
    assert g["state"] == "wrong" and "outside the declared vocabulary" in g["text"]
    assert ac.grade_distinct(TAGS, dict(unread="timeout"))["state"] == "skipped" and ac.grade_distinct(TAGS, None)["state"] == "skipped"


def test_REAL_SQL_values_from_a_committed_constant_closes_the_live_values_and_a_value_it_misses_is_a_FAIL(db, monkeypatch, src):
    rel = src("TAGS = (" + ",".join(repr(t) for t in TAGS) + ")")
    _ins(db, TAGS[3])
    _ins(db, TAGS[200])
    d = (_vocab_decl(None, values_from=_spec(rel)))
    d["prose_none"]["closed_columns"][1] = dict(column="topics", why="the topic list holds only reference_topic_tags values", values_from=_spec(rel))
    got = _measure(db, monkeypatch, d)
    fs.all_na(got)
    vf = got["Narr.agree"]["prose_none"]["forms"]["values_from"]
    assert {(x["column"], x["constant"], x["count"]) for x in vf} == {("topic", "TAGS", len(TAGS)), ("topics", "TAGS", len(TAGS))}
    # MUTATION 1: the committed constant loses a value a live row holds => FAIL (the live value is outside the resolved set)
    src("TAGS = (" + ",".join(repr(t) for t in TAGS if t != TAGS[200]) + ")")
    got = _measure(db, monkeypatch, d)
    assert got["Narr.agree"]["v"] == FAIL and "formgap_topics.topic" in got["Narr.agree"]["measured"]
    # MUTATION 2: the constant stops being a plain literal => NO_DETECTOR, never PASS (the vocabulary cannot be resolved)
    src("TAGS = [t for t in 'ab']")
    got = _measure(db, monkeypatch, d)
    assert all(got[c]["v"] == NO_DET for c in CELLS) and "values_from" in got["Narr.agree"]["measured"] and "not a plain literal" in got["Narr.agree"]["measured"]


def test_REAL_SQL_two_charts_the_distinct_read_and_the_closure_judge_the_measured_chart_only(db, monkeypatch):
    _ins(db, TAGS[1], chart=fs.CHART_A)
    _ins(db, "another chart's stray sentence", chart=fs.CHART_B)
    scope_a = {"formgap_topics": dict(where=f"chart_id = '{fs.CHART_A}'", label="the measured chart")}
    scope_b = {"formgap_topics": dict(where=f"chart_id = '{fs.CHART_B}'", label="the other chart")}
    assert _measure(db, monkeypatch, (_vocab_decl(TAGS)), scope=scope_a)["Narr.agree"]["v"] == NA
    assert _measure(db, monkeypatch, (_vocab_decl(TAGS)), scope=scope_b)["Narr.agree"]["v"] == FAIL


TIMEOUT = "ERROR:  canceling statement due to statement timeout"


def test_a_distinct_read_that_times_out_is_not_a_verdict_and_the_row_closure_still_decides(monkeypatch):
    """The DISTINCT read of a scaled vocabulary is supplementary: a timeout there leaves the closure verdict to the row-level read (an exact count or its existence twin), which itself never reads PASS on a timeout."""
    def scalar(q):
        if "SELECT DISTINCT" in q:
            raise ac.Unknown(TIMEOUT)
        return "0"
    monkeypatch.setattr(ac, "scalar", scalar)
    out = ac.formgap_reads("x", (_vocab_decl(TAGS)), {"t": (["topic"], {"topic": "text"}, None)}, "t", udts={})
    assert "statement timeout" in out["distinct"][("t", "topic")]["unread"]
    got = ac.grade_prose_none("x", (_vocab_decl(TAGS)), {"t": (["topic"], {"topic": "text"}, None)}, "t", {("t", "topic"): 0}, forms=out)
    assert "scaled_vocabulary" not in (got["Narr.agree"]["prose_none"].get("forms") or {})                       # no invented distinct count


# ───────────────────────────── values_from, per-key form and nested rows (the L0 seeds are dict(...) calls and rows of strings) ─────────────────────────────

def test_values_from_per_key_reads_the_string_literals_assigned_to_a_key_in_dict_displays_and_dict_calls(src):
    rel = src('''
        NAME = "x"
        ROWS = [
            dict(pakshi="Owl", alt_names=["Moon-star", "Second"], deity=NAME),         # a name is not a literal
            {"pakshi": "Crow", "alt_names": ("Third",), "deity": f"composed {NAME}"},   # a composed value is not a literal
            dict(pakshi="Owl", alt_names=[], deity="Fixed"),
        ]
        MORE = [dict(pakshi="Hen")]
    ''')
    got = pf.resolve_values_from(ac.ROOT, dict(file=rel, constants=["ROWS", "MORE"], key="pakshi"))
    assert got == ["Crow", "Hen", "Owl"]
    assert pf.resolve_values_from(ac.ROOT, dict(file=rel, constants=["ROWS"], key="alt_names")) == ["Moon-star", "Second", "Third"]          # list / tuple values contribute their elements
    assert pf.resolve_values_from(ac.ROOT, dict(file=rel, constants=["ROWS"], key="deity")) == ["Fixed"]
    with pytest.raises(ValueError, match="holds no value"):
        pf.resolve_values_from(ac.ROOT, dict(file=rel, constants=["ROWS"], key="absent_key"))
    with pytest.raises(ValueError, match="assigned 0 time"):
        pf.resolve_values_from(ac.ROOT, dict(file=rel, constants=["NOPE"], key="pakshi"))


def test_values_from_flattens_a_literal_list_of_rows_of_strings_one_level(src):
    rel = src('ROWS = [("a", "b"), ("b", "c")]\nMIXED = [("a", 1)]')
    assert pf.resolve_values_from(ac.ROOT, dict(file=rel, constant="ROWS")) == ["a", "b", "c"]
    assert pf.resolve_values_from(ac.ROOT, dict(file=rel, constant="ROWS", field=1)) == ["b", "c"]
    with pytest.raises(ValueError, match="not a string"):
        pf.resolve_values_from(ac.ROOT, dict(file=rel, constant="MIXED"))


def test_the_per_key_form_is_a_sound_declaration_and_the_resolved_set_closes_the_column(src, db, monkeypatch):
    rel = src('ROWS = [' + ",".join(f"dict(topic={t!r})" for t in TAGS[:5]) + "]")
    vf = dict(file=rel, constants=["ROWS"], key="topic")
    assert ac.prose_none_problem(_decl(_cc(None, values_from=vf))) is None
    for bad in (dict(file=rel, constants=[], key="topic"), dict(file=rel, constants=["ROWS"]), dict(file=rel, constants=["ROWS"], key="topic", constant="ROWS")):
        assert ac.prose_none_problem(_decl(_cc(None, values_from=bad))) is not None, bad
    for t in TAGS[:3]:
        _ins(db, t)
    d = _vocab_decl(None, values_from=vf)
    d["prose_none"]["closed_columns"][1] = dict(column="topics", why="the topic list holds only reference_topic_tags values", values_from=vf)
    fs.all_na(_measure(db, monkeypatch, d))
    _ins(db, TAGS[200])                                                                               # a value the seed does not hold
    got = _measure(db, monkeypatch, d)
    assert got["Narr.agree"]["v"] == FAIL and "formgap_topics.topic" in got["Narr.agree"]["measured"]
