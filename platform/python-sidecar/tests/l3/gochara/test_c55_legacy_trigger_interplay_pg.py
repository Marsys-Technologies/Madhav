"""C55 (F-R16-5b) — migration 1071's legacy generation guard beside 1240's boundary guards, on the REAL legacy relations.

The question this answers (steward ST-KIMI-MONTHLY-LIMIT-B, C55): on a database that carries the real legacy relations, 1071's own
triggers on `kala_gochara_windows` AND 1240's governed-generation boundary triggers on the four legacy relations
(`kala_gochara_coverage`, `kala_gochara_publication`, `kala_gochara_contacts`, `kala_gochara_windows`) both fire on the same statement.
For every (relation x operation x chart x generation x isolation level) the test records WHICH guard answered and with WHICH refusal,
as the real non-owner builder login (`data_plane_builder`, LOGIN granted for the test only), and asserts the behaviour it observed.
The behaviour table is printed at the end of the module (and written to $C55_BEHAVIOUR_TABLE when that is set).

What is REAL and what is a stand-in (the test says so rather than letting the green read as more than it is):
  REAL    migrations 460, 461, 1071 (the fresh-database path: its own triggers, not the production `trg_kgw_*` pair), 1081, 1152, 1153-1157,
          1204, 1206, 1232, 1233, 1240, and the builder grants 1216 / 1220 / 1234 / 1237 / 1242 — applied verbatim in migration order, as
          a faithful mirror (builder / verifier / sealer principals exist when the migrations run; PUBLIC EXECUTE revoked by default).
  STAND-IN `kala_gochara_windows.generation` — no migration in this repository adds the column (production got it from the cutover
          script, 1071's own header says so), so the test adds `generation text NOT NULL DEFAULT 'v1'`; `asset_registry` (460 INSERTs into
          it) is a permissive stub; `charts`/`chart_facts`/`chart_dashas`/`bg_transit_rules` are the same minimal stubs the A5.3 tests use.
  NOT COVERED production's stricter `trg_kgw_generation_guard_*` pair (installed by the cutover script; 1071 skips when it is bound) —
          its function body is not in the repository, so it is not mirrored here; and SEALED generations (no seal is created).

Runs only against a throwaway database on a loopback server (the shared disposable-DB guard); with GOCHARA_A53_REQUIRE_DB=1 an
unreachable server is a failure, otherwise NOT_RUN (skipped), never a pass.
"""
from __future__ import annotations

import os
import re
import uuid
from contextlib import contextmanager
from pathlib import Path

import pytest

from ._disposable_db_guard import UnsafeAdminDSN, guarded_admin_connect
from .test_a53_record_store import ADMIN_DSN, DB_PREFIX, MIGRATIONS

CANON = "482012f1-710e-4a25-994a-93821f5871aa"
OTHER = "00000000-0000-4000-8000-0000000c5500"
RC, RR = "READ COMMITTED", "REPEATABLE READ"
BUILDER = "data_plane_builder"
BUILDER_PASSWORD = "c55-disposable-only"
LEGACY_WINDOW_GENS = ("v1", "3.0", "4.0")
RELATIONS = ("kala_gochara_windows", "kala_gochara_contacts", "kala_gochara_coverage", "kala_gochara_publication")

# real migration order (numeric); 1071 is the generation guard, 1240 the boundary
CHAIN = (
    "460_kala_gochara_windows.sql",
    "461_kala_gochara_windows_continuity_state.sql",
    "1071_kala_gochara_windows_generation_guard.sql",
    "1081_nirmana_l3_gochara_ledger_coverage_publication.sql",
    "1152_kala_gochara_contacts_t_exact_nullable_truncated.sql",
    "1153_gochara_sky_event_substrate.sql",
    "1154_gochara_rule_path_registry.sql",
    "1155_gochara_relationship_record.sql",
    "1156_gochara_eval_window.sql",
    "1157_gochara_av_polarity_declaration.sql",
    "1204_gochara_av_qualifier_object_role.sql",
    "1206_gochara_search_inventory_completeness.sql",
    "1232_gochara_search_moon_scope_domain.sql",
    "1233_gochara_p1_period_anchor.sql",
    "1240_gochara_window_verification_gate.sql",
    "1216_gochara_contract_builder_grants.sql",
    "1220_gochara_contract_builder_function_execute.sql",
    "1234_gochara_eval_window_builder_grants.sql",
    "1237_kala_gochara_windows_builder_grant_record.sql",
    "1242_gochara_builder_record_replace_finalise_grants.sql",
)

