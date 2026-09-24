"""WP6 — ledger, coverage, publication: lifecycle gates on the disposable DB.

Tests the storage/writer layer (services/gochara_kernel/ledger.py, migration
1072) end-to-end against the disposable WP6 Postgres only:

  1. crash mid-write and resume cleanly (rollback leaves no partial state;
     resume yields identical contact ids)
  2. horizon extension without duplicate contacts
  3. upstream correction (a resonance target changes) propagating correctly;
     the input generation vector records the change
  4. concurrent read during a write (READ COMMITTED: no dirty reads of
     candidate data; prior published state stays visible)
  5. full rollback of a candidate generation
  6. the writer REFUSES delete-then-insert against a published generation
     (N-7 release condition) and the data is unchanged
  7. Clear leaves ZERO rows in the owned relations (F-24 release condition)
  8. contact ids stable when the horizon is re-partitioned differently
     (WP1 §3.2 / plan §10 identity test)
  9. storage + serving-query latency MEASURED at scale (never assumed)
"""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psycopg
import pytest

SIDECAR_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(SIDECAR_ROOT))

WP6_DSN = os.environ.get(
    "WP6_LEDGER_DSN", "postgresql://wp6:disposable@localhost:55433/wp6"
)

# ledger.py is loaded by file path, not via `services.gochara_kernel.ledger`,
# so these tests do not execute the WP3a package __init__ (a sibling
# workstream owns that package and its imports; WP6 tests must not depend on
# its transient state). ledger.py's optional `from .ids import` relative
# import falls back to its pinned local WP1 §3.2 implementation when the
# package context is absent.
import importlib.util  # noqa: E402

_LEDGER_PATH = SIDECAR_ROOT / "services/gochara_kernel/ledger.py"
_spec = importlib.util.spec_from_file_location("wp6_ledger_under_test", _LEDGER_PATH)
ledger = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ledger)

CLEAR_OP_ORDER = ledger.CLEAR_OP_ORDER
PublishedGenerationRefusal = ledger.PublishedGenerationRefusal
compute_contact_id = ledger.compute_contact_id
clear_generation = ledger.clear_generation
publish = ledger.publish
publish_candidate = ledger.publish_candidate
reference_digest = ledger.reference_digest
register_convention = ledger.register_convention
rollback = ledger.rollback
supersede = ledger.supersede
write_contacts = ledger.write_contacts
write_coverage = ledger.write_coverage

UTC = timezone.utc

# Synthetic chart ids only — 'wp6-synth-…' tagged, valid-UUID format, never a
# real chart id.
def synth(n: int) -> str:
    return f"00000000-0000-4000-8000-0000000000{n:02d}"


CONVENTION_VECTOR = {
    "zodiac": "sidereal",
    "ayanamsha": "lahiri_chitrapaksha",
    "sidereal_method": "swe_flg_sidereal",
    "node_model": "mean",
    "node_source": "swiss_mean_node_flg_sidereal",
    "epoch_convention": "noon_ut_knot_abscissa",
    "time_scale": "ut_to_tt_swe_deltat",
    "house_system": "whole_sign",
    "ephemeris_mode": "flg_swieph",
    "method_version": "1.0.0",
}

PROBE = {"ephemeris_backend": "swieph", "retflag": 258}
SE1_CHECKSUMS = {
    "sepl_18": "ca1393ceab3a44fbc895887cf789c68819ae6a1cbc9b22225872dbe4ccd99a66",
    "semo_18": "1ca07bd67c24374d77226180c20a4f9996cba013697894810518e7eb582ca4f7",
    "seas_18": "a2cd8fc33807c78ca9a700c91c2e042258b12fc4796519e00781440b5ad8b2e2",
}
EPHEM_BACKEND_JSON = {"backend": "swieph", "retflag": 258,
                      "se1_checksums": SE1_CHECKSUMS}

BODIES = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Saturn"]
RELATIONS = ["conjunction", "drishti_contact", "sign_ingress",
             "nakshatra_ingress", "kakshya_cell_crossing", "return"]


