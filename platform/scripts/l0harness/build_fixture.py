"""Build and rehearse the L0-W7 minimal data-plane fixture.

Rehearsal-only: creates a fresh local database on the rehearsal cluster
(127.0.0.1:55433, trust auth), applies the probe-derived fixture schema, seeds
bounded production reference data, then applies migrations 171-extract / 596 /
1035 / 1036 verbatim under their required actor roles, synthesizes two complete
L1 generations (ga_positions, ga_structural) with capture-faithful snapshots,
and asserts the trigger/role/grant gates via pg_catalog.

CI restores production --schema-only pg_dump instead; nothing here touches the
CI restore path. All reference-data choices trace to scripts/l0harness/
production_seed/*.jsonl (see seed_manifest.json) and all schema choices trace to
scripts/l0harness/production_schema/*.json probes. Deviations and probe
surprises are recorded in REHEARSAL_NOTES.md.

Usage: python3 scripts/l0harness/build_fixture.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLATFORM = HERE.parent.parent
SCHEMA_DIR = HERE / "production_schema"
SEED_DIR = HERE / "production_seed"
MIGRATIONS = PLATFORM / "supabase" / "migrations"

PGHOST = "127.0.0.1"
PGPORT = "55433"
SUPERUSER = "Dev"
MAINTENANCE_DB = "postgres"
FIXTURE_DB = "madhav_l0w7_fixture"

# Fixed identities (uuid-shaped, hex-only) so every seeded cross-reference is
# deterministic and greppable.
CHART_ID = "f0000000-0000-4000-8000-000000000001"        # charts.id (production chart_facts join key)
CHART_ALT_ID = "f0000000-0000-4000-8000-000000000002"    # charts.chart_id (unique column)
RUN_GA_POSITIONS = "f0000000-0000-4000-8000-000000000101"
RUN_GA_STRUCTURAL = "f0000000-0000-4000-8000-000000000102"
RUN_GA_YOGA = "f0000000-0000-4000-8000-000000000103"
RUN_BO_LAKSANA = "f0000000-0000-4000-8000-000000000104"
SIGNAL_ID = "f0000000-0000-4000-8000-000000000201"

AYANAMSHA = "surya_siddhanta_classical"
PARTITION_KEY = f"ayanamsha:{AYANAMSHA}"

CONTRACT_VERSION = "l1.data-plane.contract.1.0"
L0_RELEASE_ID = "l0.semantic.2026-09-13.1"
L0_RELEASE_DIGEST = "665096a74a59ea7e0e50ce98fc685899b89f325aca0d91c214f0040e4d259dd1"
L0_CONFIG_ID = "l0-resource-config-g1"
L0_CONFIG_DIGEST = "d516aecff9d4e05d929dc7fd71a113fd5c53d1f6ea1eb2582caafd3a339c279a"

GUARDED_L1_TABLES = [
    "chart_facts", "chart_dashas", "chart_divisionals", "ga_condition_composite",
    "ga_yoga_firings", "chart_vichara", "ga_transit_anchors",
    "l1_tajik_varsha_year_lords", "ga_medical", "ga_vastu_planet_direction_map",
    "ga_prashna_lagna", "ga_prashna_judgment",
]
CAPTURE_L1_TABLES = [t for t in GUARDED_L1_TABLES if t != "chart_dashas"]

STEP = 0


def log(msg: str) -> None:
    print(f"[build_fixture] {msg}", flush=True)


def step(name: str) -> None:
    global STEP
    STEP += 1
    log(f"── step {STEP}: {name}")


def psql(sql: str, *, user: str = SUPERUSER, db: str = FIXTURE_DB,
         set_role: str | None = None, expect_fail: bool = False) -> subprocess.CompletedProcess:
    """Run sql via psql -X -v ON_ERROR_STOP=1. Returns the CompletedProcess."""
    if set_role:
        sql = f"SET ROLE {set_role};\n" + sql
    cmd = [
        "psql", "-X", "-h", PGHOST, "-p", PGPORT, "-U", user, "-d", db,
        "-v", "ON_ERROR_STOP=1", "-q", "-c", sql,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if expect_fail:
        if res.returncode == 0:
            raise SystemExit(f"expected failure but succeeded: {sql[:200]}")
        return res
    if res.returncode != 0:
        print(res.stdout)
        print(res.stderr, file=sys.stderr)
        raise SystemExit(f"psql failed as {user} (role {set_role}): {sql[:400]}")
    return res


def psql_file(path: Path, *, user: str = SUPERUSER, db: str = FIXTURE_DB,
              set_role: str | None = None) -> None:
    """Pipe (optional SET ROLE +) a file into psql so multi-statement migrations
    run in one session, preserving their own BEGIN/COMMIT blocks."""
    content = path.read_text()
    if set_role:
        content = f"SET ROLE {set_role};\n" + content
    cmd = [
        "psql", "-X", "-h", PGHOST, "-p", PGPORT, "-U", user, "-d", db,
        "-v", "ON_ERROR_STOP=1", "-q",
    ]
    res = subprocess.run(cmd, input=content, capture_output=True, text=True)
    if res.returncode != 0:
        print(res.stdout)
        print(res.stderr, file=sys.stderr)
        raise SystemExit(f"psql failed applying {path.name} as {user} (role {set_role})")


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


# ── step a: fresh database ────────────────────────────────────────────────────

def step_recreate_db() -> None:
    step("drop/create fixture database")
    psql(f"DROP DATABASE IF EXISTS {FIXTURE_DB} (FORCE);", db=MAINTENANCE_DB)
    psql(f"CREATE DATABASE {FIXTURE_DB};", db=MAINTENANCE_DB)
    log(f"created {FIXTURE_DB} on {PGHOST}:{PGPORT}")


# ── step b: schema, support table, roles, owners ─────────────────────────────

def step_schema_roles() -> None:
    step("fixture DDL + asset_output_digest_specs + roles + table owners")
    ddl = subprocess.run(
        [sys.executable, str(HERE / "fixture_schema.py")],
        capture_output=True, text=True, check=True,
    ).stdout
    psql(ddl)

    # Support table required by 1036's bo_samvada digest preflight
    # (1036:396-405). DDL probed from production 2026-09-26; not part of the
    # 27-table fixture set — disclosed in REHEARSAL_NOTES.md.
    psql("""
