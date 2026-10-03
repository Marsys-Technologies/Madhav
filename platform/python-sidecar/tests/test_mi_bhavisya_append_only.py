"""
mi_bhavisya is APPEND-ONLY on mimamsa_predictions / mimamsa_manifestation_sets (SS N-104,
an application of N-46; a documented exception to CLAUDE.md §N.3 delete-then-insert).

The ruling: calibration records are HISTORY, not rebuildable state.  A rebuild must

  * never DELETE a prediction row (pending, due, stale, frozen - any),
  * never UPDATE one (so emitted_at / frozen_bundle_hash / source_pramana_id keep their bytes),
  * INSERT a prediction only when none exists yet for the anchor (natural key, see the writer
    docstring: prediction_id = 'pred_<anchor>' OR source_pramana_id = '<anchor>', same chart).

The same discipline covers mimamsa_manifestation_sets (its citation_ref is where the original
freeze id of a migration-680-rewritten row survives).

TESTS BOTH WAYS
  1. A FAKE in-memory DB (always runs, no Postgres needed) executes the real writer and records
     every statement it issues.
  2. A DISPOSABLE local PostgreSQL cluster (initdb in a temp dir, unix socket only, started and
     stopped by this module; skipped when no PostgreSQL binaries are found, failure with
     REQUIRE_PG_BINARIES=1) runs the SAME scenarios through the real SQL against the production
     DDL shape (migration 347 + the later stale columns/constraints/trigger as read from the
     production catalog), additionally as a role holding ONLY SELECT+INSERT on the two tables.
  3. MUTATION PROOFS: the writer source is rewritten to reintroduce each defect (delete, re-stamp,
     weaker natural key, no prefilter, inflated count, ...) and every mutant must be caught by the
     scenarios.  Each mutation asserts that its target text exists exactly once, so a refactor of
     the writer cannot silently turn a mutant into a no-op.

Scenarios (each returns a list of VIOLATIONS; the real writer must produce none):
  existing  a rebuild over EXISTING rows (pending, due, confirmed, stale-marked, and a migration-680
            shape row whose prediction_id differs from 'pred_' || source_pramana_id): row count does
            not drop and every row's bytes (all columns) are unchanged; rows_inserted == 0.
  empty     an empty table receives the full set (a prediction and a manifestation set per anchor);
            a second run is a byte-identical no-op.
  moved     an anchor re-identified since the freeze: the old prediction and its set stay; one new of each is added.
  partial   with some natural keys absent, exactly those are inserted (plus their sets).
  notiming  anchors without a window / no anchors at all never delete anything.
  dry_run   writes nothing and reports exactly what a real run would add.
  race      (fake only) a row that appears between the read and the insert is NOT overwritten.
  audit     no executed statement is DELETE / UPDATE / TRUNCATE / DO UPDATE against these tables.
"""
from __future__ import annotations

import datetime as dt
import inspect
import json
import os
import re
import shutil
import socket
import subprocess
import tempfile
import types
import uuid
from pathlib import Path

import psycopg
import pytest
from psycopg import errors as pgerr

from pipeline.orchestrator.writers import ContextSpec, mi_bhavisya

_REPO = Path(__file__).resolve().parents[3]
WRITER_SRC = Path(inspect.getsourcefile(mi_bhavisya)).read_text(encoding="utf-8")
MIGRATION_347 = _REPO / "platform" / "migrations" / "347_mimamsa_bhavisya.sql"

CHART = "482012f1-710e-4a25-994a-93821f5871aa"
OTHER = "1c826d5a-41cb-4450-b4dc-59d440e5f75a"


def _u(n: int) -> str:
    return str(uuid.UUID(int=0xA11C0000000000000000000000000000 + n))


A = {i: _u(i) for i in range(1, 8)}  # anchor ids a1..a7
OLD4 = "pred_" + _u(900)  # the freeze-time id of the row whose anchor was re-pointed (migration 680 shape)

T_OLD = dt.datetime(2026, 8, 13, 1, 16, 29, tzinfo=dt.timezone.utc)
T_CREATED = dt.datetime(2026, 8, 13, 1, 16, 30, tzinfo=dt.timezone.utc)
STALE_AT = dt.datetime(2026, 9, 1, 0, 0, 0, tzinfo=dt.timezone.utc)


def anchor(i: int, chart: str = CHART, **kw) -> dict:
    d = {
        "anchor_id": A[i], "chart_id": chart, "domain": "career",
        "window_start": dt.date(2030, 1, i), "window_end": dt.date(2030, 6, i),
        "event_type": "career_entry", "direction": "amplified", "karmic_note": f"claim {i}",
        "magnitude": "minor", "confidence_low": 0.45, "confidence_high": 0.65,
        "falsifier": json.dumps({"id": i}),
    }
    d.update(kw)
    return d


# ======================================================================================
# Writer loading (real and mutated)
# ======================================================================================

def load_writer(src: str | None = None, name: str = "mi_bhavisya_mut"):
    """Return the writer CLASS: the real one, or one compiled from rewritten source."""
    if src is None:
        return mi_bhavisya.MiBhavisyaWriter
    src = src.replace('@register("mi_bhavisya")', "")  # a mutant must not touch the registry
    mod = types.ModuleType(f"pipeline.orchestrator.writers.{name}")
    mod.__file__ = f"<{name}>"
    exec(compile(src, f"<{name}>", "exec"), mod.__dict__)
    return mod.MiBhavisyaWriter


def mutate(old: str, new: str) -> str:
    assert WRITER_SRC.count(old) == 1, f"mutation target must occur exactly once: {old!r}"
    return WRITER_SRC.replace(old, new)


# ======================================================================================
# Backend 1: FAKE in-memory DB (executes the writer's real SQL strings by pattern)
# ======================================================================================

PRED_COLS = ["chart_id", "prediction_id", "source_pramana_id", "outcome_claim", "domain",
             "observation_window", "eval_date", "confidence_band", "magnitude_expected",
             "falsifier_jsonb", "base_rate", "emitted_at", "lifecycle_status", "driving_signals",
             "frozen_bundle_hash", "bundle_formula_version"]
