"""test_n189_forwarded_leaves.py: the forwarded-L1-leaves detector (SS ruling N-189): bo_laksana MUST certify, and the L1 leaves it forwards into bodha_msr_signals are measured by a REAL
data comparison, not a closed-values declaration.

CLAUDE.md N.5: an L2 signal never restates an L1 computed value as its own truth; it REFERENCES the L1 fact_id and INHERITS the value. The detector compares, in ONE set-based join of the measured
chart's signals to chart_facts on the cited fact_id, every forwarded leaf with the L1 value. Rows below are built by the REAL writer (`bo_laksana._build_signal_row`, `_make_aggregate_fact_row`,
`_load_vichara_divergence_signals`), so the detector's expectation is differential-tested against the code that forwards, on a DISPOSABLE PostgreSQL (never production).

Run: python -m pytest platform/scripts/governance/__tests__/test_n189_forwarded_leaves.py -q
"""
from __future__ import annotations

import ast
import json
import pathlib
import sys
import uuid

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
SIDECAR = HERE.parents[2] / "python-sidecar"
sys.path.insert(0, str(SIDECAR))

import asset_census as ac  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401  (the session fixture)

PASS, FAIL, PARTIAL, NO_DET, ERRORED = ac.PASS, ac.FAIL, ac.PARTIAL, ac.NO_DET, ac.ERRORED
CHART = ac.CHART_ID
OTHER = "11111111-2222-3333-4444-555555555555"
T = "bodha_msr_signals"
PRODUCER = "bo_laksana"
TIMEOUT = "ERROR:  canceling statement due to statement timeout"
R = dict(count_sql="SELECT count(*) FROM bodha_msr_signals WHERE chart_id = $1")
COLS = ["signal_id", "chart_id", "ayanamsha_id", "signal_type_id", "configuration_jsonb", "constituent_facts_array", "citation_ref", "citation_human", "verification_method",
        "producer_asset_id", "signal_headline_text", "signal_summary_text"]
PROSE = ["signal_headline_text", "signal_summary_text", "citation_human"]
FACTS_FORM = dict(form="chart_facts_row", rows=dict(column="verification_method", equals="L1_fact_projection"), leaf_column="configuration_jsonb")
VICHARA_FORM = dict(form="chart_vichara_row", rows=dict(column="verification_method", equals="chart_vichara_projection"), leaf_column="configuration_jsonb")
EVIDENCE = "platform/python-sidecar/pipeline/orchestrator/writers/bo_laksana.py:2380"
WHY = "bo_laksana copies the L1 fact's leaves into configuration_jsonb and cites the fact id in constituent_facts_array"


DIVISIONAL_FORM = dict(form="chart_divisional_row", rows=dict(column="verification_method", equals="L1_divisional_cross_check"), leaf_column="configuration_jsonb")
SCOPE = dict(file="bo_laksana.py", functions=["_build_signal_row", "_build_headline_text", "_load_vichara_divergence_signals"], constants=["_INSERT_SQL"])


def ff_decl(*forms, pin=None):
    return dict(table=T, cite_column="constituent_facts_array", forms=list(forms or [FACTS_FORM]), covered_scope=dict(SCOPE), pin=dict(pin or dict(empty_fallbacks=1, dynamic_row_caveats=1)),
                covers=list(PROSE), why=WHY, evidence=EVIDENCE)


@pytest.fixture(scope="module")
def writer():
    pytest.importorskip("psycopg")
    from pipeline.orchestrator.writers import bo_laksana
    return bo_laksana


def _q(v):
    if v is None:
        return "NULL"
    if isinstance(v, (dict, list)):
        return _q(json.dumps(v)) + "::jsonb"
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return repr(v)
    return "'" + str(v).replace("'", "''") + "'"


def _arr(xs):
    return "ARRAY[" + ",".join(_q(x) for x in xs) + "]::text[]" if xs else "'{}'::text[]"


def fact(fid, chart=CHART, cat="graha_dignity_per_varga", key="dignity", subject="SUN", num=1.5, text="exalted", jsonb=None, formula="F1", aya="lahiri", cref=None, chum=None):
    return dict(fact_id=fid, chart_id=chart, ayanamsha_id=aya, fact_category=cat, fact_subject=subject, fact_key=key, fact_value_num=num, fact_value_text=text, fact_value_jsonb=jsonb, formula_id=formula,
                source_calculation="ga_structural", verification_pass_status="two_pass_verified", citation_ref=cref, citation_human=chum)


@pytest.fixture
def world(disposable_pg, monkeypatch, writer):
    """`put(facts, signals=None, vichara=())`: a disposable bodha_msr_signals / chart_facts / chart_vichara. `signals` default: every fact projected by the REAL writer."""
    point_psql_at(disposable_pg, monkeypatch)
    ac.set_read_scope(None)

    def put(facts, signals=None, vichara_rows=(), ddl_extra="", divisional_rows=()):
        for t in ("bodha_msr_signals", "chart_facts", "chart_vichara", "chart_divisionals"):
            ac.psql(f"DROP TABLE IF EXISTS {t}")
        ac.psql("CREATE TABLE chart_divisionals (chart_id uuid, ayanamsha_id text, varga text, fact_key text, graha text, fact_value_text text)")
        for d in divisional_rows:
            ac.psql("INSERT INTO chart_divisionals VALUES (" + ", ".join(_q(x) for x in (d["chart_id"], d.get("aya", "lahiri"), d.get("varga", "D9"), d.get("fact_key", "dignity"), d["graha"], d["text"])) + ")")
        ac.psql("CREATE TABLE chart_facts (fact_id text PRIMARY KEY, chart_id uuid, ayanamsha_id text, fact_category text, fact_subject text, fact_key text, fact_value_num numeric, "
                "fact_value_text text, fact_value_jsonb jsonb, formula_id text, citation_ref text, citation_human text)")
        ac.psql("CREATE TABLE chart_vichara (id bigserial PRIMARY KEY, chart_id uuid, ayanamsha_id text, vichara_family text, subject text, domain text, value_num numeric, value_text text, "
                "constituent_facts_array text[])")
        ac.psql("CREATE TABLE bodha_msr_signals (signal_id uuid PRIMARY KEY, chart_id uuid NOT NULL, ayanamsha_id text, signal_type_id text, configuration_jsonb jsonb, constituent_facts_array text[] NOT NULL, "
                "citation_ref text, citation_human text, verification_method text, producer_asset_id text, signal_headline_text text, signal_summary_text text" + ddl_extra + ")")
        for f in facts:
            ac.psql("INSERT INTO chart_facts VALUES (" + ", ".join(_q(f[k]) for k in ("fact_id", "chart_id", "ayanamsha_id", "fact_category", "fact_subject", "fact_key", "fact_value_num", "fact_value_text",
                                                                                      "fact_value_jsonb", "formula_id", "citation_ref", "citation_human")) + ")")
        for v in vichara_rows:
            ac.psql("INSERT INTO chart_vichara (chart_id, ayanamsha_id, vichara_family, subject, domain, value_num, value_text, constituent_facts_array) VALUES ("
                    + ", ".join([_q(v["chart_id"]), _q(v.get("aya", "lahiri")), _q("varga_ratification_divergence"), _q(v["subject"]), _q(v["domain"]), _q(v.get("value_num", -1)), _q(v["value_text"]),
                                 _arr(v.get("constituents", []))]) + ")")
        for s in (signals if signals is not None else [project(writer, f) for f in facts]):
            insert_signal(s)

    yield put
    ac.set_read_scope(None)
    for t in ("bodha_msr_signals", "chart_facts", "chart_vichara", "chart_divisionals"):
        ac.psql(f"DROP TABLE IF EXISTS {t}")


def project(writer, f, valid=None, chart=None, producer=PRODUCER):
    """One chart_facts row projected by the REAL writer (`_build_signal_row`): the signal row exactly as bo_laksana would insert it."""
    valid = valid if valid is not None else {f["fact_id"]}
    row = writer._build_signal_row(dict(f), chart or f["chart_id"], "build-1", {}, {}, {}, "2026-01-01T00:00:00+00:00", valid_fact_ids=valid)
    return dict(signal_id=str(uuid.uuid5(uuid.NAMESPACE_URL, f["fact_id"] + "|" + str(chart or f["chart_id"]))), chart_id=chart or f["chart_id"], ayanamsha_id=row["ayanamsha_id"],
                signal_type_id=row["signal_type_id"], configuration_jsonb=json.loads(row["configuration_jsonb"]), constituent_facts_array=list(row["constituent_facts_array"]),
                citation_ref=row["citation_ref"], citation_human=row["citation_human"], verification_method=row["verification_method"], producer_asset_id=producer,
                signal_headline_text=row["signal_headline_text"], signal_summary_text=row["signal_summary_text"])


