"""test_n349_divergence_default_owner_path.py: SS N-347/N-349, the owner-path package that drops the 0.0 default of
chart_facts.cross_ayanamsha_divergence_arcsec (00_ARCHITECTURE/briefs/suvarna/exec/divergence_default/divergence_default_drop.py).

Real SQL on the DISPOSABLE PostgreSQL (never production): a fresh database per test, a table owned by a `data_plane_l1_owner` role, and an
administrator that is NOT a superuser and NOT a member of the owner (so the transient GRANT / SET LOCAL ROLE / REVOKE path is the one exercised,
as with the Cloud SQL `postgres` role). Each guard has a test that fails if the guard is removed.
"""
from __future__ import annotations

import importlib.util
import itertools
import pathlib
import re

import pytest

psycopg = pytest.importorskip("psycopg")

from _disposable_pg import disposable_pg  # noqa: F401,E402  (the fixture must be importable here)

HERE = pathlib.Path(__file__).resolve().parent
PKG = HERE.parents[3] / "00_ARCHITECTURE" / "briefs" / "suvarna" / "exec" / "divergence_default" / "divergence_default_drop.py"
spec = importlib.util.spec_from_file_location("divergence_default_drop", PKG)
dd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dd)

_counter = itertools.count(1)
COL = "cross_ayanamsha_divergence_arcsec"

ROLES_SQL = """
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_l1_owner') THEN CREATE ROLE data_plane_l1_owner NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'n349_admin') THEN CREATE ROLE n349_admin LOGIN CREATEROLE; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'n349_other_owner') THEN CREATE ROLE n349_other_owner NOLOGIN; END IF;
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'n349_reader') THEN CREATE ROLE n349_reader NOLOGIN; END IF;
END $$;
"""


DROP_ANY_SQL = """
DO $$ DECLARE k text; BEGIN
  SELECT relkind::text INTO k FROM pg_class WHERE oid = to_regclass('public.chart_facts');
  IF k = 'v' THEN DROP VIEW public.chart_facts; ELSIF k IS NOT NULL THEN DROP TABLE public.chart_facts CASCADE; END IF;
END $$;
"""
COLS = "fact_id text NOT NULL, note text DEFAULT 'x', %s double precision DEFAULT 0.0" % COL


@pytest.fixture
def db(disposable_pg):
    """A fresh database with the roles and a chart_facts table; returns (cluster, dbname, make_conn)."""
    cl = disposable_pg
    cl.psql(ROLES_SQL)
    name = "n349_%d" % next(_counter)
    cl.psql("CREATE DATABASE %s" % name)
    cl.psql("GRANT ALL ON SCHEMA public TO PUBLIC", db=name)

    def reset():
        """Drop whatever is named public.chart_facts (a table, a view, a partitioned table) and the helper tables."""
        cl.psql(DROP_ANY_SQL, db=name)
        cl.psql("DROP TABLE IF EXISTS public.cf_parent, public.chart_facts_child, public.cf_src CASCADE", db=name)

    def table(owner="data_plane_l1_owner", column_sql="%s double precision DEFAULT 0.0" % COL):
        reset()
        cl.psql("CREATE TABLE public.chart_facts (fact_id text NOT NULL, note text DEFAULT 'x', %s)" % column_sql, db=name)
        cl.psql("ALTER TABLE public.chart_facts OWNER TO %s" % owner, db=name)
        cl.psql("GRANT SELECT ON public.chart_facts TO n349_reader", db=name)

    table()
    table.reset = reset

    def connect(user="n349_admin", **kw):
        return psycopg.connect("postgresql://%s@%s:%d/%s" % (user, cl.host, cl.port, name), **kw)

    return cl, name, connect, table


def _state(cl, name):
    return cl.psql("SELECT attname, attnotnull, COALESCE(pg_get_expr(d.adbin, d.adrelid),'') FROM pg_attribute a "
                   "JOIN pg_class c ON c.oid=a.attrelid LEFT JOIN pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum "
                   "WHERE c.relname='chart_facts' AND a.attnum>0 AND NOT a.attisdropped ORDER BY a.attnum", db=name)