MSET_COLS = ["chart_id", "prediction_id", "channel_id", "domain", "source", "citation_ref",
             "is_literal", "frozen_at"]


class FakeCursor:
    def __init__(self, db, row_factory=None):
        self.db, self.rf, self._rows, self.rowcount = db, row_factory, [], -1

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)

    def executemany(self, sql, seq):
        for p in seq:
            self.execute(sql, p)

    def execute(self, sql, params=None):
        db = self.db
        s = " ".join(sql.split())
        db.statements.append(s)
        params = tuple(params or ())
        self._rows, self.rowcount = [], -1
        if "FROM information_schema.tables" in s:
            self._rows = [(1,)] if params[0] in db.tables else []
        elif s.startswith("SELECT * FROM phala_anchors"):
            self._rows = [dict(a) for a in sorted(db.anchors, key=lambda a: a["anchor_id"])
                          if a["chart_id"] == params[0]]
        elif "FROM bodha_msr_signals" in s:
            self._rows = []
        elif s.startswith("SELECT prediction_id, source_pramana_id,") and "FROM mimamsa_predictions" in s:
            self._rows = [{"prediction_id": r["prediction_id"], "source_pramana_id": r["source_pramana_id"],
                           "is_stale": r.get("chart_context_stale_at") is not None}
                          for (c, _), r in sorted(db.preds.items()) if c == params[0]
                          and ("lifecycle_status IN ('pending', 'due')" not in s
                               or r["lifecycle_status"] in ("pending", "due"))]
            if db.after_existing_select:
                db.after_existing_select(db)
                db.after_existing_select = None
        elif s.startswith("DELETE FROM mimamsa_predictions"):
            keep_other = "lifecycle_status IN ('pending', 'due')" in s
            gone = [k for k, r in db.preds.items() if k[0] == params[0]
                    and (not keep_other or r["lifecycle_status"] in ("pending", "due"))]
            for k in gone:
                del db.preds[k]
            self.rowcount = len(gone)
        elif s.startswith("DELETE FROM mimamsa_manifestation_sets"):
            gone = [k for k in db.msets if k[0] == params[0]]
            for k in gone:
                del db.msets[k]
            self.rowcount = len(gone)
        elif s.startswith("UPDATE mimamsa_predictions"):
            n = 0
            for k, r in db.preds.items():
                if k[0] == params[-1]:
                    r["emitted_at"] = params[0]
                    n += 1
            self.rowcount = n
        elif s.startswith("UPDATE mimamsa_manifestation_sets"):
            n = 0
            for k, r in db.msets.items():
                if k[0] == params[-1]:
                    r["citation_ref"] = params[0]
                    n += 1
            self.rowcount = n
        elif s.startswith("INSERT INTO mimamsa_predictions"):
            self._insert(db.preds, PRED_COLS, params, (0, 1), s,
                         update_cols=("emitted_at", "frozen_bundle_hash"))
        elif s.startswith("INSERT INTO mimamsa_manifestation_sets"):
            self._insert(db.msets, MSET_COLS, params, (0, 1, 2), s, update_cols=())
        else:  # an unrecognised statement is a violation of the scenarios' closed world
            raise AssertionError(f"unexpected SQL in fake DB: {s[:140]}")

    def _insert(self, store, cols, params, keyidx, s, update_cols):
        row = dict(zip(cols, params))
        key = tuple(params[i] for i in keyidx)
        if key in store:
            if "ON CONFLICT" in s and "DO NOTHING" in s:
                self.rowcount = 0
                return
            if "DO UPDATE" in s:
                for c in update_cols:
                    store[key][c] = row[c]
                self.rowcount = 1
                return
            raise pgerr.UniqueViolation(f"duplicate key {key}")
        row.setdefault("created_at", T_CREATED)
        store[key] = row
        self.rowcount = 1


class FakeConn:
    def __init__(self):
        self.tables = {"phala_anchors", "bodha_msr_signals", "mimamsa_predictions"}
        self.anchors: list[dict] = []
        self.preds: dict[tuple, dict] = {}
        self.msets: dict[tuple, dict] = {}
        self.statements: list[str] = []
        self.after_existing_select = None
        self.commits = 0

    def cursor(self, row_factory=None):
        return FakeCursor(self, row_factory)

    def commit(self):  # the writer must NEVER call this; the harness does
        self.commits += 1

    def close(self):
        raise AssertionError("writer must not close ctx.db_conn")


class FakeBackend:
    kind = "fake"

    def __init__(self):
        self.conn = FakeConn()

    @property
    def statements(self):
        return self.conn.statements

    def set_anchors(self, anchors):
        self.conn.anchors = [dict(a) for a in anchors]

    def seed_pred(self, chart, pid, src, status="pending", stale=False, claim="old claim"):
        row = dict(zip(PRED_COLS, [chart, pid, src, claim, "career", "[2030-01-01,2030-06-01)",
                                   dt.date(2030, 6, 1), "[0.45,0.65)", "minor", "{}", None, T_OLD,
                                   status, "[]", "oldhash-" + pid, "mi_bhavisya_v1.0"]))
        row["created_at"] = T_CREATED
        row["chart_context_stale_at"] = STALE_AT if stale else None
        self.conn.preds[(chart, pid)] = row

    def seed_mset(self, chart, pid, cited_anchor):
        self.conn.msets[(chart, pid, "ch_career_verbal")] = dict(zip(MSET_COLS, [
            chart, pid, "ch_career_verbal", "career", "phala_anchors",
            json.dumps({"anchor_id": cited_anchor}), True, T_OLD]))

    def snapshot(self):
        return (sorted((k, tuple(sorted(r.items(), key=lambda kv: kv[0]))) for k, r in self.conn.preds.items()),
                sorted((k, tuple(sorted(r.items(), key=lambda kv: kv[0]))) for k, r in self.conn.msets.items()))

    def counts(self, chart=None):
        p = sum(1 for k in self.conn.preds if chart in (None, k[0]))
        m = sum(1 for k in self.conn.msets if chart in (None, k[0]))
        return p, m

    def keys(self, chart):
        return (sorted(k[1] for k in self.conn.preds if k[0] == chart),
                sorted(k[1] for k in self.conn.msets if k[0] == chart))

    def run(self, writer_cls, chart=CHART, dry_run=False):
        ctx = ContextSpec(asset_id="mi_bhavisya", build_id="b", db_conn=self.conn,
                          config={"chart_id": chart}, dry_run=dry_run)
        res = writer_cls().run(ctx)
        assert self.conn.commits == 0, "writer committed ctx.db_conn"
        return res

    def close(self):
        pass


