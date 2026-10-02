"""Pravāha A2.5 / ASTRA v1.0 A7 — EARNED integration evidence on the disposable
remainder Postgres (port 55434), complementing the fake-conn unit suite in
test_a25_v41_candidate_writer.py.

The reviewer's A7 finding: the acceptance claims exceeded what the tests
measured — tuple-row fakes hid the runner's real types, the "retry proof"
counted one insertion from one call against no database state, and the
PostgreSQL generation trigger was never executed by the submitted evidence.

What this file executes against REAL PostgreSQL (never a fake):

  1. MANIFEST SUBSTEP end-to-end with the runner's NATIVE types — a
     psycopg dict_row connection and chart_id as a uuid.UUID object — with
     the §12.9 overlay-freshness gate genuinely GREEN (real bg_transit_rules /
     bg_vedha_malefic_scale / bg_transit_moorti seed rows, overlay rows
     fingerprinted by the writers' own fetch path). Re-running replaces the
     candidate manifest IN PLACE (one row, same manifest_id). dry_run=True
     issues no DML (A8 on a real connection that would record it).
  2. INTERRUPTED SUBSTEP / RETRY with sibling-row preservation: committed
     sibling rows (another chart's '4.1', this chart's '3.0', this chart's
     OTHER body) survive (a) a mid-substep crash = transaction rollback, and
     (b) the orchestrator's savepoint rollback; the retried body substep then
     replaces EXACTLY its own (chart × '4.1' × body) rows — no duplicates, no
     sibling loss, verified by SQL counts and contact_id sets.
  3. LIFECYCLE REFUSAL on real rows: after the manifest is marked 'published',
     write_contacts raises PublishedGenerationRefusal (N-7) — and the row set
     is unchanged afterwards.
  4. The REAL generation-guard trigger (migration 1071, applied from its
     migration file): DELETE of a 'v1' row raises the guard; DELETE of a
     '4.1' candidate row passes. ('3.0' protection is step03_guard_n6a's —
     executed in test_wp10_cutover.py::test_step03_guard_blocks_protected_
     generations against this same disposable instance.)

Schema: migration 1081 (ledger tables) + 1087 (contacts inclusivity columns)
applied from the real migration files, on minimal L0 stubs for the freshness
gate and a minimal kala_gochara_windows for the trigger.

NOT_RUN (skip with reason) when the disposable DB is unreachable — never a
fallback to any other DSN, per the WP10 convention.
"""
from __future__ import annotations

import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psycopg
import psycopg.rows
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

import pipeline.orchestrator.writers.ka_gochara_v4_41_candidate as writer_mod  # noqa: E402
from pipeline.orchestrator.writers import ContextSpec, SubStep  # noqa: E402
from services.ka_vedha_gochara import freshness as freshness_mod  # noqa: E402

SIDECAR = Path(__file__).resolve().parents[3]
MIGRATIONS = SIDECAR.parent / "migrations"

# Disposable-cluster discipline (ASTRA v1.1 EXTRA BLOCKER): this fixture
# NEVER runs its destructive setup against a database it did not create.
# It (a) verifies the destination CLUSTER's system_identifier against the
# pinned disposable id (same guard as
# scripts/kala_gochara_cutover/resonance_rebuild_disposable_rehearsal.py),
# (b) CREATEs its own throwaway database for the test, (c) DROPs it
# afterwards. Any mismatch or unreachable cluster = NOT_RUN skip, never a
# fallback to another DSN.
ADMIN_DSN = os.environ.get(
    "GOCHARA_A25_ADMIN_DSN", "postgresql://wp6:local@localhost:55434/postgres"
)
EXPECTED_CLUSTER_ID = os.environ.get(
    "GOCHARA_A25_DISPOSABLE_CLUSTER_ID", "7691638507951775319"
)

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"   # the pinned A2.5 chart
CHART_UUID = uuid.UUID(CHART_ID)
OTHER_CHART = "00000000-0000-4000-8000-0000000000b2"
UTC = timezone.utc

STUB_DDL = """
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
  era_slice_key TEXT,
  parent_window_id BIGINT,
  resolution TEXT
);
DROP TABLE IF EXISTS gochara_resonance_map CASCADE;
CREATE TABLE gochara_resonance_map (
  chart_id UUID NOT NULL,
  event_class TEXT NOT NULL,
  target_type TEXT NOT NULL,
  target_ref TEXT NOT NULL,
  weight DOUBLE PRECISION NOT NULL,
  target_resolution_state TEXT NOT NULL DEFAULT 'resolved',
  classical_citation TEXT,
  uncited_extension BOOLEAN,
  source_rule_id TEXT
);
DROP TABLE IF EXISTS chart_facts CASCADE;
CREATE TABLE chart_facts (
  fact_id TEXT PRIMARY KEY,
  chart_id UUID NOT NULL,
  ayanamsha_id TEXT NOT NULL,
  fact_category TEXT NOT NULL,
  fact_subject TEXT NOT NULL,
  fact_key TEXT NOT NULL,
  fact_value_text TEXT,
  fact_value_num DOUBLE PRECISION
);
DROP TABLE IF EXISTS chart_dashas CASCADE;
CREATE TABLE chart_dashas (
  dasha_row_id TEXT PRIMARY KEY,
  chart_id UUID NOT NULL,
  ayanamsha_id TEXT NOT NULL,
  system_id TEXT NOT NULL,
  level_n INT NOT NULL,
  parent_row_id TEXT,
  lord_graha TEXT NOT NULL,
  start_iso TIMESTAMPTZ NOT NULL,
  end_iso TIMESTAMPTZ NOT NULL,
  build_id TEXT,
  verification_pass_status TEXT NOT NULL
);
DROP TABLE IF EXISTS bg_transit_rules CASCADE;
CREATE TABLE bg_transit_rules (
  id BIGSERIAL PRIMARY KEY,
  rule_type TEXT NOT NULL,
  graha TEXT NOT NULL,
  primary_house INT NOT NULL,
  vedha_house INT,
  phala TEXT,
  classical_citation TEXT
);
DROP TABLE IF EXISTS bg_vedha_malefic_scale CASCADE;
CREATE TABLE bg_vedha_malefic_scale (
  malefic_count INT PRIMARY KEY,
  effect_grade TEXT,
  effect_description TEXT,
  source_citation TEXT
);
DROP TABLE IF EXISTS bg_transit_moorti CASCADE;
CREATE TABLE bg_transit_moorti (
  nakshatra_offset INT PRIMARY KEY,
  moorti_name TEXT,
  quality_tier TEXT,
  phala_brief TEXT,
  classical_citation TEXT
);
DROP TABLE IF EXISTS kala_vedha_gochara CASCADE;
CREATE TABLE kala_vedha_gochara (
  id BIGSERIAL PRIMARY KEY,
  chart_id UUID NOT NULL,
  window_start DATE,
  window_end DATE,
  vedha_kind TEXT NOT NULL,
  graha TEXT,
  detail JSONB NOT NULL DEFAULT '{}'::jsonb,
  classical_citation TEXT
  -- deliberately NO formula_version column: the fallback-schema path
  -- (ASTRA v1.1 A1 — the optional-column alias) is exercised by this shape
);
DROP TABLE IF EXISTS kala_moorti_nirnaya CASCADE;
CREATE TABLE kala_moorti_nirnaya (
  id BIGSERIAL PRIMARY KEY,
  chart_id UUID NOT NULL,
  upstream_fingerprint JSONB
);
DROP TABLE IF EXISTS kala_gochara_convention CASCADE;
DROP TABLE IF EXISTS kala_gochara_publication CASCADE;
DROP TABLE IF EXISTS kala_gochara_contacts CASCADE;
DROP TABLE IF EXISTS kala_gochara_coverage CASCADE;
"""

