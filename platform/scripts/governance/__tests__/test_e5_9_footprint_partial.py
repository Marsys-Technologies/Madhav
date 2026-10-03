"""test_e5_9_footprint_partial.py -- Suvarna E5.9: the footprint reports its own scope (complete | partial).

asset_registry carries one target_table per asset, so the write set _footprint_report feeds the FK closure is only what the
registry shows. A writer can write more tables; an asset can declare none; a writer's tables may not be determinable.
Any of those makes the footprint PARTIAL and has_blockers "unknown" (never false). Offline: writers are tmp-dir fixtures,
the "database" is a fake that answers the two catalog SELECTs; the real writer tree is read (never imported) by the
anchor tests at the bottom.
"""
from __future__ import annotations

import pathlib
import sys
import textwrap

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import suvarna_level_wave as slw  # noqa: E402

REAL_REPO = HERE.parents[3]
WRITERS = slw.WRITERS_REL


def write(repo: pathlib.Path, rel: str, body: str) -> pathlib.Path:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(body), encoding="utf-8")
    return p


def writer(repo, asset_id, body):
    return write(repo, f"{WRITERS}/{asset_id}.py", body)


HELPER_FIXTURE = '''
    def replace_prior_chart_facts(conn, rows):
        conn.execute("DELETE FROM chart_facts WHERE chart_id = %s", [1])

    def replace_prior_two(conn, rows):
        conn.execute("DELETE FROM public.t_one WHERE a=1")
        conn.execute("DELETE FROM public.t_two WHERE a=1")

    def clear_table_for_chart(conn, table, chart_id):
        return conn.execute(f"DELETE FROM {table} WHERE chart_id = %s", [chart_id])

    def replace_prior_dynamic(conn, obj):
        conn.execute(f"DELETE FROM {obj.table_name} WHERE a=1")
'''


@pytest.fixture
def repo(tmp_path):
    write(tmp_path, "platform/python-sidecar/ga_writers/_idempotency.py", HELPER_FIXTURE)
    write(tmp_path, "platform/python-sidecar/bodha_writers/_idempotency.py", "def noop():\n    return 1\n")
    return tmp_path


def row(asset_id, target):
    return {"asset_id": asset_id, "target_table": target}


class FakeConn:
    """Answers the two catalog SELECTs _footprint_report issues; records every statement."""

    def __init__(self, fk_rows=(), tables=()):
        self.fk_rows, self.tables, self.sql = list(fk_rows), list(tables), []

    def cursor(self):
        conn = self

        class Cur:
            def execute(self, sql, params=None):
                conn.sql.append(sql)
                self._rows = conn.fk_rows if "FROM pg_constraint" in sql else [(t,) for t in conn.tables]

            def fetchall(self):
                return self._rows

            def close(self):
                pass
        return Cur()


NO_FK = ("c_fkey", "public.tbl_b", "public.tbl_a", "n", "a", ["a_id"], ["a_id"], False, False, None, None, False, False)


def conn_for(*tables, fk=(NO_FK,)):
    return FakeConn(fk_rows=fk, tables=[f"public.{t}" for t in tables])


# ───────────────────────── the static scan: forms it resolves ─────────────────────────

@pytest.mark.parametrize("sql,expected", [
    ('"INSERT INTO t_a (x) VALUES (1)"', ["public.t_a"]),
    ('"INSERT INTO public.t_a (x) VALUES (1)"', ["public.t_a"]),
    ('"insert into public.\\"t_a\\" (x) values (1)"', ["public.t_a"]),
    ('"DELETE FROM t_a WHERE x = 1"', ["public.t_a"]),
    ('"UPDATE t_a SET x = 1"', ["public.t_a"]),
    ('"UPDATE public.t_a AS a SET x = 1"', ["public.t_a"]),
    ('"TRUNCATE TABLE t_a"', ["public.t_a"]),
    ('"TRUNCATE t_a"', ["public.t_a"]),
    ('"COPY t_a (x, y) FROM STDIN"', ["public.t_a"]),
    ('"COPY t_a FROM STDIN"', ["public.t_a"]),
    ('"INSERT INTO other.t_a (x) VALUES (1)"', ["other.t_a"]),
    ('"DELETE FROM " "t_a" " WHERE x"', ["public.t_a"]),                 # implicit concatenation
    ('"DELETE FROM " + "t_a"', ["public.t_a"]),                          # explicit + concatenation of literals
    ('"INSERT INTO t_a (x) VALUES (1) ON CONFLICT (x) DO UPDATE SET x = 2"', ["public.t_a"]),   # DO UPDATE SET is not a table
    ('"DELETE FROM t_a; INSERT INTO t_b (x) VALUES (1)"', ["public.t_a", "public.t_b"]),
])
def test_scan_resolves_literal_forms(repo, sql, expected):
    writer(repo, "a_x", f"x = {sql}\n")
    assert slw.scan_writer_tables("a_x", repo)["tables"] == expected


def test_scan_ignores_docstrings_comments_and_read_only_sql(repo):
    writer(repo, "a_x", '''
        """Module doc: this writer will INSERT INTO t_doc and DELETE FROM t_doc2."""
        # DELETE FROM t_comment
        class W:
            """Class doc: UPDATE t_cls SET x = 1"""
            def run(self):
                """Method doc: COPY t_fn FROM STDIN"""
                log = "Update asset_throughput after the copy of rows"
                "bare prose: INSERT INTO t_bare (x)"
                return "SELECT * FROM t_read WHERE x = 1"
        w = "INSERT INTO t_real (x) VALUES (1)"
        ''')
    assert slw.scan_writer_tables("a_x", repo)["tables"] == ["public.t_real"]


def test_scan_resolves_module_and_class_constants_in_f_strings(repo):
    writer(repo, "a_x", '''
        TABLE = "t_mod"
        class W:
            CLS_TABLE = "t_cls"
            def run(self, conn):
                conn.execute(f"DELETE FROM {TABLE} WHERE x = 1")
                conn.execute(f"INSERT INTO {self.CLS_TABLE} (x) VALUES (1)")
                conn.execute(f"INSERT INTO public.{TABLE}_x (x) VALUES (1)")
        ''')
    # {TABLE}_x is a name built from a constant plus text: not a single resolvable name part -> not scanned, not guessed
    res = slw.scan_writer_tables("a_x", repo)
    assert "not_scanned" in res


