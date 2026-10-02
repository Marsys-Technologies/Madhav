"""C15 (steward M20261002T040828-9e76) — the ka_gochara_v4_41_candidate
writer's database statements, exercised AS the production builder role.

The '4.1' candidate writer (pipeline/orchestrator/writers/
ka_gochara_v4_41_candidate.py, merged in #2799) will soon run in production
as data_plane_builder. Four production builds failed on 2026-10-01 on
privileges that superuser-connected suites never exercised, so this suite
drives the writer's SQL layer through an AUTHENTICATED data_plane_builder
connection on the production power structure built by the shared fixture
(tests/l3/_builder_role.py — the disposable guard refuses any other target):
schema public owned by a NOLOGIN `amjis_app` with the governed bootstrap's
default-privilege revocations in force, the builder holding only what the
REAL checked-in grant migrations (1211, 1216, 1217, 1220, 1225, 1231) give
it, applied verbatim as the owner.

THE WRITER'S DB SURFACE (read from the writer + its step06 chain, never
re-implemented here): the full chain needs a Swiss ephemeris run, so per the
task this suite drives the SQL-layer functions directly with minimal literal
rows — the PRODUCTION functions, imported by path exactly as the writer
imports them:

  manifest substep  — ledger.register_convention (INSERT
                      kala_gochara_convention) + ledger.publish_candidate
                      (INSERT/UPDATE kala_gochara_publication);
  body:<Body>       — ledger.write_contacts (DELETE+INSERT
                      kala_gochara_contacts, body-scoped) +
                      ledger.write_coverage (DELETE+INSERT
                      kala_gochara_coverage, body-partition-scoped);
  windows           — step06b_windows_projection.write_windows (DELETE+INSERT
                      kala_gochara_windows scoped chart × '4.1') +
                      update_manifest_windows_count (UPDATE
                      kala_gochara_publication.row_counts).
  The writer NEVER writes asset_throughput (frozen contract §N.2) and never
  touches kala_gochara_authority (only the step08 flip writes it).

SCHEMA: the REAL migration files that create the touched tables, applied
verbatim AS amjis_app — 460 (kala_gochara_windows), 527 (+ generation,
kala_gochara_authority), 540 (build_protected_assets, referenced by 556),
541 (kala_gochara_v2_build_state, referenced by 542), 542
(kala_gochara_windows_v2, ALTERed by 567/568), 556 (era_slice_key),
567/568 (parent_window_id + resolution + the 7-key natural index), 1081
(kala_gochara_convention / publication / contacts / coverage) and 1087
(inclusivity / completeness / tier_basis on contacts). The grant-target
schema the seven grant migrations post-check against is built by the C7
suite's own _build_schema_as_owner, reused verbatim.

What it proves (each assertion measures the claim it names):
  1. CONTROL — the mirror is faithful: schema public is owned by amjis_app,
     the builder holds NO CREATE on it, and the seven real grant migrations
     applied.
  2. WRITE PATH — the manifest substep (register_convention,
     publish_candidate), the body-substep writes (write_contacts,
     write_coverage) AND the windows substep (write_windows' scoped
     delete-then-insert on kala_gochara_windows + the manifest count stamp)
     all succeed as the builder — the windows ACL that was C15's
     strict-xfail FINDING is now recorded by grant migration 1237
     (Pravāha C16).
  3. FORBIDDEN — the builder is refused on kala_gochara_authority (the flip
     surface the writer must never touch), and ledger writes against a
     PUBLISHED generation are refused (the candidate-only rail).
  4. IDEMPOTENT — the seven grant migrations re-apply as a no-op.

Requires a THROWAWAY database; skipped unless C7_BUILDER_ROLE_TEST_DATABASE_URL
is set (same disposable identity as the C7 suite):

  createdb -h 127.0.0.1 -p 55432 -U postgres c7_builder_role_test
  C7_BUILDER_ROLE_TEST_DATABASE_URL=postgresql://postgres@127.0.0.1:55432/c7_builder_role_test \
    python -m pytest tests/l3/test_builder_role_v4_41_candidate.py -q
"""
from __future__ import annotations

import importlib.util
import os
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

