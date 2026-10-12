"""test_n431_ownership_join_scope.py: the census scope resolver reads the OWNERSHIP-JOIN count form (N-431, ga_structural).

ga_structural has no single target table: its registry count_sql counts the rows of `chart_facts` whose fact_category the ownership table `fact_category_ownership` gives to the asset (migration 410: a JOIN, never a
flat `fact_category IN (...)` list). `_count_scope_tail` cannot read a JOIN, so the asset's reads of chart_facts (Vocab.*, Narr.*, Null.*, Ldgr.*) were unscoped. `_count_scope_resolve` reads the join from its parsed
structure and BUILDS the read tail (chart pin + ownership subselect); any other shape that reads the ownership table is refused with a named cause (the table is blocked, never read unscoped); a count_sql that does
not read the ownership table gets exactly the `_count_scope_tail` answer.

PURE tests (no database): the shapes found in the repo (migration 410, the seed, the T0 manifest), the IN / EXISTS / reversed-join forms, the refusals, the flat-path parity over EVERY manifest count_sql, and the
wiring into read_scopes / vocab_scopes / _table_scope / the read builders.
PLANTED-ROW tests on a DISPOSABLE PostgreSQL (the `disposable_pg` fixture; they run in the CI shard that has PostgreSQL): a read scoped for asset A sees only A's rows.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
from _disposable_pg import disposable_pg, point_psql_at  # noqa: E402,F401  (the session fixture)

REPO = HERE.parents[3]
CHART = ac.CHART_ID
CF, FCO = "chart_facts", "fact_category_ownership"
GA = ("SELECT count(*) AS count FROM chart_facts cf\nJOIN fact_category_ownership fco ON fco.fact_category = cf.fact_category\n"
      "WHERE cf.chart_id = $1 AND fco.owning_asset_id = 'ga_structural'")


def want(asset: str) -> str:
    return f" WHERE chart_id = $1 AND fact_category IN (SELECT fco.fact_category FROM fact_category_ownership fco WHERE fco.owning_asset_id = '{asset}')"


# ───────────────────────── the shapes found in the repo ─────────────────────────

def _migration_410_count_sql() -> str:
    text = (REPO / "platform" / "supabase" / "migrations" / "410_ga_structural_category_ownership.sql").read_text(encoding="utf-8")
    m = re.search(r"SET count_sql = \$sql\$(.*?)\$sql\$", text, re.S)
    assert m, "migration 410 no longer carries the ownership-join count_sql"
    return m.group(1)


def _seed_count_sql() -> str:
    text = (REPO / "platform" / "scripts" / "seed" / "asset_registry_seed.ts").read_text(encoding="utf-8")
    m = re.search(r"count_sql: `(SELECT count\(\*\) AS count FROM chart_facts cf\nJOIN fact_category_ownership.*?)`", text, re.S)
    assert m
    return m.group(1)


def _manifest_count_sqls() -> dict:
    p = REPO / "00_ARCHITECTURE" / "control" / "NIRMANA_T0_MANIFEST_v1_1.json"
    return {a["asset_id"]: (a["registry_contract"].get("count_sql") or "") for a in json.loads(p.read_text(encoding="utf-8"))["assets"]}


@pytest.mark.parametrize("sql", [_migration_410_count_sql(), _seed_count_sql(), _manifest_count_sqls()["ga_structural"], GA], ids=["migration-410", "seed", "t0-manifest", "literal"])
def test_every_ownership_join_count_sql_found_in_the_repo_resolves_to_the_built_tail(sql):
    assert ac._count_scope_resolve(sql, "chart_facts") == (want("ga_structural"), None)
    assert ac._count_scope_resolve(sql, "CHART_FACTS") == (want("ga_structural"), None)
    assert ac._count_scope_resolve(sql, '"chart_facts"') == (want("ga_structural"), None)
    assert ac._count_scope_resolve(sql, "fact_category_ownership") == (None, None)            # the reference table has no row scope
    assert ac._count_scope_resolve(sql, "some_other_table") == (None, None)


def test_the_only_ownership_count_sql_in_the_manifest_is_ga_structural():
    got = {a for a, s in _manifest_count_sqls().items() if ac._OWN_READS.search(s)}
    assert got == {"ga_structural"}


def test_the_built_tail_is_chart_pinned_and_binds_like_every_other_tail():
    tail, _ = ac._count_scope_resolve(GA, "chart_facts")
    assert ac._chart_pinned(tail) and ac._tail_mentions_chart(tail)
    bound = ac._bind_chart(tail, CHART)
    assert bound == f" WHERE chart_id = '{CHART}' AND fact_category IN (SELECT fco.fact_category FROM fact_category_ownership fco WHERE fco.owning_asset_id = 'ga_structural')"
    with pytest.raises(ac.Unknown):
        ac._bind_chart(tail, "362f9f17-0000-0000-0000-000000000000")                         # the phantom chart is still refused


# ───────────────────────── the recognised forms ─────────────────────────

RECOGNISED = [
    # join, chart pin and asset restriction in WHERE, no aliases
    "SELECT count(*) FROM chart_facts JOIN fact_category_ownership ON fact_category_ownership.fact_category = chart_facts.fact_category WHERE chart_facts.chart_id = $1 AND fact_category_ownership.owning_asset_id = 'ga_x'",
    # asset restriction in ON, AS aliases, INNER JOIN, uuid cast, count(1), trailing semicolon, comment
    "SELECT count(1) FROM chart_facts AS cf INNER JOIN fact_category_ownership AS o ON o.fact_category = cf.fact_category AND o.owning_asset_id = 'ga_x' WHERE cf.chart_id = $1::uuid; -- tail",
    # ownership table first, the equality reversed, public. prefixes, lower-case keywords, parenthesised conjuncts
    "select count(*) from public.fact_category_ownership o join public.chart_facts f on (f.fact_category = o.fact_category) where (o.owning_asset_id = 'ga_x') and (f.chart_id = $1)",
    # unqualified chart pin and asset column
    "SELECT count(*) FROM chart_facts cf JOIN fact_category_ownership fco ON fco.fact_category = cf.fact_category WHERE chart_id = $1 AND owning_asset_id = 'ga_x'",
    # IN subselect (qualified, unqualified)
    "SELECT count(*) FROM chart_facts WHERE chart_id = $1 AND fact_category IN (SELECT fact_category FROM fact_category_ownership WHERE owning_asset_id = 'ga_x')",
    "SELECT count(*) AS n FROM chart_facts cf WHERE fact_category IN (SELECT o.fact_category FROM fact_category_ownership o WHERE o.owning_asset_id = 'ga_x') AND cf.chart_id = $1",
    # EXISTS subselect (both inner orders)
    "SELECT count(*) FROM chart_facts cf WHERE cf.chart_id = $1 AND EXISTS (SELECT 1 FROM fact_category_ownership fco WHERE fco.fact_category = cf.fact_category AND fco.owning_asset_id = 'ga_x')",
    "SELECT count(*) FROM chart_facts cf WHERE cf.chart_id = $1 AND EXISTS (SELECT * FROM fact_category_ownership fco WHERE fco.owning_asset_id = 'ga_x' AND cf.fact_category = fco.fact_category)",
]


@pytest.mark.parametrize("sql", RECOGNISED)
def test_each_recognised_form_resolves_to_the_same_built_tail(sql):
    assert ac._count_scope_resolve(sql, "chart_facts") == (want("ga_x"), None)
    assert ac._count_scope_resolve(sql, "fact_category_ownership") == (None, None)


def test_the_asset_literal_is_taken_from_the_parse_not_from_a_fixed_name():
    assert ac._count_scope_resolve(GA.replace("ga_structural", "ga_other9"), "chart_facts")[0] == want("ga_other9")


# ───────────────────────── the refusals: a named cause, never an unscoped tail ─────────────────────────

BASE_J = "SELECT count(*) FROM chart_facts cf JOIN fact_category_ownership fco ON fco.fact_category = cf.fact_category WHERE cf.chart_id = $1 AND fco.owning_asset_id = 'ga_x'"
REFUSED = {
    "left join": BASE_J.replace("JOIN fact_category_ownership", "LEFT JOIN fact_category_ownership"),
    "right join": BASE_J.replace("JOIN fact_category_ownership", "RIGHT JOIN fact_category_ownership"),
    "full join": BASE_J.replace("cf JOIN", "cf FULL JOIN"),
    "comma join": "SELECT count(*) FROM chart_facts cf, fact_category_ownership fco WHERE fco.fact_category = cf.fact_category AND cf.chart_id = $1 AND fco.owning_asset_id = 'ga_x'",
    "third table": BASE_J.replace("WHERE", "JOIN other_t t ON t.id = cf.id WHERE"),
    "no asset restriction": "SELECT count(*) FROM chart_facts cf JOIN fact_category_ownership fco ON fco.fact_category = cf.fact_category WHERE cf.chart_id = $1",
    "two asset restrictions": BASE_J + " AND fco.owning_asset_id = 'ga_y'",
    "no chart pin": "SELECT count(*) FROM chart_facts cf JOIN fact_category_ownership fco ON fco.fact_category = cf.fact_category WHERE fco.owning_asset_id = 'ga_x'",
    "two chart pins": BASE_J + " AND cf.chart_id = $1",
    "extra predicate": BASE_J + " AND cf.fact_category <> 'x'",
    "OR": BASE_J.replace("cf.chart_id = $1 AND", "cf.chart_id = $1 OR"),
    "asset not equals": BASE_J.replace("fco.owning_asset_id = 'ga_x'", "fco.owning_asset_id <> 'ga_x'"),
    "asset IN list": BASE_J.replace("fco.owning_asset_id = 'ga_x'", "fco.owning_asset_id IN ('ga_x','ga_y')"),
    "asset literal with a quote": BASE_J.replace("'ga_x'", "'ga_x''; DROP TABLE t; --'"),
    "asset literal not an identifier": BASE_J.replace("'ga_x'", "'ga x'"),
    "no join equality": BASE_J.replace("ON fco.fact_category = cf.fact_category", "ON true"),
    "join on the wrong column": BASE_J.replace("ON fco.fact_category = cf.fact_category", "ON fco.fact_category = cf.fact_subject"),
    "join links a table to itself": BASE_J.replace("fco.fact_category = cf.fact_category", "cf.fact_category = cf.fact_category"),
    "chart pin on the ownership table": BASE_J.replace("cf.chart_id = $1", "fco.chart_id = $1"),
    "asset restriction qualified by the fact table": BASE_J.replace("fco.owning_asset_id", "cf.owning_asset_id"),
    "a different fact table": BASE_J.replace("chart_facts", "other_facts"),
    "ownership table is the counted table": "SELECT count(*) FROM fact_category_ownership WHERE owning_asset_id = 'ga_x' AND chart_id = $1",
    "a sum": "SELECT (" + BASE_J + ") + (SELECT count(*) FROM chart_facts WHERE chart_id = $1)",
    "group by": BASE_J + " GROUP BY cf.fact_category",
    "limit": BASE_J + " LIMIT 5",
    "not a count": "SELECT cf.fact_category FROM chart_facts cf JOIN fact_category_ownership fco ON fco.fact_category = cf.fact_category WHERE cf.chart_id = $1 AND fco.owning_asset_id = 'ga_x'",
    "in subselect with an extra predicate": "SELECT count(*) FROM chart_facts WHERE chart_id = $1 AND fact_category IN (SELECT fact_category FROM fact_category_ownership WHERE owning_asset_id = 'ga_x' AND true)",
    "in subselect over the wrong column": "SELECT count(*) FROM chart_facts WHERE chart_id = $1 AND fact_subject IN (SELECT fact_category FROM fact_category_ownership WHERE owning_asset_id = 'ga_x')",
    "not in subselect": "SELECT count(*) FROM chart_facts WHERE chart_id = $1 AND fact_category NOT IN (SELECT fact_category FROM fact_category_ownership WHERE owning_asset_id = 'ga_x')",
    "not exists": "SELECT count(*) FROM chart_facts cf WHERE cf.chart_id = $1 AND NOT EXISTS (SELECT 1 FROM fact_category_ownership fco WHERE fco.fact_category = cf.fact_category AND fco.owning_asset_id = 'ga_x')",
    "exists uncorrelated": "SELECT count(*) FROM chart_facts cf WHERE cf.chart_id = $1 AND EXISTS (SELECT 1 FROM fact_category_ownership fco WHERE fco.owning_asset_id = 'ga_x' AND true)",
    "in subselect and join": BASE_J + " AND cf.fact_category IN (SELECT fact_category FROM fact_category_ownership WHERE owning_asset_id = 'ga_x')",
    "subselect in the select list": "SELECT (SELECT count(*) FROM fact_category_ownership WHERE owning_asset_id = 'ga_x') FROM chart_facts WHERE chart_id = $1",
}


@pytest.mark.parametrize("name", sorted(REFUSED))
def test_a_shape_the_resolver_does_not_recognise_is_refused_with_the_named_cause(name):
    sql = REFUSED[name]
    tail, refused = ac._count_scope_resolve(sql, "chart_facts")
    assert tail is None and refused and refused.startswith("NO_DETECTOR - " + ac.OWNERSHIP_REFUSED), (name, tail, refused)
    assert "not read unscoped" in refused
    assert ac._count_scope_resolve(sql, "fact_category_ownership") == (None, None)             # the reference table is never refused


def test_a_refusal_never_falls_through_to_the_flat_resolver():
    # the flat resolver reads `FROM chart_facts a JOIN x ON true` as "unreadable" (None): for an ownership-reading count that None must become a refusal
    sql = REFUSED["left join"]
    assert ac._count_scope_tail(sql, "chart_facts") is None
    assert ac._count_scope_resolve(sql, "chart_facts")[1]


def test_a_join_that_does_not_read_the_ownership_table_is_not_this_resolvers_business():
    odd = "SELECT count(*) FROM chart_facts a JOIN x ON true"
    assert ac._count_scope_resolve(odd, "chart_facts") == (ac._count_scope_tail(odd, "chart_facts"), None) == (None, None)


# ───────────────────────── flat-list / single-table / sum assets: EXACTLY the old tail ─────────────────────────

FLAT = [
    "SELECT count(*) FROM t",
    "SELECT count(*) FROM t WHERE chart_id = $1",
    "SELECT count(*) AS count FROM chart_facts WHERE chart_id = $1 AND fact_category IN ('a','b')",
    "SELECT count(*) FROM chart_facts WHERE chart_id = $1 AND (fact_category LIKE 'graha_%' OR fact_category = 'x')",
    "SELECT (SELECT count(*) FROM a WHERE chart_id = $1) + (SELECT count(*) FROM b WHERE chart_id = $1) AS n",
    "WITH p AS (SELECT $1::uuid AS cid) SELECT (SELECT count(*) FROM a x, p WHERE x.chart_id = p.cid) + (SELECT count(*) FROM b y, p WHERE y.chart_id = p.cid) AS count",
    "SELECT count(*) FROM chart_facts a JOIN x ON true",
    "SELECT count(*) FROM chart_facts WHERE chart_id = $1 GROUP BY fact_category",
    "SELECT 0 AS count",
    "",
]


@pytest.mark.parametrize("sql", FLAT)
@pytest.mark.parametrize("table", ["t", "a", "b", "chart_facts", "fact_category_ownership", "zzz"])
def test_a_count_sql_that_does_not_read_the_ownership_table_gets_exactly_the_flat_tail(sql, table):
    assert ac._count_scope_resolve(sql, table) == (ac._count_scope_tail(sql, table), None)


def test_every_manifest_count_sql_except_the_ownership_one_resolves_exactly_as_before():
    n = 0
    for aid, sql in _manifest_count_sqls().items():
        if ac._OWN_READS.search(sql):
            continue
        for t in set(ac._count_tables(sql)) | {"chart_facts", "zzz"}:
            assert ac._count_scope_resolve(sql, t) == (ac._count_scope_tail(sql, t), None), (aid, t)
            n += 1
    assert n > 100


# ───────────────────────── the wiring: which reads use the tail ─────────────────────────

R_GA = dict(count_sql=GA)
COLS = {"chart_facts": ["id", "chart_id", "fact_category", "fact_subject", "fact_value_text"], "fact_category_ownership": ["fact_category", "owning_asset_id", "created_at"]}
SHARED = {"chart_facts"}


def test_vocab_scopes_scopes_the_shared_chart_facts_by_the_ownership_join():
    got = ac.vocab_scopes(["chart_facts", "fact_category_ownership"], R_GA, {}, SHARED, {}, CHART)
    assert set(got) == {"chart_facts"}
    assert got["chart_facts"]["where"] == f"chart_id = '{CHART}' AND fact_category IN (SELECT fco.fact_category FROM fact_category_ownership fco WHERE fco.owning_asset_id = 'ga_structural')"
    assert "registry count_sql predicate" in got["chart_facts"]["label"] and not got["chart_facts"].get("block")


def test_a_declared_produced_filter_still_beats_the_count_sql_scope():
    decl = {"produced_tables": [dict(table="chart_facts", filter=dict(column="fact_category", equals="dasha_scope_cap"), why="the writer's own row set")]}
    got = ac.vocab_scopes(["chart_facts"], R_GA, {}, SHARED, dict(decl, kind="data"), CHART)
    assert got["chart_facts"]["where"] == "(\"fact_category\"::text = 'dasha_scope_cap')"


def test_read_scopes_gives_chart_facts_the_chart_and_the_ownership_restriction_and_leaves_the_ownership_table_whole():
    sc = ac.read_scopes(["chart_facts", "fact_category_ownership"], R_GA, COLS, SHARED, {}, CHART)
    w = sc["chart_facts"]["where"]
    assert w.startswith(f"(\"chart_id\" = '{CHART}')") and "fact_category IN (SELECT fco.fact_category FROM fact_category_ownership fco WHERE fco.owning_asset_id = 'ga_structural')" in w
    assert not sc["chart_facts"].get("block")
    assert sc["fact_category_ownership"] == dict(where=None, label="whole table (global: no chart_id column)")


def test_read_scopes_blocks_an_unrecognised_ownership_shape_instead_of_reading_it_whole():
    bad = dict(count_sql=REFUSED["left join"])
    for shared in (SHARED, set()):                                    # shared or not: the table is not read
        sc = ac.read_scopes(["chart_facts", "fact_category_ownership"], bad, COLS, shared, {}, CHART)
        assert sc["chart_facts"]["where"] is None and sc["chart_facts"]["block"].startswith("NO_DETECTOR - " + ac.OWNERSHIP_REFUSED)
        assert sc["fact_category_ownership"] == dict(where=None, label="whole table (global: no chart_id column)")
    vs = ac.vocab_scopes(["chart_facts"], bad, {}, SHARED, {}, CHART)
    assert vs["chart_facts"]["where"] is None and vs["chart_facts"]["block"].startswith("NO_DETECTOR - " + ac.OWNERSHIP_REFUSED)


def test_a_blocked_scope_is_what_the_read_builders_refuse_on(monkeypatch):
    bad = dict(count_sql=REFUSED["comma join"])
    sc = ac.read_scopes(["chart_facts"], bad, COLS, SHARED, {}, CHART)
    try:
        ac.set_read_scope(sc)
        assert ac._scope_block("chart_facts") and ac._scope_block("chart_facts").startswith("NO_DETECTOR - " + ac.OWNERSHIP_REFUSED)
        monkeypatch.setattr(ac, "scalar", lambda q: pytest.fail("a blocked scope must not be probed"))
        assert ac.mark_empty_scopes(sc) is sc
    finally:
        ac.set_read_scope(None)


def test_table_scope_returns_the_built_tail_chart_scoped_and_none_for_a_refused_shape():
    own = {"chart_facts": (COLS["chart_facts"], None, None), "fact_category_ownership": (COLS["fact_category_ownership"], None, None)}
    tail, label = ac._table_scope("chart_facts", R_GA, own, SHARED)
    assert tail == want("ga_structural") and label == "chart-scoped by count_sql"
    assert ac._table_scope("chart_facts", dict(count_sql=REFUSED["left join"]), own, SHARED) is None
    assert ac._table_scope("chart_facts", dict(count_sql=REFUSED["left join"]), own, set()) is None          # even when the table is not shared: the ownership shape is refused


def test_the_scope_reaches_every_read_builder_of_chart_facts():
    sc = ac.read_scopes(["chart_facts"], R_GA, COLS, SHARED, {}, CHART)
    clause = "fact_category IN (SELECT fco.fact_category FROM fact_category_ownership fco WHERE fco.owning_asset_id = 'ga_structural')"
    try:
        ac.set_read_scope(sc)
        assert clause in ac.label_distinct_sql("chart_facts", "fact_subject")
        assert clause in ac._sw("chart_facts", "x IS NOT NULL") and clause in ac._where_scope("chart_facts")
    finally:
        ac.set_read_scope(None)
    w = sc["chart_facts"]["where"]
    assert ac.vocab_batch_sql("chart_facts", [("fact_subject", "text"), ("fact_value_text", "text")], w).count(clause) == 2
    assert clause in ac.vocab_probe_sql("chart_facts", "fact_subject", "text", w)
    assert clause in ac.prose_row_counts_sql("chart_facts", ["fact_value_text"], ac._bind_chart(want("ga_structural"), CHART))


def test_the_flat_wiring_is_untouched():
    flat = dict(count_sql="SELECT count(*) FROM chart_facts WHERE chart_id = $1 AND fact_category IN ('dasha','sade_sati')")
    assert ac.vocab_scopes(["chart_facts"], flat, {}, SHARED, {}, CHART)["chart_facts"]["where"] == f"chart_id = '{CHART}' AND fact_category IN ('dasha','sade_sati')"
    assert ac._table_scope("chart_facts", flat, {"chart_facts": (COLS["chart_facts"], None, None)}, SHARED) == (" WHERE chart_id = $1 AND fact_category IN ('dasha','sade_sati')", "chart-scoped by count_sql")


# ───────────────────────── PLANTED ROWS on a DISPOSABLE PostgreSQL (CI shard with PostgreSQL; not run on the local machine) ─────────────────────────

OTHER = "11111111-2222-3333-4444-555555555555"


def _q(s):
    return "'" + s.replace("'", "''") + "'"


@pytest.fixture
def planted(disposable_pg, monkeypatch):
    """chart_facts with rows of TWO assets' categories (ga_structural: cat_a1 / cat_a2; ga_other: cat_b) on the measured chart, one ga_structural row on ANOTHER chart, and the ownership table."""
    point_psql_at(disposable_pg, monkeypatch)
    ac.set_read_scope(None)
    ac.psql("DROP TABLE IF EXISTS chart_facts")
    ac.psql("DROP TABLE IF EXISTS fact_category_ownership")
    ac.psql("CREATE TABLE fact_category_ownership (fact_category text NOT NULL, owning_asset_id text NOT NULL, created_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY (fact_category, owning_asset_id))")
    ac.psql("INSERT INTO fact_category_ownership (fact_category, owning_asset_id) VALUES ('cat_a1','ga_structural'), ('cat_a2','ga_structural'), ('cat_b','ga_other')")
    ac.psql("CREATE TABLE chart_facts (id serial PRIMARY KEY, chart_id uuid NOT NULL, fact_category text NOT NULL, fact_subject text, fact_value_text text, citation_human text)")

    def put(rows):
        """rows: (chart, category, subject, citation_human)."""
        for chart, cat, subj, cit in rows:
            ac.psql(f"INSERT INTO chart_facts (chart_id, fact_category, fact_subject, citation_human) VALUES ('{chart}', {_q(cat)}, {_q(subj)}, {'NULL' if cit is None else _q(cit)})")

    yield put
    ac.set_read_scope(None)
    ac.psql("DROP TABLE IF EXISTS chart_facts")
    ac.psql("DROP TABLE IF EXISTS fact_category_ownership")


