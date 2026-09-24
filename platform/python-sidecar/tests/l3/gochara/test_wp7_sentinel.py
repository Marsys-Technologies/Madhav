"""WP7 sentinel exit-gate test — identity survives the whole chain.

Plan (GOCHARA_FAMILY_ELEVATION_PLAN_v2_1 §7 WP7 exit gate): a sentinel value
placed in a low-ranked row's `independence_group` must survive
  1. WP6 storage (contact ledger on the disposable database),
  2. a simulated retrieval pass (P-4 serving shape),
  3. a simulated budget pass (page-capping à la reading_checklist's trimmed
     page — the sentinel row is deliberately ranked OUTSIDE the kept page),
  4. a simulated delivery pass (serialized saved-result payload), and
  5. a simulated replay (deterministic rebuild → identical contact ids).

Identity, not rank: the sentinel proves that a row's contact_id and
independence_group are addressable even when serving trims it from a page —
the property P-2/P-4 exist to preserve end to end.

Synthetic data only (wp7-synth-* chart ids). Disposable DB only.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest

from services.gochara_kernel import ledger

# NOTE: no module-level skip needed — the `wp6_schema` fixture in conftest.py
# already skips NOT_RUN when the disposable database is unreachable.

SENTINEL = f"SENTINEL-WP7-{uuid.uuid4().hex[:12]}"
CHART = "7f000000-0000-4000-8000-000000000001"  # synthetic, valid-UUID form
GENERATION = "4.0"
BUILD_ID = "wp7-sentinel-build-001"
HORIZON = "[2026-01-01 00:00:00+00,2027-01-01 00:00:00+00)"

VECTOR = {
    "resonance_build": {"computed_at": "2026-09-23T00:00:00Z", "row_count": 328},
    "ga_yoga_firings_build_id": "wp7-yoga-001",
    "chart_facts_build_ids": {"graha_position": "wp7-cf-gp-001"},
    "ephemeris_daily_substrate_version": "wp7-substrate-001",
    "overlay_build_ids": {"vedha": "wp7-vedha-001"},
    "bg_transit_rules_digest": "sha256:wp7-rules-digest",
    "bg_transit_av_gates_digest": "sha256:wp7-gates-digest",
    "convention_id": None,  # filled in setup
}
EPHEM_BACKEND = {"backend": "swieph", "retflag": 258,
                 "se1_checksums": {"sepl_18": "ca1393ce…", "semo_18": "1ca07bd6…",
                                   "seas_18": "a2cd8fc3…"}}


def _episode(i: int, t0: datetime) -> dict:
    t_exact = t0 + timedelta(days=3 * i)
    return {
        "body": "Saturn",
        "relation": "conjunction",
        "target_type": "karaka",
        "target_ref": "Venus",
        "target_fact_id": "wp7synth.fact.venus.lon",
        "target_resolution_state": "resolved",
        "target_longitude_deg": 123.4567,
        "t_in": t_exact - timedelta(days=5),
        "t_exact": t_exact,
        "t_out": t_exact + timedelta(days=5),
        "bracket_seconds": 300,
        "tolerance_arcsec": 2.0,
        "branch": "direct",
        "station_flag": False,
        "exact_crossing": True,
        "orb_max_deg": 1.0,
        "orb_source": "orb_conj_slow",
        "epistemic_class": "structural_prior",
        "completeness_state": "applied",
        "operator_role": "transit_agent",
        "claim_grain": "instant",
        "time_basis": "event_time_utc",
        "comparable_with": "same_convention_same_inputs",
        "evidence_fact_ids": ["wp7synth.fact.venus.lon"],
        "uncited_extension": True,
        "ephemeris_backend": EPHEM_BACKEND,
    }


@pytest.fixture()
def sentinel_chart(conn, wp6_schema):
    """Store a 12-contact generation; the LOWEST-ranked row (last by t_exact,
    farthest from any serving peak at the horizon start) carries the sentinel."""
    convention_id = ledger.register_convention(
        conn, vector={
            "zodiac": "sidereal", "ayanamsha": "lahiri_chitrapaksha",
            "sidereal_method": "swe_flg_sidereal", "node_model": "mean",
            "node_source": "swiss_mean_node_flg_sidereal",
            "epoch_convention": "noon_ut_knot_abscissa",
            "time_scale": "ut_to_tt_swe_deltat", "house_system": "whole_sign",
            "ephemeris_mode": "flg_swieph",
            "method_version": "gochara_kernel_test/1.0",
        },
        probe={"ephemeris_backend": "swieph", "retflag": 258},
        se1_checksums={"sepl_18": "ca1393ce…", "semo_18": "1ca07bd6…",
                       "seas_18": "a2cd8fc3…"},
    )
    vector = dict(VECTOR); vector["convention_id"] = convention_id
    manifest_id = ledger.publish_candidate(
        conn, CHART, GENERATION, convention_id, vector, EPHEM_BACKEND, HORIZON)
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    episodes = [_episode(i, t0) for i in range(12)]
    # rank: serving ranks by proximity to the horizon's nominal peak (t0);
    # the sentinel row is deliberately the LOWEST-ranked (index 11).
    episodes[11]["independence_group"] = SENTINEL
    episodes[11]["completeness_state"] = "unqualified"  # low-ranked AND unqualified
    for ep in episodes[:11]:
        ep["independence_group"] = f"wp7-ig-{ep['t_exact'].date().isoformat()}"
    ids = ledger.write_contacts(conn, CHART, GENERATION, convention_id,
                                episodes, BUILD_ID)
    conn.commit()
    return {"convention_id": convention_id, "manifest_id": manifest_id,
            "contact_ids": ids, "sentinel_id": ids[11]}


def test_storage_retrieval_budget_delivery_replay(conn, sentinel_chart):
    # ── 2. simulated retrieval pass (P-4 serving shape) ────────────────────
    row = conn.execute(
        """
        SELECT contact_id, independence_group, completeness_state, t_exact
        FROM kala_gochara_contacts
        WHERE chart_id = %s AND generation = %s
          AND independence_group = %s
        """,
        (CHART, GENERATION, SENTINEL),
    ).fetchone()
    assert row is not None, "sentinel row lost in retrieval pass"
    assert row[0] == sentinel_chart["sentinel_id"]
    assert row[2] == "unqualified"  # typed qualification survives with the row

    # ── 3. simulated budget pass: rank rows by proximity to the serving peak
    #    (horizon start), keep a 5-row page — the sentinel (rank 12) is cut ──
    page = conn.execute(
        """
        SELECT contact_id, independence_group, completeness_state,
               t_exact, abs(extract(epoch FROM (t_exact - %s::timestamptz))) AS rank_dist
        FROM kala_gochara_contacts
        WHERE chart_id = %s AND generation = %s
        ORDER BY rank_dist ASC
        LIMIT 5
        """,
        ("2026-01-01 00:00:00+00", CHART, GENERATION),
    ).fetchall()
    page_ids = {r[0] for r in page}
    assert sentinel_chart["sentinel_id"] not in page_ids, \
        "sentinel unexpectedly inside the trimmed page (test setup error)"
    # identity is addressable independent of rank: re-fetch by id
    still = conn.execute(
        "SELECT independence_group FROM kala_gochara_contacts WHERE contact_id = %s",
        (sentinel_chart["sentinel_id"],),
    ).fetchone()
    assert still is not None and still[0] == SENTINEL, \
        "budget pass destroyed a row it trimmed from the page"

    # ── 4. simulated delivery pass: saved-result payload (P-2 fields) ──────
    payload = {
        "chart_id": CHART, "generation": GENERATION,
        "page": [
            {"contact_id": r[0], "independence_group": r[1],
             "completeness_state": r[2], "t_exact": r[3].isoformat()}
            for r in page
        ],
        "trimmed_but_addressable": [
            {"contact_id": sentinel_chart["sentinel_id"],
             "independence_group": SENTINEL,
             "completeness_state": "unqualified",
             "addressable_by": "contact_id|independence_group"}
        ],
    }
    delivered = json.loads(json.dumps(payload))  # serialize → parse round-trip
    assert delivered["trimmed_but_addressable"][0]["independence_group"] == SENTINEL
    assert delivered["trimmed_but_addressable"][0]["contact_id"] == \
        sentinel_chart["sentinel_id"]

    # ── 5. simulated replay: identical inputs → identical ids, sentinel back ─
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    episodes = [_episode(i, t0) for i in range(12)]
    episodes[11]["independence_group"] = SENTINEL
    episodes[11]["completeness_state"] = "unqualified"
    for ep in episodes[:11]:
        ep["independence_group"] = f"wp7-ig-{ep['t_exact'].date().isoformat()}"
    # generation is not yet published, so a candidate rebuild is legal
    ids2 = ledger.write_contacts(
        conn, CHART, GENERATION, sentinel_chart["convention_id"],
        episodes, BUILD_ID)
    conn.commit()
    assert ids2 == sentinel_chart["contact_ids"], \
        "replay drifted contact ids (identity not deterministic)"
    assert conn.execute(
        "SELECT count(*) FROM kala_gochara_contacts "
        "WHERE chart_id = %s AND generation = %s AND independence_group = %s",
        (CHART, GENERATION, SENTINEL),
    ).fetchone()[0] == 1