# which guard answered, by the text of the refusal (first match wins)
GUARDS = (
    ("1071-row-guard", "BUILD-PROTECTED: kala_gochara_windows generation='v1'"),
    ("1071-truncate-guard", "BUILD-PROTECTED: kala_gochara_windows cannot be TRUNCATEd"),
    ("1240-truncate-needs-RC", "boundary_truncate_requires_read_committed"),
    ("1240-truncate-governed-rows", "TRUNCATE while governed-generation rows exist"),
    ("1240-sealed-boundary", "refused (sealed boundary"),
    ("1240>lock:D-SCOPE", "is not governed by the Gochara-5 contract"),
    ("1240>lock:needs-RC", "ka_gochara writes require READ COMMITTED"),
    ("fk-violation", "violates foreign key constraint"),
    ("privilege", "permission denied"),
    ("fk-truncate", "cannot truncate a table referenced in a foreign key constraint"),
)


# ── the database ─────────────────────────────────────────────────────────────

def _connect_admin():
    psycopg = pytest.importorskip("psycopg")
    try:
        return guarded_admin_connect(ADMIN_DSN, autocommit=True, connect_timeout=3)
    except UnsafeAdminDSN:
        raise                                   # a hostile admin DSN is a configuration ERROR, never a skip
    except Exception as exc:  # noqa: BLE001
        if os.environ.get("GOCHARA_A53_REQUIRE_DB") == "1":
            pytest.fail(f"GOCHARA_A53_REQUIRE_DB=1 but the disposable database server is unreachable ({exc})")
        pytest.skip(f"NOT_RUN: disposable database server unreachable ({exc})")


def _apply_stubs_and_chain(conn):
    conn.execute("CREATE TABLE public.charts (id uuid PRIMARY KEY)")
    conn.execute("CREATE TABLE public._migrations_applied (filename text PRIMARY KEY, applied_at timestamptz DEFAULT now(),"
                 " sha256 text NOT NULL DEFAULT repeat('0', 64))")
    conn.execute("CREATE TABLE public.chart_facts (fact_id text PRIMARY KEY, chart_id uuid, ayanamsha_id text, fact_category text,"
                 " fact_subject text, fact_key text, fact_value_num double precision,"
                 " verification_pass_status text NOT NULL DEFAULT 'single', created_at timestamptz DEFAULT now())")
    conn.execute("CREATE TABLE public.chart_dashas (dasha_row_id uuid PRIMARY KEY, chart_id uuid, ayanamsha_id text, system_id text,"
                 " level_n int, parent_row_id uuid, lord_graha text, start_iso timestamptz, end_iso timestamptz, build_id uuid,"
                 " verification_pass_status text, computed_at timestamptz DEFAULT now())")
    conn.execute("CREATE TABLE public.bg_transit_rules (id SERIAL PRIMARY KEY, rule_type TEXT NOT NULL, graha TEXT NOT NULL,"
                 " primary_house INTEGER NOT NULL, vedha_house INTEGER, phala TEXT NOT NULL, classical_citation TEXT NOT NULL,"
                 " rule_notes TEXT, UNIQUE (graha, rule_type, primary_house))")
    # 460 INSERTs the ka_gochara_sweep registry row: a permissive stub of exactly the columns it writes
    conn.execute("CREATE TABLE public.asset_registry (asset_id text PRIMARY KEY, layer text, sort_order int, sanskrit_name text,"
                 " english_name text, english_description text, storage_type text, target_table text, count_sql text, size_sql text,"
                 " target_floor int, scope text, is_active boolean, has_writer boolean, has_substeps boolean,"
                 " writer_timeout_seconds int, layer_name text, layer_index text, catalog_status text, depends_on text[])")
    for fname in CHAIN:
        path = MIGRATIONS / fname
        if not path.exists():
            pytest.fail(f"{fname} is not in platform/migrations: this test applies the REAL migrations")
        if fname.startswith("1071_"):
            # the column production's cutover script added (no repository migration does) — the guard reads OLD.generation
            conn.execute("ALTER TABLE public.kala_gochara_windows ADD COLUMN IF NOT EXISTS generation text NOT NULL DEFAULT 'v1'")
        conn.execute(path.read_text())
        conn.execute("INSERT INTO public._migrations_applied(filename) VALUES (%s)", (fname,))


