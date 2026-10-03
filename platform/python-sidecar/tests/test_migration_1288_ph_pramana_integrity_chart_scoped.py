"""
Migration 1288 (Suvarna, SS N-120): ph_pramana's registered integrity_check_sql becomes CHART-SCOPED (the chart being built is read from the
orchestrator's committed state, because the check is executed UNBOUND). HELD draft, routine path.

STATIC tier: the OLD text is migration 681's ph_pramana check = the live production md5; the NEW text hashes to the named md5/length, contains no bind
placeholder and has the scope structure; file shape, guards, header.
LIVE tier (PostgreSQL binaries; REQUIRE_PG_BINARIES=1 makes a skip a failure; PG_BINS=<path:path> runs several majors): applies the REAL file AS amjis_app
on a cluster with the production roles and schema ACL from the W1 privilege audit (fixtures/w1_roles.sql, fixtures/w1_schema_acl.sql, verbatim: amjis_app
has USAGE only and no CREATE on public; every table is owned by amjis_app), with the real nirmana_registry_receipt_invalidation trigger. The check text is
EXECUTED the way the orchestrator executes it (cursor.execute(sql), no parameters, same transaction as the writer) in the states: today (both charts
consistent), after the #3072 delete (8 life_event_miss rows of the second chart removed), after a synthetic rebuild; outside a build and inside a build for
each chart; with corruption in the chart being built / in the other chart; zombie and planned runs; concurrent runs. A mutation section requires every
mutant (of the migration and of the check text) to be caught.
"""
from __future__ import annotations

import glob
import hashlib
import os
import re
import shutil
import socket
import subprocess
import tempfile
import time
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_REPO = Path(__file__).resolve().parents[3]
_MIG = _REPO / "platform" / "migrations"
_M1288 = _MIG / "1288_ph_pramana_integrity_check_chart_scoped.sql"
_M681 = _MIG / "681_l4_phala_c12_registry_contracts.sql"
_REAL = _M1288.read_text()
OLD_MD5, NEW_MD5, OLD_LEN, NEW_LEN = "45f89d4853b157e22507ffccdb9af0e0", "c3f1b7949ebfda27ab959e55c2a14898", 1284, 3398
NEW_SHA256 = "040cf925736b063b41b894812835d6c97fcc0083544c899efa2978020f46267f"
CHART_A = "482012f1-710e-4a25-994a-93821f5871aa"   # canonical: 4 anchors
CHART_B = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"   # 56 anchors in production; 8 are the contaminated life_event_miss rows' anchors
INTEGRITY_SENTINEL = "SELECT true AS integrity_passed -- stand-in; another migration's column"


def _code(path: Path) -> str:
    return "\n".join(l for l in path.read_text().splitlines() if not l.lstrip().startswith("--"))


def _flat(path: Path) -> str:
    return re.sub(r"\s+", " ", re.sub(r"^--", " ", path.read_text(), flags=re.M))


def _md5(t: str) -> str:
    return hashlib.md5(t.encode()).hexdigest()


def _old_text() -> str:
    for m in re.finditer(r"\$check\$(.*?)\$check\$", _M681.read_text(), re.S):
        if _md5(m.group(1)) == OLD_MD5:
            return m.group(1)
    raise AssertionError("ph_pramana check not found in migration 681")


def _new_text(sql: str | None = None) -> str:
    return re.search(r"\$ck\$(.*)\$ck\$", sql or _REAL, re.S).group(1)


def _remake(new_text: str, base: str | None = None) -> str:
    """The migration with another target text (md5/length constants re-derived so it still applies): used for text mutants."""
    s = base or _REAL
    cur = _new_text(s)
    return s.replace(cur, new_text).replace(_md5(cur), _md5(new_text)).replace("IS DISTINCT FROM %d THEN" % len(cur), "IS DISTINCT FROM %d THEN" % len(new_text))


# -- STATIC ---------------------------------------------------------------------------

def test_old_text_is_681s_ph_pramana_check_and_the_live_production_text():
    assert _md5(_old_text()) == OLD_MD5 and len(_old_text()) == OLD_LEN


def test_new_text_named_md5_length_no_bind_placeholder_and_the_scope_structure():
    new = _new_text()
    assert _md5(new) == NEW_MD5 and len(new) == NEW_LEN
    assert "$1" not in new and "%s" not in new, "the orchestrator executes the text with no parameters"
    assert new.count("b.asset_id = 'ph_pramana' AND b.state = 'building' AND r.state = 'running'") == 2
    assert new.count("IN (SELECT r.chart_id FROM build_runs r JOIN build_run_assets b") == 2
    assert new.count("AND txid_current_if_assigned() IS NOT NULL") == 4, "the scope applies only to a session that has written"
    assert "xmin" not in new and "chart_id IS NOT NULL" not in new.replace("a.chart_id IS NOT NULL", "")
    assert hashlib.sha256(new.encode()).hexdigest() == NEW_SHA256
    assert "information_schema.columns" in new and "count(DISTINCT anchor_id)" in new and "FULL OUTER JOIN phala_pramana p" in new
    assert "WHERE NOT EXISTS (SELECT 1 FROM build_runs r2 JOIN build_run_assets b2" in new, "the outside-a-build fallback"