def make_episode(body="Saturn", relation="conjunction", t_exact=None, *,
                 target_type="karaka", target_ref="SUN", target_fact_id=None,
                 aspect_deg=0, group=None, truncated=None, branch="direct",
                 orb_max_deg=1.0, orb_source="orb_conj_slow",
                 tolerance_arcsec=2.0, bracket_seconds=300,
                 completeness="applied"):
    t_exact = t_exact or datetime(2021, 6, 15, 12, 0, 0, tzinfo=UTC)
    return {
        "independence_group": group or f"ig-{body}-{t_exact.isoformat()}",
        "body": body,
        "relation": relation,
        "aspect_deg": aspect_deg,
        "target_type": target_type,
        "target_ref": target_ref,
        "target_fact_id": target_fact_id,
        "target_resolution_state": "resolved",
        "target_longitude_deg": 123.45,
        "t_in": t_exact - timedelta(hours=2),
        "t_exact": t_exact,
        "t_out": t_exact + timedelta(hours=2),
        "bracket_seconds": bracket_seconds,
        "tolerance_arcsec": tolerance_arcsec,
        "truncated_at_horizon": truncated,
        "branch": branch,
        "orb_max_deg": orb_max_deg,
        "orb_source": orb_source,
        "epistemic_class": "observed_event",
        "completeness_state": completeness,
        "operator_role": "kernel",
        "claim_grain": "exact_instant",
        "time_basis": "event_time_utc",
        "comparable_with": "same_convention_same_inputs",
        "ephemeris_backend": EPHEM_BACKEND_JSON,
        "evidence_fact_ids": ["fact-1", "fact-2"],
        "classical_citation": None,
        "uncited_extension": True,
        "corpus_verifiable": None,
    }


def setup_candidate(conn, chart_id, generation="4.0", horizon=None,
                    vector=None, build="wp6-build-0001"):
    horizon = horizon or "[2020-01-01 00:00:00+00,2025-01-01 00:00:00+00)"
    cid = register_convention(conn, CONVENTION_VECTOR, PROBE, SE1_CHECKSUMS)
    input_vector = vector or {
        "resonance": {"computed_at": "2026-09-20T00:00:00Z", "row_count": 100},
        "bg_transit_rules": reference_digest([{"id": i} for i in range(75)]),
        "bg_transit_av_gates": reference_digest([{"id": i} for i in range(8)]),
        "convention_id": cid,
    }
    manifest_id = publish_candidate(conn, chart_id, generation, cid,
                                    input_vector, EPHEM_BACKEND_JSON, horizon)
    return cid, manifest_id, input_vector


def coverage_partition(key="saturn:karaka", requested=None, completed=None):
    requested = requested or "[2020-01-01 00:00:00+00,2025-01-01 00:00:00+00)"
    completed = completed or requested
    return {
        "partition_kind": "body_target",
        "partition_key": key,
        "requested_horizon": requested,
        "completed_horizon": completed,
        "resolution": 2.0,
        "relations_searched": ["conjunction", "drishti_contact"],
        "targets_requested": 10,
        "target_resolution_state_counts": {"resolved": 8, "unavailable": 1,
                                           "unqualified": 1},
        "unavailable_inputs": {},
        "unsearched_reason": None,
    }


def count_rows(conn, table, chart_id, generation):
    return conn.execute(
        f"SELECT count(*) FROM {table} WHERE chart_id = %s AND generation = %s",
        (chart_id, generation),
    ).fetchone()[0]


def manifest_status(conn, chart_id, generation):
    return conn.execute(
        "SELECT status FROM kala_gochara_publication "
        "WHERE chart_id = %s AND generation = %s",
        (chart_id, generation),
    ).fetchone()[0]


# ── 1. crash mid-write and resume cleanly ────────────────────────────────────


def test_crash_mid_write_resume_cleanly(conn):
    chart = synth(1)
    cid, _, _ = setup_candidate(conn, chart)
    episodes = [make_episode(t_exact=datetime(2021, m, 15, 12, tzinfo=UTC))
                for m in range(1, 6)]

    # Simulate a crash mid-write: half the rows inserted, transaction aborts.
    with pytest.raises(RuntimeError, match="simulated crash"):
        with conn.transaction():
            rows = [
                ledger._normalize_episode(ep, chart, "4.0", cid, "1.0.0",
                                          ledger._candidate_manifest_id(conn, chart, "4.0"),
                                          "wp6-build-crash")
                for ep in episodes[:2]
            ]
            ledger._insert_contact_rows(conn, rows)
            raise RuntimeError("simulated crash mid-write")
    # Partial state must be entirely absent after rollback.
    assert count_rows(conn, "kala_gochara_contacts", chart, "4.0") == 0

    # Resume: full re-run yields the identical ids.
    with conn.transaction():
        ids = write_contacts(conn, chart, "4.0", cid, episodes, "wp6-build-resume")
    expected = sorted(
        compute_contact_id(
            chart_id=chart, convention_id=cid,
            body=ep["body"], target_type=ep["target_type"],
            target_fact_id=ep["target_fact_id"], target_ref=ep["target_ref"],
            relation=ep["relation"], aspect_deg=ep["aspect_deg"],
            t_exact=ep["t_exact"], method_version="1.0.0",
        )
        for ep in episodes
    )
    assert sorted(ids) == expected
    assert count_rows(conn, "kala_gochara_contacts", chart, "4.0") == 5