def test_scan_resolves_plain_constants_with_schema_prefix_but_never_a_dotted_attribute(repo):
    writer(repo, "a_x", '''
        TABLE = "t_mod"
        class W:
            CLS_TABLE = "t_cls"
            def run(self, conn):
                conn.execute(f"DELETE FROM {TABLE} WHERE x = 1")
                conn.execute(f"INSERT INTO public.{CLS_TABLE} (x) VALUES (1)")
        ''')
    assert slw.scan_writer_tables("a_x", repo)["tables"] == ["public.t_cls", "public.t_mod"]
    # FP2 item 4: a dotted / attribute name is never a table constant (it used to resolve by its last segment)
    writer(repo, "a_y", '''
        class W:
            CLS_TABLE = "t_cls"
            def run(self, conn):
                conn.execute(f"INSERT INTO public.{self.CLS_TABLE} (x) VALUES (1)")
        ''')
    assert "unresolved_table_expression" in slw.scan_writer_tables("a_y", repo)["not_scanned"]


def test_scan_ambiguous_constant_is_not_scanned(repo):
    writer(repo, "a_x", '''
        TABLE = "t_one"
        class W:
            TABLE = "t_two"
            def run(self, conn):
                conn.execute(f"DELETE FROM {TABLE} WHERE x = 1")
        ''')
    assert "not_scanned" in slw.scan_writer_tables("a_x", repo)


def test_scan_resolves_known_idempotency_helper_calls(repo):
    writer(repo, "a_x", '''
        from ga_writers._idempotency import replace_prior_two
        def run(conn, rows):
            replace_prior_two(conn, rows)
        ''')
    assert slw.scan_writer_tables("a_x", repo)["tables"] == ["public.t_one", "public.t_two"]


def test_helper_whose_own_table_cannot_be_resolved_makes_the_caller_not_scanned(repo):
    writer(repo, "a_x", '''
        from ga_writers._idempotency import replace_prior_dynamic
        def run(conn, obj):
            conn.execute("INSERT INTO t_lit (x) VALUES (1)")
            replace_prior_dynamic(conn, obj)
        ''')
    res = slw.scan_writer_tables("a_x", repo)
    assert "tables" not in res and "replace_prior_dynamic" in res["not_scanned"]


def test_copy_to_is_a_read_not_a_write(repo):
    writer(repo, "a_x", 'x = "COPY t_a TO STDOUT"\ny = "INSERT INTO t_b (x) VALUES (1)"\n')
    assert slw.scan_writer_tables("a_x", repo)["tables"] == ["public.t_b"]


def test_scan_resolves_parametric_helper_with_literal_argument(repo):
    writer(repo, "a_x", '''
        from ga_writers._idempotency import clear_table_for_chart
        def run(conn):
            clear_table_for_chart(conn, "chart_dashas", "c1")
        ''')
    assert slw.scan_writer_tables("a_x", repo)["tables"] == ["public.chart_dashas"]


def test_parametric_helper_with_runtime_argument_is_not_scanned(repo):
    writer(repo, "a_x", '''
        from ga_writers._idempotency import clear_table_for_chart
        def run(conn, which):
            clear_table_for_chart(conn, which, "c1")
        ''')
    assert "not_scanned" in slw.scan_writer_tables("a_x", repo)


def test_local_parametric_function_resolves_from_call_site_and_needs_one(repo):
    writer(repo, "a_x", '''
        def _wipe(conn, tbl):
            conn.execute(f"DELETE FROM {tbl} WHERE x = 1")
        def run(conn):
            _wipe(conn, "t_local")
        ''')
    assert slw.scan_writer_tables("a_x", repo)["tables"] == ["public.t_local"]
    writer(repo, "a_y", '''
        def _wipe(conn, tbl):
            conn.execute(f"DELETE FROM {tbl} WHERE x = 1")
        ''')
    assert "not_scanned" in slw.scan_writer_tables("a_y", repo)


def test_scan_follows_source_paths_one_level(repo):
    write(repo, "platform/python-sidecar/ga_writers/a_x_writer.py", 'SQL = "INSERT INTO t_real (x) VALUES (1)"\n')
    writer(repo, "a_x", '''
        class W:
            source_paths = ['platform/python-sidecar/ga_writers/a_x_writer.py']
        ''')
    res = slw.scan_writer_tables("a_x", repo)
    assert res["tables"] == ["public.t_real"] and any(f.endswith("a_x_writer.py") for f in res["files"])


def test_source_path_escaping_the_repo_or_unreadable_is_not_scanned(repo):
    writer(repo, "a_x", "class W:\n    source_paths = ['../../outside.py']\n")
    assert "source_path_outside_repo" in slw.scan_writer_tables("a_x", repo)["not_scanned"]
    writer(repo, "a_y", "class W:\n    source_paths = ['platform/python-sidecar/ga_writers/missing.py']\n")
    assert "unreadable" in slw.scan_writer_tables("a_y", repo)["not_scanned"]


# ───────────────────────── the static scan: what it refuses to guess ─────────────────────────

def test_delegating_writer_with_no_write_statement_is_not_scanned(repo):
    writer(repo, "a_x", "from brahmagyan.l0_x import seed\ndef run(ctx):\n    return seed(ctx.db_conn)\n")
    res = slw.scan_writer_tables("a_x", repo)
    assert "tables" not in res and res["not_scanned"].startswith("no_write_statement_found")