def insert_signal(s):
    ac.psql("INSERT INTO bodha_msr_signals VALUES (" + ", ".join([_q(s["signal_id"]), _q(s["chart_id"]), _q(s["ayanamsha_id"]), _q(s["signal_type_id"]), _q(s["configuration_jsonb"]),
                                                                  _arr(s["constituent_facts_array"]), _q(s["citation_ref"]), _q(s["citation_human"]), _q(s["verification_method"]),
                                                                  _q(s["producer_asset_id"]), _q(s["signal_headline_text"]), _q(s["signal_summary_text"])]) + ")")


def measure(ff=None, shared=(), decl=None, chart=CHART):
    """Install the engine's read scope for the signal table and run the detector (for `chart`: the measured chart)."""
    sc = ac.read_scopes([T], R, {T: COLS}, set(shared), decl or {}, chart)
    ac.set_read_scope(sc)
    ff = ff or ff_decl()
    return ac.grade_forwarded_leaves(ff, ac.forwarded_leaves_read(ff, COLS, chart))


def mutate(sid, sql_set):
    ac.psql(f"UPDATE bodha_msr_signals SET {sql_set} WHERE signal_id = '{sid}'")


FACTS = [
    fact("f1", text="exalted", num=1.5, jsonb={"graha": "Sun", "varga": "D1", "house": 1, "note": None, "nested": {"a": [1, 2]}, "flag": False, "zero": 0}),
    fact("f2", key="own_sign", subject="MOO", num=None, text="Cancer", jsonb=None, formula=None),
    fact("f3", cat="yoga_fires", key="raja", subject=None, num=0.123456789012345678, text=None, jsonb={"graha": "Jupiter", "constituent_facts_array": ["f1"]}, cref="BPHS 34.1", chum="Raja yoga, BPHS 34.1"),
    fact("f4", cat="panchanga", key="tithi", subject="CHART", num=3, text="Shukla Tritiya", jsonb={"aggregated": True, "member_count": 2}),
]


# ───────────────────────── PASS: the forwarded leaves equal the cited L1 value ─────────────────────────

def test_REAL_SQL_equal_leaves_read_pass_over_rows_built_by_the_real_writer(world):
    world(FACTS)
    rec = measure()
    assert rec["v"] == PASS, rec["measured"]
    assert rec["forms"]["chart_facts_row"]["count"] == 4 and rec["forms"]["chart_facts_row"]["at_least"] is False
    assert f"chart {CHART[:8]}" in rec["read_scope"] and "every cited fact_id resolves" in rec["measured"]


def test_REAL_SQL_the_writer_really_forwards_what_the_detector_expects(world, writer):
    """The differential check: the leaf object the detector expects (`_fl_expected`: the writer's own order, its whole-string uuid-v4 strip) equals the writer's config EXACTLY, key for key,
    apart from the keys the writer resolves itself."""
    rid = str(uuid.uuid4())
    extra = [fact("d1", key="kd", jsonb={"rows": [rid, 5], "deep": {"x": rid, "y": 2}, "parent_fact": rid, "empty": [rid], "bare": rid, "keep": "see " + rid + " here", "n": {"m": {"o": [rid, 5]}}})]
    world(FACTS + extra)
    for f in FACTS + extra:
        s = project(writer, f, valid={g["fact_id"] for g in FACTS + extra})
        got = ac.psql("SELECT x.e FROM chart_facts f " + ac._fl_expected("f", CHART) + " WHERE f.fact_id = '" + f["fact_id"] + "'")
        exp = json.loads(got[0][0])
        cfg = {k: v for k, v in s["configuration_jsonb"].items() if k not in ("graha", "house", "target_house") or k in exp}
        assert cfg == exp, (f["fact_id"], cfg, exp)


def test_REAL_SQL_numbers_compare_as_float8_like_the_writer_and_text_exactly(world):
    world([fact("n1", num=0.1 + 0.2, text="Sun "), fact("n2", key="k2", num=12345678901234567890.5, text="é x")])
    assert measure()["v"] == PASS


def test_REAL_SQL_a_serialized_uuid_v4_leaf_is_not_compared_the_writer_strips_it_by_design(world):
    rid = str(uuid.uuid4())
    world([fact("u1", jsonb={"constituent_fact_id": rid, "graha": "Sun", "rows": [rid, 5], "deep": {"x": rid, "y": 2}})])
    rec = measure()
    assert rec["v"] == PASS, rec["measured"]


def test_REAL_SQL_a_composite_rollup_is_not_compared_one_to_one_but_its_members_are_resolved(world, writer):
    members = [fact(f"m{i}", cat="graha_dignity_per_varga", key=f"k{i}", subject="SUN") for i in range(3)]
    agg = writer._make_aggregate_fact_row([dict(m) for m in members], "D9")
    row = writer._build_signal_row(agg, CHART, "b", {}, {}, {}, "2026-01-01T00:00:00+00:00", valid_fact_ids={m["fact_id"] for m in members})
    sid = str(uuid.uuid4())
    sig = dict(signal_id=sid, chart_id=CHART, ayanamsha_id=row["ayanamsha_id"], signal_type_id=row["signal_type_id"], configuration_jsonb=json.loads(row["configuration_jsonb"]),
               constituent_facts_array=list(row["constituent_facts_array"]), citation_ref=row["citation_ref"], citation_human=row["citation_human"], verification_method="L1_fact_projection",
               producer_asset_id=PRODUCER, signal_headline_text="h", signal_summary_text="s")
    assert sig["configuration_jsonb"]["fact_key"] == "aggregate_D9" and len(sig["constituent_facts_array"]) == 3
    world(members, signals=[project(writer, members[0]), sig])
    assert measure()["v"] == PASS
    mutate(sid, "constituent_facts_array = ARRAY['m0','m1','ghost']")                                   # a member that resolves to nothing
    rec = measure()
    assert rec["v"] == FAIL and "ghost" in rec["measured"]


# ───────────────────────── FAIL: a differing leaf (the mutation test: flip one forwarded value) ─────────────────────────

FLIPS = [
    ("fact_value_text", "jsonb_set(configuration_jsonb, '{fact_value_text}', '\"forged\"')", "fact_value_text", '"forged"', '"exalted"'),
    ("fact_value_num", "jsonb_set(configuration_jsonb, '{fact_value_num}', '9.5')", "fact_value_num", "9.5", "1.5"),
    ("jsonb leaf", "jsonb_set(configuration_jsonb, '{graha}', '\"Mars\"')", "graha", '"Mars"', '"Sun"'),
    ("nested jsonb leaf", "jsonb_set(configuration_jsonb, '{nested}', '{\"a\": [1, 3]}')", "nested", '{"a": [1, 3]}', '{"a": [1, 2]}'),
    ("fact_subject", "jsonb_set(configuration_jsonb, '{fact_subject}', '\"MON\"')", "fact_subject", '"MON"', '"SUN"'),
    ("formula id", "jsonb_set(configuration_jsonb, '{l1_formula_id}', '\"F9\"')", "l1_formula_id", '"F9"', '"F1"'),
    ("dropped leaf", "configuration_jsonb - 'house'", "house", "<NULL>", "1"),
    ("null for a value", "jsonb_set(configuration_jsonb, '{fact_value_text}', 'null')", "fact_value_text", "<NULL>", '"exalted"'),
    ("empty string for a value", "jsonb_set(configuration_jsonb, '{fact_value_text}', '\"\"')", "fact_value_text", '""', '"exalted"'),
    ("fact_key", "jsonb_set(configuration_jsonb, '{fact_key}', '\"other\"')", "fact_key", "other", "(no cited fact carries this fact_key)"),
]


@pytest.mark.parametrize("name,expr,leaf,fwd,l1", FLIPS, ids=[f[0] for f in FLIPS])
def test_REAL_SQL_mutation_flipping_one_forwarded_leaf_reads_fail_naming_the_offender(world, writer, name, expr, leaf, fwd, l1):
    world(FACTS)
    assert measure()["v"] == PASS                                                                         # green before the mutation ...
    sid = project(writer, FACTS[0])["signal_id"]
    mutate(sid, f"configuration_jsonb = {expr}")
    rec = measure()
    assert rec["v"] == FAIL, (name, rec["measured"])                                                      # ... red after it
    m = rec["measured"]
    assert f"signal {sid}" in m and "fact_id f1" in m and f"leaf {leaf}:" in m and "bounded sample (not a total)" in m, m
    assert f"forwarded {fwd} vs L1 {l1}" in m, m


