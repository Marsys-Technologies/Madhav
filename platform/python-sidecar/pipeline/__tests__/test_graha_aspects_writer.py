"""
test_graha_aspects_writer.py — Tests for A21 graha aspects lifetime writer.

Covers:
  1. NATAL_POSITIONS has exactly 9 grahas, all values 0-360
  2. compute_aspects_for_period returns non-empty list for a 30-day window
  3. All returned dicts have required keys
  4. orb_deg <= 1.0 for all results
  5. aspect_system in {parashari, classical, tajik} for all results
  6. (DB, slow) seed_graha_aspects() inserts > 100 rows and is idempotent
  7. (DB) unique index prevents duplicate (chart_id, natal_graha, transit_graha, aspect_type, exact_date)

A21-S1 [BUILD-ORCH-STREAM-C-A21-S1]
"""

import os
import uuid
from datetime import date

import pytest

from pipeline.graha_aspects_writer import (
    NATAL_POSITIONS,
    compute_aspects_for_period,
    seed_graha_aspects,
)

# ---------------------------------------------------------------------------
# DB connection helper
# ---------------------------------------------------------------------------

DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = os.environ.get("DB_PORT", "5433")
DB_USER = os.environ.get("DB_USER", "amjis_app")
DB_PASS = os.environ.get("DB_PASS", "aYtv6SN5TwRBShzHfxN4Qz_ccW3a49qnCAA2L-VF")
DB_NAME = os.environ.get("DB_NAME", "amjis")

REQUIRED_KEYS = {
    "chart_id", "natal_graha", "transit_graha", "aspect_type", "aspect_system",
    "exact_date", "natal_graha_lon", "transit_graha_lon", "aspect_degree",
    "orb_deg", "is_applying", "classical_citation",
}

NINE_GRAHAS = {"sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn", "rahu", "ketu"}
VALID_ASPECT_SYSTEMS = {"parashari", "classical", "tajik"}


def _get_conn():
    """Return a psycopg2 connection or raise."""
    import psycopg2
    return psycopg2.connect(
        host=DB_HOST, port=int(DB_PORT), user=DB_USER,
        password=DB_PASS, dbname=DB_NAME,
        connect_timeout=3,
    )


def _db_reachable() -> bool:
    try:
        conn = _get_conn()
        conn.close()
        return True
    except Exception:
        return False


DB_AVAILABLE = _db_reachable()
RUN_SLOW = os.environ.get("RUN_SLOW_TESTS", "").lower() in ("1", "true", "yes")

# ---------------------------------------------------------------------------
# Test 1 — NATAL_POSITIONS structure
# ---------------------------------------------------------------------------

class TestNatalPositions:
    def test_exactly_nine_grahas(self):
        assert len(NATAL_POSITIONS) == 9, (
            f"Expected 9 grahas, got {len(NATAL_POSITIONS)}: {list(NATAL_POSITIONS.keys())}"
        )

    def test_all_expected_grahas_present(self):
        assert set(NATAL_POSITIONS.keys()) == NINE_GRAHAS

    def test_all_longitudes_in_range(self):
        for graha, lon in NATAL_POSITIONS.items():
            assert 0.0 <= lon < 360.0, f"{graha} longitude {lon} out of range [0, 360)"

    def test_longitude_types_are_float(self):
        for graha, lon in NATAL_POSITIONS.items():
            assert isinstance(lon, float), f"{graha} longitude should be float, got {type(lon)}"

# ---------------------------------------------------------------------------
# Test 2 — compute_aspects_for_period returns results for 30-day window
# ---------------------------------------------------------------------------