@pytest.fixture(scope="module")
def world():
    import psycopg
    from psycopg.conninfo import make_conninfo
    admin = _connect_admin()
    name = f"{DB_PREFIX}c55_{uuid.uuid4().hex[:8]}"
    admin.execute("DO $$ BEGIN"
                  " IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_builder') THEN CREATE ROLE data_plane_builder NOLOGIN; END IF;"
                  " IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gochara_verifier') THEN CREATE ROLE gochara_verifier NOLOGIN; END IF;"
                  " IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gochara_sealer') THEN CREATE ROLE gochara_sealer NOLOGIN; END IF;"
                  " END $$")
    admin.execute(f'CREATE DATABASE "{name}"')
    dsn = make_conninfo(ADMIN_DSN, dbname=name)
    owner = None
    try:
        owner = psycopg.connect(dsn, autocommit=True, connect_timeout=3)
        owner.execute("ALTER DEFAULT PRIVILEGES REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC")
        _apply_stubs_and_chain(owner)
        owner.execute("INSERT INTO public.charts(id) VALUES (%s), (%s)", (CANON, OTHER))
        _seed(owner)
        admin.execute(f"ALTER ROLE {BUILDER} LOGIN PASSWORD '{BUILDER_PASSWORD}'")
        builder = psycopg.connect(make_conninfo(dsn, user=BUILDER, password=BUILDER_PASSWORD), autocommit=True, connect_timeout=3)
        table = []
        held = {(rel, p): owner.execute("SELECT has_table_privilege(%s, %s, %s)", (BUILDER, f"public.{rel}", p)).fetchone()[0]
                for rel in RELATIONS for p in ("INSERT", "UPDATE", "DELETE", "TRUNCATE")}
        yield type("World", (), {"owner": owner, "builder": builder, "dsn": dsn, "table": table, "held": held})
        builder.close()
        _emit_table(table)
    finally:
        try:
            admin.execute(f"ALTER ROLE {BUILDER} NOLOGIN PASSWORD NULL")
        finally:
            if owner is not None:
                owner.close()
            assert name.startswith(DB_PREFIX), name                 # never drop what we did not create
            admin.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
            admin.close()



# ── seed rows (replica role: the guards under test do not fire while seeding) ──────────────────────────────────────────────

CONV = "sha256:" + "c5" * 32
MANIFEST = {("canon", "4.0"): "00000000-0000-4000-8000-0000000c5501", ("canon", "5.0"): "00000000-0000-4000-8000-0000000c5502",
            ("other", "4.0"): "00000000-0000-4000-8000-0000000c5503", ("other", "5.0"): "00000000-0000-4000-8000-0000000c5504"}
CHART_OF = {"canon": CANON, "other": OTHER}


def _publication_row(conn, who, gen):
    conn.execute(
        "INSERT INTO public.kala_gochara_publication (manifest_id, chart_id, generation, writer_asset_id, convention_id,"
        " input_generation_vector, ephemeris_backend, horizon, row_counts, content_digest, status)"
        " VALUES (%s, %s, %s, 'ka_gochara', %s, '{}'::jsonb, '{}'::jsonb,"
        " tstzrange('2025-01-01+00', '2025-03-01+00'), '{}'::jsonb, 'x', 'candidate')",
        (MANIFEST[(who, gen)], CHART_OF[who], gen, CONV))


CONTACT_SQL = ("INSERT INTO public.kala_gochara_contacts (chart_id, generation, contact_id, independence_group, body, relation, aspect_deg,"
               " target_type, target_ref, target_resolution_state, t_in, t_exact, t_out, bracket_seconds, tolerance_arcsec, branch,"
               " orb_max_deg, orb_source, epistemic_class, completeness_state, operator_role, precision_regime, time_basis,"
               " comparable_with, convention_id, ephemeris_backend, input_generation_vector_id, build_id, computed_at)"
               " VALUES (%s, %s, %s, 'g', 'Saturn', 'conjunction', 0, 'graha', 'Sun', 'resolved', now(), now(), now(), 1, 1, 'direct',"
               " 1, 'o', 'e', 'c', 'r', 'p', 't', 'self', %s, '{}'::jsonb, %s, 'b', now())")
COVERAGE_SQL = ("INSERT INTO public.kala_gochara_coverage (chart_id, generation, partition_kind, partition_key, convention_id,"
                " requested_horizon, completed_horizon, resolution, relations_searched, targets_requested, targets_resolved,"
                " targets_unresolved, target_resolution_state_counts, build_id)"
                " VALUES (%s, %s, 'event_class', %s, %s, tstzrange('2025-01-01+00', '2025-03-01+00'),"
                " tstzrange('2025-01-01+00', '2025-03-01+00'), 1, ARRAY['conjunction'], 1, 1, 0, '{}'::jsonb, 'b')")