@pytest.mark.parametrize("col,val", [("citation_human", "'forged'"), ("citation_ref", "'chart_facts/other'"), ("signal_type_id", "'graha_dignity_per_varga:other'")])
def test_REAL_SQL_the_forwarded_columns_are_compared_too(world, writer, col, val):
    world(FACTS)
    mutate(project(writer, FACTS[0])["signal_id"], f"{col} = {val}")
    rec = measure()
    assert rec["v"] == FAIL and f"leaf {col}:" in rec["measured"], rec["measured"]


def test_REAL_SQL_l1_changing_after_the_build_is_drift(world):
    world(FACTS)
    ac.psql("UPDATE chart_facts SET fact_value_text = 'debilitated' WHERE fact_id = 'f1'")
    rec = measure()
    assert rec["v"] == FAIL and 'forwarded "exalted" vs L1 "debilitated"' in rec["measured"], rec["measured"]


def test_REAL_SQL_null_equals_null_and_null_is_not_an_empty_string(world, writer):
    world([fact("z1", text=None, num=None, subject=None, formula=None, jsonb=None)])
    assert measure()["v"] == PASS                                                                          # NULL = NULL
    sid = project(writer, fact("z1", text=None, num=None, subject=None, formula=None, jsonb=None))["signal_id"]
    mutate(sid, "configuration_jsonb = jsonb_set(configuration_jsonb, '{fact_value_text}', '\"\"')")
    assert measure()["v"] == FAIL                                                                          # NULL vs '' is DIFFERENT


def test_REAL_SQL_the_sample_is_bounded_and_no_total_is_invented(world, writer):
    facts = [fact(f"b{i}", key=f"k{i}") for i in range(6)]
    world(facts)
    ac.psql("UPDATE bodha_msr_signals SET configuration_jsonb = jsonb_set(configuration_jsonb, '{fact_value_text}', '\"forged\"')")
    rec = measure()
    assert rec["v"] == FAIL
    assert rec["measured"].count("(signal ") == ac.FORWARDED_SAMPLE_LIMIT and "(not a total)" in rec["measured"]
    assert sum(len(v) for v in rec["offenders"]["drift"].values()) == ac.FORWARDED_SAMPLE_LIMIT


# ───────────────────────── FAIL: dangling citation; PARTIAL: a leaf with no fact_id ─────────────────────────

def test_REAL_SQL_a_cited_fact_id_that_is_not_in_chart_facts_is_a_fail(world, writer):
    world(FACTS)
    sid = project(writer, FACTS[0])["signal_id"]
    mutate(sid, "constituent_facts_array = ARRAY['f1', 'nope']")
    rec = measure()
    assert rec["v"] == FAIL and f"signal {sid}" in rec["measured"] and "cited fact_id nope is not in chart_facts" in rec["measured"], rec["measured"]


def test_REAL_SQL_a_cited_id_that_exists_only_in_another_chart_is_dangling(world, writer):
    world(FACTS + [fact("o1", chart=OTHER, key="elsewhere")])
    sid = project(writer, FACTS[0])["signal_id"]
    mutate(sid, "constituent_facts_array = ARRAY['f1', 'o1']")
    rec = measure()
    assert rec["v"] == FAIL and "cited fact_id o1" in rec["measured"], rec["measured"]


def test_REAL_SQL_a_row_citing_a_fact_with_another_key_is_a_fail_not_a_pass(world, writer):
    world(FACTS)
    sid = project(writer, FACTS[0])["signal_id"]
    mutate(sid, "constituent_facts_array = ARRAY['f2']")                                                # f2 resolves, but it is not the fact this row forwards
    rec = measure()
    assert rec["v"] == FAIL and "(no cited fact carries this fact_key)" in rec["measured"], rec["measured"]


def test_REAL_SQL_a_leaf_with_no_fact_id_stays_partial_with_the_named_cause(world, writer):
    world(FACTS)
    sid = project(writer, FACTS[0])["signal_id"]
    mutate(sid, "constituent_facts_array = '{}'")
    rec = measure()
    assert rec["v"] == PARTIAL and "cite no fact_id" in rec["measured"] and sid in rec["measured"] and "no L1 fact to be compared to" in rec["measured"], rec["measured"]


# ───────────────────────── the measured chart only ─────────────────────────

def test_REAL_SQL_another_charts_drift_does_not_affect_the_measured_chart_and_the_reverse(world, writer):
    facts = FACTS + [fact("o1", chart=OTHER, key="elsewhere")]
    world(facts)
    ac.psql(f"UPDATE bodha_msr_signals SET configuration_jsonb = jsonb_set(configuration_jsonb, '{{fact_value_text}}', '\"forged\"') WHERE chart_id = '{OTHER}'")
    ac.psql(f"UPDATE bodha_msr_signals SET constituent_facts_array = ARRAY['gone'] WHERE chart_id = '{OTHER}'")
    rec = measure()
    assert rec["v"] == PASS, rec["measured"]                                                              # the other chart is dirty, the measured one clean
    assert measure(chart=OTHER)["v"] == FAIL                                                              # and read as its own chart, it is the dirty one
    mutate(project(writer, FACTS[1])["signal_id"], "configuration_jsonb = jsonb_set(configuration_jsonb, '{fact_value_text}', '\"forged\"')")
    assert measure()["v"] == FAIL                                                                         # a drift in the measured chart is found whatever the other chart holds


def test_REAL_SQL_a_shared_table_is_read_through_the_assets_own_rows(world, writer):
    world(FACTS)
    other_asset = project(writer, fact("x1", key="otherasset"), producer="bo_other")
    ac.psql("INSERT INTO chart_facts VALUES ('x1', '" + CHART + "', 'lahiri', 'graha_dignity_per_varga', 'SUN', 'otherasset', 1.5, 'exalted', NULL, 'F1', NULL, NULL)")
    insert_signal(other_asset)
    mutate(other_asset["signal_id"], "configuration_jsonb = jsonb_set(configuration_jsonb, '{fact_value_text}', '\"forged\"')")      # ANOTHER asset's row is dirty
    decl = {"kind": "data", "produced_tables": [dict(table=T, filter=dict(column="producer_asset_id", equals=PRODUCER), why="the writer's own row set")]}
    rec = measure(shared=[T], decl=decl)
    assert rec["v"] == PASS and "declared produced rows" in rec["read_scope"], rec
    assert measure()["v"] == FAIL                                                                         # unscoped (not shared) it would judge every producer's rows


def test_REAL_SQL_zero_rows_of_the_measured_chart_is_unmeasured_never_pass(world):
    world([fact("o1", chart=OTHER)])                                                                      # the only rows belong to another chart
    rec = measure()
    assert rec["v"] == NO_DET and "empty scoped read is unmeasured" in rec["measured"] and rec["v"] != PASS


def test_REAL_SQL_a_declared_form_with_no_row_is_partial_not_pass(world):
    world(FACTS)
    rec = measure(ff_decl(FACTS_FORM, VICHARA_FORM))
    assert rec["v"] == PARTIAL and "chart_vichara_row have no row in the measured chart" in rec["measured"], rec["measured"]


# ───────────────────────── the chart_vichara form (the writer's own divergence signals) ─────────────────────────

class _Cur:
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, *a, **k):
        return self


class _Conn:
    def __init__(self, rows):
        self.rows = rows

    def cursor(self):
        return _Cur()

    def execute(self, sql, params=None):
        outer = self

        class C:
            def fetchall(self):
                return outer.rows
        return C()


class _DConn:
    """A connection stub for `_build_navamsha_cross_check_signals`: the D1 dignity facts, the D9 dignity rows, nothing else (no neecha-bhanga firings)."""

    def __init__(self, d1, d9):
        self.d1, self.d9 = d1, d9

    def cursor(self):
        return _Cur()

    def execute(self, sql, params=None):
        outer = self

        class C:
            def fetchall(self):
                if "graha_dignity_per_varga" in sql and "D1" in sql:
                    return outer.d1
                if "chart_divisionals" in sql and "'D9'" in sql and "dignity" in sql:
                    return outer.d9
                return []
        return C()