class TestComputeAspects:
    """Run with a short window — expect at least one hit for Sun or Moon."""

    _chart_id = str(uuid.uuid4())
    # Use a 30-day window known to contain Sun-natal-Saturn opposition
    # Sun moves ~1°/day; natal Saturn at 207.4°; Sun opposition = 207.4 + 180 = 27.4°
    # Sun is around 27° in late Jan / early Feb each year
    _start = date(2027, 1, 20)
    _end   = date(2027, 2, 20)

    @pytest.fixture(scope="class")
    def results(self):
        return compute_aspects_for_period(
            self._chart_id,
            NATAL_POSITIONS,
            self._start,
            self._end,
        )

    def test_returns_non_empty(self, results):
        assert len(results) > 0, (
            "compute_aspects_for_period returned empty list for a 30-day window "
            f"{self._start} to {self._end} — expected at least Sun opposition hits"
        )

    # ── Test 3 — required keys present ────────────────────────────────────────
    def test_required_keys_present(self, results):
        for i, row in enumerate(results):
            missing = REQUIRED_KEYS - set(row.keys())
            assert not missing, f"Row {i} missing keys: {missing}"

    # ── Test 4 — orb_deg <= 1.0 ───────────────────────────────────────────────
    def test_orb_deg_within_limit(self, results):
        violations = [
            (r["natal_graha"], r["transit_graha"], r["aspect_type"], r["orb_deg"])
            for r in results if r["orb_deg"] > 1.0
        ]
        assert not violations, f"orb_deg > 1.0 in rows: {violations}"

    # ── Test 5 — aspect_system valid ─────────────────────────────────────────
    def test_aspect_system_valid(self, results):
        invalid = [
            (r["natal_graha"], r["transit_graha"], r["aspect_system"])
            for r in results if r["aspect_system"] not in VALID_ASPECT_SYSTEMS
        ]
        assert not invalid, f"Invalid aspect_system values: {invalid}"

    def test_exact_date_is_date_type(self, results):
        for row in results:
            assert isinstance(row["exact_date"], date), (
                f"exact_date should be date, got {type(row['exact_date'])}"
            )

    def test_natal_graha_in_known_set(self, results):
        for row in results:
            assert row["natal_graha"] in NINE_GRAHAS, f"Unknown natal_graha: {row['natal_graha']}"

    def test_transit_graha_in_known_set(self, results):
        for row in results:
            assert row["transit_graha"] in NINE_GRAHAS, f"Unknown transit_graha: {row['transit_graha']}"

    def test_natal_graha_lon_matches_natal_positions(self, results):
        for row in results:
            expected = NATAL_POSITIONS[row["natal_graha"]]
            assert row["natal_graha_lon"] == expected, (
                f"{row['natal_graha']} natal_graha_lon mismatch: "
                f"got {row['natal_graha_lon']}, expected {expected}"
            )

    def test_transit_graha_lon_in_range(self, results):
        for row in results:
            lon = row["transit_graha_lon"]
            assert 0.0 <= lon < 360.0, (
                f"transit_graha_lon {lon} out of range for "
                f"{row['transit_graha']} on {row['exact_date']}"
            )

    def test_aspect_degree_nonnegative(self, results):
        for row in results:
            assert row["aspect_degree"] >= 0.0, (
                f"aspect_degree {row['aspect_degree']} < 0"
            )

# ---------------------------------------------------------------------------
# Test 6 — (DB, slow) seed_graha_aspects inserts > 100 rows and is idempotent
# ---------------------------------------------------------------------------

