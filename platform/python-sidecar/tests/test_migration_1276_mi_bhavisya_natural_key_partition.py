"""
Migration 1276 (Suvarna): asset_registry.natural_key_partition of mi_bhavisya is rewritten from the delete-based justification of migration 991
to the accurate append-only one (SS N-104 / N-107; PR #3040). HELD, POST-WINDOW: own draft PR, routine path.

STATIC tier (DB-free): the stored OLD text (the literal of migration 991) must hash to the live production md5; the NEW text must hash to the md5 and
length the migration names, state the append-only facts and no longer rely on a delete; file shape, guards, header facts.
LIVE tier (needs PostgreSQL binaries; REQUIRE_PG_BINARIES=1 turns a skip into a failure): applies the REAL file AS amjis_app on a disposable cluster
that mirrors production's privileges (schema public owned by data_plane_schema_owner, amjis_app USAGE only, owns every table), with the REAL
trigger function body and definition of nirmana_registry_receipt_invalidation. Proves: the text is stored (md5, length, exact text) and no other column of
the row changed; the serving effect (0 freshness rows to stale; the trigger column list contains natural_key_partition); the partition-key strand guard;
md5 guard; idempotency; active-run guard; lock_timeout; a mutation section requires every mutant to be caught.
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

_REPO = Path(__file__).resolve().parents[3]
_MIG = _REPO / "platform" / "migrations"
_M1276 = _MIG / "1276_mi_bhavisya_natural_key_partition_append_only.sql"
_M991 = _MIG / "991_nirmana_l5_mi_bhavisya_natural_key_partition.sql"
_REAL = _M1276.read_text()
OLD_MD5, NEW_MD5, OLD_LEN, NEW_LEN = "07d729f8f0487ac3d3ddb114dd4cdc73", "a411af1488287dced6b8b121ec1eb28b", 2838, 3544
INTEGRITY_SENTINEL = "SELECT true AS integrity_passed -- stand-in; 1259 owns this column"


def _code(path: Path) -> str:
    return "\n".join(l for l in path.read_text().splitlines() if not l.lstrip().startswith("--"))


def _flat(path: Path) -> str:
    return re.sub(r"\s+", " ", re.sub(r"^--", " ", path.read_text(), flags=re.M))


def _old_text() -> str:
    """The single-quoted literal that migration 991 stored."""
    s = _M991.read_text()
    m = re.search(r"SET natural_key_partition = '((?:[^']|'')*)'", s, re.S)
    return m.group(1).replace("''", "'")


def _new_text(sql: str | None = None) -> str:
    return re.search(r"\$nkp\$(.*)\$nkp\$", sql or _REAL, re.S).group(1)


def _md5(t: str) -> str:
    return hashlib.md5(t.encode()).hexdigest()


# -- STATIC ---------------------------------------------------------------------------

def test_old_text_is_the_991_literal_and_the_live_production_text():
    assert _md5(_old_text()) == OLD_MD5 and len(_old_text()) == OLD_LEN


def test_new_text_has_the_named_md5_and_length_and_is_stored_in_the_file_as_the_only_update():
    new = _new_text()
    assert _md5(new) == NEW_MD5 and len(new) == NEW_LEN
    code = _code(_M1276)
    assert len(re.findall(r"\bUPDATE asset_registry\b", code)) == 1
    assert re.findall(r"\bSET\s+([a-z_]+)\s*=", code.split("$nkp$")[0], re.I) == ["natural_key_partition"]
    assert "WHERE asset_id = 'mi_bhavisya'" in code and f"AND md5(natural_key_partition) = '{OLD_MD5}';" in code


def test_new_text_states_the_append_only_facts_and_no_longer_relies_on_a_delete():
    new = _new_text()
    for needle in ("mimamsa_manifestation_sets (chart_id, prediction_id, channel_id) -- ", "APPEND-ONLY", "N-104", "N-107", "PR #3040",
                   "MI_BHAVISYA_APPEND_ONLY_v1_0.md", "never DELETEs or UPDATEs", "never TRUNCATEs", "no ON CONFLICT DO UPDATE", "ON CONFLICT DO NOTHING",
                   "CUMULATIVE", "TWO-PART NATURAL KEY", "prediction_id = 'pred_<anchor_id>'", "source_pramana_id = '<anchor_id>'", "migration 680",
                   "existing-key skip", "output_changed false", "195 rows, 0 duplicate", "frozen_at", "DELIBERATELY NOT COVERED", "mimamsa_predictions", "#1770"):
        assert needle in new, needle
    for gone in ("DELETE FROM", "idempotent DELETE", "exactly the current run's row set exists", "differs every rebuild"):
        assert gone not in new, gone
    assert "idempotent DELETE FROM mimamsa_manifestation_sets" in _old_text(), "the old text really was the delete-based one"


def test_migration_shape_guards_and_header():
    code = _code(_M1276)
    assert code.strip().startswith("SET LOCAL lock_timeout = '5s';")
    assert not re.search(r"^\s*(BEGIN|COMMIT|ROLLBACK)\s*;", code, re.M)
    outside = re.sub(r"\$nkp\$.*?\$nkp\$", "", code, flags=re.S)  # the stored text may MENTION these words
    assert not re.search(r"\b(INSERT INTO|DELETE FROM|TRUNCATE|GRANT|REVOKE|ALTER\s)|(?<!COMMIT )DROP\s", outside)
    assert "integrity_check_sql" not in code, "1259 owns that column"
    for needle in ("$runs$", "$pre$", "$post$", "r.state NOT IN ('completed', 'failed', 'stopped')", "active build run(s)",
                   "is not the text this migration was written against", "would strand them", "did not take",
                   "another column of the mi_bhavisya registry row changed", "is not the append-only text"):
        assert needle in code, needle
    sql = _flat(_M1276)
    for needle in ("HELD, POST-WINDOW", "AFTER PR #3040", "natural_key_partition IS in its column list", "asset_freshness has 0 rows for mi_bhavisya",
                   "THE TEXT IS A KEY", "partition_key", "THE MIGRATION ENFORCES THAT", "OTHER COLUMNS OF THE SAME ROW", "expected_volume_formula",
                   "integrity_check_sql belongs to migration 1259", "ACTIVE RUNS (ENFORCED", "IDEMPOTENT SHAPE", "VERIFICATION BY PRODUCTION STRUCTURE",
                   "ROLLBACK", "suvarna_reader", "Migration 991 is NOT edited", OLD_MD5, NEW_MD5):
        assert needle in sql, f"header no longer states: {needle}"
    assert _M1276.name.startswith("1276_") and len(list(_MIG.glob("1276_*.sql"))) == 1


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
    root = Path(tempfile.mkdtemp(prefix="m1276pg"))
    data = root / "data"
    sockdir = Path(tempfile.mkdtemp(prefix="m76", dir="/tmp"))  # unix socket paths are length-limited
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
            for r in ("amjis_app LOGIN", "data_plane_schema_owner NOLOGIN"):
                c.execute(f"CREATE ROLE {r}")
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
    natural_key_partition text, volume_explanation text, expected_volume_formula text
);
CREATE TABLE asset_freshness (
    asset_id text NOT NULL REFERENCES asset_registry(asset_id) ON DELETE CASCADE, chart_id uuid, scope_key text NOT NULL,
    partition_key text NOT NULL, freshness_state text NOT NULL, reasons jsonb NOT NULL DEFAULT '[]'::jsonb,
    receipt_version text NOT NULL, observed_at timestamptz NOT NULL DEFAULT now(), PRIMARY KEY (asset_id, scope_key, partition_key));
CREATE TABLE asset_provenance_receipts (asset_id text NOT NULL, chart_id uuid, scope_key text NOT NULL DEFAULT 'x', partition_key text NOT NULL, receipt_version text,
    PRIMARY KEY (asset_id, scope_key, partition_key));
CREATE TABLE build_runs (id bigserial PRIMARY KEY, state text NOT NULL);
CREATE TABLE build_run_assets (run_id bigint NOT NULL REFERENCES build_runs(id), asset_id text NOT NULL);
"""
ASSETS = ["mi_bhavisya", "mi_kula", "mi_jivanaghatana", "ph_nimitta", "ga_vargas"]
CHARTS = ["482012f1-710e-4a25-994a-93821f5871aa", "1c826d5a-41cb-4450-b4dc-59d440e5f75a"]


