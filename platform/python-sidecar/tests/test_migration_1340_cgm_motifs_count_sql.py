"""
Migration 1340 (after-certification fix): bo_cgm_motifs' registered count_sql is widened from bodha_cgm_motifs alone (600 rows)
to the three tables its writer writes (motifs + sub-graphs + topology summary = 610 on the canonical chart).

Two tiers:
  * STATIC (always runs): the file's own SQL text, md5s, guard shape, the writer's three INSERT targets.
  * LIVE (needs PostgreSQL server binaries): applies the REAL on-disk migration to a DISPOSABLE cluster this module creates with
    initdb in a temp dir (own port, trust auth, removed at session end). Skipped, loudly, when no initdb/pg_ctl is found.

LIVE proves: the new count_sql returns 5+60+5 = 70 for a synthetic chart and ONLY that chart's rows (a second chart is not counted);
it runs through the orchestrator's own probe shape (count_sql.replace("$1", "%s") with ONE bound parameter, as
asset_runner._data_rows_present does) AND with a native $1 bind; the UPDATE is guarded (a foreign text is left untouched, NOTICE, no
failure), idempotent (second run rewrites nothing, xmin unchanged), the row's other columns are untouched, the production trigger body
does not fire (count_sql is not one of its columns), and a silent no-op is caught by the post-check.
It does NOT prove production state (read from production structure after deploy; Trap 103).
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
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[3]
_M1340 = _REPO / "platform" / "migrations" / "1340_bo_cgm_motifs_count_sql_three_tables.sql"
_WRITER = _REPO / "platform" / "python-sidecar" / "pipeline" / "orchestrator" / "writers" / "bo_cgm_motifs.py"

OLD_TEXT = "SELECT count(*) FROM bodha_cgm_motifs WHERE chart_id = $1"
OLD_MD5 = "610fd9db0ecced863abfe7cd31764a53"
NEW_MD5 = "1c2dc6a2c4a26699635eecb0309d5f18"
TABLES = ["bodha_cgm_motifs", "bodha_cgm_sub_graphs", "bodha_cgm_chart_topology_summary"]
CANON = "482012f1-710e-4a25-994a-93821f5871aa"
OTHER = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"


def _md5(t: str) -> str:
    return hashlib.md5(t.encode()).hexdigest()


def _code(path: Path) -> str:
    return "\n".join(l for l in path.read_text().splitlines() if not l.lstrip().startswith("--"))


def _new_text() -> str:
    return re.search(r"\$cs\$(.*?)\$cs\$", _M1340.read_text(), re.S).group(1)


# -- STATIC tier --------------------------------------------------------------------------------------------------------

def test_static_old_and_new_text_hash_to_the_named_md5s():
    assert _md5(OLD_TEXT) == OLD_MD5 and len(OLD_TEXT) == 57
    assert _md5(_new_text()) == NEW_MD5 and len(_new_text()) == 284


def test_static_new_text_counts_exactly_the_three_tables_the_writer_inserts_into():
    w = _WRITER.read_text()
    written = re.findall(r"INSERT INTO public\.(bodha_cgm_\w+) \(", w)
    assert sorted(set(written)) == sorted(TABLES)
    assert sorted(re.findall(r"\bFROM\s+(\w+)", _new_text())) == sorted(TABLES)
    assert _new_text().count("$1") == 1


def test_static_one_guarded_update_of_count_sql_only_lock_timeout_first():
    code = _code(_M1340)
    assert code.strip().startswith("SET LOCAL lock_timeout = '5s';")
    assert re.findall(r"\bSET\s+([a-z_]+)\s*=", code.replace("SET LOCAL lock_timeout =", ""), re.I) == ["count_sql"]
    assert f"AND md5(count_sql) = '{OLD_MD5}';" in code
    assert not re.search(r"\b(BEGIN|COMMIT|ROLLBACK)\b\s*;", code)


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
    root = Path(tempfile.mkdtemp(prefix="m1340pg"))
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


_FIXTURE_DDL = """
CREATE TABLE asset_registry (
    asset_id text PRIMARY KEY, layer text NOT NULL, depends_on text[], is_active boolean NOT NULL DEFAULT true,
    target_table text, count_sql text, target_floor integer, size_sql text, volume_explanation text,
    natural_key_partition text, health_probe text, integrity_check_sql text, asset_kind text, asset_type text,
    scope text, has_writer boolean);