SEED_SQL = """
INSERT INTO bg_transit_rules (rule_type, graha, primary_house, vedha_house,
                              phala, classical_citation)
VALUES ('favourable', 'Jupiter', 5, 2, 'rehearsal phala', 'PG321 (rehearsal)');
INSERT INTO bg_vedha_malefic_scale (malefic_count, effect_grade,
                                    effect_description, source_citation)
VALUES (1, 'mild', 'rehearsal scale', 'PG353 (rehearsal)');
INSERT INTO bg_transit_moorti (nakshatra_offset, moorti_name, quality_tier,
                               phala_brief, classical_citation)
VALUES (1, 'Janma', 'neutral', 'rehearsal moorti', 'PG (rehearsal)');
"""


def _apply_migration(conn, number_prefix: str) -> None:
    path = next(MIGRATIONS.glob(f"{number_prefix}_*.sql"))
    with conn.cursor() as cur:
        cur.execute(path.read_text())


def _fingerprint_overlays(conn, chart_id: str) -> None:
    """Stamp overlay rows with the fingerprint the writers' OWN fetch path
    computes right now — the only honest way to make §12.9 green."""
    vedha_fp = freshness_mod.current_fingerprint(conn)
    moorti_fp = freshness_mod.current_moorti_fingerprint(conn)
    import json
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO kala_vedha_gochara (chart_id, vedha_kind, detail) "
            "VALUES (%s, 'house_vedha', jsonb_build_object('upstream_fingerprint', %s::jsonb))",
            (chart_id, json.dumps(vedha_fp)),
        )
        cur.execute(
            "INSERT INTO kala_moorti_nirnaya (chart_id, upstream_fingerprint) "
            "VALUES (%s, %s::jsonb)",
            (chart_id, json.dumps(moorti_fp)),
        )


@pytest.fixture()
def disposable_dsn():
    """A brand-new throwaway database on the pinned disposable cluster —
    created for the test, dropped afterwards. Skips (NOT_RUN) unless the
    cluster IS the pinned disposable one."""
    try:
        admin = psycopg.connect(ADMIN_DSN, autocommit=True, connect_timeout=3)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"NOT_RUN: disposable cluster unreachable ({exc})")
    actual = admin.execute(
        "SELECT system_identifier FROM pg_control_system()").fetchone()[0]
    if str(actual) != EXPECTED_CLUSTER_ID:
        admin.close()
        pytest.skip(
            "NOT_RUN: cluster system_identifier "
            f"{actual} is not the pinned disposable cluster — refusing to "
            "run any setup against an unrecognised cluster (set "
            "GOCHARA_A25_DISPOSABLE_CLUSTER_ID to the disposable cluster's "
            "own identifier)")
    dbname = f"a25pg_{os.getpid()}_{uuid.uuid4().hex[:8]}"
    admin.execute(f'CREATE DATABASE "{dbname}"')
    parts = psycopg.conninfo.conninfo_to_dict(ADMIN_DSN)
    parts["dbname"] = dbname
    dsn = psycopg.conninfo.make_conninfo(**parts)
    admin.close()
    yield dsn
    admin = psycopg.connect(ADMIN_DSN, autocommit=True)
    admin.execute(f'DROP DATABASE IF EXISTS "{dbname}" WITH (FORCE)')
    admin.close()


@pytest.fixture()
def pg(disposable_dsn):
    conn = psycopg.connect(disposable_dsn, autocommit=True)
    with conn.cursor() as cur:
        cur.execute(STUB_DDL)
    _apply_migration(conn, "1081")
    _apply_migration(conn, "1087")
    _apply_migration(conn, "1071")
    # 1152: t_exact nullable for N3 truncated contacts (the A2 residence
    # geometry writes such rows through the real ledger).
    _apply_migration(conn, "1152")
    with conn.cursor() as cur:
        cur.execute(SEED_SQL)
    _fingerprint_overlays(conn, CHART_ID)
    yield conn
    conn.close()


@pytest.fixture()
def pg_dict(pg, disposable_dsn):
    """The same disposable database through the runner's NATIVE connection
    shape: dict_row rows, autocommit off (the test owns commit/rollback —
    exactly the orchestrator's posture)."""
    conn = psycopg.connect(disposable_dsn, row_factory=psycopg.rows.dict_row)
    yield conn
    conn.rollback()
    conn.close()


def _scalar(conn, sql, args=()):
    with conn.cursor() as cur:
        cur.execute(sql, args)
        row = cur.fetchone()
    if isinstance(row, dict):
        return next(iter(row.values()))
    return row[0]