SIDECAR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SIDECAR))
sys.path.insert(0, str(SIDECAR / "scripts" / "kala_gochara_cutover"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import _builder_role as BR  # noqa: E402


def _load(path: Path, name: str):
    """Import-by-path — the writer's own idiom (scripts/ is not a package)."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


ledger = _load(SIDECAR / "services" / "gochara_kernel" / "ledger.py", "c15_ledger")
step06_build = _load(
    SIDECAR / "scripts" / "kala_gochara_cutover" / "step06_candidate_build.py",
    "c15_step06_build")
step06b = _load(
    SIDECAR / "scripts" / "kala_gochara_cutover" / "step06b_windows_projection.py",
    "c15_step06b")

DSN = os.environ.get("C7_BUILDER_ROLE_TEST_DATABASE_URL")

pytestmark = pytest.mark.skipif(not DSN, reason="NOT_RUN: set C7_BUILDER_ROLE_TEST_DATABASE_URL to the disposable Postgres")

# The writer's pinned A2.5 candidate chart and fixed generation.
CHART = "482012f1-710e-4a25-994a-93821f5871aa"
CHART_B = "00000000-0000-4000-8000-0000000000b5"  # isolation for the published-refusal test
GENERATION = "4.1"
HORIZON_TEXT = "[1998-01-01 00:00:00+00,2026-04-18 00:00:00+00)"

# The real migration files creating every table the writer's SQL layer
# touches, in dependency order, located by prefix under the two migration
# roots (the fixture raises if any prefix is absent or ambiguous). 1081 (the
# ledger tables) is already applied by the C7 grant-target schema build
# below and re-applies harmlessly (every statement is IF NOT EXISTS).
SCHEMA_MIGRATION_PREFIXES = ("460", "527", "540", "541", "542", "556", "567", "568", "1081", "1087")


def _apply_schema_as_owner(conn) -> dict:
    # The grant migrations post-check has_table_privilege on their targets,
    # so the ENTIRE C7 grant-target schema must exist — the C7 suite's own
    # builder (the rehearsal-derived resonance schema + the grant-target DDL
    # extracted statement-by-statement + the 1153-1157 contract DDL + 1081),
    # reused verbatim rather than re-derived.
    import test_builder_role_resonance_writer as C7

    applied = {"c7_grant_target_schema": C7._build_schema_as_owner(conn),
               "windows_chain": []}
    with BR.as_owner(conn):
        # Stub: 460/541's trailing registration INSERTs reference
        # asset_registry. The rehearsal schema already creates it with most
        # columns; top up the three the 460/541 DML also names. The writer's
        # SQL layer never touches this table.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS public.asset_registry (
              asset_id TEXT PRIMARY KEY,
              layer TEXT, sort_order INTEGER,
              sanskrit_name TEXT, english_name TEXT, english_description TEXT,
              storage_type TEXT, target_table TEXT, count_sql TEXT, size_sql TEXT,
              target_floor INTEGER, scope TEXT,
              is_active BOOLEAN, has_writer BOOLEAN, has_substeps BOOLEAN,
              writer_timeout_seconds INTEGER,
              layer_name TEXT, layer_index TEXT, catalog_status TEXT,
              depends_on TEXT[])""")
        conn.execute("""
            ALTER TABLE public.asset_registry
              ADD COLUMN IF NOT EXISTS has_substeps BOOLEAN,
              ADD COLUMN IF NOT EXISTS writer_timeout_seconds INTEGER,
              ADD COLUMN IF NOT EXISTS depends_on TEXT[]""")
        for prefix in SCHEMA_MIGRATION_PREFIXES:
            path = BR._find_migration(prefix)
            conn.execute(path.read_text())
            applied["windows_chain"].append(path.name)
    return applied


@pytest.fixture(scope="module")
def builder_world():
    import psycopg

    BR.require_disposable(DSN)
    admin = psycopg.connect(DSN, autocommit=True, connect_timeout=5)
    try:
        BR.provision(admin)
        applied = _apply_schema_as_owner(admin)
        applied["grant_migrations"] = BR.apply_grant_migrations(admin)
        yield {"admin": admin, "applied": applied}
    finally:
        try:
            admin.execute("DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;")
            for role in (BR.BUILDER_ROLE, BR.OWNER_ROLE):
                admin.execute(f"DROP OWNED BY {role} CASCADE")
        finally:
            admin.close()


# ── Minimal literal rows for the production SQL-layer functions ──────────────

def _manifest(conn, chart_id: str) -> tuple[str, str]:
    """The manifest substep's two production calls; returns (convention_id,
    manifest_id)."""
    cid = ledger.register_convention(
        conn, step06_build.CONVENTION_VECTOR,
        {"ephemeris_backend": "swieph", "retflag": 258})
    mid = ledger.publish_candidate(
        conn, chart_id, GENERATION, cid,
        dict(step06_build.GENERATION_VECTOR_FLAGS),
        {"backend": "swieph", "retflag": 258}, HORIZON_TEXT,
        writer_asset_id="ka_gochara_v4_41_candidate")
    return cid, mid


def _episode() -> dict:
    tz = timezone.utc
    return {
        "independence_group": "c15-ig-1",
        "body": "Saturn",
        "relation": "conjunction",
        "target_type": "karaka",
        "target_ref": "Saturn",
        "target_resolution_state": "resolved",
        "t_in": datetime(2020, 1, 10, tzinfo=tz),
        "t_exact": datetime(2020, 1, 15, tzinfo=tz),
        "t_out": datetime(2020, 1, 20, tzinfo=tz),
        "bracket_seconds": 864000,
        "tolerance_arcsec": 1.0,
        "branch": "direct",
        "orb_max_deg": 5.0,
        "orb_source": "c15_fixture_orb",
        "epistemic_class": "observed",
        "completeness_state": "applied",
        "operator_role": "testimony",
        "precision_regime": "exact",
        "time_basis": "event_time_utc",
        "comparable_with": "self",
        "ephemeris_backend": {"backend": "swieph", "retflag": 258},
    }


def _partition() -> dict:
    return {
        "partition_kind": "body_target",
        "partition_key": "Saturn:karaka",
        "requested_horizon": "[1998-01-01 00:00:00+00,2026-04-18 00:00:00+00)",
        "completed_horizon": "[1998-01-01 00:00:00+00,2026-04-18 00:00:00+00)",
        "resolution": 1.0,
        "relations_searched": ["conjunction"],
        "targets_requested": 1,
        "target_resolution_state_counts": {"resolved": 1},
    }


def _window_row() -> dict:
    return {
        "window_key": "c15-era-1",
        "parent_key": None,
        "event_class": "marriage",
        "temporal_shape": "interval",
        "window_start": date(2020, 1, 1),
        "window_end": date(2020, 2, 1),
        "peak_date": date(2020, 1, 15),
        "milestone_id": None,
        "is_irreversibility_milestone": False,
        "signed_intensity": 0.5,
        "raw_intensity": 0.5,
        "valence": "gain",
        "is_adverse": False,
        "active_sentences": [],
        "contributing_systems": [],
        "suppression_state": {},
        "peak_basis": "gochara_lambda_e_v1",
        "calibration_state": "structural_prior",
        "resolution": "era",
    }


def _ledger_write_path_as_builder(admin_dsn: str, chart_id: str) -> dict:
    """The manifest + body-substep write statement classes of the writer's
    SQL layer, through one authenticated builder connection."""
    counts: dict = {}
    with BR.connect_as_builder(admin_dsn, connect_timeout=5) as conn:
        cid, _mid = _manifest(conn, chart_id)
        counts["manifest"] = 1
        ids = ledger.write_contacts(
            conn, chart_id, GENERATION, cid, [_episode()],
            "c15-build-body", bodies=["Saturn"])
        counts["contacts"] = len(ids)
        counts["coverage"] = ledger.write_coverage(
            conn, chart_id, GENERATION, cid, [_partition()],
            "c15-build-body", bodies=["Saturn"])
        conn.commit()
    return counts


def _windows_write_path_as_builder(admin_dsn: str, chart_id: str) -> int:
    """The windows-substep write statement class (write_windows' scoped
    delete-then-insert + the manifest count stamp) as the builder."""
    with BR.connect_as_builder(admin_dsn, connect_timeout=5) as conn:
        window_columns = {
            r[0] for r in conn.execute(
                "SELECT column_name FROM information_schema.columns"
                " WHERE table_schema = 'public'"
                "   AND table_name = 'kala_gochara_windows'").fetchall()
        }
        written, _dupes = step06b.write_windows(
            conn, chart_id, GENERATION, [_window_row()],
            source="fixture", window_columns=window_columns)
        step06b.update_manifest_windows_count(conn, chart_id, GENERATION, written)
        conn.commit()
    return written


# ── Tests ────────────────────────────────────────────────────────────────────

def test_control_mirror_is_deployment_faithful(builder_world):
    admin = builder_world["admin"]
    owner = admin.execute(
        "SELECT pg_get_userbyid(nspowner) FROM pg_namespace WHERE nspname = 'public'"
    ).fetchone()[0]
    assert owner == BR.OWNER_ROLE
    create_priv = admin.execute(
        "SELECT has_schema_privilege(%s, 'public', 'CREATE')", (BR.BUILDER_ROLE,)
    ).fetchone()[0]
    assert create_priv is False
    assert [Path(p).name for p in BR.grant_migration_files()] == \
        builder_world["applied"]["grant_migrations"]
    # The expected windows-chain migrations applied verbatim.
    assert builder_world["applied"]["windows_chain"] == [
        BR._find_migration(p).name for p in SCHEMA_MIGRATION_PREFIXES]


def test_manifest_and_ledger_write_path_as_builder(builder_world):
    """SUCCEEDS — the manifest substep (register_convention INSERT +
    publish_candidate INSERT/UPDATE) and the body-substep writes
    (write_contacts / write_coverage delete-then-insert) all land as
    data_plane_builder, and the rows read back. Proven privileges:
    SELECT/INSERT on kala_gochara_convention, SELECT/INSERT/UPDATE on
    kala_gochara_publication, SELECT/INSERT/DELETE on kala_gochara_contacts
    and kala_gochara_coverage."""
    counts = _ledger_write_path_as_builder(DSN, CHART)
    assert counts == {"manifest": 1, "contacts": 1, "coverage": 1}
    with BR.connect_as_builder(DSN, connect_timeout=5) as conn:
        for table, n in (("kala_gochara_contacts", 1),
                         ("kala_gochara_coverage", 1)):
            got = conn.execute(
                f"SELECT count(*) FROM {table}"
                " WHERE chart_id = %s AND generation = %s",
                (CHART, GENERATION)).fetchone()[0]
            assert got == n, f"{table}: expected {n} '{GENERATION}' row(s), found {got}"


def test_windows_write_path_as_builder(builder_world):
    """SUCCEEDS — the windows substep's write statement class as the builder:
    write_windows' scoped delete-then-insert on kala_gochara_windows plus the
    manifest windows-count stamp (UPDATE kala_gochara_publication.row_counts)
    land, and the row reads back as the builder. The ACL that made this a
    strict-xfail FINDING in C15 is recorded by grant migration 1237 (C16):
    SELECT/INSERT/UPDATE/DELETE on kala_gochara_windows + USAGE/SELECT on its
    identity sequence — exactly the production ACL."""
    written = _windows_write_path_as_builder(DSN, CHART)
    assert written == 1
    with BR.connect_as_builder(DSN, connect_timeout=5) as conn:
        got = conn.execute(
            "SELECT count(*) FROM kala_gochara_windows"
            " WHERE chart_id = %s AND generation = %s",
            (CHART, GENERATION)).fetchone()[0]
        assert got == 1, f"kala_gochara_windows: expected 1 '{GENERATION}' row, found {got}"


def test_forbidden_authority_write_refused_as_builder(builder_world):
    """FORBIDDEN — kala_gochara_authority is the step08 flip surface; the
    writer never touches it, and the builder role must be unable to."""
    import psycopg

    with BR.connect_as_builder(DSN, connect_timeout=5) as conn:
        with pytest.raises(psycopg.errors.InsufficientPrivilege):
            conn.execute(
                "INSERT INTO kala_gochara_authority (chart_id, authoritative_generation)"
                " VALUES (%s, '4.1')", (CHART,))
        conn.rollback()


def test_forbidden_write_after_publication_refused(builder_world):
    """FORBIDDEN — the candidate-only rail: once generation '4.1' is published
    for a chart, the ledger's write path refuses (N-7). The publication flip
    itself is performed AS THE OWNER (the builder must not hold UPDATE that
    lets it self-publish); the refused write is attempted as the builder. Two
    refusal classes are both a pass: the ledger's own
    PublishedGenerationRefusal where the builder can read the manifest, or the
    database's InsufficientPrivilege where it cannot even see it — either way
    a published generation is unwritable by the builder."""
    import psycopg

    admin = builder_world["admin"]
    with BR.as_owner(admin):
        cid, _mid = _manifest(admin, CHART_B)
        admin.execute(
            "UPDATE kala_gochara_publication SET status = 'published',"
            " published_at = now() WHERE chart_id = %s AND generation = %s",
            (CHART_B, GENERATION))
    with BR.connect_as_builder(DSN, connect_timeout=5) as conn:
        with pytest.raises((ledger.PublishedGenerationRefusal,
                            psycopg.errors.InsufficientPrivilege)):
            ledger.write_contacts(
                conn, CHART_B, GENERATION, cid, [_episode()], "c15-build-pub")
        conn.rollback()
    with BR.as_owner(admin):
        admin.execute(
            "UPDATE kala_gochara_publication SET status = 'rolled_back',"
            " published_at = NULL WHERE chart_id = %s AND generation = %s",
            (CHART_B, GENERATION))


def test_grant_migrations_idempotent(builder_world):
    admin = builder_world["admin"]
    again = BR.apply_grant_migrations(admin)
    assert again == builder_world["applied"]["grant_migrations"]