CREATE TABLE asset_output_digest_specs (
  asset_id text NOT NULL,
  spec_sha256 text NOT NULL,
  spec jsonb NOT NULL,
  reviewed_at timestamptz NOT NULL DEFAULT now(),
  retired_at timestamptz,
  PRIMARY KEY (asset_id, spec_sha256),
  FOREIGN KEY (asset_id) REFERENCES asset_registry(asset_id),
  CHECK (spec_sha256 ~ '^[a-f0-9]{64}$'),
  CHECK (jsonb_typeof(spec) = 'object'),
  CHECK (retired_at IS NULL OR retired_at >= reviewed_at)
);
""")

    # Roles mirror production pg_roles flags (probed 2026-09-26):
    # amjis_app/builder/verifier/migrator LOGIN NOINHERIT; owners NOLOGIN.
    # None super/createrole/createdb/bypassrls — 1035/1036 preflights check this.
    psql("""
DROP ROLE IF EXISTS amjis_app, data_plane_builder, data_plane_verifier,
  data_plane_migrator, data_plane_l1_owner, data_plane_l2_owner,
  data_plane_schema_owner, role_orchestrator;
CREATE ROLE amjis_app LOGIN NOINHERIT;
CREATE ROLE data_plane_builder LOGIN NOINHERIT;
CREATE ROLE data_plane_verifier LOGIN NOINHERIT;
CREATE ROLE data_plane_migrator LOGIN NOINHERIT;
CREATE ROLE data_plane_l1_owner NOLOGIN NOINHERIT;
CREATE ROLE data_plane_l2_owner NOLOGIN NOINHERIT;
CREATE ROLE data_plane_schema_owner NOLOGIN NOINHERIT;
CREATE ROLE role_orchestrator NOLOGIN NOINHERIT;
GRANT data_plane_l1_owner, data_plane_l2_owner, data_plane_schema_owner
  TO data_plane_migrator;
""")

    # Fixture bootstrap: the fresh DB's public schema is owned by the
    # superuser; production grants on schema public were probed as
    # CREATE+USAGE for amjis_app and USAGE for the data-plane roles.
    # 1035/1036 create tables/sequences as the owner roles, so CREATE must
    # reach them, and sequences created pre-migration must be owned by a
    # role able to run 1035's dynamic GRANT ... ON SEQUENCE (l1_owner).
    psql("""
ALTER SCHEMA public OWNER TO amjis_app;
GRANT CREATE ON SCHEMA public TO data_plane_l1_owner, data_plane_l2_owner;
GRANT USAGE ON SCHEMA public TO data_plane_builder, data_plane_verifier,
  data_plane_migrator, data_plane_l1_owner, data_plane_l2_owner,
  role_orchestrator;