def divisional_signals(writer, d1_facts, d9_rows):
    """The D9 cross-check signals as the REAL writer builds them (`_build_navamsha_cross_check_signals`) from D1 dignity facts and chart_divisionals rows."""
    built = writer._build_navamsha_cross_check_signals(_DConn([dict(fact_id=f["fact_id"], fact_subject=f["fact_subject"], fact_value_text=f["fact_value_text"]) for f in d1_facts],
                                                              [dict(graha=d["graha"], fact_value_text=d["text"]) for d in d9_rows]), CHART, "lahiri", "build-1", "2026-01-01T00:00:00+00:00", {}, {}, {})
    return [dict(signal_id=str(uuid.uuid4()), chart_id=CHART, ayanamsha_id="lahiri", signal_type_id=b["signal_type_id"], configuration_jsonb=json.loads(b["configuration_jsonb"]),
                 constituent_facts_array=list(b["constituent_facts_array"]), citation_ref=b["citation_ref"], citation_human=b["citation_human"], verification_method=b["verification_method"],
                 producer_asset_id=PRODUCER, signal_headline_text=b["signal_headline_text"], signal_summary_text=b["signal_summary_text"]) for b in built]


def d1_fact(fid, subject="D1_SUN", text="exalted"):
    return fact(fid, cat="graha_dignity_per_varga", key="dignity", subject=subject, num=None, text=text, jsonb={"varga": "D1"}, formula=None)


def vichara_world(world, writer, rows, facts=None, with_projections=False, divisional=None):
    """`divisional`: [(D1 fact, D9 text)]: the D1 facts join chart_facts, the D9 texts chart_divisionals, and the REAL writer's cross-check signals are inserted."""
    facts = facts if facts is not None else [fact("v1", key="vk1"), fact("v2", key="vk2")]
    sigs = [project(writer, f) for f in facts] if with_projections else []
    div_rows = []
    if divisional:
        d1s = [d for d, _ in divisional]
        facts = list(facts) + d1s
        div_rows = [dict(chart_id=CHART, graha=ac_graha(d["fact_subject"]), text=t) for d, t in divisional]
        sigs += divisional_signals(writer, d1s, div_rows)
    for r in rows:
        built = writer._load_vichara_divergence_signals(_Conn([dict(subject=r["subject"], domain=r["domain"], value_text=r["value_text"], value_num=-1, constituent_facts_array=r.get("constituents", []))]),
                                                         CHART, "lahiri", "build-1", "2026-01-01T00:00:00+00:00")
        for b in built:
            sigs.append(dict(signal_id=str(uuid.uuid4()), chart_id=CHART, ayanamsha_id="lahiri", signal_type_id=b["signal_type_id"], configuration_jsonb=json.loads(b["configuration_jsonb"]),
                             constituent_facts_array=list(b["constituent_facts_array"]), citation_ref=b["citation_ref"], citation_human=b["citation_human"],
                             verification_method=b["verification_method"], producer_asset_id=PRODUCER, signal_headline_text=b["signal_headline_text"], signal_summary_text=b["signal_summary_text"]))
    world(facts, signals=sigs, vichara_rows=[dict(r, chart_id=CHART) for r in rows], divisional_rows=div_rows)
    return sigs


def ac_graha(subject):
    return {"D1_SUN": "Sun", "D1_MOON": "Moon", "D1_MAR": "Mars"}[subject]


VROWS = [dict(subject="SUN", domain="career", value_text="D1 vs D10 diverge", constituents=["v1", "v2"]), dict(subject="MON", domain="wealth", value_text="D9 divergence", constituents=[])]


def test_REAL_SQL_vichara_divergence_signals_forward_their_chart_vichara_leaves_faithfully(world, writer):
    vichara_world(world, writer, VROWS)
    rec = measure(ff_decl(VICHARA_FORM))
    assert rec["v"] == PASS and rec["forms"]["chart_vichara_row"]["count"] == 2, rec["measured"]


@pytest.mark.parametrize("sql,leaf", [("configuration_jsonb = jsonb_set(configuration_jsonb, '{value_text}', '\"forged\"')", "value_text"),
                                      ("configuration_jsonb = jsonb_set(configuration_jsonb, '{domain}', '\"health\"')", "domain"),
                                      ("constituent_facts_array = ARRAY['v2']", "constituent_facts_array"),
                                      ("citation_ref = 'chart_vichara/SUN/other'", "citation_ref")])
def test_REAL_SQL_a_differing_vichara_leaf_reads_fail_naming_it(world, writer, sql, leaf):
    sigs = vichara_world(world, writer, VROWS)
    mutate(sigs[0]["signal_id"], sql)
    rec = measure(ff_decl(VICHARA_FORM))
    assert rec["v"] == FAIL and f"leaf {leaf}:" in rec["measured"] and f"signal {sigs[0]['signal_id']}" in rec["measured"], rec["measured"]


def test_REAL_SQL_a_vichara_signal_with_no_chart_vichara_row_fails(world, writer):
    sigs = vichara_world(world, writer, VROWS)
    ac.psql("DELETE FROM chart_vichara WHERE subject = 'SUN'")
    rec = measure(ff_decl(VICHARA_FORM))
    assert rec["v"] == FAIL and "(no chart_vichara row for this subject)" in rec["measured"], rec["measured"]


def test_REAL_SQL_a_null_domain_forwarded_as_an_empty_string_is_different_not_equal(world, writer):
    """The writer turns an absent domain / value_text into '' (a literal fallback the static scan flags). NULL vs '' is a DIFFERENT leaf (a value standing in for NULL): the reading names it."""
    sigs = vichara_world(world, writer, [dict(subject="SUN", domain=None, value_text="x", constituents=[])])
    rec = measure(ff_decl(VICHARA_FORM))
    assert rec["v"] == FAIL and "leaf domain:" in rec["measured"], rec["measured"]


# ───────────────────────── review round (N-194): the writer's whole-string uuid-v4 strip, mirrored exactly ─────────────────────────

RID = str(uuid.uuid4())
OTHER_RID = str(uuid.uuid4())
UFACT = dict(jsonb={"rows": [RID, 5], "deep": {"x": RID, "y": 2}, "parent_fact": RID, "empty": [RID], "keep": "kept " + RID + " text"}, text="see " + RID + " for details", key="uk")


def _uworld(world, *extra):
    f = fact("u1", **UFACT)
    world([f] + list(extra), signals=[project(writer_mod(), g, valid={x["fact_id"] for x in [f] + list(extra)}) for g in [f] + list(extra)])
    return f


_WRITER = []


def writer_mod():
    from pipeline.orchestrator.writers import bo_laksana
    return bo_laksana


def test_REAL_SQL_honest_rows_with_serialized_row_ids_read_pass_nothing_skipped(world):
    _uworld(world)
    rec = measure()
    assert rec["v"] == PASS, rec["measured"]
    assert "no leaf skipped" in rec["measured"]


FORGERIES = [
    ("deep forged", "jsonb_set(configuration_jsonb, '{deep}', '{\"y\": 999}')", "deep"),
    ("rows forged", "jsonb_set(configuration_jsonb, '{rows}', '[777]')", "rows"),
    ("text beside a uuid forged", "jsonb_set(configuration_jsonb, '{fact_value_text}', '\"unrelated text\"')", "fact_value_text"),
    ("parent_fact forged to a random uuid", "jsonb_set(configuration_jsonb, '{parent_fact}', '\"" + OTHER_RID + "\"')", "extra key parent_fact"),
    ("the uuid left in a list", "jsonb_set(configuration_jsonb, '{rows}', '[\"" + RID + "\", 5]')", "rows"),
    ("the uuid left in a dict", "jsonb_set(configuration_jsonb, '{deep}', '{\"x\": \"" + RID + "\", \"y\": 2}')", "deep"),
    ("emptied container made absent", "configuration_jsonb - 'empty'", "empty"),
    ("embedded uuid text changed", "jsonb_set(configuration_jsonb, '{keep}', '\"kept other text\"')", "keep"),
]


@pytest.mark.parametrize("name,expr,leaf", FORGERIES, ids=[f[0] for f in FORGERIES])
def test_REAL_SQL_a_forgery_next_to_a_serialized_row_id_reads_fail(world, name, expr, leaf):
    f = _uworld(world)
    mutate(project(writer_mod(), f)["signal_id"], "configuration_jsonb = " + expr)
    rec = measure()
    assert rec["v"] == FAIL and ("leaf " + leaf + ":") in rec["measured"], (name, rec["measured"])


def test_REAL_SQL_a_uuid_that_is_a_fact_id_of_the_chart_is_kept_by_the_writer_and_so_expected(world):
    ref = str(uuid.uuid4())
    refd = fact(ref, key="refd")
    holder = fact("h1", key="holder", jsonb={"ref": ref, "also": [ref, RID]})
    allf = [refd, holder]
    world(allf, signals=[project(writer_mod(), g, valid={x["fact_id"] for x in allf}) for g in allf])
    assert measure()["v"] == PASS
    mutate(project(writer_mod(), holder, valid={x["fact_id"] for x in allf})["signal_id"], "configuration_jsonb = configuration_jsonb - 'ref'")       # the writer kept it: dropping it is a drift
    assert measure()["v"] == FAIL


