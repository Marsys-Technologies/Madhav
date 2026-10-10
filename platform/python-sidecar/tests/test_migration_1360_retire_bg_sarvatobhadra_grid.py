"""
Migration 1360 (SS ruling N-430): RETIRE the unbuilt registry asset bg_sarvatobhadra_grid and remove its depends_on edge from ka_vedha_gochara.

Two tiers:
  * STATIC (always runs): the file's own SQL text: transaction ownership, the exact SET lists of its two UPDATEs, no DDL/DML elsewhere, the guard
    and post-check blocks and what each one raises.
  * LIVE (needs PostgreSQL server binaries): applies the REAL on-disk migration to a DISPOSABLE cluster this module creates with initdb in a temp dir
    (own port, trust auth, removed at session end). Skipped, loudly, when no initdb/pg_ctl is found. No production or shared database is touched.

LIVE proves: the grid row ends is_active=false / RETIRED / RETAINED_AS_CAPITAL with superseded_by NULL and has_writer false; ka_vedha_gochara.depends_on is
its pre-state minus the grid edge (every other edge, in order); every other registry row and the grid TABLE are untouched; the production staling trigger
(596) stales exactly the two touched assets' freshness rows (ka_vedha_gochara on every chart) and no other; a second run rewrites nothing; the guard RAISES
(and rolls everything back) when the table has a row, when has_writer is true, when the table / grid row / ka_vedha_gochara row is missing, when another
asset depends on the grid, and on a conflicting superseded_by / data_disposition / dead_flag; and the post-checks RAISE when either UPDATE silently does
nothing. The fixture carries the REAL CHECK / FK constraints of migrations 328, 590 and 591 (the retired row must satisfy them).
It does NOT prove production state (read from production structure after deploy; Trap 103).
"""
from __future__ import annotations

import glob
import os
import re
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_M1360 = _REPO / "platform" / "migrations" / "1360_retire_bg_sarvatobhadra_grid.sql"

GRID = "bg_sarvatobhadra_grid"
VEDHA = "ka_vedha_gochara"
# ka_vedha_gochara.depends_on as the seed declares it (asset_registry_seed.ts); production may carry more or fewer edges, the migration removes ONE.
PRE_DEPS = ["ga_positions", "bg_ephemeris", "bg_transit_rules", GRID, "bg_vedha_malefic_scale", "bg_phaladeepika_latta"]
POST_DEPS = [d for d in PRE_DEPS if d != GRID]
CANON = "482012f1-710e-4a25-994a-93821f5871aa"
OTHER = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"


def _code(path: Path) -> str:
    return "\n".join(l for l in path.read_text().splitlines() if not l.lstrip().startswith("--"))


# -- STATIC tier --------------------------------------------------------------------------------------------------------

def test_static_lock_timeout_first_no_transaction_control_no_ddl_no_inserts_or_deletes():
    code = _code(_M1360)
    assert code.strip().startswith("SET LOCAL lock_timeout = '5s';")
    assert not re.search(r"\b(BEGIN|COMMIT|ROLLBACK)\b\s*;", code.replace("BEGIN\n", ""))   # plpgsql BEGIN has no semicolon
    assert not re.search(r"\b(CREATE|ALTER|DROP|TRUNCATE|GRANT|REVOKE|COMMENT\s+ON)\b", code, re.I)
    assert not re.search(r"\b(INSERT\s+INTO|DELETE\s+FROM)\b", code, re.I)