def test_migration_shape_guards_and_header():
    code = _code(_M1288)
    assert code.strip().startswith("SET LOCAL lock_timeout = '5s';")
    assert not re.search(r"^\s*(BEGIN|COMMIT|ROLLBACK)\s*;", code, re.M)
    outside = re.sub(r"\$ck\$.*?\$ck\$", "", code, flags=re.S)
    assert not re.search(r"\b(INSERT INTO|DELETE FROM|TRUNCATE|GRANT|REVOKE|ALTER\s)|(?<!COMMIT )DROP\s|CREATE\s+(OR\s+REPLACE\s+)?(VIEW|FUNCTION|TABLE|INDEX|TRIGGER|SCHEMA)", outside.replace("CREATE TEMP TABLE _m1288_before ON COMMIT DROP AS", ""))
    assert len(re.findall(r"\bUPDATE asset_registry\b", code)) == 1
    assert re.findall(r"\bSET\s+([a-z_]+)\s*=", code.split("$ck$")[0], re.I) == ["integrity_check_sql"]
    assert "WHERE asset_id = 'ph_pramana'" in code and f"AND md5(integrity_check_sql) = '{OLD_MD5}';" in code
    assert code.count(OLD_MD5) == 2 and code.count(NEW_MD5) == 2
    for needle in ("$runs$", "$pre$", "$post$", "r.state IN ('planned', 'running', 'paused') AND b.state IN ('queued', 'building')", "active build run(s)",
                   "is not the text this migration was written against", "did not take", "another column of the ph_pramana registry row changed",
                   "is not the chart-scoped text"):
        assert needle in code, needle
    sql = _flat(_M1288)
    for needle in ("HOW THE ORCHESTRATOR BINDS A CHART: IT DOES NOT", "cur.execute(integrity_sql)", "FROZEN", "asset_runner.py:1200", "THE PROBLEM", "REVIEW_3072.md MED-1",
                   "read-only session", "txid_current_if_assigned() IS NOT NULL", "LOST DETECTION", "ZERO pramana rows", "PRE-WRITE state", "NEVER RUN TWO ph_pramana BUILDS CONCURRENTLY", "LIST FOREIGN build_runs", "RE-COUPLE THE CHARTS", "sha256", "READBACKS", "after the #3072 delete", "SERVING / FRESHNESS EFFECT AT APPLY", "asset_freshness holds 0 rows for ph_pramana",
                   "ACTIVE RUNS (ENFORCED)", "Zombie rows", "KNOWN LIMITS", "NOT DONE HERE", "txid_current_if_assigned() IS NOT NULL", "LOST DETECTION", "ZERO pramana rows",
                   "PRE-WRITE state", "NEVER RUN TWO ph_pramana BUILDS CONCURRENTLY", "LIST FOREIGN build_runs", "RE-COUPLE THE CHARTS", "sha256", "xmin-based", "VERIFICATION BY PRODUCTION STRUCTURE", "ROLLBACK", OLD_MD5, NEW_MD5):
        assert needle in sql, f"header no longer states: {needle}"
    assert _M1288.name.startswith("1288_") and len(list(_MIG.glob("1288_*.sql"))) == 1


# -- LIVE -----------------------------------------------------------------------------

def _bin_dirs() -> list[Path]:
    cands: list[Path] = []
    for env in ("PG_BINS", "PG_BIN"):
        for p in os.environ.get(env, "").split(os.pathsep):
            if p:
                cands.append(Path(p))
    which = shutil.which("initdb")
    if which:
        cands.append(Path(which).parent)
    cands += [Path(p) for p in sorted(glob.glob("/opt/homebrew/opt/postgresql@*/bin"), reverse=True)]
    cands += [Path(p) for p in sorted(glob.glob("/usr/lib/postgresql/*/bin"), reverse=True)]
    seen, out = set(), []
    for c in cands:
        if (c / "initdb").exists() and (c / "pg_ctl").exists() and str(c.resolve()) not in seen:
            seen.add(str(c.resolve()))
            out.append(c)
    return out


def _versions() -> list[Path | None]:
    dirs = _bin_dirs()
    if os.environ.get("PG_BINS"):
        return dirs or [None]
    return dirs[:1] or [None]


@pytest.fixture(scope="module", params=_versions(), ids=lambda p: "nopg" if p is None else p.parent.name)
def pg_cluster(request):
    psycopg = pytest.importorskip("psycopg")
    binp = request.param
    if binp is None:
        if os.environ.get("REQUIRE_PG_BINARIES") == "1":
            pytest.fail("no PostgreSQL server binaries and REQUIRE_PG_BINARIES=1")
        pytest.skip("no PostgreSQL server binaries (initdb/pg_ctl) found; set PG_BIN")
    root = Path(tempfile.mkdtemp(prefix="m1288pg"))
    data = root / "data"
    sockdir = Path(tempfile.mkdtemp(prefix="m88", dir="/tmp"))  # unix socket paths are length-limited
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    subprocess.run([str(binp / "initdb"), "-D", str(data), "-U", "postgres", "-A", "trust", "-E", "UTF8", "--no-sync"],
                   check=True, capture_output=True)
    opts = f"-p {port} -c listen_addresses='' -c unix_socket_directories={sockdir} -c fsync=off"
    subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-o", opts, "-w", "-l", str(root / "log"), "start"],
                   check=True, capture_output=True)
    try:
        with psycopg.connect(host=str(sockdir), port=port, user="postgres", dbname="postgres", autocommit=True) as c:
            c.execute((_HERE / "fixtures" / "w1_roles.sql").read_text())  # production roles, attributes and memberships (W1 audit, verbatim)
        yield {"port": port, "sock": str(sockdir), "psycopg": psycopg, "major": binp.parent.name}
    finally:
        subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-m", "immediate", "stop"], capture_output=True)
        shutil.rmtree(root, ignore_errors=True)
        shutil.rmtree(sockdir, ignore_errors=True)


_db_counter = 0


@pytest.fixture()
def db(pg_cluster):
    global _db_counter
    _db_counter += 1
    name = f"t{_db_counter}"
    psycopg, port, sock = pg_cluster["psycopg"], pg_cluster["port"], pg_cluster["sock"]
    with psycopg.connect(host=sock, port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"CREATE DATABASE {name}")

    def connect(user="postgres", **kw):
        return psycopg.connect(host=sock, port=port, user=user, dbname=name, **kw)

    yield connect
    with psycopg.connect(host=sock, port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)")



_db_counter = 0


@pytest.fixture()
def db(pg_cluster):
    global _db_counter
    _db_counter += 1
    name = f"t{_db_counter}"
    psycopg, port, sock = pg_cluster["psycopg"], pg_cluster["port"], pg_cluster["sock"]
    with psycopg.connect(host=sock, port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"CREATE DATABASE {name}")

    def connect(user="postgres", **kw):
        return psycopg.connect(host=sock, port=port, user=user, dbname=name, **kw)

    yield connect
    with psycopg.connect(host=sock, port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)")




def _apply(connect, sql: str, notices=None, user: str = "amjis_app"):
    conn = connect(user=user)
    try:
        if notices is not None:
            conn.add_notice_handler(lambda d: notices.append(d.message_primary or ""))
        conn.execute(sql)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _exec(connect, sql, params=None, user="postgres"):
    with connect(user=user) as c:
        c.execute(sql, params)


def _q(connect, sql, params=None, user="postgres"):
    with connect(user=user) as c:
        return c.execute(sql, params).fetchall()