# the windows natural key (chart, event_class, window_start, peak_date, milestone) does NOT include the generation: one event_class per generation
WINDOW_SQL = ("INSERT INTO public.kala_gochara_windows (chart_id, event_class, temporal_shape, window_start, window_end, peak_date,"
              " signed_intensity, raw_intensity, valence, is_adverse, generation)"
              " VALUES (%s, %s, 'point', %s::date, %s::date, %s::date, 1, 1, 'gain', false, %s)")


@contextmanager
def replica(conn):
    """One transaction under session_replication_role = replica: no trigger of the migrations under test (and no FK) fires."""
    conn.execute("BEGIN")
    try:
        conn.execute("SET LOCAL session_replication_role = replica")
        yield conn
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise


def _seed_governed(c, with_other_publication=False):
    for who in ("canon", "other"):
        if who == "canon" or with_other_publication:
            _publication_row(c, who, "5.0")
        c.execute(CONTACT_SQL, (CHART_OF[who], "5.0", f"sha256:seed-{who}-5.0", CONV, MANIFEST[(who, "5.0")]))
        c.execute(COVERAGE_SQL, (CHART_OF[who], "5.0", "seed", CONV))
        c.execute(WINDOW_SQL, (CHART_OF[who], "seed_5.0", "2025-01-01", "2025-01-02", "2025-01-01", "5.0"))


def _seed(owner):
    owner.execute(f"INSERT INTO public.kala_gochara_convention (convention_id, zodiac, ayanamsha, sidereal_method, node_model, node_source,"
                  f" epoch_convention, time_scale, house_system, ephemeris_mode, method_version)"
                  f" VALUES ('{CONV}', 'sidereal', 'lahiri', 'm', 'mean', 's', 'e', 'ut', 'whole_sign', 'swiss', '1')")
    with replica(owner) as c:
        for who in ("canon", "other"):
            _publication_row(c, who, "4.0")
            c.execute(CONTACT_SQL, (CHART_OF[who], "4.0", f"sha256:seed-{who}-4.0", CONV, MANIFEST[(who, "4.0")]))
            c.execute(COVERAGE_SQL, (CHART_OF[who], "4.0", "seed", CONV))
            for gen in ("v1", "3.0", "4.0"):
                c.execute(WINDOW_SQL, (CHART_OF[who], f"seed_{gen}", "2025-01-01", "2025-01-02", "2025-01-01", gen))
        # base state: governed rows in every relation for BOTH charts — except a governed MANIFEST of the other chart (its effect is its own test)
        _seed_governed(c, with_other_publication=False)


# ── the observation primitive ────────────────────────────────────────────────

def _guard_of(message: str) -> str:
    for label, needle in GUARDS:
        if needle in message:
            return label
    return "other"


def attempt(conn, statement, params=(), iso=RC, setup=()):
    """Run ONE statement in a transaction that is ALWAYS rolled back. Returns (verdict, guard, detail)."""
    import psycopg
    conn.execute(f"BEGIN ISOLATION LEVEL {iso}")
    try:
        for s in setup:
            conn.execute(s)
        cur = conn.execute(statement, params)
        return ("OK", "-", f"{cur.rowcount} row(s)")
    except psycopg.Error as exc:
        msg = str(exc).strip().splitlines()[0]
        return ("REFUSED", _guard_of(str(exc)), f"{exc.sqlstate}: {msg[:150]}")
    finally:
        conn.execute("ROLLBACK")


SHORT = {r: r.replace("kala_gochara_", "") for r in RELATIONS}
_fresh = iter(range(1, 10 ** 6))


def _gens(rel):
    return LEGACY_WINDOW_GENS + ("5.0",) if rel == "kala_gochara_windows" else ("4.0", "5.0")