def _ctx(conn, chart, dry_run=False) -> ContextSpec:
    return ContextSpec(
        asset_id=writer_mod.ASSET_ID,
        build_id=f"a25pg-{uuid.uuid4()}",
        db_conn=conn,
        config={"chart_id": chart},
        dry_run=dry_run,
    )


def _episode(body: str, t: datetime, relation: str = "conjunction") -> dict:
    return {
        "independence_group": f"ig-{body.lower()}-pg",
        "body": body, "relation": relation, "aspect_deg": 0,
        "target_type": "karaka", "target_ref": "SUN", "target_fact_id": None,
        "target_resolution_state": "resolved", "target_longitude_deg": 90.0,
        "t_in": t - timedelta(hours=2), "t_exact": t, "t_out": t + timedelta(hours=2),
        "bracket_seconds": 300, "tolerance_arcsec": 2.0,
        "truncated_at_horizon": None, "branch": "direct",
        "orb_max_deg": 5.0, "orb_source": "orb_conj_slow",
        "epistemic_class": "observed_event", "completeness_state": "applied",
        "operator_role": "kernel", "precision_regime": "instant_grain",
        "time_basis": "event_time_utc",
        "comparable_with": "same_convention_same_inputs",
        "ephemeris_backend": {"backend": "swieph", "retflag": 258},
        "evidence_fact_ids": [], "classical_citation": None,
        "uncited_extension": True, "corpus_verifiable": None,
    }


def _coverage(body: str, horizon: str = "[2020-01-01,2020-02-01)") -> dict:
    return {
        "partition_kind": "body_target", "partition_key": f"{body.lower()}:karaka",
        "requested_horizon": horizon, "completed_horizon": horizon,
        "resolution": 2.0, "relations_searched": ["conjunction"],
        "targets_requested": 1,
        "target_resolution_state_counts": {"resolved": 1, "unavailable": 0,
                                           "unqualified": 0},
        "unavailable_inputs": {}, "unsearched_reason": None,
    }


def _seed_manifest(conn, chart, generation="4.1"):
    cid = writer_mod.ledger.register_convention(
        conn, writer_mod.step06_build.CONVENTION_VECTOR,
        {"ephemeris_backend": "swieph", "retflag": 258})
    mid = writer_mod.ledger.publish_candidate(
        conn, chart, generation, cid, {"seed": True},
        {"backend": "swieph", "retflag": 258}, "[2020-01-01,2020-02-01)")
    return cid, mid


# ── windows-substep inputs (A1/A7 real execution) ───────────────────────────

_NATAL = {
    "SUN": 291.96, "MOON": 327.06, "MAR": 198.52, "MER": 270.84,
    "JUP": 148.87, "VEN": 265.39, "SAT": 356.74,
    "RAH_MEAN": 21.34, "KET_MEAN": 201.34,
}
_LAGNA = 12.43


def _seed_windows_inputs(conn, chart) -> None:
    """Everything the REAL windows chain reads outside the ledger tables:
    one resolved resonance-map row (marriage/karaka/SUN), the chart's L1
    operands (graha positions + LAGNA + paksha + day_birth), and a
    tier-pinned Vimśottarī MD/AD/PD chain covering the contact dates."""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO gochara_resonance_map (chart_id, event_class,"
            " target_type, target_ref, weight, target_resolution_state,"
            " classical_citation, uncited_extension, source_rule_id)"
            " VALUES (%s, 'marriage', 'karaka', 'SUN', 0.9, 'resolved',"
            " 'PG249-250 (XX.34-38)', false, 'test-rule')", (chart,))
        for subj, lon in [*_NATAL.items(), ("LAGNA", _LAGNA)]:
            cur.execute(
                "INSERT INTO chart_facts (fact_id, chart_id, ayanamsha_id,"
                " fact_category, fact_subject, fact_key, fact_value_num)"
                " VALUES (%s, %s, 'lahiri_chitrapaksha', 'graha_position',"
                " %s, 'longitude_sidereal', %s)",
                (f"fact-{subj.lower()}", chart, subj, lon))
        cur.execute(
            "INSERT INTO chart_facts (fact_id, chart_id, ayanamsha_id,"
            " fact_category, fact_subject, fact_key, fact_value_text)"
            " VALUES ('fact-paksha', %s, 'lahiri_chitrapaksha',"
            " 'panchanga_tithi', 'TITHI', 'paksha', 'Shukla')", (chart,))
        cur.execute(
            "INSERT INTO chart_facts (fact_id, chart_id, ayanamsha_id,"
            " fact_category, fact_subject, fact_key, fact_value_num)"
            " VALUES ('fact-daybirth', %s, 'lahiri_chitrapaksha',"
            " 'saham_position', 'DAYBIRTH', 'day_birth', 1)", (chart,))
        for row_id, level, parent, lord, start, end in (
            ("d-md", 1, None, "JUP", "2010-01-01", "2026-01-01"),
            ("d-ad", 2, "d-md", "SAT", "2019-01-01", "2022-01-01"),
            ("d-pd", 3, "d-ad", "VEN", "2019-06-01", "2020-06-01"),
        ):
            cur.execute(
                "INSERT INTO chart_dashas (dasha_row_id, chart_id,"
                " ayanamsha_id, system_id, level_n, parent_row_id,"
                " lord_graha, start_iso, end_iso, build_id,"
                " verification_pass_status)"
                " VALUES (%s, %s, 'lahiri_chitrapaksha', 'vimshottari',"
                " %s, %s, %s, %s, %s, '1f89fd4c-7d1e-4f3a-b3ae-e7ff839a6feb', 'two_pass_verified')",
                (row_id, chart, level, parent, lord, start, end))
    conn.commit()


# ── 1 · manifest substep, native runner types, real freshness gate ───────────