_TRIGGER_FN = """
CREATE OR REPLACE FUNCTION public.nirmana_invalidate_registry_receipts()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
  UPDATE asset_freshness
     SET freshness_state = 'stale',
         reasons = CASE
           WHEN reasons ? 'registry_changed' THEN reasons
           ELSE reasons || '["registry_changed"]'::jsonb
         END,
         observed_at = now()
   WHERE asset_id = NEW.asset_id;
  RETURN NEW;
END;
$function$
"""
_TRIGGER_DEF = ("CREATE TRIGGER nirmana_registry_receipt_invalidation AFTER UPDATE OF depends_on, "
                "natural_key_partition, health_probe, integrity_check_sql, target_floor, asset_kind, asset_type, "
                "scope, has_writer, is_active, target_table ON public.asset_registry FOR EACH ROW WHEN "
                "((old.* IS DISTINCT FROM new.*)) EXECUTE FUNCTION nirmana_invalidate_registry_receipts()")
_DDL = """
CREATE TABLE asset_registry (
    asset_id text PRIMARY KEY, layer text NOT NULL, sort_order integer NOT NULL, english_name text NOT NULL,
    target_table text, target_floor integer, depends_on text[] DEFAULT ARRAY[]::text[],
    scope text NOT NULL DEFAULT 'per_chart', is_active boolean DEFAULT true, asset_type text NOT NULL DEFAULT 'data',
    health_probe jsonb, integrity_check_sql text, asset_kind text NOT NULL DEFAULT 'data', has_writer boolean NOT NULL DEFAULT false,
    natural_key_partition text, volume_explanation text
);
CREATE TABLE asset_freshness (
    asset_id text NOT NULL REFERENCES asset_registry(asset_id) ON DELETE CASCADE, chart_id uuid, scope_key text NOT NULL,
    partition_key text NOT NULL, freshness_state text NOT NULL, reasons jsonb NOT NULL DEFAULT '[]'::jsonb,
    receipt_version text NOT NULL, observed_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY (asset_id, scope_key, partition_key));
CREATE TABLE build_runs (id uuid PRIMARY KEY DEFAULT gen_random_uuid(), chart_id uuid NOT NULL, state text NOT NULL
    CHECK (state IN ('planned','running','paused','completed','stopped','failed')));
CREATE TABLE build_run_assets (run_id uuid NOT NULL REFERENCES build_runs(id), asset_id text NOT NULL, position int NOT NULL DEFAULT 0,
    state text NOT NULL CHECK (state IN ('queued','building','complete','skipped','error','aborted')), PRIMARY KEY (run_id, asset_id));
CREATE TABLE asset_throughput (chart_id uuid, asset_id text, last_built_at timestamptz, rows_written int);
CREATE TABLE phala_anchors (anchor_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), chart_id uuid NOT NULL, label text);
CREATE TABLE phala_pramana (
    pramana_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), chart_id uuid NOT NULL, anchor_id uuid NOT NULL, evidence_type text NOT NULL,
    evidence_strength_label text NOT NULL DEFAULT 'indirect', falsifier_text text NOT NULL DEFAULT 'f',
    observable_criteria_jsonb jsonb NOT NULL DEFAULT '{}'::jsonb, window_status text NOT NULL DEFAULT 'open', lel_entry_id bigint,
    lel_entry_jsonb jsonb, linked_sodhana_id uuid, derivation_ledger_jsonb jsonb NOT NULL DEFAULT '{}'::jsonb,
    source_citation text NOT NULL DEFAULT 's', computed_at timestamptz NOT NULL DEFAULT now());
CREATE UNIQUE INDEX phala_pramana_natural_key ON phala_pramana (anchor_id, evidence_type, COALESCE(lel_entry_id, ('-1'::integer)::bigint));
"""
ASSETS = ["ph_pramana", "ph_nimitta", "mi_kula", "ga_vargas"]
N_A, N_B, N_B_MISS = 4, 12, 8   # anchors of chart A; of chart B (8 of them are the life_event_miss ones)
GENERIC_ANCHORS = {}


def _make_fixture(connect, *, text="__OLD__", pramana_rows=True):
    txt = _old_text() if text == "__OLD__" else text
    with connect() as c:
        c.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public")
        c.execute(_DDL)
        for i, a in enumerate(ASSETS):
            c.execute("INSERT INTO asset_registry (asset_id, layer, sort_order, english_name, integrity_check_sql, natural_key_partition) VALUES (%s, 'ph', %s, %s, %s, 'p')",
                      (a, i, a.upper(), txt if a == "ph_pramana" else INTEGRITY_SENTINEL))
        c.execute(_TRIGGER_FN)
        c.execute(_TRIGGER_DEF)
        c.execute("INSERT INTO asset_freshness (asset_id, chart_id, scope_key, partition_key, freshness_state, receipt_version) VALUES ('ph_nimitta', %s, 'k', 'p', 'fresh', 'v1')", (CHART_A,))
        c.execute("INSERT INTO asset_throughput VALUES (%s, 'ph_pramana', now(), 0), (%s, 'ph_pramana', now(), 0)", (CHART_A, CHART_B))
        for chart, n in ((CHART_A, N_A), (CHART_B, N_B)):
            for k in range(n):
                c.execute("INSERT INTO phala_anchors (chart_id, label) VALUES (%s, %s)", (chart, f"a{k}"))
        if pramana_rows:
            c.execute("INSERT INTO phala_pramana (chart_id, anchor_id, evidence_type) SELECT a.chart_id, a.anchor_id, "
                      "CASE WHEN a.chart_id = %s AND a.label IN ('a0','a1','a2','a3','a4','a5','a6','a7') THEN 'life_event_miss' ELSE 'astro_only' END FROM phala_anchors a", (CHART_B,))
        c.execute("GRANT SELECT ON asset_registry, build_runs, build_run_assets, phala_anchors, phala_pramana, asset_freshness, asset_throughput TO data_plane_builder, suvarna_reader")
        # the production owners, applied like W1: the schema ACL verbatim (amjis_app: USAGE only), every table owned by amjis_app
        c.execute((_HERE / "fixtures" / "w1_schema_acl.sql").read_text())
        for (t,) in c.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'").fetchall():
            c.execute(f'ALTER TABLE public."{t}" OWNER TO amjis_app')
        c.execute("ALTER FUNCTION public.nirmana_invalidate_registry_receipts() OWNER TO amjis_app")
        c.commit()


def _row(connect, aid="ph_pramana"):
    return _q(connect, "SELECT integrity_check_sql, md5(integrity_check_sql), length(integrity_check_sql), to_jsonb(r) - 'integrity_check_sql' FROM asset_registry r WHERE asset_id = %s", (aid,))[0]


def _freshness(connect):
    return _q(connect, "SELECT asset_id, chart_id::text, freshness_state, reasons::text, observed_at::text FROM asset_freshness ORDER BY 1, 2")