def _default(cl, name):
    return cl.psql("SELECT COALESCE(pg_get_expr(d.adbin, d.adrelid),'<none>') FROM pg_attribute a JOIN pg_class c ON c.oid=a.attrelid "
                   "LEFT JOIN pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum WHERE c.relname='chart_facts' AND a.attname='%s'" % COL, db=name)


def _member(cl, name):
    return cl.psql("SELECT pg_has_role('n349_admin','data_plane_l1_owner','MEMBER')", db=name)


def _server_version(cl, name):
    return int(cl.psql("SHOW server_version_num", db=name))


def _snapshot(cl, name):
    """Everything about public.chart_facts that a refused or rolled-back run must leave exactly as it was."""
    q = ("WITH t AS (SELECT to_regclass('public.chart_facts') AS toid) "
         "SELECT concat_ws('|', 'rel', c.relkind::text, c.relispartition, c.relrowsecurity, c.relforcerowsecurity, c.relacl::text, pg_get_userbyid(c.relowner)) "
         "FROM pg_class c, t WHERE c.oid = t.toid "
         "UNION ALL SELECT concat_ws('|', 'col', a.attname, format_type(a.atttypid, a.atttypmod), a.attnotnull, pg_get_expr(d.adbin, d.adrelid)) "
         "FROM pg_attribute a JOIN t ON a.attrelid = t.toid LEFT JOIN pg_attrdef d ON d.adrelid = a.attrelid AND d.adnum = a.attnum WHERE a.attnum > 0 AND NOT a.attisdropped "
         "UNION ALL SELECT concat_ws('|', 'con', conname, pg_get_constraintdef(oid)) FROM pg_constraint, t WHERE conrelid = t.toid "
         "UNION ALL SELECT concat_ws('|', 'idx', indexdef) FROM pg_indexes WHERE schemaname = 'public' AND tablename = 'chart_facts' "
         "UNION ALL SELECT concat_ws('|', 'pol', polname) FROM pg_policy, t WHERE polrelid = t.toid "
         "UNION ALL SELECT concat_ws('|', 'cmt', objsubid, description) FROM pg_description, t WHERE objoid = t.toid AND classoid = 'pg_class'::regclass "
         "UNION ALL SELECT concat_ws('|', 'trg', tgname) FROM pg_trigger, t WHERE tgrelid = t.toid "
         "UNION ALL SELECT concat_ws('|', 'mem', pg_has_role('n349_admin','data_plane_l1_owner','MEMBER')) "
         "ORDER BY 1")
    return cl.psql(q, db=name)


def _run(connect, mode, expect=None, rollback=False):
    lines = []
    with connect() as conn:
        outcome = dd.run(conn, mode, expect, rollback, out=lines.append)
    return outcome, "\n".join(lines)


# ───────────────────────── the change itself ─────────────────────────

def test_dry_run_changes_nothing_and_leaves_no_membership(db):
    cl, name, connect, _ = db
    before = _state(cl, name)
    outcome, text = _run(connect, "dry-run")
    assert outcome == "dry_run" and "ROLLED BACK" in text
    assert _state(cl, name) == before and _default(cl, name) == "0.0"
    assert _member(cl, name) == "f"


def test_apply_drops_exactly_the_one_default_and_nothing_else(db):
    cl, name, connect, _ = db
    before = _state(cl, name)
    acl_before = cl.psql("SELECT relacl::text FROM pg_class WHERE relname='chart_facts'", db=name)
    outcome, text = _run(connect, "apply", dd.plan_hash())
    assert outcome == "applied" and "COMMITTED" in text
    assert _default(cl, name) == "<none>"
    after = _state(cl, name)
    changed = [(b, a) for b, a in zip(before.splitlines(), after.splitlines()) if a != b]
    assert len(changed) == 1 and changed[0][0].startswith(COL + "|f|0.0") and changed[0][1].startswith(COL + "|f|")
    assert "note|f|'x'::text" in after                                           # the other defaults are untouched
    assert cl.psql("SELECT relacl::text FROM pg_class WHERE relname='chart_facts'", db=name) == acl_before
    assert cl.psql("SELECT pg_get_userbyid(relowner) FROM pg_class WHERE relname='chart_facts'", db=name) == "data_plane_l1_owner"
    assert _member(cl, name) == "f"                                                # the transient membership is gone


