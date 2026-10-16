"""J-1a / #3140: execute the inert publication-guard draft on real PostgreSQL.

The draft stays outside the migration chain. Each case gets a guarded disposable
clone of the real migration schema; direct SQL bypasses all Python refusals.
These oracles catch the review's eight SQL mutations, including positive-path
regressions, without changing the draft or any applied migration.
"""
from pathlib import Path
import importlib.util
import json
import uuid

import psycopg
from psycopg import sql
from psycopg.conninfo import make_conninfo
from psycopg.types.json import Jsonb
import pytest

from .test_a53_inventory import CHART_ID, _boot, create_am5_database, drop_am5_database

ROOT = Path(__file__).resolve().parents[5]
DRAFT = ROOT / "00_ARCHITECTURE/briefs/pravaha/drafts/DRAFT_publication_refuses_test_slice_v1_0.sql"
CONSTRAINT = "kala_gochara_publication_no_published_test_slice"
GENERATION = "5.0"
MARKERS = [{"stored_scope": "test_slice"}, {"test_slice": {}},
           {"test_slice": None}, {"test_slice": False},
           {"stored_scope": "test_slice", "test_slice": {}}]


@pytest.fixture(scope="module")
def publication_template():
    admin, name, dsn = create_am5_database("j1aguard")
    try:
        yield admin, name, dsn
    finally:
        drop_am5_database(admin, name)


@pytest.fixture
def pre_guard_db(publication_template):
    admin, template, dsn = publication_template
    name = "ky_j1a_" + uuid.uuid4().hex[:12]
    admin.execute(sql.SQL("CREATE DATABASE {} TEMPLATE {}").format(sql.Identifier(name), sql.Identifier(template)))
    try:
        with psycopg.connect(make_conninfo(dsn, dbname=name), autocommit=True) as conn:
            yield conn
    finally:
        admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))


@pytest.fixture
def guard_db(pre_guard_db):
    pre_guard_db.execute(DRAFT.read_text())
    return pre_guard_db


def candidate(conn, vector):
    _boot(conn, GENERATION, vector=vector)
    # _boot uses a default for an empty mapping; pin the requested vector exactly.
    conn.execute("UPDATE kala_gochara_publication SET input_generation_vector = %s WHERE chart_id = %s AND generation = %s",
                 (Jsonb(vector), CHART_ID, GENERATION))


def manifest(conn):
    return conn.execute("SELECT status, input_generation_vector FROM kala_gochara_publication WHERE chart_id = %s AND generation = %s",
                        (CHART_ID, GENERATION)).fetchone()


@pytest.mark.parametrize("vector", MARKERS)
@pytest.mark.parametrize("replication_role", ["origin", "replica"])
def test_either_marker_refuses_direct_publication_even_in_replica_mode(guard_db, vector, replication_role):
    candidate(guard_db, vector)
    with guard_db.transaction():
        guard_db.execute("SELECT set_config('session_replication_role', %s, true)", (replication_role,))
        with pytest.raises(psycopg.errors.CheckViolation) as refused:
            with guard_db.transaction():
                guard_db.execute("UPDATE kala_gochara_publication SET status = 'published' WHERE chart_id = %s AND generation = %s",
                                 (CHART_ID, GENERATION))
        assert refused.value.diag.constraint_name == CONSTRAINT
        assert manifest(guard_db) == ("candidate", vector)


@pytest.mark.parametrize("status", ["published", "superseded", "rolled_back"])
def test_every_non_candidate_vector_is_frozen_but_unchanged_updates_work(guard_db, status):
    original = {"stored_scope": "stored_non_moon", "rule_registry": "r1"}
    candidate(guard_db, original)
    guard_db.execute("UPDATE kala_gochara_publication SET status = %s WHERE chart_id = %s AND generation = %s",
                     (status, CHART_ID, GENERATION))
    # An idempotent assignment must work even after leaving candidate.
    guard_db.execute("UPDATE kala_gochara_publication SET input_generation_vector = input_generation_vector WHERE chart_id = %s AND generation = %s",
                     (CHART_ID, GENERATION))
    with pytest.raises(psycopg.errors.CheckViolation, match="input vector.*immutable"):
        with guard_db.transaction():
            guard_db.execute("UPDATE kala_gochara_publication SET input_generation_vector = %s WHERE chart_id = %s AND generation = %s",
                             (Jsonb({**original, "rule_registry": "r2"}), CHART_ID, GENERATION))
    assert manifest(guard_db) == (status, original)