def _statement(rel, op, who, gen):
    chart = CHART_OF[who]
    if op == "INSERT":
        n = next(_fresh)
        if rel == "kala_gochara_windows":
            d = f"2030-{(n % 12) + 1:02d}-{(n % 27) + 1:02d}"
            return WINDOW_SQL, (chart, f"c55_{n}", d, d, d, gen)
        if rel == "kala_gochara_contacts":
            return CONTACT_SQL, (chart, gen, f"sha256:new-{n}", CONV, MANIFEST[(who, gen)])
        if rel == "kala_gochara_coverage":
            return COVERAGE_SQL, (chart, gen, f"new_{n}", CONV)
        # a manifest is unique per (chart, generation): the NEW key is generation '<major>.<n>' — same major, so same governed/legacy side
        return ("INSERT INTO public.kala_gochara_publication (chart_id, generation, writer_asset_id, convention_id, input_generation_vector,"
                " ephemeris_backend, horizon, row_counts, content_digest, status) VALUES (%s, %s, 'ka_gochara', %s, '{}'::jsonb, '{}'::jsonb,"
                " tstzrange('2025-01-01+00', '2025-03-01+00'), '{}'::jsonb, 'x', 'candidate')", (chart, f"{gen.split('.')[0]}.{900 + n}", CONV))
    if op == "UPDATE":
        col = {"kala_gochara_windows": "valence", "kala_gochara_contacts": "build_id", "kala_gochara_coverage": "build_id",
               "kala_gochara_publication": "content_digest"}[rel]
        return f"UPDATE public.{rel} SET {col} = {col} WHERE chart_id = %s AND generation = %s", (chart, gen)
    return f"DELETE FROM public.{rel} WHERE chart_id = %s AND generation = %s", (chart, gen)


def expected(held, actor, rel, op, who, gen, iso, has_governed_publication=True):
    """The behaviour read from the migrations' text — each branch names the code that produces it."""
    governed = gen == "5.0"
    if actor == "builder" and not held[(rel, op)]:
        return "privilege"                                   # the builder's REAL table ACL (read from the database) answers before any trigger
    if rel == "kala_gochara_windows" and gen == "v1" and op in ("UPDATE", "DELETE"):
        return "1071-row-guard"                              # 1071's row guard (BEFORE DELETE/UPDATE) — 1240's regex skips 'v1', every isolation level
    if rel == "kala_gochara_publication" and op in ("UPDATE", "DELETE") and has_governed_publication and iso == RR:
        return "1240>lock:needs-RC"                          # the publication STATEMENT lock walks every governed manifest, whatever rows are touched
    if governed and iso == RR:
        return "1240>lock:needs-RC"                          # a governed row's write calls ka_gochara_lock_chart, which refuses outside READ COMMITTED
    if governed and who == "other":
        return "1240>lock:D-SCOPE"                           # …and refuses a non-canonical chart (1153 D-SCOPE) — INSERT, UPDATE and DELETE alike
    if rel == "kala_gochara_publication" and op == "DELETE":
        return "fk-violation"                                # the guard passed; the contacts' foreign key to the manifest then refuses the delete
    return "-"                                               # allowed (unsealed canonical governed write, or any legacy generation)


@pytest.fixture(scope="module")
def matrix(world):
    """Every (actor x relation x operation x chart x generation x isolation) case, observed once; the tests below assert on it."""
    out = {}
    for actor, conn in (("builder", world.builder), ("owner", world.owner)):
        for rel in RELATIONS:
            for who in ("canon", "other"):
                for gen in _gens(rel):
                    for op in ("INSERT", "UPDATE", "DELETE"):
                        for iso in (RC, RR):
                            if iso == RR and op == "DELETE" and rel != "kala_gochara_publication":
                                continue                     # RR matters for UPDATE (and the publication statement lock); DELETE adds no new branch
                            if rel == "kala_gochara_publication" and who == "other" and gen == "5.0" and op != "INSERT":
                                continue                     # no such manifest in the base state (its own test below)
                            sql, params = _statement(rel, op, who, gen)
                            r = attempt(conn, sql, params, iso=iso)
                            out[(actor, rel, op, who, gen, iso)] = r
                            world.table.append((SHORT[rel], op, who, gen, iso, r[0], r[1], r[2], actor))
    return out


# ── 0. the stage is what we say it is ───────────────────────────────────────