ALTER SEQUENCE chart_vichara_id_seq OWNER TO data_plane_l1_owner;
ALTER SEQUENCE ga_yoga_firings_id_seq OWNER TO data_plane_l1_owner;
ALTER SEQUENCE yoga_families_id_seq OWNER TO amjis_app;
""")

    # Owners per production pg_class probe (table_acls.json).
    acls = json.loads((SCHEMA_DIR / "table_acls.json").read_text())
    for row in acls:
        psql(f"ALTER TABLE {row['table_name']} OWNER TO {row['owner']};")
    psql("ALTER TABLE asset_output_digest_specs OWNER TO amjis_app;")
    # Support-table grants probed from production 2026-09-26 (amjis_app grantor):
    # SELECT to data_plane_builder + data_plane_l2_owner (1036 preflight reads
    # it as l2_owner). Production also grants retrieval_census_ro and
    # nirmana_evidence_ingress_writer — outside the fixture role set, omitted.
    psql("GRANT SELECT ON asset_output_digest_specs TO data_plane_builder, data_plane_l2_owner;",
         set_role="amjis_app")

    # L2 producer stub tables: 1036's closing GRANT (1036:2049-2062) names all
    # 29 L2 producer tables unconditionally, so verbatim application requires
    # them to exist. Only bodha_msr_signals is in the 27-table fixture set;
    # the other 28 are created as identity-column-only stubs owned by
    # data_plane_l2_owner (production owner, probed 2026-09-26). Identity
    # columns from 1036:1749-1777. Disclosed in REHEARSAL_NOTES.md.
    l2_stubs = [
        ("bodha_cgm_nodes", "node_id"), ("bodha_cgm_edges", "edge_id"),
        ("bodha_contradictions", "contradiction_id"), ("bodha_cgm_paths", "path_id"),
        ("bodha_cgm_motifs", "motif_id"), ("bodha_cgm_sub_graphs", "subgraph_id"),
        ("bodha_cgm_chart_topology_summary", "summary_id"), ("bodha_mechanisms", "mechanism_id"),
        ("bodha_cdlm_cells", "cell_id"), ("bodha_convergence", "convergence_id"),
        ("bodha_triangulation", "triangulation_id"), ("bodha_cdlm_chart_summary", "summary_id"),
        ("bodha_cdlm_domain_rollups", "rollup_id"), ("bodha_cdlm_pattern_clusters", "pattern_id"),
        ("bodha_pratijna", "pratijna_id"), ("bodha_rm_resonances", "resonance_id"),
        ("bodha_rm_remedy_prescriptions", "prescription_id"),
        ("bodha_rm_dasha_windowed_prescriptions", "window_prescription_id"),
        ("bodha_rm_chart_summary", "summary_id"), ("bodha_rm_dosha_remedy_bundles", "bundle_id"),
        ("bodha_rm_pattern_remedies", "pattern_remedy_id"), ("bodha_signal_embeddings", "signal_id"),
        ("bodha_discoveries", "discovery_id"), ("bodha_anomalies", "anomaly_id"),
        ("bodha_question_lenses", "lens_id"), ("bodha_chart_gestalt", "gestalt_id"),
        ("synthesis_quality_scorecard", "scorecard_id"), ("bodha_grounding_matches", "match_id"),
    ]
    for table, ident in l2_stubs:
        psql(f"CREATE TABLE {table} ({ident} text PRIMARY KEY);"
             f" ALTER TABLE {table} OWNER TO data_plane_l2_owner;")
    log(f"  28 L2 producer stub tables created (owner data_plane_l2_owner)")
    log(f"27 fixture tables + support table created; owners set for {len(acls)} tables")


# ── step c: reference data ────────────────────────────────────────────────────

def load_jsonl(table: str) -> list[dict]:
    return [json.loads(line) for line in (SEED_DIR / f"{table}.jsonl").read_text().splitlines() if line.strip()]


def seed_table(table: str, rows: list[dict]) -> None:
    if not rows:
        return
    payload = json.dumps(rows)
    psql(
        "INSERT INTO " + table + " "
        "SELECT * FROM jsonb_populate_recordset(NULL::" + table + ", $seed$"
        + payload + "$seed$::jsonb);"
    )
    log(f"  seeded {table}: {len(rows)} rows")


def step_reference_data() -> None:
    step("seed bounded production reference data (JSONL)")
    # asset_registry first; topologically ordered so superseded_by self-FK
    # targets land before their dependents.
    assets = load_jsonl("asset_registry")
    by_id = {r["asset_id"]: r for r in assets}
    ordered: list[dict] = []
    seen: set[str] = set()

    def visit(r: dict) -> None:
        aid = r["asset_id"]
        if aid in seen:
            return
        seen.add(aid)
        sup = r.get("superseded_by")
        if sup and sup in by_id:
            visit(by_id[sup])
        ordered.append(r)

    for r in assets:
        visit(r)
    seed_table("asset_registry", ordered)
    seed_table("classical_texts", load_jsonl("classical_texts"))
    seed_table("classical_text_chunks", load_jsonl("classical_text_chunks"))
    seed_table("brahma_yoga_catalog", load_jsonl("brahma_yoga_catalog"))
    seed_table("brahma_dosha_catalog", load_jsonl("brahma_dosha_catalog"))
    seed_table("sutravali_rules", load_jsonl("sutravali_rules"))
    seed_table("fact_category_ownership", load_jsonl("fact_category_ownership"))


# ── step d: pre-trigger data seeds ────────────────────────────────────────────

def step_data_seeds() -> None:
    step("seed charts row + L1/L2 data rows (pre-trigger, guard-compliant)")
    chunk_id = json.loads((SEED_DIR / "classical_text_chunks.jsonl").read_text().strip())["id"]

    psql(f"""
INSERT INTO charts (id, client_id, name, birth_date, birth_time, birth_place,
                    birth_lat, birth_lng, ayanamsa, house_system, native_id,
                    owner_id, subject_name, chart_id, role, chart_type, timezone_id)
VALUES ({sql_literal(CHART_ID)}, 'fixture-client', 'L0W7 Fixture Chart',
        DATE '1990-01-15', TIME '14:30:00', 'Varanasi, IN',
        25.3176, 82.9739, 'lahiri', 'sripathi', 'abhisek',
        'fixture-owner', 'Fixture Subject', {sql_literal(CHART_ALT_ID)},
        'fixture', 'natal', 'Asia/Kolkata');
""")

    facts = [
        # ga_positions row — production category graha_position (1,290 rows in
        # production), single-valued so a live capture's fact-snapshot CHECK
        # would accept it. Attached to the ga_positions generation in step i.
        dict(fact_id="f100000000000001", category="graha_position", subject="SUN",
             key="longitude_sidereal", num="271.5000", text=None, jsonb=None,
             unit="degree", ayanamsha=AYANAMSHA, build=RUN_GA_POSITIONS),
        # ga_structural-owned categories (fact_category_ownership rows 1-64).
        dict(fact_id="f100000000000002", category="graha_vargottama_amplification_factor",
             subject="SUN", key="amplification_factor", num="1.25", text=None,
             jsonb=None, unit=None, ayanamsha=AYANAMSHA, build=RUN_GA_STRUCTURAL),
        dict(fact_id="f100000000000003", category="net_argala_per_varga",
             subject="D1_HOUSE_2", key="net_argala", num="3", text=None,
             jsonb=None, unit=None, ayanamsha=AYANAMSHA, build=RUN_GA_STRUCTURAL),
        # Multi-valued (text + jsonb) — bo_laksana's D1 dignity lookup needs
        # fact_value_jsonb->>'varga'. A live capture's fact-snapshot CHECK
        # (exactly one typed value) would reject it, as it would 175,949
        # production rows; row+fact snapshots are therefore NOT synthesized
        # for this row (disclosed in REHEARSAL_NOTES.md).
        dict(fact_id="f100000000000004", category="graha_dignity_per_varga",
             subject="D1_MOON", key="dignity_state", num=None, text="own",
             jsonb={"varga": "D1"}, unit=None, ayanamsha=AYANAMSHA,
             build=RUN_GA_STRUCTURAL),
        # yoga_label bridge row for bo_laksana's classical-source join.
        # Category exists in production (125 rows) but has no
        # fact_category_ownership row — pre-trigger seed only.
        dict(fact_id="f100000000000005", category="yoga_label", subject="sunapha",
             key="fired", num=None, text=None,
             jsonb={"fired": True, "state": "present",
                    "classical_citations": [
                        {"text_id": "bphs", "chapter": 30, "chunk_id": chunk_id},
                        {"text_id": "saravali", "chapter": 38}]},
             unit=None, ayanamsha=AYANAMSHA, build=RUN_GA_YOGA),
        # bo_laksana strength lookup rows (category real in production,
        # unowned); required_rupa mirrors the INVARIANT convention documented
        # in bo_laksana.py:_build_strength_lookup.
        dict(fact_id="f100000000000006", category="graha_shadbala_total",
             subject="MOON", key="ratio", num="1.12", text=None, jsonb=None,
             unit="ratio", ayanamsha=AYANAMSHA, build=RUN_GA_STRUCTURAL),
        dict(fact_id="f100000000000007", category="graha_shadbala_total",
             subject="MOON", key="required_rupa", num="5.0", text=None,
             jsonb=None, unit="rupa", ayanamsha="INVARIANT", build=RUN_GA_STRUCTURAL),
    ]
    for f in facts:
        psql(f"""