def test_manifest_substep_real_pg_native_types_gate_green(pg_dict, monkeypatch):
    """The writer's manifest substep on a dict_row conn with a UUID chart_id,
    §12.9 gate genuinely green: convention + candidate manifest land; a rerun
    replaces the manifest IN PLACE (one row, same manifest_id). C17: the
    recorded ephemeris columns carry the PROBED backend (the helper's probe
    is stubbed to swieph — the writer's fail-closed backend_name call over
    the pinned horizon runs real); the refusal path is covered by the unit
    suite's moseph test."""
    from panchang_engine import swiss_backend as sb_mod
    monkeypatch.setattr(sb_mod, "_observed_backend_name", lambda swe: "swieph")
    writer = writer_mod.GocharaV41CandidateWriter()
    step = SubStep(key="manifest", label="m")
    res1 = writer_mod.GocharaV41CandidateWriter.run_substep(
        writer, _ctx(pg_dict, CHART_UUID), step)
    assert res1.rows_updated == 1
    pg_dict.commit()
    mid1 = _scalar(pg_dict,
                   "SELECT manifest_id FROM kala_gochara_publication "
                   "WHERE chart_id = %s AND generation = '4.1'", (CHART_ID,))
    assert _scalar(pg_dict,
                   "SELECT status FROM kala_gochara_publication "
                   "WHERE chart_id = %s AND generation = '4.1'",
                   (CHART_ID,)) == "candidate"
    assert _scalar(pg_dict,
                   "SELECT writer_asset_id FROM kala_gochara_publication "
                   "WHERE chart_id = %s AND generation = '4.1'",
                   (CHART_ID,)) == writer_mod.ASSET_ID
    # the recorded claim is the probed value, not the old hardcoded literal
    assert _scalar(pg_dict,
                   "SELECT ephemeris_backend FROM kala_gochara_convention",
                   ()) == "swieph"
    import swisseph as _swe
    assert _scalar(pg_dict,
                   "SELECT probe_retflag FROM kala_gochara_convention",
                   ()) == int(_swe.FLG_SWIEPH | _swe.FLG_SPEED)
    # rerun: replaced in place, never duplicated
    writer_mod.GocharaV41CandidateWriter.run_substep(
        writer, _ctx(pg_dict, CHART_UUID), step)
    pg_dict.commit()
    assert _scalar(pg_dict,
                   "SELECT count(*) FROM kala_gochara_publication "
                   "WHERE chart_id = %s AND generation = '4.1'", (CHART_ID,)) == 1
    assert _scalar(pg_dict,
                   "SELECT manifest_id FROM kala_gochara_publication "
                   "WHERE chart_id = %s AND generation = '4.1'",
                   (CHART_ID,)) == mid1


def test_manifest_substep_dry_run_issues_no_dml(pg_dict):
    """A8 on a real connection: dry_run=True stages nothing — no convention,
    no manifest, no rows anywhere."""
    writer = writer_mod.GocharaV41CandidateWriter()
    res = writer_mod.GocharaV41CandidateWriter.run_substep(
        writer, _ctx(pg_dict, CHART_UUID, dry_run=True),
        SubStep(key="manifest", label="m"))
    assert res.rows_inserted == 0 and "dry_run" in res.notes
    pg_dict.commit()
    assert _scalar(pg_dict, "SELECT count(*) FROM kala_gochara_publication") == 0
    assert _scalar(pg_dict, "SELECT count(*) FROM kala_gochara_convention") == 0


# ── 2 · interrupted substep / retry with sibling-row preservation ────────────

def _seed_siblings(conn) -> dict:
    """Committed sibling state the retry must never touch:
    - OTHER_CHART's '4.1' Mars contact + coverage;
    - THIS chart's '3.0' Mars contact (its own candidate manifest);
    - THIS chart's '4.1' Venus contact + coverage (the OTHER body substep)."""
    t = datetime(2020, 1, 15, 12, 0, tzinfo=UTC)
    # other chart, '4.1'
    cid_b, _ = _seed_manifest(conn, OTHER_CHART)
    writer_mod.ledger.write_contacts(
        conn, OTHER_CHART, "4.1", cid_b, [_episode("Mars", t)], "seed-b",
        bodies=["Mars"])
    writer_mod.ledger.write_coverage(
        conn, OTHER_CHART, "4.1", cid_b, [_coverage("mars")], "seed-b",
        bodies=["Mars"])
    # this chart, '3.0' (candidate manifest of the rollback surface)
    cid_30, _ = _seed_manifest(conn, CHART_ID, generation="3.0")
    writer_mod.ledger.write_contacts(
        conn, CHART_ID, "3.0", cid_30, [_episode("Mars", t)], "seed-30",
        bodies=["Mars"])
    # this chart, '4.1', Venus (the other body's substep, already done)
    cid, _ = _seed_manifest(conn, CHART_ID)
    writer_mod.ledger.write_contacts(
        conn, CHART_ID, "4.1", cid, [_episode("Venus", t)], "seed-venus",
        bodies=["Venus"])
    writer_mod.ledger.write_coverage(
        conn, CHART_ID, "4.1", cid, [_coverage("venus")], "seed-venus",
        bodies=["Venus"])
    conn.commit()
    return {"cid": cid}


def _contact_ids(conn, chart, generation, body) -> set:
    with conn.cursor() as cur:
        cur.execute(
            "SELECT contact_id FROM kala_gochara_contacts "
            "WHERE chart_id = %s AND generation = %s AND body = %s",
            (chart, generation, body))
        return {r[0] if not isinstance(r, dict) else r["contact_id"]
                for r in cur.fetchall()}