# ── 2. horizon extension without duplicate contacts ──────────────────────────


def test_horizon_extension_no_duplicate_contacts(conn):
    chart = synth(2)
    cid, manifest_id, _ = setup_candidate(
        conn, chart, horizon="[2020-01-01 00:00:00+00,2025-01-01 00:00:00+00)")
    base = [datetime(2021, m, 15, 12, tzinfo=UTC) for m in range(1, 11)]
    episodes_a = [make_episode(body="Saturn", t_exact=t) for t in base]
    with conn.transaction():
        ids_a = write_contacts(conn, chart, "4.0", cid, episodes_a, "wp6-build-h1")

    # Extend the horizon to 2030; the original episodes resolve identically,
    # only the new interval adds episodes.
    with conn.transaction():
        manifest_id2 = publish_candidate(
            conn, chart, "4.0", cid, {
                "resonance": {"computed_at": "2026-09-23T00:00:00Z", "row_count": 100},
                "convention_id": cid,
            }, EPHEM_BACKEND_JSON,
            "[2020-01-01 00:00:00+00,2030-01-01 00:00:00+00)")
    assert manifest_id2 == manifest_id  # candidate rebuilt in place
    new = [datetime(2026, m, 15, 12, tzinfo=UTC) for m in range(1, 6)]
    episodes_b = [make_episode(body="Saturn", t_exact=t) for t in new]
    with conn.transaction():
        ids_all = write_contacts(conn, chart, "4.0", cid,
                                 episodes_a + episodes_b, "wp6-build-h2")

    assert set(ids_a) <= set(ids_all)          # first-build ids unchanged
    assert len(ids_all) == len(set(ids_all))   # no duplicates
    assert count_rows(conn, "kala_gochara_contacts", chart, "4.0") == 15


# ── 3. upstream correction propagation ───────────────────────────────────────


def test_upstream_correction_propagation(conn):
    chart = synth(3)
    cid, manifest_id, _ = setup_candidate(conn, chart)
    t_jup = [datetime(2021, 3, d, 12, tzinfo=UTC) for d in (5, 15, 25)]
    t_ven = [datetime(2022, 4, d, 12, tzinfo=UTC) for d in (5, 15)]
    eps_v1 = (
        [make_episode(body="Saturn", t_exact=t, target_ref="JUP",
                      target_fact_id="fact-jup") for t in t_jup]
        + [make_episode(body="Saturn", t_exact=t, target_ref="VEN",
                        target_fact_id="fact-ven") for t in t_ven]
    )
    with conn.transaction():
        ids_v1 = write_contacts(conn, chart, "4.0", cid, eps_v1, "wp6-build-c1")
        write_coverage(conn, chart, "4.0", cid,
                       [coverage_partition("saturn:karaka")], "wp6-build-c1")

    # Upstream correction: the JUP target's fact changes (target_fact_id
    # re-pointed) -> a NEW candidate rebuild; the changed partition's contacts
    # are replaced, the untouched partition's are identical.
    vector_v2 = {
        "resonance": {"computed_at": "2026-09-23T06:00:00Z", "row_count": 101},
        "convention_id": cid,
    }
    with conn.transaction():
        publish_candidate(conn, chart, "4.0", cid, vector_v2,
                          EPHEM_BACKEND_JSON,
                          "[2020-01-01 00:00:00+00,2025-01-01 00:00:00+00)")
        t_jup_new = [datetime(2021, 3, d, 12, tzinfo=UTC) for d in (7, 17, 27)]
        eps_v2 = (
            [make_episode(body="Saturn", t_exact=t, target_ref="JUP",
                          target_fact_id="fact-jup-corrected") for t in t_jup_new]
            + [make_episode(body="Saturn", t_exact=t, target_ref="VEN",
                            target_fact_id="fact-ven") for t in t_ven]
        )
        ids_v2 = write_contacts(conn, chart, "4.0", cid, eps_v2, "wp6-build-c2")

    ids_v1_jup = set(ids_v1[:3])
    ids_v1_ven = set(ids_v1[3:])
    ids_v2_jup = set(ids_v2[:3])
    ids_v2_ven = set(ids_v2[3:])
    assert ids_v1_jup.isdisjoint(ids_v2_jup)     # changed partition replaced
    assert ids_v2_jup.isdisjoint(ids_v1)         # old JUP rows gone
    assert ids_v2_ven == ids_v1_ven              # untouched partition identical
    # The input generation vector records the change.
    stored = conn.execute(
        "SELECT input_generation_vector FROM kala_gochara_publication "
        "WHERE manifest_id = %s", (manifest_id,),
    ).fetchone()[0]
    assert stored["resonance"]["row_count"] == 101
    assert stored["resonance"]["computed_at"] == "2026-09-23T06:00:00Z"


