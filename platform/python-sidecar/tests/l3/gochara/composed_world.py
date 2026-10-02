"""Composed-flow rehearsal world (Codex round 9, R9-6 iv): the REAL production-ordered migration stack on a deployment-faithful
disposable database, with ALL guards enabled.

Faithful to production where it matters for the privilege flows:
  * every object is OWNED by `amjis_app` (the migration principal); the schema's default privileges revoke PUBLIC EXECUTE on every
    function it creates (nirmana-evidence-ownership-preflight.ts:259);
  * the builder / verifier / sealer exist as separate NOLOGIN principals BEFORE the migrations run (so the role-guarded grants apply);
  * the order is production's: the earlier contract window (1081, 1152–1157), the routine grants (1216, 1220, 1234, 1236), then the
    protected window (1204, 1206 [+ PC-4], 1232, 1233, 1240);
  * L1/L0 reads the builder holds in production today (chart_facts, chart_dashas, bg_transit_rules — read-only production check,
    2026-10-02) are granted to the builder; the verifier/sealer are granted the same READS explicitly (provisioning the ND-ROLES grants
    migration must carry).
`stage` lets a test stop BEFORE a migration so a generation can be sealed in an older world and the later guards applied after it.
"""
from __future__ import annotations

import os
import uuid

import pytest

from .test_a53_inventory import (CHART_ID, DASHA, DASHA_PARENT, DB_PREFIX, L0_VEDHA_ROWS, PINNED_BUILD, CHART,
                                 drop_am5_database)
from .test_a53_record_store import ADMIN_DSN, MIGRATIONS

OWNER = "amjis_app"
BUILDER, VERIFIER, SEALER = "data_plane_builder", "gochara_verifier", "gochara_sealer"

EARLIER_WINDOW = ["1081_nirmana_l3_gochara_ledger_coverage_publication.sql",
                  "1152_kala_gochara_contacts_t_exact_nullable_truncated.sql",
                  "1153_gochara_sky_event_substrate.sql", "1154_gochara_rule_path_registry.sql",
                  "1155_gochara_relationship_record.sql", "1156_gochara_eval_window.sql",
                  "1157_gochara_av_polarity_declaration.sql"]
ROUTINE = ["1216_gochara_contract_builder_grants.sql", "1220_gochara_contract_builder_function_execute.sql",
           "1234_gochara_eval_window_builder_grants.sql", "1236_gochara_authority_refuses_governed_generation.sql",
           "1242_gochara_builder_record_replace_finalise_grants.sql"]
PROTECTED_WINDOW = ["1204_gochara_av_qualifier_object_role.sql", "1206_gochara_search_inventory_completeness.sql",
                    "1232_gochara_search_moon_scope_domain.sql", "1233_gochara_p1_period_anchor.sql",
                    "1240_gochara_window_verification_gate.sql"]
FULL_STACK = EARLIER_WINDOW + ROUTINE + PROTECTED_WINDOW

AUTHORITY_STUB = ("CREATE TABLE IF NOT EXISTS kala_gochara_authority (chart_id UUID PRIMARY KEY, authoritative_generation TEXT NOT NULL"
                  " DEFAULT 'v1', flipped_at TIMESTAMPTZ, flipped_by TEXT, evidence_ref TEXT)")


def composed_create(tag="comp", stack=None):
    """-> (admin_conn, db_name, dsn). `stack` = the migration files to apply, in order (default: the full production-ordered stack)."""
    psycopg = pytest.importorskip("psycopg")
    from psycopg.conninfo import make_conninfo
    missing = [f for f in (FULL_STACK if stack is None else stack) + [M1241] if not (MIGRATIONS / f).exists()]
    if missing:
        pytest.skip(f"NOT_RUN: integration exhibit — the migration tree lacks {missing} (they ship in the stacked draft PRs; see the PR description)")
    try:
        admin = psycopg.connect(ADMIN_DSN, autocommit=True, connect_timeout=3)
    except Exception as exc:  # noqa: BLE001
        if os.environ.get("GOCHARA_A53_REQUIRE_DB") == "1":
            pytest.fail(f"GOCHARA_A53_REQUIRE_DB=1 but the disposable database server is unreachable ({exc})")
        pytest.skip(f"NOT_RUN: disposable database server unreachable ({exc})")
    host = psycopg.conninfo.conninfo_to_dict(ADMIN_DSN).get("host", "")
    assert host in ("localhost", "127.0.0.1", ""), f"refusing a non-local server ({host})"
    for r in (OWNER, BUILDER, VERIFIER, SEALER):
        admin.execute(f"DO $$ BEGIN IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='{r}') THEN CREATE ROLE {r} NOLOGIN; END IF; END $$")
    name = f"{DB_PREFIX}{tag}_{uuid.uuid4().hex[:8]}"
    admin.execute(f'CREATE DATABASE "{name}"')
    dsn = make_conninfo(ADMIN_DSN, dbname=name)
    try:
        conn = psycopg.connect(dsn, autocommit=True, connect_timeout=3)
        conn.execute(f"DROP SCHEMA public CASCADE; CREATE SCHEMA public AUTHORIZATION {OWNER}")
        conn.execute(f"GRANT USAGE ON SCHEMA public TO {BUILDER}, {VERIFIER}, {SEALER}")
        conn.execute(f"ALTER DEFAULT PRIVILEGES FOR ROLE {OWNER} REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC")
        _populate(conn, FULL_STACK if stack is None else stack)
        conn.close()
    except BaseException:
        drop_am5_database(admin, name)
        raise
    return admin, name, dsn