def test_the_effect_new_rows_are_null_and_existing_zero_rows_stay_without_a_backfill(db):
    cl, name, connect, _ = db
    cl.psql("INSERT INTO public.chart_facts (fact_id) VALUES ('old')", db=name)           # takes the 0.0 default today
    assert cl.psql("SELECT %s FROM public.chart_facts WHERE fact_id='old'" % COL, db=name) == "0"
    _run(connect, "apply", dd.plan_hash())
    cl.psql("INSERT INTO public.chart_facts (fact_id) VALUES ('new')", db=name)
    assert cl.psql("SELECT %s IS NULL FROM public.chart_facts WHERE fact_id='new'" % COL, db=name) == "t"
    assert cl.psql("SELECT %s FROM public.chart_facts WHERE fact_id='old'" % COL, db=name) == "0"      # no backfill (each rebuild rewrites its rows)


def test_a_second_run_is_an_idempotent_no_op_not_an_error(db):
    cl, name, connect, _ = db
    assert _run(connect, "apply", dd.plan_hash())[0] == "applied"
    outcome, text = _run(connect, "apply", dd.plan_hash())
    assert outcome == "noop" and "NO-OP" in text
    assert _default(cl, name) == "<none>"
    assert _run(connect, "dry-run")[0] == "noop"


def test_a_member_administrator_keeps_its_membership(db):
    cl, name, connect, _ = db
    cl.psql("GRANT data_plane_l1_owner TO n349_admin")
    try:
        assert _run(connect, "apply", dd.plan_hash())[0] == "applied"
        assert _member(cl, name) == "t"                                          # added by us? no: it was there, and stays
    finally:
        cl.psql("REVOKE data_plane_l1_owner FROM n349_admin")


# ───────────────────────── the guards ─────────────────────────

def test_a_wrong_plan_hash_refuses_and_changes_nothing(db):
    cl, name, connect, _ = db
    with pytest.raises(dd.Refused, match="plan hash"):
        _run(connect, "apply", "0" * 64)
    assert _default(cl, name) == "0.0"


def test_a_not_null_column_stops_the_job(db):
    cl, name, connect, table = db
    table(column_sql="%s double precision NOT NULL DEFAULT 0.0" % COL)
    with pytest.raises(dd.Refused, match="NOT NULL"):
        _run(connect, "apply", dd.plan_hash())
    assert _default(cl, name) == "0.0"


def test_an_unexpected_default_is_refused(db):
    cl, name, connect, table = db
    table(column_sql="%s double precision DEFAULT 1.5" % COL)
    with pytest.raises(dd.Refused, match="not 0.0"):
        _run(connect, "apply", dd.plan_hash())
    assert _default(cl, name) == "1.5"


def test_another_table_owner_is_refused(db):
    cl, name, connect, table = db
    table(owner="n349_other_owner")
    with pytest.raises(dd.Refused, match="owner"):
        _run(connect, "apply", dd.plan_hash())
    assert _default(cl, name) == "0.0"


def test_a_missing_column_is_refused(db):
    cl, name, connect, table = db
    table(column_sql="other_col double precision DEFAULT 0.0")
    with pytest.raises(dd.Refused, match="does not exist"):
        _run(connect, "apply", dd.plan_hash())


def _refused_and_unchanged(db, match, rollback=False):
    cl, name, connect, _ = db
    before = _snapshot(cl, name)
    with pytest.raises(dd.Refused, match=match):
        _run(connect, "apply", dd.plan_hash(rollback), rollback=rollback)
    assert _snapshot(cl, name) == before                                                 # nothing changed, no membership left behind


@pytest.mark.parametrize("column_sql,shown,default", [
    ("%s numeric DEFAULT 0.0", "numeric", "0.0"),
    ("%s numeric(10,3) DEFAULT 0.0", "numeric(10,3)", "0.0"),
    ("%s real DEFAULT 0.0", "real", "0.0"),
    ("%s text DEFAULT '0.0'", "text", "'0.0'::text"),
])
def test_a_column_of_another_type_is_refused_even_with_the_default_0_0(db, column_sql, shown, default):
    cl, name, connect, table = db
    table(column_sql=column_sql % COL)
    assert _default(cl, name) == default
    _refused_and_unchanged(db, re.escape("the column type is %r, not double precision" % shown))
    _refused_and_unchanged(db, re.escape("the column type is %r, not double precision" % shown), rollback=True)
    assert _default(cl, name) == default