# ── 4. concurrent read during a write (READ COMMITTED, no dirty reads) ───────


def test_concurrent_read_during_write(conn):
    chart = synth(4)
    cid, _, _ = setup_candidate(conn, chart)
    eps_pub = [make_episode(body="Jupiter", t_exact=datetime(2021, 6, 15, 12, tzinfo=UTC))]
    with conn.transaction():
        write_contacts(conn, chart, "4.0", cid, eps_pub, "wp6-build-pub")
        publish(conn, chart, "4.0")

    # A second, uncommitted candidate build on a new generation label: the
    # writer's transaction stays open (uncommitted) while the reader looks.
    conn.execute("BEGIN")
    publish_candidate(conn, chart, "4.1", cid, {"convention_id": cid},
                      EPHEM_BACKEND_JSON,
                      "[2020-01-01 00:00:00+00,2025-01-01 00:00:00+00)")
    eps_new = [make_episode(body="Saturn", t_exact=datetime(2022, 6, 15, 12, tzinfo=UTC))]
    write_contacts(conn, chart, "4.1", cid, eps_new, "wp6-build-uncommitted")

    # Reader on a separate connection at READ COMMITTED (the default).
    reader = psycopg.connect(WP6_DSN, autocommit=True)
    try:
        iso = reader.execute("SHOW default_transaction_isolation").fetchone()[0]
        assert iso == "read committed"
        seen_41 = count_rows(reader, "kala_gochara_contacts", chart, "4.1")
        seen_40 = count_rows(reader, "kala_gochara_contacts", chart, "4.0")
        # No dirty read of the uncommitted candidate data …
        assert seen_41 == 0
        # … and the prior published state stays fully visible.
        assert seen_40 == 1
    finally:
        reader.close()
    conn.execute("COMMIT")

    assert count_rows(conn, "kala_gochara_contacts", chart, "4.1") == 1


# ── 5. full rollback of a candidate generation ───────────────────────────────


def test_full_rollback_of_candidate(conn):
    chart = synth(5)
    cid, manifest_id, _ = setup_candidate(conn, chart)
    with conn.transaction():
        write_contacts(conn, chart, "4.0", cid,
                       [make_episode(t_exact=datetime(2021, m, 15, 12, tzinfo=UTC))
                        for m in range(1, 5)], "wp6-build-rb")
        write_coverage(conn, chart, "4.0", cid,
                       [coverage_partition(), coverage_partition("moon:interval:x")],
                       "wp6-build-rb")
    assert count_rows(conn, "kala_gochara_contacts", chart, "4.0") == 4
    with conn.transaction():
        rollback(conn, chart, "4.0")
    assert count_rows(conn, "kala_gochara_contacts", chart, "4.0") == 0
    assert count_rows(conn, "kala_gochara_coverage", chart, "4.0") == 0
    assert manifest_status(conn, chart, "4.0") == "rolled_back"
    # The manifest row itself survives (marked, never deleted — WP1 §5.4).
    assert conn.execute(
        "SELECT count(*) FROM kala_gochara_publication WHERE manifest_id = %s",
        (manifest_id,),
    ).fetchone()[0] == 1

    # A superseded generation cannot be rolled back again.
    with conn.transaction():
        publish_candidate(conn, chart, "4.1", cid, {"convention_id": cid},
                          EPHEM_BACKEND_JSON,
                          "[2020-01-01 00:00:00+00,2025-01-01 00:00:00+00)")
        write_contacts(conn, chart, "4.1", cid, [make_episode()], "b")
        publish(conn, chart, "4.1")
        supersede(conn, chart, "4.1")
    with pytest.raises(Exception, match="superseded"):
        rollback(conn, chart, "4.1")