def _start_run(connect, chart, run_state="running", asset_state="building", asset="ph_pramana"):
    rid = _q(connect, "INSERT INTO build_runs (chart_id, state) VALUES (%s, %s) RETURNING id", (chart, run_state))[0][0]
    with connect() as c:
        c.execute("INSERT INTO build_run_assets (run_id, asset_id, state) VALUES (%s, %s, %s)", (rid, asset, asset_state))
        c.commit()
    return rid


def _check(connect, sql, user="amjis_app", wrote=True):
    """Executed the way asset_runner._probe_asset does: cur.execute(sql) with NO parameters; first column of the one row.
    wrote=True: the session has a txid, like the orchestrator's probe (writer + heartbeat wrote in the same transaction).
    wrote=False: a read-only session (freeze-time detector, census, operator SELECT): no txid."""
    with connect(user=user) as c:
        cur = c.cursor()
        if wrote:
            cur.execute("SELECT txid_current()")
        else:
            c.read_only = True
        cur.execute(sql)
        return cur.fetchone()[0]


def _delete_contaminated(connect):
    _exec(connect, "DELETE FROM phala_pramana WHERE chart_id = %s AND evidence_type = 'life_event_miss'", (CHART_B,))


def _rebuild_b(connect):
    _exec(connect, "INSERT INTO phala_pramana (chart_id, anchor_id, evidence_type) SELECT a.chart_id, a.anchor_id, 'astro_only' FROM phala_anchors a "
                   "WHERE a.chart_id = %s AND NOT EXISTS (SELECT 1 FROM phala_pramana p WHERE p.anchor_id = a.anchor_id)", (CHART_B,))


def test_fixture_mirrors_production_roles_and_the_runner_cannot_create_in_public(db):
    _make_fixture(db)
    r = _q(db, "SELECT has_schema_privilege('amjis_app','public','CREATE'), has_schema_privilege('amjis_app','public','USAGE'), "
               "(SELECT relowner::regrole::text FROM pg_class WHERE oid='asset_registry'::regclass), (SELECT nspowner::regrole::text FROM pg_namespace WHERE nspname='public')")[0]
    assert r == (False, True, "amjis_app", "data_plane_schema_owner")
    assert _row(db)[1] == OLD_MD5


# -- apply -----------------------------------------------------------------------------

def test_apply_stores_the_new_text_changes_no_other_column_and_stales_nothing(db):
    _make_fixture(db)
    others = {a: _row(db, a) for a in ASSETS if a != "ph_pramana"}
    rest_before, fresh_before = _row(db)[3], _freshness(db)
    _apply(db, _REAL)
    txt, md5, ln, rest = _row(db)
    assert (md5, ln, txt) == (NEW_MD5, NEW_LEN, _new_text()) and rest == rest_before
    assert {a: _row(db, a) for a in ASSETS if a != "ph_pramana"} == others
    assert _freshness(db) == fresh_before, "ph_pramana has no freshness row, so the trigger must stale nothing"


def test_the_trigger_fires_on_this_column_so_no_stale_means_no_rows(db):
    _make_fixture(db)
    _exec(db, "UPDATE asset_registry SET integrity_check_sql = 'SELECT 1' WHERE asset_id = 'ph_nimitta'")
    assert [(a, s) for a, _, s, _, _ in _freshness(db)] == [("ph_nimitta", "stale")]


@pytest.mark.parametrize("bad", ["SELECT false", "", None])
def test_md5_guard_refuses_an_unexpected_text_including_null_and_changes_nothing(db, bad):
    _make_fixture(db, text=bad)
    before = _row(db)
    with pytest.raises(Exception) as ei:
        _apply(db, _REAL)
    assert "is not the text this migration was written against" in str(ei.value) and _row(db) == before


def test_refuses_a_missing_row(db):
    _make_fixture(db)
    _exec(db, "DELETE FROM asset_registry WHERE asset_id = 'ph_pramana'")
    with pytest.raises(Exception) as ei:
        _apply(db, _REAL)
    assert "expected exactly one ph_pramana registry row" in str(ei.value)


def test_idempotent_second_run_rewrites_nothing_and_does_not_fire_the_trigger(db):
    _make_fixture(db)
    _apply(db, _REAL)
    _exec(db, "INSERT INTO asset_freshness (asset_id, chart_id, scope_key, partition_key, freshness_state, receipt_version) VALUES ('ph_pramana', NULL, 'k', 'p', 'fresh', 'v1')")
    snap, fresh = _q(db, "SELECT asset_id, xmin::text FROM asset_registry ORDER BY 1"), _freshness(db)
    notices: list[str] = []
    _apply(db, _REAL, notices)
    assert any("already carries the chart-scoped text" in n for n in notices)
    assert _q(db, "SELECT asset_id, xmin::text FROM asset_registry ORDER BY 1") == snap and _freshness(db) == fresh


@pytest.mark.parametrize("run_state", ["planned", "running", "paused"])
@pytest.mark.parametrize("asset_state", ["queued", "building"])
def test_active_run_guard_refuses_and_changes_nothing(db, run_state, asset_state):
    _make_fixture(db)
    _start_run(db, CHART_A, run_state, asset_state)
    before = _row(db)
    with pytest.raises(Exception) as ei:
        _apply(db, _REAL)
    assert "active build run" in str(ei.value) and _row(db) == before


def test_zombie_rows_and_unrelated_runs_do_not_block(db):
    """production today: stopped+queued 1, failed+queued 18 zombie ph_pramana rows; they must not block."""
    _make_fixture(db)
    for run_state, asset_state in (("stopped", "queued"), ("failed", "queued"), ("failed", "building"), ("completed", "queued"), ("completed", "complete"),
                                   ("failed", "error"), ("stopped", "aborted")):
        _start_run(db, CHART_A, run_state, asset_state)
    _start_run(db, CHART_A, "running", "building", asset="ph_nimitta")          # another asset's active run
    _start_run(db, CHART_B, "running", "complete")                               # active run, ph_pramana already finished
    _apply(db, _REAL)
    assert _row(db)[1] == NEW_MD5


def test_lock_timeout_fails_fast_when_the_registry_is_locked(db):
    _make_fixture(db)
    blocker = db()
    blocker.execute("LOCK TABLE asset_registry IN ACCESS EXCLUSIVE MODE")
    try:
        t0 = time.monotonic()
        victim = db(user="amjis_app", options="-c statement_timeout=20000")
        with pytest.raises(Exception) as ei:
            victim.execute(_REAL)
        elapsed = time.monotonic() - t0
        victim.rollback()
        victim.close()
    finally:
        blocker.rollback()
        blocker.close()
    assert "lock timeout" in str(ei.value).lower() and elapsed < 15