def _make_fixture(connect, *, nkp="__OLD__", fresh_for=(), receipts_for=()):
    nkp = _old_text() if nkp == "__OLD__" else nkp
    with connect() as c:
        c.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public")
        c.execute(_DDL)
        for i, a in enumerate(ASSETS):
            c.execute("INSERT INTO asset_registry (asset_id, layer, sort_order, english_name, integrity_check_sql, natural_key_partition, volume_explanation, expected_volume_formula) "
                      "VALUES (%s, 'mi', %s, %s, %s, %s, 'Accumulates as predictions are logged', 'COUNT(phala_anchors WHERE chart_id = $chart)')",
                      (a, i, a.upper(), INTEGRITY_SENTINEL, nkp if a in ("mi_bhavisya", "mi_kula") else "other-" + a))  # mi_kula is a twin carrying the SAME text: only the asset_id guard keeps it untouched
        c.execute(_TRIGGER_FN)
        c.execute(_TRIGGER_DEF)
        for a in ("mi_kula", "mi_jivanaghatana", "ph_nimitta"):
            c.execute("INSERT INTO asset_freshness (asset_id, chart_id, scope_key, partition_key, freshness_state, receipt_version) VALUES (%s, %s, 'k', 'p', 'fresh', 'v1')", (a, CHARTS[0]))
        for a in fresh_for:
            for ch in CHARTS:
                c.execute("INSERT INTO asset_freshness (asset_id, chart_id, scope_key, partition_key, freshness_state, receipt_version) VALUES (%s, %s, %s, 'p', 'fresh', 'v1')", (a, ch, "k" + ch))
        for a in receipts_for:
            c.execute("INSERT INTO asset_provenance_receipts (asset_id, chart_id, partition_key) VALUES (%s, %s, 'p')", (a, CHARTS[0]))
        c.execute("ALTER SCHEMA public OWNER TO data_plane_schema_owner")
        c.execute("REVOKE ALL ON SCHEMA public FROM PUBLIC")
        c.execute("GRANT USAGE ON SCHEMA public TO amjis_app")
        for (t,) in c.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'").fetchall():
            c.execute(f'ALTER TABLE public."{t}" OWNER TO amjis_app')
        for (sq,) in c.execute("SELECT sequencename FROM pg_sequences WHERE schemaname = 'public'").fetchall():
            c.execute(f'ALTER SEQUENCE public."{sq}" OWNER TO amjis_app')
        c.execute("ALTER FUNCTION public.nirmana_invalidate_registry_receipts() OWNER TO amjis_app")
        c.commit()


