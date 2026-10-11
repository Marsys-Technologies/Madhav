"""test_ss_reads_scan_residual.py -- residual detectors D5/D6 of the Build.dag `reads_scan` (bg_concordance), on the real writer and synthetic fixtures.

D5  a NESTED function's SQL name assigned in an ENCLOSING function (`insert_sql = \"\"\"...\"\"\"` then `def _flush(): cur.execute(insert_sql, p)`) is traced when every assignment to it
    in the enclosing chain is a literal. (bg_concordance:246 was "execute() is given SQL that is not traced to a literal ('insert_sql')".)
D6  a prose f-string that merely contains `insert` and `from` ("would insert ~{n} rows from {m} tagged chunks") is not SQL: a SQL string must BEGIN like a statement (after whitespace
    and comments; `{?}` and `(` are kept: never dropped on a guess). It used to read as "a table is named dynamically" (bg_concordance:144) and, for astrological prose, as reads of
    the tables `the`, `moon`, `lagna`, `karakamsha` ... in nine L0/L1 writers.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

import asset_census as ac  # noqa: E402
import test_w2_3_deeper_detectors as w3  # noqa: E402

_HDR = w3._HDR
_CLS = '@register("ka_up")\nclass KaUp(WriterBase):\n    def run(self, ctx):\n'


def _side(monkeypatch, tmp_path, body):
    w3._sidecar(monkeypatch, tmp_path, {"pipeline/orchestrator/writers/ka_up.py": _HDR + body})
    return ac.reads_scan("ka_up", ["ka_up.py"])


# ───────────── the real writer ─────────────

def test_the_real_bg_concordance_now_parses_complete():
    s = ac.reads_scan("bg_concordance", ac.registered_ids("bg_")["bg_concordance"])
    assert s["incomplete"] == [], s["incomplete"]
    assert "classical_text_chunks" in s["reads"], s["reads"]


@pytest.mark.parametrize("aid,words", [("bg_doshas", {"moon", "none"}), ("bg_yogas", {"karakamsha", "affliction", "the"}), ("bg_remedies", {"lagna", "moon"}),
                                       ("bg_prashna_rules", {"east", "north"}), ("ga_structural", {"ul"})])
def test_the_real_prose_that_read_as_tables_no_longer_does(aid, words):
    s = ac.reads_scan(aid, ac.registered_ids(aid[:3])[aid])
    assert not (words & set(s["reads"])), s["reads"]


def test_a_genuinely_dynamic_writer_stays_incomplete(monkeypatch, tmp_path):
    # bo_pramana_mapa was the real example until its table / column names stopped being built at run time (its SQL is now literal module constants); the premise is kept on a synthetic
    # writer whose table name IS an f-string interpolation, so the detector is still proven to flag a dynamic writer, and the literal twin proves it is not flagging everything.
    s = _side(monkeypatch, tmp_path, 'def _read(conn, table):\n    return conn.execute(f"SELECT x FROM {table} WHERE chart_id = %s", (1,))\n' + _CLS + '        _read(ctx.db_conn, ctx.table)\n')
    assert s["incomplete"], s
    s = _side(monkeypatch, tmp_path, 'READ_SQL = "SELECT x FROM bg_up WHERE chart_id = %s"\n' + _CLS + '        ctx.db_conn.execute(READ_SQL, (1,))\n')
    assert s["incomplete"] == [] and list(s["reads"]) == ["bg_up"], s


# ───────────── D5: closure SQL names ─────────────

def test_d5_a_closure_literal_is_traced(monkeypatch, tmp_path):
    s = _side(monkeypatch, tmp_path, _CLS + '        sql = "SELECT x FROM bg_up WHERE a = %s"\n        def _flush(p):\n            ctx.db_conn.execute(sql, p)\n        _flush(1)\n')
    assert s["incomplete"] == [] and "bg_up" in s["reads"], s


def test_d5_a_closure_name_with_a_non_literal_assignment_stays_untraced(monkeypatch, tmp_path):
    s = _side(monkeypatch, tmp_path, _CLS + '        sql = "SELECT x FROM bg_up"\n        sql = ctx.build()\n        def _flush(p):\n            ctx.db_conn.execute(sql, p)\n        _flush(1)\n')
    assert any("not traced to a literal ('sql')" in x for x in s["incomplete"]), s


def test_d5_a_closure_name_augmented_stays_untraced(monkeypatch, tmp_path):
    s = _side(monkeypatch, tmp_path, _CLS + '        sql = "SELECT x FROM bg_up"\n        sql += ctx.tail\n        def _flush(p):\n            ctx.db_conn.execute(sql, p)\n        _flush(1)\n')
    assert any("not traced to a literal ('sql')" in x for x in s["incomplete"]), s


def test_d5_a_name_never_assigned_in_any_enclosing_function_stays_untraced(monkeypatch, tmp_path):
    s = _side(monkeypatch, tmp_path, _CLS + '        def _flush(p):\n            ctx.db_conn.execute(missing_sql, p)\n        _flush(1)\n')
    assert any("not traced to a literal ('missing_sql')" in x for x in s["incomplete"]), s


def test_d5_an_enclosing_functions_PARAMETER_is_not_a_literal(monkeypatch, tmp_path):
    s = _side(monkeypatch, tmp_path, _CLS + '        self.go(ctx.dyn)\n    def go(self, sql):\n        def _flush(p):\n            self.c.execute(sql, p)\n        _flush(1)\n')
    assert any("not traced to a literal ('sql')" in x for x in s["incomplete"]), s


def test_d5_the_enclosing_assignment_is_found_two_levels_up(monkeypatch, tmp_path):
    s = _side(monkeypatch, tmp_path, _CLS + '        sql = "SELECT x FROM bg_deep"\n        def a():\n            def b(p):\n                ctx.db_conn.execute(sql, p)\n            b(1)\n        a()\n')
    assert s["incomplete"] == [] and "bg_deep" in s["reads"], s


# ───────────── D6: a SQL string begins like a statement ─────────────

def test_d6_prose_with_insert_and_from_is_not_sql(monkeypatch, tmp_path):
    s = _side(monkeypatch, tmp_path, _CLS + '        n = 1\n        return f"dry_run=True; would insert ~{n} rows from {n} tagged chunks"\n')
    assert s["incomplete"] == [] and s["reads"] == {}, s


@pytest.mark.parametrize("stmt", ["SELECT a FROM bg_q", "  \\n  SELECT a FROM bg_q", "-- c\\nSELECT a FROM bg_q", "/* c */ SELECT a FROM bg_q", "WITH x AS (SELECT 1) SELECT a FROM bg_q",
                                  "INSERT INTO bg_w SELECT a FROM bg_q", "CREATE OR REPLACE VIEW v AS SELECT a FROM bg_q", "(SELECT a FROM bg_q)", "UPDATE bg_w SET a = 1 FROM bg_q"])
def test_d6_real_statements_are_still_read(monkeypatch, tmp_path, stmt):
    s = _side(monkeypatch, tmp_path, _CLS + f'        ctx.db_conn.execute("{stmt}")\n')
    assert "bg_q" in s["reads"], (stmt, s)


def test_d6_a_dynamic_prefix_is_kept_as_possible_sql_and_stays_incomplete(monkeypatch, tmp_path):
    s = _side(monkeypatch, tmp_path, _CLS + '        ctx.db_conn.execute(f"{ctx.prefix} SELECT a FROM {ctx.t}")\n')
    assert s["incomplete"], s


@pytest.mark.parametrize("frag", ["FROM moon m JOIN (SELECT 1 FROM sun) s ON s.x = m.x", "  join (select 1 from sun) s on true", "UNION SELECT 1 FROM sun", "INTERSECT SELECT 1 FROM sun",
                                  "EXCEPT SELECT 1 FROM sun", "WHERE x IN (SELECT 1 FROM sun)", "AND EXISTS (SELECT 1 FROM sun)", "OR x IN (SELECT 1 FROM sun)", "ON a.x IN (SELECT 1 FROM sun)",
                                  "LEFT JOIN sun s ON true", "RIGHT JOIN sun s ON true", "INNER JOIN sun s ON true", "CROSS JOIN sun s", "FULL JOIN sun s ON true"])
def test_d6_a_clause_fragment_of_a_longer_statement_is_still_scanned(frag):
    """Review: a fragment that starts with a clause keyword and holds a sub-select must not be dropped (it read False after the first D6)."""
    assert ac._sql_statement_text(frag), frag
    assert ac._FROM_JOIN.search(frag) and ac._SQL_CTX.search(frag) or "SELECT" not in frag.upper(), frag


@pytest.mark.parametrize("frag", ["ON CONFLICT (a, b) DO UPDATE SET a = 1", "FROM bg_x", "FROM bg_x x WHERE a = 1", "FROM {?} WHERE a = 1", "FROM (SELECT 1 FROM sun) q", "FROM bg_x AS x JOIN y ON true",
                                  "AND a.x = b.x", "WHERE chart_id = %s", "OR NOT EXISTS (SELECT 1 FROM sun)", "ON a.id = b.id", "NATURAL JOIN sun", "LEFT OUTER JOIN sun s ON true", "JOIN sun s USING (id)",
                                  "UNION ALL SELECT 1", "EXCEPT ALL SELECT 1 FROM sun"])
def test_d6_second_pass_real_clause_continuations_are_sql(frag):
    assert ac._sql_statement_text(frag), frag


@pytest.mark.parametrize("prose", ["And the moon with Saturn from the 7th house", "From {x} with strength {y}", "From the 7th house", "Or the moon in kendra from lagna",
                                   "On the day of the full moon from the lagna", "Where the Moon sits from Saturn", "FROM the Moon with Saturn", "Left of the lagna from the Moon",
                                   "Join the Sun and the Moon from the 4th", "Union of the two lords from the 10th house", "On the Moon, from Saturn", "And, from the Moon"])
def test_d6_second_pass_prose_that_starts_with_a_clause_word_is_not_sql(prose):
    """Review MED: 'And the moon with Saturn from the 7th house' read table `the`; 'From {x} with strength {y}' read a dynamic table. A clause word needs a SQL-shaped continuation."""
    assert not ac._sql_statement_text(prose), prose


@pytest.mark.parametrize("prose", ["And Saturn is aspected with Jupiter from the Moon {x}", "And the moon is in the 7th from Saturn", "Or Saturn is not with Jupiter",
                                   "Where the Moon is in Cancer from Saturn", "On the day Saturn is any planet from the Moon", "And Mars is all with Saturn from the Moon",
                                   "And Mars not in the 7th from the Moon", "Or the Moon is like Venus from Saturn", "And (Saturn is aspected) from the Moon",
                                   "Where Saturn between Mars and Moon from here"])
def test_d6_third_pass_english_is_in_not_any_all_like_between_are_not_sql_comparators(prose):
    """Review MED: `And Saturn is aspected with Jupiter from the Moon {x}` read as SQL (reads_scan reported table `the`): WHERE/AND/OR/ON need a SQL-only comparison."""
    assert not ac._sql_statement_text(prose), prose


@pytest.mark.parametrize("frag", ["WHERE x IN (SELECT 1 FROM sun)", "AND a.x = b.x", "OR a.x <> b.x", "AND a.x != 1", "AND a >= 1", "AND a <= 1", "AND a < 1", "AND a > 1", "AND a::int > 1",
                                  "WHERE a IS NULL", "WHERE a IS NOT NULL", "AND a IS TRUE", "AND a IS NOT FALSE", "AND a IN (1, 2)", "AND a NOT IN (1, 2)", "WHERE name LIKE 'x%'",
                                  "WHERE name NOT ILIKE %s", "AND a BETWEEN 1 AND 5", "AND a BETWEEN %s AND %s", "AND cardinality(r.x) > 0", "AND (a.x = 1 OR b.y = 2)", "WHERE ((a = 1))",
                                  "ON a.id = b.id", "AND NOT EXISTS (SELECT 1 FROM sun)"])
def test_d6_third_pass_the_sql_only_comparisons_are_still_sql(frag):
    assert ac._sql_statement_text(frag), frag


@pytest.mark.parametrize("frag", ["WHERE (a, b) IN (SELECT a, b FROM t)", "AND (SELECT count(*) FROM t) > 0", "AND x IS DISTINCT FROM y AND id IN (SELECT id FROM t)", "AND x IS NOT DISTINCT FROM y",
                                  "AND ({?})", "WHERE %s = ANY(ids)", "WHERE true", "WHERE 1=1", "AND false", "OR TRUE AND a = 1", "WHERE x -> 'k' = 'v'", "AND doc ->> 'k' = 'v'",
                                  "WHERE a ~ '^x'", "AND a ~* 'x'", "AND a !~ 'x'", "AND a !~* 'x'", "AND tags @> ARRAY['a']", "AND a && b", "AND a <@ b", "AND a SIMILAR TO 'x%'",
                                  "AND a NOT SIMILAR TO 'x'", "AND a @@ q", "AND ((SELECT 1 FROM t) = 1)", "WHERE 'x' = ANY(ids)", "AND 1 < a", "WHERE $1 = id", "AND :p = id"])
def test_d6_fourth_pass_real_sql_predicates_that_the_third_pass_rejected_are_scanned_again(frag):
    """Review MED (latent: the 125-writer sweep showed 0 differences): a rejected real predicate is a silent miss, hence a false Build.dag PASS."""
    assert ac._sql_statement_text(frag), frag


@pytest.mark.parametrize("prose", ["And true love from the Moon", "Or false hope from Saturn with Jupiter", "Where the 7th lord is distinct from the 1st", "And Mars is similar to Venus from the Moon",
                                   "And (Saturn, Mars) are aspected from the Moon", "And 7 planets are in kendra from the Moon", "And Saturn is aspected with Jupiter from the Moon {x}",
                                   "Or Saturn is not with Jupiter", "Where the Moon is in Cancer from Saturn"])
def test_d6_fourth_pass_the_prose_rejections_stand(prose):
    assert not ac._sql_statement_text(prose), prose


def test_d6_third_pass_a_stated_limit_IS_NULL_after_a_word_reads_as_sql():
    assert ac._sql_statement_text("And Moon is null from Saturn")           # `IS NULL` is SQL-shaped; no English clause reads like it


def test_d6_second_pass_prose_does_not_reach_the_reads_scan(monkeypatch, tmp_path):
    s = _side(monkeypatch, tmp_path, _CLS + '        n = 1\n        a = "And the moon with Saturn from the 7th house"\n        b = f"From {n} with strength {n}"\n        c = f"And Saturn is aspected with Jupiter from the Moon {n}"\n        return a + b + c\n')
    assert s["incomplete"] == [] and s["reads"] == {}, s


def test_d6_a_known_limit_FROM_two_words_and_a_tail_reads_as_sql():
    """Stated, not hidden: `FROM <ident> <alias>` followed by the end of the text is SQL-shaped, so prose 'From the Moon' (two words after FROM, then the end) is still accepted."""
    assert ac._sql_statement_text("From the Moon")


def test_d6_a_known_limit_the_real_corpus_sweep():
    """The sweep of every candidate text of every registered writer (verb-start texts unchanged): only real SQL fragments start with a clause word (ON CONFLICT, AND EXISTS, AND cardinality)."""
    seen, clause = set(), []
    for pre in ("bg_", "ga_", "bo_", "ka_", "ph_", "mi_"):
        for aid, f in ac.registered_ids(pre).items():
            try:
                units, _ = ac._delegation_scope(aid, f, hops=ac.READS_DELEGATION_HOPS)
                eu, _u = ac._constant_units(units, ac.READS_DELEGATION_HOPS)
            except Exception:
                continue
            for u in units + eu:
                for text, _ln in ac._sql_texts(u):
                    if text in seen or not (ac._SQL_CTX.search(text) and ac._FROM_JOIN.search(text)):
                        continue
                    seen.add(text)
                    if ac._sql_statement_text(text) and not ac._SQL_VERB_START.match(text):
                        clause.append(" ".join(text.split())[:40])
    assert len(seen) > 500 and clause and all(c.upper().startswith(("ON CONFLICT", "AND ")) for c in clause), clause


def test_d6_a_clause_fragment_with_a_subselect_reaches_the_reads_scan(monkeypatch, tmp_path):
    s = _side(monkeypatch, tmp_path, _CLS + '        tail = "FROM moon m JOIN (SELECT 1 FROM sun) s ON s.x = m.x"\n        ctx.db_conn.execute("SELECT a " + tail)\n')
    assert {"moon", "sun"} <= set(s["reads"]), s
    s2 = _side(monkeypatch, tmp_path, _CLS + '        tail = "FROM moon m JOIN (SELECT 1 FROM sun) s ON s.x = m.x"\n        return tail\n')
    assert {"moon", "sun"} <= set(s2["reads"]), s2          # the fragment alone (no execute call) is read too: it is SQL-shaped and names relations


def test_d6_the_statement_start_function():
    for ok in ("SELECT 1 FROM t", "  select 1 from t", "{?} select 1 from t", "(select 1 from t)", "-- x\nWITH a AS (select 1) select * from a", "/* x */ delete from t"):
        assert ac._sql_statement_text(ok), ok
    for no in ("would insert rows from here", "The Moon is in a kendra from lagna", "a SELECT from b"):
        assert not ac._sql_statement_text(no), no