INSERT INTO chart_facts (fact_id, chart_id, ayanamsha_id, build_id,
    fact_category, fact_subject, fact_key,
    fact_value_num, fact_value_text, fact_value_jsonb, unit,
    citation_ref, citation_human, source_calculation,
    verification_pass_status, engine_version, computed_at)
VALUES ({sql_literal(f['fact_id'])}, {sql_literal(CHART_ID)}, {sql_literal(f['ayanamsha'])},
    {sql_literal(f['build'])},
    {sql_literal(f['category'])}, {sql_literal(f['subject'])}, {sql_literal(f['key'])},
    {f['num'] if f['num'] is not None else 'NULL'},
    {sql_literal(f['text']) if f['text'] is not None else 'NULL'},
    {sql_literal(json.dumps(f['jsonb'])) + '::jsonb' if f['jsonb'] is not None else 'NULL'},
    {sql_literal(f['unit']) if f['unit'] is not None else 'NULL'},
    'fixture://l0w7', 'L0-W7 fixture seed', 'fixture_seed',
    'two_pass_verified', 'fixture_seed_v1', now());
""")
    log(f"  seeded chart_facts: {len(facts)} rows")

    psql(f"""
INSERT INTO ga_yoga_firings (chart_id, build_id, ayanamsha_id,
    yoga_canonical_id, fired, constituent_planets, constituent_houses,
    strength, is_partial, bhanga_active, family_ids,
    derivation, citation_ref, citation_human)
VALUES ({sql_literal(CHART_ID)}, {sql_literal(RUN_GA_YOGA)}, {sql_literal(AYANAMSHA)},
    'sunapha', true, '["MOON","VENUS"]'::jsonb, '[2]'::jsonb,
    0.8, false, false, '[]'::jsonb,
    'Venus occupies 2nd from Moon (fixture)', 'bphs:30',
    'BPHS ch.30 — Sunapha Yoga (fixture seed)');
""")

    psql(f"""
INSERT INTO chart_vichara (chart_id, ayanamsha_id, build_id, vichara_family,
    subject, actor, target, domain, varga, value_text, value_num,
    ratification_factor)
VALUES
  ({sql_literal(CHART_ID)}, {sql_literal(AYANAMSHA)}, {sql_literal(RUN_GA_STRUCTURAL)},
   'varga_ratification', 'MAR', NULL, NULL, 'wealth', NULL, NULL, NULL, 1.2),
  ({sql_literal(CHART_ID)}, {sql_literal(AYANAMSHA)}, {sql_literal(RUN_GA_STRUCTURAL)},
   'valence_pass', 'MAR', 'MAR', 'H2', NULL, 'D1', 'strong_benefic', 0.8, NULL);
""")

    psql(f"""
INSERT INTO bodha_msr_signals (signal_id, chart_id, ayanamsha_id, build_id,
    signal_type_id, signal_type_class, signal_tradition, fact_kind,
    source_l1_asset, source_subsystem,
    signal_summary_text, configuration_jsonb, constituent_facts_array,
    deterministic_strength, verification_certainty, computed_salience,
    salience_formula_version, domains_affected_array, domain_salience_jsonb,
    active_duration_class, verification_pass_status,
    citation_ref, citation_human, computed_at, engine_version, producer_asset_id)
VALUES ({sql_literal(SIGNAL_ID)}, {sql_literal(CHART_ID)}, {sql_literal(AYANAMSHA)},
    {sql_literal(RUN_BO_LAKSANA)},
    'fixture_yoga_signal', 'yoga', 'parashari', 'yoga_label',
    'ga_yoga', 'ganita',
    'Sunapha Yoga present (fixture)', '{{}}'::jsonb, '{{f100000000000005}}'::text[],
    0.8, 0.9, 1.0,
    'fixture_salience_v1', '{{wealth}}'::text[], '{{"wealth": 1.0}}'::jsonb,
    'long_term', 'two_pass_verified',
    'fixture://l0w7', 'L0-W7 fixture seed', now(), 'bo_laksana', 'bo_laksana');
