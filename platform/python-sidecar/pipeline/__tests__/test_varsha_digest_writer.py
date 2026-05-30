"""
test_varsha_digest_writer.py — Tests for varsha_digest_writer.py

Covers:
  Test 1: SADE_SATI_BY_YEAR has keys for all years 2026-2060 (35 years)
  Test 2: all sade_sati values in {active, approaching, leaving, inactive}
  Test 3: VIMSHOTTARI_SCHEDULE ad_by_year covers 2026-2060
  Test 4 (DB): seed_varsha_digest inserts exactly 35 rows; idempotent on re-run
  Test 5 (DB): 2036 row has vimshottari_md='ketu' (MD transition year)
  Test 6 (DB): 2048-2049 rows have sade_sati_status='active'
  Test 7: year_theme is non-empty string for all years

Stream C — A22 [BUILD-ORCH-STREAM-C-A22-S1]
"""
from __future__ import annotations

import os

import pytest

from pipeline.varsha_digest_writer import (
    DIGEST_YEARS,
    SADE_SATI_BY_YEAR,
    VIMSHOTTARI_SCHEDULE,
    _compose_year_theme,
    _md_for_year,
    seed_varsha_digest,
)

# ── constants ─────────────────────────────────────────────────────────────────

VALID_SADE_SATI = {"active", "approaching", "leaving", "inactive"}
NATIVE_CHART_ID = "362f9f17-95a5-490b-a5a7-027d3e0efda0"

DB_AVAILABLE = bool(os.environ.get("DB_NAME"))


def _get_conn():
    """Return a psycopg2 connection using env vars."""
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


# ── Test 1: SADE_SATI_BY_YEAR completeness ───────────────────────────────────


class TestSadeSatiCompleteness:
    def test_all_35_years_present(self):
        """SADE_SATI_BY_YEAR must have exactly 35 keys: 2026-2060 inclusive."""
        expected = set(range(2026, 2061))
        actual = set(SADE_SATI_BY_YEAR.keys())
        missing = expected - actual
        extra = actual - expected
        assert not missing, f"Missing sade sati keys: {sorted(missing)}"
        assert not extra, f"Unexpected sade sati keys: {sorted(extra)}"

    def test_count_is_35(self):
        """Exactly 35 entries."""
        assert len(SADE_SATI_BY_YEAR) == 35


# ── Test 2: all sade_sati values are valid ───────────────────────────────────


class TestSadeSatiValues:
    def test_all_values_in_allowed_set(self):
        """Every sade sati status must be one of the four allowed values."""
        invalid = {
            year: status
            for year, status in SADE_SATI_BY_YEAR.items()
            if status not in VALID_SADE_SATI
        }
        assert not invalid, f"Invalid sade sati statuses: {invalid}"

    def test_known_active_years(self):
        """2048 and 2049 must be 'active' (Saturn in Aquarius = natal Moon sign)."""
        assert SADE_SATI_BY_YEAR[2048] == "active"
        assert SADE_SATI_BY_YEAR[2049] == "active"

    def test_2026_is_leaving(self):
        """2026: Saturn just left Pisces — status should be 'leaving'."""
        assert SADE_SATI_BY_YEAR[2026] == "leaving"

    def test_2047_is_approaching(self):
        """2047: Saturn entering Capricorn — approaching status."""
        assert SADE_SATI_BY_YEAR[2047] == "approaching"


# ── Test 3: VIMSHOTTARI ad_by_year completeness ──────────────────────────────


class TestVimshottariSchedule:
    def test_ad_by_year_covers_all_digest_years(self):
        """ad_by_year must have an entry for every year in DIGEST_YEARS."""
        ad_by_year = VIMSHOTTARI_SCHEDULE["ad_by_year"]
        missing = [y for y in DIGEST_YEARS if y not in ad_by_year]
        assert not missing, f"ad_by_year missing years: {missing}"

    def test_2036_md_is_ketu(self):
        """2036 is the Ketu MD transition year — _md_for_year(2036) should return 'ketu'."""
        assert _md_for_year(2036) == "ketu"

    def test_md_mercury_for_2026(self):
        """2026 is within Mercury MD (2019-2036)."""
        assert _md_for_year(2026) == "mercury"

    def test_md_venus_for_2043(self):
        """2043 is the start of Venus MD."""
        assert _md_for_year(2043) == "venus"

    def test_md_periods_count(self):
        """md_periods covers all 35 digest years without gaps."""
        for year in DIGEST_YEARS:
            md = _md_for_year(year)
            assert md != "unknown", f"Year {year} has no MD mapping"


# ── Test 7: year_theme is non-empty for all years ────────────────────────────
# (Note: placed before DB tests so it runs even without DB)