def test_REAL_SQL_a_whole_uuid_leaf_is_dropped_by_the_writer_so_the_signal_must_not_carry_it(world):
    f = fact("w1", key="wk", text=RID, jsonb=None)
    world([f], signals=[project(writer_mod(), f, valid={"w1"})])
    assert "fact_value_text" not in project(writer_mod(), f, valid={"w1"})["configuration_jsonb"]
    assert measure()["v"] == PASS
    mutate(project(writer_mod(), f, valid={"w1"})["signal_id"], "configuration_jsonb = jsonb_set(configuration_jsonb, '{fact_value_text}', '\"forged\"')")
    rec = measure()
    assert rec["v"] == FAIL and "leaf extra key fact_value_text:" in rec["measured"], rec["measured"]


def test_REAL_SQL_a_leaf_nested_deeper_than_the_mirrored_strip_is_named_not_compared(world):
    f = fact("n1", key="nk", jsonb={"a": {"b": {"c": {"d": [RID, {"e": RID}]}}}})
    world([f], signals=[project(writer_mod(), f, valid={"n1"})])
    rec = measure()
    assert rec["v"] == PARTIAL and "nest deeper than " + str(ac.FORWARDED_STRIP_DEPTH) + " levels" in rec["measured"], rec["measured"]


# ───────────────────────── review round (N-194): the third form, unmeasured rows, extra keys, the own fact ─────────────────────────

def test_REAL_SQL_every_row_of_the_asset_must_fall_in_a_measured_form_else_partial_naming_the_method_and_count(world, writer):
    vichara_world(world, writer, [], facts=FACTS, with_projections=True, divisional=[(d1_fact("d1sun"), "debilitated")])
    rec = measure(ff_decl(FACTS_FORM))                                                                 # the divisional rows are declared nowhere
    assert rec["v"] == PARTIAL and "L1_divisional_cross_check (1)" in rec["measured"] and "NOT compared" in rec["measured"], rec["measured"]
    ac.psql("UPDATE bodha_msr_signals SET verification_method = NULL WHERE verification_method = 'L1_divisional_cross_check'")
    rec = measure(ff_decl(FACTS_FORM))
    assert rec["v"] == PARTIAL and "<NULL> (1)" in rec["measured"], rec["measured"]


def test_REAL_SQL_the_divisional_cross_check_copies_read_pass_on_the_writers_own_rows(world, writer):
    vichara_world(world, writer, [], facts=FACTS, with_projections=True, divisional=[(d1_fact("d1sun"), "debilitated"), (d1_fact("d1moon", "D1_MOON", "own"), "own")])
    rec = measure(ff_decl(FACTS_FORM, DIVISIONAL_FORM))
    assert rec["v"] == PASS and rec["forms"]["chart_divisional_row"]["count"] == 2, rec["measured"]
    assert "d1_tier / d9_tier / classification" in rec["measured"] and "NOT compared" in rec["measured"]


@pytest.mark.parametrize("sql,leaf", [("configuration_jsonb = jsonb_set(configuration_jsonb, '{d9_dignity}', '\"exalted\"')", "d9_dignity"),
                                      ("configuration_jsonb = jsonb_set(configuration_jsonb, '{d1_dignity}', '\"debilitated\"')", "d1_dignity"),
                                      ("citation_ref = 'chart_divisionals/D9/Mars'", "citation_ref"),
                                      ("constituent_facts_array = ARRAY['d1sun', 'f1']", None)])
def test_REAL_SQL_a_forged_divisional_row_reads_fail(world, writer, sql, leaf):
    sigs = vichara_world(world, writer, [], facts=FACTS, with_projections=True, divisional=[(d1_fact("d1sun"), "debilitated")])
    sid = next(x["signal_id"] for x in sigs if x["verification_method"] == "L1_divisional_cross_check")
    ff = ff_decl(FACTS_FORM, DIVISIONAL_FORM)
    assert measure(ff)["v"] == PASS
    mutate(sid, sql)
    rec = measure(ff)
    assert rec["v"] == FAIL and (leaf is None or ("leaf " + leaf + ":") in rec["measured"]) and sid in rec["measured"], rec["measured"]


def test_REAL_SQL_a_divisional_row_with_no_d9_row_or_no_d1_fact_is_not_a_pass(world, writer):
    """The writer's `neutral` defaults: a D9 dignity with no chart_divisionals row is an invented value (FAIL); a D1 dignity with no cited fact has no L1 source (PARTIAL)."""
    vichara_world(world, writer, [], facts=FACTS, with_projections=True, divisional=[(d1_fact("d1sun"), "debilitated")])
    ac.psql("DELETE FROM chart_divisionals")
    rec = measure(ff_decl(FACTS_FORM, DIVISIONAL_FORM))
    assert rec["v"] == FAIL and "(no chart_divisionals D9 dignity row for this graha)" in rec["measured"], rec["measured"]
    vichara_world(world, writer, [], facts=FACTS, with_projections=True, divisional=[(d1_fact("d1sun"), "debilitated")])
    ac.psql("UPDATE bodha_msr_signals SET constituent_facts_array = '{}' WHERE verification_method = 'L1_divisional_cross_check'")
    rec = measure(ff_decl(FACTS_FORM, DIVISIONAL_FORM))
    assert rec["v"] == PARTIAL and "cite no fact_id" in rec["measured"], rec["measured"]


def test_REAL_SQL_an_invented_extra_key_in_the_signal_reads_fail(world, writer):
    world(FACTS)
    sid = project(writer, FACTS[1])["signal_id"]
    mutate(sid, "configuration_jsonb = configuration_jsonb || '{\"extra_key\": 1}'")
    rec = measure()
    assert rec["v"] == FAIL and "leaf extra key extra_key:" in rec["measured"], rec["measured"]
    mutate(sid, "configuration_jsonb = (configuration_jsonb - 'extra_key') || '{\"graha\": \"Mars\"}'")                # a writer-resolved key is not compared: it is named, not judged
    rec = measure()
    assert rec["v"] == PASS and "graha / house / target_house" in rec["measured"] and "NOT compared" in rec["measured"], rec["measured"]


def test_REAL_SQL_leaves_that_equal_another_cited_fact_are_a_drift_the_own_fact_is_the_first_cited(world, writer):
    a = fact("a1", key="same", subject="SUN", cref="BPHS 1", chum="same cite")
    b = fact("b1", key="same", subject="MOO", text="own", cref="BPHS 1", chum="same cite")
    world([a, b])
    assert measure()["v"] == PASS
    sid = project(writer, b)["signal_id"]
    mutate(sid, "constituent_facts_array = ARRAY['a1', 'b1']")                                          # the row forwards B's complete leaves but its own (first cited) fact is A
    rec = measure()
    assert rec["v"] == FAIL and sid in rec["measured"], rec["measured"]
    mutate(sid, "constituent_facts_array = ARRAY['b1', 'a1']")                                          # B first: B is the own fact, A is just cited
    assert measure()["v"] == PASS


def test_REAL_SQL_an_l1_fact_that_lists_constituents_may_be_cited_after_them(world, writer):
    m1, m2 = fact("m1", key="c1"), fact("m2", key="c2")
    own = fact("own1", key="comp", jsonb={"constituent_facts_array": ["m1", "m2", "own1"], "graha": "Sun"})
    allf = [m1, m2, own]
    sig = project(writer, own, valid={"m1", "m2", "own1"})
    assert sig["constituent_facts_array"] == ["m1", "m2", "own1"]
    world(allf, signals=[project(writer, m1), project(writer, m2), sig])
    assert measure()["v"] == PASS


def test_REAL_SQL_the_fact_is_bound_to_the_signals_ayanamsha_or_invariant(world, writer):
    f = fact("y1", aya="lahiri")
    inv = fact("y2", key="invkey", aya="INVARIANT")
    world([f, inv], signals=[project(writer, f), project(writer, inv)])
    assert measure()["v"] == PASS                                                                       # an INVARIANT fact is cited by any ayanamsha's signal
    ac.psql("UPDATE bodha_msr_signals SET ayanamsha_id = 'kp' WHERE constituent_facts_array = ARRAY['y1']")      # a lahiri fact cited by a kp signal does not resolve as its own
    rec = measure()
    assert rec["v"] == FAIL and "(no cited fact carries this fact_key)" in rec["measured"], rec["measured"]