def _sample_values(where):
    got = ac.vocab_fetch_samples("chart_facts", [("fact_subject", "text")], where)["fact_subject"]
    return sorted(got["values"])


def _scopes_for(count_sql):
    return ac.read_scopes(["chart_facts", "fact_category_ownership"], dict(count_sql=count_sql), COLS, SHARED, {}, CHART)


A_SQL = GA
B_SQL = GA.replace("ga_structural", "ga_other")


def test_REAL_SQL_a_read_scoped_for_asset_a_sees_only_a_rows(planted):
    planted([(CHART, "cat_a1", "Sun", "ok"), (CHART, "cat_a2", "Moon", "ok"), (CHART, "cat_b", "MARS", ""), (OTHER, "cat_a1", "KETU", "")])
    wa, wb = _scopes_for(A_SQL)["chart_facts"]["where"], _scopes_for(B_SQL)["chart_facts"]["where"]
    assert _sample_values(wa) == ["Moon", "Sun"]                       # B's MARS and the other chart's KETU are not A's
    assert _sample_values(wb) == ["MARS"]
    assert _sample_values(None) == ["KETU", "MARS", "Moon", "Sun"]     # the unscoped read (what ga_structural got before) sees everything
    assert int(ac.scalar(f"SELECT count(*) FROM chart_facts WHERE {wa}")) == 2