def test_static_exactly_two_updates_with_the_declared_set_lists_and_scoped_to_one_row_each():
    code = _code(_M1360)
    updates = re.findall(r"UPDATE\s+asset_registry\s+SET\s+(.*?)\s+WHERE\s+(asset_id\s*=\s*\w+)\s*;", code, re.S)
    assert len(updates) == 2 and len(re.findall(r"\bUPDATE\b", code)) == 2
    (set_a, where_a), (set_b, where_b) = updates
    assert re.sub(r"\s+", " ", set_a) == "is_active = false, catalog_status = 'RETIRED', data_disposition = 'RETAINED_AS_CAPITAL'"
    assert where_a == "asset_id = c_grid"
    assert re.sub(r"\s+", " ", set_b) == "depends_on = array_remove(depends_on, c_grid)"
    assert where_b == "asset_id = c_vedha"
    assert "superseded_by =" not in code.replace("superseded_by = %", "")          # superseded_by is never written (stays NULL)
    assert "c_grid    constant text := 'bg_sarvatobhadra_grid'" in code and "c_vedha   constant text := 'ka_vedha_gochara'" in code


def test_static_guard_raises_for_every_refusal_and_postchecks_exist():
    code = _code(_M1360)
    guard = code.split("IF v_active IS FALSE AND v_status = 'RETIRED'", 1)[0]                  # everything before the first write
    assert "UPDATE" not in guard
    for needle in ("v_has_writer IS DISTINCT FROM false", "to_regclass('public.bg_sarvatobhadra_grid') IS NULL",
                   "SELECT count(*) FROM public.bg_sarvatobhadra_grid", "v_rows <> 0", "v_succ IS NOT NULL",
                   "v_disp <> 'RETAINED_AS_CAPITAL'", "v_dead IS TRUE", "depends_on @> ARRAY[c_grid]::text[]", "asset_id <> c_vedha"):
        assert needle in guard, needle
    assert guard.count("RAISE EXCEPTION") == 9 and "RAISE NOTICE" not in guard
    post = code.split("WHERE asset_id = c_grid AND is_active IS FALSE", 1)[1]                    # the post-checks proper (after the last write)
    for needle in ("did not take", "still depend on the retired", "array_remove(v_pre_deps, c_grid)", "xmin = pg_current_xact_id()::xid"):
        assert needle in post, needle
    assert post.count("RAISE EXCEPTION") == 4 and "RAISE NOTICE" not in post and "UPDATE" not in post


# -- LIVE tier: disposable PostgreSQL -------------------------------------------------------------------------------------

def _find_pg_bin() -> Path | None:
    cands: list[Path] = []
    if os.environ.get("PG_BIN"):
        cands.append(Path(os.environ["PG_BIN"]))
    which = shutil.which("initdb")
    if which:
        cands.append(Path(which).parent)
    cands += [Path(p) for p in sorted(glob.glob("/opt/homebrew/opt/postgresql@*/bin"), reverse=True)]
    cands += [Path(p) for p in sorted(glob.glob("/usr/lib/postgresql/*/bin"), reverse=True)]
    for c in cands:
        if (c / "initdb").exists() and (c / "pg_ctl").exists():
            return c
    return None


@pytest.fixture(scope="session")
def pg_cluster():
    psycopg = pytest.importorskip("psycopg")
    binp = _find_pg_bin()
    if binp is None:
        pytest.skip("no PostgreSQL server binaries (initdb/pg_ctl) found; set PG_BIN")
    root = Path(tempfile.mkdtemp(prefix="m1360pg"))
    data = root / "data"
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    subprocess.run([str(binp / "initdb"), "-D", str(data), "-U", "postgres", "-A", "trust", "-E", "UTF8", "--no-sync"],
                   check=True, capture_output=True)
    opts = f"-p {port} -c listen_addresses=127.0.0.1 -c unix_socket_directories={root} -c fsync=off"
    subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-o", opts, "-w", "-l", str(root / "log"), "start"],
                   check=True, capture_output=True)
    try:
        yield {"port": port, "psycopg": psycopg}
    finally:
        subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-m", "immediate", "stop"], capture_output=True)
        shutil.rmtree(root, ignore_errors=True)


_n = 0


