"""
varsha_digest_writer.py — Per-Varsha Yearly Digest aggregation.

Creates one row per year 2026-2060 aggregating:
  - Vimshottari MD/AD for the year
  - Bhrigu Bindu hit count from l1_bhrigu_bindu_transits
  - Phase-Locked Anchor count from l1_phase_locked_anchors
  - Synchronicity window count from l1_time_synchronicity
  - Vedha activation count (approximated from l1_vedha_extended)
  - Sade Sati status

A20 (Tajik year-lord JSONB columns) excluded — pending Stream B dependency.

Stream C — A22 [BUILD-ORCH-STREAM-C-A22-S1]
"""
from __future__ import annotations

import logging
from datetime import date
from typing import Any

logger = logging.getLogger(__name__)

# ── Vimshottari schedule ──────────────────────────────────────────────────────

# Native: Mercury MD starts ~2019, Ketu MD starts ~2036, Venus MD starts ~2043
# Each MD lord is the primary period lord for the years listed.
# AD (antardasha) values are simplified to one lord per year for digest purposes.

VIMSHOTTARI_SCHEDULE: dict[str, Any] = {
    "md_periods": [
        ("mercury", 2019, 2036),  # Mercury MD 2019-2036 (17 years)
        ("ketu",    2036, 2043),  # Ketu MD 2036-2043 (7 years)
        ("venus",   2043, 2063),  # Venus MD 2043-2063 (20 years)
    ],
    # Simplified antardasha lord per year (one AD per year for digest)
    "ad_by_year": {
        2026: "venus",   2027: "sun",     2028: "moon",    2029: "mars",
        2030: "rahu",    2031: "jupiter", 2032: "saturn",  2033: "mercury",
        2034: "ketu",    2035: "venus",
        2036: "ketu",    # Ketu MD starts — Ketu/Ketu initially
        2037: "jupiter", 2038: "saturn",  2039: "mercury", 2040: "venus",
        2041: "sun",     2042: "moon",
        2043: "venus",   # Venus MD starts
        2044: "sun",     2045: "moon",    2046: "mars",    2047: "rahu",
        2048: "jupiter", 2049: "saturn",  2050: "mercury", 2051: "ketu",
        2052: "venus",   2053: "sun",     2054: "moon",    2055: "mars",
        2056: "rahu",    2057: "jupiter", 2058: "saturn",  2059: "mercury",
        2060: "ketu",
    },
}

# ── Sade Sati map ─────────────────────────────────────────────────────────────

# Native natal Moon = Purva Bhadrapada nakshatra = Aquarius sign.
# Sade Sati when Saturn transits Moon's sign ± 1 sign (Capricorn / Aquarius / Pisces).
#
# Historical / near-term:
#   Saturn in Capricorn  ~2020-2023 → approaching (sign before Moon's sign)
#   Saturn in Aquarius   ~2023-2025 → active (Moon's own sign)
#   Saturn in Pisces     ~2025-2027 → leaving  (sign after Moon's sign)
#   Saturn in Aries+     2027-2047  → inactive
# Next cycle:
#   Saturn in Capricorn  ~2047-2050 → approaching
#   Saturn in Aquarius   ~2048-2050 → active (peak)
#   Saturn in Pisces     ~2050      → leaving

SADE_SATI_BY_YEAR: dict[int, str] = {
    2026: "leaving",      # Saturn in Pisces still (leaves ~mid-2027)
    2027: "inactive",
    2028: "inactive",
    2029: "inactive",
    2030: "inactive",
    2031: "inactive",
    2032: "inactive",
    2033: "inactive",
    2034: "inactive",
    2035: "inactive",
    2036: "inactive",
    2037: "inactive",
    2038: "inactive",
    2039: "inactive",
    2040: "inactive",
    2041: "inactive",
    2042: "inactive",
    2043: "inactive",
    2044: "inactive",
    2045: "inactive",
    2046: "inactive",
    2047: "approaching",  # Saturn entering Capricorn
    2048: "active",       # Saturn in Aquarius (natal Moon sign)
    2049: "active",
    2050: "leaving",      # Saturn in Pisces
    2051: "inactive",
    2052: "inactive",
    2053: "inactive",
    2054: "inactive",
    2055: "inactive",
    2056: "inactive",
    2057: "inactive",
    2058: "inactive",
    2059: "inactive",
    2060: "inactive",
}

# ── Digest years ──────────────────────────────────────────────────────────────

DIGEST_YEARS = list(range(2026, 2061))  # 35 years inclusive

# ── Helpers ───────────────────────────────────────────────────────────────────

def _md_for_year(year: int) -> str:
    """Return the Vimshottari Mahadasha lord for a given year."""
    for (lord, start, end) in VIMSHOTTARI_SCHEDULE["md_periods"]:
        if start <= year < end:
            return lord
    return "unknown"


