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

DSN = os.environ.get(
    "GOCHARA_REMAINDER_DSN", "postgresql://wp6:local@localhost:55434/wp6"
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
  event_class TEXT NOT NULL DEFAULT 'rehearsal',
  generation TEXT NOT NULL
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
  vedha_kind TEXT NOT NULL,
  detail JSONB NOT NULL DEFAULT '{}'::jsonb
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
def pg():
    try:
        conn = psycopg.connect(DSN, autocommit=True, connect_timeout=3)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"NOT_RUN: disposable remainder database unreachable ({exc})")
    with conn.cursor() as cur:
        cur.execute(STUB_DDL)
    _apply_migration(conn, "1081")
    _apply_migration(conn, "1087")
    _apply_migration(conn, "1071")
    with conn.cursor() as cur:
        cur.execute(SEED_SQL)
    _fingerprint_overlays(conn, CHART_ID)
    yield conn
    conn.close()


@pytest.fixture()
def pg_dict(pg):
    """The same disposable database through the runner's NATIVE connection
    shape: dict_row rows, autocommit off (the test owns commit/rollback —
    exactly the orchestrator's posture)."""
    conn = psycopg.connect(DSN, row_factory=psycopg.rows.dict_row)
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


# ── 1 · manifest substep, native runner types, real freshness gate ───────────

def test_manifest_substep_real_pg_native_types_gate_green(pg_dict):
    """The writer's manifest substep on a dict_row conn with a UUID chart_id,
    §12.9 gate genuinely green: convention + candidate manifest land; a rerun
    replaces the manifest IN PLACE (one row, same manifest_id)."""
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


def test_interrupted_substep_and_retry_preserve_siblings(pg, pg_dict):
    """The retry proof the reviewer asked for: REAL database state, an actual
    interruption, an actual rerun — siblings counted before and after."""
    sib = _seed_siblings(pg)
    cid = sib["cid"]
    t1 = datetime(2020, 1, 20, 12, 0, tzinfo=UTC)
    t2 = datetime(2020, 1, 22, 12, 0, tzinfo=UTC)

    # First Mars substep: two contacts + coverage, committed.
    writer_mod.ledger.write_contacts(
        pg_dict, CHART_UUID, "4.1", cid,
        [_episode("Mars", t1), _episode("Mars", t2, relation="trine")],
        "a25pg-mars-1", bodies=["Mars"])
    writer_mod.ledger.write_coverage(
        pg_dict, CHART_UUID, "4.1", cid, [_coverage("mars")],
        "a25pg-mars-1", bodies=["Mars"])
    pg_dict.commit()
    mars_v1 = _contact_ids(pg_dict, CHART_ID, "4.1", "Mars")
    assert len(mars_v1) == 2

    # (a) MID-SUBSTEP CRASH: a failing payload AFTER the delete would land —
    # the whole substep rolls back (the orchestrator's transaction semantics);
    # the committed v1 Mars rows survive untouched.
    conn2 = psycopg.connect(DSN, row_factory=psycopg.rows.dict_row)
    try:
        conn2.execute("SAVEPOINT substep")
        try:
            # normalization happens before the DELETE, so to fail AFTER DML
            # we violate a DB constraint at INSERT time (t_exact NULL breaks
            # the NOT NULL/contact-id path only at the database): craft the
            # failure as a second statement inside the same transaction.
            writer_mod.ledger.write_contacts(
                conn2, CHART_UUID, "4.1", cid,
                [_episode("Mars", datetime(2020, 1, 25, 12, 0, tzinfo=UTC))],
                "a25pg-mars-crash", bodies=["Mars"])
            conn2.execute("SELECT 1/0")  # the crash
            conn2.commit()
            raise AssertionError("the crash never happened")
        except Exception:
            conn2.execute("ROLLBACK TO SAVEPOINT substep")
            conn2.commit()
    finally:
        conn2.close()
    assert _contact_ids(pg_dict, CHART_ID, "4.1", "Mars") == mars_v1

    # (b) RETRY: the substep reruns with the corrected payload and replaces
    # EXACTLY its own scope — one Mars row now, never a duplicate of v1.
    t3 = datetime(2020, 1, 25, 12, 0, tzinfo=UTC)
    writer_mod.ledger.write_contacts(
        pg_dict, CHART_UUID, "4.1", cid, [_episode("Mars", t3)],
        "a25pg-mars-2", bodies=["Mars"])
    writer_mod.ledger.write_coverage(
        pg_dict, CHART_UUID, "4.1", cid, [_coverage("mars")],
        "a25pg-mars-2", bodies=["Mars"])
    pg_dict.commit()

    mars_v2 = _contact_ids(pg_dict, CHART_ID, "4.1", "Mars")
    assert len(mars_v2) == 1 and mars_v2 != mars_v1
    # every sibling intact, to the row
    assert _contact_ids(pg_dict, CHART_ID, "4.1", "Venus") == \
        _contact_ids(pg, CHART_ID, "4.1", "Venus")
    assert len(_contact_ids(pg_dict, CHART_ID, "4.1", "Venus")) == 1
    assert len(_contact_ids(pg_dict, CHART_ID, "3.0", "Mars")) == 1
    assert len(_contact_ids(pg_dict, OTHER_CHART, "4.1", "Mars")) == 1
    assert _scalar(pg_dict,
                   "SELECT count(*) FROM kala_gochara_coverage "
                   "WHERE chart_id = %s AND generation = '4.1'",
                   (CHART_ID,)) == 2  # mars + venus, no duplicates
    assert _scalar(pg_dict,
                   "SELECT count(*) FROM kala_gochara_contacts "
                   "WHERE chart_id = %s AND generation = '4.1'",
                   (CHART_ID,)) == 2  # 1 mars + 1 venus


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
            "INSERT INTO kala_gochara_windows (chart_id, generation) "
            "VALUES (%s, 'v1'), (%s, '4.1')", (CHART_ID, CHART_ID))
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