# ───────────────────────── review round (N-194): composites verified, the explicit chart predicate, the engine's empty-scope state ─────────────────────────

def _composite_world(world, writer, n=3):
    members = [fact("m" + str(i), key="k" + str(i)) for i in range(n)]
    agg = writer._make_aggregate_fact_row([dict(m) for m in members], "D9")
    row = writer._build_signal_row(agg, CHART, "b", {}, {}, {}, "2026-01-01T00:00:00+00:00", valid_fact_ids={m["fact_id"] for m in members})
    sid = str(uuid.uuid4())
    sig = dict(signal_id=sid, chart_id=CHART, ayanamsha_id=row["ayanamsha_id"], signal_type_id=row["signal_type_id"], configuration_jsonb=json.loads(row["configuration_jsonb"]),
               constituent_facts_array=list(row["constituent_facts_array"]), citation_ref=row["citation_ref"], citation_human=row["citation_human"], verification_method="L1_fact_projection",
               producer_asset_id=PRODUCER, signal_headline_text="h", signal_summary_text="s")
    world(members, signals=[project(writer, members[0]), sig])
    return sid


def test_REAL_SQL_a_composite_is_verified_and_counted_in_the_cell_text(world, writer):
    _composite_world(world, writer)
    rec = measure()
    assert rec["v"] == PASS and rec["composites"] == dict(count=1, at_least=False) and "1 composite roll-up(s) are not compared one to one but verified" in rec["measured"], rec["measured"]


@pytest.mark.parametrize("sql", ["configuration_jsonb = jsonb_set(configuration_jsonb, '{member_count}', '7')", "configuration_jsonb = jsonb_set(configuration_jsonb, '{fact_value_num}', '9')",
                                 "constituent_facts_array = ARRAY['m0', 'm1']", "constituent_facts_array = ARRAY['m0', 'm1', 'f1']"])
def test_REAL_SQL_a_composite_that_is_not_what_it_claims_reads_fail(world, writer, sql):
    sid = _composite_world(world, writer)
    mutate(sid, sql)
    rec = measure()
    assert rec["v"] == FAIL and "composite roll-up is not what its own values claim" in rec["measured"] and sid in rec["measured"], rec["measured"]


def test_REAL_SQL_an_ordinary_row_dressed_as_a_composite_is_not_exempt(world, writer):
    world(FACTS)
    sid = project(writer, FACTS[0])["signal_id"]
    mutate(sid, "configuration_jsonb = configuration_jsonb || '{\"aggregated\": true, \"fact_key\": \"aggregate_D9\"}'")
    rec = measure()
    assert rec["v"] == FAIL and "composite roll-up is not what its own values claim" in rec["measured"], rec["measured"]


def test_REAL_SQL_a_composite_citing_nothing_is_partial(world, writer):
    sid = _composite_world(world, writer)
    mutate(sid, "constituent_facts_array = '{}'")
    rec = measure()
    assert rec["v"] == PARTIAL and "cite no fact_id" in rec["measured"] and sid in rec["measured"], rec["measured"]


def test_REAL_SQL_the_signals_side_carries_an_explicit_chart_predicate_whatever_the_scope(world, writer):
    world(FACTS + [fact("o1", chart=OTHER, key="elsewhere")])
    ac.psql("UPDATE bodha_msr_signals SET constituent_facts_array = ARRAY['gone'] WHERE chart_id = '" + OTHER + "'")
    ac.set_read_scope({T: dict(where=None, label="whole table (global)")})                                 # an installed scope that names no chart at all
    rec = ac.grade_forwarded_leaves(ff_decl(), ac.forwarded_leaves_read(ff_decl(), COLS, CHART))
    assert rec["v"] == PASS, rec["measured"]                                                              # the other chart's dangling row is not read


def test_REAL_SQL_the_engines_empty_scope_state_reads_no_detector(world):
    world([fact("o1", chart=OTHER, key="elsewhere")])
    sc = ac.mark_empty_scopes(ac.read_scopes([T], R, {T: COLS}, set(), {}, CHART))
    assert sc[T].get("empty") is True and sc[T].get("block")
    ac.set_read_scope(sc)
    rec = ac.grade_forwarded_leaves(ff_decl(), ac.forwarded_leaves_read(ff_decl(), COLS, CHART))
    assert rec["v"] == NO_DET and "NO rows" in rec["measured"] and rec["v"] != PASS, rec["measured"]


# ───────────────────────── the read is bounded and fails closed ─────────────────────────

def _fault(monkeypatch, contains, exc):
    real = ac.psql

    def fake(sql, *a, **k):
        if contains in sql:
            raise exc
        return real(sql, *a, **k)
    monkeypatch.setattr(ac, "psql", fake)


@pytest.mark.parametrize("marker", ["LIMIT 250001", "unnest(m.\"constituent_facts_array\") AS c(fid) WHERE", "CROSS JOIN LATERAL unnest"], ids=["count", "drift-or-nocite", "dangling"])
def test_REAL_SQL_a_statement_timeout_reads_no_detector_with_the_cause_never_pass_or_errored(world, monkeypatch, marker):
    world(FACTS)
    _fault(monkeypatch, marker, ac.Unknown(TIMEOUT))
    rec = measure()
    assert rec["v"] == NO_DET and "statement timeout" in rec["measured"] and rec["v"] not in (PASS, ERRORED), rec["measured"]


def test_REAL_SQL_a_timeout_does_not_hide_an_offender_already_found(world, writer, monkeypatch):
    world(FACTS)
    mutate(project(writer, FACTS[0])["signal_id"], "constituent_facts_array = ARRAY['f1', 'nope']")
    _fault(monkeypatch, "LIMIT 250001", ac.Unknown(TIMEOUT))                                              # the population count times out ...
    rec = measure()
    assert rec["v"] == FAIL and "cited fact_id nope" in rec["measured"]                                   # ... an offender already found stands: a fact, not a claim about the unread


def test_REAL_SQL_any_other_failed_read_is_errored_never_pass(world, monkeypatch):
    world(FACTS)
    _fault(monkeypatch, "LIMIT 250001", ac.Unknown("ERROR:  syntax error at or near \"FROM\""))
    rec = measure()
    assert rec["v"] == ERRORED and "syntax error" in rec["measured"]


def test_REAL_SQL_permission_denied_under_the_census_role_is_no_detector_not_errored(world, monkeypatch):
    world(FACTS)
    _fault(monkeypatch, "CROSS JOIN LATERAL unnest", ac.Unknown("ERROR:  permission denied for table chart_facts"))
    rec = measure()
    assert rec["v"] == NO_DET and "not readable under the census role" in rec["measured"], rec["measured"]


def test_REAL_SQL_python_truthiness_of_an_aggregated_leaf_is_followed(world):
    """The writer skips fact_subject / l1_formula_id when `fvj.get('aggregated')` is TRUTHY (a non-empty string, a non-zero number ...), not only for the boolean true."""
    world([fact("t1", key="ka", jsonb={"aggregated": "yes"}), fact("t2", key="kb", jsonb={"aggregated": 0}), fact("t3", key="kc", jsonb={"aggregated": ""})])
    assert measure()["v"] == PASS


def test_REAL_SQL_a_missing_column_or_table_columns_not_read_is_no_detector(world):
    world(FACTS)
    sc = ac.read_scopes([T], R, {T: COLS}, set(), {}, CHART)
    ac.set_read_scope(sc)
    rec = ac.forwarded_leaves_check(ff_decl(), [c for c in COLS if c != "citation_human"])
    assert rec["v"] == NO_DET and "citation_human" in rec["measured"]
    assert ac.forwarded_leaves_check(ff_decl(), None)["v"] == NO_DET


def test_the_phantom_chart_and_a_malformed_chart_are_refused_before_any_sql():
    with pytest.raises(ac.Unknown, match="phantom"):
        ac._fl_chart("362f9f17-0000-0000-0000-000000000000")
    with pytest.raises(ac.Unknown, match="not a uuid"):
        ac._fl_chart("x'; drop table t; --")
    with pytest.raises(ValueError):
        ac.fl_diag_sql(T, FACTS_FORM, "constituent_facts_array", CHART, ["x'; drop table t; --"])