@pytest.mark.parametrize("body", [
    'def run(c, t):\n    c.execute(f"DELETE FROM {t} WHERE x = 1")\n',
    'for tbl in ["a", "b"]:\n    cur.execute(f"DELETE FROM {tbl} WHERE chart_id = %s")\n',
    'cur.execute("DELETE FROM {} WHERE x".format(t))\n',
    'cur.execute("INSERT INTO %s (x) VALUES (1)" % t)\n',
    'def run(self):\n    cur.execute(f"INSERT INTO {self.table} (x) VALUES (1)")\n',
    'cur.execute(f"INSERT INTO {get_table()} (x) VALUES (1)")\n',
])
def test_runtime_named_tables_are_not_scanned(repo, body):
    writer(repo, "a_x", body)
    assert "not_scanned" in slw.scan_writer_tables("a_x", repo)


def test_one_unresolved_target_makes_the_whole_writer_not_scanned_even_with_literals_present(repo):
    writer(repo, "a_x", 'a = "INSERT INTO t_lit (x) VALUES (1)"\ndef r(c, t):\n    c.execute(f"DELETE FROM {t} WHERE x")\n')
    res = slw.scan_writer_tables("a_x", repo)
    assert "tables" not in res and "not_scanned" in res


def test_missing_unparseable_and_non_identifier_writers_are_not_scanned(repo):
    assert slw.scan_writer_tables("a_missing", repo)["not_scanned"] == "writer_file_not_found"
    writer(repo, "a_bad", "def broken(:\n")
    assert slw.scan_writer_tables("a_bad", repo)["not_scanned"] == "writer_file_unparseable"
    for evil in ("../a_x", "a/../a_x", "A_X", "a x", ""):
        assert "not_scanned" in slw.scan_writer_tables(evil, repo)


def test_scan_never_imports_or_executes_the_writer(repo):
    marker = repo / "executed.flag"
    writer(repo, "a_boom", f'''
        import pathlib
        pathlib.Path({str(marker)!r}).write_text("ran")
        raise SystemExit("imported")
        X = "INSERT INTO t_a (x) VALUES (1)"
        ''')
    sys.path.insert(0, str(repo / WRITERS))
    try:
        res = slw.scan_writer_tables("a_boom", repo)
    finally:
        sys.path.remove(str(repo / WRITERS))
    assert res["tables"] == ["public.t_a"] and not marker.exists() and "a_boom" not in sys.modules


def test_scan_is_read_only(repo):
    p = writer(repo, "a_x", 'x = "INSERT INTO t_a (x) VALUES (1)"\n')
    before = {q: q.read_bytes() for q in repo.rglob("*") if q.is_file()}
    slw.scan_writer_tables("a_x", repo)
    slw.footprint_scope([row("a_x", "t_a")], ["t_a"], repo)
    assert before == {q: q.read_bytes() for q in repo.rglob("*") if q.is_file()} and p.exists()


# ───────────────────────── footprint_scope: the conditions ─────────────────────────

def test_clean_single_table_set_is_complete(repo):
    writer(repo, "a_one", 'x = "INSERT INTO t_a (x) VALUES (1)"\n')
    writer(repo, "a_two", 'x = "DELETE FROM public.t_b WHERE x = 1"\ny = "INSERT INTO t_b (x) VALUES (1)"\n')
    sc = slw.footprint_scope([row("a_one", "t_a"), row("a_two", "public.t_b")], ["t_a", "public.t_b"], repo)
    assert sc["footprint_scope"] == "complete"
    assert sc["assets_without_target_table"] == sc["assets_whose_writer_writes_other_tables"] == sc["assets_not_scanned"] == []


def test_writer_writing_a_second_table_makes_scope_partial(repo):
    writer(repo, "a_one", 'x = "INSERT INTO t_a (x) VALUES (1)"\ny = "INSERT INTO t_extra (x) VALUES (1)"\n')
    sc = slw.footprint_scope([row("a_one", "t_a")], ["t_a"], repo)
    assert sc["footprint_scope"] == "partial"
    (o,) = sc["assets_whose_writer_writes_other_tables"]
    assert o["asset_id"] == "a_one" and o["extra_tables"] == ["public.t_extra"] and o["source"] == "indicative_static_scan"
    assert sc["assets_without_target_table"] == [] and sc["assets_not_scanned"] == []


def test_registry_schema_prefix_is_normalised_on_both_sides(repo):
    writer(repo, "a_one", 'x = "INSERT INTO public.t_a (x) VALUES (1)"\n')
    assert slw.footprint_scope([row("a_one", "t_a")], ["t_a"], repo)["footprint_scope"] == "complete"
    writer(repo, "a_two", 'x = "INSERT INTO t_b (x) VALUES (1)"\n')
    assert slw.footprint_scope([row("a_two", "public.t_b")], ["public.t_b"], repo)["footprint_scope"] == "complete"
    writer(repo, "a_three", 'x = "INSERT INTO other.t_c (x) VALUES (1)"\n')
    sc = slw.footprint_scope([row("a_three", "t_c")], ["t_c"], repo)      # other.t_c is NOT public.t_c
    assert sc["footprint_scope"] == "partial" and sc["assets_whose_writer_writes_other_tables"][0]["extra_tables"] == ["other.t_c"]


def test_extra_table_that_is_another_assets_target_is_already_in_the_footprint(repo):
    writer(repo, "a_one", 'x = "INSERT INTO t_a (x) VALUES (1)"\ny = "DELETE FROM t_b WHERE x = 1"\n')
    writer(repo, "a_two", 'x = "INSERT INTO t_b (x) VALUES (1)"\n')
    sc = slw.footprint_scope([row("a_one", "t_a"), row("a_two", "t_b")], ["t_a", "t_b"], repo)
    assert sc["footprint_scope"] == "complete"
    sc = slw.footprint_scope([row("a_one", "t_a")], ["t_a"], repo)       # t_b is not in this wave's write set
    assert sc["footprint_scope"] == "partial"


def test_null_target_alone_is_enough_when_its_tables_are_already_in_the_write_set(repo):
    writer(repo, "a_one", 'x = "INSERT INTO t_a (x) VALUES (1)"\n')
    writer(repo, "a_two", 'x = "INSERT INTO t_a (x) VALUES (1)"\n')       # writes only a table another asset declares
    sc = slw.footprint_scope([row("a_one", "t_a"), row("a_two", None)], ["t_a"], repo)
    assert sc["footprint_scope"] == "partial" and sc["assets_without_target_table"] == ["a_two"]
    assert sc["assets_whose_writer_writes_other_tables"] == [] and sc["assets_not_scanned"] == []