CREATE TABLE bodha_cgm_motifs (summary_id serial PRIMARY KEY, chart_id uuid NOT NULL);
CREATE TABLE bodha_cgm_sub_graphs (rollup_id serial PRIMARY KEY, chart_id uuid NOT NULL);
CREATE TABLE bodha_cgm_chart_topology_summary (pattern_id serial PRIMARY KEY, chart_id uuid NOT NULL);
CREATE TABLE asset_freshness (
    asset_id text NOT NULL, chart_id uuid NOT NULL, freshness_state text NOT NULL,
    reasons jsonb NOT NULL DEFAULT '[]'::jsonb, observed_at timestamptz NOT NULL DEFAULT '2026-10-01T00:00:00Z',
    PRIMARY KEY (asset_id, chart_id));
CREATE OR REPLACE FUNCTION nirmana_invalidate_registry_receipts() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  UPDATE asset_freshness SET freshness_state = 'stale',
         reasons = CASE WHEN reasons ? 'registry_changed' THEN reasons ELSE reasons || '["registry_changed"]'::jsonb END,
         observed_at = now()
   WHERE asset_id = NEW.asset_id;
  RETURN NEW;
END; $$;
CREATE TRIGGER nirmana_registry_receipt_invalidation
AFTER UPDATE OF depends_on, natural_key_partition, health_probe, integrity_check_sql, target_floor, asset_kind, asset_type,
                scope, has_writer, is_active, target_table ON asset_registry
FOR EACH ROW WHEN (OLD IS DISTINCT FROM NEW) EXECUTE FUNCTION nirmana_invalidate_registry_receipts();
"""


def _setup(connect, count_sql: str | None = OLD_TEXT, with_row: bool = True):
    with connect() as c:
        c.execute(_FIXTURE_DDL)
        if with_row:
            c.execute("INSERT INTO asset_registry (asset_id, layer, depends_on, target_table, count_sql, target_floor, size_sql, "
                      "volume_explanation, scope, has_writer) VALUES ('bo_cgm_motifs','bodha','{bo_sangati}',"
                      "'bodha_cgm_motifs', %s, 5, 'SELECT 1', 'x', 'per_chart', true)", (count_sql,))
            c.execute("INSERT INTO asset_registry (asset_id, layer, count_sql) VALUES ('bo_other','bodha','SELECT 1 WHERE $1 IS NOT NULL')")
        # canonical chart: 600 + 5 + 5 = 610 (the production readback of 2026-10-09); another chart must NOT be counted
        for chart, (a, b, d) in {CANON: (600, 5, 5), OTHER: (50, 3, 7)}.items():
            for t, n in zip(TABLES, (a, b, d)):
                c.execute(f"INSERT INTO {t} (chart_id) SELECT %s::uuid FROM generate_series(1, %s)", (chart, n))
        c.execute("INSERT INTO asset_freshness (asset_id, chart_id, freshness_state) VALUES ('bo_cgm_motifs', %s, 'fresh')", (CANON,))
        c.commit()


def _apply(connect, capture_notices: list[str] | None = None):
    conn = connect()
    if capture_notices is not None:
        conn.add_notice_handler(lambda d: capture_notices.append(d.message_primary))
    try:
        conn.execute(_M1340.read_text())
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _q(connect, sql, params=None):
    with connect() as c:
        return c.execute(sql, params).fetchall()


def _csql(connect):
    return _q(connect, "SELECT count_sql FROM asset_registry WHERE asset_id='bo_cgm_motifs'")[0][0]


def test_live_old_text_counts_600_new_text_counts_610_and_only_the_given_chart(db):
    _setup(db)
    assert _q(db, OLD_TEXT.replace("$1", "%s"), (CANON,))[0][0] == 600
    _apply(db)
    txt = _csql(db)
    assert _md5(txt) == NEW_MD5
    # (1) the orchestrator's own probe shape: replace $1 with %s, ONE parameter
    assert _q(db, txt.replace("$1", "%s"), (CANON,))[0][0] == 610
    assert _q(db, txt.replace("$1", "%s"), (OTHER,))[0][0] == 50 + 3 + 7
    # (2) a native $1 bind (what the cockpit / watchdog routes do through node-postgres)
    with db() as c:
        c.execute("PREPARE q AS " + txt)  # $1's type is inferred from the ::uuid cast, no type list needed
        assert c.execute(f"EXECUTE q('{CANON}')").fetchone()[0] == 610
    # a chart with no rows counts 0
    assert _q(db, txt.replace("$1", "%s"), ("00000000-0000-4000-8000-0000000000a1",))[0][0] == 0


def test_live_a_repeated_dollar_one_form_would_break_the_single_parameter_probe(db):
    """Why the new text has $1 exactly once: this is what the repeated form does under the orchestrator's probe shape."""
    _setup(db)
    repeated = ("SELECT (SELECT count(*) FROM bodha_cgm_motifs WHERE chart_id = $1) + "
                "(SELECT count(*) FROM bodha_cgm_sub_graphs WHERE chart_id = $1) AS count")
    with pytest.raises(Exception):
        _q(db, repeated.replace("$1", "%s"), (CANON,))