def test_REAL_SQL_a_value_planted_in_b_does_not_change_a_and_one_planted_in_a_does(planted):
    planted([(CHART, "cat_a1", "Sun", "ok"), (CHART, "cat_b", "MARS", None)])
    wa = _scopes_for(A_SQL)["chart_facts"]["where"]
    ac.set_read_scope(_scopes_for(A_SQL))
    assert ac.psql(ac.label_distinct_sql("chart_facts", "fact_subject")) == [["Sun"]]
    assert ac.prose_row_counts("chart_facts", ["citation_human"], ac._bind_chart(ac._table_scope("chart_facts", dict(count_sql=A_SQL), {"chart_facts": (COLS["chart_facts"], None, None)}, SHARED)[0], CHART)) \
        == {"citation_human": dict(checkable=1, blank=0)}
    planted([(CHART, "cat_b", "KETU", "")])                              # more in B (a blank citation too): A is unchanged
    assert _sample_values(wa) == ["Sun"]
    assert ac.psql(ac.label_distinct_sql("chart_facts", "fact_subject")) == [["Sun"]]
    planted([(CHART, "cat_a2", "RAHU", "")])                             # one in A's category: A sees it
    assert _sample_values(wa) == ["RAHU", "Sun"]
    assert sorted(r[0] for r in ac.psql(ac.label_distinct_sql("chart_facts", "fact_subject"))) == ["RAHU", "Sun"]
    tail = ac._table_scope("chart_facts", dict(count_sql=A_SQL), {"chart_facts": (COLS["chart_facts"], None, None)}, SHARED)[0]
    assert ac.prose_row_counts("chart_facts", ["citation_human"], ac._bind_chart(tail, CHART)) == {"citation_human": dict(checkable=1, blank=1)}