# ======================================================================================
# Backend 2: DISPOSABLE PostgreSQL cluster
# ======================================================================================

SOCKDIR_ROOT = os.environ.get("SUVARNA_PG_SOCKDIR", tempfile.gettempdir())
VERSIONS = ["17", "15"]


def _bindir(version: str) -> Path | None:
    for cand in (os.environ.get(f"PG{version}_BIN"),
                 f"/opt/homebrew/opt/postgresql@{version}/bin",
                 f"/usr/local/opt/postgresql@{version}/bin",
                 f"/usr/lib/postgresql/{version}/bin"):
        if cand and (Path(cand) / "initdb").exists():
            return Path(cand)
    return None


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# Production shape beyond migration 347, read from the production catalog (reader role, 2026-10-03):
EXTRA_DDL = """
CREATE TABLE build_runs (id uuid PRIMARY KEY);
ALTER TABLE mimamsa_predictions
  ADD COLUMN contact_id text,
  ADD COLUMN chart_context_stale_at timestamptz,
  ADD COLUMN chart_context_stale_reason text,
  ADD COLUMN chart_context_superseded_by_run_id uuid REFERENCES build_runs(id) ON DELETE SET NULL,
  ADD CONSTRAINT mimamsa_predictions_stale_pair_check
      CHECK ((chart_context_stale_at IS NULL) = (chart_context_stale_reason IS NULL)),
  ADD CONSTRAINT mimamsa_predictions_stale_reason_check
      CHECK (chart_context_stale_reason IS NULL OR chart_context_stale_reason = 'chart_details_changed');
CREATE INDEX idx_mimamsa_predictions_chart_current ON mimamsa_predictions (chart_id)
  WHERE chart_context_stale_at IS NULL;
CREATE FUNCTION mimamsa_predictions_builder_guard() RETURNS trigger LANGUAGE plpgsql
  SET search_path TO 'pg_catalog', 'pg_temp' AS $f$
BEGIN
  IF current_user = 'data_plane_builder' OR session_user = 'data_plane_builder' THEN
    IF TG_OP = 'INSERT' THEN
      IF NEW.lifecycle_status IS NULL OR NEW.lifecycle_status NOT IN ('pending', 'due') THEN
        RAISE EXCEPTION 'builder may insert only pending/due' USING ERRCODE = '42501';
      END IF;
    ELSIF TG_OP = 'DELETE' THEN
      IF OLD.lifecycle_status IS NULL OR OLD.lifecycle_status NOT IN ('pending', 'due') THEN
        RAISE EXCEPTION 'builder may delete only pending/due' USING ERRCODE = '42501';
      END IF;
    END IF;
  END IF;
  IF TG_OP = 'DELETE' THEN RETURN OLD; END IF;
  RETURN NEW;
END $f$;
CREATE TRIGGER mimamsa_predictions_builder_guard BEFORE INSERT OR DELETE ON mimamsa_predictions
  FOR EACH ROW EXECUTE FUNCTION mimamsa_predictions_builder_guard();
CREATE TABLE phala_anchors (
  anchor_id uuid PRIMARY KEY, chart_id uuid NOT NULL, domain text, window_start date, window_end date,
  event_type text, direction text, karmic_note text, magnitude text,
  confidence_low numeric, confidence_high numeric, falsifier text);
CREATE TABLE bodha_msr_signals (
  signal_id uuid PRIMARY KEY, chart_id uuid NOT NULL, computed_salience numeric,
  domains_affected_array jsonb, signal_type_class text, source_subsystem text, source_l1_asset text);
"""


