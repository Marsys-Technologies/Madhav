"""L0-M code-only source preparation; no extracted corpus rows or reseal.

The projection matches origin/main's services/ka_muhurta_seva/parihara_eval.py
load_rules contract. Fixtures are deliberately synthetic, never source proof.
"""
from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import re
import shlex
import sys
import uuid

import psycopg
from psycopg import sql
from psycopg.types.json import Jsonb
import pytest
import yaml

from tests.l3._disposable_db_guard import (
    assert_disposable_connection, validate_disposable_dsn,
)

PLATFORM = Path(__file__).resolve().parents[4]
MIGRATION_NAME = "1386_l0_m_parihara_typed_source_prepare.sql"
MIGRATION = PLATFORM / "migrations" / MIGRATION_NAME
FIELDS = ("predicate", "source_chunk_id", "source_verse", "conjunction_reading",
          "tika_extension", "priority_rank")


@pytest.fixture(scope="module")
def source_dsn():
    admin_dsn = os.environ.get("KALA_ADMIN_DSN")
    if not admin_dsn:
        if os.environ.get("KALA_REQUIRE_DB") == "1":
            pytest.fail("KALA_REQUIRE_DB=1 requires KALA_ADMIN_DSN")
        pytest.skip("NOT_RUN: KALA_ADMIN_DSN absent")
    validate_disposable_dsn(admin_dsn, "postgres")
    try:
        admin = psycopg.connect(admin_dsn, autocommit=True, connect_timeout=3)
    except psycopg.OperationalError:
        if os.environ.get("KALA_REQUIRE_DB") == "1":
            pytest.fail("required local test cluster unreachable")
        pytest.skip("NOT_RUN: local test cluster unreachable")
    name = "l0_parihara_test_" + uuid.uuid4().hex
    created = False
    try:
        assert_disposable_connection(admin, "postgres")
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
        created = True
        dsn = psycopg.conninfo.make_conninfo(admin_dsn, dbname=name)
        validate_disposable_dsn(dsn, name)
        yield dsn
    finally:
        if created:
            # All test connections have closed; never terminate peer sessions.
            assert_disposable_connection(admin, "postgres")
            admin.execute(sql.SQL("DROP DATABASE {}").format(sql.Identifier(name)))
        admin.close()


@pytest.fixture
def db(source_dsn):
    with psycopg.connect(source_dsn) as conn:
        assert_disposable_connection(conn, psycopg.conninfo.conninfo_to_dict(source_dsn)["dbname"])
        with conn.transaction(force_rollback=True):
            original = (PLATFORM / "supabase/migrations/544_bg_parihara_rules.sql").read_text()
            table = re.search(r"CREATE TABLE IF NOT EXISTS bg_parihara_rules \(.*?\n\);", original, re.S)
            assert table
            conn.execute(table.group())
            # Execute the historical CHECK/provenance alterations, without its
            # transaction wrappers (the fixture owns this rollback transaction).
            context = (PLATFORM / "supabase/migrations/524_bg_parihara_rules_muhurta_extraction_context.sql").read_text()
            conn.execute(context.split("BEGIN;", 1)[1].split("COMMIT;", 1)[0])
            conn.execute((PLATFORM / "migrations/1332_l0_muhurta_parihara_scope_prepare.sql").read_text())
            for i, scope in enumerate(("natal", "muhurta"), 1):
                conn.execute("""INSERT INTO public.bg_parihara_rules
                    (dosha_canonical_id,dosha_name_en,dosha_category,cancellation_index,
                     cancellation_condition_text,scope,source_text_id,source_citation,extraction_context)
                    VALUES (%s,'Synthetic fixture','fixture',1,'Synthetic condition',%s,
                            'test_source','test-only locator','mula_sutra_citation')""", (f"fixture_{i}", scope))
            yield conn


def apply(conn):
    conn.execute(MIGRATION.read_text())


def insert(conn, **patch):
    row = dict(dosha_canonical_id="fixture_new", dosha_name_en="Synthetic fixture",
               dosha_category="fixture", cancellation_index=1,
               cancellation_condition_text="Synthetic condition", scope="marriage",
               source_text_id="test_source", source_citation="test-only locator")
    row.update(patch)
    cols = list(row)
    conn.execute(sql.SQL("INSERT INTO public.bg_parihara_rules ({}) VALUES ({})").format(
        sql.SQL(",").join(map(sql.Identifier, cols)),
        sql.SQL(",").join(sql.Placeholder() for _ in cols)),
        [Jsonb(row[k]) if k == "predicate" else row[k] for k in cols])