def _row(connect, aid="mi_bhavisya"):
    return _q(connect, "SELECT natural_key_partition, md5(natural_key_partition), length(natural_key_partition), to_jsonb(r) - 'natural_key_partition' "
                       "FROM asset_registry r WHERE asset_id = %s", (aid,))[0]


def _freshness(connect):
    return _q(connect, "SELECT asset_id, chart_id::text, scope_key, partition_key, freshness_state, reasons::text, observed_at::text FROM asset_freshness ORDER BY 1, 2, 3")


def test_fixture_mirrors_production_and_the_trigger_column_list_contains_natural_key_partition(db):
    _make_fixture(db)
    r = _q(db, "SELECT has_schema_privilege('amjis_app','public','CREATE'), (SELECT relowner::regrole::text FROM pg_class WHERE oid='asset_registry'::regclass), "
               "(SELECT pg_get_triggerdef(oid) FROM pg_trigger WHERE tgname='nirmana_registry_receipt_invalidation')")[0]
    assert r[0] is False and r[1] == "amjis_app" and "UPDATE OF depends_on, natural_key_partition," in r[2]
    assert _row(db)[1] == OLD_MD5


def test_apply_stores_the_new_text_changes_no_other_column_and_stales_nothing(db):
    _make_fixture(db)
    others_before = {a: _row(db, a) for a in ASSETS if a != "mi_bhavisya"}
    rest_before = _row(db)[3]
    fresh_before = _freshness(db)
    _apply(db, _REAL)
    txt, md5, ln, rest = _row(db)
    assert (md5, ln, txt) == (NEW_MD5, NEW_LEN, _new_text())
    assert rest == rest_before and rest["integrity_check_sql"] == INTEGRITY_SENTINEL, "another column changed (integrity_check_sql is 1259's)"
    assert {a: _row(db, a) for a in ASSETS if a != "mi_bhavisya"} == others_before
    assert _freshness(db) == fresh_before, "the trigger fired on freshness rows: it must update 0 rows (mi_bhavisya has none)"