class Cluster:
    def __init__(self, version: str, bindir: Path):
        self.version, self.bindir = version, bindir
        self.data = tempfile.mkdtemp(prefix=f"mibpg{version}_")
        self.sock = tempfile.mkdtemp(prefix="p", dir=SOCKDIR_ROOT)
        self.port = _free_port()
        self.started = False
        self.n = 0

    def _run(self, exe, *args, timeout=120):
        subprocess.run([str(self.bindir / exe), *args], check=True, timeout=timeout,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    def start(self):
        self._run("initdb", "-D", self.data, "-U", "postgres", "--auth=trust", "-E", "UTF8", "--no-locale")
        opts = (f"-c listen_addresses='' -c unix_socket_directories={self.sock} -p {self.port} "
                "-c fsync=off -c max_connections=40 -c shared_buffers=16MB")
        self._run("pg_ctl", "-D", self.data, "-o", opts, "-w", "-t", "60", "-l",
                  os.path.join(self.data, "server.log"), "start")
        self.started = True
        with self.connect("postgres", "postgres", autocommit=True) as c:
            c.execute("CREATE ROLE data_plane_builder LOGIN NOINHERIT")

    def stop(self):
        try:
            if self.started:
                self._run("pg_ctl", "-D", self.data, "-m", "immediate", "-w", "-t", "60", "stop")
        finally:
            shutil.rmtree(self.data, ignore_errors=True)
            shutil.rmtree(self.sock, ignore_errors=True)

    def connect(self, db, user, autocommit=False):
        return psycopg.connect(host=self.sock, port=self.port, dbname=db, user=user,
                               autocommit=autocommit, connect_timeout=10)


@pytest.fixture(scope="module", params=VERSIONS)
def cluster(request):
    version = request.param
    bindir = _bindir(version)
    if bindir is None:
        if os.environ.get("REQUIRE_PG_BINARIES") == "1":
            pytest.fail(f"PostgreSQL {version} binaries not found and REQUIRE_PG_BINARIES=1")
        pytest.skip(f"PostgreSQL {version} binaries not found")
    cl = Cluster(version, bindir)
    try:
        cl.start()
        yield cl
    finally:
        cl.stop()


class PgBackend:
    kind = "pg"

    def __init__(self, cl: Cluster, as_builder: bool = False):
        cl.n += 1
        self.cl, self.db, self.as_builder = cl, f"t{cl.n}", as_builder
        with cl.connect("postgres", "postgres", autocommit=True) as c:
            c.execute(f"CREATE DATABASE {self.db} TEMPLATE template0")
        self.admin = cl.connect(self.db, "postgres", autocommit=True)
        self.admin.execute(MIGRATION_347.read_text(encoding="utf-8"))
        self.admin.execute(EXTRA_DDL)
        self.admin.execute("GRANT USAGE ON SCHEMA public TO data_plane_builder")
        self.admin.execute("GRANT SELECT ON phala_anchors, bodha_msr_signals TO data_plane_builder")
        self.admin.execute("GRANT SELECT, INSERT ON mimamsa_predictions, mimamsa_manifestation_sets "
                           "TO data_plane_builder")  # NO UPDATE, NO DELETE
        self.statements: list[str] = []
        self._conns: list[psycopg.Connection] = []

    # recording cursor: every statement the WRITER issues is captured
    def _factory(self):
        stmts = self.statements

        class Rec(psycopg.Cursor):
            def execute(self, query, params=None, **kw):
                stmts.append(" ".join(str(query).split()))
                return super().execute(query, params, **kw)

            def executemany(self, query, seq, **kw):
                stmts.append(" ".join(str(query).split()))
                return super().executemany(query, seq, **kw)

        return Rec

    def set_anchors(self, anchors):
        self.admin.execute("TRUNCATE phala_anchors")
        for a in anchors:
            self.admin.execute(
                "INSERT INTO phala_anchors VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                [a["anchor_id"], a["chart_id"], a["domain"], a["window_start"], a["window_end"],
                 a["event_type"], a["direction"], a["karmic_note"], a["magnitude"],
                 a["confidence_low"], a["confidence_high"], a["falsifier"]])
        self.admin.execute(
            "INSERT INTO bodha_msr_signals VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
            [_u(500), CHART, 3.0, json.dumps(["career"]), "yoga", "yoga", "ga_yogas"])

    def seed_pred(self, chart, pid, src, status="pending", stale=False, claim="old claim"):
        self.admin.execute(
            "INSERT INTO mimamsa_predictions (chart_id, prediction_id, source_pramana_id, outcome_claim, domain,"
            " observation_window, eval_date, confidence_band, magnitude_expected, falsifier_jsonb, base_rate,"
            " emitted_at, lifecycle_status, driving_signals, frozen_bundle_hash, bundle_formula_version,"
            " created_at, chart_context_stale_at, chart_context_stale_reason)"
            " VALUES (%s,%s,%s,%s,'career','[2030-01-01,2030-06-01)','2030-06-01','[0.45,0.65)','minor','{}',NULL,"
            " %s,%s,'[]',%s,'mi_bhavisya_v1.0',%s,%s,%s)",
            [chart, pid, src, claim, T_OLD, status, "oldhash-" + pid, T_CREATED,
             STALE_AT if stale else None, "chart_details_changed" if stale else None])

    def seed_mset(self, chart, pid, cited_anchor):
        self.admin.execute(
            "INSERT INTO mimamsa_manifestation_sets VALUES (%s,%s,'ch_career_verbal','career','phala_anchors',%s,true,%s)",
            [chart, pid, json.dumps({"anchor_id": cited_anchor}), T_OLD])

    def snapshot(self):
        p = [r[0] for r in self.admin.execute("SELECT t::text FROM mimamsa_predictions t ORDER BY 1").fetchall()]
        m = [r[0] for r in self.admin.execute("SELECT t::text FROM mimamsa_manifestation_sets t ORDER BY 1").fetchall()]
        return p, m

    def counts(self, chart=None):
        w, a = ("", []) if chart is None else (" WHERE chart_id = %s", [chart])
        return (self.admin.execute("SELECT count(*) FROM mimamsa_predictions" + w, a).fetchone()[0],
                self.admin.execute("SELECT count(*) FROM mimamsa_manifestation_sets" + w, a).fetchone()[0])

    def keys(self, chart):
        return ([r[0] for r in self.admin.execute(
                    "SELECT prediction_id FROM mimamsa_predictions WHERE chart_id=%s ORDER BY 1", [chart])],
                [r[0] for r in self.admin.execute(
                    "SELECT prediction_id FROM mimamsa_manifestation_sets WHERE chart_id=%s ORDER BY 1", [chart])])

    def run(self, writer_cls, chart=CHART, dry_run=False):
        conn = self.cl.connect(self.db, "data_plane_builder" if self.as_builder else "postgres",
                               autocommit=False)
        conn.cursor_factory = self._factory()
        self._conns.append(conn)
        ctx = ContextSpec(asset_id="mi_bhavisya", build_id="b", db_conn=conn,
                          config={"chart_id": chart}, dry_run=dry_run)
        try:
            res = writer_cls().run(ctx)
        except BaseException:
            conn.rollback()
            raise
        conn.commit()  # the orchestrator's commit, never the writer's
        return res

    def close(self):
        for c in self._conns:
            c.close()
        self.admin.close()


# ======================================================================================
# Scenarios
# ======================================================================================

_STMT_BAD = re.compile(r"^\s*(DELETE|UPDATE|TRUNCATE)\b", re.I)


def audit(be) -> list[str]:
    bad = []
    for s in be.statements:
        if _STMT_BAD.match(s) and re.search(r"mimamsa_(predictions|manifestation_sets)", s):
            bad.append(f"mutating statement against the frozen tables: {s[:90]}")
        if re.search(r"DO\s+UPDATE", s, re.I):
            bad.append(f"ON CONFLICT DO UPDATE (rewrite of an existing row): {s[:90]}")
        if re.match(r"\s*INSERT INTO mimamsa_(predictions|manifestation_sets)", s) and "DO NOTHING" not in s:
            bad.append(f"INSERT without ON CONFLICT DO NOTHING: {s[:90]}")
    return bad


