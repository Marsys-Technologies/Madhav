"""
Migration 1296 (Suvarna S-L2 fast path): asset_registry.writer_timeout_seconds raised for seven bodha writers
(bo_arudha / bo_nakshatra_semantic / bo_special_lagna / bo_vargottama_dhana / bo_yantra_mechanism 600 -> 3600;
bo_grounding / bo_laksana_rerank 1800 -> 5400), each row only WHERE it still holds its expected old value.

Applies the REAL on-disk migration to a DISPOSABLE PostgreSQL cluster this module creates with initdb in a temp dir (own port, trust
auth, removed at session end). Skipped, loudly, when no initdb/pg_ctl is found. Proves: guarded update (all seven take their new value;
bo_sudarshana and a bystander keep theirs), idempotent replay (no row rewritten, xmin unchanged, NOTICE), a deliberately different value
is left alone with a NOTICE and no failure, the production trigger body does not fire (asset_freshness untouched), a missing row is a
NOTICE, and a silent no-op on a guard-matched row RAISES. Does NOT prove production state (read from production after deploy; Trap 103).
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
_M1296 = _REPO / "platform" / "migrations" / "1296_bodha_writer_timeouts_s_l2_rebuild.sql"

OLD = {"bo_arudha": 600, "bo_nakshatra_semantic": 600, "bo_special_lagna": 600, "bo_vargottama_dhana": 600,
       "bo_yantra_mechanism": 600, "bo_grounding": 1800, "bo_laksana_rerank": 1800}
NEW = {"bo_arudha": 3600, "bo_nakshatra_semantic": 3600, "bo_special_lagna": 3600, "bo_vargottama_dhana": 3600,
       "bo_yantra_mechanism": 3600, "bo_grounding": 5400, "bo_laksana_rerank": 5400}
UNTOUCHED = {"bo_sudarshana": 600, "bo_laksana": 10800, "bo_bimba": 10800, "ga_dashas": 1800}
CANON = "482012f1-710e-4a25-994a-93821f5871aa"


# -- STATIC ---------------------------------------------------------------------------------------------------------------

def test_static_file_matches_the_plan_and_sets_lock_timeout_first():
    code = "\n".join(l for l in _M1296.read_text().splitlines() if not l.lstrip().startswith("--"))
    assert code.strip().startswith("SET LOCAL lock_timeout = '5s';")
    tuples = {m[0]: (int(m[1]), int(m[2])) for m in re.findall(r"\('(bo_[a-z_]+)',\s*(\d+),\s*(\d+)\)", code)}
    assert tuples == {k: (OLD[k], NEW[k]) for k in OLD}


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
    root = Path(tempfile.mkdtemp(prefix="m1296pg"))
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
    scope text, has_writer boolean, writer_timeout_seconds integer NOT NULL DEFAULT 600);
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


def _setup(connect, overrides: dict[str, int] | None = None, skip: tuple[str, ...] = ()):
    rows = {**OLD, **UNTOUCHED, **(overrides or {})}
    with connect() as c:
        c.execute(_FIXTURE_DDL)
        for a, v in rows.items():
            if a in skip:
                continue
            c.execute("INSERT INTO asset_registry (asset_id, layer, writer_timeout_seconds) VALUES (%s, 'bodha', %s)", (a, v))
            c.execute("INSERT INTO asset_freshness (asset_id, chart_id, freshness_state) VALUES (%s, %s, 'fresh')", (a, CANON))
        c.commit()


def _apply(connect, notices: list[str] | None = None):
    conn = connect()
    if notices is not None:
        conn.add_notice_handler(lambda d: notices.append(d.message_primary))
    try:
        conn.execute(_M1296.read_text())
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _q(connect, sql, params=None):
    with connect() as c:
        return c.execute(sql, params).fetchall()


def _timeouts(connect) -> dict[str, int]:
    return dict(_q(connect, "SELECT asset_id, writer_timeout_seconds FROM asset_registry"))


def test_live_guarded_update_raises_exactly_the_seven_rows(db):
    _setup(db)
    _apply(db)
    assert _timeouts(db) == {**NEW, **UNTOUCHED}


def test_live_update_touches_only_the_timeout_column_and_does_not_fire_the_staling_trigger(db):
    _setup(db)
    before = _q(db, "SELECT to_jsonb(r) - 'writer_timeout_seconds' FROM asset_registry r ORDER BY asset_id")
    fresh = _q(db, "SELECT asset_id, chart_id, freshness_state, reasons::text, observed_at FROM asset_freshness ORDER BY asset_id")
    _apply(db)
    assert _q(db, "SELECT to_jsonb(r) - 'writer_timeout_seconds' FROM asset_registry r ORDER BY asset_id") == before
    assert _q(db, "SELECT asset_id, chart_id, freshness_state, reasons::text, observed_at FROM asset_freshness ORDER BY asset_id") == fresh
    assert {r[2] for r in fresh} == {"fresh"}


def test_live_idempotent_second_run_rewrites_nothing(db):
    _setup(db)
    _apply(db)
    x1 = _q(db, "SELECT asset_id, xmin::text FROM asset_registry ORDER BY asset_id")
    notes: list[str] = []
    _apply(db, notes)
    assert _q(db, "SELECT asset_id, xmin::text FROM asset_registry ORDER BY asset_id") == x1
    assert _timeouts(db) == {**NEW, **UNTOUCHED}
    assert sum("already" in n and "nothing to do" in n for n in notes) == 7


def test_live_a_different_value_is_left_alone_with_a_notice_and_no_failure(db):
    _setup(db, {"bo_arudha": 900, "bo_grounding": 10800})
    notes: list[str] = []
    _apply(db, notes)  # must not raise
    t = _timeouts(db)
    assert t["bo_arudha"] == 900 and t["bo_grounding"] == 10800
    assert all(t[a] == NEW[a] for a in NEW if a not in ("bo_arudha", "bo_grounding"))
    assert any("bo_arudha" in n and "left untouched" in n and "900" in n for n in notes)
    assert any("bo_grounding" in n and "left untouched" in n for n in notes)


def test_live_a_row_already_at_its_new_value_is_a_noop_notice(db):
    _setup(db, {"bo_special_lagna": 3600})
    notes: list[str] = []
    _apply(db, notes)
    assert _timeouts(db) == {**NEW, **UNTOUCHED}
    assert any("bo_special_lagna" in n and "already 3600" in n for n in notes)


def test_live_missing_rows_are_a_notice(db):
    _setup(db, skip=("bo_yantra_mechanism",))
    notes: list[str] = []
    _apply(db, notes)
    assert "bo_yantra_mechanism" not in _timeouts(db)
    assert any("bo_yantra_mechanism has no asset_registry row" in n for n in notes)


def test_live_post_check_catches_a_silent_noop_on_a_guard_matched_row(db):
    _setup(db)
    with db() as c:
        c.execute("CREATE RULE swallow AS ON UPDATE TO asset_registry WHERE OLD.asset_id = 'bo_arudha' DO INSTEAD NOTHING")
        c.commit()
    with pytest.raises(Exception) as ei:
        _apply(db)
    assert "bo_arudha writer_timeout_seconds update did not take" in str(ei.value)
    assert _timeouts(db) == {**OLD, **UNTOUCHED}  # the whole file rolled back