def test_the_stage_has_the_real_guards_of_both_migrations(world):
    c = world.owner
    names = {r[0] for r in c.execute(
        "SELECT t.tgname FROM pg_trigger t WHERE t.tgrelid = 'public.kala_gochara_windows'::regclass AND NOT t.tgisinternal").fetchall()}
    # 1071's own fresh-path pair AND 1240's pair — and NOT production's trg_kgw_* pair (this is the fresh-database path)
    assert {"trg_kala_gochara_windows_generation_guard_row", "trg_kala_gochara_windows_generation_guard_truncate",
            "ka_gochara_boundary_1_write_guard", "ka_gochara_boundary_2_no_truncate"} <= names, names
    assert not {n for n in names if n.startswith("trg_kgw_")}
    inv = {r[0]: r[1:] for r in c.execute("SELECT * FROM public.ka_gochara_boundary_guard_inventory()").fetchall()}
    assert inv == {r: (True, True, True) for r in RELATIONS}, inv
    # the builder is the non-owner, non-superuser login the matrix runs as
    assert world.builder.execute("SELECT current_user, (SELECT rolsuper FROM pg_roles WHERE rolname = current_user)").fetchone() == (BUILDER, False)
    assert world.builder.execute("SELECT pg_get_userbyid(relowner) FROM pg_class WHERE oid = 'public.kala_gochara_windows'::regclass"
                                 ).fetchone()[0] != BUILDER
    # the seed: every (relation x chart x generation) the matrix reads exists, so a zero-row UPDATE can never read as a pass
    for rel in RELATIONS:
        for who in ("canon", "other"):
            for gen in _gens(rel):
                if rel == "kala_gochara_publication" and who == "other" and gen == "5.0":
                    continue
                n = c.execute(f"SELECT count(*) FROM public.{rel} WHERE chart_id = %s AND generation = %s", (CHART_OF[who], gen)).fetchone()[0]
                assert n >= 1, (rel, who, gen)


def test_the_builders_real_privileges_are_what_decides_which_cases_the_builder_can_even_reach(world):
    held = {}
    for rel in RELATIONS:
        for priv in ("INSERT", "UPDATE", "DELETE", "TRUNCATE"):
            held[(SHORT[rel], priv)] = world.owner.execute("SELECT has_table_privilege(%s, %s, %s)", (BUILDER, f"public.{rel}", priv)).fetchone()[0]
    world.table.append(("(privileges)", "builder holds", "-", "-", "-", "INFO", "-",
                        ", ".join(f"{k[0]}.{k[1]}={'Y' if v else 'n'}" for k, v in held.items()), "builder"))
    assert all(not v for (rel, p), v in held.items() if p == "TRUNCATE"), held        # TRUNCATE is owner-only in this deployment
    assert all(held[("windows", p)] for p in ("INSERT", "UPDATE", "DELETE")), held        # 1237 records production's arwd on the legacy windows table
    assert all(held[(r, "INSERT")] for r in ("contacts", "coverage", "publication")), held


# ── 1. the matrix ───────────────────────────────────────────────────────────

def test_every_case_is_answered_by_the_guard_the_migrations_text_says(world, matrix):
    wrong = []
    for (actor, rel, op, who, gen, iso), (verdict, guard, detail) in sorted(matrix.items()):
        want = expected(world.held, actor, rel, op, who, gen, iso)
        got = "-" if verdict == "OK" else guard
        if got != want:
            wrong.append(f"{actor} {SHORT[rel]} {op} chart={who} gen={gen} {iso}: expected {want!r}, observed {got!r} ({detail})")
    assert not wrong, "\n".join(wrong)


def test_a_legacy_generation_is_never_refused_by_a_governed_generation_guard_except_through_the_publication_statement_lock(matrix):
    for (actor, rel, op, who, gen, iso), (verdict, guard, detail) in matrix.items():
        if gen == "5.0" or verdict == "OK":
            continue
        assert guard in ("privilege", "1071-row-guard", "fk-violation") or (
            rel == "kala_gochara_publication" and op in ("UPDATE", "DELETE") and guard == "1240>lock:needs-RC"), \
            (actor, rel, op, who, gen, iso, guard, detail)


def test_only_the_v1_snapshot_of_the_windows_table_is_answered_by_1071_and_both_charts_alike(matrix):
    answered = {k for k, v in matrix.items() if v[1] == "1071-row-guard"}
    assert answered and all(k[1] == "kala_gochara_windows" and k[4] == "v1" and k[2] in ("UPDATE", "DELETE") for k in answered), answered
    for who in ("canon", "other"):
        for actor in ("builder", "owner"):
            assert matrix[(actor, "kala_gochara_windows", "UPDATE", who, "v1", RC)][1] == "1071-row-guard"
            assert matrix[(actor, "kala_gochara_windows", "INSERT", who, "v1", RC)][0] == "OK"      # 1071 never gates INSERT


def test_a_governed_write_of_the_other_chart_is_refused_by_1240_through_the_chart_lock_on_every_relation_and_operation(matrix):
    for rel in RELATIONS:
        for op in ("INSERT", "UPDATE", "DELETE"):
            if rel == "kala_gochara_publication" and op != "INSERT":
                continue
            for actor in ("builder", "owner"):
                if actor == "builder" and rel != "kala_gochara_windows" and op != "INSERT":
                    continue
                got = matrix[(actor, rel, op, "other", "5.0", RC)]
                assert got[:2] == ("REFUSED", "1240>lock:D-SCOPE"), (actor, rel, op, got)