def test_an_assets_own_registry_table_is_never_an_extra_whatever_the_write_set_says(repo):
    writer(repo, "a_one", 'x = "INSERT INTO public.t_a (x) VALUES (1)"\n')
    sc = slw.footprint_scope([row("a_one", "t_a")], [], repo)             # write_set deliberately does not contain it
    assert sc["footprint_scope"] == "complete" and sc["assets_whose_writer_writes_other_tables"] == []


def test_null_target_table_asset_makes_scope_partial(repo):
    writer(repo, "a_one", 'x = "INSERT INTO t_a (x) VALUES (1)"\n')
    writer(repo, "a_two", 'x = "INSERT INTO t_b (x) VALUES (1)"\n')
    for empty in (None, ""):
        sc = slw.footprint_scope([row("a_one", "t_a"), row("a_two", empty)], ["t_a"], repo)
        assert sc["footprint_scope"] == "partial" and sc["assets_without_target_table"] == ["a_two"]
        # its scanned table is still reported, it is not in the write set
        assert sc["assets_whose_writer_writes_other_tables"][0]["extra_tables"] == ["public.t_b"]


def test_unscannable_writer_makes_scope_partial(repo):
    writer(repo, "a_one", 'x = "INSERT INTO t_a (x) VALUES (1)"\n')
    writer(repo, "a_two", "def run(c):\n    return delegate(c)\n")
    sc = slw.footprint_scope([row("a_one", "t_a"), row("a_two", "t_b")], ["t_a", "t_b"], repo)
    assert sc["footprint_scope"] == "partial"
    assert [x["asset_id"] for x in sc["assets_not_scanned"]] == ["a_two"] and sc["assets_whose_writer_writes_other_tables"] == []
    sc = slw.footprint_scope([row("a_one", "t_a"), row("a_gone", "t_c")], ["t_a", "t_c"], repo)    # no writer file at all
    assert sc["footprint_scope"] == "partial" and sc["assets_not_scanned"][0]["reason"] == "writer_file_not_found"


def test_each_condition_alone_is_enough_and_lists_are_independent(repo):
    writer(repo, "a_ok", 'x = "INSERT INTO t_a (x) VALUES (1)"\n')
    writer(repo, "a_extra", 'x = "INSERT INTO t_b (x) VALUES (1)"\ny = "INSERT INTO t_z (x) VALUES (1)"\n')
    writer(repo, "a_null", 'x = "INSERT INTO t_n (x) VALUES (1)"\n')
    writer(repo, "a_dark", "def run(c):\n    pass\n")
    rows = [row("a_ok", "t_a"), row("a_extra", "t_b"), row("a_null", None), row("a_dark", "t_d")]
    sc = slw.footprint_scope(rows, ["t_a", "t_b", "t_d"], repo)
    assert [o["asset_id"] for o in sc["assets_whose_writer_writes_other_tables"]] == ["a_extra", "a_null"]
    assert sc["assets_without_target_table"] == ["a_null"]
    assert [o["asset_id"] for o in sc["assets_not_scanned"]] == ["a_dark"]
    for keep in ("a_extra", "a_null", "a_dark"):
        only = [r for r in rows if r["asset_id"] in ("a_ok", keep)]
        assert slw.footprint_scope(only, ["t_a", "t_b", "t_d"], repo)["footprint_scope"] == "partial", keep


def test_duplicate_rows_for_one_asset_are_listed_once(repo):
    writer(repo, "a_one", 'x = "INSERT INTO t_a (x) VALUES (1)"\ny = "INSERT INTO t_x (x) VALUES (1)"\n')
    sc = slw.footprint_scope([row("a_one", "t_a"), row("a_one", "t_a")], ["t_a"], repo)
    assert len(sc["assets_whose_writer_writes_other_tables"]) == 1


# ───────────────────────── _footprint_report: has_blockers is never false while partial ─────────────────────────

def blockers_fk():
    # tbl_b -> tbl_a with NO ACTION: deleting tbl_a rows can be refused -> has_blockers True when complete
    return ("c_fkey", "public.tbl_b", "public.tbl_a", "a", "a", ["a_id"], [], False, False, None, None, False, False)


def test_complete_scope_reports_has_blockers_as_computed(repo):
    writer(repo, "a_one", 'x = "INSERT INTO tbl_a (x) VALUES (1)"\n')
    clean = slw._footprint_report(conn_for("tbl_a", "tbl_b", fk=(("c", "public.tbl_b", "public.tbl_c", "c", "a", ["x"], [], False, False, None, None, False, False),)),
                                  [row("a_one", "tbl_a")], repo=repo)
    assert clean["footprint_scope"] == "complete" and clean["has_blockers"] is False and clean["footprint"]["has_blockers"] is False
    assert not any("PARTIAL" in l for l in clean["impact_lines"])
    blocked = slw._footprint_report(conn_for("tbl_a", "tbl_b", fk=(blockers_fk(),)), [row("a_one", "tbl_a")], repo=repo)
    assert blocked["footprint_scope"] == "complete" and blocked["has_blockers"] is True