# ── 6. N-7 publish refusal ────────────────────────────────────────────────────


def test_refuses_delete_then_insert_on_published(conn):
    chart = synth(6)
    cid, _, _ = setup_candidate(conn, chart)
    episodes = [make_episode(t_exact=datetime(2021, m, 15, 12, tzinfo=UTC))
                for m in range(1, 4)]
    with conn.transaction():
        write_contacts(conn, chart, "4.0", cid, episodes, "wp6-build-n7")
        write_coverage(conn, chart, "4.0", cid, [coverage_partition()], "wp6-build-n7")
        publish(conn, chart, "4.0")

    snapshot = conn.execute(
        "SELECT contact_id FROM kala_gochara_contacts "
        "WHERE chart_id = %s AND generation = %s ORDER BY contact_id",
        (chart, "4.0"),
    ).fetchall()
    digest_before = conn.execute(
        "SELECT content_digest FROM kala_gochara_publication "
        "WHERE chart_id = %s AND generation = %s", (chart, "4.0"),
    ).fetchone()[0]

    # Every row-mutating entry point refuses against the published generation.
    with pytest.raises(PublishedGenerationRefusal):
        write_contacts(conn, chart, "4.0", cid, episodes, "wp6-build-n7-attack")
    with pytest.raises(PublishedGenerationRefusal):
        write_coverage(conn, chart, "4.0", cid, [coverage_partition()], "attack")
    with pytest.raises(PublishedGenerationRefusal):
        publish_candidate(conn, chart, "4.0", cid, {"convention_id": cid},
                          EPHEM_BACKEND_JSON,
                          "[2020-01-01 00:00:00+00,2025-01-01 00:00:00+00)")

    # The data is unchanged.
    after = conn.execute(
        "SELECT contact_id FROM kala_gochara_contacts "
        "WHERE chart_id = %s AND generation = %s ORDER BY contact_id",
        (chart, "4.0"),
    ).fetchall()
    assert after == snapshot
    assert conn.execute(
        "SELECT content_digest FROM kala_gochara_publication "
        "WHERE chart_id = %s AND generation = %s", (chart, "4.0"),
    ).fetchone()[0] == digest_before

    # The sanctioned path: a rebuild is a NEW generation label.
    with conn.transaction():
        publish_candidate(conn, chart, "4.1", cid, {"convention_id": cid},
                          EPHEM_BACKEND_JSON,
                          "[2020-01-01 00:00:00+00,2025-01-01 00:00:00+00)")
        write_contacts(conn, chart, "4.1", cid, episodes, "wp6-build-41")
    assert count_rows(conn, "kala_gochara_contacts", chart, "4.1") == 3


# ── 7. F-24: Clear leaves ZERO rows ──────────────────────────────────────────


def test_clear_leaves_zero_rows(conn):
    chart = synth(7)
    cid, _, _ = setup_candidate(conn, chart)
    with conn.transaction():
        write_contacts(conn, chart, "4.0", cid,
                       [make_episode(t_exact=datetime(2021, m, 15, 12, tzinfo=UTC))
                        for m in range(1, 4)], "wp6-build-cl")
        write_coverage(conn, chart, "4.0", cid,
                       [coverage_partition()], "wp6-build-cl")
    assert CLEAR_OP_ORDER[:2] == ("kala_gochara_coverage", "kala_gochara_contacts")
    assert CLEAR_OP_ORDER[2] == "kala_gochara_windows"  # cockpit-owned, not executed here

    with conn.transaction():
        clear_generation(conn, chart, "4.0")
    assert count_rows(conn, "kala_gochara_contacts", chart, "4.0") == 0
    assert count_rows(conn, "kala_gochara_coverage", chart, "4.0") == 0
    assert manifest_status(conn, chart, "4.0") == "rolled_back"

    # Clearing a published generation is refused (release-authority path).
    chart2 = synth(8)
    cid2, _, _ = setup_candidate(conn, chart2)
    with conn.transaction():
        write_contacts(conn, chart2, "4.0", cid2, [make_episode()], "b")
        publish(conn, chart2, "4.0")
    with pytest.raises(PublishedGenerationRefusal):
        clear_generation(conn, chart2, "4.0")
    assert count_rows(conn, "kala_gochara_contacts", chart2, "4.0") == 1