def test_the_trigger_does_fire_on_this_column_so_the_no_stale_result_is_because_there_are_no_rows(db):
    _make_fixture(db)
    _exec(db, "UPDATE asset_registry SET natural_key_partition = 'changed' WHERE asset_id = 'mi_kula'")
    st = {(a, s) for a, _, _, _, s, _, _ in _freshness(db)}
    assert ("mi_kula", "stale") in st and ("mi_jivanaghatana", "fresh") in st and ("ph_nimitta", "fresh") in st


@pytest.mark.parametrize("kind", ["freshness", "receipt"])
def test_refuses_when_a_freshness_or_receipt_row_exists_keyed_by_the_old_text_and_changes_nothing(db, kind):
    _make_fixture(db, fresh_for=("mi_bhavisya",) if kind == "freshness" else (), receipts_for=("mi_bhavisya",) if kind == "receipt" else ())
    before, fresh = _row(db), _freshness(db)
    with pytest.raises(Exception) as ei:
        _apply(db, _REAL)
    assert "would strand them" in str(ei.value), str(ei.value)
    assert _row(db) == before and _freshness(db) == fresh


@pytest.mark.parametrize("bad", ["SELECT false", "", None])
def test_md5_guard_refuses_an_unexpected_text_including_null_and_changes_nothing(db, bad):
    _make_fixture(db, nkp=bad)
    before = _row(db)
    with pytest.raises(Exception) as ei:
        _apply(db, _REAL)
    assert "is not the text this migration was written against" in str(ei.value), str(ei.value)
    assert _row(db) == before


def test_refuses_a_missing_registry_row(db):
    _make_fixture(db)
    _exec(db, "DELETE FROM asset_registry WHERE asset_id = 'mi_bhavisya'")
    with pytest.raises(Exception) as ei:
        _apply(db, _REAL)
    assert "expected exactly one mi_bhavisya registry row" in str(ei.value)


def test_idempotent_second_run_rewrites_nothing_and_does_not_fire_the_trigger(db):
    _make_fixture(db)
    _apply(db, _REAL)
    _exec(db, "INSERT INTO asset_freshness (asset_id, chart_id, scope_key, partition_key, freshness_state, receipt_version) VALUES ('mi_bhavisya', NULL, 'k', 'p', 'fresh', 'v1')")
    snap_reg = _q(db, "SELECT asset_id, xmin::text FROM asset_registry ORDER BY 1")
    snap_fresh = _freshness(db)
    notices: list[str] = []
    _apply(db, _REAL, notices)
    assert any("already carries the append-only text" in n for n in notices)
    assert _q(db, "SELECT asset_id, xmin::text FROM asset_registry ORDER BY 1") == snap_reg and _freshness(db) == snap_fresh


def test_a_1259_style_update_of_integrity_check_sql_before_or_after_does_not_interfere(db):
    for order in ("before", "after"):
        _make_fixture(db)
        upd = "UPDATE asset_registry SET integrity_check_sql = 'SELECT true -- 1259 text' WHERE asset_id = 'mi_bhavisya'"
        if order == "before":
            _exec(db, upd)
        _apply(db, _REAL)
        if order == "after":
            _exec(db, upd)
        txt, md5, ln, rest = _row(db)
        assert md5 == NEW_MD5 and rest["integrity_check_sql"] == "SELECT true -- 1259 text"


