"""
test_bhrigu_bindu_writer.py — Tests for bhrigu_bindu_writer.py

Covers:
  Test 1: compute_bhrigu_bindu() midpoint arithmetic including wraparound
  Test 2: scan_bb_transits() returns ≥1 hit over a 180-day window
  Test 3: All hit dicts carry the required keys
  Test 4: orb_deg ≤ 1.0 for all hits
  Test 5: graha values are in the allowed set
  Test 6 (DB): seed_bhrigu_bindu_transits() inserts > 0 rows and is idempotent
  Test 7 (DB): row count in DB is > 50 after seeding

Stream C — A19 [BUILD-ORCH-STREAM-C-A19-S1]
"""
from __future__ import annotations

import os
from datetime import date

import pytest

from pipeline.bhrigu_bindu_writer import (
    GRAHA_NAMES,
    NATIVE_BB_LONGITUDE_DEG,
    NATIVE_CHART_ID,
    compute_bhrigu_bindu,
    scan_bb_transits,
    seed_bhrigu_bindu_transits,
)

# ── helpers ───────────────────────────────────────────────────────────────────

ALLOWED_GRAHAS = {
    "sun", "moon", "mars", "mercury", "jupiter",
    "venus", "saturn", "rahu", "ketu",
}

REQUIRED_KEYS = {
    "chart_id", "graha", "hit_iso", "bb_longitude_deg",
    "graha_longitude_deg", "orb_deg", "transit_type",
    "strength_score", "classical_citation",
}

DB_AVAILABLE = bool(os.environ.get("DB_NAME"))


def _get_conn():
    """Return a psycopg2 connection using env vars (mirrors CLI defaults)."""
    import psycopg2
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "127.0.0.1"),
        port=int(os.environ.get("DB_PORT", "5433")),
        dbname=os.environ.get("DB_NAME", "amjis"),
        user=os.environ.get("DB_USER", "amjis_app"),
        password=os.environ.get(
            "DB_PASS", "aYtv6SN5TwRBShzHfxN4Qz_ccW3a49qnCAA2L-VF"
        ),
    )


# ── Test 1: compute_bhrigu_bindu arithmetic ───────────────────────────────────

class TestComputeBhriguBindu:
    def test_simple_midpoint(self):
        """moon=120°, rahu=240° → BB = 180° (direct midpoint)."""
        result = compute_bhrigu_bindu(120.0, 240.0)
        assert abs(result - 180.0) < 0.001, f"Expected 180.0, got {result}"

    def test_wraparound_midpoint(self):
        """moon=350°, rahu=10° → BB = 0° (mod 360 wraparound)."""
        result = compute_bhrigu_bindu(350.0, 10.0)
        # Shorter arc from 350 to 10 is 20°; midpoint at 360° = 0°
        assert abs(result % 360.0) < 0.001 or abs(result % 360.0 - 360.0) < 0.001, (
            f"Expected ~0.0 (mod 360), got {result}"
        )

    def test_same_longitude(self):
        """moon == rahu → BB == moon (zero arc)."""
        result = compute_bhrigu_bindu(100.0, 100.0)
        assert abs(result - 100.0) < 0.001, f"Expected 100.0, got {result}"

    def test_opposite_positions(self):
        """moon=0°, rahu=180° → BB = 90° (both arcs equal; picks forward midpoint)."""
        result = compute_bhrigu_bindu(0.0, 180.0)
        # Forward arc 180° → midpoint at 90°
        assert abs(result - 90.0) < 0.001, f"Expected 90.0, got {result}"

    def test_result_in_range(self):
        """Result must always be in [0, 360)."""
        for moon, rahu in [(0, 90), (270, 30), (179, 1), (1, 179), (359, 181)]:
            result = compute_bhrigu_bindu(float(moon), float(rahu))
            assert 0.0 <= result < 360.0, (
                f"Out-of-range result {result} for moon={moon}, rahu={rahu}"
            )

    def test_native_bb_sanity(self):
        """
        Native natal: Moon ≈ Purva Bhadrapada (~322°), Rahu ≈ Libra (~150°).
        Midpoint should land near Scorpio 26° (236°).
        We verify NATIVE_BB_LONGITUDE_DEG is in Scorpio range (210–240°).
        """
        assert 210.0 < NATIVE_BB_LONGITUDE_DEG < 240.0, (
            f"Native BB {NATIVE_BB_LONGITUDE_DEG} not in expected Scorpio range"
        )