# -- the check, evaluated the way the orchestrator evaluates it --------------------------------

def test_executed_unbound_a_dollar_one_text_would_fail_which_is_why_the_scope_comes_from_state(db):
    _make_fixture(db)
    with pytest.raises(Exception):
        _check(db, "SELECT NOT EXISTS (SELECT 1 FROM phala_pramana WHERE chart_id = $1)")


def test_TODAYS_STATE_both_charts_consistent_old_and_new_are_true_outside_and_inside_a_build(db):
    _make_fixture(db)
    new = _new_text()
    assert _check(db, _old_text()) is True and _check(db, new) is True
    for chart in (CHART_A, CHART_B):
        _start_run(db, chart)
        assert _check(db, new) is True
    _make_fixture(db)
    _apply(db, _REAL)
    assert _check(db, _row(db)[0]) is True, "the text as stored"


def test_AFTER_THE_3072_DELETE_old_goes_false_for_everyone_new_is_true_for_the_other_chart_and_false_for_the_incomplete_one(db):
    _make_fixture(db)
    _delete_contaminated(db)
    old, new = _old_text(), _new_text()
    assert _check(db, old) is False, "the OLD global check fails after the delete (the problem)"
    assert _check(db, new) is False, "outside a build the NEW check is still the global-over-built-charts one: it reports the real incompleteness"
    # a ph_pramana build on the OTHER chart (the canonical one): old FALSE would error it, new passes
    ra = _start_run(db, CHART_A)
    assert _check(db, old) is False and _check(db, new) is True
    _exec(db, "UPDATE build_runs SET state = 'completed' WHERE id = %s", (ra,))
    # a build of the incomplete chart itself fails until its pramana is rebuilt
    rb = _start_run(db, CHART_B)
    assert _check(db, new) is False
    _rebuild_b(db)
    assert _check(db, new) is True
    _exec(db, "UPDATE build_runs SET state = 'completed' WHERE id = %s", (rb,))


def test_AFTER_A_SYNTHETIC_REBUILD_both_charts_true_everywhere(db):
    _make_fixture(db)
    _delete_contaminated(db)
    _rebuild_b(db)
    new = _new_text()
    assert _check(db, _old_text()) is True and _check(db, new) is True
    for chart in (CHART_A, CHART_B):
        _start_run(db, chart)
        assert _check(db, new) is True


def test_orchestrator_shaped_transaction_delete_then_insert_then_check_in_one_transaction(db):
    """The writer's own transaction: committed 'building' run row, then DELETE + INSERT of the chart's rows, then the check on the same connection."""
    _make_fixture(db)
    _delete_contaminated(db)                      # chart B incomplete (the post-#3072 state)
    _start_run(db, CHART_A)
    conn = db(user="amjis_app")
    cur = conn.cursor()
    cur.execute("DELETE FROM phala_pramana WHERE chart_id = %s", (CHART_A,))
    cur.execute("INSERT INTO phala_pramana (chart_id, anchor_id, evidence_type) SELECT chart_id, anchor_id, 'astro_only' FROM phala_anchors WHERE chart_id = %s", (CHART_A,))
    cur.execute(_new_text())
    new_ok = cur.fetchone()[0]
    cur.execute(_old_text())
    old_ok = cur.fetchone()[0]
    conn.rollback()
    conn.close()
    assert new_ok is True and old_ok is False


def test_the_builder_role_can_run_the_new_check(db):
    _make_fixture(db)
    _start_run(db, CHART_A)
    assert _check(db, _new_text(), user="data_plane_builder") is True


def test_corruption_in_the_chart_being_built_fails_it_and_in_the_other_chart_does_not(db):
    new = _new_text()
    corruptions = {
        "anchor_without_pramana": "DELETE FROM phala_pramana WHERE anchor_id = (SELECT anchor_id FROM phala_anchors WHERE chart_id = %s LIMIT 1)",
        "pramana_without_anchor": "INSERT INTO phala_pramana (chart_id, anchor_id, evidence_type) VALUES (%s, gen_random_uuid(), 'astro_only')",
        "duplicate_pramana_per_anchor": "INSERT INTO phala_pramana (chart_id, anchor_id, evidence_type) SELECT chart_id, anchor_id, 'other_type' FROM phala_anchors WHERE chart_id = %s LIMIT 1",
    }
    for name, sql in corruptions.items():
        for bad_chart, other in ((CHART_A, CHART_B), (CHART_B, CHART_A)):
            _make_fixture(db)
            _exec(db, sql, (bad_chart,))
            _start_run(db, other)
            assert _check(db, new) is True, f"{name}: corruption of {bad_chart} must not fail a build of {other}"
            _make_fixture(db)
            _exec(db, sql, (bad_chart,))
            _start_run(db, bad_chart)
            assert _check(db, new) is False, f"{name}: corruption of the chart being built must fail it"
            _make_fixture(db)
            _exec(db, sql, (bad_chart,))
            assert _check(db, new) is False, f"{name}: outside a build the check still catches it (not vacuous)"


def test_a_numeric_column_fails_the_schema_clause_everywhere(db):
    _make_fixture(db)
    _exec(db, "ALTER TABLE phala_pramana ADD COLUMN score numeric")
    assert _check(db, _new_text()) is False
    _start_run(db, CHART_A)
    assert _check(db, _new_text()) is False


def test_a_chart_being_built_with_anchors_but_no_pramana_rows_is_judged_and_fails_and_outside_a_build_an_unbuilt_chart_is_not_corruption(db):
    _make_fixture(db, pramana_rows=False)
    new = _new_text()
    assert _check(db, new) is True, "outside a build: no chart has pramana rows, nothing is built, nothing is wrong"
    _start_run(db, CHART_A)
    assert _check(db, new) is False, "the chart being built must have a pramana row for each of its anchors"
    _exec(db, "INSERT INTO phala_pramana (chart_id, anchor_id, evidence_type) SELECT chart_id, anchor_id, 'astro_only' FROM phala_anchors WHERE chart_id = %s", (CHART_A,))
    assert _check(db, new) is True, "chart B has no pramana rows (unbuilt) and is not in scope"


def test_a_chart_being_built_with_no_anchors_at_all_passes_even_if_another_chart_is_incomplete(db):
    _make_fixture(db)
    _delete_contaminated(db)
    _exec(db, "DELETE FROM phala_pramana WHERE chart_id = %s", (CHART_A,))
    _exec(db, "DELETE FROM phala_anchors WHERE chart_id = %s", (CHART_A,))
    _start_run(db, CHART_A)
    assert _check(db, _new_text()) is True