@pytest.fixture()
def db(pg_cluster):
    global _n
    _n += 1
    name = f"t{_n}"
    psycopg, port = pg_cluster["psycopg"], pg_cluster["port"]
    with psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"CREATE DATABASE {name}")

    def connect():
        return psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname=name)

    yield connect
    with psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)")


# The registry columns this migration reads or writes, with the REAL constraints: migration 328 (catalog_status), 590 (data_disposition CHECK,
# superseded_by FK + not-self CHECK), 591 (dead_flag_not_retired CHECK) and the 596 staling trigger on asset_registry.
_FIXTURE_DDL = """
CREATE TABLE asset_registry (
    asset_id text PRIMARY KEY, layer text NOT NULL, depends_on text[], is_active boolean NOT NULL DEFAULT true,
    catalog_status text NOT NULL DEFAULT 'CURRENT', has_writer boolean NOT NULL DEFAULT false, target_table text, count_sql text,
    superseded_by text, data_disposition text, dead_flag boolean, scope text, volume_explanation text,
    CONSTRAINT asset_registry_catalog_status_check CHECK (catalog_status = ANY (ARRAY['CURRENT','DRAFT','RETIRED'])),
    CONSTRAINT asset_registry_data_disposition_check CHECK (data_disposition IS NULL
        OR data_disposition IN ('RETAINED_AS_CAPITAL','SUPERSEDED_IN_PLACE','DROPPABLE')),
    CONSTRAINT asset_registry_superseded_by_fkey FOREIGN KEY (superseded_by) REFERENCES asset_registry(asset_id) ON DELETE RESTRICT,
    CONSTRAINT asset_registry_superseded_by_not_self CHECK (superseded_by IS NULL OR superseded_by <> asset_id),
    CONSTRAINT asset_registry_dead_flag_not_retired CHECK (dead_flag IS NOT TRUE OR (catalog_status <> 'RETIRED' AND is_active IS NOT FALSE)));
CREATE TABLE bg_sarvatobhadra_grid (id bigserial PRIMARY KEY, school_tag text NOT NULL, cell_index int NOT NULL, cell_kind text NOT NULL,
    cell_value text NOT NULL, table_version text NOT NULL);
CREATE TABLE asset_freshness (
    asset_id text NOT NULL, chart_id uuid, scope_key text GENERATED ALWAYS AS (COALESCE(chart_id::text, '__global__')) STORED,
    partition_key text NOT NULL DEFAULT '__whole_asset__', freshness_state text NOT NULL,
    reasons jsonb NOT NULL DEFAULT '[]'::jsonb, observed_at timestamptz NOT NULL DEFAULT '2026-10-01T00:00:00Z',
    PRIMARY KEY (asset_id, scope_key, partition_key));
CREATE OR REPLACE FUNCTION nirmana_invalidate_registry_receipts() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  UPDATE asset_freshness SET freshness_state = 'stale',
         reasons = CASE WHEN reasons ? 'registry_changed' THEN reasons ELSE reasons || '["registry_changed"]'::jsonb END,
         observed_at = now()
   WHERE asset_id = NEW.asset_id;
  RETURN NEW;
END; $$;
CREATE TRIGGER nirmana_registry_receipt_invalidation
AFTER UPDATE OF depends_on, has_writer, is_active, target_table ON asset_registry
FOR EACH ROW WHEN (OLD IS DISTINCT FROM NEW) EXECUTE FUNCTION nirmana_invalidate_registry_receipts();
"""