def composed_clone(template_name):
    """-> (admin_conn, db_name, dsn): a byte-for-byte clone of an already-built database (CREATE DATABASE ... TEMPLATE) — the template must have
    no open connection. Roles are cluster-level, so the clone carries the same principals; object ACLs ride the catalog copy."""
    psycopg = pytest.importorskip("psycopg")
    from psycopg.conninfo import make_conninfo
    admin = psycopg.connect(ADMIN_DSN, autocommit=True, connect_timeout=3)
    name = f"{DB_PREFIX}clone_{uuid.uuid4().hex[:8]}"
    admin.execute(f'CREATE DATABASE "{name}" TEMPLATE "{template_name}"')
    return admin, name, make_conninfo(ADMIN_DSN, dbname=name)


def apply_migrations(conn, files):
    """Apply migration files AS the migration principal, one transaction per file (migrate.ts's contract)."""
    conn.execute(f"SET ROLE {OWNER}")
    try:
        for fname in files:
            if fname.startswith("1236_"):
                conn.execute(AUTHORITY_STUB)
                conn.execute("INSERT INTO kala_gochara_authority (chart_id, authoritative_generation) VALUES (%s, '3.0')"
                             " ON CONFLICT DO NOTHING", (CHART_ID,))
            with conn.transaction():
                conn.execute((MIGRATIONS / fname).read_text())
                conn.execute("INSERT INTO public._migrations_applied(filename) VALUES (%s)", (fname,))
    finally:
        conn.execute("RESET ROLE")