def snapshot(conn):
    # Same content fields/order as migration 703's parihara pin. New nullable
    # metadata must not silently reclassify or change any pinned legacy tuple.
    return conn.execute("""SELECT count(*), encode(sha256(convert_to(COALESCE(string_agg(
        jsonb_build_array(dosha_canonical_id,dosha_name_en,dosha_category,cancellation_index,
        cancellation_condition_text,net_standing,scope,source_text_id,source_chapter,
        source_citation,extraction_context)::text, E'\n'
        ORDER BY dosha_canonical_id COLLATE "C",cancellation_index),''),'UTF8')),'hex')
        FROM public.bg_parihara_rules""").fetchone()


def test_consumer_projection_exists_with_honest_nulls(db):
    apply(db)
    rows = db.execute("""SELECT id,dosha_canonical_id,scope,source_citation,source_chunk_id,
        source_verse,predicate,conjunction_reading,tika_extension,priority_rank,
        net_standing,extraction_context FROM public.bg_parihara_rules
        WHERE scope = ANY(%s) AND dosha_canonical_id = ANY(%s)
        ORDER BY dosha_canonical_id,cancellation_index,id""",
        (["natal", "muhurta"], ["fixture_1", "fixture_2"])).fetchall()
    assert len(rows) == 2
    assert all(row[4:10] == (None,) * 6 for row in rows)


def test_migration_is_repeatable_and_preserves_every_existing_value_and_pin(db):
    before = snapshot(db)
    rows = db.execute("SELECT to_jsonb(r) FROM public.bg_parihara_rules r ORDER BY id").fetchall()
    apply(db)
    apply(db)
    assert snapshot(db) == before
    after = db.execute("SELECT to_jsonb(r) - %s::text[] FROM public.bg_parihara_rules r ORDER BY id", (list(FIELDS),)).fetchall()
    assert after == rows
    # Historical reader projection and default scope retain their behavior.
    db.execute("""INSERT INTO public.bg_parihara_rules
        (dosha_canonical_id,dosha_name_en,dosha_category,cancellation_index,
         cancellation_condition_text,source_text_id,source_citation)
        VALUES ('fixture_new','Synthetic fixture','fixture',1,'Synthetic condition',
                'test_source','test-only locator')""")
    assert db.execute("SELECT scope FROM public.bg_parihara_rules WHERE dosha_canonical_id='fixture_new'").fetchone() == ("natal",)


@pytest.mark.parametrize("scope", ["natal", "muhurta", "marriage", "upanayana", "general"])
def test_scope_domain_is_backward_compatible(db, scope):
    apply(db)
    insert(db, scope=scope)


@pytest.mark.parametrize("patch", [
    {"scope": "business"}, {"scope": ""}, {"scope": None},
    {"source_chunk_id": ""}, {"source_chunk_id": "   "},
    {"source_verse": 0}, {"source_verse": -88}, {"source_verse": 88},
    {"source_chunk_id": "test_chunk"},
    {"predicate": {}}, {"predicate": []}, {"predicate": "prose"},
    {"predicate": {"planet": "Mars", "house_from_lagna": [8]}},
    {"conjunction_reading": "assumed"}, {"priority_rank": 0}, {"priority_rank": -1},
    {"extraction_context": "unclassified_guess"}, {"net_standing": "verified"},
])
def test_invalid_metadata_is_rejected_by_postgres(db, patch):
    apply(db)
    with pytest.raises((psycopg.errors.CheckViolation, psycopg.errors.NotNullViolation)):
        with db.transaction():
            insert(db, **patch)


@pytest.mark.parametrize("context", ["mula", "mula_reconstructed", "tika_commentary"])
def test_typed_source_and_distinct_readings_are_representable(db, context):
    apply(db)
    insert(db, predicate={"planet": "Mars", "house_from_lagna": [8]},
           source_chunk_id="test_chunk", source_verse=88, conjunction_reading="tika",
           extraction_context=context, tika_extension=False, priority_rank=1)
    assert db.execute("SELECT source_verse,predicate,extraction_context FROM public.bg_parihara_rules WHERE dosha_canonical_id='fixture_new'").fetchone() == (
        88, {"planet": "Mars", "house_from_lagna": [8]}, context)


def test_unsupported_predicate_stays_null_and_vedha_prohibition_is_explicit(db):
    apply(db)
    insert(db, source_chunk_id="test_chunk", source_verse=69,
           extraction_context="mula", net_standing="never_cancelled")
    assert db.execute("SELECT predicate,tika_extension,priority_rank,net_standing FROM public.bg_parihara_rules WHERE dosha_canonical_id='fixture_new'").fetchone() == (
        None, None, None, "never_cancelled")


@pytest.mark.parametrize("standing", ["cancellable_by_condition", "cancellable_by_remedial_act", "cancelled"])
@pytest.mark.parametrize("context", [None, "mula_sutra_citation", "translator_gloss_in_narrative"])
def test_all_legacy_standings_and_contexts_remain_writable(db, standing, context):
    apply(db)
    insert(db, scope="natal", net_standing=standing, extraction_context=context)
    assert db.execute("SELECT net_standing,extraction_context FROM public.bg_parihara_rules WHERE dosha_canonical_id='fixture_new'").fetchone() == (standing, context)


