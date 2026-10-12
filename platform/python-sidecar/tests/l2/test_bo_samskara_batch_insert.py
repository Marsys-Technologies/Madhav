"""
tests/l2/test_bo_samskara_batch_insert.py -- bo_samskara insert-phase batching (PREPARED fallback).

Production run 7c95b3e1 (2026-10-08): the insert phase of ~25k embedding rows per ayanamsha went
through ``executemany`` in batches of 10 (~2,500 statements per ayanamsha, ~8 min uncontended, ~19 min
under contention). It is now one multi-row INSERT per 500 rows (5,000 bind parameters, under the
65,535 limit) with identical per-row values, identical vector literal, identical ON CONFLICT semantics.

Tiers:
  * FAKE CURSOR (always runs): statement count for 25k rows, row values/order identical to the old
    per-row path, keepalive between batches, no commit/rollback/close of the connection.
  * LIVE (disposable PostgreSQL via initdb in a temp dir, skipped loudly if binaries are absent):
    the new path stores a table byte-identical to the old per-row ``_INSERT`` path, re-insert is an
    idempotent upsert, and a failing batch falls back per-row without aborting the transaction.
"""
from __future__ import annotations

import glob
import os
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path

import pytest

from pipeline.orchestrator.writers import bo_samskara as mod


def _row(i: int, *, vec_seed: float = 0.0) -> dict:
    vec = [(i % 7) * 0.125 + j * 1e-3 + vec_seed for j in range(768)]
    return {
        "embedding_id": f"00000000-0000-0000-0000-{i:012d}",
        "signal_id": f"SIG.{i:05d}",
        "chart_id": "482012f1-710e-4a25-994a-93821f5871aa",
        "ayanamsha_id": "lahiri_chitrapaksha",
        "build_id": "00000000-0000-0000-0000-00000000bbbb",
        "embedding_vec": "[" + ",".join(f"{v:.8f}" for v in vec) + "]",
        "embedding_model": "m",
        "embedding_model_version": "v1",
        "embedding_input_summary": f"summary {i}",
        "computed_at": "2026-10-09T00:00:00+00:00",
    }


class Cur:
    def __init__(self, conn):
        self.conn = conn
        self.rowcount = 0

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def execute(self, sql, params=None):
        self.conn.calls.append((" ".join(str(sql).split()), params))
        if str(sql).lstrip().startswith("INSERT"):
            n = len(params) // len(mod._COLS) if isinstance(params, (list, tuple)) else 1
            if self.conn.fail_multi and isinstance(params, (list, tuple)) and n > 1:
                raise RuntimeError("boom")
            self.rowcount = n
        return self

    def executemany(self, sql, seq):
        self.conn.calls.append(("EXECUTEMANY", list(seq)))


class Conn:
    def __init__(self, fail_multi=False):
        self.calls = []
        self.fail_multi = fail_multi

    def cursor(self):
        return Cur(self)

    def commit(self):
        raise AssertionError("never commit ctx.db_conn")

    def rollback(self):
        raise AssertionError("never rollback ctx.db_conn")

    def close(self):
        raise AssertionError("never close ctx.db_conn")


def _inserts(conn):
    return [c for c in conn.calls if c[0].startswith("INSERT")]


def test_batch_size_is_500_and_params_under_postgres_limit():
    assert mod._BATCH_SIZE == 500
    assert mod._BATCH_SIZE * len(mod._COLS) < 65535
    assert len(mod._COLS) == 10


def test_25k_rows_use_50_statements_not_2500():
    rows = [{c: i for c in mod._COLS} for i in range(25000)]
    conn = Conn()
    assert mod._batch_insert(conn, rows) == 25000
    assert len(_inserts(conn)) == 50                      # was 2,500 at 10 rows per batch
    assert all(len(p) <= 5000 for _, p in _inserts(conn))