def seed_existing(be):
    """Rows as production has them: pending, due, confirmed, stale-marked, and a 680-shape row."""
    be.set_anchors([anchor(i) for i in (1, 2, 3, 4, 5)])
    rows = [("pred_" + A[1], A[1], "pending", False),
            ("pred_" + A[2], A[2], "confirmed", False),
            ("pred_" + A[3], A[3], "due", False),
            (OLD4, A[4], "pending", False),          # migration 680: source_pramana_id is the NEW id
            ("pred_" + A[5], A[5], "pending", True)]  # stale-marked
    for pid, src, st, stale in rows:
        be.seed_pred(CHART, pid, src, status=st, stale=stale)
        be.seed_mset(CHART, pid, src if pid.startswith("pred_" + src) else _u(900))
    # an unrelated chart's pending row must be untouched as well
    be.seed_pred(OTHER, "pred_" + _u(77), _u(77))
    be.seed_mset(OTHER, "pred_" + _u(77), _u(77))


def sc_existing(be, w) -> list[str]:
    v = []
    seed_existing(be)
    before, n_before = be.snapshot(), be.counts()
    res = be.run(w)
    after, n_after = be.snapshot(), be.counts()
    if n_after[0] < n_before[0] or n_after[1] < n_before[1]:
        v.append(f"existing: row count dropped {n_before} -> {n_after}")
    if after != before:
        v.append("existing: bytes of existing rows changed or rows were added")
    if res.rows_inserted != 0:
        v.append(f"existing: rows_inserted={res.rows_inserted}, expected 0 for a no-op rebuild")
    if res.rows_skipped != 5:
        v.append(f"existing: rows_skipped={res.rows_skipped}, expected 5 already-frozen anchors")
    return v + audit(be)


def sc_empty(be, w) -> list[str]:
    v = []
    be.set_anchors([anchor(i) for i in (1, 2, 3, 4, 5)])
    res = be.run(w)
    if be.counts(CHART) != (5, 5):
        v.append(f"empty: expected 5 predictions + 5 sets, got {be.counts(CHART)}")
    if res.rows_inserted != 10:
        v.append(f"empty: rows_inserted={res.rows_inserted}, expected 10")
    pids, mids = be.keys(CHART)
    want = sorted("pred_" + A[i] for i in (1, 2, 3, 4, 5))
    if pids != want or mids != want:
        v.append("empty: wrong prediction/set keys")
    snap = be.snapshot()
    res2 = be.run(w)
    if be.snapshot() != snap:
        v.append("empty: second run changed bytes")
    if res2.rows_inserted != 0:
        v.append(f"empty: second run rows_inserted={res2.rows_inserted}, expected 0")
    return v + audit(be)


def sc_partial(be, w) -> list[str]:
    v = []
    be.set_anchors([anchor(i) for i in (1, 2, 3, 4, 5, 6)])
    be.seed_pred(CHART, "pred_" + A[1], A[1])             # present by prediction_id AND source
    be.seed_mset(CHART, "pred_" + A[1], A[1])
    be.seed_pred(CHART, "pred_" + A[6], A[7])             # present by prediction_id ONLY (source points elsewhere)
    be.seed_mset(CHART, "pred_" + A[6], A[7])
    be.seed_pred(CHART, OLD4, A[4], status="confirmed")   # present by source_pramana_id (680 shape)
    be.seed_mset(CHART, OLD4, _u(900))
    before = be.snapshot()
    res = be.run(w)
    pids, mids = be.keys(CHART)
    want_new = {"pred_" + A[2], "pred_" + A[3], "pred_" + A[5]}
    kept = {"pred_" + A[1], "pred_" + A[6], OLD4}
    if set(pids) != want_new | kept:
        v.append(f"partial: wrong predictions after run: {pids}")
    if set(mids) != want_new | kept:
        v.append(f"partial: wrong manifestation sets after run: {mids}")
    if res.rows_inserted != 6:
        v.append(f"partial: rows_inserted={res.rows_inserted}, expected 6")
    if res.rows_skipped != 3:
        v.append(f"partial: rows_skipped={res.rows_skipped}, expected 3 (a1 by key, a6 by prediction_id, a4 by source)")
    old_p = [r for r in before[0] if any(k in str(r) for k in kept)]
    new_p = be.snapshot()[0]
    if not all(r in new_p for r in old_p):
        v.append("partial: an existing row changed")
    return v + audit(be)


def sc_notiming(be, w) -> list[str]:
    v = []
    seed_existing(be)
    before = be.snapshot()
    be.set_anchors([anchor(i, window_start=None) for i in (1, 2, 3)])  # no timing -> skipped
    res = be.run(w)
    if be.snapshot() != before or res.rows_inserted != 0:
        v.append("notiming: anchors without a window altered or deleted existing rows")
    be.set_anchors([])
    res = be.run(w)
    if be.snapshot() != before or res.rows_inserted != 0:
        v.append("notiming: a chart with no anchors altered or deleted existing rows")
    return v + audit(be)


def sc_dry_run(be, w) -> list[str]:
    v = []
    be.set_anchors([anchor(i) for i in (1, 2, 3)])
    be.seed_pred(CHART, "pred_" + A[1], A[1])
    be.seed_mset(CHART, "pred_" + A[1], A[1])
    before = be.snapshot()
    n_stmts = len(be.statements)
    res = be.run(w, dry_run=True)
    if be.snapshot() != before:
        v.append("dry_run: wrote to the DB")
    if any(s.startswith(("INSERT", "DELETE", "UPDATE")) for s in be.statements[n_stmts:]):
        v.append("dry_run: issued a write statement")
    if res.rows_inserted != 4:
        v.append(f"dry_run: reported {res.rows_inserted}, a real run would add 4")
    real = be.run(w)
    if real.rows_inserted != 4:
        v.append(f"dry_run: real run then added {real.rows_inserted}, expected 4")
    return v + audit(be)


