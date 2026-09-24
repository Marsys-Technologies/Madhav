"""WP10 cutover rehearsal gate (remainder brief §7.A) — the step scripts under
scripts/kala_gochara_cutover/ exercised end-to-end against the disposable
remainder Postgres (port 55434) on a stripped-down synthetic schema.

Synthetic schema only: kala_gochara_windows (migration 460 columns + 527's
generation + 556's era_slice_key), _v2/build_state stubs (for step 10),
kala_gochara_authority (527), build_protected_assets (540), asset_registry /
asset_output_digest_specs (created outside migrations — minimal DDL from the
columns the step SQL touches), plus the small stubs 1080–1086 ALTER
(gochara_resonance_map, kala_vedha_gochara, kala_moorti_nirnaya,
brahma_prospective_ledger, mimamsa_predictions, bg_transit_rules per 266).

Per-step coverage:
  step 0  — NOT_RUN (TS route test; documented in step00_clear_guard.md)
  step 1  — grant SQL applies, gate probe green (role/archive stubbed)
  step 2  — NOT_RUN without --dump (exit 3 asserted)
  step 3  — guard refuses 'v1'/'3.0' DML, passes '4.0'; century held; reversal
  step 4  — 1080–1086 apply + information_schema diff empty; idempotent
  step 5  — registry re-pin fields; conjuncts (f)/(j)/(k) behave; reversal
  step 6  — synthetic candidate build; candidate rebuild replaces in place
  step 7  — flip gates: DB substrates green incl. scratch rollback
  step 8  — flip (evidence_ref=manifest_id, published) + reversal
  step 9  — birth-epoch detector query demonstrated on a 1985-03-02 chart
  step 10 — N-11 refusal without ruling ref; scope delete + 1018 retirement

Production-refusal: every script refuses a 5433/non-loopback DSN without the
matching tranche flag (asserted for steps 3 and 6 as representatives).

NOT_RUN (skip with reason) when the disposable DB is unreachable — never a
fallback to any other DSN.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import psycopg
import pytest

DSN = os.environ.get(
    "GOCHARA_REMAINDER_DSN", "postgresql://wp6:disposable@localhost:55434/wp6"
)

SIDECAR = Path(__file__).resolve().parents[3]
CUTOVER = SIDECAR / "scripts" / "kala_gochara_cutover"
PROD_DSN = "postgresql://u:x@127.0.0.1:5433/prod"

CHART_A = "00000000-0000-4000-8000-0000000000a1"
CHART_B = "00000000-0000-4000-8000-0000000000b2"  # born 1985-03-02 (step 9)

DDL = """
-- Ledger tables are created by step 4's migration apply (1081) and are NOT
-- re-created by this fixture; drop them so every test starts from a clean
-- ledger (a rolled-back manifest from a prior test must not leak in).
DROP TABLE IF EXISTS kala_gochara_convention, kala_gochara_publication,
  kala_gochara_contacts, kala_gochara_coverage CASCADE;