def test_params_are_row_values_in_order_identical_to_old_per_row_path():
    rows = [_row(i) for i in range(1203)]                 # 500 + 500 + 203
    conn = Conn()
    mod._batch_insert(conn, rows)
    flat = [v for _, p in _inserts(conn) for v in p]
    old_order = [r[c] for r in rows for c in mod._COLS]   # what executemany(_INSERT) bound, row by row
    assert flat == old_order
    assert [len(p) // 10 for _, p in _inserts(conn)] == [500, 500, 203]


def test_statement_shape_one_values_tuple_per_row_vector_cast_on_vec_only_and_upsert_kept():
    sql = mod._multi_insert_sql(3)
    assert sql.count("::vector") == 3
    assert sql.count("%s") == 30
    assert "ON CONFLICT (signal_id) DO UPDATE SET" in sql
    assert "embedding_vec           = EXCLUDED.embedding_vec" in sql
    assert " ".join(mod._multi_insert_sql(1).split()).startswith(
        "INSERT INTO public.bodha_signal_embeddings ( embedding_id, signal_id, chart_id, ayanamsha_id, build_id, "
        "embedding_vec, embedding_model, embedding_model_version, embedding_input_summary, computed_at ) VALUES")
    # the single-row fallback statement binds the same columns in the same order
    assert [c for c in mod._COLS] == [
        "embedding_id", "signal_id", "chart_id", "ayanamsha_id", "build_id", "embedding_vec",
        "embedding_model", "embedding_model_version", "embedding_input_summary", "computed_at"]


def test_keepalive_between_every_insert_batch_and_no_tx_control_on_connection():
    conn = Conn()
    mod._batch_insert(conn, [{c: i for c in mod._COLS} for i in range(1203)])
    seq = [c[0] for c in conn.calls if c[0].startswith(("INSERT", "SELECT 1"))]
    assert [s.startswith("INSERT") for s in seq] == [True, False, True, False, True, False]
    assert seq[1] == seq[3] == seq[5] == "SELECT 1"


def test_failed_batch_falls_back_per_row_under_savepoint():
    rows = [{c: i for c in mod._COLS} for i in range(7)]
    conn = Conn(fail_multi=True)
    assert mod._batch_insert(conn, rows) == 7
    stmts = [c[0] for c in conn.calls]
    assert "ROLLBACK TO SAVEPOINT batch_sp" in stmts      # transaction not left aborted
    single = [c for c in _inserts(conn) if len(c[1]) == 10 or isinstance(c[1], dict)]
    assert len(single) == 7


# ── LIVE tier ────────────────────────────────────────────────────────────────

def _find_pg_bin():
    cands = []
    if os.environ.get("PG_BIN"):
        cands.append(Path(os.environ["PG_BIN"]))
    w = shutil.which("initdb")
    if w:
        cands.append(Path(w).parent)
    cands += [Path(p) for p in sorted(glob.glob("/opt/homebrew/opt/postgresql@*/bin"), reverse=True)]
    cands += [Path(p) for p in sorted(glob.glob("/usr/lib/postgresql/*/bin"), reverse=True)]
    for c in cands:
        if (c / "initdb").exists() and (c / "pg_ctl").exists():
            return c
    return None


@pytest.fixture(scope="module")
def pg():
    psycopg = pytest.importorskip("psycopg")
    binp = _find_pg_bin()
    if binp is None:
        pytest.skip("no PostgreSQL server binaries (initdb/pg_ctl) found; set PG_BIN")
    root = Path(tempfile.mkdtemp(prefix="samskarapg"))
    data = root / "data"
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    subprocess.run([str(binp / "initdb"), "-D", str(data), "-U", "postgres", "-A", "trust", "-E", "UTF8",
                    "--no-sync"], check=True, capture_output=True)
    opts = f"-p {port} -c listen_addresses=127.0.0.1 -c unix_socket_directories={root} -c fsync=off"
    subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-o", opts, "-w", "-l", str(root / "log"), "start"],
                   check=True, capture_output=True)
    try:
        yield psycopg, port
    finally:
        subprocess.run([str(binp / "pg_ctl"), "-D", str(data), "-m", "immediate", "stop"], capture_output=True)
        shutil.rmtree(root, ignore_errors=True)


_n = 0


@pytest.fixture()
def conn(pg):
    global _n
    _n += 1
    psycopg, port = pg
    name = f"s{_n}"
    with psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"CREATE DATABASE {name}")
    cn = psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname=name)
    try:
        cn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        cn.commit()
        dim = "vector(768)"
    except Exception:
        cn.rollback()
        cn.execute("CREATE DOMAIN vector AS text")     # byte-identical text round trip stand-in
        dim = "vector"
    cn.execute(f"""CREATE TABLE public.bodha_signal_embeddings (
        embedding_id uuid, signal_id text PRIMARY KEY, chart_id uuid, ayanamsha_id text, build_id uuid,
        embedding_vec {dim}, embedding_model text, embedding_model_version text,
        embedding_input_summary text, computed_at timestamptz)""")
    cn.commit()
    yield cn
    cn.close()
    with psycopg.connect(host="127.0.0.1", port=port, user="postgres", dbname="postgres", autocommit=True) as c:
        c.execute(f"DROP DATABASE IF EXISTS {name} WITH (FORCE)")


def _dump(cn):
    return cn.execute("SELECT embedding_id, signal_id, chart_id, ayanamsha_id, build_id, embedding_vec::text, "
                      "embedding_model, embedding_model_version, embedding_input_summary, computed_at "
                      "FROM public.bodha_signal_embeddings ORDER BY signal_id").fetchall()


def test_live_new_path_stores_exactly_what_the_old_per_row_path_stores(conn):
    rows = [_row(i) for i in range(1203)]
    assert mod._batch_insert(conn, rows) == 1203
    new = _dump(conn)
    conn.rollback()
    conn.execute("TRUNCATE public.bodha_signal_embeddings")
    with conn.cursor() as cur:                              # the old path
        for r in rows:
            cur.execute(mod._INSERT, r)
    old = _dump(conn)
    assert len(new) == 1203 and new == old


def test_live_reinsert_is_an_idempotent_upsert(conn):
    mod._batch_insert(conn, [_row(i) for i in range(600)])
    mod._batch_insert(conn, [_row(i, vec_seed=0.5) for i in range(600)])
    got = _dump(conn)
    assert len(got) == 600
    assert got[0][5] == _row(0, vec_seed=0.5)["embedding_vec"] or got[0][5].startswith("[0.5")


def test_live_bad_batch_falls_back_per_row_without_aborting_transaction(conn):
    rows = [_row(i) for i in range(10)]
    rows[3] = dict(rows[3], signal_id=rows[4]["signal_id"])   # duplicate key inside one statement
    n = mod._batch_insert(conn, rows)
    assert n == 10                                              # per-row upserts all succeed
    assert len(_dump(conn)) == 9
    conn.execute("SELECT 1")                                    # transaction still usable