def sc_race(be, w) -> list[str]:
    """Fake only: another writer lands pred_a2 (with a different claim/stamp) between our read and our insert."""
    v = []
    be.set_anchors([anchor(i) for i in (1, 2)])

    def racer(db):
        db.preds[(CHART, "pred_" + A[2])] = dict(zip(PRED_COLS, [
            CHART, "pred_" + A[2], A[2], "RACER claim", "career", "x", dt.date(2030, 1, 1), "x", "x", "{}",
            None, T_OLD, "pending", "[]", "racerhash", "mi_bhavisya_v1.0"]), created_at=T_CREATED)

    be.conn.after_existing_select = racer
    res = be.run(w)
    if res.rows_inserted != 2:
        v.append(f"race: rows_inserted={res.rows_inserted}, expected 2 (a1's prediction + set; the raced a2 adds nothing)")
    if (CHART, "pred_" + A[2], "ch_career_verbal") in be.conn.msets:
        v.append("race: a manifestation set was inserted for a prediction whose insert conflicted")
    if (CHART, "pred_" + A[1]) not in be.conn.preds or (CHART, "pred_" + A[1], "ch_career_verbal") not in be.conn.msets:
        v.append("race: a1 was not frozen with its set")
    row = be.conn.preds[(CHART, "pred_" + A[2])]
    if row["outcome_claim"] != "RACER claim" or row["emitted_at"] != T_OLD or row["frozen_bundle_hash"] != "racerhash":
        v.append("race: a concurrently-inserted row was overwritten")
    return v + audit(be)


def sc_anchor_moved(be, w) -> list[str]:
    """An anchor whose id changed since the freeze (a new identity for the same event): the old prediction AND
    its manifestation set stay exactly as frozen (citation_ref still names the freeze-time anchor); the new
    anchor adds one new prediction + one new set."""
    v = []
    be.set_anchors([anchor(1)])
    be.seed_pred(CHART, "pred_" + A[1], A[1])
    be.seed_mset(CHART, "pred_" + A[1], A[1])
    be.set_anchors([anchor(6)])  # a1 is gone; a6 is the same event under a new identity
    before = be.snapshot()
    res = be.run(w)
    after = be.snapshot()
    if be.counts(CHART) != (2, 2):
        v.append(f"anchor_moved: expected 2 predictions + 2 sets (old kept, new added), got {be.counts(CHART)}")
    if res.rows_inserted != 2:
        v.append(f"anchor_moved: rows_inserted={res.rows_inserted}, expected 2")
    if not all(r in after[0] for r in before[0]) or not all(r in after[1] for r in before[1]):
        v.append("anchor_moved: the frozen prediction or its manifestation set changed")
    pids, mids = be.keys(CHART)
    if pids != sorted(["pred_" + A[1], "pred_" + A[6]]) or mids != pids:
        v.append("anchor_moved: wrong prediction/set keys")
    return v + audit(be)


CORE = [sc_existing, sc_empty, sc_partial, sc_notiming, sc_dry_run, sc_anchor_moved]


def run_scenarios(make_backend, w, scenarios=CORE) -> list[str]:
    v = []
    for sc in scenarios:
        be = make_backend()
        try:
            v += sc(be, w)
        except BaseException as exc:  # a crash is a violation, not a pass
            v.append(f"{sc.__name__}: raised {type(exc).__name__}: {str(exc)[:100]}")
        finally:
            be.close()
    return v


# ======================================================================================
# Mutants
# ======================================================================================

MUTANTS = {
    "reintroduce_prediction_delete": mutate(
        "        preds_inserted = 0\n",
        "        with conn.cursor() as _c:\n            _c.execute(\"DELETE FROM mimamsa_predictions WHERE chart_id = %s AND "
        "lifecycle_status IN ('pending', 'due')\", (chart_id,))\n        preds_inserted = 0\n"),
    "reintroduce_unscoped_prediction_delete": mutate(
        "        preds_inserted = 0\n",
        "        with conn.cursor() as _c:\n            _c.execute(\"DELETE FROM mimamsa_predictions WHERE chart_id = %s\", (chart_id,))\n"
        "        preds_inserted = 0\n"),
    "reintroduce_manifestation_delete": mutate(
        "        preds_inserted = 0\n",
        "        with conn.cursor() as _c:\n            _c.execute(\"DELETE FROM mimamsa_manifestation_sets WHERE chart_id = %s\", (chart_id,))\n"
        "        preds_inserted = 0\n"),
    "restamp_emitted_at_update": mutate(
        "        logger.info(\n            \"[mi_bhavisya] froze",
        "        with conn.cursor() as _c:\n            _c.execute(\"UPDATE mimamsa_predictions SET emitted_at = %s WHERE chart_id = %s\", "
        "(emitted_at, chart_id))\n        logger.info(\n            \"[mi_bhavisya] froze"),
    "restamp_hash_update": mutate(
        "        logger.info(\n            \"[mi_bhavisya] froze",
        "        with conn.cursor() as _c:\n            _c.execute(\"UPDATE mimamsa_predictions SET frozen_bundle_hash = 'x' WHERE chart_id = %s\", "
        "(chart_id,))\n        logger.info(\n            \"[mi_bhavisya] froze"),
    "natural_key_pk_only": mutate(
        "if prediction_id in frozen_prediction_ids or anchor_id in frozen_anchor_refs:",
        "if prediction_id in frozen_prediction_ids:"),
    "natural_key_source_only": mutate(
        "if prediction_id in frozen_prediction_ids or anchor_id in frozen_anchor_refs:",
        "if anchor_id in frozen_anchor_refs:"),
    "no_existing_check": mutate(
        "if prediction_id in frozen_prediction_ids or anchor_id in frozen_anchor_refs:", "if False:"),
    "on_conflict_do_update_restamp": mutate(
        "            ON CONFLICT (chart_id, prediction_id) DO NOTHING\n",
        "            ON CONFLICT (chart_id, prediction_id) DO UPDATE SET emitted_at = EXCLUDED.emitted_at,"
        " frozen_bundle_hash = EXCLUDED.frozen_bundle_hash\n"),
    "no_on_conflict_clause": mutate(
        "            ON CONFLICT (chart_id, prediction_id) DO NOTHING\n", ""),
    "count_planned_not_inserted": mutate(
        "            rows_inserted=preds_inserted + msets_inserted,\n            rows_skipped",
        "            rows_inserted=len(pred_rows) + len(mset_rows),\n            rows_skipped"),
    "dry_run_writes": mutate("        if ctx.dry_run:\n", "        if False:\n"),
    "sets_for_skipped_predictions": mutate(
        "        new_mset_rows = [m for m in mset_rows if m[1] in new_pred_ids]",
        "        new_mset_rows = list(mset_rows)\n"
        "        with conn.cursor() as _c:\n"
        "            for _m in new_mset_rows:\n"
        "                _c.execute(\"INSERT INTO mimamsa_manifestation_sets (chart_id, prediction_id, channel_id, domain, source,"
        " citation_ref, is_literal, frozen_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (chart_id, prediction_id, channel_id)"
        " DO NOTHING\", _m)"),
    "restamp_set_citation_ref_update": mutate(
        "        logger.info(\n            \"[mi_bhavisya] froze",
        "        with conn.cursor() as _c:\n            _c.execute(\"UPDATE mimamsa_manifestation_sets SET citation_ref = %s "
        "WHERE chart_id = %s\", ('{}', chart_id))\n        logger.info(\n            \"[mi_bhavisya] froze"),
    "set_insert_do_update": mutate(
        "            ON CONFLICT (chart_id, prediction_id, channel_id) DO NOTHING\n",
        "            ON CONFLICT (chart_id, prediction_id, channel_id) DO UPDATE SET citation_ref = EXCLUDED.citation_ref,"
        " frozen_at = EXCLUDED.frozen_at\n"),
    # NIT-2 (review of #3040): the set-only-for-an-inserted-prediction guard, and "frozen = every status"
    "set_inserted_when_prediction_conflicted": mutate(
        "                if cur.rowcount == 1:\n                    preds_inserted += 1\n",
        "                if True:\n                    preds_inserted += 1\n"),
    "frozen_means_pending_or_due_only": mutate(
        "\"FROM mimamsa_predictions WHERE chart_id = %s\",",
        "\"FROM mimamsa_predictions WHERE chart_id = %s AND lifecycle_status IN ('pending', 'due')\","),
    "commits_the_connection": mutate(
        "        logger.info(\n            \"[mi_bhavisya] froze",
        "        conn.commit()\n        logger.info(\n            \"[mi_bhavisya] froze"),
}
# a commit by the writer is observable on the fake connection only (PG sees it as the orchestrator's commit)
FAKE_ONLY = {"commits_the_connection", "set_inserted_when_prediction_conflicted"}