def test_live_update_touches_only_count_sql_and_does_not_fire_the_staling_trigger(db):
    _setup(db)
    before = _q(db, "SELECT to_jsonb(r) - 'count_sql' FROM asset_registry r ORDER BY asset_id")
    fresh = _q(db, "SELECT asset_id, chart_id, freshness_state, reasons::text, observed_at FROM asset_freshness")
    _apply(db)
    assert _q(db, "SELECT to_jsonb(r) - 'count_sql' FROM asset_registry r ORDER BY asset_id") == before
    assert _q(db, "SELECT asset_id, chart_id, freshness_state, reasons::text, observed_at FROM asset_freshness") == fresh
    assert fresh[0][2] == "fresh"
    # the other asset's count_sql is untouched
    assert _q(db, "SELECT count_sql FROM asset_registry WHERE asset_id='bo_other'")[0][0] == "SELECT 1 WHERE $1 IS NOT NULL"


def test_live_idempotent_second_run_rewrites_nothing(db):
    _setup(db)
    _apply(db)
    x1 = _q(db, "SELECT xmin::text FROM asset_registry WHERE asset_id='bo_cgm_motifs'")
    notes: list[str] = []
    _apply(db, notes)
    assert _q(db, "SELECT xmin::text FROM asset_registry WHERE asset_id='bo_cgm_motifs'") == x1
    assert any("already counts the three tables" in n for n in notes)
    assert _md5(_csql(db)) == NEW_MD5


def test_live_foreign_text_is_left_untouched_notice_and_no_failure(db):
    foreign = "SELECT count(*) FROM bodha_cgm_motifs WHERE chart_id = $1 AND true"
    _setup(db, foreign)
    notes: list[str] = []
    _apply(db, notes)  # must not raise
    assert _csql(db) == foreign
    assert any("not the text this migration was written against" in n and "NO-OP" in n for n in notes)


def test_live_empty_registry_is_a_noop(db):
    _setup(db, with_row=False)
    notes: list[str] = []
    _apply(db, notes)
    assert any("no bo_cgm_motifs registry row" in n for n in notes)


def test_live_post_check_catches_a_silent_noop(db):
    """If the UPDATE silently did nothing while the row still carries the old text, the migration RAISES (here: a rule that swallows it)."""
    _setup(db)
    with db() as c:
        c.execute("CREATE RULE swallow AS ON UPDATE TO asset_registry WHERE OLD.asset_id = 'bo_cgm_motifs' DO INSTEAD NOTHING")
        c.commit()
    with pytest.raises(Exception) as ei:
        _apply(db)
    assert "update did not take" in str(ei.value)
    assert _csql(db) == OLD_TEXT


# -- STATIC pins for the guard blocks (reviewer note: the live tier catches only RAISE->NOTICE) -----------------------------

def test_static_pre_and_post_blocks_exist_and_pin_both_md5s():
    code = _code(_M1340)
    assert code.count("DO $pre$") == 1 and code.count("DO $post$") == 1
    pre = code.split("DO $pre$", 1)[1].split("$pre$;", 1)[0]
    post = code.split("DO $post$", 1)[1].split("$post$;", 1)[0]
    # the pre-check recognises the NEW text (idempotent no-op) and the OLD text (the one this was written against)
    assert f"'{NEW_MD5}'" in pre and f"'{OLD_MD5}'" in pre
    # the post-check RAISES EXCEPTION when the row still carries the OLD md5, and only then
    assert "RAISE EXCEPTION" in post and f"'{OLD_MD5}'" in post and "RAISE NOTICE" not in post
    # the UPDATE is guarded by the OLD md5 and writes the text whose md5 is NEW_MD5
    upd = code.split("UPDATE asset_registry", 1)[1].split(";", 1)[0]
    assert f"md5(count_sql) = '{OLD_MD5}'" in upd and "asset_id = 'bo_cgm_motifs'" in upd
    assert _md5(_new_text()) == NEW_MD5                       # the text the UPDATE writes hashes to the NEW md5
