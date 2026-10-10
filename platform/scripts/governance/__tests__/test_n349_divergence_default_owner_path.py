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


@pytest.fixture
def db(disposable_pg):
    """A fresh database with the roles and a chart_facts table; returns (cluster, dbname, make_conn)."""
    cl = disposable_pg
    cl.psql(ROLES_SQL)
    name = "n349_%d" % next(_counter)
    cl.psql("CREATE DATABASE %s" % name)
    cl.psql("GRANT ALL ON SCHEMA public TO PUBLIC", db=name)

    def table(owner="data_plane_l1_owner", column_sql="%s double precision DEFAULT 0.0" % COL):
        cl.psql("DROP TABLE IF EXISTS public.chart_facts", db=name)
        cl.psql("CREATE TABLE public.chart_facts (fact_id text NOT NULL, note text DEFAULT 'x', %s)" % column_sql, db=name)
        cl.psql("ALTER TABLE public.chart_facts OWNER TO %s" % owner, db=name)
        cl.psql("GRANT SELECT ON public.chart_facts TO n349_reader", db=name)

    table()

    def connect(user="n349_admin"):
        return psycopg.connect("postgresql://%s@%s:%d/%s" % (user, cl.host, cl.port, name))

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


def test_a_change_that_touches_anything_else_is_refused_and_rolled_back(db, monkeypatch):
    cl, name, connect, _ = db
    sabotaged = list(dd.DROP_STATEMENTS) + ["ALTER TABLE public.chart_facts ALTER COLUMN note DROP DEFAULT"]
    monkeypatch.setattr(dd, "DROP_STATEMENTS", sabotaged)
    with pytest.raises(dd.Refused, match="diff exactly the one planned line"):
        _run(connect, "apply", dd.plan_hash())
    assert _default(cl, name) == "0.0" and "note|f|'x'::text" in _state(cl, name)         # nothing was committed
    assert _member(cl, name) == "f"


def test_a_changed_acl_is_refused_and_rolled_back(db, monkeypatch):
    cl, name, connect, _ = db
    sabotaged = list(dd.DROP_STATEMENTS) + ["GRANT INSERT ON public.chart_facts TO n349_reader"]
    monkeypatch.setattr(dd, "DROP_STATEMENTS", sabotaged)
    with pytest.raises(dd.Refused, match="acl unchanged"):
        _run(connect, "apply", dd.plan_hash())
    assert _default(cl, name) == "0.0"


def test_the_statement_carries_a_lock_timeout_that_really_fires(db):
    assert dd.DROP_STATEMENTS[0] == "SET LOCAL lock_timeout = '5s'" and dd.RESTORE_STATEMENTS[0] == "SET LOCAL lock_timeout = '5s'"
    cl, name, connect, _ = db
    with connect(cl.user) as holder:                                            # an open reader (the cluster user) holds ACCESS SHARE on the table
        holder.execute("SELECT 1 FROM public.chart_facts LIMIT 1")
        with pytest.raises(psycopg.errors.LockNotAvailable):
            _run(connect, "apply", dd.plan_hash())
        holder.rollback()
    assert _default(cl, name) == "0.0"


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