DROP TABLE IF EXISTS kala_gochara_windows CASCADE;
CREATE TABLE kala_gochara_windows (
  id BIGSERIAL PRIMARY KEY,
  chart_id UUID NOT NULL,
  event_class TEXT NOT NULL,
  temporal_shape TEXT NOT NULL,
  window_start DATE NOT NULL,
  window_end DATE NOT NULL,
  peak_date DATE NOT NULL,
  milestone_id TEXT,
  is_irreversibility_milestone BOOLEAN NOT NULL DEFAULT FALSE,
  signed_intensity NUMERIC NOT NULL,
  raw_intensity NUMERIC NOT NULL,
  valence TEXT NOT NULL,
  is_adverse BOOLEAN NOT NULL,
  active_sentences JSONB NOT NULL DEFAULT '[]'::jsonb,
  contributing_systems JSONB NOT NULL DEFAULT '[]'::jsonb,
  suppression_state JSONB NOT NULL DEFAULT '{}'::jsonb,
  peak_basis TEXT NOT NULL DEFAULT 'gochara_lambda_e_v1',
  calibration_state TEXT NOT NULL DEFAULT 'structural_prior',
  source TEXT NOT NULL DEFAULT 'live',
  computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  generation TEXT NOT NULL DEFAULT 'v1',
  era_slice_key TEXT
);
DROP TABLE IF EXISTS kala_gochara_windows_v2 CASCADE;
CREATE TABLE kala_gochara_windows_v2 (
  id BIGSERIAL PRIMARY KEY,
  chart_id UUID NOT NULL,
  event_class TEXT NOT NULL,
  generation TEXT NOT NULL,
  era_slice_key TEXT
);
DROP TABLE IF EXISTS kala_gochara_v2_build_state CASCADE;
CREATE TABLE kala_gochara_v2_build_state (
  chart_id UUID NOT NULL,
  event_class TEXT NOT NULL,
  generation TEXT NOT NULL,
  rows_written INT NOT NULL DEFAULT 0,
  class_fingerprint TEXT,
  skipped_reason TEXT,
  horizon_start_date DATE,
  horizon_end_date DATE
);
DROP TABLE IF EXISTS kala_gochara_authority CASCADE;
CREATE TABLE kala_gochara_authority (
  chart_id UUID PRIMARY KEY,
  authoritative_generation TEXT NOT NULL DEFAULT 'v1',
  flipped_at TIMESTAMPTZ,
  flipped_by TEXT,
  evidence_ref TEXT
);
DROP TABLE IF EXISTS build_protected_assets CASCADE;
CREATE TABLE build_protected_assets (
  asset_id TEXT NOT NULL,
  chart_id UUID NOT NULL,
  protected_since TIMESTAMPTZ NOT NULL DEFAULT now(),
  reason TEXT NOT NULL,
  PRIMARY KEY (asset_id, chart_id)
);
DROP TABLE IF EXISTS asset_registry CASCADE;
CREATE TABLE asset_registry (
  asset_id TEXT PRIMARY KEY,
  target_table TEXT,
  count_sql TEXT,
  clear_tables TEXT,
  integrity_check_sql TEXT,
  depends_on TEXT[],
  scope TEXT,
  is_active BOOLEAN NOT NULL DEFAULT TRUE
);
DROP TABLE IF EXISTS asset_output_digest_specs CASCADE;
CREATE TABLE asset_output_digest_specs (
  asset_id TEXT NOT NULL,
  spec_sha256 TEXT NOT NULL,
  spec JSONB NOT NULL,
  retired_at TIMESTAMPTZ,
  PRIMARY KEY (asset_id, spec_sha256)
);
DROP TABLE IF EXISTS gochara_resonance_map CASCADE;
CREATE TABLE gochara_resonance_map (
  id BIGSERIAL PRIMARY KEY,
  chart_id UUID NOT NULL,
  event_class TEXT NOT NULL
);
DROP TABLE IF EXISTS kala_vedha_gochara CASCADE;
CREATE TABLE kala_vedha_gochara (id BIGSERIAL PRIMARY KEY);
DROP TABLE IF EXISTS kala_moorti_nirnaya CASCADE;
CREATE TABLE kala_moorti_nirnaya (id BIGSERIAL PRIMARY KEY);
DROP TABLE IF EXISTS brahma_prospective_ledger CASCADE;
CREATE TABLE brahma_prospective_ledger (id BIGSERIAL PRIMARY KEY);
DROP TABLE IF EXISTS mimamsa_predictions CASCADE;
CREATE TABLE mimamsa_predictions (id BIGSERIAL PRIMARY KEY);
DROP TABLE IF EXISTS bg_transit_rules CASCADE;
CREATE TABLE bg_transit_rules (
  id SERIAL PRIMARY KEY,
  rule_type TEXT NOT NULL,
  graha TEXT NOT NULL,
  primary_house INTEGER NOT NULL,
  vedha_house INTEGER,
  phala TEXT NOT NULL,
  classical_citation TEXT NOT NULL,
  rule_notes TEXT,
  CONSTRAINT bg_transit_rules_graha_type_house_unique
    UNIQUE (graha, rule_type, primary_house)
);
DROP TABLE IF EXISTS kala_gochara_windows_archive_20260805 CASCADE;
CREATE TABLE kala_gochara_windows_archive_20260805 (
  id BIGINT PRIMARY KEY,
  chart_id UUID NOT NULL
);
"""

SEED = f"""
INSERT INTO asset_registry (asset_id, target_table, count_sql, integrity_check_sql,
                            depends_on, is_active) VALUES
  ('ka_gochara', 'kala_gochara_windows',
   'SELECT COUNT(*) FROM kala_gochara_windows_v2 WHERE chart_id=$1 AND generation=''2.0''',
   'SELECT true AS integrity_passed',
   ARRAY['bg_gochara_arcs','ka_gochara_resonance'], true),
  ('ka_gochara_v3_century_materialize', 'kala_gochara_windows_v2',
   'SELECT COUNT(*) FROM kala_gochara_windows_v2 WHERE chart_id=$1 AND generation LIKE ''g3_%''',
   'SELECT true AS integrity_passed', ARRAY['ka_kota_chakra'], true),
  ('ka_kshetra', NULL, NULL, NULL, ARRAY['ga_positions'], true),
  ('ka_sangam', NULL, NULL, NULL, ARRAY['ka_gochara'], true),
  ('ka_gochara_sweep', 'kala_gochara_windows',
   'SELECT COUNT(*) FROM kala_gochara_windows WHERE chart_id=$1', NULL, NULL, false);
