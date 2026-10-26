"""SR-W4-VERIFIER-GRANTS: every relation the verification job's import closure reads is readable by role gochara_verifier (migration 1411).

The first W4 verification execution died on "permission denied for table bg_combustion_orbs": the verifier's closure had grown past its grants and
nothing compared the two. This guard does, statically (no database): it walks the verification job's import closure inside services/gochara_kernel
(pipeline/orchestrator/verification_job.py and every kernel module it imports, transitively), collects the public relations the closure names, and
requires each to be EITHER in the measured pre-1411 grant set OR granted by migration 1411.

CLAIMS, each with its fail-on-revert oracle:
  C1 every relation the closure names (among the relations the migration chain creates) is granted: pre-1411 measured set U 1411's list
     (revert: drop one GRANT line from 1411 -> that table is in neither set and this fails, naming it)
  C2 1411 grants exactly its eleven tables, SELECT only, to gochara_verifier, and never ka_gochara_seal_approval
     (revert: add a write privilege or the seal-approval table -> this fails)
  C3 applied on a throwaway database with the role present, the post-apply block passes and every table carries an explicit ACL SELECT entry
     (revert: replace one GRANT by a no-op -> the post-apply block RAISES naming that table)
C3 runs on the guarded local disposable cluster (GOCHARA_A53_ADMIN_DSN; NOT_RUN skip when unreachable, a FAILURE under GOCHARA_A53_REQUIRE_DB=1).
"""
from __future__ import annotations

import ast
import os
import re
import uuid
from pathlib import Path

import pytest

SIDECAR = Path(__file__).resolve().parents[3]
REPO = SIDECAR.parents[1]
KERNEL = SIDECAR / "services" / "gochara_kernel"
ENTRY = SIDECAR / "pipeline" / "orchestrator" / "verification_job.py"
MIGRATION = REPO / "platform" / "migrations" / "1411_gochara_verifier_closure_grants.sql"
GRANTED_1411 = ("_migrations_applied", "bg_combustion_orbs", "bg_dignity_reference", "bg_graha_naisargika_friendship", "bg_transit_rules",
                "ephemeris_daily", "ka_gochara_contact_identity", "ka_gochara_sky_event", "kala_gochara_authority", "kala_gochara_convention",
                "kala_gochara_windows")
# Measured 2026-10-26 (production readback w4-verifier-closure-acl-20261026T0856Z: has_table_privilege('gochara_verifier', t, 'SELECT') true)
GRANTED_BEFORE_1411 = frozenset((
    "chart_dashas", "chart_facts", "ka_gochara_contact", "ka_gochara_convention_bridge", "ka_gochara_eval_window", "ka_gochara_eval_window_record",
    "ka_gochara_eval_window_verification", "ka_gochara_factor", "ka_gochara_generation_seal", "ka_gochara_near_miss", "ka_gochara_near_miss_object",
    "ka_gochara_near_miss_search", "ka_gochara_near_miss_verification", "ka_gochara_physical_object", "ka_gochara_predicate",
    "ka_gochara_record_prerequisite", "ka_gochara_relationship_record", "ka_gochara_rule_path", "ka_gochara_rule_path_prerequisite",
    "ka_gochara_rule_path_seal", "ka_gochara_rule_path_soft_factor", "ka_gochara_seal_brief", "ka_gochara_search_input_snapshot",
    "ka_gochara_search_interval", "ka_gochara_search_inventory", "ka_gochara_search_inventory_verification", "ka_gochara_search_obligation",
    "ka_gochara_search_path_pin", "ka_gochara_sky_convention", "kala_gochara_contacts", "kala_gochara_coverage", "kala_gochara_publication"))
NAMED = re.compile(r"\b(?:FROM|JOIN|from|join)\s+(?:\"?public\"?\.)?\"?([a-z_][a-z0-9_]{3,})")
CREATED = re.compile(r"(?i)\bCREATE\s+(?:OR\s+REPLACE\s+)?(?:UNLOGGED\s+)?(?:TABLE|VIEW|MATERIALIZED\s+VIEW)\s+(?:IF\s+NOT\s+EXISTS\s+)?(?:\"?public\"?\.)?\"?([a-z_][a-z0-9_]*)")
RUNNER_TABLES = frozenset(("_migrations_applied",))          # created by platform/scripts/migrate.ts, not by a migration file


def closure() -> dict[Path, str]:
    """The verification job's import closure inside the kernel package plus the entry point (relative and absolute kernel imports, transitively)."""
    seen, todo = {}, [ENTRY]
    while todo:
        p = todo.pop()
        if p in seen or not p.is_file():
            continue
        seen[p] = p.read_text()
        for node in ast.walk(ast.parse(seen[p])):
            if isinstance(node, ast.ImportFrom):
                base = node.module or ""
                if node.level:
                    mods = [base] if base else [a.name for a in node.names]
                    todo += [KERNEL / (m.split(".")[0] + ".py") for m in mods if m]
                elif base == "services.gochara_kernel":
                    todo += [KERNEL / (a.name + ".py") for a in node.names]
                elif base.startswith("services.gochara_kernel."):
                    todo.append(KERNEL / (base.split(".")[2] + ".py"))
    return seen