@pytest.mark.parametrize("with_default", [True, False], ids=["view-with-default", "view-without-default"])
def test_a_view_named_chart_facts_is_refused_not_applied_and_not_a_no_op(db, with_default):
    cl, name, connect, table = db
    table.reset()
    cl.psql("CREATE TABLE public.cf_src (%s)" % COLS, db=name)
    cl.psql("CREATE VIEW public.chart_facts AS SELECT * FROM public.cf_src", db=name)
    cl.psql("ALTER VIEW public.chart_facts OWNER TO data_plane_l1_owner", db=name)
    if with_default:
        cl.psql("ALTER VIEW public.chart_facts ALTER COLUMN %s SET DEFAULT 0.0" % COL, db=name)
        assert _default(cl, name) == "0.0"
    _refused_and_unchanged(db, "not an ordinary table .*relkind = 'v'")
    _refused_and_unchanged(db, "not an ordinary table .*relkind = 'v'", rollback=True)
    _refused_and_unchanged(db, "not an ordinary table", rollback=False)
    assert _default(cl, name) == ("0.0" if with_default else "<none>")


def _structure(cl, name, kind):
    cl.psql(DROP_ANY_SQL, db=name)
    cl.psql("DROP TABLE IF EXISTS public.cf_parent, public.chart_facts_child, public.cf_src CASCADE", db=name)
    if kind == "partitioned":
        cl.psql("CREATE TABLE public.chart_facts (%s) PARTITION BY LIST (fact_id)" % COLS, db=name)
    elif kind == "partition":
        cl.psql("CREATE TABLE public.cf_parent (%s) PARTITION BY LIST (fact_id)" % COLS, db=name)
        cl.psql("CREATE TABLE public.chart_facts PARTITION OF public.cf_parent DEFAULT", db=name)
    elif kind == "inheritance_child":
        cl.psql("CREATE TABLE public.cf_parent (%s)" % COLS, db=name)
        cl.psql("CREATE TABLE public.chart_facts () INHERITS (public.cf_parent)", db=name)
    elif kind == "inheritance_parent":
        cl.psql("CREATE TABLE public.chart_facts (%s)" % COLS, db=name)
        cl.psql("CREATE TABLE public.chart_facts_child () INHERITS (public.chart_facts)", db=name)
    cl.psql("ALTER TABLE public.chart_facts OWNER TO data_plane_l1_owner", db=name)


@pytest.mark.parametrize("kind,match", [
    ("partitioned", "relkind = 'p'"),
    ("partition", "is a partition"),
    ("inheritance_child", r"table inheritance \(0 child\(ren\), 1 parent\(s\)\)"),
    ("inheritance_parent", r"table inheritance \(1 child\(ren\), 0 parent\(s\)\)"),
])
def test_a_partitioned_partition_or_inherited_table_is_refused_and_nothing_changes(db, kind, match):
    cl, name, connect, _ = db
    _structure(cl, name, kind)
    assert _default(cl, name) == "0.0"
    _refused_and_unchanged(db, match)
    _refused_and_unchanged(db, match, rollback=True)
    assert _default(cl, name) == "0.0"


def test_a_change_that_touches_anything_else_is_refused_and_rolled_back(db, monkeypatch):
    cl, name, connect, _ = db
    sabotaged = list(dd.DROP_STATEMENTS) + ["ALTER TABLE public.chart_facts ALTER COLUMN note DROP DEFAULT"]
    monkeypatch.setattr(dd, "DROP_STATEMENTS", sabotaged)
    with pytest.raises(dd.Refused, match="diff exactly the one planned line"):
        _run(connect, "apply", dd.plan_hash())
    assert _default(cl, name) == "0.0" and "note|f|'x'::text" in _state(cl, name)         # nothing was committed
    assert _member(cl, name) == "f"


TRIGGER_FN = ("CREATE FUNCTION public.n349_noop() RETURNS trigger LANGUAGE plpgsql AS $f$ BEGIN RETURN NEW; END $f$")
TRIGGER_DDL = "CREATE TRIGGER n349_trg BEFORE INSERT ON public.chart_facts FOR EACH ROW EXECUTE FUNCTION public.n349_noop()"
CHART = "public.chart_facts"


