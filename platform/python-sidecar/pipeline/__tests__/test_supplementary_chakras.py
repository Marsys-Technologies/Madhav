"""
test_supplementary_chakras.py — Tests for A17-S2 supplementary chakra reference data.

Covers:
  1. SAPTA_SHALAKA_DATA has 27 rows; shalaka_numbers all in 1-7
  2. KALANALA_DATA has 27 rows; fire_intensity values in {mild, moderate, intense}
  3. KOTA_DATA has 28 rows (including Abhijit id=28); rings all in {swami, madhya, bahya}
  4. CKN_DATA has 27 rows; d150_amsa_group values in 1-7 where not None
  5. All nakshatra_ids unique within each dataset
  6. (DB) seed_supplementary_chakras() inserts correct counts (27+27+28+27=109)
  7. (DB) second seed call inserts 0 (idempotency)

A17-S2 [BUILD-ORCH-STREAM-C-A17-S2]
"""

import os
import pytest

from pipeline.supplementary_chakras import (
    SAPTA_SHALAKA_DATA,
    KALANALA_DATA,
    KOTA_DATA,
    CKN_DATA,
    seed_supplementary_chakras,
)

# ---------------------------------------------------------------------------
# DB connection helper (mirrors test_sarvatobhadra_chakra.py pattern)
# ---------------------------------------------------------------------------

DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
DB_PORT = os.environ.get("DB_PORT", "5433")
DB_USER = os.environ.get("DB_USER", "amjis_app")
DB_PASS = os.environ.get("DB_PASS", "aYtv6SN5TwRBShzHfxN4Qz_ccW3a49qnCAA2L-VF")
DB_NAME = os.environ.get("DB_NAME", "amjis")


def _get_conn():
    """Return a psycopg2 connection, or raise if unavailable."""
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

# ---------------------------------------------------------------------------
# Test 1 — SAPTA_SHALAKA_DATA: 27 rows, shalaka_numbers in 1-7
# ---------------------------------------------------------------------------

def test_sapta_shalaka_count_and_range():
    """SAPTA_SHALAKA_DATA must have 27 rows and all shalaka_numbers in 1-7."""
    assert len(SAPTA_SHALAKA_DATA) == 27, (
        f"Expected 27 rows, got {len(SAPTA_SHALAKA_DATA)}"
    )
    for row in SAPTA_SHALAKA_DATA:
        assert 1 <= row["shalaka_number"] <= 7, (
            f"nakshatra '{row['nakshatra_name']}' has invalid shalaka_number {row['shalaka_number']}"
        )


# ---------------------------------------------------------------------------
# Test 2 — KALANALA_DATA: 27 rows, fire_intensity in allowed set
# ---------------------------------------------------------------------------

ALLOWED_INTENSITIES = {"mild", "moderate", "intense"}


def test_kalanala_count_and_intensity():
    """KALANALA_DATA must have 27 rows and all fire_intensity values in {mild, moderate, intense}."""
    assert len(KALANALA_DATA) == 27, (
        f"Expected 27 rows, got {len(KALANALA_DATA)}"
    )
    for row in KALANALA_DATA:
        assert row["fire_intensity"] in ALLOWED_INTENSITIES, (
            f"nakshatra '{row['nakshatra_name']}' has invalid fire_intensity '{row['fire_intensity']}'"
        )


# ---------------------------------------------------------------------------
# Test 3 — KOTA_DATA: 28 rows (including Abhijit id=28), rings in allowed set
# ---------------------------------------------------------------------------

ALLOWED_RINGS = {"swami", "madhya", "bahya"}


def test_kota_count_and_rings():
    """KOTA_DATA must have 28 rows, include Abhijit (id=28), and all rings in {swami, madhya, bahya}."""
    assert len(KOTA_DATA) == 28, (
        f"Expected 28 rows, got {len(KOTA_DATA)}"
    )
    ids = [row["nakshatra_id"] for row in KOTA_DATA]
    assert 28 in ids, "Abhijit (nakshatra_id=28) must be present in KOTA_DATA"
    for row in KOTA_DATA:
        assert row["ring"] in ALLOWED_RINGS, (
            f"nakshatra '{row['nakshatra_name']}' has invalid ring '{row['ring']}'"
        )