class TestYearTheme:
    def test_all_years_have_non_empty_theme(self):
        """_compose_year_theme should produce a non-empty string for every year."""
        ad_by_year = VIMSHOTTARI_SCHEDULE["ad_by_year"]
        for year in DIGEST_YEARS:
            md = _md_for_year(year)
            ad = ad_by_year.get(year)
            ss = SADE_SATI_BY_YEAR.get(year, "inactive")
            theme = _compose_year_theme(year, md, ad, ss, [])
            assert isinstance(theme, str), f"Theme for {year} is not a string"
            assert len(theme) > 0, f"Theme for {year} is empty"
            assert str(year) in theme, f"Theme for {year} does not mention the year"

    def test_theme_mentions_dasha(self):
        """Theme should include the MD lord name."""
        theme = _compose_year_theme(2036, "ketu", "ketu", "inactive", [])
        assert "Ketu" in theme

    def test_theme_includes_anchor_when_present(self):
        """Theme should reference the anchor label when one is provided."""
        theme = _compose_year_theme(2047, "ketu", "rahu", "approaching", ["Rahu transit peak"])
        assert "Rahu transit peak" in theme

    def test_theme_includes_sade_sati_active(self):
        """Theme should mention Sade Sati when active."""
        theme = _compose_year_theme(2048, "ketu", "jupiter", "active", [])
        assert "Sade Sati" in theme


# ── DB Tests ──────────────────────────────────────────────────────────────────


@pytest.mark.skipif(not DB_AVAILABLE, reason="DB_NAME not set")
class TestSeedVarshaDigestDB:
    """Tests 4, 5, 6 — require live DB connection."""

    def test_4_inserts_35_rows_and_is_idempotent(self):
        """seed_varsha_digest inserts exactly 35 rows; second call also returns 35."""
        conn = _get_conn()
        try:
            # First run
            count1 = seed_varsha_digest(conn, NATIVE_CHART_ID)
            assert count1 == 35, f"Expected 35 rows processed, got {count1}"

            # Second run (idempotent upsert)
            count2 = seed_varsha_digest(conn, NATIVE_CHART_ID)
            assert count2 == 35, f"Expected 35 rows on re-run, got {count2}"

            # Verify DB row count
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) FROM l1_varsha_digest WHERE chart_id = %s",
                (NATIVE_CHART_ID,),
            )
            db_count = cur.fetchone()[0]
            cur.close()
            assert db_count == 35, f"Expected 35 rows in DB, found {db_count}"
        finally:
            conn.close()

    def test_5_year_2036_has_ketu_md(self):
        """2036 row should have vimshottari_md='ketu' (MD transition year)."""
        conn = _get_conn()
        try:
            seed_varsha_digest(conn, NATIVE_CHART_ID)
            cur = conn.cursor()
            cur.execute(
                """
                SELECT vimshottari_md
                FROM   l1_varsha_digest
                WHERE  chart_id = %s AND varsha_year = 2036
                """,
                (NATIVE_CHART_ID,),
            )
            row = cur.fetchone()
            cur.close()
            assert row is not None, "Row for year 2036 not found"
            assert row[0] == "ketu", f"Expected md='ketu' for 2036, got '{row[0]}'"
        finally:
            conn.close()

    def test_6_years_2048_2049_are_sade_sati_active(self):
        """2048 and 2049 rows must have sade_sati_status='active'."""
        conn = _get_conn()
        try:
            seed_varsha_digest(conn, NATIVE_CHART_ID)
            cur = conn.cursor()
            cur.execute(
                """
                SELECT varsha_year, sade_sati_status
                FROM   l1_varsha_digest
                WHERE  chart_id = %s
                  AND  varsha_year IN (2048, 2049)
                ORDER  BY varsha_year
                """,
                (NATIVE_CHART_ID,),
            )
            rows = {r[0]: r[1] for r in cur.fetchall()}
            cur.close()
            assert 2048 in rows, "Row for 2048 missing"
            assert 2049 in rows, "Row for 2049 missing"
            assert rows[2048] == "active", f"2048 sade_sati={rows[2048]!r}, expected 'active'"
            assert rows[2049] == "active", f"2049 sade_sati={rows[2049]!r}, expected 'active'"
        finally:
            conn.close()

    def test_all_rows_have_non_empty_year_theme(self):
        """Every seeded row should have a non-null, non-empty year_theme."""
        conn = _get_conn()
        try:
            seed_varsha_digest(conn, NATIVE_CHART_ID)
            cur = conn.cursor()
            cur.execute(
                """
                SELECT varsha_year, year_theme
                FROM   l1_varsha_digest
                WHERE  chart_id = %s
                ORDER  BY varsha_year
                """,
                (NATIVE_CHART_ID,),
            )
            rows = cur.fetchall()
            cur.close()
            empty = [(r[0], r[1]) for r in rows if not r[1] or not r[1].strip()]
            assert not empty, f"Rows with empty year_theme: {empty}"
        finally:
            conn.close()