def test_only_a_running_run_with_a_building_ph_pramana_row_scopes_the_check(db):
    _make_fixture(db)
    _delete_contaminated(db)                       # chart B incomplete: any run scoping B would make it false
    new = _new_text()
    for run_state, asset_state in (("planned", "queued"), ("paused", "building"), ("completed", "building"), ("failed", "building"), ("stopped", "queued"), ("running", "queued"),
                                   ("running", "complete")):
        _start_run(db, CHART_B, run_state, asset_state)
    _start_run(db, CHART_B, "running", "building", asset="ph_nimitta")
    assert _check(db, new) is False, "none of these scopes chart B, so the check is the outside-a-build global one: it reports B"
    _start_run(db, CHART_A)                        # a real running/building ph_pramana run for A
    assert _check(db, new) is True, "scoped to A only: the zombie/planned/other-asset rows for B do not add B"


def test_two_concurrent_ph_pramana_builds_put_both_charts_in_scope(db):
    _make_fixture(db)
    _delete_contaminated(db)
    _start_run(db, CHART_A)
    assert _check(db, _new_text()) is True
    _start_run(db, CHART_B)
    assert _check(db, _new_text()) is False


def test_REAL_probe_asset_in_a_writer_shaped_transaction_has_a_txid_and_the_scope_applies(db):
    """MED-1/MED-2 hardening: the orchestrator's probe runs after the writer and its heartbeat wrote, in the same transaction (savepoint per sub-step),
    so txid_current_if_assigned() is not NULL and the chart scope applies. The REAL _probe_asset is called (dict rows, like the orchestrator)."""
    from psycopg.rows import dict_row
    from pipeline.orchestrator.asset_runner import _probe_asset
    _make_fixture(db)
    _delete_contaminated(db)                      # chart B incomplete: the post-#3072 state
    _apply(db, _REAL)
    reg = {"integrity_check_sql": _row(db)[0]}
    assert reg["integrity_check_sql"] == _new_text()
    _start_run(db, CHART_A)                       # committed 'running' + 'building' rows, as run_asset leaves them
    conn = db(user="amjis_app", row_factory=dict_row)
    cur = conn.cursor()
    cur.execute("SELECT txid_current_if_assigned() IS NOT NULL AS has_txid")
    assert cur.fetchone()["has_txid"] is False, "precondition: nothing written yet"
    cur.execute("SAVEPOINT writer_exec")
    cur.execute("DELETE FROM phala_pramana WHERE chart_id = %s", (CHART_A,))
    cur.execute("INSERT INTO phala_pramana (chart_id, anchor_id, evidence_type) SELECT chart_id, anchor_id, 'astro_only' FROM phala_anchors WHERE chart_id = %s", (CHART_A,))
    cur.execute("RELEASE SAVEPOINT writer_exec")
    cur.execute("UPDATE asset_throughput SET last_built_at = NOW(), rows_written = 4 WHERE chart_id IS NOT DISTINCT FROM %s AND asset_id = 'ph_pramana'", (CHART_A,))
    cur.execute("SELECT txid_current_if_assigned() IS NOT NULL AS has_txid")
    assert cur.fetchone()["has_txid"] is True
    ok, message = _probe_asset(conn, cur, "ph_pramana", reg, False)
    old_ok, _ = _probe_asset(conn, cur, "ph_pramana", {"integrity_check_sql": _old_text()}, False)
    conn.rollback()
    conn.close()
    assert ok is True, message
    assert old_ok is False, "the old global check fails the same transaction (the problem)"


def test_REAL_probe_asset_rebuild_of_the_incomplete_chart_itself_reads_true_after_the_writer(db):
    """LOW-2: the FALSE for 1c826d5a in the table is the PRE-WRITE state; the probe runs after the writer regenerated the rows, so that build reads TRUE."""
    from psycopg.rows import dict_row
    from pipeline.orchestrator.asset_runner import _probe_asset
    _make_fixture(db)
    _delete_contaminated(db)
    _start_run(db, CHART_B)
    conn = db(user="amjis_app", row_factory=dict_row)
    cur = conn.cursor()
    cur.execute("DELETE FROM phala_pramana WHERE chart_id = %s", (CHART_B,))
    cur.execute("INSERT INTO phala_pramana (chart_id, anchor_id, evidence_type) SELECT chart_id, anchor_id, 'astro_only' FROM phala_anchors WHERE chart_id = %s", (CHART_B,))
    cur.execute("UPDATE asset_throughput SET rows_written = 12 WHERE chart_id = %s AND asset_id = 'ph_pramana'", (CHART_B,))
    ok, message = _probe_asset(conn, cur, "ph_pramana", {"integrity_check_sql": _new_text()}, False)
    conn.rollback()
    conn.close()
    assert ok is True, message


def test_READ_ONLY_sessions_are_never_narrowed_by_an_in_flight_or_stuck_run(db):
    """MED-2: a running+building row used to narrow the detector/census to one chart (TRUE where the old check was FALSE). With the txid condition a
    read-only session (no txid) takes the all-charts scope; the orchestrator session (txid) is still scoped."""
    _make_fixture(db)
    _exec(db, "DELETE FROM phala_pramana WHERE anchor_id = (SELECT anchor_id FROM phala_anchors WHERE chart_id = %s LIMIT 1)", (CHART_B,))   # chart B corrupt
    _start_run(db, CHART_A)
    new = _new_text()
    assert _check(db, _old_text(), wrote=False) is False
    assert _check(db, new, wrote=False) is False, "read-only: not narrowed to the chart in flight"
    assert _check(db, new, wrote=True) is True, "the orchestrator session of chart A is scoped to A"
    assert _check(db, new, user="suvarna_reader", wrote=False) is False, "the reader role / detector"


def test_MED_1_two_concurrent_builds_recouple_the_charts_documented_and_runbook_rule(db):
    """Chart X complete, chart Y's COMMITTED rows incomplete (1c826d5a after #3072), both builds running: X's probe reads FALSE (fails closed, transient)."""
    _make_fixture(db)
    _delete_contaminated(db)
    _start_run(db, CHART_A)
    _start_run(db, CHART_B)
    assert _check(db, _new_text(), wrote=True) is False
    sql = _flat(_M1288)
    assert "NEVER RUN TWO ph_pramana BUILDS CONCURRENTLY" in sql and "LIST FOREIGN build_runs BEFORE EVERY DISPATCH" in sql