# ── 2. the 1071 override, and relabelling ───────────────────────────────────

def test_the_1071_override_opens_only_1071_and_never_a_governed_refusal(world):
    on = ("SET LOCAL app.allow_protected_sweep_rewrite = 'on'",)
    upd = "UPDATE public.kala_gochara_windows SET valence = valence WHERE chart_id = %s AND generation = %s"
    r = attempt(world.builder, upd, (CANON, "v1"), setup=on)
    world.table.append(("windows", "UPDATE + override", "canon", "v1", RC, *r, "builder"))
    assert r[0] == "OK", r                                      # the native-authorised override still opens the v1 snapshot
    r = attempt(world.builder, upd, (OTHER, "5.0"), setup=on)
    world.table.append(("windows", "UPDATE + override", "other", "5.0", RC, *r, "builder"))
    assert r[:2] == ("REFUSED", "1240>lock:D-SCOPE"), r         # the override is 1071's GUC: it does not reach 1240's refusal
    # relabelling a v1 row into the governed range: 1240 lets the NEW side through for the canonical chart, 1071 then refuses the OLD side
    r = attempt(world.builder, "UPDATE public.kala_gochara_windows SET generation = '5.0' WHERE chart_id = %s AND generation = 'v1'", (CANON,))
    world.table.append(("windows", "UPDATE relabel v1 -> 5.0", "canon", "v1->5.0", RC, *r, "builder"))
    assert r[:2] == ("REFUSED", "1071-row-guard"), r
    r = attempt(world.builder, "UPDATE public.kala_gochara_windows SET generation = '5.0' WHERE chart_id = %s AND generation = '3.0'", (OTHER,))
    world.table.append(("windows", "UPDATE relabel 3.0 -> 5.0", "other", "3.0->5.0", RC, *r, "builder"))
    assert r[:2] == ("REFUSED", "1240>lock:D-SCOPE"), r         # the NEW side is governed and not canonical
    r = attempt(world.builder, "UPDATE public.kala_gochara_windows SET generation = '3.0' WHERE chart_id = %s AND generation = '5.0'", (OTHER,))
    world.table.append(("windows", "UPDATE relabel 5.0 -> 3.0", "other", "5.0->3.0", RC, *r, "builder"))
    assert r[:2] == ("REFUSED", "1240>lock:D-SCOPE"), r         # the OLD side is governed: relabelling a governed row OUT is guarded too


# ── 3. a governed manifest of another chart ─────────────────────────────────

def test_a_governed_manifest_of_another_chart_blocks_every_publication_update_and_delete_even_the_canonical_legacy_ones(world):
    """1240's own concurrency note: the publication STATEMENT trigger locks the chart of EVERY governed manifest, and the lock refuses a
    non-canonical chart — so while an (OTHER, '5.0') manifest exists, an UPDATE of an ordinary (CANON, '4.0') manifest is refused too."""
    c = world.owner
    upd = "UPDATE public.kala_gochara_publication SET content_digest = content_digest WHERE chart_id = %s AND generation = '4.0'"
    before = attempt(c, upd, (CANON,))
    assert before[0] == "OK", before                                       # base state: no non-canonical governed manifest
    with replica(c) as r:
        _publication_row(r, "other", "5.0")
    try:
        with_other = attempt(c, upd, (CANON,))
        also_zero_rows = attempt(c, "UPDATE public.kala_gochara_publication SET content_digest = content_digest WHERE false")
        also_delete = attempt(c, "DELETE FROM public.kala_gochara_publication WHERE false")
        also_legacy_chart = attempt(c, upd, (OTHER,))
    finally:
        with replica(c) as r:
            r.execute("DELETE FROM public.kala_gochara_publication WHERE chart_id = %s AND generation = '5.0'", (OTHER,))
    for label, res in (("UPDATE canon 4.0", with_other), ("UPDATE ... WHERE false (no row touched)", also_zero_rows),
                       ("DELETE ... WHERE false (no row touched)", also_delete), ("UPDATE other 4.0", also_legacy_chart)):
        world.table.append(("publication", label + " [other-chart 5.0 manifest present]", "-", "4.0", RC, *res, "owner"))
        assert res[:2] == ("REFUSED", "1240>lock:D-SCOPE"), (label, res)
    after = attempt(c, upd, (CANON,))
    assert after[0] == "OK", after                                          # restored: the same statement passes again