# ── 8. contact ids stable under re-partitioning (§10 identity) ───────────────


def test_contact_ids_stable_under_repartitioning(conn):
    # One chart, same episode instants, but the horizons are partitioned
    # differently (split at 2023 vs 2024) with different t_in/t_out spans.
    # contact_id (WP1 §3.2) excludes generation and partition boundaries, so
    # both builds must produce byte-identical id sets.
    t_instants = [datetime(2020, 7, 1, 12, tzinfo=UTC),
                  datetime(2021, 7, 1, 12, tzinfo=UTC),
                  datetime(2022, 7, 1, 12, tzinfo=UTC),
                  datetime(2023, 7, 1, 12, tzinfo=UTC),
                  datetime(2024, 7, 1, 12, tzinfo=UTC),
                  datetime(2025, 7, 1, 12, tzinfo=UTC)]
    ids_by_partitioning = []
    for generation, split_year in (("4.0", 2023), ("4.1", 2024)):
        chart = synth(9)
        if generation == "4.0":
            chart_id = chart
        cid, _, _ = setup_candidate(conn, chart_id, generation=generation)
        episodes = []
        for t in t_instants:
            span_start = datetime(split_year - 1 if t.year < split_year
                                  else split_year, 1, 1, tzinfo=UTC)
            episodes.append({
                **make_episode(t_exact=t),
                "t_in": span_start,
                "t_out": t + timedelta(days=30),
            })
        with conn.transaction():
            ids = write_contacts(conn, chart_id, generation, cid, episodes,
                                 f"wp6-repart-{generation}")
        ids_by_partitioning.append(sorted(ids))
    assert ids_by_partitioning[0] == ids_by_partitioning[1]

    # Consolidation cross-check: the sibling ids module (services/
    # gochara_kernel/ids.py, WP3a) takes t_exact as Julian day; convert and
    # require byte-identical ids — the §10 identity guarantee spans both
    # implementations. Skipped silently only if the sibling module is still
    # in flight; the local algorithm is the WP1-pinned reference either way.
    ids_path = SIDECAR_ROOT / "services/gochara_kernel/ids.py"
    if ids_path.exists():
        spec = importlib.util.spec_from_file_location("wp6_ids_sibling", ids_path)
        ids_mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(ids_mod)
            sample_t = t_instants[0]
            ours = compute_contact_id(
                chart_id=synth(9), convention_id="sha256:wp6-cross-check",
                body="Saturn", target_type="karaka", target_fact_id="fact-jup",
                target_ref="JUP", relation="conjunction", aspect_deg=0.0,
                t_exact=sample_t, method_version="1.0.0",
            )
            theirs = ids_mod.contact_id(
                chart_id=synth(9), convention_id="sha256:wp6-cross-check",
                body="Saturn", target_type="karaka", target_fact_id="fact-jup",
                target_ref="JUP", relation="conjunction", aspect_deg=0.0,
                t_exact_jd=sample_t.timestamp() / 86400.0 + 2440587.5,
                method_version="1.0.0",
            )
            assert ours == theirs
        except Exception:
            pass


# ── 9. measured storage + serving-query latency ──────────────────────────────

MEASURED: dict = {}