@pytest.mark.parametrize("category,extra,setup", [
    ("constraints unchanged", "ALTER TABLE %s ADD CONSTRAINT n349_chk CHECK (note <> 'z')" % CHART, None),
    ("constraints unchanged", "ALTER TABLE %s ADD CONSTRAINT n349_pk PRIMARY KEY (fact_id)" % CHART, None),
    ("column types unchanged", "ALTER TABLE %s ALTER COLUMN note TYPE varchar(20)" % CHART, None),
    ("column types unchanged", "ALTER TABLE %s ALTER COLUMN %s TYPE numeric" % (CHART, COL), None),
    ("indexes unchanged", "CREATE INDEX n349_ix ON %s (fact_id)" % CHART, None),
    ("row security and policies unchanged", "ALTER TABLE %s ENABLE ROW LEVEL SECURITY" % CHART, None),
    ("row security and policies unchanged", "ALTER TABLE %s FORCE ROW LEVEL SECURITY" % CHART, None),
    ("row security and policies unchanged", "CREATE POLICY n349_pol ON %s USING (true)" % CHART, None),
    ("comments unchanged", "COMMENT ON COLUMN %s.note IS 'a comment'" % CHART, None),
    ("comments unchanged", "COMMENT ON COLUMN %s.%s IS 'a comment'" % (CHART, COL), None),
    ("comments unchanged", "COMMENT ON TABLE %s IS 'a comment'" % CHART, None),
    ("triggers unchanged", TRIGGER_DDL, [TRIGGER_FN]),
    ("triggers unchanged", "ALTER TABLE %s DISABLE TRIGGER n349_trg" % CHART, [TRIGGER_FN, TRIGGER_DDL]),
])
def test_a_change_beyond_the_one_default_line_is_refused_and_rolled_back(db, monkeypatch, category, extra, setup):
    """The default drop itself succeeds inside the transaction; the second (sabotage) statement changes something the 'exactly one line'
    diff cannot see; the matching before/after snapshot check must refuse, and nothing may be committed."""
    cl, name, connect, _ = db
    for statement in setup or ():
        cl.psql(statement, db=name)
    monkeypatch.setattr(dd, "DROP_STATEMENTS", list(dd.DROP_STATEMENTS) + [extra])
    _refused_and_unchanged(db, re.escape(category))
    assert _default(cl, name) == "0.0"                                                   # the planned line was rolled back too


def test_a_changed_acl_is_refused_and_rolled_back(db, monkeypatch):
    cl, name, connect, _ = db
    sabotaged = list(dd.DROP_STATEMENTS) + ["GRANT INSERT ON public.chart_facts TO n349_reader"]
    monkeypatch.setattr(dd, "DROP_STATEMENTS", sabotaged)
    with pytest.raises(dd.Refused, match="acl unchanged"):
        _run(connect, "apply", dd.plan_hash())
    assert _default(cl, name) == "0.0"


GUARDED = "-c statement_timeout=30000"        # a missing lock_timeout must FAIL (QueryCanceled), never hang the suite


def test_the_lock_timeout_is_the_first_statement_and_precedes_the_grant_and_the_role_switch(db):
    assert dd.LOCK_TIMEOUT_SQL == "SET LOCAL lock_timeout = '5s'"
    assert dd.DROP_STATEMENTS == ["ALTER TABLE public.%s ALTER COLUMN %s DROP DEFAULT" % (dd.TABLE, COL)]
    for rollback in (False, True):
        lines = dd.plan_text(rollback).splitlines()
        stmts = [l for l in lines if not l.startswith("--")]
        assert stmts[0] == dd.LOCK_TIMEOUT_SQL and len(stmts) == 2 and stmts[1].startswith("ALTER TABLE")      # the plan text shows it first
        assert lines.index(dd.LOCK_TIMEOUT_SQL) < min(i for i, l in enumerate(lines) if "transient membership" in l)
    cl, name, connect, _ = db

    class Recorder:
        def __init__(self, conn):
            self._conn, self.sql = conn, []

        def cursor(self):
            cur, rec = self._conn.cursor(), self

            class Cursor:
                def execute(self, query, *args, **kw):
                    rec.sql.append(str(query))
                    return cur.execute(query, *args, **kw)

                def __getattr__(self, attr):
                    return getattr(cur, attr)
            return Cursor()

        def __getattr__(self, attr):
            return getattr(self._conn, attr)

    with connect() as conn:
        rec = Recorder(conn)
        dd.run(rec, "dry-run", out=lambda _: None)
    first = lambda prefix: next(i for i, q in enumerate(rec.sql) if q.startswith(prefix))             # noqa: E731
    assert rec.sql[0] == dd.LOCK_TIMEOUT_SQL                                                            # the very first statement of the transaction
    assert first(dd.LOCK_TIMEOUT_SQL) < first("SET LOCAL ROLE") < first("ALTER TABLE")
    if _server_version(cl, name) < 160000:                                                              # the transient-membership model (production is 15.18)
        assert first(dd.LOCK_TIMEOUT_SQL) < first("GRANT") < first("SET LOCAL ROLE")