# ======================================================================================
# Tests
# ======================================================================================

def test_static_the_writer_never_mentions_a_mutating_statement_on_the_frozen_tables():
    src = inspect.getsource(mi_bhavisya.MiBhavisyaWriter.run)
    code = "\n".join(l for l in src.splitlines() if not l.strip().startswith("#"))
    assert not re.search(r"\bDELETE\b", code), "run() must not DELETE (SS N-104)"
    assert not re.search(r"\bUPDATE\b", code.replace("DO UPDATE", "DO_UPDATE")), "run() must not UPDATE (SS N-104)"
    assert not re.search(r"DO\s+UPDATE", code)
    assert not re.search(r"\bTRUNCATE\b", code)
    assert code.count("DO NOTHING") == 2, "both inserts must be ON CONFLICT DO NOTHING"
    assert "outcome_observed" not in code and "brier_score" not in code


def test_exception_to_n3_is_documented_in_the_writer():
    doc = mi_bhavisya.__doc__
    assert "N-104" in doc and "§N.3" in doc and "APPEND-ONLY" in doc
    assert "DELETE FROM mimamsa_predictions WHERE chart_id" not in doc


def test_writer_is_still_a_frozen_contract_writer():
    from pipeline.orchestrator.writers import WriterBase, get_writer
    assert get_writer("mi_bhavisya") is mi_bhavisya.MiBhavisyaWriter
    assert issubclass(mi_bhavisya.MiBhavisyaWriter, WriterBase)
    src = inspect.getsource(mi_bhavisya)
    assert "asset_throughput" not in src and ".commit(" not in src and ".close(" not in src


# ---- fake backend ----------------------------------------------------------------------

def test_fake_real_writer_has_no_violations():
    assert run_scenarios(FakeBackend, load_writer(), CORE + [sc_race]) == []


@pytest.mark.parametrize("name", sorted(MUTANTS))
def test_fake_every_mutant_is_caught(name):
    scenarios = CORE + [sc_race]
    v = run_scenarios(FakeBackend, load_writer(MUTANTS[name], name), scenarios)
    assert v, f"mutant {name} survived the fake-DB scenarios"


def test_fake_audit_itself_flags_a_delete():
    be = FakeBackend()
    be.statements.append("DELETE FROM mimamsa_predictions WHERE chart_id = %s")
    assert audit(be)


# ---- real SQL on a disposable PostgreSQL ------------------------------------------------

def test_pg_real_writer_has_no_violations(cluster):
    assert run_scenarios(lambda: PgBackend(cluster), load_writer()) == []


def test_pg_real_writer_needs_only_select_and_insert(cluster):
    """The build role holds SELECT+INSERT only (no UPDATE, no DELETE): the writer works with exactly that."""
    assert run_scenarios(lambda: PgBackend(cluster, as_builder=True), load_writer()) == []


def test_pg_table_shape_is_the_production_shape(cluster):
    be = PgBackend(cluster)
    try:
        idx = be.admin.execute("SELECT indexdef FROM pg_indexes WHERE tablename='mimamsa_predictions' "
                               "AND indexdef LIKE 'CREATE UNIQUE%'").fetchall()
        assert len(idx) == 1 and "(chart_id, prediction_id)" in idx[0][0], idx
        cons = {r[0] for r in be.admin.execute(
            "SELECT conname FROM pg_constraint WHERE conrelid='mimamsa_predictions'::regclass").fetchall()}
        assert {"mimamsa_predictions_pkey", "mimamsa_predictions_stale_pair_check"} <= cons
    finally:
        be.close()


STALENESS_TS = _REPO / "platform" / "src" / "lib" / "charts" / "chartContextStaleness.ts"


def _staleness_update_sql(ts_source: str) -> str:
    """The real UPDATE template a strict birth-detail correction runs on mimamsa_predictions
    (chartContextStaleness.ts), turned into psycopg parameters ($1 -> chart, $2 -> run)."""
    m = re.search(r"sql: `(UPDATE \$\{table\}.*?)`", ts_source, re.S)
    assert m, "stale-marker UPDATE template not found in chartContextStaleness.ts"
    return m.group(1).replace("${table}", "mimamsa_predictions").replace("$1", "%(chart)s").replace("$2", "%(run)s")