def test_interrupted_substep_and_retry_preserve_siblings(
        pg, pg_dict, disposable_dsn, monkeypatch):
    """The retry proof the reviewer asked for, driven through the REAL writer
    substep (never the ledger functions directly): REAL database state, an
    actual mid-substep crash, an actual rerun — siblings snapshotted before
    and after. enumerate_core is stubbed (its evidence lives in the
    enumerate tests); everything downstream — validation, DML, transaction
    semantics — is the writer's own code against real PostgreSQL."""
    sib = _seed_siblings(pg)
    cid = sib["cid"]
    t1 = datetime(2020, 1, 20, 12, 0, tzinfo=UTC)
    t2 = datetime(2020, 1, 22, 12, 0, tzinfo=UTC)
    writer = writer_mod.GocharaV41CandidateWriter()
    step = SubStep(key="body:Mars", label="mars")

    def _payload(episodes):
        return (episodes, [_coverage("mars")],
                {"convention_id": cid, "episodes_truncated_no_exact_kept": 0})

    def _sibling_snapshot(conn):
        return {
            "venus41": _contact_ids(conn, CHART_ID, "4.1", "Venus"),
            "mars30": _contact_ids(conn, CHART_ID, "3.0", "Mars"),
            "mars_other": _contact_ids(conn, OTHER_CHART, "4.1", "Mars"),
            "coverage": _scalar(conn,
                                "SELECT count(*) FROM kala_gochara_coverage "
                                "WHERE chart_id = %s AND generation = '4.1'",
                                (CHART_ID,)),
        }

    # First Mars substep: two contacts + coverage, committed.
    monkeypatch.setattr(writer_mod.step06_enumerate, "enumerate_core",
                        lambda *a, **kw: _payload(
                            [_episode("Mars", t1),
                             _episode("Mars", t2, relation="trine")]))
    res = writer.run_substep(_ctx(pg_dict, CHART_UUID), step)
    assert res.rows_inserted == 3  # 2 contacts + 1 coverage row
    pg_dict.commit()
    mars_v1 = _contact_ids(pg_dict, CHART_ID, "4.1", "Mars")
    assert len(mars_v1) == 2
    before = _sibling_snapshot(pg_dict)

    # (a) MID-SUBSTEP CRASH: the write_coverage leg raises AFTER
    # write_contacts' DML — the whole substep rolls back to the savepoint
    # (the orchestrator's transaction semantics); committed v1 rows survive.
    conn2 = psycopg.connect(disposable_dsn,
                            row_factory=psycopg.rows.dict_row)
    try:
        conn2.execute("SAVEPOINT substep")
        try:
            with monkeypatch.context() as mp:
                mp.setattr(writer_mod.ledger, "write_coverage",
                           lambda *a, **kw: (_ for _ in ()).throw(
                               RuntimeError("simulated mid-substep crash")))
                writer.run_substep(_ctx(conn2, CHART_UUID), step)
            conn2.commit()
            raise AssertionError("the crash never happened")
        except RuntimeError:
            conn2.execute("ROLLBACK TO SAVEPOINT substep")
            conn2.commit()
    finally:
        conn2.close()
    assert _contact_ids(pg_dict, CHART_ID, "4.1", "Mars") == mars_v1
    assert _sibling_snapshot(pg_dict) == before

    # (b) RETRY: the substep reruns with the corrected payload and replaces
    # EXACTLY its own scope — one Mars row now, never a duplicate of v1.
    monkeypatch.setattr(writer_mod.step06_enumerate, "enumerate_core",
                        lambda *a, **kw: _payload(
                            [_episode("Mars",
                                      datetime(2020, 1, 25, 12, 0,
                                               tzinfo=UTC))]))
    res = writer.run_substep(_ctx(pg_dict, CHART_UUID), step)
    assert res.rows_inserted == 2  # 1 contact + 1 coverage row
    pg_dict.commit()

    mars_v2 = _contact_ids(pg_dict, CHART_ID, "4.1", "Mars")
    assert len(mars_v2) == 1 and mars_v2 != mars_v1
    # every sibling intact, to the row
    after = _sibling_snapshot(pg_dict)
    assert after["venus41"] == before["venus41"]
    assert after["mars30"] == before["mars30"]
    assert after["mars_other"] == before["mars_other"]
    assert after["coverage"] == 2  # mars + venus, no duplicates
    assert _scalar(pg_dict,
                   "SELECT count(*) FROM kala_gochara_contacts "
                   "WHERE chart_id = %s AND generation = '4.1'",
                   (CHART_ID,)) == 2  # 1 mars + 1 venus


# ── 2b · windows substep, REAL end-to-end execution (A1/A7) ─────────────────

def _sun_episode(t: datetime, relation: str = "conjunction") -> dict:
    ep = _episode("Sun", t, relation=relation)
    ep["target_longitude_deg"] = _NATAL["SUN"]  # karaka SUN = natal Sun
    return ep


def test_windows_substep_real_execution_native_dict_rows(pg, pg_dict):
    """A1 + A7: the REAL windows entry point, start to finish, with the
    runner's native types — a uuid.UUID chart_id and NON-EMPTY dict-row
    results through every fetch (the v1.1 reviewer's crash geometry:
    'str' object has no attribute 'timestamp' at step06a:329), the fallback
    overlay schema WITHOUT formula_version (the alias path — the reviewer's
    KeyError), and the §12.9 gate genuinely green. Nothing is stubbed below
    the writer: class context, permission, projection, validation and DML
    all run. Whether any window is EMITTED is the permission systems'
    honest semantics (union admission at each sample instant); the crash
    geometry and the honest-completion contract are what this test pins."""
    cid, _ = _seed_manifest(pg_dict, CHART_UUID)
    t1 = datetime(2020, 1, 15, 12, 0, tzinfo=UTC)
    t2 = datetime(2020, 1, 22, 12, 0, tzinfo=UTC)
    writer_mod.ledger.write_contacts(
        pg_dict, CHART_UUID, "4.1", cid,
        [_sun_episode(t1), _sun_episode(t2)], "a25pg-sun", bodies=["Sun"])
    writer_mod.ledger.write_coverage(
        pg_dict, CHART_UUID, "4.1", cid, [_coverage("sun")],
        "a25pg-sun", bodies=["Sun"])
    pg_dict.commit()
    _seed_windows_inputs(pg, CHART_ID)

    # The two A1 crash points, directly, over the runner's dict rows:
    from scripts.kala_gochara_cutover import step06a_class_context as sa
    from scripts.kala_gochara_cutover import step06b_windows_projection as sb
    by_class, null_exact = sa.fetch_class_contact_instants(
        pg_dict, CHART_UUID, "4.1")
    assert len(by_class["marriage"]) == 2 and null_exact == 0
    import json as _json
    vedha_fp = freshness_mod.current_fingerprint(pg)
    with pg.cursor() as cur:
        cur.execute(
            "INSERT INTO kala_vedha_gochara (chart_id, window_start,"
            " window_end, vedha_kind, graha, detail, classical_citation)"
            " VALUES (%s, '2020-01-15', '2020-01-16', 'house_vedha',"
            " 'Saturn', %s::jsonb, 'PG (rehearsal)')",
            (CHART_ID, _json.dumps({"upstream_fingerprint": vedha_fp})))
    vedha_rows = sb.fetch_vedha_rows(pg_dict, CHART_UUID)
    assert vedha_rows  # overlay rows exist (fingerprint + the inserted one)
    assert all("formula_version" in r for r in vedha_rows)  # the alias —
    # never '?column?' (the reviewer's KeyError geometry)
    mine = [r for r in vedha_rows if r["window_start"] == "2020-01-15"]
    assert len(mine) == 1 and mine[0]["formula_version"] is None

    writer = writer_mod.GocharaV41CandidateWriter()
    res = writer.run_substep(_ctx(pg_dict, CHART_UUID),
                             SubStep(key="windows", label="w"))
    pg_dict.commit()
    # honest completion: the class was reached and projected (never a crash,
    # never an omitted-without-cause), the DB agrees with the report, and
    # every written row honours the pinned horizon
    assert "windows=" in res.notes and "classes=" in res.notes
    assert "class_context_omitted=0" in res.notes
    n = _scalar(pg_dict,
                "SELECT count(*) FROM kala_gochara_windows "
                "WHERE chart_id = %s AND generation = '4.1'", (CHART_ID,))
    assert n == res.rows_inserted
    bad = _scalar(pg_dict,
                  "SELECT count(*) FROM kala_gochara_windows "
                  "WHERE chart_id = %s AND generation = '4.1' AND ("
                  " window_start < '1998-01-01' OR peak_date < '1998-01-01'"
                  " OR peak_date >= '2026-04-18')", (CHART_ID,))
    assert bad == 0