@pytest.mark.parametrize("make", ["extra", "null", "dark"])
def test_partial_scope_reports_has_blockers_unknown_never_false(repo, make):
    writer(repo, "a_one", 'x = "INSERT INTO tbl_a (x) VALUES (1)"\n' + ('y = "INSERT INTO tbl_x (x) VALUES (1)"\n' if make == "extra" else ""))
    rows = [row("a_one", "tbl_a")]
    if make == "null":
        writer(repo, "a_two", 'x = "INSERT INTO tbl_x (x) VALUES (1)"\n')
        rows.append(row("a_two", None))
    if make == "dark":
        writer(repo, "a_two", "def run(c):\n    pass\n")
        rows.append(row("a_two", "tbl_d"))
    for fk, known in (((("c", "public.tbl_b", "public.tbl_c", "c", "a", ["x"], [], False, False, None, None, False, False),), False),
                      ((blockers_fk(),), True)):
        rep = slw._footprint_report(conn_for("tbl_a", "tbl_b", "tbl_d", fk=fk), rows, repo=repo)
        assert rep["footprint_scope"] == "partial"
        assert rep["has_blockers"] == "unknown" and rep["has_blockers"] is not False
        assert rep["footprint"]["has_blockers"] == "unknown" and rep["footprint"]["has_immediate_blockers"] == "unknown"
        assert rep["footprint"]["has_blockers_known_subset"] is known     # the sound partial fact is kept, labelled
        assert rep["footprint"]["footprint_scope"] == "partial"


def test_partial_impact_lines_print_scope_and_all_three_lists(repo):
    writer(repo, "a_one", 'x = "INSERT INTO tbl_a (x) VALUES (1)"\ny = "INSERT INTO tbl_x (x) VALUES (1)"\n')
    writer(repo, "a_dark", "def run(c):\n    pass\n")
    rep = slw._footprint_report(conn_for("tbl_a", "tbl_b"), [row("a_one", "tbl_a"), row("a_dark", None)], repo=repo)
    text = "\n".join(rep["impact_lines"])
    assert "Footprint scope: PARTIAL" in text and "has_blockers is UNKNOWN, not false" in text
    assert "Assets without a target_table (1): a_dark" in text
    assert "a_one: public.tbl_x" in text and "indicative" in text
    assert "Assets not scanned (1):" in text and "a_dark: no_write_statement_found" in text
    assert "0 found in the edges supplied; not a clean reading while INCOMPLETE or PARTIAL" in text
    assert "none beyond the write set (computed over" not in text           # no clean-zero claim under a partial scope


def test_complete_impact_lines_state_scope_complete(repo):
    writer(repo, "a_one", 'x = "INSERT INTO tbl_a (x) VALUES (1)"\n')
    rep = slw._footprint_report(conn_for("tbl_a", "tbl_b"), [row("a_one", "tbl_a")], repo=repo)
    text = "\n".join(rep["impact_lines"])
    assert "Footprint scope: COMPLETE_PER_STATIC_SCAN" in text and "PARTIAL" not in text and "indicative" in text


def test_no_target_tables_is_partial_with_unknown_blockers(repo):
    writer(repo, "a_one", 'x = "INSERT INTO tbl_a (x) VALUES (1)"\n')
    rep = slw._footprint_report(conn_for("tbl_a"), [row("a_one", None)], repo=repo)
    assert rep["status"] == "NO_TARGET_TABLES" and rep["footprint_scope"] == "partial" and rep["has_blockers"] == "unknown"
    assert rep["assets_without_target_table"] == ["a_one"]


def test_footprint_report_still_issues_only_select_statements(repo):
    writer(repo, "a_one", 'x = "INSERT INTO tbl_a (x) VALUES (1)"\n')
    conn = conn_for("tbl_a", "tbl_b")
    slw._footprint_report(conn, [row("a_one", "tbl_a")], repo=repo)
    assert conn.sql and all(s.lstrip().upper().startswith("SELECT") for s in conn.sql)


def test_scope_fields_are_json_serialisable(repo):
    import json
    writer(repo, "a_one", 'x = "INSERT INTO tbl_a (x) VALUES (1)"\ny = "INSERT INTO tbl_x (x) VALUES (1)"\n')
    rep = slw._footprint_report(conn_for("tbl_a", "tbl_b"), [row("a_one", "tbl_a")], repo=repo)
    json.dumps(rep)


# ───────────────────────── review round: FK-closure incompleteness makes the report partial ─────────────────────────

def _one_clean_writer(repo):
    writer(repo, "a_one", 'x = "INSERT INTO tbl_a (x) VALUES (1)"\n')
    return [row("a_one", "tbl_a")]


def test_incomplete_fk_closure_no_edges_in_catalog_makes_the_report_partial(repo):
    rows = _one_clean_writer(repo)
    rep = slw._footprint_report(conn_for("tbl_a", fk=()), rows, repo=repo)         # catalog returned no FK edges at all
    assert rep["footprint"]["fk_closure_status"] == "INCOMPLETE"
    assert rep["fk_closure_status"] == "INCOMPLETE"
    assert rep["footprint_scope"] == "partial" and "fk_closure_incomplete" in rep["partial_reasons"]
    assert rep["has_blockers"] == "unknown" and rep["has_blockers"] is not False
    assert rep["has_blockers_known_subset"] is False and rep["fk_closure_incomplete_reasons"]
    assert rep["footprint"]["has_blockers"] == "unknown" and rep["footprint"]["footprint_scope"] == "partial"
    text = "\n".join(rep["impact_lines"])
    assert "Footprint scope: PARTIAL" in text and "FK closure is INCOMPLETE" in text and "fk_closure_incomplete" in text


def test_incomplete_fk_closure_table_unknown_to_the_catalog_makes_the_report_partial(repo):
    rows = _one_clean_writer(repo)
    other_edge = ("c", "public.tbl_b", "public.tbl_c", "c", "a", ["x"], [], False, False, None, None, False, False)
    rep = slw._footprint_report(conn_for("tbl_b", "tbl_c", fk=(other_edge,)), rows, repo=repo)   # tbl_a is not in the catalog
    assert rep["footprint"]["unknown_tables"] and rep["fk_closure_status"] == "INCOMPLETE"
    assert rep["footprint_scope"] == "partial" and rep["has_blockers"] == "unknown"
    assert rep["has_blockers_known_subset"] is False


def test_complete_closure_and_clean_writers_report_complete_with_closure_status(repo):
    rows = _one_clean_writer(repo)
    harmless = ("c", "public.tbl_b", "public.tbl_c", "c", "a", ["x"], [], False, False, None, None, False, False)
    rep = slw._footprint_report(conn_for("tbl_a", "tbl_b", "tbl_c", fk=(harmless,)), rows, repo=repo)
    assert rep["fk_closure_status"] == "COMPLETE" and rep["footprint_scope"] == "complete"
    assert rep["partial_reasons"] == [] and rep["has_blockers"] is False and rep["has_blockers_known_subset"] is False