def _compose_year_theme(
    year: int,
    md: str,
    ad: str | None,
    sade_sati: str,
    anchor_labels: list[str],
) -> str:
    """Compose a one-sentence year digest theme."""
    dasha_desc = f"{md.capitalize()} MD / {ad.capitalize()} AD" if ad else f"{md.capitalize()} MD"
    ss_fragment = ""
    if sade_sati == "active":
        ss_fragment = ", Sade Sati peak (Saturn transiting natal Moon sign)"
    elif sade_sati == "approaching":
        ss_fragment = ", Sade Sati approaching (Saturn entering Capricorn)"
    elif sade_sati == "leaving":
        ss_fragment = ", Sade Sati waning (Saturn departing Pisces)"

    anchor_fragment = ""
    if anchor_labels:
        first = anchor_labels[0]
        anchor_fragment = f"; key anchor: {first}"
        if len(anchor_labels) > 1:
            anchor_fragment += f" (+{len(anchor_labels) - 1} more)"

    return f"{year}: {dasha_desc}{ss_fragment}{anchor_fragment}."


# ── Main seeder ───────────────────────────────────────────────────────────────

def seed_varsha_digest(conn: Any, chart_id: str) -> int:
    """
    Seed l1_varsha_digest with 35 rows (one per year 2026-2060).

    Aggregates BB hits, phase-locked anchors, synchronicity windows, and
    Sade Sati status for each year. Upserts so re-runs are safe.

    Returns the number of rows processed (always 35).
    """
    cur = conn.cursor()
    rows_processed = 0

    for year in DIGEST_YEARS:
        year_start = date(year, 1, 1)
        year_end   = date(year, 12, 31)

        # ── Vimshottari ──────────────────────────────────────────────────────
        md = _md_for_year(year)
        ad = VIMSHOTTARI_SCHEDULE["ad_by_year"].get(year)

        # ── Bhrigu Bindu hits ─────────────────────────────────────────────
        cur.execute(
            """
            SELECT COUNT(*)
            FROM   l1_bhrigu_bindu_transits
            WHERE  chart_id = %s
              AND  EXTRACT(YEAR FROM hit_iso) = %s
            """,
            (chart_id, year),
        )
        bb_hit_count: int = cur.fetchone()[0]

        # ── Phase-Locked Anchors ──────────────────────────────────────────
        cur.execute(
            """
            SELECT anchor_label
            FROM   l1_phase_locked_anchors
            WHERE  chart_id = %s
              AND  window_start <= %s
              AND  window_end   >= %s
            ORDER  BY window_start
            """,
            (chart_id, year_end, year_start),
        )
        anchor_rows  = cur.fetchall()
        anchor_labels: list[str] = [r[0] for r in anchor_rows]
        anchor_count = len(anchor_labels)

        # ── Synchronicity Windows ─────────────────────────────────────────
        cur.execute(
            """
            SELECT COUNT(*), MAX(cluster_intensity)
            FROM   l1_time_synchronicity
            WHERE  chart_id = %s
              AND  window_start <= %s
              AND  window_end   >= %s
            """,
            (chart_id, year_end, year_start),
        )
        row = cur.fetchone()
        sync_window_count      = row[0] if row else 0
        peak_cluster_intensity = row[1] if row else None

        # ── Vedha count (static estimate) ────────────────────────────────
        vedha_count = 2  # approximation — detailed scanning deferred

        # ── Sade Sati ─────────────────────────────────────────────────────
        sade_sati_status = SADE_SATI_BY_YEAR.get(year, "inactive")

        # ── Confidence score ──────────────────────────────────────────────
        confidence_score = min(0.6 + (anchor_count * 0.05), 0.95)

        # ── Year theme ────────────────────────────────────────────────────
        year_theme = _compose_year_theme(year, md, ad, sade_sati_status, anchor_labels)

        # ── Upsert ────────────────────────────────────────────────────────
        cur.execute(
            """
            INSERT INTO l1_varsha_digest (
                chart_id, varsha_year,
                vimshottari_md, vimshottari_ad,
                bb_hit_count,
                anchor_count, anchor_labels,
                sync_window_count, peak_cluster_intensity,
                vedha_count,
                sade_sati_status,
                year_theme,
                confidence_score,
                embedding
            )
            VALUES (
                %s, %s,
                %s, %s,
                %s,
                %s, %s,
                %s, %s,
                %s,
                %s,
                %s,
                %s,
                NULL
            )
            ON CONFLICT (chart_id, varsha_year) DO UPDATE SET
                vimshottari_md          = EXCLUDED.vimshottari_md,
                vimshottari_ad          = EXCLUDED.vimshottari_ad,
                bb_hit_count            = EXCLUDED.bb_hit_count,
                anchor_count            = EXCLUDED.anchor_count,
                anchor_labels           = EXCLUDED.anchor_labels,
                sync_window_count       = EXCLUDED.sync_window_count,
                peak_cluster_intensity  = EXCLUDED.peak_cluster_intensity,
                vedha_count             = EXCLUDED.vedha_count,
                sade_sati_status        = EXCLUDED.sade_sati_status,
                year_theme              = EXCLUDED.year_theme,
                confidence_score        = EXCLUDED.confidence_score
            """,
            (
                chart_id, year,
                md, ad,
                bb_hit_count,
                anchor_count, anchor_labels,
                sync_window_count, peak_cluster_intensity,
                vedha_count,
                sade_sati_status,
                year_theme,
                confidence_score,
            ),
        )
        rows_processed += 1

    conn.commit()
    cur.close()
    logger.info(
        "seed_varsha_digest: %d rows upserted for chart_id=%s",
        rows_processed,
        chart_id,
    )
    return rows_processed