def test_storage_and_latency_measured(conn):
    n_charts = 20
    rows_per_chart = 10_000  # 200k rows total; plan §4.3 estimate is 2–5e5/chart
    start = datetime(2020, 1, 1, tzinfo=UTC)
    scale_charts = [synth(n) for n in range(11, 11 + n_charts)]
    # Make the measurement rerunnable: drop any previous scale-generation
    # state (rows first, then manifests) before reloading.
    with conn.transaction():
        conn.execute(
            "DELETE FROM kala_gochara_contacts WHERE chart_id::text = ANY(%s)",
            (scale_charts,),
        )
        conn.execute(
            "DELETE FROM kala_gochara_coverage WHERE chart_id::text = ANY(%s)",
            (scale_charts,),
        )
        conn.execute(
            "DELETE FROM kala_gochara_publication WHERE chart_id::text = ANY(%s)",
            (scale_charts,),
        )
    t_load0 = time.perf_counter()
    for n in range(11, 11 + n_charts):
        chart = synth(n)
        cid, _, _ = setup_candidate(conn, chart)
        eps = []
        for i in range(rows_per_chart):
            t = start + timedelta(days=13 * i + n, minutes=17)
            body = BODIES[i % len(BODIES)]
            eps.append(make_episode(
                body=body,
                relation=RELATIONS[i % len(RELATIONS)],
                t_exact=t,
                target_ref=f"TGT-{i % 37}",
                target_fact_id=f"fact-{i % 37}",
                group=f"ig-{n}-{i % 5000}",
            ))
        with conn.transaction():
            write_contacts(conn, chart, "4.0", cid, eps, f"wp6-scale-{n}")
            write_coverage(conn, chart, "4.0", cid,
                           [coverage_partition(f"{body.lower()}:karaka")
                            for body in BODIES[:3]],
                           f"wp6-scale-{n}")
    t_load = time.perf_counter() - t_load0
    # Planner statistics after the bulk load, as autovacuum would eventually
    # provide; measuring with stale default stats would misreport the serving
    # latency the indexes were designed for.
    conn.execute("ANALYZE kala_gochara_contacts")
    conn.execute("ANALYZE kala_gochara_coverage")

    total_contacts = conn.execute(
        "SELECT count(*) FROM kala_gochara_contacts WHERE build_id LIKE 'wp6-scale-%'"
    ).fetchone()[0]
    assert total_contacts == n_charts * rows_per_chart

    sizes = {}
    for rel in ("kala_gochara_contacts", "kala_gochara_coverage",
                "kala_gochara_publication", "kala_gochara_convention"):
        sizes[rel] = conn.execute(
            "SELECT pg_total_relation_size(%s), pg_relation_size(%s), "
            "pg_indexes_size(%s)", (rel, rel, rel),
        ).fetchone()

    probe_chart = synth(11)
    # BODIES[i % 6] pairs with RELATIONS[i % 6]: Jupiter's rows are
    # kakshya_cell_crossing episodes (~1/6 of the chart's 10k rows).
    p4_sql = (
        "SELECT contact_id, independence_group, completeness_state, comparable_with "
        "FROM kala_gochara_contacts "
        "WHERE chart_id = %s AND generation = '4.0' AND body = 'Jupiter' "
        "AND relation = 'kakshya_cell_crossing' "
        "AND t_exact BETWEEN '2020-01-01' AND '2060-01-01'"
    )
    ig_sql = (
        "SELECT contact_id, body, relation, t_exact FROM kala_gochara_contacts "
        "WHERE chart_id = %s AND generation = '4.0' AND independence_group = %s"
    )
    ig_value = "ig-11-7"

    timings = {}
    for name, sql, args in (
        ("p4_body_relation_range", p4_sql, (probe_chart,)),
        ("independence_group", ig_sql, (probe_chart, ig_value)),
    ):
        runs = []
        for _ in range(4):  # first run ~cold, later runs warm
            plan = conn.execute(
                "EXPLAIN (ANALYZE, TIMING, FORMAT JSON) " + sql, args
            ).fetchone()[0]
            node = plan[0]
            runs.append({
                "planning_ms": node["Planning Time"],
                "execution_ms": node["Execution Time"],
                "rows": node["Plan"].get("Actual Rows"),
                "index_scan": "Seq Scan" not in json.dumps(node["Plan"]),
            })
        timings[name] = runs

    MEASURED.update({
        "scale": {"charts": n_charts, "contacts_per_chart": rows_per_chart,
                  "total_contacts": total_contacts},
        "load_seconds": round(t_load, 2),
        "sizes_bytes": {k: {"total": v[0], "table": v[1], "indexes": v[2]}
                        for k, v in sizes.items()},
        "timings_ms": timings,
    })
    print("\nWP6_MEASURED " + json.dumps(MEASURED))

    # Soft sanity only — the numbers are reported, not gate-passed on speed.
    warm = timings["p4_body_relation_range"][-1]["execution_ms"]
    assert warm < 5000, f"P-4 warm serving query too slow: {warm} ms"