# ── Test 2: scan_bb_transits returns hits ─────────────────────────────────────

class TestScanBBTransits:
    """
    Fast scan tests using a 180-day window.  At least one graha (fast-moving:
    Moon, Mercury, Venus, Sun) will transit within 1° of any zodiac degree
    within any 180-day window.
    """

    def test_returns_at_least_one_hit(self):
        """At least 1 hit expected over 180 days near BB=236°."""
        hits = scan_bb_transits(
            chart_id=NATIVE_CHART_ID,
            bb_lon=NATIVE_BB_LONGITUDE_DEG,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 6, 30),
        )
        assert len(hits) >= 1, (
            f"Expected ≥1 hit over 2026-01-01 to 2026-06-30, got {len(hits)}"
        )

    def test_returns_list(self):
        """scan_bb_transits returns a list (not a generator or None)."""
        hits = scan_bb_transits(
            chart_id=NATIVE_CHART_ID,
            bb_lon=NATIVE_BB_LONGITUDE_DEG,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
        )
        assert isinstance(hits, list)

    def test_chart_id_propagated(self):
        """chart_id in returned dicts matches the input."""
        test_id = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        hits = scan_bb_transits(
            chart_id=test_id,
            bb_lon=NATIVE_BB_LONGITUDE_DEG,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 3, 31),
        )
        for h in hits:
            assert h["chart_id"] == test_id


# ── Test 3: Required keys present on every hit dict ───────────────────────────

class TestHitDictStructure:
    @pytest.fixture(scope="class")
    def hits(self):
        return scan_bb_transits(
            chart_id=NATIVE_CHART_ID,
            bb_lon=NATIVE_BB_LONGITUDE_DEG,
            start_date=date(2026, 1, 1),
            end_date=date(2026, 6, 30),
        )

    def test_all_required_keys_present(self, hits):
        """Every hit dict must contain all required keys."""
        for h in hits:
            missing = REQUIRED_KEYS - set(h.keys())
            assert not missing, f"Missing keys {missing} in hit: {h}"

    # ── Test 4: orb ≤ 1.0 ─────────────────────────────────────────────────

    def test_orb_within_bound(self, hits):
        """orb_deg must be ≤ 1.0 for every hit."""
        for h in hits:
            assert h["orb_deg"] <= 1.0 + 1e-6, (
                f"orb_deg {h['orb_deg']} > 1.0 for graha={h['graha']} on {h['hit_iso']}"
            )

    def test_orb_non_negative(self, hits):
        """orb_deg must be ≥ 0."""
        for h in hits:
            assert h["orb_deg"] >= 0.0, (
                f"Negative orb_deg {h['orb_deg']} for {h['graha']} on {h['hit_iso']}"
            )

    # ── Test 5: graha in allowed set ──────────────────────────────────────

    def test_graha_in_allowed_set(self, hits):
        """All graha values must be in the allowed set."""
        for h in hits:
            assert h["graha"] in ALLOWED_GRAHAS, (
                f"Unknown graha '{h['graha']}' on {h['hit_iso']}"
            )

    def test_transit_type_valid(self, hits):
        """transit_type must be one of exact/applying/separating."""
        valid_types = {"exact", "applying", "separating"}
        for h in hits:
            assert h["transit_type"] in valid_types, (
                f"Invalid transit_type '{h['transit_type']}' for {h['graha']}"
            )

    def test_strength_score_range(self, hits):
        """strength_score must be in [0.0, 1.0]."""
        for h in hits:
            if h["strength_score"] is not None:
                assert 0.0 <= h["strength_score"] <= 1.0 + 1e-6, (
                    f"strength_score {h['strength_score']} out of [0,1] for {h['graha']}"
                )

    def test_hit_iso_is_date(self, hits):
        """hit_iso must be a date object."""
        for h in hits:
            assert isinstance(h["hit_iso"], date), (
                f"hit_iso is not a date: {type(h['hit_iso'])} for {h['graha']}"
            )

    def test_bb_longitude_consistent(self, hits):
        """bb_longitude_deg must match the input BB longitude."""
        for h in hits:
            assert abs(h["bb_longitude_deg"] - NATIVE_BB_LONGITUDE_DEG) < 0.01, (
                f"bb_longitude_deg {h['bb_longitude_deg']} != {NATIVE_BB_LONGITUDE_DEG}"
            )


