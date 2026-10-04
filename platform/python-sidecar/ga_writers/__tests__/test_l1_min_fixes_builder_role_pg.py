"""TI-l1-min-fixes-001 -- the two minimum S-L1 fixes, proven on a REAL Postgres
with the production power structure (owner role `amjis_app`, LOGIN builder role
`data_plane_builder`) from the shared fixture tests/l3/_builder_role.py.

Background (swallow audit): the S-L1 job runs as `data_plane_builder`; L1 writers
share the orchestrator's single transaction (`ctx.db_conn`) and swallow DB errors,
leaving it ABORTED.

(b) ga_sade_sati_writer._refresh_mv -- `mv_chart_sade_sati_lifetime_summary` is
    owned by amjis_app and the builder is not a member, so REFRESH fails with
    "must be owner of materialized view", the writer swallowed it, and the
    transaction was left aborted: a deterministic build abort.  Fix: skip the
    refresh when the connection does not own the view.

(c) data_plane_runtime.guarded -- universal guard: after a decorated writer
    returns, an aborted transaction (psycopg `TransactionStatus.INERROR`) raises
    a named ContractError instead of surfacing later as an opaque
    InFailedSqlTransaction (or not at all).

Requires a THROWAWAY database; skipped unless C7_BUILDER_ROLE_TEST_DATABASE_URL is
set (same disposable identity as the C7/C15/C18/C19 suites):

  createdb -h 127.0.0.1 -p 55442 -U postgres c7_builder_role_test
  C7_BUILDER_ROLE_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55442/c7_builder_role_test \
    python -m pytest ga_writers/__tests__/test_l1_min_fixes_builder_role_pg.py -q

The test-double case at the bottom needs no database and always runs.
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

SIDECAR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SIDECAR))
sys.path.insert(0, str(SIDECAR / "tests" / "l3"))

import _builder_role as BR  # noqa: E402
from ga_writers import data_plane_runtime as dpr  # noqa: E402
from ga_writers import ga_sade_sati_writer as ssw  # noqa: E402
from ga_writers.data_plane_contracts import ContractError  # noqa: E402
from pipeline.orchestrator.writers import WriterResult  # noqa: E402

DSN = os.environ.get("C7_BUILDER_ROLE_TEST_DATABASE_URL")
# Visible deselection in the generic sidecar job (`-m "not integration"`); this file's own CI step
# runs it explicitly with the disposable-Postgres DSN and no -m filter. (`integration` is used
# unregistered across tests/; no --strict-markers is configured anywhere.)
pytestmark = pytest.mark.integration

# Locally an unset DSN SKIPS (NOT_RUN). Under GitHub Actions it must FAIL, never skip: a suite that
# silently skips in CI is green without being evidence (CLAUDE.md §N.8). In CI `needs_pg` is a
# no-op so the tests run and the `world` fixture fails with a clear message.
_IN_CI = os.environ.get("GITHUB_ACTIONS", "").strip().lower() == "true"
needs_pg = (lambda fn: fn) if _IN_CI else pytest.mark.skipif(
    not DSN, reason="NOT_RUN: set C7_BUILDER_ROLE_TEST_DATABASE_URL to the disposable Postgres"
)

# ── local DSN safety (in addition to BR.require_disposable, which we must not edit) ───────────────
# When this lane was written BR.require_disposable read urlparse(dsn).hostname, which sees only the
# FIRST host of a multi-host URI (`postgresql://u:p@localhost:5432,db.prod.example.com:5432/c7_builder_role_test`
# passed it and libpq would fail over to the second host). Main's C24/C25 (#2978, #2980) has since moved
# the checks into the shared guard tests/l3/_disposable_db_guard.py, which now refuses that DSN too; this
# local validation is kept as a second, independent layer. This fixture drops schema public and alters
# cluster roles, so the whole libpq target (hosts, hostaddrs, dbname, env overrides) is validated here first.
# A refused DSN FAILS in every environment (never skips, in CI or locally).

_LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})
_EXPECTED_DB = BR.EXPECTED_DB_NAME
_QUERY_TARGET_KEYS = frozenset({"host", "hostaddr", "dbname", "service"})


def _is_loopback_or_socket(entry: str) -> bool:
    return entry in _LOOPBACK_HOSTS or entry.startswith("/")


def refuse_unsafe_dsn(dsn: str, env: "dict[str, str] | None" = None) -> None:
    """Raise ValueError unless every libpq target in `dsn` (and the environment) is a loopback
    host or unix socket and the database is exactly the disposable one."""
    from urllib.parse import parse_qsl, urlparse

    from psycopg.conninfo import conninfo_to_dict

    env = os.environ if env is None else env
    parsed = urlparse(dsn)
    if "," in (parsed.netloc or ""):
        raise ValueError("REFUSED: ',' in the DSN authority (multi-host failover list)")
    if parsed.scheme in ("postgresql", "postgres"):
        overrides = {k.lower() for k, _ in parse_qsl(parsed.query)} & _QUERY_TARGET_KEYS
        if overrides:
            raise ValueError(f"REFUSED: query-string target override(s) {sorted(overrides)}")
    info = conninfo_to_dict(dsn)
    for key in ("host", "hostaddr"):
        if "," in info.get(key, ""):
            raise ValueError(f"REFUSED: ',' in {key} (multi-host failover list)")
    entries = [e for key in ("host", "hostaddr") for e in info.get(key, "").split(",") if e]
    if not info.get("host") and not info.get("hostaddr"):
        raise ValueError("REFUSED: the DSN names no host (the target would come from the environment)")
    bad = [e for e in entries if not _is_loopback_or_socket(e)]
    if bad:
        raise ValueError(f"REFUSED: non-loopback host/hostaddr {bad}")
    if info.get("dbname") != _EXPECTED_DB:
        raise ValueError(f"REFUSED: dbname {info.get('dbname')!r} is not {_EXPECTED_DB!r}")
    # Environment overrides libpq would honour: PGHOSTADDR redirects the connection even when the
    # DSN names a host; PGHOST/PGDATABASE would redirect a DSN that omits them; PGSERVICE can fill
    # any unset parameter from a service file we cannot see.
    for var in ("PGHOST", "PGHOSTADDR"):
        env_bad = [e for e in env.get(var, "").split(",") if e and not _is_loopback_or_socket(e)]
        if env_bad:
            raise ValueError(f"REFUSED: environment {var} names non-loopback {env_bad}")
    if env.get("PGDATABASE") and env["PGDATABASE"] != _EXPECTED_DB:
        raise ValueError(f"REFUSED: environment PGDATABASE {env['PGDATABASE']!r} is not {_EXPECTED_DB!r}")
    if env.get("PGSERVICE"):
        raise ValueError("REFUSED: environment PGSERVICE is set (a service file could redirect the target)")


MV = "mv_chart_sade_sati_lifetime_summary"
CHART = "11111111-1111-4111-8111-111111111111"
BUILD = "22222222-2222-4222-8222-222222222222"


@pytest.fixture(scope="module")
def world():
    import psycopg

    if not DSN:
        pytest.fail(
            "C7_BUILDER_ROLE_TEST_DATABASE_URL is unset under GITHUB_ACTIONS: this suite must run "
            "against the disposable Postgres in CI, never skip"
        )
    try:
        refuse_unsafe_dsn(DSN)
    except ValueError as exc:
        pytest.fail(str(exc))  # a refused DSN fails in every environment, never skips
    BR.require_disposable(DSN)
    admin = psycopg.connect(DSN, autocommit=True, connect_timeout=5)
    try:
        BR.provision(admin)
        with BR.as_owner(admin):
            admin.execute("CREATE TABLE sade_sati_src (x int PRIMARY KEY)")
            admin.execute("INSERT INTO sade_sati_src VALUES (1), (2)")
            admin.execute(f"CREATE MATERIALIZED VIEW {MV} AS SELECT x FROM sade_sati_src")
            # unique index => REFRESH ... CONCURRENTLY is legal for the owner
            admin.execute(f"CREATE UNIQUE INDEX {MV}_u ON {MV} (x)")
        yield admin
    finally:
        try:
            admin.execute("DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;")
            for role in (BR.BUILDER_ROLE, BR.OWNER_ROLE):
                admin.execute(f"DROP OWNED BY {role} CASCADE")
        finally:
            admin.close()


def _mv_rows(admin) -> int:
    return admin.execute(f"SELECT count(*) FROM {MV}").fetchone()[0]


def _src_rows(admin) -> int:
    return admin.execute("SELECT count(*) FROM sade_sati_src").fetchone()[0]


def _add_source_row(admin, x: int) -> None:
    with BR.as_owner(admin):
        admin.execute("INSERT INTO sade_sati_src VALUES (%s) ON CONFLICT DO NOTHING", [x])


def _status(conn) -> str:
    return conn.info.transaction_status.name


# ── (b) skip the refresh when the connection does not own the view ───────────

@needs_pg
def test_non_owner_builder_skips_refresh_and_transaction_stays_healthy(world, caplog):
    import psycopg.rows

    stale_before = _mv_rows(world)
    _add_source_row(world, 100 + stale_before)  # source moves; MV must stay stale
    assert _mv_rows(world) == stale_before

    with BR.connect_as_builder(DSN, row_factory=psycopg.rows.dict_row) as conn:
        assert conn.execute("SELECT session_user").fetchone()["session_user"] == BR.BUILDER_ROLE
        with caplog.at_level(logging.INFO, logger=ssw.logger.name):
            outcome = ssw._refresh_mv(conn)
        assert outcome == "skipped_not_owner"
        # the transaction must be healthy: not INERROR, and still usable
        assert _status(conn) != "INERROR"
        assert conn.execute("SELECT 1 AS one").fetchone()["one"] == 1
        conn.rollback()

    assert _mv_rows(world) == stale_before  # not refreshed
    msgs = [r for r in caplog.records if "NOT refreshed" in r.getMessage()]
    assert msgs and msgs[0].levelno == logging.INFO
    assert BR.OWNER_ROLE in msgs[0].getMessage()


@needs_pg
def test_non_owner_with_tuple_rows_also_skips(world):
    with BR.connect_as_builder(DSN) as conn:
        assert ssw._refresh_mv(conn) == "skipped_not_owner"
        assert _status(conn) != "INERROR"
        conn.rollback()


@needs_pg
def test_owner_connection_refreshes(world):
    import psycopg

    before = _mv_rows(world)
    _add_source_row(world, 1000 + before)
    assert _mv_rows(world) < _src_rows(world)  # stale until refreshed
    with psycopg.connect(DSN, connect_timeout=5) as conn:  # superuser login...
        conn.execute(f"SET ROLE {BR.OWNER_ROLE}")  # ...acting as the view's owner
        assert conn.execute("SELECT current_user").fetchone()[0] == BR.OWNER_ROLE
        assert ssw._refresh_mv(conn) == "refreshed"
        assert _status(conn) != "INERROR"
        conn.commit()
    assert _mv_rows(world) == _src_rows(world) > before


@needs_pg
def test_absent_view_is_skipped_not_attempted(world, monkeypatch):
    monkeypatch.setattr(ssw, "SADE_SATI_MV", "mv_does_not_exist_anywhere")
    with BR.connect_as_builder(DSN) as conn:
        assert ssw._refresh_mv(conn) == "skipped_not_owner"
        assert _status(conn) != "INERROR"
        conn.rollback()


@needs_pg
def test_prefix_behaviour_was_a_deterministic_abort(world):
    """Control: the pre-fix body (unconditional REFRESH, errors swallowed) run as
    the builder leaves the transaction INERROR -- the defect these fixes close."""
    with BR.connect_as_builder(DSN) as conn:
        try:
            conn.execute(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {MV}")
        except Exception:
            try:
                conn.execute(f"REFRESH MATERIALIZED VIEW {MV}")
            except Exception:
                pass
        assert _status(conn) == "INERROR"
        conn.rollback()


# ── (c) universal guard ──────────────────────────────────────────────────────

class _Recorder:
    def __init__(self, monkeypatch):
        self.opened: list[str] = []
        self.completed: list[str] = []
        monkeypatch.setattr(
            dpr, "_open_partition",
            lambda ctx, *, asset_id, partition_key, expected_partitions: self.opened.append(partition_key),
        )
        monkeypatch.setattr(
            dpr, "_complete_partition",
            lambda ctx, *, asset_id, partition_key, rows_inserted: self.completed.append(partition_key),
        )


def _ctx(conn):
    return SimpleNamespace(
        dry_run=False, db_conn=conn, build_id=BUILD, config={"chart_id": CHART}, asset_id="ga_positions"
    )


def _light_writer(body):
    class W:
        asset_id = "ga_positions"

        def run(self, ctx):
            return body(ctx)

    return dpr.l1_producer_contract(W)


@needs_pg
def test_guard_raises_named_error_when_writer_swallows_a_db_error(world, monkeypatch):
    rec = _Recorder(monkeypatch)

    def swallowing(ctx):
        try:
            ctx.db_conn.execute("SELECT * FROM table_that_does_not_exist")
        except Exception:
            pass  # the audited defect: swallowed, transaction left aborted
        return WriterResult(asset_id="ga_positions", rows_inserted=3)

    W = _light_writer(swallowing)
    with BR.connect_as_builder(DSN) as conn:
        with pytest.raises(ContractError, match="writer swallowed a DB error: transaction is aborted") as ei:
            W().run(_ctx(conn))
        assert "ga_positions" in str(ei.value)
        assert _status(conn) == "INERROR"  # the error is about a real aborted txn
        conn.rollback()
    assert rec.opened == ["ga_positions"]
    assert rec.completed == []  # never reached the partition-complete step


@needs_pg
def test_guard_does_not_affect_a_healthy_writer(world, monkeypatch):
    rec = _Recorder(monkeypatch)

    def healthy(ctx):
        assert ctx.db_conn.execute("SELECT 41 + 1").fetchone()[0] == 42
        return WriterResult(asset_id="ga_positions", rows_inserted=7)

    W = _light_writer(healthy)
    with BR.connect_as_builder(DSN) as conn:
        result = W().run(_ctx(conn))
        assert result.rows_inserted == 7
        assert _status(conn) != "INERROR"
        conn.rollback()
    assert rec.completed == ["ga_positions"]


@needs_pg
def test_guard_allows_a_db_error_handled_inside_a_savepoint(world, monkeypatch):
    """A legitimately recovered error (savepoint rollback) leaves the transaction
    healthy: the guard must not flag it."""
    rec = _Recorder(monkeypatch)

    def recovered(ctx):
        try:
            with ctx.db_conn.transaction():  # savepoint
                ctx.db_conn.execute("SELECT * FROM table_that_does_not_exist")
        except Exception:
            pass
        return WriterResult(asset_id="ga_positions", rows_inserted=1)

    W = _light_writer(recovered)
    with BR.connect_as_builder(DSN) as conn:
        assert W().run(_ctx(conn)).rows_inserted == 1
        assert _status(conn) != "INERROR"
        conn.rollback()
    assert rec.completed == ["ga_positions"]


@needs_pg
def test_guard_covers_the_substep_shape(world, monkeypatch):
    rec = _Recorder(monkeypatch)

    class H:
        asset_id = "ga_sensitive"
        has_substeps = True

        def plan_substeps(self, ctx):
            return [SimpleNamespace(key="ayanamsha:lahiri")]

        def run_substep(self, ctx, step):
            try:
                ctx.db_conn.execute("SELECT * FROM table_that_does_not_exist")
            except Exception:
                pass
            return WriterResult(asset_id="ga_sensitive", rows_inserted=2)

    W = dpr.l1_producer_contract(H)
    with BR.connect_as_builder(DSN) as conn:
        with pytest.raises(ContractError, match="transaction is aborted") as ei:
            W().run_substep(_ctx(conn), SimpleNamespace(key="ayanamsha:lahiri"))
        assert "ga_sensitive" in str(ei.value) and "ayanamsha:lahiri" in str(ei.value)
        conn.rollback()
    assert rec.completed == []


# ── no database needed ───────────────────────────────────────────────────────

def test_contract_test_doubles_stay_ignored(monkeypatch):
    """A conn flagged `_l1_contract_test_double` is never inspected, even if it
    claims an aborted transaction."""
    from psycopg.pq import TransactionStatus

    rec = _Recorder(monkeypatch)

    class Double:
        _l1_contract_test_double = True
        info = SimpleNamespace(transaction_status=TransactionStatus.INERROR)

    W = _light_writer(lambda ctx: WriterResult(asset_id="ga_positions", rows_inserted=5))
    assert W().run(_ctx(Double())).rows_inserted == 5
    assert rec.completed == ["ga_positions"]


# ── no database needed: the DSN refusal ──────────────────────────────────────────────────────────

GOOD = "postgresql://postgres:postgres@localhost:5432/c7_builder_role_test"


@pytest.mark.parametrize("dsn", [
    GOOD,
    "postgresql://postgres@127.0.0.1:55442/c7_builder_role_test",
    "postgresql://postgres@[::1]:5432/c7_builder_role_test",
    "host=/tmp/pg_socket_dir dbname=c7_builder_role_test",
    "host=localhost dbname=c7_builder_role_test user=postgres",
])
def test_dsn_guard_accepts_loopback_and_socket_targets(dsn):
    refuse_unsafe_dsn(dsn, env={})


@pytest.mark.parametrize(("dsn", "why"), [
    ("postgresql://u:p@localhost:5432,db.prod.example.com:5432/c7_builder_role_test", "','"),
    ("postgresql://u@localhost,db.prod.example.com/c7_builder_role_test", "','"),
    ("postgresql://u@localhost:5432,10.0.0.5:5432/c7_builder_role_test", "','"),
    ("postgresql://u@localhost,10.0.0.5/c7_builder_role_test", "','"),
    ("host=localhost,10.0.0.5 dbname=c7_builder_role_test", "','"),
    ("hostaddr=127.0.0.1,10.0.0.5 host=localhost dbname=c7_builder_role_test", "','"),
    ("postgresql://u@localhost/c7_builder_role_test?host=db.prod.example.com", "query-string"),
    ("postgresql://u@localhost/c7_builder_role_test?hostaddr=10.1.1.1", "query-string"),
    ("postgresql:///c7_builder_role_test?host=/tmp/pg_socket_dir", "query-string"),
    ("postgresql://u@localhost/c7_builder_role_test?dbname=postgres", "query-string"),
    ("postgresql://u@localhost/c7_builder_role_test?service=prod", "query-string"),
    ("postgresql://u@db.prod.example.com:5432/c7_builder_role_test", "non-loopback"),
    ("postgresql://u@10.0.0.5/c7_builder_role_test", "non-loopback"),
    ("host=localhost hostaddr=10.0.0.5 dbname=c7_builder_role_test", "non-loopback"),
    ("postgresql://u@localhost:5432/postgres", "dbname"),
    ("postgresql://u@localhost:5432/", "dbname"),
    ("postgresql://u@localhost:5432/c7_builder_role_test_other", "dbname"),
    ("postgresql:///c7_builder_role_test", "names no host"),
])
def test_dsn_guard_refuses_unsafe_targets(dsn, why):
    with pytest.raises(ValueError, match="REFUSED") as ei:
        refuse_unsafe_dsn(dsn, env={})
    assert why in str(ei.value)


@pytest.mark.parametrize(("env", "why"), [
    ({"PGHOSTADDR": "10.0.0.5"}, "PGHOSTADDR"),
    ({"PGHOSTADDR": "127.0.0.1,10.0.0.5"}, "PGHOSTADDR"),
    ({"PGHOST": "db.prod.example.com"}, "PGHOST"),
    ({"PGHOST": "localhost,db.prod.example.com"}, "PGHOST"),
    ({"PGDATABASE": "postgres"}, "PGDATABASE"),
    ({"PGSERVICE": "prod"}, "PGSERVICE"),
])
def test_dsn_guard_refuses_environment_overrides(env, why):
    with pytest.raises(ValueError, match="REFUSED") as ei:
        refuse_unsafe_dsn(GOOD, env=env)
    assert why in str(ei.value)


def test_dsn_guard_allows_loopback_environment():
    refuse_unsafe_dsn(GOOD, env={"PGHOST": "localhost", "PGHOSTADDR": "127.0.0.1",
                                 "PGDATABASE": "c7_builder_role_test"})


def test_shared_fixture_guard_and_local_guard_both_refuse_the_multihost_dsn():
    """Both layers refuse a multi-host DSN. Integration merge interaction (S-L1): at the time this lane
    was written BR.require_disposable accepted the first host (the local refusal existed for that reason);
    main's C24/C25 shared guard (tests/l3/_disposable_db_guard.py) now refuses it as well, so the shared
    fixture guard is asserted to REFUSE and the local one is kept as the independent second layer."""
    multi = "postgresql://u:p@localhost:5432,db.prod.example.com:5432/c7_builder_role_test"
    with pytest.raises(RuntimeError, match="REFUSED"):
        BR.require_disposable(multi)
    with pytest.raises(ValueError, match="REFUSED"):
        refuse_unsafe_dsn(multi, env={})