def test_candidate_vector_can_be_replaced_and_ordinary_manifest_published(guard_db):
    candidate(guard_db, {"stored_scope": "test_slice"})
    ordinary = {"stored_scope": "stored_non_moon", "rule_registry": "r2"}
    guard_db.execute("UPDATE kala_gochara_publication SET input_generation_vector = %s WHERE chart_id = %s AND generation = %s",
                     (Jsonb(ordinary), CHART_ID, GENERATION))
    guard_db.execute("UPDATE kala_gochara_publication SET status = 'published' WHERE chart_id = %s AND generation = %s",
                     (CHART_ID, GENERATION))
    assert manifest(guard_db) == ("published", ordinary)


@pytest.mark.parametrize("vector", [{}, {"stored_scope": "stored_non_moon"}])
def test_ordinary_publication_without_either_marker_remains_compatible(guard_db, vector):
    candidate(guard_db, vector)
    guard_db.execute("UPDATE kala_gochara_publication SET status = 'published' WHERE chart_id = %s AND generation = %s",
                     (CHART_ID, GENERATION))
    assert manifest(guard_db) == ("published", vector)


@pytest.mark.parametrize("vector", MARKERS[:2])
def test_existing_published_slice_is_rejected_when_draft_validates(pre_guard_db, vector):
    candidate(pre_guard_db, vector)
    pre_guard_db.execute("UPDATE kala_gochara_publication SET status = 'published' WHERE chart_id = %s AND generation = %s",
                         (CHART_ID, GENERATION))
    with pytest.raises(psycopg.errors.CheckViolation) as refused:
        try:
            pre_guard_db.execute(DRAFT.read_text())
        finally:
            pre_guard_db.rollback()
    assert refused.value.diag.constraint_name == CONSTRAINT
    assert manifest(pre_guard_db) == ("published", vector)


@pytest.fixture
def local_ky(pre_guard_db):
    from . import _runner_world as rw
    rw.apply_orchestrator_schema(pre_guard_db)
    pre_guard_db.execute((ROOT / "platform/migrations/436_build_substep_progress.sql").read_text())
    pre_guard_db.execute("CREATE TABLE IF NOT EXISTS public.kala_gochara_authority (chart_id uuid PRIMARY KEY, authoritative_generation text)")
    rw.seed_registry(pre_guard_db, {"ka_gochara_v5", "ga_positions", "ga_dashas"})
    return pre_guard_db


@pytest.mark.parametrize("argv", [
    ["--run", "one_class_full", "--classes", "marriage", "--dry-run"],
    ["--run", "all_classes_1y", "--classes", "all", "--horizon-start", "2025-04-17T00:00:00+00:00",
     "--horizon-end", "2026-04-17T00:00:00+00:00", "--dry-run"],
])
def test_launch_cli_dry_run_rolls_back_on_local_ky_without_claim_or_remote_call(local_ky, publication_template, tmp_path, monkeypatch, capsys, argv):
    path = ROOT / "00_ARCHITECTURE/briefs/kalayantra/fleet/smalltest_launch.py"
    spec = importlib.util.spec_from_file_location("j1a_launch_bridge", path)
    bridge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bridge)
    # ci-j1a / PR #3585: info.dsn redacts the password CI needs to reconnect.
    dsn = make_conninfo(publication_template[2], dbname=local_ky.info.dbname)
    monkeypatch.setenv("DATABASE_URL", dsn)
    monkeypatch.setenv("KY_ROOT", str(tmp_path))
    monkeypatch.delenv("KY_OPERATION_REQUEST", raising=False)
    monkeypatch.setattr(bridge, "launch_staged", lambda **kw: pytest.fail("dry run must never enter the launch path"))
    before = local_ky.execute("SELECT asset_id, state, rows_written FROM asset_throughput ORDER BY asset_id").fetchall()
    assert bridge.cli(argv) == 0
    streams = capsys.readouterr()
    report = json.loads(streams.out)
    assert report["asset_id"] == "ka_gochara_v5"
    assert report["plan_manifest"]["gochara_v5_test_slice"]["run"] == argv[1]
    assert "ROLLED BACK" in streams.err
    assert local_ky.execute("SELECT count(*) FROM build_runs").fetchone() == (0,)
    assert local_ky.execute("SELECT count(*) FROM build_run_assets").fetchone() == (0,)
    assert local_ky.execute("SELECT asset_id, state, rows_written FROM asset_throughput ORDER BY asset_id").fetchall() == before
    assert not list(tmp_path.rglob("*.json")), "a rehearsal must not claim a launch"