def _populate(conn, stack):
    conn.execute(f"SET ROLE {OWNER}")
    # `charts` as in production (read-only check 2026-10-02): row-level security ON (not forced), three PERMISSIVE policies for PUBLIC — the grant policy reads
    # `chart_grants`, so ANY role that reads `charts` needs SELECT on `chart_grants` too (policy expressions run as the invoker). chart_facts, chart_dashas and
    # bg_transit_rules have RLS OFF and no policies in production, so a table-level SELECT on them suffices (the mirror has none either).
    conn.execute("CREATE TABLE public.charts (id uuid PRIMARY KEY, owner_id text)")
    conn.execute("CREATE TABLE public.chart_grants (chart_id uuid, principal_id text)")
    conn.execute("ALTER TABLE public.charts ENABLE ROW LEVEL SECURITY")
    conn.execute("CREATE POLICY chart_grant_policy ON public.charts FOR SELECT USING (EXISTS (SELECT 1 FROM public.chart_grants g WHERE g.chart_id = charts.id"
                 " AND g.principal_id = current_setting('app.principal_id', true)))")
    conn.execute("CREATE POLICY chart_owner_policy ON public.charts USING (owner_id = current_setting('app.principal_id', true))")
    conn.execute("CREATE POLICY chart_service_policy ON public.charts USING (current_setting('app.principal_id', true) IS NULL"
                 " OR current_setting('app.principal_id', true) = '')")
    conn.execute("CREATE TABLE public._migrations_applied (filename text PRIMARY KEY, applied_at timestamptz DEFAULT now())")
    conn.execute("CREATE TABLE public.chart_facts (fact_id text PRIMARY KEY, chart_id uuid, ayanamsha_id text, fact_category text,"
                 " fact_subject text, fact_key text, fact_value_num double precision, created_at timestamptz DEFAULT now())")
    conn.execute("CREATE TABLE public.chart_dashas (dasha_row_id uuid PRIMARY KEY, chart_id uuid, ayanamsha_id text, system_id text,"
                 " level_n int, parent_row_id uuid, lord_graha text, start_iso timestamptz, end_iso timestamptz, build_id uuid,"
                 " verification_pass_status text, computed_at timestamptz DEFAULT now())")
    conn.execute("CREATE TABLE public.bg_transit_rules (id SERIAL PRIMARY KEY, rule_type TEXT NOT NULL CHECK (rule_type IN"
                 " ('favourable','unfavourable','vedha')), graha TEXT NOT NULL, primary_house INTEGER NOT NULL, vedha_house INTEGER,"
                 " phala TEXT NOT NULL, classical_citation TEXT NOT NULL, rule_notes TEXT, UNIQUE (graha, rule_type, primary_house))")
    for graha, house, vedha, citation, rule_type in L0_VEDHA_ROWS:
        conn.execute("INSERT INTO public.bg_transit_rules (rule_type, graha, primary_house, vedha_house, phala, classical_citation)"
                     " VALUES (%s,%s,%s,%s,'x',%s)", (rule_type, graha, house, vedha, citation))
    # the LEGACY 4.x windows relation (production: owned by amjis_app, RLS off, many readers). `ledger.publish` counts its rows for the manifest when the
    # relation EXISTS (ledger.py:612), so a production-shaped schema must carry it (Codex R10-7 ii): the sealer needs a column-narrow SELECT on it.
    conn.execute("CREATE TABLE public.kala_gochara_windows (window_id uuid PRIMARY KEY DEFAULT gen_random_uuid(), chart_id uuid NOT NULL, generation text NOT NULL,"
                 " raw_intensity numeric, signed_intensity numeric, payload jsonb)")
    conn.execute("INSERT INTO public.charts(id) VALUES (%s)", (CHART_ID,))
    conn.execute("INSERT INTO public.kala_gochara_windows(chart_id, generation, raw_intensity, signed_intensity) VALUES (%s,'5.0',1.0,1.0),(%s,'5.0',2.0,-2.0)",
                 (CHART_ID, CHART_ID))
    subj = {"LAGNA": CHART["lagna_deg"], "SUN": CHART["natal"]["Sun"], "MOON": CHART["natal"]["Moon"], "MAR": CHART["natal"]["Mars"],
            "MER": CHART["natal"]["Mercury"], "JUP": CHART["natal"]["Jupiter"], "VEN": CHART["natal"]["Venus"],
            "SAT": CHART["natal"]["Saturn"], "RAH_MEAN": CHART["natal"]["Rahu"], "KET_MEAN": CHART["natal"]["Ketu"]}
    for sname, lon in subj.items():
        conn.execute("INSERT INTO public.chart_facts(fact_id, chart_id, ayanamsha_id, fact_category, fact_subject, fact_key,"
                     " fact_value_num) VALUES (%s,%s,'lahiri_chitrapaksha','graha_position',%s,'longitude_sidereal',%s)",
                     (f"fact-{sname}", CHART_ID, sname, lon))
    for r in DASHA:
        parent = DASHA_PARENT[int(uuid.UUID(r.row_id).int)]
        conn.execute("INSERT INTO public.chart_dashas(dasha_row_id, chart_id, ayanamsha_id, system_id, level_n, parent_row_id,"
                     " lord_graha, start_iso, end_iso, build_id, verification_pass_status)"
                     " VALUES (%s,%s,'lahiri_chitrapaksha','vimshottari',%s,%s,%s,%s,%s,%s,'two_pass_verified')",
                     (r.row_id, CHART_ID, r.level, None if parent is None else str(uuid.UUID(int=parent)), r.lord.title(),
                      r.start, r.end, PINNED_BUILD))
    # the reads the BUILDER holds in production today (read-only check 2026-10-02). The verifier's and sealer's L1/L0 reads are NOT granted here:
    # they are part of the derived sets the 1241 grants migration must carry (test_b6_composed_seal_flows.BASELINE), so the sweep covers them.
    conn.execute(f"GRANT SELECT ON public.charts, public.chart_grants, public.chart_facts, public.chart_dashas, public.bg_transit_rules TO {BUILDER}")
    conn.execute("RESET ROLE")
    apply_migrations(conn, stack)


#: the world as it stood BETWEEN 1206 and 1240 — a generation sealed here is "sealed before 1240 existed"
STACK_BETWEEN_1206_AND_1240 = [f for f in FULL_STACK if not f.startswith("1240_")]
M1240 = "1240_gochara_window_verification_gate.sql"
M1241 = "1241_gochara_verifier_sealer_inventory_grants.sql"