@pytest.mark.parametrize("state", ["running", "planned", "paused"])
def test_active_build_run_guard_refuses_and_changes_nothing(db, state):
    _make_fixture(db)
    _exec(db, "INSERT INTO build_runs (state) VALUES (%s)", (state,))
    _exec(db, "INSERT INTO build_run_assets (run_id, asset_id) SELECT max(id), 'mi_bhavisya' FROM build_runs")
    before = _row(db)
    with pytest.raises(Exception) as ei:
        _apply(db, _REAL)
    assert "active build run" in str(ei.value) and _row(db) == before


def test_finished_runs_and_runs_of_other_assets_do_not_block(db):
    _make_fixture(db)
    for st, aid in (("completed", "mi_bhavisya"), ("failed", "mi_bhavisya"), ("stopped", "mi_bhavisya"), ("running", "mi_kula")):
        _exec(db, "INSERT INTO build_runs (state) VALUES (%s)", (st,))
        _exec(db, "INSERT INTO build_run_assets (run_id, asset_id) SELECT max(id), %s FROM build_runs", (aid,))
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


# -- MUTATION proof ---------------------------------------------------------------------

def _scenario(db, sql):
    v = []
    _make_fixture(db)
    rest_before = _row(db)[3]
    others = {a: _row(db, a) for a in ASSETS if a != "mi_bhavisya"}
    fresh = _freshness(db)
    try:
        _apply(db, sql)
    except Exception as exc:  # noqa: BLE001
        return [f"apply failed: {str(exc).splitlines()[0]}"]
    txt, md5, ln, rest = _row(db)
    if (md5, ln, txt) != (NEW_MD5, NEW_LEN, _new_text()):
        v.append(f"new text not stored ({md5})")
    if rest != rest_before:
        v.append("another column changed")
    if {a: _row(db, a) for a in ASSETS if a != "mi_bhavisya"} != others:
        v.append("another asset changed")
    if _freshness(db) != fresh:
        v.append("freshness moved")
    return v


def _guard_scenario(db, sql):
    v = []
    _make_fixture(db, nkp="SELECT false")
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
    snap = _q(db, "SELECT xmin::text FROM asset_registry WHERE asset_id='mi_bhavisya'")
    try:
        _apply(db, sql)
    except Exception as exc:  # noqa: BLE001
        return v + [f"re-run failed: {str(exc).splitlines()[0]}"]
    if _q(db, "SELECT xmin::text FROM asset_registry WHERE asset_id='mi_bhavisya'") != snap:
        v.append("re-run rewrote the row")
    return v


def _strand_scenario(db, sql):
    v = []
    for kw in ({"receipts_for": ("mi_bhavisya",)}, {"fresh_for": ("mi_bhavisya",)}):
        _make_fixture(db, **kw)
        before = _row(db)
        try:
            _apply(db, sql)
            v.append(f"applied although a row keyed by the old text exists ({list(kw)[0]})")
        except Exception as exc:  # noqa: BLE001
            if "would strand them" not in str(exc):
                v.append(f"refused for another reason: {str(exc).splitlines()[0]}")
        if _row(db) != before:
            v.append("changed the row while refusing")
    return v


def _runs_scenario(db, sql):
    _make_fixture(db)
    _exec(db, "INSERT INTO build_runs (state) VALUES ('running')")
    _exec(db, "INSERT INTO build_run_assets (run_id, asset_id) VALUES (1, 'mi_bhavisya')")
    try:
        _apply(db, sql)
        return ["applied during an active run"]
    except Exception as exc:  # noqa: BLE001
        return [] if "active build run" in str(exc) else [f"refused for another reason: {str(exc).splitlines()[0]}"]


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
    """An embedded target text that no longer hashes to the named md5 (edited, md5 forgotten) must be refused by the post-check."""
    edited = sql.replace("The key matches the table's own live PRIMARY KEY exactly.", "The key matches the table's own live PRIMARY KEY, approximately.", 1)
    assert edited != sql
    _make_fixture(db)
    try:
        _apply(db, edited)
        return ["a target text that does not hash to the named md5 was installed"]
    except Exception:  # noqa: BLE001
        return []