def created_relations() -> set[str]:
    names = set()
    for path in (REPO / "platform" / "migrations").glob("*.sql"):
        names |= {m.group(1) for m in CREATED.finditer(path.read_text())}
    return (names - {"public"}) | RUNNER_TABLES               # a schema-qualified name is never a relation called public


def test_c1_every_relation_the_verifier_closure_reads_is_granted():
    files = closure()
    assert ENTRY in files and len(files) > 10, "the closure walk found too little: the guard would read nothing"
    granted_1411 = set(re.findall(r"GRANT SELECT ON public\.([a-z_0-9]+) TO gochara_verifier;", MIGRATION.read_text()))
    named = {m.group(1) for text in files.values() for m in NAMED.finditer(text)} & created_relations()
    ungranted = sorted(named - GRANTED_BEFORE_1411 - granted_1411)
    assert not ungranted, f"the verifier's closure reads {ungranted} but gochara_verifier is never granted SELECT on them (add them to a grant migration)"
    text = "\n".join(files.values())                          # 1411's list came from the closure's text (a word, not only a FROM/JOIN: ephemeris_daily)
    unread = sorted(t for t in GRANTED_1411 if not re.search(r"\b" + re.escape(t) + r"\b", text))
    assert not unread, f"1411 grants tables the closure never names: {unread}"


def test_c2_1411_grants_exactly_its_eleven_tables_select_only():
    text = MIGRATION.read_text()
    grants = re.findall(r"GRANT\s+([A-Z, ]+)\s+ON\s+public\.([a-z_0-9]+)\s+TO\s+([a-z_]+);", text)
    assert sorted(t for _, t, _ in grants) == sorted(GRANTED_1411)
    assert {p.strip() for p, _, _ in grants} == {"SELECT"} and {r for _, _, r in grants} == {"gochara_verifier"}
    assert "ka_gochara_seal_approval" not in re.sub(r"--[^\n]*", "", text), "1411 must not touch ka_gochara_seal_approval"


@pytest.fixture()
def database():
    psycopg = pytest.importorskip("psycopg")
    from psycopg.conninfo import make_conninfo
    from ._disposable_db_guard import UnsafeAdminDSN, guarded_admin_connect
    from .test_a53_record_store import ADMIN_DSN, DB_PREFIX
    try:
        admin = guarded_admin_connect(ADMIN_DSN, autocommit=True, connect_timeout=3)
    except UnsafeAdminDSN:
        raise
    except Exception as exc:  # noqa: BLE001
        if os.environ.get("GOCHARA_A53_REQUIRE_DB") == "1":
            pytest.fail(f"GOCHARA_A53_REQUIRE_DB=1 but the disposable database server is unreachable ({exc})")
        pytest.skip(f"NOT_RUN: disposable database server unreachable ({exc})")
    created = admin.execute("SELECT 1 FROM pg_roles WHERE rolname = 'gochara_verifier'").fetchone() is None
    if created:
        admin.execute('CREATE ROLE "gochara_verifier" NOLOGIN')
    name = f"{DB_PREFIX}vgrants_{uuid.uuid4().hex[:8]}"
    admin.execute(f'CREATE DATABASE "{name}"')
    conn = psycopg.connect(make_conninfo(ADMIN_DSN, dbname=name), autocommit=True, connect_timeout=3)
    try:
        for t in GRANTED_1411:                                         # the eleven prerequisites as bare tables (grants depend on nothing else)
            conn.execute(f"CREATE TABLE public.{t} (id int)")
        yield conn
    finally:
        conn.close()
        assert name.startswith(DB_PREFIX), name                       # never drop what we did not create
        admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
        if created:
            admin.execute('DROP ROLE IF EXISTS "gochara_verifier"')
        admin.close()


def _apply(conn, text):
    with conn.transaction():                                          # the migration runner owns the transaction (SET LOCAL lock_timeout)
        conn.execute(text)


def test_c3_applied_the_post_apply_block_measures_an_explicit_select_grant_on_every_table(database):
    _apply(database, MIGRATION.read_text())
    for t in GRANTED_1411:
        n = database.execute("SELECT count(*) FROM pg_class c, LATERAL aclexplode(c.relacl) a WHERE c.oid = %s::regclass"
                             " AND a.grantee = 'gochara_verifier'::regrole::oid AND a.privilege_type = 'SELECT' AND a.grantor <> a.grantee", (f"public.{t}",)).fetchone()[0]
        assert n == 1, t
        assert database.execute("SELECT has_table_privilege('gochara_verifier', %s, 'INSERT')", (f"public.{t}",)).fetchone()[0] is False, t


def test_c3_with_one_grant_reverted_the_post_apply_block_raises_naming_that_table(database):
    grant = "GRANT SELECT ON public.ephemeris_daily TO gochara_verifier;"
    assert grant in MIGRATION.read_text(), "the migration no longer states the grant in the form this oracle reverts"
    with pytest.raises(Exception, match="no explicit ACL grant of SELECT on: public.ephemeris_daily"):
        _apply(database, MIGRATION.read_text().replace(grant, "NULL;"))