def _setup(connect, *, grid_row=True, vedha_row=True, grid_table=True, grid_rows=0, has_writer=False, vedha_deps=None, dependents=(),
           superseded_by=None, disposition=None, dead_flag=None, is_active=True, status="CURRENT"):
    deps = PRE_DEPS if vedha_deps is None else vedha_deps
    with connect() as c:
        c.execute(_FIXTURE_DDL)
        if not grid_table:
            c.execute("DROP TABLE bg_sarvatobhadra_grid")
        elif grid_rows:
            c.execute("INSERT INTO bg_sarvatobhadra_grid (school_tag, cell_index, cell_kind, cell_value, table_version) "
                      "SELECT 's', g, 'vedha_pair', 'x', 'v01' FROM generate_series(1, %s) g", (grid_rows,))
        c.execute("INSERT INTO asset_registry (asset_id, layer, depends_on, has_writer, scope) VALUES ('successor_x','kala','{}',true,'global')")
        for other in ("ga_positions", "bg_ephemeris", "bg_transit_rules", "bg_vedha_malefic_scale", "bg_phaladeepika_latta"):
            c.execute("INSERT INTO asset_registry (asset_id, layer, depends_on, has_writer) VALUES (%s,'x','{}',%s)", (other, other == "ga_positions"))
        if grid_row:
            c.execute("INSERT INTO asset_registry (asset_id, layer, depends_on, is_active, catalog_status, has_writer, target_table, count_sql, "
                      "superseded_by, data_disposition, dead_flag, scope) VALUES (%s,'brahmagyan','{}',%s,%s,%s,%s,%s,%s,%s,%s,'global')",
                      (GRID, is_active, status, has_writer, GRID, "SELECT COUNT(*) FROM bg_sarvatobhadra_grid", superseded_by, disposition, dead_flag))
        if vedha_row:
            c.execute("INSERT INTO asset_registry (asset_id, layer, depends_on, has_writer, target_table, scope) "
                      "VALUES (%s,'kala',%s,true,'kala_vedha_gochara','per_chart')", (VEDHA, deps))
        for d in dependents:
            c.execute("INSERT INTO asset_registry (asset_id, layer, depends_on) VALUES (%s,'kala',%s)", (d, [GRID]))
        # freshness: the grid's global sentinel (migration 911), ka_vedha_gochara on two charts, and an unrelated asset on the canonical chart
        c.execute("INSERT INTO asset_freshness (asset_id, chart_id, freshness_state) VALUES (%s, NULL, 'fresh')", (GRID,))
        for chart in (CANON, OTHER):
            c.execute("INSERT INTO asset_freshness (asset_id, chart_id, freshness_state) VALUES (%s, %s, 'fresh')", (VEDHA, chart))
        c.execute("INSERT INTO asset_freshness (asset_id, chart_id, freshness_state) VALUES ('ga_positions', %s, 'fresh')", (CANON,))
        c.commit()


def _apply(connect, capture_notices: list[str] | None = None):
    conn = connect()
    if capture_notices is not None:
        conn.add_notice_handler(lambda d: capture_notices.append(d.message_primary))
    try:
        conn.execute(_M1360.read_text())
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _q(connect, sql, params=None):
    with connect() as c:
        return c.execute(sql, params).fetchall()


def _snapshot(connect):
    return _q(connect, "SELECT to_jsonb(r)::text, xmin::text FROM asset_registry r ORDER BY asset_id")


def _grid(connect):
    return _q(connect, "SELECT is_active, catalog_status, data_disposition, superseded_by, has_writer, dead_flag FROM asset_registry WHERE asset_id=%s", (GRID,))[0]


def _refuses(db, fragment, **setup):
    """The migration RAISEs with `fragment`, and the registry is exactly as it was (the migration rolled back)."""
    _setup(db, **setup)
    before = _snapshot(db)
    with pytest.raises(Exception) as ei:
        _apply(db)
    assert fragment in str(ei.value), str(ei.value)
    assert _snapshot(db) == before