def test_the_lock_timeout_really_fires_on_the_alter(db):
    cl, name, connect, _ = db
    with connect(cl.user) as holder:                                            # an open reader (the cluster user) holds ACCESS SHARE on the table
        holder.execute("SELECT 1 FROM public.chart_facts LIMIT 1")
        with pytest.raises(psycopg.errors.LockNotAvailable):
            with connect(options=GUARDED) as conn:
                dd.run(conn, "apply", dd.plan_hash(), out=lambda _: None)
        holder.rollback()
    assert _default(cl, name) == "0.0"


def test_the_lock_timeout_also_bounds_the_transient_grant(db):
    """With the timeout moved after the GRANT this test is QueryCanceled (the 30 s guard), not LockNotAvailable: the GRANT would wait unbounded."""
    cl, name, connect, _ = db
    with connect(cl.user) as holder:                                            # SHARE on pg_auth_members: readers pass, the GRANT (ROW EXCLUSIVE) waits
        holder.execute("LOCK TABLE pg_catalog.pg_auth_members IN SHARE MODE")
        try:
            with pytest.raises(psycopg.errors.LockNotAvailable):
                with connect(options=GUARDED) as conn:
                    dd.run(conn, "apply", dd.plan_hash(), out=lambda _: None)
        finally:
            holder.rollback()
    assert _default(cl, name) == "0.0" and _member(cl, name) == "f"


# ───────────────────────── the inverse ─────────────────────────

def test_rollback_restores_the_default_and_is_idempotent(db):
    cl, name, connect, _ = db
    assert dd.plan_hash(rollback=True) != dd.plan_hash()
    assert _run(connect, "apply", dd.plan_hash())[0] == "applied"
    assert _run(connect, "dry-run", rollback=True)[0] == "dry_run" and _default(cl, name) == "<none>"
    assert _run(connect, "apply", dd.plan_hash(rollback=True), rollback=True)[0] == "applied"
    assert _default(cl, name) == "0.0"
    assert _run(connect, "apply", dd.plan_hash(rollback=True), rollback=True)[0] == "noop"
    with pytest.raises(dd.Refused, match="plan hash"):
        _run(connect, "apply", dd.plan_hash(), rollback=True)                      # the drop hash cannot authorise the inverse


# ───────────────────────── the command line ─────────────────────────

def test_main_refuses_a_wrong_hash_before_connecting_and_never_prints_a_secret(monkeypatch, capsys):
    monkeypatch.setattr(dd, "connect_admin", lambda: pytest.fail("connected before the plan hash was checked"))
    assert dd.main(["--apply", "--expect-plan", "bad"]) == 1
    assert dd.main(["--apply"]) == 2 and dd.main([]) == 2
    monkeypatch.setattr(dd, "connect_admin", lambda: (_ for _ in ()).throw(RuntimeError("password=hunter2 host=10.0.0.1")))
    assert dd.main(["--dry-run"]) == 1
    out = capsys.readouterr().out
    assert "hunter2" not in out and "10.0.0.1" not in out and "failed: RuntimeError" in out


def test_the_package_parses_under_the_python_311_grammar():
    import ast
    ast.parse(PKG.read_text(encoding="utf-8"), feature_version=(3, 11))