""")
    log("  seeded ga_yoga_firings(1), chart_vichara(2), bodha_msr_signals(1)")


# ── step e: migrations ────────────────────────────────────────────────────────

def extract_171() -> Path:
    """Verbatim build_runs + build_run_assets DDL from 171_build_runs.sql.

    The migration's asset_throughput ALTERs are excluded because
    asset_throughput is outside the 27-table fixture set (recorded in
    REHEARSAL_NOTES.md). Only the two CREATE TABLE statements are extracted,
    textually, from the migration file — never retyped.
    """
    src = (MIGRATIONS / "171_build_runs.sql").read_text()
    blocks = re.findall(
        r"CREATE TABLE IF NOT EXISTS (?:build_runs|build_run_assets)\s*\(.*?\n\);",
        src, re.DOTALL,
    )
    if len(blocks) != 2:
        raise SystemExit(f"171 extract expected 2 CREATE TABLE blocks, got {len(blocks)}")
    out = HERE / "_171_extract.sql"
    out.write_text(
        "-- Extracted verbatim from supabase/migrations/171_build_runs.sql\n"
        "-- (build_runs + build_run_assets only; asset_throughput ALTERs excluded\n"
        "--  because asset_throughput is not in the fixture set.)\n\n"
        + "\n\n".join(blocks) + "\n"
    )
    return out


def step_migrations() -> None:
    step("apply 171-extract → 596 → 1035 → 1036 under required actors")
    extract = extract_171()
    psql_file(extract)
    psql("ALTER TABLE build_runs OWNER TO amjis_app; ALTER TABLE build_run_assets OWNER TO amjis_app;")
    log("  171 extract applied (build_runs, build_run_assets)")

    psql_file(MIGRATIONS / "596_nirmana_provenance_receipts.sql")
    psql("ALTER TABLE asset_provenance_receipts OWNER TO amjis_app; ALTER TABLE asset_freshness OWNER TO amjis_app;")
    log("  596 applied (asset_provenance_receipts, asset_freshness + triggers)")

    psql_file(MIGRATIONS / "1035_data_plane_l1_producer_history.sql",
              user="data_plane_migrator", set_role="data_plane_l1_owner")
    log("  1035 applied as data_plane_migrator SET ROLE data_plane_l1_owner")

    psql_file(MIGRATIONS / "1036_data_plane_l2_producer_generations.sql",
              user="data_plane_migrator", set_role="data_plane_l2_owner")
    log("  1036 applied as data_plane_migrator SET ROLE data_plane_l2_owner")


# ── step f: grant replay ──────────────────────────────────────────────────────

def step_grants() -> None:
    step("replay production table grants (grantor-faithful)")
    grants = json.loads((SCHEMA_DIR / "grants.json").read_text())
    by_grantor: dict[str, list[dict]] = {}
    for g in grants:
        by_grantor.setdefault(g["grantor"], []).append(g)
    for grantor, rows in by_grantor.items():
        stmts = "; ".join(
            f"GRANT {r['privilege_type']} ON TABLE {r['table_name']} TO {r['grantee']}"
            for r in rows
        )
        psql(stmts + ";", set_role=grantor)
        log(f"  replayed {len(rows)} grants with grantor {grantor}")


# ── steps h+i: generations and snapshots ─────────────────────────────────────

GENERATION_SQL = f"""
WITH chart AS (SELECT * FROM charts WHERE id = {sql_literal(CHART_ID)})
INSERT INTO build_runs (id, chart_id, scope, scope_target, action, state, plan,
                        triggered_by, created_at, started_at, ended_at)
SELECT r.run_id, chart.id, 'asset', r.asset_id, 'build', 'completed',
       '{{"fixture": "l0w7"}}'::jsonb, 'l0w7_fixture', now(), now(), now()
FROM chart, (VALUES ({sql_literal(RUN_GA_POSITIONS)}::uuid, 'ga_positions'),
                    ({sql_literal(RUN_GA_STRUCTURAL)}::uuid, 'ga_structural'),
                    ({sql_literal(RUN_GA_YOGA)}::uuid, 'ga_yoga'),
                    ({sql_literal(RUN_BO_LAKSANA)}::uuid, 'bo_laksana'))
     AS r(run_id, asset_id);

INSERT INTO build_run_assets (run_id, asset_id, position, state, started_at, ended_at)
SELECT run_id, asset_id, 1, 'complete', now(), now()
FROM (VALUES ({sql_literal(RUN_GA_POSITIONS)}::uuid, 'ga_positions'),
             ({sql_literal(RUN_GA_STRUCTURAL)}::uuid, 'ga_structural'),
             ({sql_literal(RUN_GA_YOGA)}::uuid, 'ga_yoga'),
             ({sql_literal(RUN_BO_LAKSANA)}::uuid, 'bo_laksana'))
     AS r(run_id, asset_id);

-- Generations replicate open_l1_data_plane_generation (1035:643-685) exactly:
-- same pins, same base_context_jsonb shape, inserted in empty building state
-- as the generation guard requires.
WITH chart AS (SELECT * FROM charts WHERE id = {sql_literal(CHART_ID)})
INSERT INTO l1_data_plane_generations (
  chart_id, asset_id, generation_id, contract_version,
  l0_semantic_release_id, l0_semantic_release_digest,
  l0_config_generation_id, l0_config_digest, base_context_jsonb,
  expected_partitions
)
SELECT chart.id, r.asset_id, r.run_id::text, {sql_literal(CONTRACT_VERSION)},
  {sql_literal(L0_RELEASE_ID)}, {sql_literal(L0_RELEASE_DIGEST)},
  {sql_literal(L0_CONFIG_ID)}, {sql_literal(L0_CONFIG_DIGEST)},
  jsonb_build_object(
    'subject_id', COALESCE(chart.client_id, chart.owner_id, chart.id::text),
    'chart_id', chart.id::text,
    'build_id', r.run_id::text,
    'generation_id', r.run_id::text,
    'instant_iso', to_char(
      timezone('UTC', timezone(chart.timezone_id, chart.birth_date + chart.birth_time)),
      'YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),
    'latitude_deg', chart.birth_lat,
    'longitude_deg', chart.birth_lng,
    'timezone_name', chart.timezone_id,
    'input_precision', 'postgres_date_plus_time_microsecond',
    'frame', 'sidereal',
    'ayanamsha_id', 'mixed_or_invariant',
    'node_type', 'mean',
    'house_convention', chart.house_system,
    'varga', 'D1',
    'varga_formula', 'writer_row_declared',
    'varga_domain', 'writer_row_declared',
    'karaka_school', 'writer_row_declared',
    'engine_version', r.asset_id,
    'contract_version', {sql_literal(CONTRACT_VERSION)},
    'l0_semantic_release_id', {sql_literal(L0_RELEASE_ID)},
    'l0_semantic_release_digest', {sql_literal(L0_RELEASE_DIGEST)},
    'l0_resource_config_generation_id', {sql_literal(L0_CONFIG_ID)},
    'l0_resource_config_digest', {sql_literal(L0_CONFIG_DIGEST)}
  ), 1
FROM chart, (VALUES ({sql_literal(RUN_GA_POSITIONS)}::uuid, 'ga_positions'),
                    ({sql_literal(RUN_GA_STRUCTURAL)}::uuid, 'ga_structural'))
     AS r(run_id, asset_id);

INSERT INTO l1_data_plane_partition_contexts (chart_id, asset_id, generation_id, partition_key)
SELECT chart_id, asset_id, generation_id, {sql_literal(PARTITION_KEY)}
FROM l1_data_plane_generations
WHERE chart_id = {sql_literal(CHART_ID)};
"""


def snapshot_do_block() -> str:
    """Capture-faithful snapshot synthesis. Every expression mirrors
    l1_data_plane_capture_row (1035:722-962) against the seeded chart_facts
    rows; only the rows listed in v_map are snapshotted (the multi-valued
    dignity row is excluded — a live capture's fact CHECK would reject it).
    """
    return f"""
DO $fixture_snapshots$
DECLARE
  v_map CONSTANT jsonb := '{{
    "f100000000000001": "ga_positions",
    "f100000000000002": "ga_structural",
    "f100000000000003": "ga_structural"
  }}';
  v_partition CONSTANT text := {sql_literal(PARTITION_KEY)};
  v_chart CONSTANT uuid := {sql_literal(CHART_ID)};
  rec RECORD;
  v_asset TEXT;
  v_generation TEXT;
  v_base JSONB;
  v_row JSONB;
  v_identity TEXT;
  v_context JSONB;
  v_context_id TEXT;
  v_semantic JSONB;
  v_digest TEXT;
  v_missingness TEXT;
  v_epistemic TEXT;
  v_deps TEXT[];
  v_dependencies JSONB;
  v_snapshot_id UUID;
  v_value_num NUMERIC;
  v_value_text TEXT;
  v_value_jsonb JSONB;