def test_live_retires_the_grid_and_removes_exactly_the_one_edge(db):
    _setup(db)
    before = {r[0]: r for r in _q(db, "SELECT asset_id, to_jsonb(r) - 'is_active' - 'catalog_status' - 'data_disposition' - 'depends_on' FROM asset_registry r")}
    _apply(db)
    assert _grid(db) == (False, "RETIRED", "RETAINED_AS_CAPITAL", None, False, None)
    assert _q(db, "SELECT depends_on FROM asset_registry WHERE asset_id=%s", (VEDHA,))[0][0] == POST_DEPS      # order preserved, five edges remain
    assert _q(db, "SELECT asset_id FROM asset_registry WHERE depends_on @> ARRAY[%s]::text[]", (GRID,)) == []
    # nothing else on either touched row changed, and no other row version changed at all
    after = {r[0]: r for r in _q(db, "SELECT asset_id, to_jsonb(r) - 'is_active' - 'catalog_status' - 'data_disposition' - 'depends_on' FROM asset_registry r")}
    assert after == before
    # the table is kept and still empty
    assert _q(db, "SELECT count(*) FROM bg_sarvatobhadra_grid")[0][0] == 0
    # the census population filter (`is_active AND NOT dead_flag`) no longer contains the grid, and contains ka_vedha_gochara
    active = {r[0] for r in _q(db, "SELECT asset_id FROM asset_registry WHERE is_active AND NOT coalesce(dead_flag,false)")}
    assert GRID not in active and VEDHA in active
    # every active asset's depends_on resolves to an active asset (what Build.dag's `exists` clause requires)
    dangling = _q(db, "SELECT a.asset_id, d FROM asset_registry a, unnest(a.depends_on) d "
                      "WHERE a.is_active AND NOT EXISTS (SELECT 1 FROM asset_registry b WHERE b.asset_id = d AND b.is_active)")
    assert dangling == []


def test_live_keeping_the_edge_on_an_inactive_grid_would_leave_a_dangling_dependency(db):
    """The reason (c) exists: with only (b) applied the exists-resolution above would fail for ka_vedha_gochara."""
    _setup(db)
    with db() as c:
        c.execute("UPDATE asset_registry SET is_active=false, catalog_status='RETIRED', data_disposition='RETAINED_AS_CAPITAL' WHERE asset_id=%s", (GRID,))
        c.commit()
    dangling = _q(db, "SELECT a.asset_id, d FROM asset_registry a, unnest(a.depends_on) d "
                      "WHERE a.is_active AND NOT EXISTS (SELECT 1 FROM asset_registry b WHERE b.asset_id = d AND b.is_active)")
    assert dangling == [(VEDHA, GRID)]


def test_live_the_staling_trigger_stales_exactly_the_two_touched_assets_on_every_chart(db):
    _setup(db)
    _apply(db)
    rows = _q(db, "SELECT asset_id, coalesce(chart_id::text,'global'), freshness_state, reasons::text FROM asset_freshness ORDER BY 1, 2")
    state = {(a, c): (s, r) for a, c, s, r in rows}
    assert state[(GRID, "global")][0] == "stale" and "registry_changed" in state[(GRID, "global")][1]
    assert state[(VEDHA, CANON)][0] == "stale" and state[(VEDHA, OTHER)][0] == "stale"          # per-chart asset: stale on EVERY chart
    assert state[("ga_positions", CANON)][0] == "fresh"                                           # an untouched asset is not staled
    # the sentinel rows are kept, not deleted
    assert len(rows) == 4


def test_live_second_run_rewrites_nothing_and_says_so(db):
    _setup(db)
    _apply(db)
    x1 = _snapshot(db)
    notes: list[str] = []
    _apply(db, notes)
    assert _snapshot(db) == x1                                       # content and xmin of every row identical
    assert any("already RETIRED" in n for n in notes) and any("edge already removed" in n for n in notes)
    assert _grid(db) == (False, "RETIRED", "RETAINED_AS_CAPITAL", None, False, None)


def test_live_an_edge_that_is_absent_already_is_a_notice_not_a_failure(db):
    _setup(db, vedha_deps=POST_DEPS)
    notes: list[str] = []
    _apply(db, notes)
    assert _q(db, "SELECT depends_on FROM asset_registry WHERE asset_id=%s", (VEDHA,))[0][0] == POST_DEPS
    assert _grid(db)[:3] == (False, "RETIRED", "RETAINED_AS_CAPITAL")