# ── 3 · lifecycle refusal on real rows ───────────────────────────────────────

def test_write_contacts_refused_after_publication_real_pg(pg_dict):
    """N-7 on real rows: a published manifest refuses every subsequent write,
    and the already-written rows are byte-identical afterwards."""
    cid, _ = _seed_manifest(pg_dict, CHART_ID)
    t = datetime(2020, 1, 15, 12, 0, tzinfo=UTC)
    writer_mod.ledger.write_contacts(
        pg_dict, CHART_UUID, "4.1", cid, [_episode("Saturn", t)],
        "a25pg-saturn", bodies=["Saturn"])
    pg_dict.commit()
    before = _contact_ids(pg_dict, CHART_ID, "4.1", "Saturn")
    pg_dict.execute(
        "UPDATE kala_gochara_publication SET status = 'published' "
        "WHERE chart_id = %s AND generation = '4.1'", (CHART_ID,))
    pg_dict.commit()
    with pytest.raises(writer_mod.ledger.PublishedGenerationRefusal):
        writer_mod.ledger.write_contacts(
            pg_dict, CHART_UUID, "4.1", cid,
            [_episode("Saturn", datetime(2020, 2, 1, 12, 0, tzinfo=UTC))],
            "a25pg-saturn-2", bodies=["Saturn"])
    pg_dict.rollback()
    assert _contact_ids(pg_dict, CHART_ID, "4.1", "Saturn") == before


# ── 4 · the real generation-guard trigger (migration 1071) ───────────────────

def test_generation_guard_trigger_real_pg(pg):
    """Migration 1071 applied from its file: 'v1' rows are immutable at the
    DATABASE layer; '4.1' candidate rows are writable (the writer's DML is
    pinned to '4.1')."""
    with pg.cursor() as cur:
        cur.execute(
            "INSERT INTO kala_gochara_windows (chart_id, event_class,"
            " temporal_shape, window_start, window_end, peak_date,"
            " signed_intensity, raw_intensity, valence, is_adverse,"
            " generation)"
            " VALUES (%s, 'marriage', 'interval', '2020-01-01', '2020-02-01',"
            " '2020-01-15', 1, 1, 'gain', false, 'v1'),"
            " (%s, 'marriage', 'interval', '2020-01-01', '2020-02-01',"
            " '2020-01-15', 1, 1, 'gain', false, '4.1')",
            (CHART_ID, CHART_ID))
    # 1071's row guard raises BUILD-PROTECTED (the 'v1' sweep snapshot);
    # 'GOCHARA GENERATION GUARD' is step03_guard_n6a's '3.0' message — that
    # trigger is executed by the WP10 suite on this same instance.
    with pytest.raises(Exception, match="BUILD-PROTECTED"):
        with pg.cursor() as cur:
            cur.execute(
                "DELETE FROM kala_gochara_windows WHERE generation = 'v1'")
    with pytest.raises(Exception, match="BUILD-PROTECTED"):
        with pg.cursor() as cur:
            cur.execute(
                "UPDATE kala_gochara_windows SET generation = '4.1' "
                "WHERE generation = 'v1'")
    with pg.cursor() as cur:
        cur.execute(
            "DELETE FROM kala_gochara_windows WHERE generation = '4.1'")
    assert _scalar(pg,
                   "SELECT count(*) FROM kala_gochara_windows "
                   "WHERE generation = 'v1'") == 1
    assert _scalar(pg,
                   "SELECT count(*) FROM kala_gochara_windows "
                   "WHERE generation = '4.1'") == 0


# ── 2c · A2 half-open horizon — producer→validator→projection geometry ─────
#
# ASTRA v1.1 A2's three reproduced geometries, driven through the REAL
# producer (gochara_kernel episodes / step06b projection) into the REAL
# writer validator and the REAL ledger on disposable PostgreSQL — never
# source-string evidence. Each test fails against the pre-repair code:
#   (1) the empty "overlap" at the excluded end (t_in == h1) — pre-repair
#       _clip_to_horizon KEPT it and write_contacts INSERTed it;
#   (2) residence ingress membership with the old slack + closed end —
#       pre-repair an ingress 40µs before h0 was stamped as observed exact
#       (the writer validator then had to refuse the body), and an ingress
#       exactly at h1 produced a zero-length residence that ABORTED the
#       body with HorizonViolation;
#   (3) projection sampling — pre-repair the horizon limit was not a series
#       point, so legitimate final-day truncated activity closed at the
#       last in-domain sample instead of the horizon limit.

from datetime import date  # noqa: E402