def test_REAL_SQL_the_built_tail_selects_exactly_the_rows_the_registry_count_counts(planted):
    planted([(CHART, "cat_a1", "Sun", "x"), (CHART, "cat_a2", "Moon", "x"), (CHART, "cat_a2", "Mars", "x"), (CHART, "cat_b", "Rahu", "x"), (OTHER, "cat_a1", "Ketu", "x")])
    registry = int(ac.scalar(ac._bind_chart(A_SQL, CHART)))
    tail = ac._bind_chart(ac._count_scope_resolve(A_SQL, "chart_facts")[0], CHART)
    assert registry == int(ac.scalar(f"SELECT count(*) FROM chart_facts{tail}")) == 3


def test_REAL_SQL_every_recognised_form_counts_the_same_rows_as_its_built_tail(planted):
    planted([(CHART, "cat_a1", "Sun", "x"), (CHART, "cat_a2", "Moon", "x"), (CHART, "cat_b", "Rahu", "x"), (OTHER, "cat_a1", "Ketu", "x")])
    for sql in RECOGNISED:
        sql = sql.replace("ga_x", "ga_structural").replace(" -- tail", "")
        tail = ac._bind_chart(ac._count_scope_resolve(sql, "chart_facts")[0], CHART)
        assert int(ac.scalar(ac._bind_chart(sql, CHART))) == int(ac.scalar(f"SELECT count(*) FROM chart_facts{tail}")) == 2, sql


def test_REAL_SQL_an_unrecognised_ownership_shape_is_not_read_at_all(planted):
    planted([(CHART, "cat_a1", "Sun", "ok"), (CHART, "cat_b", "MARS", "")])
    sc = _scopes_for(REFUSED["left join"])
    assert sc["chart_facts"]["where"] is None and sc["chart_facts"]["block"]
    ac.set_read_scope(sc)
    try:
        assert ac._scope_block("chart_facts")                              # the builders that honour the block refuse here; nothing falls back to the whole table
        assert ac._table_scope("chart_facts", dict(count_sql=REFUSED["left join"]), {"chart_facts": (COLS["chart_facts"], None, None)}, SHARED) is None
    finally:
        ac.set_read_scope(None)