def test_prebuild_contains_no_reference_data_or_reseal_writes():
    code = "\n".join(line for line in MIGRATION.read_text().splitlines()
                     if not line.lstrip().startswith("--"))
    assert not re.search(r"\b(INSERT|UPDATE|DELETE|TRUNCATE)\b", code, re.I)
    assert "asset_registry" not in code
    assert not re.search(r"\b(BEGIN|COMMIT)\s*;", code, re.I)


def test_migration_is_listed_for_the_protected_public_schema_window():
    names = (PLATFORM / "scripts/kala_protected_migrations.txt").read_text().splitlines()
    assert MIGRATION_NAME in names


def assert_required_source_ci(ci):
    # D-29 separates DB fixtures from the light Unit Tests context, while the
    # existing protected Governance Gates verdict now requires their full-suite result.
    sys.path.insert(0, str(PLATFORM / 'scripts/governance'))
    sys.path.insert(0, str(PLATFORM / 'scripts/governance/__tests__'))
    from ci_discovery import expanded_workflow
    from _ci_gate_test_support import runs_in_full_gate
    jobs = expanded_workflow(ci['jobs'])
    assert 'unit-db-tests' in jobs['full-suite']['needs']
    assert 'full-suite' in jobs['governance-gates']['needs']
    assert jobs['governance-gates']['name'] == 'Governance Gates (drift / schema / edge / native-literal / py-sidecar)'
    job = jobs['unit-db-tests']
    assert job['name'] == 'Unit DB contracts (throwaway Postgres)'
    needs = job["needs"] if isinstance(job["needs"], list) else [job["needs"]]
    assert "changes" in needs  # A5 D-33: may also wait on CI-generated outputs
    assert runs_in_full_gate(job)
    assert "postgres" in job["services"]
    assert not job.get("continue-on-error")
    steps = [step for step in job["steps"]
             if "pytest" in step.get("run", "") and "tests/l3/l0_parihara" in step["run"]]
    assert len(steps) == 1, "entire L0-M DB suite must execute under the protected full-suite gate"
    step = steps[0]
    assert runs_in_full_gate(step) and not step.get("continue-on-error")
    assert str(step["env"]["KALA_REQUIRE_DB"]) == "1"
    assert step["env"]["KALA_ADMIN_DSN"] == "postgresql://postgres:postgres@localhost:5432/postgres"
    # Exact invocation prevents filtered collection, skip-only execution and
    # shell soft-passes from satisfying the required-DB claim.
    assert shlex.split(step["run"]) == [
        "cd", "python-sidecar", "python", "-m", "pytest", "tests/l3/l0_parihara",
        "-q", "-rs", "--tb=short", "-p", "no:cacheprovider",
    ]


def test_required_ci_executes_all_source_tests_against_postgres():
    ci = yaml.safe_load((PLATFORM.parent / ".github/workflows/ci.yml").read_text())
    assert_required_source_ci(ci)


@pytest.mark.parametrize("mutation", [
    "advisory_only", "missing_step", "skip_job", "skip_step", "soft_job", "soft_step",
    "optional_db", "missing_dsn", "missing_service", "filtered", "collect_only", "soft_shell",
])
def test_required_ci_detector_rejects_non_gating_execution(mutation):
    ci = deepcopy(yaml.safe_load((PLATFORM.parent / ".github/workflows/ci.yml").read_text()))
    job = ci["jobs"]["unit-db-tests"]
    step = next(step for step in job["steps"]
                if "unit-db-tests-l0-parihara" in step.get("run", ""))
    if mutation in {"advisory_only", "missing_step"}:
        job["steps"].remove(step)
        if mutation == "advisory_only":
            ci["jobs"]["db-integration-tests"]["steps"].append(step)
    elif mutation == "skip_job":
        job["if"] = "false"
    elif mutation == "skip_step":
        step["if"] = "false"
    elif mutation == "soft_job":
        job["continue-on-error"] = True
    elif mutation == "soft_step":
        step["continue-on-error"] = True
    elif mutation == "optional_db":
        step["env"]["KALA_REQUIRE_DB"] = "0"
    elif mutation == "missing_dsn":
        del step["env"]["KALA_ADMIN_DSN"]
    elif mutation == "missing_service":
        del job["services"]["postgres"]
    else:
        step["run"] += {"filtered": " -k projection", "collect_only": " --collect-only",
                        "soft_shell": " || true"}[mutation]
    with pytest.raises((AssertionError, KeyError)):
        assert_required_source_ci(ci)