def test_incomplete_closure_keeps_a_blocker_found_in_the_known_subset(repo):
    rows = _one_clean_writer(repo)
    # tbl_unknown_to_catalog is a second write table the catalog does not know -> closure INCOMPLETE; tbl_a has a blocker
    writer(repo, "a_two", 'x = "INSERT INTO tbl_unknown_to_catalog (x) VALUES (1)"\n')
    rep = slw._footprint_report(conn_for("tbl_a", "tbl_b", fk=(blockers_fk(),)),
                                rows + [row("a_two", "tbl_unknown_to_catalog")], repo=repo)
    assert rep["fk_closure_status"] == "INCOMPLETE" and rep["has_blockers"] == "unknown"
    assert rep["has_blockers_known_subset"] is True


# ───────────────────────── review round: a name is a constant only if EVERY binding of it is the same literal ─────────────────────────

BINDINGS = {
    "for_loop": 'for tbl in ("a", "b"):\n    pass\n',
    "for_tuple_target": 'for i, tbl in enumerate(["a"]):\n    pass\n',
    "async_for": 'async def g(xs):\n    async for tbl in xs:\n        pass\n',
    "with_as": 'with open("f") as tbl:\n    pass\n',
    "comprehension": 'names = [tbl for tbl in ("a", "b")]\n',
    "aug_assign": 'tbl += "_x"\n',
    "walrus": 'if (tbl := get()):\n    pass\n',
    "function_param": 'def other(tbl):\n    return tbl\n',
    "kwonly_param": 'def other(*, tbl="z"):\n    return tbl\n',
    "vararg_param": 'def other(*tbl):\n    return tbl\n',
    "lambda_param": 'f = lambda tbl: tbl\n',
    "import_alias": 'import something as tbl\n',
    "import_plain": 'import tbl\n',
    "from_import": 'from mod import tbl\n',
    "from_import_alias": 'from mod import other as tbl\n',
    "global_stmt": 'def g():\n    global tbl\n',
    "nonlocal_stmt": 'def outer():\n    def inner():\n        nonlocal tbl\n    tbl = 1\n',
    "except_as": 'try:\n    pass\nexcept Exception as tbl:\n    pass\n',
    "tuple_unpack": 'tbl, other = pair()\n',
    "starred_unpack": 'first, *tbl = pair()\n',
    "reassigned_other_value": 'tbl = "other"\n',
    "reassigned_non_literal": 'tbl = compute()\n',
    "def_name": 'def tbl():\n    pass\n',
    "class_name": 'class tbl:\n    pass\n',
    "del_stmt": 'del tbl\n',
    "match_capture": 'match x:\n    case tbl:\n        pass\n',
    "match_star": 'match x:\n    case [*tbl]:\n        pass\n',
    "match_mapping_rest": 'match x:\n    case {"k": 1, **tbl}:\n        pass\n',
    "attribute_assign": 'obj.tbl = runtime()\n',
}


@pytest.mark.parametrize("kind", sorted(BINDINGS))
def test_a_name_with_any_other_binding_is_unresolved_not_scanned(repo, kind):
    writer(repo, "a_x", 'tbl = "own"\ndef run(conn):\n    conn.execute(f"DELETE FROM {tbl} WHERE x = 1")\n' + BINDINGS[kind])
    res = slw.scan_writer_tables("a_x", repo)
    assert "tables" not in res and "not_scanned" in res, (kind, res)


def test_the_reviewed_example_is_not_scanned_complete(repo):
    writer(repo, "a_x", '''
        tbl = "own"
        def run(conn):
            conn.execute(f"DELETE FROM {tbl} WHERE x = 1")
            for tbl in ("a", "b"):
                conn.execute(f"INSERT INTO {tbl} (x) VALUES (1)")
        ''')
    assert "not_scanned" in slw.scan_writer_tables("a_x", repo)
    rep = slw.footprint_scope([row("a_x", "own")], ["own"], repo)
    assert rep["footprint_scope"] == "partial" and rep["assets_not_scanned"][0]["asset_id"] == "a_x"


def test_a_name_assigned_only_a_non_literal_is_not_a_constant(repo):
    writer(repo, "a_x", 'TBL = compute()\ndef run(conn):\n    conn.execute(f"DELETE FROM {TBL} WHERE x = 1")\n')
    assert "not_scanned" in slw.scan_writer_tables("a_x", repo)


def test_attribute_target_assigned_elsewhere_makes_a_class_constant_unresolved(repo):
    writer(repo, "a_x", '''
        class W:
            TBL = "own"
            def run(self, conn, other):
                self.TBL = other
                conn.execute(f"DELETE FROM {self.TBL} WHERE x = 1")
        ''')
    assert "not_scanned" in slw.scan_writer_tables("a_x", repo)


def test_positive_controls_the_same_literal_bound_twice_or_declared_without_value_still_resolves(repo):
    writer(repo, "a_x", '''
        tbl = "own"
        tbl = "own"
        class C:
            tbl: str
        def run(conn):
            conn.execute(f"DELETE FROM {tbl} WHERE x = 1")
        ''')
    assert slw.scan_writer_tables("a_x", repo)["tables"] == ["public.own"]
    writer(repo, "a_y", 'tbl: str = "own"\ndef run(conn):\n    conn.execute(f"DELETE FROM {tbl} WHERE x = 1")\n')
    assert slw.scan_writer_tables("a_y", repo)["tables"] == ["public.own"]


def test_a_function_parameter_shadowing_a_constant_resolves_as_a_parametric_helper_not_as_the_constant(repo):
    writer(repo, "a_x", '''
        tbl = "own"
        def wipe(conn, tbl):
            conn.execute(f"DELETE FROM {tbl} WHERE x = 1")
        def run(conn):
            wipe(conn, "other_table")
        ''')
    # the module constant is unusable (parameter binding); the helper resolves from its call site: the table is other_table
    assert slw.scan_writer_tables("a_x", repo)["tables"] == ["public.other_table"]