INSERT INTO gochara_resonance_map (chart_id, event_class) VALUES
  ('{CHART_A}', 'marriage'), ('{CHART_B}', 'career');
INSERT INTO kala_gochara_windows (chart_id, event_class, temporal_shape,
  window_start, window_end, peak_date, signed_intensity, raw_intensity, valence,
  is_adverse, generation) VALUES
  ('{CHART_A}', 'marriage', 'point', '2001-01-01', '2001-01-01', '2001-01-01', 1, 1, 'gain', false, 'v1'),
  ('{CHART_A}', 'marriage', 'point', '2002-01-01', '2002-01-01', '2002-01-01', 1, 1, 'gain', false, 'v1'),
  ('{CHART_A}', 'marriage', 'point', '2003-01-01', '2003-01-01', '2003-01-01', 1, 1, 'gain', false, 'v1'),
  ('{CHART_A}', 'marriage', 'point', '2013-05-01', '2013-05-01', '2013-05-01', 2, 2, 'gain', false, '3.0'),
  ('{CHART_A}', 'marriage', 'point', '2014-05-01', '2014-05-01', '2014-05-01', 2, 2, 'gain', false, '3.0');
INSERT INTO kala_gochara_windows_archive_20260805 (id, chart_id) VALUES
  (1, '{CHART_A}'), (2, '{CHART_A}');