def test_the_reads_are_one_set_based_statement_each_and_bounded():
    c = "constituent_facts_array"
    sqls = [ac.fl_drift_sql(T, FACTS_FORM, c, CHART), ac.fl_drift_sql(T, VICHARA_FORM, c, CHART), ac.fl_drift_sql(T, DIVISIONAL_FORM, c, CHART), ac.fl_dangling_sql(T, c, CHART),
            ac.fl_nocite_sql(T, FACTS_FORM, c, CHART), ac.fl_composite_sql(T, FACTS_FORM, c, CHART)]
    for q in sqls:
        assert q.rstrip().endswith("LIMIT " + str(ac.FORWARDED_SAMPLE_LIMIT)) and q.count(";") == 0 and "ORDER BY" not in q.split("WHERE", 1)[0]
        assert '"chart_id" = ' in q                                                                       # the signals side carries its own explicit chart predicate (not the installed scope alone)
    assert "NOT EXISTS" in sqls[0] and "JOIN chart_facts f ON f.fact_id::text = c.fid::text" in sqls[0] and "f.ayanamsha_id IN (m.ayanamsha_id, 'INVARIANT')" in sqls[0]
    assert "LIMIT " + str(ac.FORWARDED_COUNT_CAP + 1) in ac.fl_count_sql(T, FACTS_FORM, CHART) and "LIMIT " + str(ac.FORWARDED_COUNT_CAP + 1) in ac.fl_unmeasured_sql(T, [FACTS_FORM], CHART)


# ───────────────────────── the declaration ─────────────────────────

def _entry(**kw):
    e = dict(prose_fields=list(PROSE), forwarded_leaves=ff_decl())
    e.update(kw)
    return e


def test_a_sound_declaration_validates():
    assert ac.forwarded_leaves_problem(_entry()) is None and ac.forwarded_leaves_problem({}) is None
    ac.validate_declarations(dict(version="1", kind_enum=list(ac.DECLARED_KINDS), assets={"a": dict(kind="data", prose_fields=list(PROSE), forwarded_leaves=ff_decl(),
                                                                                                     evidence={"prose_fields": EVIDENCE})}))


@pytest.mark.parametrize("mut", [
    lambda fl: fl.pop("why"), lambda fl: fl.update(extra=1), lambda fl: fl.update(table="x y"), lambda fl: fl.update(cite_column="a;b"), lambda fl: fl.update(forms=[]),
    lambda fl: fl.update(forms=[FACTS_FORM, FACTS_FORM]), lambda fl: fl.update(forms=[dict(FACTS_FORM, form="other")]), lambda fl: fl.update(forms=[dict(FACTS_FORM, rows=dict(column="c", equals=""))]),
    lambda fl: fl.update(forms=[dict(FACTS_FORM, leaf_column="a b")]), lambda fl: fl.update(covers=["signal_headline_text"]), lambda fl: fl.update(covers=PROSE + ["x"]),
    lambda fl: fl.update(why="TBD"), lambda fl: fl.update(why="short"), lambda fl: fl.update(evidence="nope/missing.py:3"), lambda fl: fl.update(evidence="platform/python-sidecar/pipeline/orchestrator/writers/bo_laksana.py"),
    lambda fl: fl.update(evidence="platform/python-sidecar/pipeline/orchestrator/writers/bo_laksana.py:99999"),
])
def test_a_malformed_declaration_is_refused(mut):
    e = _entry()
    mut(e["forwarded_leaves"])
    assert ac.forwarded_leaves_problem(e) is not None
    with pytest.raises(ac.DeclarationsError):
        ac.validate_forwarded_leaves_declaration("assets['x']", e)


# ───────────────────────── the fold into the two Null records, and the rollup ─────────────────────────

NULL = ("Null.schema_default", "Null.blank_rows")
FB = dict(kind="literal_fallback", where="bo_laksana.py:1425", text="literal fallback `or`: ''", entry="signal_headline_text")
DYN = "citation_human: bo_laksana.py:3207 named parameter %(citation_human)s: dynamic row construction in the files that build it could also supply the key (bo_laksana.py:2580 a dict comprehension)"
GOOD = dict(declared=True, v=PASS, table=T, cite_column="constituent_facts_array", chart=CHART, read_scope=f"chart {CHART[:8]}", forms={"chart_facts_row": dict(count=12, at_least=False)},
            composites=dict(count=2, at_least=False), own_fact_rule=ac.FORWARDED_OWN_FACT_RULE, not_compared=["writer-resolved graha / house / target_house"],
            measured="forwarded L1 leaves equal their cited L1 fact on every compared row")
_UNITS = []


def units():
    """The REAL scan units of bo_laksana.py (the scope the census reads): the covered-code spans are computed from their AST."""
    if not _UNITS:
        _UNITS.append(ac.writer_scan_scope("bo_laksana", ["bo_laksana.py"])[0])
    return _UNITS[0]


def _base(**scan):
    ws = dict(v=PARTIAL, problems=[FB], unresolved=[DYN], files=["bo_laksana.py"], entries={}, measured="writer scan NOT clean")
    ws.update(scan)
    rec = dict(v=PARTIAL, clean=True, measured="no schema default on the declared prose column(s); writer literal fallbacks are not measured here")
    return {c: dict(rec) for c in NULL}, ws


def _fold(ffr, decl=None, scan_units=None, **scan):
    out, ws = _base(**scan)
    ctx = dict(forwarded_leaves=ffr, forwarded_decl=decl or ff_decl(), scan_result=ws, scan_units=scan_units if scan_units is not None else units())
    ac._apply_forwarded_leaves(out, list(PROSE), ctx)
    return out


def test_both_null_records_lift_when_the_detector_passes_the_graders_are_clean_and_every_scan_finding_is_covered():
    out = _fold(GOOD)
    for c in NULL:
        assert out[c]["v"] == PASS and out[c]["forwarded_leaves"]["verified"] is True and "PASS earned by the forwarded-leaf detector (measured chart only)" in out[c]["measured"]
        assert out[c]["forwarded_leaves"]["scan_waived"] == dict(empty_fallbacks=1, dynamic_row_caveats=1) and ac.forwarded_leaves_problem_of(out[c], dict(declared_prose_fields=PROSE)) is None
    cells = ac.rollup_asset("L2", {c: out[c] for c in NULL}, dict(declared_prose_fields=PROSE))
    assert cells["Null"]["v"] == PASS and all(ch.get("null_forwarded_leaves_verified") is True for ch in cells["Null"]["checks"]), cells["Null"]


def test_a_non_empty_literal_or_any_other_unresolved_path_keeps_the_cap():
    for scan in (dict(problems=[FB, dict(kind="literal_fallback", where="x.py:9", text="literal default for a missing / empty value (`occupants`): ' — untenanted'", entry="signal_headline_text")]),
                 dict(problems=[dict(FB, kind="constant_write")]), dict(problems=[dict(FB, entry="other")]),
                 dict(unresolved=[DYN, "citation_human: x.py:1 positional parameter 3: no execute call bound to this statement in the scanned scope"]),
                 dict(unresolved=["scope: delegation chain cut at the hop limit (x) holds write SQL the scan did not read"])):
        out = _fold(GOOD, **scan)
        assert all(out[c]["v"] == PARTIAL for c in NULL), scan
        assert "not lifted: the writer scan holds finding(s) the detector does not cover" in out["Null.blank_rows"]["measured"], scan
        assert ac.rollup_asset("L2", {c: out[c] for c in NULL})["Null"]["v"] == PARTIAL


def test_a_failing_detector_flips_blank_rows_to_fail_and_names_the_offenders():
    out = _fold(dict(declared=True, v=FAIL, measured="forwarded L1 leaves DIFFER from L1 (CLAUDE.md N.5: halt-worthy drift): (signal s1, fact_id f1, leaf x: forwarded a vs L1 b)", offenders=dict(drift={})))
    assert out["Null.blank_rows"]["v"] == FAIL and "signal s1, fact_id f1" in out["Null.blank_rows"]["measured"] and out["Null.schema_default"]["v"] == PARTIAL
    assert ac.rollup_asset("L2", {c: out[c] for c in NULL})["Null"]["v"] == FAIL


@pytest.mark.parametrize("v", [PARTIAL, NO_DET, ERRORED])
def test_a_detector_that_is_not_pass_leaves_the_records_and_says_what_it_read(v):
    out = _fold(dict(declared=True, v=v, measured=f"detector says {v}"))
    for c in NULL:
        assert out[c]["v"] == PARTIAL and f"forwarded-leaf detector {v}: detector says {v}" in out[c]["measured"] and out[c]["forwarded_leaves"]["verified"] is False
    assert ac.rollup_asset("L2", {c: out[c] for c in NULL})["Null"]["v"] == PARTIAL