# ───────────────────────── review round: write forms the scan does not analyse -> not scanned ─────────────────────────

TRIPWIRES = {
    "merge": ('"MERGE INTO t_m USING s ON t_m.id = s.id WHEN MATCHED THEN UPDATE SET x = 1"', "MERGE INTO"),
    "refresh_mv": ('"REFRESH MATERIALIZED VIEW CONCURRENTLY mv_x"', "REFRESH MATERIALIZED VIEW"),
    "refresh_mv_lower": ('"refresh materialized view mv_x"', "REFRESH MATERIALIZED VIEW"),
    "create_table_as": ('"CREATE TABLE t_new AS SELECT 1"', "CREATE TABLE"),
    "create_temp_table": ('"CREATE TEMP TABLE t_tmp (x int)"', "CREATE TABLE"),
    "create_unlogged": ('"CREATE UNLOGGED TABLE t_u (x int)"', "CREATE TABLE"),
    "select_into": ('"SELECT a, b INTO t_new FROM src"', "SELECT ... INTO"),
    "select_into_temp": ('"SELECT a INTO TEMP t_new FROM src"', "SELECT ... INTO"),
    "alter_table": ('"ALTER TABLE t_a ADD COLUMN x int"', "ALTER TABLE"),
    "drop_table": ('"DROP TABLE IF EXISTS t_a"', "DROP TABLE"),
}


@pytest.mark.parametrize("name", sorted(TRIPWIRES))
def test_unanalysed_write_forms_make_a_writer_not_scanned(repo, name):
    sql, label = TRIPWIRES[name]
    writer(repo, "a_x", f'ok = "INSERT INTO t_a (x) VALUES (1)"\nother = {sql}\n')
    res = slw.scan_writer_tables("a_x", repo)
    assert "tables" not in res and label in res["not_scanned"], res


@pytest.mark.parametrize("src,label", [
    ("from psycopg import sql\ndef r(c):\n    c.execute(sql.SQL('x'))\n", "composition"),
    ("from psycopg import sql\ndef r(c):\n    q = sql.Identifier('t')\n", "composition"),
    ("from psycopg.sql import Identifier\ndef r(c):\n    q = Identifier('t')\n", "composition"),
    ("def r(c):\n    c.execute(open('q.txt').read())\n", "read from a file"),
    ("import pathlib\ndef r(c):\n    q = pathlib.Path('q.txt').read_text()\n    c.execute(q)\n", "read from a file"),
    ("def r(c):\n    with open('q.txt') as f:\n        q = f.read()\n    c.executemany(q, [])\n", "read from a file"),
    ("Q = 'queries/insert_things.sql'\n", "sql file reference"),
])
def test_call_level_tripwires_make_a_writer_not_scanned(repo, src, label):
    writer(repo, "a_x", 'ok = "INSERT INTO t_a (x) VALUES (1)"\n' + src)
    res = slw.scan_writer_tables("a_x", repo)
    assert "tables" not in res and label in res["not_scanned"], res


def test_tripwires_do_not_fire_on_ordinary_single_table_writers(repo):
    writer(repo, "a_x", '''
        """Docstring may mention REFRESH MATERIALIZED VIEW, MERGE INTO, DROP TABLE, CREATE TABLE and SELECT x INTO y."""
        # ALTER TABLE in a comment
        import json, pathlib
        CFG = json.loads(pathlib.Path("cfg.json").read_text())
        A = "WITH s AS (SELECT 1 AS x) INSERT INTO t_a (x) SELECT x FROM s"
        B = "INSERT INTO t_a (x) SELECT x FROM src WHERE c = 1"
        C = "SELECT a, b FROM src WHERE c = 1"
        def r(c):
            c.execute("SELECT 1")
            c.execute(A)
        ''')
    assert slw.scan_writer_tables("a_x", repo)["tables"] == ["public.t_a"]


def test_real_refresh_materialized_view_writers_are_not_scanned_as_single_table():
    for asset in ("ga_sade_sati", "ga_sensitive", "bo_pramana_mapa"):
        res = slw.scan_writer_tables(asset, REAL_REPO)
        assert "tables" not in res and "REFRESH MATERIALIZED VIEW" in res["not_scanned"], (asset, res)


# ───────────────────────── review round: edge cases ─────────────────────────

def test_empty_row_set_is_partial_never_complete(repo):
    sc = slw.footprint_scope([], [], repo)
    assert sc["footprint_scope"] == "partial" and sc["partial_reasons"] == ["no_assets_in_set"]
    rep = slw._footprint_report(conn_for("tbl_a"), [], repo=repo)
    assert rep["footprint_scope"] == "partial" and rep["has_blockers"] == "unknown" and rep["status"] == "NO_TARGET_TABLES"
    text = "\n".join(rep["impact_lines"])
    assert "Footprint scope: PARTIAL" in text and "FK closure is NOT_COMPUTED" in text and rep["fk_closure_status"] == "NOT_COMPUTED"


def test_relative_repo_argument_does_not_raise(repo, monkeypatch):
    _one_clean_writer(repo)
    monkeypatch.chdir(repo)
    assert slw.scan_writer_tables("a_one", ".")["tables"] == ["public.tbl_a"]
    assert slw.footprint_scope([row("a_one", "tbl_a")], ["tbl_a"], ".")["footprint_scope"] == "complete"
    rep = slw._footprint_report(conn_for("tbl_a", "tbl_b"), [row("a_one", "tbl_a")], repo=".")
    assert rep["footprint_scope"] == "complete"
    (repo / "sub").mkdir()
    assert slw.scan_writer_tables("a_one", "sub/..")["tables"] == ["public.tbl_a"]      # relative with .. still resolves
    # a relative repo with source_paths followed (the resolved candidate is compared with the repo root)
    write(repo, "platform/python-sidecar/ga_writers/a_follow_writer.py", 'S = "INSERT INTO t_f (x) VALUES (1)"\n')
    writer(repo, "a_follow", "class W:\n    source_paths = ['platform/python-sidecar/ga_writers/a_follow_writer.py']\n")
    res = slw.scan_writer_tables("a_follow", ".")
    assert res["tables"] == ["public.t_f"] and res["files"][-1].endswith("a_follow_writer.py")
    assert slw.footprint_scope([row("a_follow", "t_f")], ["t_f"], ".")["footprint_scope"] == "complete"