BEGIN
  FOR rec IN SELECT * FROM public.chart_facts WHERE fact_id IN (SELECT jsonb_object_keys(v_map)) LOOP
    v_asset := v_map ->> rec.fact_id;
    SELECT g.base_context_jsonb, g.generation_id INTO v_base, v_generation
    FROM public.l1_data_plane_generations g
    WHERE g.chart_id = v_chart AND g.asset_id = v_asset;

    v_row := to_jsonb(rec);
    v_identity := 'fact_id=' || rec.fact_id;
    -- Context overrides verbatim from l1_data_plane_capture_row (1035:801-836).
    v_context := v_base || jsonb_build_object(
      'ayanamsha_id', COALESCE(v_row->>'ayanamsha_id', v_base->>'ayanamsha_id'),
      'frame', CASE WHEN lower(COALESCE(v_row->>'ayanamsha_id','')) = 'tropical'
                    THEN 'tropical' ELSE 'sidereal' END,
      'node_type', CASE WHEN upper(v_row::text) ~ '(RAH_TRUE|KET_TRUE|TRUE_NODE)'
                        THEN 'true' ELSE 'mean' END,
      'varga', COALESCE(v_row->>'varga', v_row->>'varga_id', 'D1'),
      'varga_formula', COALESCE(v_row->>'varga_formula', v_row->>'formula_version',
        v_row->>'formula_provenance_text', v_row->>'condition_formula_version', 'not_applicable'),
      'varga_domain', COALESCE(v_row->>'domain', 'row_declared_or_not_applicable'),
      'karaka_school', COALESCE(v_row->>'karaka_school', 'not_applicable'),
      'method_id', COALESCE(v_row->>'system_id', v_row->>'year_lord_method',
        v_row->>'lagna_method', v_row->>'source_calculation', 'not_applicable'),
      'output_precision', COALESCE(v_row->>'tolerance_arcsec', v_row->>'unit', 'schema_declared'),
      'engine_version', COALESCE(v_row->>'engine_version', v_row->>'source_calculation', v_asset)
    );
    v_context_id := 'l1ctx:' || substr(encode(digest(
      ((v_context - 'build_id') - 'generation_id')::text, 'sha256'), 'hex'), 1, 24);
    v_semantic := v_row
      - 'id' - 'snapshot_id' - 'build_id' - 'computed_at' - 'created_at'
      - 'recorded_at' - 'updated_at';
    v_digest := encode(digest(v_semantic::text, 'sha256'), 'hex');
    v_missingness := CASE lower(COALESCE(v_row #>> '{{fact_value_jsonb,state}}', ''))
      WHEN 'method_inapplicable' THEN 'inapplicable'
      WHEN 'unqualified_source' THEN 'unqualified_source'
      WHEN 'failed' THEN 'failed'
      WHEN 'unavailable' THEN 'unavailable'
      WHEN 'unexplored' THEN 'unexplored'
      WHEN 'floored' THEN 'floored'
      ELSE CASE WHEN v_row ? 'fact_value_num' AND v_row->>'fact_value_num' = '0'
                THEN 'zero' ELSE 'present' END
    END;
    v_epistemic := CASE
      WHEN v_asset IN ('ga_positions','ga_nakshatra','ga_panchanga','ga_transit_anchors')
        THEN 'astronomical'
      ELSE 'deterministic_derivation'
    END;
    SELECT depends_on INTO v_deps FROM public.asset_registry WHERE asset_id = v_asset;
    v_dependencies := jsonb_build_object(
      'producer_assets', to_jsonb(COALESCE(v_deps, ARRAY[]::TEXT[])),
      'constituent_fact_ids', '[]'::jsonb
    );

    INSERT INTO public.l1_data_plane_row_snapshots (
      chart_id, asset_id, generation_id, partition_key, source_table,
      row_identity, context_id, calculation_context_jsonb, grain_jsonb,
      source_dependencies_jsonb, epistemic_class, missingness_state,
      verification_class, unit, semantic_payload_jsonb, source_row_jsonb,
      semantic_digest
    ) VALUES (
      v_chart, v_asset, v_generation, v_partition, 'chart_facts',
      v_identity, v_context_id, v_context,
      jsonb_build_object('source_table', 'chart_facts',
                         'natural_key', ARRAY['fact_id=' || rec.fact_id]),
      v_dependencies, v_epistemic, v_missingness,
      COALESCE(v_row->>'verification_pass_status', v_row->>'verification_method', 'unverified'),
      v_row->>'unit', v_semantic, v_row, v_digest
    ) RETURNING snapshot_id INTO v_snapshot_id;

    -- Fact projection (1035:925-962), chart_facts branch, single-valued rows only.
    v_value_num := CASE WHEN v_row->>'fact_value_num' IS NOT NULL
      THEN (v_row->>'fact_value_num')::numeric ELSE NULL END;
    v_value_text := v_row->>'fact_value_text';
    v_value_jsonb := NULLIF(v_row->'fact_value_jsonb', 'null'::jsonb);
    INSERT INTO public.l1_data_plane_fact_snapshots (
      row_snapshot_id, chart_id, asset_id, generation_id, partition_key,
      source_table, row_identity, context_id, fact_identity, fact_category,
      fact_subject, fact_key, grain_jsonb, source_dependencies_jsonb,
      unit, epistemic_class, missingness_state, missingness_reason,
      verification_class, value_num, value_text, value_jsonb
    ) VALUES (
      v_snapshot_id, v_chart, v_asset, v_generation, v_partition,
      'chart_facts', v_identity, v_context_id, rec.fact_id,
      rec.fact_category, rec.fact_subject, rec.fact_key,
      jsonb_build_object(
        'source_table', 'chart_facts', 'row_identity', v_identity,
        'fact_category', rec.fact_category, 'fact_subject', rec.fact_subject,
        'fact_key', rec.fact_key),
      v_dependencies,
      public.l1_data_plane_fact_unit('chart_facts', rec.fact_key, v_row),
      v_epistemic, v_missingness, NULL,
      COALESCE(v_row->>'verification_pass_status', v_row->>'verification_method', 'unverified'),
      v_value_num, v_value_text, v_value_jsonb
    );
  END LOOP;
END
$fixture_snapshots$;
"""


COMPLETE_SQL = f"""
-- Partition receipts, then guarded completion transition, then heads.
INSERT INTO l1_data_plane_generation_partitions
  (chart_id, asset_id, generation_id, partition_key, rows_inserted)
SELECT g.chart_id, g.asset_id, g.generation_id, s.partition_key, count(*)
FROM l1_data_plane_generations g
JOIN l1_data_plane_row_snapshots s
  ON s.chart_id = g.chart_id AND s.asset_id = g.asset_id
 AND s.generation_id = g.generation_id
WHERE g.chart_id = {sql_literal(CHART_ID)}
GROUP BY g.chart_id, g.asset_id, g.generation_id, s.partition_key;

UPDATE l1_data_plane_generations g
SET completed_partitions = 1,
    status = 'complete',
    semantic_output_digest = (
      SELECT encode(digest(string_agg(s.semantic_digest, '|' ORDER BY s.semantic_digest),
                           'sha256'), 'hex')
      FROM l1_data_plane_row_snapshots s
      WHERE s.chart_id = g.chart_id AND s.asset_id = g.asset_id
        AND s.generation_id = g.generation_id),
    completed_at = now()
WHERE g.chart_id = {sql_literal(CHART_ID)};

INSERT INTO l1_data_plane_generation_heads (chart_id, asset_id, current_generation_id)
SELECT chart_id, asset_id, generation_id FROM l1_data_plane_generations
WHERE chart_id = {sql_literal(CHART_ID)};
"""


def step_generations() -> None:
    step("synthesize complete ga_positions + ga_structural generations")
    psql(GENERATION_SQL)
    log("  build_runs(4) + build_run_assets(4) + generations(2) + partition_contexts(2)")
    step("synthesize capture-faithful row/fact snapshots")
    psql(snapshot_do_block())
    psql(COMPLETE_SQL)
    log("  snapshots(3) + fact_snapshots(3) + partitions(2) + heads(2); generations complete")


# ── step k: gates ─────────────────────────────────────────────────────────────

def query_scalar(sql: str) -> str:
    res = psql_tuple(sql)
    return res[0] if res else ""


def psql_tuple(sql: str) -> list[str]:
    cmd = [
        "psql", "-X", "-h", PGHOST, "-p", PGPORT, "-U", SUPERUSER, "-d", FIXTURE_DB,
        "-v", "ON_ERROR_STOP=1", "-qAt", "-c", sql,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise SystemExit(f"gate query failed: {res.stderr}\n{sql[:300]}")
    return [line for line in res.stdout.splitlines() if line]


def gate(name: str, sql: str, expected: str) -> bool:
    got = query_scalar(sql)
    ok = got == expected
    log(f"  {'PASS' if ok else 'FAIL'} {name}: got={got!r} expected={expected!r}")
    return ok


def step_gates() -> None:
    step("gates via pg_catalog (pg_trigger/pg_class/pg_roles)")
    results = []

    results.append(gate(
        "mutation guard on 12 guarded L1 tables",
        "SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid "
        "WHERE t.tgname='l1_data_plane_mutation_guard' AND c.relname IN ("
        + ",".join(sql_literal(t) for t in GUARDED_L1_TABLES) + ")",
        "12"))
    results.append(gate(
        "capture trigger on 11 L1 tables (chart_dashas set-based, intentionally none)",
        "SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid "
        "WHERE t.tgname='l1_data_plane_capture' AND c.relname IN ("
        + ",".join(sql_literal(t) for t in CAPTURE_L1_TABLES) + ")",
        "11"))
    results.append(gate(
        "L2 guard+capture on bodha_msr_signals",
        "SELECT count(*) FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid "
        "WHERE c.relname='bodha_msr_signals' AND t.tgname IN "
        "('l2_data_plane_mutation_guard','l2_data_plane_capture')",
        "2"))
    results.append(gate(
        "L1 admin immutability triggers",
        "SELECT count(*) FROM pg_trigger WHERE tgname IN "
        "('l1_data_plane_partitions_immutable','l1_data_plane_partition_contexts_immutable',"
        "'l1_data_plane_snapshots_immutable','l1_data_plane_facts_immutable',"
        "'l1_data_plane_dashas_immutable','l1_data_plane_configurations_immutable',"
        "'l1_data_plane_generation_immutable')",
        "7"))
    results.append(gate(
        "L1 data-plane admin tables (13 per 1035)",
        "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
        "WHERE n.nspname='public' AND c.relkind='r' AND c.relname LIKE 'l1\\_data\\_plane\\_%'",
        "13"))
    results.append(gate(
        "L2 data-plane admin tables (15 per 1036)",
        "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
        "WHERE n.nspname='public' AND c.relkind='r' AND c.relname LIKE 'l2\\_data\\_plane\\_%'",
        "15"))
    results.append(gate(
        "fixture 27 tables + support/receipt/build tables",
        "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace "
        "WHERE n.nspname='public' AND c.relkind='r' AND c.relname IN ("
        "'asset_output_digest_specs','asset_provenance_receipts','asset_freshness',"
        "'build_runs','build_run_assets')",
        "5"))
    results.append(gate(
        "roles",
        "SELECT count(*) FROM pg_roles WHERE rolname IN "
        "('amjis_app','data_plane_builder','data_plane_verifier','data_plane_migrator',"
        "'data_plane_l1_owner','data_plane_l2_owner','data_plane_schema_owner','role_orchestrator')",
        "8"))
    results.append(gate(
        "fixture FK count (6; charts_client_id_fkey skipped)",
        "SELECT count(*) FROM pg_constraint con JOIN pg_class c ON c.oid=con.conrelid "
        "JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname='public' "
        "AND con.contype='f' AND c.relname IN ("
        "'asset_registry','classical_text_chunks','yoga_families','yoga_family_members',"
        "'chart_divisionals','ga_prashna_judgment')",
        "6"))
    results.append(gate(
        "complete generations + heads",
        "SELECT count(*) FROM l1_data_plane_generations g "
        "JOIN l1_data_plane_generation_heads h ON h.chart_id=g.chart_id "
        "AND h.asset_id=g.asset_id AND h.current_generation_id=g.generation_id "
        "WHERE g.status='complete'",
        "2"))
    results.append(gate(
        "row snapshots / fact snapshots",
        "SELECT (SELECT count(*) FROM l1_data_plane_row_snapshots) || '/' || "
        "(SELECT count(*) FROM l1_data_plane_fact_snapshots)",
        "3/3"))
    results.append(gate(
        "reference data rows (512)",
        "SELECT (SELECT count(*) FROM asset_registry) + (SELECT count(*) FROM brahma_yoga_catalog) + "
        "(SELECT count(*) FROM brahma_dosha_catalog) + (SELECT count(*) FROM sutravali_rules) + "
        "(SELECT count(*) FROM classical_texts) + (SELECT count(*) FROM classical_text_chunks) + "
        "(SELECT count(*) FROM fact_category_ownership)",
        "512"))
    results.append(gate(
        "seeded data rows",
        "SELECT (SELECT count(*) FROM charts) || '/' || (SELECT count(*) FROM chart_facts) || '/' || "
        "(SELECT count(*) FROM ga_yoga_firings) || '/' || (SELECT count(*) FROM chart_vichara) || '/' || "
        "(SELECT count(*) FROM bodha_msr_signals)",
        "1/7/1/2/1"))

    # Negative gate: the mutation guard must reject a non-builder write.
    res = psql("INSERT INTO chart_facts (fact_id, chart_id, ayanamsha_id, build_id, "
               "fact_category, fact_subject, fact_key, citation_ref, citation_human, "
               "source_calculation, verification_pass_status, engine_version, computed_at) "
               "VALUES ('guardprobe', 'f0000000-0000-4000-8000-000000000001'::uuid, 'x', NULL, "
               "'c','s','k','r','h','s','v','e', now());",
               expect_fail=True)
    guard_ok = "data_plane_builder" in res.stderr
    log(f"  {'PASS' if guard_ok else 'FAIL'} mutation guard rejects non-builder chart_facts write")
    results.append(guard_ok)

    if not all(results):
        raise SystemExit(f"GATES FAILED: {results.count(False)} of {len(results)}")
    log(f"all {len(results)} gates green")


# ── step l: summary ───────────────────────────────────────────────────────────

def step_summary() -> None:
    step("seed manifest summary")
    manifest = json.loads((SEED_DIR / "seed_manifest.json").read_text())
    for t in manifest["tables"]:
        log(f"  {t['table']:<28} {t['row_count']:>4} rows  sha256:{t['sha256'][:16]}…  [{t['filter']}]")
    log(f"fixture database {FIXTURE_DB} on {PGHOST}:{PGPORT} is ready")


def main() -> None:
    step_recreate_db()          # a
    step_schema_roles()         # b
    step_reference_data()       # c
    step_data_seeds()           # d (+ j, pre-trigger by design — see REHEARSAL_NOTES)
    step_grants()               # f/g — before migrations: every grants.json table
                                # is a pre-migration fixture table, and production's
                                # grants (e.g. SELECT on asset_registry to the owner
                                # roles) predated 1035/1036, whose preflights read them
    step_migrations()           # e
    step_generations()          # h + i
    step_gates()                # k
    step_summary()              # l
    log("BUILD GREEN")


if __name__ == "__main__":
    main()