def test_a_build_whose_session_wrote_nothing_takes_the_all_charts_scope_documented_limit(db):
    """A chart with no anchors, no asset_throughput row to heartbeat, writer deleted 0 rows: no txid, so the check behaves like the old one."""
    _make_fixture(db)
    _delete_contaminated(db)
    _exec(db, "DELETE FROM phala_pramana WHERE chart_id = %s", (CHART_A,))
    _exec(db, "DELETE FROM phala_anchors WHERE chart_id = %s", (CHART_A,))
    _exec(db, "DELETE FROM asset_throughput WHERE chart_id = %s", (CHART_A,))
    _start_run(db, CHART_A)
    assert _check(db, _new_text(), wrote=False) is False
    assert _check(db, _new_text(), wrote=True) is True


# -- MUTATION proof ---------------------------------------------------------------------------

_REAL_NEW = _new_text()


def _scenario(db, sql):
    v = []
    _make_fixture(db)
    rest_before = _row(db)[3]
    fresh = _freshness(db)
    try:
        _apply(db, sql)
    except Exception as exc:  # noqa: BLE001
        return [f"apply failed: {str(exc).splitlines()[0]}"]
    txt, md5, ln, rest = _row(db)
    if md5 != _md5(_new_text(sql)) or txt != _new_text(sql):
        v.append("target text not stored")
    if rest != rest_before:
        v.append("another column changed")
    if _freshness(db) != fresh:
        v.append("freshness moved")
    return v


def _semantic_scenario(db, sql):
    """The stored text must behave: the contract of the whole migration, evaluated on the text the file would store."""
    v = []
    t = _new_text(sql)
    _make_fixture(db)
    if _check(db, t) is not True:
        v.append("today: not true outside a build")
    _delete_contaminated(db)
    if _check(db, t) is not False:
        v.append("after delete, outside a build: must be false (not vacuous)")
    ra = _start_run(db, CHART_A)
    if _check(db, t) is not True:
        v.append("after delete, build of the other chart: must be true")
    _exec(db, "UPDATE build_runs SET state = 'completed' WHERE id = %s", (ra,))
    _start_run(db, CHART_B)
    if _check(db, t) is not False:
        v.append("after delete, build of the incomplete chart: must be false")
    _make_fixture(db)
    _exec(db, "DELETE FROM phala_pramana WHERE anchor_id = (SELECT anchor_id FROM phala_anchors WHERE chart_id = %s LIMIT 1)", (CHART_A,))
    _start_run(db, CHART_A)
    if _check(db, t) is not False:
        v.append("anchor without pramana in the chart being built: must be false")
    _make_fixture(db)
    _exec(db, "INSERT INTO phala_pramana (chart_id, anchor_id, evidence_type) VALUES (%s, gen_random_uuid(), 'astro_only')", (CHART_A,))
    _start_run(db, CHART_A)
    if _check(db, t) is not False:
        v.append("pramana without anchor in the chart being built: must be false")
    _make_fixture(db)
    _exec(db, "INSERT INTO phala_pramana (chart_id, anchor_id, evidence_type) SELECT chart_id, anchor_id, 'other_type' FROM phala_anchors WHERE chart_id = %s LIMIT 1", (CHART_A,))
    _start_run(db, CHART_A)
    if _check(db, t) is not False:
        v.append("duplicate pramana per anchor in the chart being built: must be false")
    _make_fixture(db)
    _exec(db, "ALTER TABLE phala_pramana ADD COLUMN score numeric")
    if _check(db, t) is not False:
        v.append("numeric column: must be false")
    _make_fixture(db)
    _delete_contaminated(db)
    for run_state, asset_state in (("planned", "queued"), ("completed", "building"), ("failed", "building"), ("running", "queued")):
        _start_run(db, CHART_B, run_state, asset_state)
    _start_run(db, CHART_A)
    if _check(db, t) is not True:
        v.append("zombie/planned rows of the incomplete chart must not scope it")
    _make_fixture(db, pramana_rows=False)
    _start_run(db, CHART_A)
    if _check(db, t) is not False:
        v.append("a chart being built with anchors and no pramana must be judged")
    _make_fixture(db)
    _exec(db, "DELETE FROM phala_pramana WHERE anchor_id = (SELECT anchor_id FROM phala_anchors WHERE chart_id = %s LIMIT 1)", (CHART_B,))
    _start_run(db, CHART_A)
    if _check(db, t, wrote=False) is not False:
        v.append("read-only session narrowed by an in-flight run: must stay all-charts (false)")
    if _check(db, t, wrote=True) is not True:
        v.append("orchestrator session (txid) must be scoped to the chart being built")
    return v


def _guard_scenario(db, sql):
    v = []
    _make_fixture(db, text="SELECT false")
    before = _row(db)
    try:
        _apply(db, sql)
        v.append("accepted an unexpected base text")
    except Exception as exc:  # noqa: BLE001
        if "is not the text this migration was written against" not in str(exc):
            v.append(f"refused, not by the pre-check: {str(exc).splitlines()[0]}")
    if _row(db) != before:
        v.append("overwrote an unexpected text")
    _make_fixture(db)
    _apply(db, _REAL)
    snap = _q(db, "SELECT xmin::text FROM asset_registry WHERE asset_id='ph_pramana'")
    try:
        _apply(db, sql)
    except Exception as exc:  # noqa: BLE001
        return v + [f"re-run failed: {str(exc).splitlines()[0]}"]
    if _q(db, "SELECT xmin::text FROM asset_registry WHERE asset_id='ph_pramana'") != snap:
        v.append("re-run rewrote the row")
    return v


def _runs_scenario(db, sql):
    v = []
    for run_state, asset_state in (("planned", "queued"), ("running", "building"), ("paused", "queued")):
        _make_fixture(db)
        _start_run(db, CHART_A, run_state, asset_state)
        try:
            _apply(db, sql)
            v.append(f"applied during an active run ({run_state}/{asset_state})")
        except Exception as exc:  # noqa: BLE001
            if "active build run" not in str(exc):
                v.append(f"refused for another reason: {str(exc).splitlines()[0]}")
    _make_fixture(db)
    for run_state, asset_state in (("stopped", "queued"), ("failed", "queued"), ("completed", "queued")):
        _start_run(db, CHART_A, run_state, asset_state)
    try:
        _apply(db, sql)
    except Exception as exc:  # noqa: BLE001
        v.append(f"a zombie row blocked the migration: {str(exc).splitlines()[0]}")
    return v