def test_live_a_pre_existing_matching_disposition_is_accepted(db):
    _setup(db, disposition="RETAINED_AS_CAPITAL")
    _apply(db)
    assert _grid(db)[:3] == (False, "RETIRED", "RETAINED_AS_CAPITAL")


# -- guard refusals: each RAISEs and rolls the whole migration back ---------------------------------------------------------

def test_live_guard_refuses_when_the_table_has_a_row(db):
    _refuses(db, "has 1 row(s)", grid_rows=1)


def test_live_guard_refuses_when_the_table_has_many_rows(db):
    _refuses(db, "has 81 row(s)", grid_rows=81)


def test_live_guard_refuses_when_the_asset_has_a_writer(db):
    _refuses(db, "has_writer = t", has_writer=True)


def test_live_guard_refuses_when_the_table_is_missing(db):
    _refuses(db, "table bg_sarvatobhadra_grid does not exist", grid_table=False)


def test_live_guard_refuses_when_the_grid_registry_row_is_missing(db):
    _refuses(db, "expected exactly one asset_registry row", grid_row=False)


def test_live_guard_refuses_when_ka_vedha_gochara_is_missing(db):
    _refuses(db, "no asset_registry row for ka_vedha_gochara", vedha_row=False)


def test_live_guard_refuses_when_another_asset_depends_on_the_grid(db):
    _refuses(db, "asset(s) other than ka_vedha_gochara depend on bg_sarvatobhadra_grid: ka_other_a, ka_other_b", dependents=("ka_other_b", "ka_other_a"))


def test_live_guard_refuses_a_declared_successor(db):
    _refuses(db, "already declares superseded_by = successor_x", superseded_by="successor_x")


def test_live_guard_refuses_a_conflicting_disposition(db):
    _refuses(db, "conflicting data_disposition = DROPPABLE", disposition="DROPPABLE")


def test_live_guard_refuses_dead_flag_true(db):
    _refuses(db, "dead_flag = true", dead_flag=True)


# -- post-checks: a silent no-op of either UPDATE is caught -------------------------------------------------------------------

def test_live_post_check_catches_a_silent_noop_of_the_retirement(db):
    _setup(db)
    with db() as c:
        c.execute("CREATE RULE swallow AS ON UPDATE TO asset_registry WHERE OLD.asset_id = 'bg_sarvatobhadra_grid' DO INSTEAD NOTHING")
        c.commit()
    before = _snapshot(db)
    with pytest.raises(Exception) as ei:
        _apply(db)
    assert "did not take" in str(ei.value)
    assert _snapshot(db) == before


def test_live_post_check_catches_a_silent_noop_of_the_edge_removal(db):
    _setup(db)
    with db() as c:
        c.execute("CREATE RULE swallow AS ON UPDATE TO asset_registry WHERE OLD.asset_id = 'ka_vedha_gochara' DO INSTEAD NOTHING")
        c.commit()
    before = _snapshot(db)
    with pytest.raises(Exception) as ei:
        _apply(db)
    assert "still depend on the retired bg_sarvatobhadra_grid: ka_vedha_gochara" in str(ei.value)
    assert _snapshot(db) == before


def test_live_the_retired_row_satisfies_the_real_590_and_591_constraints(db):
    """The fixture carries the real CHECKs; applying succeeds only because the retired row satisfies all of them, and a dead_flag=true row cannot be retired."""
    _setup(db)
    _apply(db)
    with pytest.raises(Exception) as ei:
        with db() as c:
            c.execute("UPDATE asset_registry SET dead_flag = true WHERE asset_id=%s", (GRID,))
    assert "asset_registry_dead_flag_not_retired" in str(ei.value)