def test_the_data_graders_must_be_clean_and_a_data_level_fail_is_untouched():
    out, ws = _base()
    out["Null.blank_rows"] = dict(out["Null.blank_rows"], clean=False)
    ac._apply_forwarded_leaves(out, list(PROSE), dict(forwarded_leaves=GOOD, forwarded_decl=ff_decl(), scan_result=ws, scan_units=units()))
    assert out["Null.blank_rows"]["v"] == PARTIAL and out["Null.schema_default"]["v"] == PARTIAL
    out, ws = _base()
    out["Null.blank_rows"] = dict(v=FAIL, measured="a blank row")
    ac._apply_forwarded_leaves(out, list(PROSE), dict(forwarded_leaves=GOOD, forwarded_decl=ff_decl(), scan_result=ws, scan_units=units()))
    assert out["Null.blank_rows"]["v"] == FAIL


def test_without_the_declaration_nothing_changes_byte_for_byte():
    out, ws = _base()
    before = json.dumps(out, sort_keys=True)
    ac._apply_forwarded_leaves(out, list(PROSE), dict(scan_result=ws))
    ac._apply_forwarded_leaves(out, list(PROSE), dict(forwarded_leaves=GOOD, scan_result=ws))                 # a result without the declaration is ignored too
    ac._apply_forwarded_leaves(out, [], dict(forwarded_leaves=GOOD, forwarded_decl=ff_decl(), scan_result=ws, scan_units=units()))
    assert json.dumps(out, sort_keys=True) == before


def test_a_forged_or_one_sided_block_does_not_lift_the_cap_in_the_rollup():
    out = _fold(GOOD)
    ms = {c: out[c] for c in NULL}
    facts = dict(declared_prose_fields=PROSE)
    assert ac.rollup_asset("L2", ms, facts)["Null"]["v"] == PASS
    one = dict(ms, **{"Null.blank_rows": dict(ms["Null.blank_rows"], v=PARTIAL, forwarded_leaves=None)})
    assert ac.rollup_asset("L2", one, facts)["Null"]["v"] == PARTIAL
    for mut in (dict(forms={"chart_facts_row": dict(count=0, at_least=False)}, composites=dict(count=0, at_least=False)), dict(forms={}), dict(covers=["citation_human"]), dict(verified=False), dict(v=FAIL), dict(read_scope=""), dict(chart=""),
                dict(scan_waived={}), dict(pinned={"empty_fallbacks": 0, "dynamic_row_caveats": 0}), dict(not_compared=[]), dict(own_fact_rule=""), dict(schema_default_clean=False), dict(detector=""), dict(why=""), dict(evidence="")):
        bad = {c: dict(r, forwarded_leaves=dict(r["forwarded_leaves"], **mut)) for c, r in ms.items()}
        assert ac.rollup_asset("L2", bad, facts)["Null"]["v"] != PASS, mut
    assert ac.rollup_asset("L2", {c: dict(r, basis="declaration") for c, r in ms.items()}, facts)["Null"]["v"] != PASS
    assert ac.rollup_asset("L2", {c: dict(r, inconclusive=True) for c, r in ms.items()}, facts)["Null"]["v"] != PASS
    assert ac.rollup_asset("L2", ms, dict(declared_prose_fields=PROSE + ["x"]))["Null"]["v"] == PARTIAL          # a record cannot narrow the claim
    nob = {c: {k: v for k, v in r.items() if k != "forwarded_leaves"} for c, r in ms.items()}
    assert ac.rollup_asset("L2", nob, facts)["Null"]["v"] == PARTIAL


def _real_scan(unit_list=None):
    unit_list = unit_list if unit_list is not None else units()
    holders = {ac.parse_prose_field(e)[0]: [T] for e in PROSE}
    return ac._lint_module("writer_literal_scan").scan(unit_list, list(PROSE), holders, is_placeholder=ac.ldgr_placeholder_py, sql_texts=ac._sql_texts, parse_entry=ac.parse_prose_field)


def test_the_real_bo_laksana_writer_scan_findings_are_all_covered_and_pinned():
    """Offline, on the REAL writer: the static scan's findings of bo_laksana are exactly the two classes the detector covers, each inside the declared covered code, and their number is the pin (11 + 1)."""
    ws = _real_scan()
    assert ws["v"] == PARTIAL
    decl = json.loads((HERE.parent / "asset_declarations.json").read_text())["assets"]["bo_laksana"]["forwarded_leaves"]
    cover = ac.forwarded_scan_cover(ws, PROSE, decl["covered_scope"], units())
    assert cover["uncovered"] == [] and dict(empty_fallbacks=cover["empty_fallbacks"], dynamic_row_caveats=cover["dynamic_row_caveats"]) == decl["pin"] == dict(empty_fallbacks=11, dynamic_row_caveats=1), cover
    assert len(ws["problems"]) == 11 and len(ws["unresolved"]) == 1


def _units_with_edit(edit):
    """The real scan units with the text of bo_laksana.py edited by `edit(text) -> text` (a COPY of the writer: nothing on disk changes)."""
    src = (SIDECAR / "pipeline" / "orchestrator" / "writers" / "bo_laksana.py").read_text(encoding="utf-8")
    new = edit(src)
    assert new != src
    tree = ast.parse(new)
    out = []
    for u in units():
        out.append(dict(u, tree=tree, nodes=[tree]) if u["rel"] == "bo_laksana.py" else u)
    return out


def test_a_new_empty_fallback_in_the_d9_builder_is_outside_the_covered_code_and_keeps_the_cap():
    """MED-3: `headline = headline or ""` in the D9 cross-check builder forwards nothing that is compared: it is a literal fallback ending `: ''` on a covered entry, but it sits OUTSIDE the declared
    covered functions, so it is uncovered and both Null cells keep the cap."""
    edited = _units_with_edit(lambda t: t.replace("        summary = (\n            f\"category=navamsha_d9_cross_check", "        headline = headline or \"\"\n        summary = (\n            f\"category=navamsha_d9_cross_check", 1))
    ws = _real_scan(edited)
    cover = ac.forwarded_scan_cover(ws, PROSE, SCOPE, edited)
    assert cover["uncovered"] and any("signal_headline_text" in u for u in cover["uncovered"]) and cover["empty_fallbacks"] == 11, cover
    out, _ = _base()
    ffr = GOOD
    c = dict(forwarded_leaves=ffr, forwarded_decl=ff_decl(pin=dict(empty_fallbacks=11, dynamic_row_caveats=1)), scan_result=ws, scan_units=edited)
    ac._apply_forwarded_leaves(out, list(PROSE), c)
    assert all(out[x]["v"] == PARTIAL and "not lifted: the writer scan holds finding(s) the detector does not cover" in out[x]["measured"] for x in NULL), out


def test_a_new_finding_inside_the_covered_code_breaks_the_pin_visibly():
    """A twelfth empty-string fallback INSIDE `_build_signal_row` is covered by location but not by the pin: the cap stays and the cell says the count changed."""
    edited = _units_with_edit(lambda t: t.replace("    fact_cat = str(fact_row.get(\"fact_category\", \"\"))", "    fact_cat = str(fact_row.get(\"fact_category\", \"\"))\n    fact_cat = fact_cat or \"\"", 1))
    ws = _real_scan(edited)
    cover = ac.forwarded_scan_cover(ws, PROSE, SCOPE, edited)
    assert cover["uncovered"] == [] and cover["empty_fallbacks"] > 11, cover
    out, _ = _base()
    ac._apply_forwarded_leaves(out, list(PROSE), dict(forwarded_leaves=GOOD, forwarded_decl=ff_decl(pin=dict(empty_fallbacks=11, dynamic_row_caveats=1)), scan_result=ws, scan_units=edited))
    assert all(out[x]["v"] == PARTIAL and "differ from the declared pin" in out[x]["measured"] for x in NULL), out["Null.blank_rows"]["measured"]


def test_a_finding_whose_covered_function_is_missing_from_the_writer_keeps_the_cap():
    ws = _real_scan()
    cover = ac.forwarded_scan_cover(ws, PROSE, dict(SCOPE, functions=["_build_signal_row", "no_such_function"]), units())
    assert cover["empty_fallbacks"] == 0 and any("declared covered code not found" in u for u in cover["uncovered"])


# ───────────────────────── the registry ─────────────────────────

def test_only_the_two_null_criteria_changed_and_say_what_the_detector_measures():
    for c in NULL:
        e = ac.CRITERION_REGISTRY[c]
        assert e["revision"] == 8 and "forwarded_leaves" in e["applicability"] and "N-189" in e["applicability"]
    assert ac.REGISTRY_REVISION == 26
    for c, e in ac.CRITERION_REGISTRY.items():
        if c not in NULL:
            assert "N-189" not in e["applicability"], c