import swisseph as swe  # noqa: E402

from services.gochara_kernel import arcs as gk_arcs  # noqa: E402
from services.gochara_kernel import episodes as gk_episodes  # noqa: E402
from services.gochara_kernel import legacy_semantics as leg  # noqa: E402
from scripts.kala_gochara_cutover import step06b_windows_projection as sb  # noqa: E402

_H_END = datetime.fromisoformat(writer_mod.HORIZON_END)  # 2026-04-18T00:00Z
_SYNTH_TOL_ARCSEC = 1e-7


def _jd(dt: datetime) -> float:
    return dt.timestamp() / 86400.0 + 2440587.5


def _dt(jd: float) -> datetime:
    return datetime.fromtimestamp((jd - 2440587.5) * 86400.0, tz=UTC)


def _daily_knots(start: date, end: date, curve) -> tuple[list[float], list[float]]:
    """Daily noon-UT knots of a synthetic curve(jd) — the same fixture shape
    as test_wp3a_kernel.daily_knots (F-15 abscissa)."""
    jds, lons = [], []
    d = start
    while d <= end:
        jd = swe.julday(d.year, d.month, d.day, 12.0)
        jds.append(jd)
        lons.append(curve(jd) % 360.0)
        d += timedelta(days=1)
    return jds, lons


# A small horizon at the END of the pinned one — every produced instant is
# inside the pinned horizon, so the REAL writer validator may run on it.
_H1 = _jd(_H_END)
_H0 = _H1 - 30.0


def test_a2_clip_to_horizon_truth_table():
    """The half-open membership predicate itself: [h0, h1), degenerate
    instantaneous events kept iff h0 <= t < h1, spans overlapping iff
    t_out > h0 and t_in < h1."""
    clip = gk_episodes._clip_to_horizon
    h0, h1 = 100.0, 200.0
    # degenerate instantaneous events
    assert clip(100.0, 100.0, (h0, h1)) == (100.0, 100.0, None, True)
    assert clip(150.0, 150.0, (h0, h1)) == (150.0, 150.0, None, True)
    assert clip(200.0, 200.0, (h0, h1))[3] is False   # the excluded end
    assert clip(99.0, 99.0, (h0, h1))[3] is False
    assert clip(201.0, 201.0, (h0, h1))[3] is False
    # spans
    assert clip(200.0, 210.0, (h0, h1))[3] is False  # empty overlap at h1
    assert clip(90.0, 100.0, (h0, h1))[3] is False   # ends exactly at h0
    assert clip(90.0, 150.0, (h0, h1)) == (100.0, 150.0, "start", True)
    assert clip(150.0, 210.0, (h0, h1)) == (150.0, 200.0, "end", True)
    assert clip(90.0, 210.0, (h0, h1)) == (100.0, 200.0, "both", True)
    assert clip(120.0, 130.0, (h0, h1)) == (120.0, 130.0, None, True)


def test_a2_orb_span_empty_overlap_at_excluded_end_dropped(pg, pg_dict):
    """The v1.1 reviewer's exact repro: Sun moving 1°/day, target 0°, orb
    5°, exact centre five days beyond the horizon end → the in-orb interval
    [h1, h1+10d] touches the half-open horizon only AT the excluded end.
    Pre-repair this produced an empty t_in == t_out == h1 episode which the
    writer validator accepted and ledger.write_contacts INSERTed. Now: the
    producer emits NOTHING and the ledger records NOTHING — while the
    neighbouring legitimate truncated span (exact 5 days INSIDE the horizon,
    in-orb through the excluded end) is kept, validated and written."""
    centre = _H1 + 5.0
    jds, lons = _daily_knots(date(2026, 3, 1), date(2026, 5, 20),
                             lambda jd: (jd - centre) * 1.0)
    idx = gk_arcs.build_arc_index("Sun", jds, lons,
                                  tolerance_arcsec=_SYNTH_TOL_ARCSEC)

    # (a) the reproduced defect geometry — nothing survives the chain
    eps = gk_episodes.solve_episodes(idx, "Sun", "conjunction", 0.0,
                                     (_H0, _H1), "orb_conj_slow",
                                     refine=False, orb_override_deg=5.0)
    assert eps == []
    writer_mod._validate_episodes_within_horizon([])
    cid, _ = _seed_manifest(pg_dict, CHART_UUID)
    writer_mod.ledger.write_contacts(pg_dict, CHART_UUID, "4.1", cid, [],
                                     "a25pg-a2-empty", bodies=["Sun"])
    pg_dict.commit()
    assert _scalar(pg_dict,
                   "SELECT count(*) FROM kala_gochara_contacts "
                   "WHERE chart_id = %s AND generation = '4.1'",
                   (CHART_ID,)) == 0

    # (b) control — the legitimate final-day truncated span IS kept: exact
    # 3 days before the limit (inside), in-orb until h1+2d (t_out clipped
    # to the exclusive limit, truncated 'end'), validator green, row written.
    eps2 = gk_episodes.solve_episodes(idx, "Sun", "conjunction", 352.0,
                                      (_H0, _H1), "orb_conj_slow",
                                      refine=False, orb_override_deg=5.0)
    assert len(eps2) == 1
    ep = eps2[0]
    assert ep.t_exact == pytest.approx(_H1 - 3.0, abs=1e-6)
    assert ep.t_out == _H1
    assert ep.truncated_at_horizon == "end"
    d = {**_episode("Sun", _dt(ep.t_exact)),
         "t_in": _dt(ep.t_in), "t_exact": _dt(ep.t_exact),
         "t_out": _dt(ep.t_out), "truncated_at_horizon": "end",
         "target_longitude_deg": 352.0}
    writer_mod._validate_episodes_within_horizon([d])  # must not raise
    writer_mod.ledger.write_contacts(pg_dict, CHART_UUID, "4.1", cid, [d],
                                     "a25pg-a2-ctrl", bodies=["Sun"])
    pg_dict.commit()
    assert _scalar(pg_dict,
                   "SELECT count(*) FROM kala_gochara_contacts "
                   "WHERE chart_id = %s AND generation = '4.1'",
                   (CHART_ID,)) == 1