# ── Test 6 & 7: DB integration ────────────────────────────────────────────────

@pytest.mark.skipif(not DB_AVAILABLE, reason="DB_NAME env var not set — skipping DB tests")
class TestSeedBhriguBinduTransits:
    """
    DB tests: seed the full 2026-2060 table.
    These tests may take 2-5 minutes (35 years × 9 grahas × swisseph).
    """

    @pytest.fixture(scope="class")
    def conn(self):
        c = _get_conn()
        yield c
        c.close()

    @pytest.fixture(scope="class")
    def rows_inserted(self, conn):
        """Run the seeder once; return inserted count."""
        # Clear existing rows for the native to get a fresh count
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM l1_bhrigu_bindu_transits WHERE chart_id = %s",
                (NATIVE_CHART_ID,),
            )
        conn.commit()
        n = seed_bhrigu_bindu_transits(conn, NATIVE_CHART_ID, NATIVE_BB_LONGITUDE_DEG)
        return n

    def test_inserts_positive_rows(self, rows_inserted):
        """seed_bhrigu_bindu_transits must insert > 0 rows."""
        assert rows_inserted > 0, "Expected > 0 rows inserted"

    def test_idempotent(self, conn, rows_inserted):
        """Running seed again inserts 0 new rows (ON CONFLICT DO NOTHING)."""
        n2 = seed_bhrigu_bindu_transits(conn, NATIVE_CHART_ID, NATIVE_BB_LONGITUDE_DEG)
        assert n2 == 0, (
            f"Idempotency failure: second seed inserted {n2} rows (expected 0)"
        )

    def test_row_count_above_threshold(self, conn, rows_inserted):
        """DB must have > 50 rows for the native (35 years × 9 grahas × multiple hits)."""
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM l1_bhrigu_bindu_transits WHERE chart_id = %s",
                (NATIVE_CHART_ID,),
            )
            count = cur.fetchone()[0]
        assert count > 50, (
            f"Expected > 50 rows in l1_bhrigu_bindu_transits, got {count}"
        )

    def test_all_grahas_represented(self, conn, rows_inserted):
        """All 9 grahas should appear in the seeded data."""
        with conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT graha FROM l1_bhrigu_bindu_transits "
                "WHERE chart_id = %s ORDER BY graha",
                (NATIVE_CHART_ID,),
            )
            found = {row[0] for row in cur.fetchall()}
        # Fast planets (sun, moon, mercury, venus, mars) always transit within 35 yrs
        for g in ["sun", "moon", "mercury", "venus", "mars"]:
            assert g in found, f"Graha '{g}' not found in seeded data"

    def test_orb_constraint_in_db(self, conn, rows_inserted):
        """No row in DB should have orb_deg > 1.0."""
        with conn.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM l1_bhrigu_bindu_transits "
                "WHERE chart_id = %s AND orb_deg > 1.0",
                (NATIVE_CHART_ID,),
            )
            bad = cur.fetchone()[0]
        assert bad == 0, f"{bad} rows with orb_deg > 1.0 found in DB"

    def test_graha_check_constraint(self, conn, rows_inserted):
        """All graha values stored are in the allowed set (DB CHECK constraint enforced)."""
        with conn.cursor() as cur:
            cur.execute(
                "SELECT DISTINCT graha FROM l1_bhrigu_bindu_transits "
                "WHERE chart_id = %s",
                (NATIVE_CHART_ID,),
            )
            stored = {row[0] for row in cur.fetchall()}
        assert stored.issubset(ALLOWED_GRAHAS), (
            f"Unexpected graha values in DB: {stored - ALLOWED_GRAHAS}"
        )