def test_recursion_error_while_parsing_puts_the_asset_in_not_scanned(repo, monkeypatch):
    writer(repo, "a_x", 'x = "INSERT INTO t_a (x) VALUES (1)"\n')

    def boom(*a, **k):
        raise RecursionError("maximum recursion depth exceeded")
    monkeypatch.setattr(slw.ast, "parse", boom)
    res = slw.scan_writer_tables("a_x", repo)
    assert res["not_scanned"] == "writer_file_unparseable"
    sc = slw.footprint_scope([row("a_x", "t_a")], ["t_a"], repo)
    assert sc["footprint_scope"] == "partial" and sc["assets_not_scanned"][0]["asset_id"] == "a_x"


def test_recursion_error_while_walking_puts_the_asset_in_not_scanned(repo, monkeypatch):
    writer(repo, "a_x", 'x = "INSERT INTO t_a (x) VALUES (1)"\n')

    def boom(self, node, fn_stack):
        raise RecursionError("deep")
    monkeypatch.setattr(slw._WriteScan, "_walk", boom)
    assert "too_deeply_nested" in slw.scan_writer_tables("a_x", repo)["not_scanned"]


def test_any_other_scan_exception_becomes_not_scanned_never_a_crash_or_clean(repo, monkeypatch):
    writer(repo, "a_x", 'x = "INSERT INTO t_a (x) VALUES (1)"\n')

    def boom(*a, **k):
        raise RuntimeError("unexpected")
    monkeypatch.setattr(slw, "scan_writer_tables", boom)
    sc = slw.footprint_scope([row("a_x", "t_a")], ["t_a"], repo)
    assert sc["footprint_scope"] == "partial" and sc["assets_not_scanned"][0]["reason"] == "scan_error: RuntimeError"


def test_a_very_long_concatenation_never_raises(repo):
    writer(repo, "a_x", "x = " + " + ".join(['"a"'] * 4000) + "\n")
    res = slw.scan_writer_tables("a_x", repo)
    assert isinstance(res, dict) and ("tables" in res or "not_scanned" in res)


def test_non_python_source_path_is_not_scanned(repo):
    writer(repo, "a_x", "class W:\n    source_paths = ['platform/python-sidecar/ga_writers/a_x_writer.py', 'docs/notes.md']\n")
    write(repo, "platform/python-sidecar/ga_writers/a_x_writer.py", 'S = "INSERT INTO t_a (x) VALUES (1)"\n')
    assert slw.scan_writer_tables("a_x", repo)["not_scanned"] == "source_path_not_python: docs/notes.md"
    writer(repo, "a_dir", "class W:\n    source_paths = ['platform/python-sidecar/services/a_dir/']\n")
    assert "source_path_not_python" in slw.scan_writer_tables("a_dir", repo)["not_scanned"]


def test_source_paths_that_is_not_a_literal_list_is_not_scanned(repo):
    writer(repo, "a_x", 'P = "x.py"\nclass W:\n    source_paths = [P]\n    s = "INSERT INTO t_a (x) VALUES (1)"\n')
    assert slw.scan_writer_tables("a_x", repo)["not_scanned"] == "source_paths_not_a_literal_list_of_strings"
    writer(repo, "a_y", 'class W:\n    source_paths = compute()\n    s = "INSERT INTO t_a (x) VALUES (1)"\n')
    assert slw.scan_writer_tables("a_y", repo)["not_scanned"] == "source_paths_not_a_literal_list_of_strings"


def test_schema_version_is_bumped_because_has_blockers_can_be_unknown(repo):
    assert slw.SCHEMA == "suvarna.e5_9.transitive_footprint/3"
    rows = _one_clean_writer(repo)
    rep = slw._footprint_report(conn_for("tbl_a", fk=()), rows, repo=repo)
    assert rep["footprint"]["schema"] == slw.SCHEMA and rep["footprint"]["has_blockers"] == "unknown"


def test_limitations_of_the_scan_are_printed_with_the_impact_lines(repo):
    rep = slw._footprint_report(conn_for("tbl_a", "tbl_b"), _one_clean_writer(repo), repo=repo)
    text = "\n".join(rep["impact_lines"])
    assert "Limitations of the writer scan:" in text and "stored functions" in text and "delegates" in text


# ───────────────────────── anchors on the REAL writer tree (read, never imported) ─────────────────────────

@pytest.mark.parametrize("asset", ["bo_karanajala", "bo_sangati", "bo_upaya", "bo_anveshana", "bo_cdlm_summary", "bo_cgm_motifs"])
def test_real_multi_table_bodha_writers_show_more_than_one_table(asset):
    res = slw.scan_writer_tables(asset, REAL_REPO)
    assert "tables" in res and len(res["tables"]) >= 2, res


def test_real_ga_thin_adapter_is_followed_through_source_paths():
    res = slw.scan_writer_tables("ga_positions", REAL_REPO)
    assert res["tables"] == ["public.chart_facts"] and any(f.endswith("ga_positions_writer.py") for f in res["files"])


def test_real_l0_delegating_adapter_is_not_scanned_rather_than_guessed():
    assert "not_scanned" in slw.scan_writer_tables("bg_nakshatra", REAL_REPO)


def test_real_helper_effects_cover_the_l1_and_bodha_idempotency_helpers():
    h = slw.helper_write_effects(REAL_REPO)
    assert h["replace_prior_chart_facts"]["tables"] == {"public.chart_facts"}
    assert h["clear_table_for_chart"]["params"] == [("table", 1)]
    assert "public.bodha_msr_signals" in h["replace_prior_msr_signals"]["tables"]