# ── 4. TRUNCATE ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("rel", RELATIONS)
def test_the_builder_cannot_truncate_any_legacy_relation(world, rel):
    r = attempt(world.builder, f"TRUNCATE public.{rel}")
    world.table.append((SHORT[rel], "TRUNCATE", "-", "-", RC, *r, "builder"))
    assert r[:2] == ("REFUSED", "privilege"), r


def _truncate_expectation(rel, state, iso, override=False):
    if rel in ("kala_gochara_coverage", "kala_gochara_publication"):
        return "fk-truncate"                                  # PostgreSQL refuses a TRUNCATE of a referenced table before ANY trigger fires
    if iso == RR:
        return "1240-truncate-needs-RC"                       # 1240 refuses to decide outside READ COMMITTED — even with no governed row at all
    if state == "governed":
        return "1240-truncate-governed-rows"
    if rel == "kala_gochara_windows" and not override:
        return "1071-truncate-guard"                          # a legacy-only table passes 1240; 1071's statement guard then refuses
    return "-"


def test_truncate_by_the_owner_which_guard_answers_by_state_and_isolation_level(world):
    c = world.owner
    refs = c.execute("SELECT DISTINCT conrelid::regclass::text, confrelid::regclass::text FROM pg_constraint "
                     "WHERE contype = 'f' AND confrelid IN ('public.kala_gochara_coverage'::regclass, 'public.kala_gochara_publication'::regclass)"
                     ).fetchall()
    world.table.append(("(foreign keys)", "referenced by", "-", "-", "-", "INFO", "-", "; ".join(f"{a} -> {b}" for a, b in sorted(refs)), "owner"))
    assert any(b == "kala_gochara_coverage" for a, b in refs) and any(b == "kala_gochara_publication" for a, b in refs), refs

    def run(state, rels):
        for rel in rels:
            for iso in (RC, RR):
                r = attempt(c, f"TRUNCATE public.{rel}", iso=iso)
                world.table.append((SHORT[rel], f"TRUNCATE ({state} rows)", "-", "-", iso, *r, "owner"))
                want = _truncate_expectation(rel, state, iso)
                assert ("-" if r[0] == "OK" else r[1]) == want, (state, rel, iso, r)

    run("governed", RELATIONS)
    # the only-legacy state: remove the governed rows (replica role: the guards under test are skipped), observe, restore
    with replica(c) as r:
        for rel in RELATIONS:
            r.execute(f"DELETE FROM public.{rel} WHERE generation ~ '^([5-9]|[1-9][0-9]+)\\.[0-9]+$'")
    try:
        run("legacy-only", RELATIONS)
        r = attempt(c, "TRUNCATE public.kala_gochara_windows", setup=("SET LOCAL app.allow_protected_sweep_rewrite = 'on'",))
        world.table.append(("windows", "TRUNCATE + override (legacy-only rows)", "-", "-", RC, *r, "owner"))
        assert r[0] == "OK", r                                  # the 1071 override opens 1071 only; 1240 had already let a legacy-only table through
    finally:
        with replica(c) as r:
            _seed_governed(r)
    for rel in RELATIONS:                                        # restored
        assert c.execute(f"SELECT count(*) FROM public.{rel} WHERE generation = '5.0'").fetchone()[0] >= 1, rel


def test_truncate_cascade_from_the_referenced_legacy_relations_is_still_refused(world):
    """CASCADE removes the foreign-key stop, so the boundary triggers of the cascaded set can fire: record who answers."""
    for rel in ("kala_gochara_coverage", "kala_gochara_publication"):
        r = attempt(world.owner, f"TRUNCATE public.{rel} CASCADE")
        world.table.append((SHORT[rel], "TRUNCATE CASCADE (governed rows)", "-", "-", RC, *r, "owner"))
        assert r[0] == "REFUSED", (rel, r)                      # never succeeds while a governed row exists anywhere in the cascaded set


# ── the table ───────────────────────────────────────────────────────────────

def _emit_table(rows):
    head = "| relation | operation | chart | generation | isolation | verdict | answering guard | detail | actor |\n|---|---|---|---|---|---|---|---|---|\n"
    seen, body = set(), ""
    for r in rows:
        if r in seen:
            continue
        seen.add(r)
        body += "| " + " | ".join(re.sub(r"[|]", "/", str(x)) for x in r) + " |\n"
    text = head + body
    print("\n" + text)
    out = os.environ.get("C55_BEHAVIOUR_TABLE")
    if out:
        Path(out).write_text(text)