def _strict_correction_scenario(be, update_sql: str) -> list[str]:
    """A strict correction must leave every prediction (pending / due / confirmed) and every
    manifestation set in place, setting only the staleness marker pair + the superseding run."""
    v = []
    seed_existing(be)
    be.admin.execute("INSERT INTO build_runs VALUES (%s)", [_u(950)])
    before_rows = be.admin.execute(
        "SELECT chart_id, prediction_id, source_pramana_id, outcome_claim, domain, observation_window, eval_date,"
        " confidence_band, magnitude_expected, falsifier_jsonb, base_rate, emitted_at, lifecycle_status, driving_signals,"
        " frozen_bundle_hash, bundle_formula_version, created_at, contact_id FROM mimamsa_predictions"
        " WHERE chart_id = %s ORDER BY prediction_id", [CHART]).fetchall()
    sets_before = be.snapshot()[1]
    already = be.admin.execute(
        "SELECT prediction_id, chart_context_stale_at FROM mimamsa_predictions WHERE chart_id=%s AND chart_context_stale_at IS NOT NULL",
        [CHART]).fetchall()
    be.admin.execute(update_sql, {"chart": CHART, "run": _u(950)})
    after_rows = be.admin.execute(
        "SELECT chart_id, prediction_id, source_pramana_id, outcome_claim, domain, observation_window, eval_date,"
        " confidence_band, magnitude_expected, falsifier_jsonb, base_rate, emitted_at, lifecycle_status, driving_signals,"
        " frozen_bundle_hash, bundle_formula_version, created_at, contact_id FROM mimamsa_predictions"
        " WHERE chart_id = %s ORDER BY prediction_id", [CHART]).fetchall()
    if after_rows != before_rows:
        v.append("strict correction: a prediction row changed beyond the staleness columns (or was deleted)")
    if be.snapshot()[1] != sets_before:
        v.append("strict correction: manifestation sets changed")
    marked = be.admin.execute(
        "SELECT count(*) FILTER (WHERE chart_context_stale_at IS NOT NULL AND chart_context_stale_reason = 'chart_details_changed'"
        " AND chart_context_superseded_by_run_id = %s), count(*) FROM mimamsa_predictions WHERE chart_id=%s",
        [_u(950), CHART]).fetchone()
    # one row was already stale-marked at seed time (set once: untouched, so it has no superseding run)
    if marked != (len(before_rows) - len(already), len(before_rows)):
        v.append(f"strict correction: expected every not-yet-stale row marked with the run, got {marked}")
    other = be.admin.execute("SELECT count(*) FROM mimamsa_predictions WHERE chart_id=%s AND chart_context_stale_at IS NOT NULL", [OTHER]).fetchone()[0]
    if other != 0:
        v.append("strict correction: another chart's prediction was marked")
    stale_before = be.admin.execute(
        "SELECT prediction_id, chart_context_stale_at FROM mimamsa_predictions WHERE chart_id=%s AND chart_context_stale_at IS NOT NULL ORDER BY 1", [CHART]).fetchall()
    be.admin.execute(update_sql, {"chart": CHART, "run": _u(950)})
    if be.admin.execute(
        "SELECT prediction_id, chart_context_stale_at FROM mimamsa_predictions WHERE chart_id=%s AND chart_context_stale_at IS NOT NULL ORDER BY 1", [CHART]).fetchall() != stale_before:
        v.append("strict correction: a second correction re-stamped an already-marked row (the marker must be set once)")
    return v


def test_pg_strict_birth_detail_correction_leaves_predictions_undeleted_with_marker_and_run_set(cluster):
    be = PgBackend(cluster)
    try:
        assert _strict_correction_scenario(be, _staleness_update_sql(STALENESS_TS.read_text(encoding="utf-8"))) == []
    finally:
        be.close()


@pytest.mark.parametrize("name,old,new", [
    ("also_rewrites_status", "SET chart_context_stale_at = NOW(),", "SET lifecycle_status = 'expired', chart_context_stale_at = NOW(),"),
    ("restamps_marked_rows", "AND chart_context_stale_at IS NULL", "AND true"),
])
def test_pg_strict_correction_mutants_are_caught(cluster, name, old, new):
    src = STALENESS_TS.read_text(encoding="utf-8")
    assert src.count(old) == 1, old
    be = PgBackend(cluster)
    try:
        assert _strict_correction_scenario(be, _staleness_update_sql(src.replace(old, new))), f"mutant {name} survived"
    finally:
        be.close()


def test_pg_the_old_writer_behaviour_is_what_the_ruling_forbids(cluster):
    """Control: the PRE-CHANGE writer deletes every pending row on a no-op rebuild (the 139-row hazard)."""
    be = PgBackend(cluster)
    try:
        seed_existing(be)
        n = be.counts(CHART)[0]
        be.admin.execute("DELETE FROM mimamsa_predictions WHERE chart_id=%s AND lifecycle_status IN ('pending','due')",
                         [CHART])
        assert be.counts(CHART)[0] < n
    finally:
        be.close()


@pytest.mark.parametrize("name", sorted(set(MUTANTS) - FAKE_ONLY))
def test_pg_every_mutant_is_caught(cluster, name):
    v = run_scenarios(lambda: PgBackend(cluster), load_writer(MUTANTS[name], name))
    assert v, f"mutant {name} survived the PostgreSQL scenarios"


@pytest.mark.parametrize("name", ["reintroduce_prediction_delete", "restamp_emitted_at_update"])
def test_pg_builder_role_privileges_independently_refuse_the_mutants(cluster, name):
    """Belt: with only SELECT+INSERT granted, the mutants that DELETE/UPDATE cannot even run."""
    be = PgBackend(cluster, as_builder=True)
    try:
        seed_existing(be)
        with pytest.raises(pgerr.InsufficientPrivilege):
            be.run(load_writer(MUTANTS[name], name))
    finally:
        be.close()