def test_a2_residence_membership_half_open(pg, pg_dict):
    """Residence ingress membership is [h0, h1) with NO slack.
    (a) Ingress ~40µs BEFORE h0 (the reviewer's measured slack geometry):
        the residence is kept as a truncated span — t_exact NULL (never a
        fabricated stamp, N3), truncated 'start' — and the writer accepts
        the row (pre-repair the slack stamped the out-of-domain instant as
        observed, which the writer's own validator then refused).
    (b) Ingress exactly AT h1: the residence overlaps only at the excluded
        end and is EXCLUDED outright — no zero-length residence and no
        HorizonViolation abort (both pre-repair behaviours)."""
    slack = 40e-6 / 86400.0  # 40µs in days — the reviewer's measurement

    # (a) ingress just before the start
    jds, lons = _daily_knots(date(2026, 3, 1), date(2026, 5, 20),
                             lambda jd: jd - (_H0 - slack))
    idx = gk_arcs.build_arc_index("Mars", jds, lons,
                                  tolerance_arcsec=_SYNTH_TOL_ARCSEC)
    spans = gk_episodes.residence_spans(idx, "Mars", (0.0, 30.0),
                                        (_H0, _H1), "rashi_sign",
                                        refine=False)
    assert len(spans) == 1
    sp = spans[0]
    assert sp.t_enter == _H0
    assert sp.truncated_at_horizon == "start"
    assert sp.ingress_episode.t_exact is None
    assert sp.ingress_episode.exact_crossing is False
    assert sp.ingress_episode.truncated_at_horizon == "start"
    d = {**_episode("Mars", _dt(sp.t_enter), relation="sign_ingress"),
         "t_in": _dt(sp.t_enter), "t_exact": None, "t_out": _dt(sp.t_enter),
         "exact_crossing": False,
         "truncated_at_horizon": "start", "orb_source": "orb_ingress",
         "target_type": "rashi_sign", "target_ref": "0-30",
         "target_longitude_deg": 0.0}
    writer_mod._validate_episodes_within_horizon([d])  # must not raise
    cid, _ = _seed_manifest(pg_dict, CHART_UUID)
    writer_mod.ledger.write_contacts(pg_dict, CHART_UUID, "4.1", cid, [d],
                                     "a25pg-a2-res", bodies=["Mars"])
    pg_dict.commit()
    assert _scalar(pg_dict,
                   "SELECT count(*) FROM kala_gochara_contacts "
                   "WHERE chart_id = %s AND generation = '4.1'",
                   (CHART_ID,)) == 1

    # (b) ingress exactly at the excluded end — excluded, never an abort
    jds2, lons2 = _daily_knots(date(2026, 3, 1), date(2026, 5, 20),
                               lambda jd: jd - _H1)
    idx2 = gk_arcs.build_arc_index("Mars", jds2, lons2,
                                   tolerance_arcsec=_SYNTH_TOL_ARCSEC)
    spans2 = gk_episodes.residence_spans(idx2, "Mars", (0.0, 30.0),
                                         (_H0, _H1), "rashi_sign",
                                         refine=False)
    assert spans2 == []
    writer_mod._validate_episodes_within_horizon([])  # no HorizonViolation


def test_a2_boundary_events_at_horizon_edges():
    """Instantaneous boundary events: a root exactly AT the horizon start is
    a real crossing and is KEPT (h0 is inside [h0, h1)); a root exactly AT
    the excluded end belongs to the next domain and is EXCLUDED."""
    jds, lons = _daily_knots(date(2026, 3, 1), date(2026, 5, 20),
                             lambda jd: jd - _H0)
    idx = gk_arcs.build_arc_index("Jupiter", jds, lons,
                                  tolerance_arcsec=_SYNTH_TOL_ARCSEC)
    eps = gk_episodes.solve_boundary_episodes(idx, "Jupiter", "sign_ingress",
                                              (_H0, _H1), refine=False)
    assert any(e.t_exact == pytest.approx(_H0, abs=1e-9) for e in eps)
    assert all(e.t_exact < _H1 for e in eps)  # the +30d crossing lands ON h1

    jds2, lons2 = _daily_knots(date(2026, 3, 1), date(2026, 5, 20),
                               lambda jd: jd - _H1)
    idx2 = gk_arcs.build_arc_index("Jupiter", jds2, lons2,
                                   tolerance_arcsec=_SYNTH_TOL_ARCSEC)
    eps2 = gk_episodes.solve_boundary_episodes(idx2, "Jupiter", "sign_ingress",
                                               (_H0, _H1), refine=False)
    assert all(e.t_exact != pytest.approx(_H1, abs=1e-9) for e in eps2)


def test_a2_projection_retains_final_day_truncated_activity():
    """Projection geometry: a contact whose support runs THROUGH the horizon
    limit is legitimate final-day truncated activity — the era window's exit
    may EQUAL the exclusive limit (2026-04-18), its peak never does, and the
    writer's row validator accepts the rows. Pre-repair the horizon limit
    was not a series point and the window closed at the last in-domain
    sample instead of the limit."""
    ctx = sb.ClassContext(
        "marriage", [0.9],
        {s: True for s in leg.PERMISSION_SYSTEM_IDS},
        weight_by_target_ref={"SUN": 0.9})
    contact = {
        "contact_id": "c-finalday", "body": "Sun", "relation": "conjunction",
        "target_type": "karaka", "target_ref": "SUN",
        "_primitive": "degree_contact",
        "_t_in_jd": _H1 - 3.0, "_t_exact_jd": _H1 + 1.0, "_t_out_jd": _H1 + 5.0,
        "_target_lon_deg": 0.0, "_aspect_deg": 0.0, "_orb_deg": 10.0,
    }
    rows, report = sb.project_class_windows(
        ctx, [contact], (_H0, _H1),
        lambda jd: {"factor_by_body": {}},
        planet_pos_fn=lambda body, jd: 0.0)
    assert report["components"] >= 1
    assert rows, "final-day truncated activity produced NO window rows"
    assert max(r["window_end"] for r in rows) == date(2026, 4, 18)
    assert all(r["peak_date"] < date(2026, 4, 18) for r in rows)
    writer_mod._validate_windows_within_horizon(rows)  # no HorizonViolation