# ---------------------------------------------------------------------------
# Test 4 — CKN_DATA: 27 rows, d150_amsa_group in 1-7 where not None
# ---------------------------------------------------------------------------

def test_ckn_count_and_amsa_group():
    """CKN_DATA must have 27 rows and all non-None d150_amsa_group values in 1-7."""
    assert len(CKN_DATA) == 27, (
        f"Expected 27 rows, got {len(CKN_DATA)}"
    )
    for row in CKN_DATA:
        grp = row.get("d150_amsa_group")
        if grp is not None:
            assert 1 <= grp <= 7, (
                f"nakshatra '{row['nakshatra_name']}' has invalid d150_amsa_group {grp}"
            )


# ---------------------------------------------------------------------------
# Test 5 — nakshatra_ids unique within each dataset
# ---------------------------------------------------------------------------

def test_nakshatra_ids_unique_per_dataset():
    """nakshatra_id values must be unique within each dataset."""
    for name, dataset in [
        ("SAPTA_SHALAKA_DATA", SAPTA_SHALAKA_DATA),
        ("KALANALA_DATA", KALANALA_DATA),
        ("KOTA_DATA", KOTA_DATA),
        ("CKN_DATA", CKN_DATA),
    ]:
        ids = [row["nakshatra_id"] for row in dataset]
        assert len(ids) == len(set(ids)), (
            f"{name} has duplicate nakshatra_id values: "
            f"{[i for i in ids if ids.count(i) > 1]}"
        )


# ---------------------------------------------------------------------------
# Test 6 (DB) — seed inserts correct counts: 27+27+28+27=109
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not DB_AVAILABLE, reason="DB not reachable at 127.0.0.1:5433")
def test_seed_inserts_correct_counts():
    """seed_supplementary_chakras() must insert 27+27+28+27=109 rows total."""
    conn = _get_conn()
    try:
        # Clear for clean test
        with conn.cursor() as cur:
            cur.execute("DELETE FROM l1_sapta_shalaka")
            cur.execute("DELETE FROM l1_kalanala_chakra")
            cur.execute("DELETE FROM l1_kota_chakra")
            cur.execute("DELETE FROM l1_ckn_chakra")
            conn.commit()

        result = seed_supplementary_chakras(conn)

        assert result["sapta_shalaka"] == 27, (
            f"Expected 27 sapta_shalaka rows, got {result['sapta_shalaka']}"
        )
        assert result["kalanala"] == 27, (
            f"Expected 27 kalanala rows, got {result['kalanala']}"
        )
        assert result["kota"] == 28, (
            f"Expected 28 kota rows, got {result['kota']}"
        )
        assert result["ckn"] == 27, (
            f"Expected 27 ckn rows, got {result['ckn']}"
        )
        total = sum(result.values())
        assert total == 109, f"Expected 109 total rows inserted, got {total}"
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Test 7 (DB) — second seed call inserts 0 rows (idempotency)
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not DB_AVAILABLE, reason="DB not reachable at 127.0.0.1:5433")
def test_seed_idempotent():
    """Seed from empty → 109 rows; second seed → 0 rows (true idempotency check)."""
    conn = _get_conn()
    try:
        # Clear tables so the first seed is a genuine fresh insert
        with conn.cursor() as cur:
            cur.execute("DELETE FROM l1_ckn_chakra")
            cur.execute("DELETE FROM l1_kota_chakra")
            cur.execute("DELETE FROM l1_kalanala_chakra")
            cur.execute("DELETE FROM l1_sapta_shalaka")
            conn.commit()
        # First seed — must insert 109 rows total
        result1 = seed_supplementary_chakras(conn)
        assert sum(result1.values()) == 109, (
            f"Expected 109 rows on first seed, got {sum(result1.values())}"
        )
        # Second seed — must return all zeros
        result2 = seed_supplementary_chakras(conn)
        assert result2["sapta_shalaka"] == 0, (
            f"Expected 0 sapta_shalaka on second seed, got {result2['sapta_shalaka']}"
        )
        assert result2["kalanala"] == 0, (
            f"Expected 0 kalanala on second seed, got {result2['kalanala']}"
        )
        assert result2["kota"] == 0, (
            f"Expected 0 kota on second seed, got {result2['kota']}"
        )
        assert result2["ckn"] == 0, (
            f"Expected 0 ckn on second seed, got {result2['ckn']}"
        )
    finally:
        conn.close()