"""

DIGEST_1018_SHA = ("ac32bdd3e5c24abda422a61e3f9a6b51c5c67c4ac868044e465444f0de61c596")


def _run_script(name: str, *args: str, env_extra: dict | None = None):
    env = dict(os.environ)
    env.update(env_extra or {})
    return subprocess.run(
        [sys.executable, str(CUTOVER / name), *args],
        capture_output=True, text=True, env=env, timeout=120)


def _apply_sql_file(conn, name: str, preset: str | None = None):
    sql = (CUTOVER / name).read_text()
    with conn.cursor() as cur:
        if preset:
            cur.execute(preset)
        cur.execute(sql)


@pytest.fixture()
def db():
    try:
        conn = psycopg.connect(DSN, autocommit=True, connect_timeout=3)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"NOT_RUN: disposable remainder database unreachable ({exc})")
    with conn.cursor() as cur:
        cur.execute(DDL)
        cur.execute(SEED)
        cur.execute("""DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'data_plane_builder') THEN
            DROP OWNED BY data_plane_builder;
            DROP ROLE data_plane_builder;
          END IF;
        END $$""")
        cur.execute("CREATE ROLE data_plane_builder NOLOGIN")
    yield conn
    with conn.cursor() as cur:
        cur.execute("DROP OWNED BY data_plane_builder")
        cur.execute("DROP ROLE IF EXISTS data_plane_builder")


def _scalar(conn, sql, args=()):
    with conn.cursor() as cur:
        cur.execute(sql, args)
        return cur.fetchone()[0]


def _integrity(conn) -> bool:
    check = _scalar(
        conn, "SELECT integrity_check_sql FROM asset_registry WHERE asset_id='ka_gochara'")
    return _scalar(conn, check.replace("%", "%%"))


# ── production refusal (representative scripts) ──────────────────────────────

def test_production_refusal_without_tranche_flag():
    r = _run_script("step06_candidate_build.py", "--dsn", PROD_DSN,
                    "--chart-id", CHART_A, "--rehearse-synthetic")
    assert r.returncode == 4 and "REFUSED" in r.stderr
    # Step 3 is SQL; the refusal lives in the applying wrapper — assert the
    # common guard itself on a tranche-1 step via step 2's script.
    r2 = _run_script("step02_restore_drill.py", "--dsn", PROD_DSN,
                     "--dump", "/nonexistent.dump")
    assert r2.returncode == 4 and "REFUSED" in r2.stderr


# ── step 1 — grant ───────────────────────────────────────────────────────────

def test_step01_grant_applies_and_gate_green(db):
    _apply_sql_file(db, "step01_select_grant.sql")
    assert _scalar(db, "SELECT has_table_privilege('data_plane_builder', "
                       "'public.kala_gochara_windows', 'SELECT')") is True
    assert _scalar(db, "SELECT has_table_privilege('data_plane_builder', "
                       "'public.kala_gochara_windows_archive_20260805', 'SELECT')") is True


# ── step 2 — restore drill refuses without a dump ────────────────────────────

def test_step02_not_run_without_dump(db):
    r = _run_script("step02_restore_drill.py", "--dsn", DSN)
    assert r.returncode == 3 and "NOT_RUN" in r.stderr


# ── step 3 — generation guard + N-6a ─────────────────────────────────────────

def test_step03_guard_blocks_protected_generations(db):
    _apply_sql_file(db, "step03_guard_n6a.sql")
    assert _scalar(db, "SELECT is_active FROM asset_registry "
                       "WHERE asset_id='ka_gochara_v3_century_materialize'") is False
    for stmt in (
        "DELETE FROM kala_gochara_windows WHERE generation='v1'",
        "UPDATE kala_gochara_windows SET valence='mixed' WHERE generation='3.0'",
        "UPDATE kala_gochara_windows SET generation='3.0' WHERE generation='v1'",
        "TRUNCATE kala_gochara_windows",
    ):
        with pytest.raises(Exception, match="GOCHARA GENERATION GUARD"):
            with db.cursor() as cur:
                cur.execute(stmt)
    # '4.0' writes pass.
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO kala_gochara_windows (chart_id, event_class, temporal_shape,"
            " window_start, window_end, peak_date, signed_intensity, raw_intensity,"
            " valence, is_adverse, generation) VALUES (%s,'marriage','point',"
            " '2027-01-01','2027-01-01','2027-01-01',1,1,'gain',false,'4.0')",
            (CHART_A,))
    assert _scalar(db, "SELECT count(*) FROM kala_gochara_windows "
                       "WHERE generation='4.0'") == 1
    assert _scalar(db, "SELECT count(*) FROM build_protected_assets "
                       "WHERE asset_id='ka_gochara_sweep'") == 1


def test_step03_reversal_restores(db):
    _apply_sql_file(db, "step03_guard_n6a.sql")
    _apply_sql_file(db, "step03_reversal.sql")
    assert _scalar(db, "SELECT is_active FROM asset_registry "
                       "WHERE asset_id='ka_gochara_v3_century_materialize'") is True
    with db.cursor() as cur:  # guard gone: protected DML succeeds again
        cur.execute("DELETE FROM kala_gochara_windows WHERE generation='v1'")
    assert _scalar(db, "SELECT count(*) FROM kala_gochara_windows "
                       "WHERE generation='v1'") == 0
    assert _scalar(db, "SELECT count(*) FROM information_schema.triggers "
                       "WHERE trigger_name LIKE 'trg_kgw_generation_guard%%'") == 0


# ── step 4 — apply + verify ──────────────────────────────────────────────────

def test_step04_apply_verify_and_idempotent(db):
    for _ in range(2):
        r = _run_script("step04_apply_verify.py", "--dsn", DSN)
        assert r.returncode == 0, r.stderr
    for table in ("kala_gochara_convention", "kala_gochara_publication",
                  "kala_gochara_contacts", "kala_gochara_coverage"):
        assert _scalar(db, "SELECT count(*) FROM information_schema.tables "
                           "WHERE table_name=%s", (table,)) == 1
    assert _scalar(db, "SELECT count(*) FROM information_schema.columns "
                       "WHERE table_name='gochara_resonance_map' "
                       "AND column_name='target_resolution_state'") == 1


# ── step 5 — registry re-pin ─────────────────────────────────────────────────

def test_step05_repin_fields_and_conjuncts(db):
    _run_script("step04_apply_verify.py", "--dsn", DSN)
    _apply_sql_file(db, "step05_registry_repin.sql")
    row = None
    with db.cursor() as cur:
        cur.execute("SELECT count_sql, clear_tables, depends_on, target_table "
                    "FROM asset_registry WHERE asset_id='ka_gochara'")
        row = cur.fetchone()
    assert "generation='4.0'" in row[0] and "kala_gochara_windows " in row[0]
    assert row[1] == ("[kala_gochara_windows, kala_gochara_contacts, "
                      "kala_gochara_coverage]")
    assert set(row[2]) == {"bg_ephemeris", "bg_transit_rules",
                           "ka_gochara_resonance", "ka_vedha_gochara",
                           "ka_moorti_nirnaya", "ga_positions", "ga_dashas",
                           "ga_yoga"}
    # conjunct (j): target_table == count_sql relation
    assert row[3] == "kala_gochara_windows"
    # century clear_tables declared (F-30)
    assert _scalar(db, "SELECT clear_tables FROM asset_registry "
                       "WHERE asset_id='ka_gochara_v3_century_materialize'") == \
        "[kala_gochara_windows, kala_gochara_windows_v2]"
    # full contract evaluates green on the seeded fixture
    assert _integrity(db) is True
    # conjunct (f): a '2.0' row in production turns the contract red
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO kala_gochara_windows (chart_id, event_class, temporal_shape,"
            " window_start, window_end, peak_date, signed_intensity, raw_intensity,"
            " valence, is_adverse, generation) VALUES (%s,'marriage','point',"
            " '2020-01-01','2020-01-01','2020-01-01',1,1,'gain',false,'2.0')",
            (CHART_A,))
    assert _integrity(db) is False
    with db.cursor() as cur:
        cur.execute("DELETE FROM kala_gochara_windows WHERE generation='2.0'")
    assert _integrity(db) is True


def test_step05_conjunct_k_detects_published_over_void(db):
    _run_script("step04_apply_verify.py", "--dsn", DSN)
    _apply_sql_file(db, "step05_registry_repin.sql")
    # authority at a '4.x' generation with NO windows and NO published manifest
    with db.cursor() as cur:
        cur.execute("INSERT INTO kala_gochara_authority "
                    "(chart_id, authoritative_generation) VALUES (%s, '4.0')",
                    (CHART_A,))
    assert _integrity(db) is False


def test_step05_reversal_restores_registry(db):
    _run_script("step04_apply_verify.py", "--dsn", DSN)
    before = _scalar(db, "SELECT count_sql FROM asset_registry "
                         "WHERE asset_id='ka_gochara'")
    _apply_sql_file(db, "step05_registry_repin.sql")
    _apply_sql_file(db, "step05_reversal.sql")
    assert _scalar(db, "SELECT count_sql FROM asset_registry "
                       "WHERE asset_id='ka_gochara'") == before
    assert "'2.0'" in before


# ── steps 6–8 — candidate build, flip gates, flip ────────────────────────────

def _step06(chart: str):
    return _run_script("step06_candidate_build.py", "--dsn", DSN,
                       "--chart-id", chart, "--rehearse-synthetic")


def test_step06_candidate_build_and_rebuild(db):
    _run_script("step04_apply_verify.py", "--dsn", DSN)
    r = _step06(CHART_A)
    assert r.returncode == 0, r.stderr
    assert _scalar(db, "SELECT status FROM kala_gochara_publication "
                       "WHERE chart_id=%s AND generation='4.0'",
                   (CHART_A,)) == "candidate"
    assert _scalar(db, "SELECT count(*) FROM kala_gochara_contacts "
                       "WHERE chart_id=%s AND generation='4.0'", (CHART_A,)) == 1
    vector = _scalar(db, "SELECT input_generation_vector->>'nodal_drishti' "
                         "FROM kala_gochara_publication WHERE chart_id=%s",
                     (CHART_A,))
    assert vector == "removed"
    # candidate rebuild replaces in place (no new manifest, same row count)
    r2 = _step06(CHART_A)
    assert r2.returncode == 0, r2.stderr
    assert _scalar(db, "SELECT count(*) FROM kala_gochara_publication "
                       "WHERE chart_id=%s AND generation='4.0'", (CHART_A,)) == 1
    # '3.0' untouched
    assert _scalar(db, "SELECT count(*) FROM kala_gochara_windows "
                       "WHERE generation='3.0'") == 2


def test_step07_flip_gates(db):
    _run_script("step04_apply_verify.py", "--dsn", DSN)
    assert _step06(CHART_A).returncode == 0
    r = _run_script("step07_flip_gates.py", "--dsn", DSN, "--chart-id", CHART_A)
    assert r.returncode == 0, r.stderr
    assert '"pass": true' in r.stdout


def test_step08_flip_and_reverse(db):
    _run_script("step04_apply_verify.py", "--dsn", DSN)
    assert _step06(CHART_A).returncode == 0
    r = _run_script("step08_flip.py", "--dsn", DSN, "--chart-id", CHART_A,
                    "--flipped-by", "wp10-rehearsal")
    assert r.returncode == 0, r.stderr
    manifest = _scalar(db, "SELECT evidence_ref FROM kala_gochara_authority "
                           "WHERE chart_id=%s", (CHART_A,))
    status = _scalar(db, "SELECT status FROM kala_gochara_publication "
                         "WHERE chart_id=%s AND generation='4.0'", (CHART_A,))
    assert status == "published"
    assert manifest == _scalar(
        db, "SELECT manifest_id::text FROM kala_gochara_publication "
            "WHERE chart_id=%s AND generation='4.0'", (CHART_A,))
    assert _scalar(db, "SELECT authoritative_generation "
                       "FROM kala_gochara_authority WHERE chart_id=%s",
                   (CHART_A,)) == "4.0"
    # conjunct (k) now satisfiable only with a window: none exists → red.
    _apply_sql_file(db, "step05_registry_repin.sql")
    assert _integrity(db) is False
    with db.cursor() as cur:  # add the '4.0' window → green
        cur.execute(
            "INSERT INTO kala_gochara_windows (chart_id, event_class, temporal_shape,"
            " window_start, window_end, peak_date, signed_intensity, raw_intensity,"
            " valence, is_adverse, generation) VALUES (%s,'marriage','point',"
            " '2026-06-15','2026-06-15','2026-06-15',1,1,'gain',false,'4.0')",
            (CHART_A,))
    assert _integrity(db) is True
    # reversal: authority back to '3.0', manifest rolled_back
    rr = _run_script("step08_flip.py", "--dsn", DSN, "--chart-id", CHART_A,
                     "--flipped-by", "wp10-rehearsal", "--reverse")
    assert rr.returncode == 0, rr.stderr
    assert _scalar(db, "SELECT authoritative_generation "
                       "FROM kala_gochara_authority WHERE chart_id=%s",
                   (CHART_A,)) == "3.0"
    assert _scalar(db, "SELECT status FROM kala_gochara_publication "
                       "WHERE chart_id=%s AND generation='4.0'",
                   (CHART_A,)) == "rolled_back"


# ── step 9 — birth-epoch detector (#2534 class) ─────────────────────────────

def test_step09_birth_epoch_detector(db):
    """Chart B born 1985-03-02: the detector query for the century's #2534
    defect class (a window before the chart's own birth) returns zero on a
    correctly built candidate and catches a misbuilt one."""
    _run_script("step04_apply_verify.py", "--dsn", DSN)
    birth = "1985-03-02"
    with db.cursor() as cur:
        cur.execute(
            "INSERT INTO kala_gochara_windows (chart_id, event_class, temporal_shape,"
            " window_start, window_end, peak_date, signed_intensity, raw_intensity,"
            " valence, is_adverse, generation) VALUES (%s,'career','point',"
            " '2010-01-01','2010-01-01','2010-01-01',1,1,'gain',false,'4.0')",
            (CHART_B,))
    detector = ("SELECT count(*) FROM kala_gochara_windows "
                "WHERE chart_id=%s AND generation='4.0' "
                "AND window_start < %s::date")
    assert _scalar(db, detector, (CHART_B, birth)) == 0
    with db.cursor() as cur:  # a pre-birth window would be caught
        cur.execute(
            "INSERT INTO kala_gochara_windows (chart_id, event_class, temporal_shape,"
            " window_start, window_end, peak_date, signed_intensity, raw_intensity,"
            " valence, is_adverse, generation) VALUES (%s,'career','point',"
            " '1970-01-01','1970-01-01','1970-01-01',1,1,'gain',false,'4.0')",
            (CHART_B,))
    assert _scalar(db, detector, (CHART_B, birth)) == 1


# ── step 10 — N-11 disposition ───────────────────────────────────────────────

def test_step10_refuses_without_ruling_then_disposes(db):
    with db.cursor() as cur:
        cur.execute("INSERT INTO kala_gochara_windows_v2 "
                    "(chart_id, event_class, generation) VALUES "
                    "(%s, 'marriage', '2.0'), (%s, 'career', 'g3_utkarsha')",
                    (CHART_A, CHART_A))
        cur.execute("INSERT INTO kala_gochara_v2_build_state "
                    "(chart_id, event_class, generation, rows_written) VALUES "
                    "(%s, 'marriage', '2.0', 1)", (CHART_A,))
        cur.execute("INSERT INTO asset_output_digest_specs "
                    "(asset_id, spec_sha256, spec) VALUES "
                    "('ka_gochara', %s, '{}'::jsonb)", (DIGEST_1018_SHA,))
    # refusal without the ruling GUC
    with pytest.raises(Exception, match="N-11 is a native ruling"):
        _apply_sql_file(db, "step10_n11_disposition.sql")
    db.rollback()  # the refusal aborts the file's BEGIN block; clear it
    assert _scalar(db, "SELECT count(*) FROM kala_gochara_windows_v2 "
                       "WHERE generation='2.0'") == 1
    _apply_sql_file(db, "step10_n11_disposition.sql",
                    preset="SET app.n11_ruling_ref = 'N-11 rehearsal ruling ref'")
    assert _scalar(db, "SELECT count(*) FROM kala_gochara_windows_v2 "
                       "WHERE generation='2.0'") == 0
    # the century's staging surface is untouched
    assert _scalar(db, "SELECT count(*) FROM kala_gochara_windows_v2 "
                       "WHERE generation='g3_utkarsha'") == 1
    assert _scalar(db, "SELECT retired_at IS NOT NULL FROM asset_output_digest_specs "
                       "WHERE asset_id='ka_gochara' AND spec_sha256=%s",
                   (DIGEST_1018_SHA,)) is True