_UPDATE_RE = r"UPDATE asset_registry\nSET natural_key_partition = \$nkp\$.*?\$nkp\$\nWHERE asset_id = 'mi_bhavisya'\n  AND md5\(natural_key_partition\) = '%s';\n" % OLD_MD5
_MUTANTS = {
    "update_guard_removed": (re.sub(r"\n  AND md5\(natural_key_partition\) = '%s';" % OLD_MD5, ";", _REAL), "guard"),
    "pre_check_neutered": (_REAL.replace("ELSIF v_md5 IS DISTINCT FROM '%s' THEN" % OLD_MD5, "ELSIF false THEN"), "guard"),
    "strand_guard_neutered": (_REAL.replace("IF v_fresh > 0 OR v_rcpt > 0 THEN", "IF false THEN"), "strand"),
    "strand_guard_ignores_receipts": (_REAL.replace("IF v_fresh > 0 OR v_rcpt > 0 THEN", "IF v_fresh > 0 THEN"), "strand"),
    "strand_guard_ignores_freshness": (_REAL.replace("IF v_fresh > 0 OR v_rcpt > 0 THEN", "IF v_rcpt > 0 THEN"), "strand"),
    "active_runs_guard_neutered": (_REAL.replace("IF n_active > 0 THEN", "IF false THEN"), "runs"),
    "post_md5_check_neutered": (_REAL.replace("IF v_md5 IS DISTINCT FROM '%s' OR v_len IS DISTINCT FROM %d THEN" % (NEW_MD5, NEW_LEN), "IF false THEN"), "post"),
    "lock_timeout_removed": (_REAL.replace("SET LOCAL lock_timeout = '5s';", "", 1), "lock"),
    "lock_timeout_session_wide": (_REAL.replace("SET LOCAL lock_timeout = '5s';", "SET lock_timeout = '0';", 1), "lock"),
    "update_removed": (re.sub(_UPDATE_RE, "", _REAL, flags=re.S), "scenario"),
    "wrong_column_updated": (_REAL.replace("SET natural_key_partition = $nkp$", "SET integrity_check_sql = $nkp$", 1), "scenario"),
    "other_column_also_changed": (_REAL.replace("$nkp$\nWHERE asset_id = 'mi_bhavisya'", "$nkp$, volume_explanation = 'changed'\nWHERE asset_id = 'mi_bhavisya'", 1), "scenario"),
    "old_text_installed_as_target": (_REAL.replace(_new_text(), _old_text()), "scenario"),
    "other_asset_also_updated": (_REAL.replace("WHERE asset_id = 'mi_bhavisya'\n  AND md5(natural_key_partition)", "WHERE asset_id IN ('mi_bhavisya', 'mi_kula')\n  AND md5(natural_key_partition)", 1), "scenario"),
}


def test_mutants_are_real_mutations_of_the_real_file():
    for name, (sql, _) in _MUTANTS.items():
        assert sql != _REAL, f"mutant {name} did not change the file (the mutation pattern is stale)"


def test_the_real_file_produces_no_violations(db):
    assert _scenario(db, _REAL) == []
    assert _guard_scenario(db, _REAL) == []
    assert _strand_scenario(db, _REAL) == []
    assert _runs_scenario(db, _REAL) == []
    assert _lock_scenario(db, _REAL) == []
    assert _post_scenario(db, _REAL) == []


@pytest.mark.parametrize("name", sorted(_MUTANTS))
def test_every_mutant_is_caught(db, name):
    sql, kind = _MUTANTS[name]
    v = {"scenario": _scenario, "guard": _guard_scenario, "strand": _strand_scenario, "runs": _runs_scenario, "lock": _lock_scenario, "post": _post_scenario}[kind](db, sql)
    assert v, f"mutant {name} was NOT caught"