def _lock_scenario(db, sql):
    _make_fixture(db)
    blocker = db()
    blocker.execute("LOCK TABLE asset_registry IN ACCESS EXCLUSIVE MODE")
    try:
        victim = db(user="amjis_app", options="-c statement_timeout=8000")
        try:
            victim.execute(sql)
            return ["did not fail while the registry was locked"]
        except Exception as exc:  # noqa: BLE001
            return [] if "lock timeout" in str(exc).lower() else [f"failed for another reason: {str(exc).splitlines()[0]}"]
        finally:
            victim.rollback()
            victim.close()
    finally:
        blocker.rollback()
        blocker.close()


def _post_scenario(db, sql):
    edited = sql.replace("-- Exactly one pramana row per anchor, no orphan in either direction, for the chart(s) in scope.", "-- Exactly one pramana row per anchor, in both directions, in scope.", 1)
    assert edited != sql
    _make_fixture(db)
    try:
        _apply(db, edited)
        return ["a target text that does not hash to the named md5 was installed"]
    except Exception:  # noqa: BLE001
        return []


_EFF_RE = re.compile(r"b\.asset_id = 'ph_pramana' AND b\.state = 'building' AND r\.state = 'running'")
_N = _REAL_NEW
_MUTANTS = {
    # mutants of the migration file
    "update_guard_removed": (re.sub(r"\n  AND md5\(integrity_check_sql\) = '%s';" % OLD_MD5, ";", _REAL), "guard"),
    "pre_check_neutered": (_REAL.replace("ELSIF v_md5 IS DISTINCT FROM '%s' THEN" % OLD_MD5, "ELSIF false THEN"), "guard"),
    "active_runs_guard_neutered": (_REAL.replace("IF n_active > 0 THEN", "IF false THEN"), "runs"),
    "active_runs_guard_ignores_paused": (_REAL.replace("r.state IN ('planned', 'running', 'paused')", "r.state IN ('planned', 'running')"), "runs"),
    "active_runs_guard_blocks_on_zombies": (_REAL.replace("r.state IN ('planned', 'running', 'paused') AND b.state IN ('queued', 'building')", "b.state IN ('queued', 'building')"), "runs"),
    "post_md5_check_neutered": (_REAL.replace("IF v_md5 IS DISTINCT FROM '%s' OR v_len IS DISTINCT FROM %d THEN" % (NEW_MD5, NEW_LEN), "IF false THEN"), "post"),
    "lock_timeout_removed": (_REAL.replace("SET LOCK_TIMEOUT", "x").replace("SET LOCAL lock_timeout = '5s';", "", 1), "lock"),
    "lock_timeout_session_wide": (_REAL.replace("SET LOCAL lock_timeout = '5s';", "SET lock_timeout = '0';", 1), "lock"),
    "update_removed": (re.sub(r"UPDATE asset_registry\nSET integrity_check_sql = \$ck\$.*?\$ck\$\nWHERE asset_id = 'ph_pramana'\n  AND md5\(integrity_check_sql\) = '%s';\n" % OLD_MD5, "", _REAL, flags=re.S), "scenario"),
    "other_column_also_changed": (_REAL.replace("$ck$\nWHERE asset_id = 'ph_pramana'", "$ck$, volume_explanation = 'x'\nWHERE asset_id = 'ph_pramana'", 1), "scenario"),
    # mutants of the check text (the migration re-made around them so it still applies)
    "text_scope_ignored_global_again": (_remake(_N.replace("IN (SELECT r.chart_id", "IN (SELECT chart_id FROM phala_pramana UNION SELECT r.chart_id", 1).replace("IN (SELECT r.chart_id", "IN (SELECT chart_id FROM phala_pramana UNION SELECT r.chart_id", 1)), "semantic"),
    "text_run_state_not_checked": (_remake(_N.replace("AND r.state = 'running'", "", 2)), "semantic"),
    "text_building_state_not_checked": (_remake(_N.replace("AND b.state = 'building'", "", 2)), "semantic"),
    "text_no_fallback_outside_a_build": (_remake(_N.replace("WHERE NOT EXISTS (SELECT 1 FROM build_runs r2", "WHERE false AND NOT EXISTS (SELECT 1 FROM build_runs r2")), "semantic"),
    "text_fallback_always_added": (_remake(_N.replace("WHERE NOT EXISTS (SELECT 1 FROM build_runs r2", "WHERE true OR NOT EXISTS (SELECT 1 FROM build_runs r2")), "semantic"),
    "text_tiling_one_direction_only": (_remake(_N.replace("WHERE (a.anchor_id IS NULL OR p.anchor_id IS NULL)", "WHERE (p.anchor_id IS NULL)")), "semantic"),
    "text_tiling_other_direction_only": (_remake(_N.replace("WHERE (a.anchor_id IS NULL OR p.anchor_id IS NULL)", "WHERE (a.anchor_id IS NULL)")), "semantic"),
    "text_grain_clause_dropped": (_remake(_N.replace("HAVING count(*) <> count(DISTINCT anchor_id)", "HAVING false")), "semantic"),
    "text_schema_clause_dropped": (_remake(_N.replace("AND data_type IN ('numeric','double precision','real'))", "AND false)")), "semantic"),
    "text_txid_condition_removed_everywhere": (_remake(_N.replace(" AND txid_current_if_assigned() IS NOT NULL", "")), "semantic"),
    "text_txid_condition_removed_from_the_fallback_only": (_remake(_N.replace("AND r2.state = 'running' AND txid_current_if_assigned() IS NOT NULL", "AND r2.state = 'running'")), "semantic"),
    "text_txid_condition_inverted": (_remake(_N.replace("txid_current_if_assigned() IS NOT NULL", "txid_current_if_assigned() IS NULL")), "semantic"),
}


def test_mutants_are_real_mutations():
    for name, (sql, _) in _MUTANTS.items():
        assert sql != _REAL, f"mutant {name} did not change the file (the mutation pattern is stale)"


def test_the_real_file_produces_no_violations(db):
    assert _scenario(db, _REAL) == []
    assert _semantic_scenario(db, _REAL) == []
    assert _guard_scenario(db, _REAL) == []
    assert _runs_scenario(db, _REAL) == []
    assert _lock_scenario(db, _REAL) == []
    assert _post_scenario(db, _REAL) == []


@pytest.mark.parametrize("name", sorted(_MUTANTS))
def test_every_mutant_is_caught(db, name):
    sql, kind = _MUTANTS[name]
    v = {"scenario": _scenario, "semantic": _semantic_scenario, "guard": _guard_scenario, "runs": _runs_scenario, "lock": _lock_scenario, "post": _post_scenario}[kind](db, sql)
    assert v, f"mutant {name} was NOT caught"
