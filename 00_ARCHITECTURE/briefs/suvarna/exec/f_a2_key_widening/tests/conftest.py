"""Disposable local PostgreSQL (initdb into a temp dir on its own port; never the project database) holding a REPLAY of migration 1035
on production-shaped roles, owners and ACLs, plus the combined-executor loader and a runner.

The database is built from tests/schema/*.sql (roles; the 15 prerequisite tables as read from the live catalog; ownership/ACL state of the
protected-owner preflight; reference seeds) and the REAL platform/supabase/migrations/1035_data_plane_l1_producer_history.sql applied as
data_plane_migrator SET ROLE data_plane_l1_owner (the way the deployment-only runner applies it). The replayed L1 function manifest
(15 functions: md5, length, owner, secdef, config, ACL), the attestation row counts (15 / 23) and the capture-trigger digest are asserted
equal to the values read live as suvarna_reader on 2026-10-02 (test_replay_is_production_faithful).

Set PG_BIN to a bin directory (e.g. /opt/homebrew/opt/postgresql@17/bin) to test another major version. The executor connects as the role
`adm` (non-superuser CREATEROLE, no table privilege, no USAGE on schema public: Cloud SQL's postgres as read live; valid on PostgreSQL <= 15).
On PostgreSQL >= 16 CREATEROLE alone cannot grant, so run with DPFA2_TEST_ADMIN=postgres there.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import pathlib
import shutil
import socket
import sys
import subprocess
import tempfile
import uuid

import psycopg
import pytest

HERE = pathlib.Path(__file__).resolve().parent
EXEC_DIR = HERE.parent
REPO = EXEC_DIR.parents[4]
SCHEMA = HERE / "schema"
GATE_FIXTURE = HERE / "gate_fixture"
MIG_1035 = REPO / "platform/supabase/migrations/1035_data_plane_l1_producer_history.sql"
ADMIN_USER = os.environ.get("DPFA2_TEST_ADMIN", "adm")
COMMIT = "0123456789abcdef0123456789abcdef01234567"
L1_TABLES = ["chart_facts", "chart_dashas", "chart_divisionals", "ga_condition_composite", "ga_yoga_firings", "chart_vichara",
             "ga_transit_anchors", "l1_tajik_varsha_year_lords", "ga_medical", "ga_vastu_planet_direction_map", "ga_prashna_lagna",
             "ga_prashna_judgment"]
CHART = "aaaaaaaa-1111-4222-8333-000000000001"
BP = {"datetime_iso": "1991-07-19T06:20:00", "latitude_deg": 18.52, "longitude_deg": 73.86, "tz_offset_hours": 5.5,
      "place_name": "synthetic", "subject_label": "syn"}


def _bin(name):
    pb = os.environ.get("PG_BIN") or "/opt/homebrew/opt/postgresql@15/bin"
    p = os.path.join(pb, name)
    return p if os.path.exists(p) else shutil.which(name)


INITDB, PG_CTL, PSQL = _bin("initdb"), _bin("pg_ctl"), _bin("psql")
HAVE_PG = bool(INITDB and PG_CTL and PSQL)


def load_exec(name="d6_combined_exec"):
    spec = importlib.util.spec_from_file_location(name, EXEC_DIR / "d6_dataplane_capture_fa2_exec.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def fixture_pins() -> dict:
    return {n: hashlib.sha256((GATE_FIXTURE / n).read_bytes()).hexdigest() for n in ("prerun_gate.py", "run_gated.sh", "executor_standards.py")}


class Cluster:
    def __init__(self, port, sockdir, major):
        self.port, self.sockdir, self.major = port, sockdir, major

    def conn(self, db, user="postgres", autocommit=False):
        return psycopg.connect(host="127.0.0.1", port=self.port, dbname=db, user=user, autocommit=autocommit, connect_timeout=10)

    def su(self, db, sql, params=None, user="postgres"):
        with self.conn(db, user=user, autocommit=True) as c:
            cur = c.cursor()
            cur.execute(sql, params)
            return cur.fetchall() if cur.description else None

    def psql_file(self, db, path, user="postgres", preamble=""):
        sql = preamble + pathlib.Path(path).read_text()
        r = subprocess.run([PSQL, "-X", "-q", "-A", "-t", "-h", "127.0.0.1", "-p", str(self.port), "-U", user, "-d", db,
                            "-v", "ON_ERROR_STOP=1"], input=sql, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"psql {path} failed: {r.stderr[-800:]}")

    def new_db(self):
        name = "t" + uuid.uuid4().hex[:10]
        self.su("postgres", f"CREATE DATABASE {name} TEMPLATE tmpl")
        return name


@pytest.fixture(scope="session")
def cluster():
    if not HAVE_PG:
        pytest.skip("no local PostgreSQL binaries (set PG_BIN)")
    d = tempfile.mkdtemp(prefix="pgdp_")
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    subprocess.run([INITDB, "-D", d + "/data", "-A", "trust", "-U", "postgres", "-E", "UTF8"], check=True, capture_output=True)
    subprocess.run([PG_CTL, "-D", d + "/data", "-o", f"-p {port} -c listen_addresses=127.0.0.1 -c unix_socket_directories={d} "
                    "-c fsync=off -c full_page_writes=off -c max_connections=60", "-l", d + "/log", "-w", "start"],
                   check=True, capture_output=True)
    major = int(subprocess.run([PSQL, "-X", "-A", "-t", "-h", "127.0.0.1", "-p", str(port), "-U", "postgres", "-d", "postgres", "-c",
                                "SHOW server_version_num"], capture_output=True, text=True).stdout.strip()) // 10000
    cl = Cluster(port, d, major)
    try:
        cl.su("postgres", (SCHEMA / "00_roles.sql").read_text())
        cl.su("postgres", "CREATE DATABASE tmpl")
        cl.su("tmpl", 'CREATE EXTENSION pgcrypto; CREATE EXTENSION "uuid-ossp"')
        for f in ("01_prereq_tables", "02_simplified", "03_asset_registry_data", "03_fco_data", "04_acl_preflight",
                  "05_seed_fco_rehearsal", "06_seed_fco_sweep"):
            cl.psql_file("tmpl", SCHEMA / f"{f}.sql")
        cl.psql_file("tmpl", MIG_1035, user="data_plane_migrator", preamble="SET ROLE data_plane_l1_owner;\n")
        cl.psql_file("tmpl", SCHEMA / "07_l2_attestation_stubs.sql")
        cl.psql_file("tmpl", SCHEMA / "08_roles_and_chart.sql")
        cl.psql_file("tmpl", SCHEMA / "09_bg_shashtiamsha_deities.sql")
        yield cl
    finally:
        subprocess.run([PG_CTL, "-D", d + "/data", "-m", "immediate", "stop"], capture_output=True)
        shutil.rmtree(d, ignore_errors=True)


@pytest.fixture(scope="session")
def mod():
    m = load_exec()
    assert m.GATE_PINS == fixture_pins()     # the pins are BOUND (N-86); tests/gate_fixture holds the byte-identical rev3 gate files (PR #2938 head 7f0db55c3)

    def boom(*a, **k):
        raise AssertionError("a test reached the Secret Manager: tests inject a disposable connection and never fetch a credential")
    m.secret = boom
    m.fa2.secret = boom
    return m


@pytest.fixture(autouse=True)
def env(monkeypatch, tmp_path):
    monkeypatch.setenv("DPFA2_TEST_GATE_DIR", str(GATE_FIXTURE))
    monkeypatch.setenv("DPFA2_TEST_EVIDENCE_ROOT", str(tmp_path / "ev"))


@pytest.fixture()
def db(cluster):
    """A fresh disposable database. Migration 1255's grants are MODELLED here (schema/10): the executor refuses without them (STEP 0); tests/test_prereq_1255.py
    revokes them to prove the refusal. Production does not have them yet."""
    name = cluster.new_db()
    cluster.psql_file(name, SCHEMA / "10_migration_1255_model.sql")
    return name


def writer_runner(mod, tag=COMMIT, digest=None):
    digest = digest or mod.fa2.WRITER_DIGEST

    def run(argv):
        if argv[0] == "gcloud":
            return f"asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline:{tag}"
        if argv[0] == "git":
            return json.dumps({"writers": {"ga_vargas": digest}})
        raise AssertionError(argv)
    return run


class Runner:
    """Runs execute() against one disposable DB as the administrator role. `apply`/`rollback` first perform the matching dry run in the
    same state and pass its evidence digest (as an operator would)."""

    def __init__(self, cluster, mod, db, tmp_path):
        self.cl, self.m, self.db, self.tmp = cluster, mod, db, tmp_path
        self.n = 0

    def args(self, mode, expect_plan=None, expect_evidence=None, writer_commit=COMMIT):
        a = ["--" + mode, "--expect-plan", expect_plan or self.m.plan_hash()]
        if expect_evidence:
            a += ["--expect-evidence", expect_evidence]
        if writer_commit and mode in ("apply", "dry-run"):
            a += ["--writer-commit", writer_commit]
        return self.m.parse_args(a)

    def execute(self, args, runner=None, user=None, **kw):
        runner = runner or writer_runner(self.m)
        return self.m.execute(args, lambda: self.cl.conn(self.db, user=user or ADMIN_USER), gate_tables=L1_TABLES, writer_runner=runner, **kw)

    def run(self, mode, **kw):
        if mode in ("apply", "rollback") and not kw.get("expect_evidence"):
            dry = "dry-run" if mode == "apply" else "rollback-dry-run"
            _, d = self.execute(self.args(dry, **{k: v for k, v in kw.items() if k in ("writer_commit",)}))
            kw["expect_evidence"] = d.get("evidence_digest") or "0" * 64
        ek = {k: v for k, v in kw.items() if k not in ("runner", "user")}
        return self.execute(self.args(mode, **ek), runner=kw.get("runner"), user=kw.get("user"))

    # ------------------------------------------------------------------------------------------------ state images
    def state(self):
        """Everything the plan may or may not change, read as the superuser: the executor's own snapshot categories plus the function text,
        all attestation rows and the shape-defining catalogs."""
        with self.cl.conn(self.db, autocommit=False) as c:
            cur = c.cursor()
            cur.execute("SET LOCAL search_path = pg_catalog, public, pg_temp")
            snap = self.m.snap(cur)
            snap.pop("membership", None)
            cur.execute("SELECT pg_get_functiondef('public.l1_data_plane_capture_row()'::regprocedure)")
            fn = cur.fetchone()[0]
            cur.execute("SELECT md5(pg_get_functiondef(p.oid)) FROM pg_proc p WHERE p.oid='public.l1_data_plane_capture_row()'::regprocedure")
            md5 = cur.fetchone()[0]
            cur.execute("SELECT 'F', function_signature, definition_digest, owner_name, security_definer::text, coalesce(config::text,'') "
                        "FROM public.l1_data_plane_function_attestations UNION ALL SELECT 'T', table_name, trigger_name, trigger_type::text, "
                        "enabled::text, definition_digest FROM public.l1_data_plane_trigger_attestations ORDER BY 1,2,3")
            att = cur.fetchall()
            c.rollback()
        return {"snap": snap, "fn": fn, "md5": md5, "att": att}