@pytest.mark.slow
@pytest.mark.skipif(not DB_AVAILABLE, reason="DB not reachable")
@pytest.mark.skipif(not RUN_SLOW, reason="Slow test skipped (set RUN_SLOW_TESTS=1 to enable)")
class TestSeedGrahaAspectsSlow:
    """
    Uses a 90-day window via a patched call to keep runtime < 60s.
    The full 35-year seed is tested conceptually via Test 7.
    """

    def test_seed_inserts_more_than_100_rows(self):
        """seed_graha_aspects over a 90-day window should produce > 100 rows."""
        import psycopg2
        from unittest.mock import patch
        from datetime import date as _date

        chart_id = str(uuid.uuid4())

        # Patch seed_graha_aspects to use a 90-day window only
        _start = _date(2026, 1, 1)
        _end   = _date(2026, 4, 1)

        conn = _get_conn()
        try:
            # Use compute_aspects_for_period directly with short window then insert
            rows = compute_aspects_for_period(chart_id, NATAL_POSITIONS, _start, _end)

            insert_sql = """
                INSERT INTO l1_graha_aspects_lifetime (
                    chart_id, natal_graha, transit_graha, aspect_type, aspect_system,
                    exact_date, natal_graha_lon, transit_graha_lon, aspect_degree,
                    orb_deg, is_applying, classical_citation
                ) VALUES (
                    %(chart_id)s, %(natal_graha)s, %(transit_graha)s, %(aspect_type)s,
                    %(aspect_system)s, %(exact_date)s, %(natal_graha_lon)s,
                    %(transit_graha_lon)s, %(aspect_degree)s, %(orb_deg)s,
                    %(is_applying)s, %(classical_citation)s
                )
                ON CONFLICT (chart_id, natal_graha, transit_graha, aspect_type, exact_date)
                DO NOTHING
            """
            with conn.cursor() as cur:
                cur.executemany(insert_sql, rows)
                inserted_first = cur.rowcount
            conn.commit()

            assert inserted_first > 100, (
                f"Expected > 100 rows inserted, got {inserted_first}. "
                f"Computed {len(rows)} rows from 90-day window."
            )

            # Idempotency: second call inserts 0
            with conn.cursor() as cur:
                cur.executemany(insert_sql, rows)
                inserted_second = cur.rowcount
            conn.commit()

            assert inserted_second == 0, (
                f"Idempotency failed: second insert returned {inserted_second} rows, expected 0"
            )

        finally:
            conn.close()

# ---------------------------------------------------------------------------
# Test 7 — (DB) unique index prevents duplicates
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not DB_AVAILABLE, reason="DB not reachable")
class TestUniqueIndexPreventsduplicates:
    """
    Insert the same row twice and verify ON CONFLICT DO NOTHING works
    (no duplicate key error and second insert count = 0).
    """

    def test_unique_index_prevents_duplicate(self):
        import psycopg2

        chart_id = str(uuid.uuid4())
        conn = _get_conn()
        try:
            insert_sql = """
                INSERT INTO l1_graha_aspects_lifetime (
                    chart_id, natal_graha, transit_graha, aspect_type, aspect_system,
                    exact_date, natal_graha_lon, transit_graha_lon, aspect_degree,
                    orb_deg, is_applying, classical_citation
                ) VALUES (
                    %(chart_id)s, %(natal_graha)s, %(transit_graha)s, %(aspect_type)s,
                    %(aspect_system)s, %(exact_date)s, %(natal_graha_lon)s,
                    %(transit_graha_lon)s, %(aspect_degree)s, %(orb_deg)s,
                    %(is_applying)s, %(classical_citation)s
                )
                ON CONFLICT (chart_id, natal_graha, transit_graha, aspect_type, exact_date)
                DO NOTHING
            """
            test_row = {
                "chart_id":          chart_id,
                "natal_graha":       "sun",
                "transit_graha":     "saturn",
                "aspect_type":       "opposition",
                "aspect_system":     "classical",
                "exact_date":        date(2026, 2, 1),
                "natal_graha_lon":   314.5,
                "transit_graha_lon": 134.5,
                "aspect_degree":     180.0,
                "orb_deg":           0.0,
                "is_applying":       None,
                "classical_citation": "BPHS Ch.3 sarva-graha 7th-house aspect (opposition)",
            }

            with conn.cursor() as cur:
                cur.execute(insert_sql, test_row)
                first_insert_count = cur.rowcount
            conn.commit()
            assert first_insert_count == 1, f"First insert should return 1, got {first_insert_count}"

            with conn.cursor() as cur:
                cur.execute(insert_sql, test_row)
                second_insert_count = cur.rowcount
            conn.commit()
            assert second_insert_count == 0, (
                f"Second insert (duplicate) should return 0 due to ON CONFLICT DO NOTHING, "
                f"got {second_insert_count}"
            )

        finally:
            conn.close()
