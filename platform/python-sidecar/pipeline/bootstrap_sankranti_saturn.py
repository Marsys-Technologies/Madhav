#!/usr/bin/env python3
"""
bootstrap_sankranti_saturn.py — G6 + G21 DB seeder
Seeds sankranti_table and saturn_sign_changes for 5 ayanamshas, 1950-2100.

Usage:
    python bootstrap_sankranti_saturn.py [--ayanamsha all|lahiri|kp|...] [--table all|sankranti|saturn]

Operator note: Running all ayanamshas for 1950-2100 takes several minutes.
For smoke-testing use: --ayanamsha lahiri --table sankranti
"""
import sys
import argparse
import swisseph as swe
import psycopg2
import psycopg2.extras
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AYANAMSHA_MAP = {
    "lahiri": swe.SIDM_LAHIRI,           # 1
    "true_chitra": swe.SIDM_TRUE_CITRA,  # 27
    "kp": swe.SIDM_KRISHNAMURTI,         # 5
    "raman": swe.SIDM_RAMAN,             # 3
    "surya_siddhanta": swe.SIDM_SURYASIDDHANTA,  # 21
}

SIGNS = [
    "aries", "taurus", "gemini", "cancer", "leo", "virgo",
    "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
]

START_YEAR = 1950
END_YEAR = 2100

DB_PARAMS = dict(
    host="127.0.0.1",
    port=5433,
    dbname="amjis",
    user="amjis_app",
    password="aYtv6SN5TwRBShzHfxN4Qz_ccW3a49qnCAA2L-VF",
)

# ---------------------------------------------------------------------------
# Ephemeris helpers
# ---------------------------------------------------------------------------

def get_sun_longitude_sidereal(jd: float, swe_id: int) -> float:
    """Return Sun's sidereal longitude (0-360) for given JD and ayanamsha."""
    swe.set_sid_mode(swe_id)
    result, _ = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)
    return result[0] % 360.0


def find_sankranti(
    target_lon: float,
    jd_start: float,
    jd_end: float,
    swe_id: int,
    tol: float = 1e-7,
) -> float:
    """
    Binary search for the JD when Sun's sidereal longitude equals target_lon,
    within the interval [jd_start, jd_end].

    Handles the 0°/360° wrap-around (Aries ingress) correctly by working in
    terms of angular distance remaining to the target.
    """
    for _ in range(80):
        if (jd_end - jd_start) < tol:
            break
        jd_mid = (jd_start + jd_end) / 2.0
        lon_start = get_sun_longitude_sidereal(jd_start, swe_id)
        lon_mid = get_sun_longitude_sidereal(jd_mid, swe_id)

        # Angular distance still to travel from each point to target_lon
        # (positive means Sun hasn't crossed yet, negative means it has)
        dist_start = (target_lon - lon_start) % 360.0
        dist_mid = (target_lon - lon_mid) % 360.0

        # If both points are "behind" target (dist > 180° ≈ already past),
        # we can still narrow via monotonicity — but the simple rule works:
        # if dist_mid < dist_start the mid is closer; advance start.
        if dist_start < 180.0:
            # Sun hasn't crossed from jd_start yet
            if dist_mid < dist_start:
                jd_start = jd_mid
            else:
                jd_end = jd_mid
        else:
            # Sun has already crossed from jd_start — target is in second half
            jd_end = jd_mid

    return (jd_start + jd_end) / 2.0


def jd_to_datetime_utc(jd: float):
    """Convert Julian Day to (datetime, date_str, year) in UTC."""
    year, month, day, hour_frac = swe.revjul(jd)
    h = int(hour_frac)
    m_frac = (hour_frac - h) * 60.0
    m = int(m_frac)
    s = int((m_frac - m) * 60.0)
    # Clamp seconds for rare floating-point overflow
    s = min(s, 59)
    dt = datetime(year, month, day, h, m, s, tzinfo=timezone.utc)
    return dt, dt.date().isoformat(), year


def get_saturn_longitude_sidereal(jd: float, swe_id: int) -> float:
    """Return Saturn's sidereal longitude (0-360) for given JD and ayanamsha."""
    swe.set_sid_mode(swe_id)
    result, _ = swe.calc_ut(jd, swe.SATURN, swe.FLG_SIDEREAL)
    return result[0] % 360.0


def get_saturn_sign(jd: float, swe_id: int) -> int:
    """Return Saturn's sign number (1=Aries … 12=Pisces)."""
    lon = get_saturn_longitude_sidereal(jd, swe_id)
    return int(lon / 30.0) + 1


def is_saturn_retrograde(jd: float, swe_id: int) -> bool:
    """Return True if Saturn is retrograde at jd (speed < 0)."""
    swe.set_sid_mode(swe_id)
    result, _ = swe.calc_ut(jd, swe.SATURN, swe.FLG_SIDEREAL | swe.FLG_SPEED)
    return result[3] < 0.0  # index 3 = longitude speed


def find_saturn_ingress(
    target_sign: int,
    jd_start: float,
    jd_end: float,
    swe_id: int,
    tol: float = 1e-7,
) -> float:
    """
    Binary search for the JD when Saturn enters target_sign within [jd_start, jd_end].
    target_sign is 1-12.
    """
    target_lon = (target_sign - 1) * 30.0  # entry longitude for sign N

    for _ in range(80):
        if (jd_end - jd_start) < tol:
            break
        jd_mid = (jd_start + jd_end) / 2.0
        lon_start = get_saturn_longitude_sidereal(jd_start, swe_id)
        lon_mid = get_saturn_longitude_sidereal(jd_mid, swe_id)

        dist_start = (target_lon - lon_start) % 360.0
        dist_mid = (target_lon - lon_mid) % 360.0

        if dist_start < 180.0:
            if dist_mid < dist_start:
                jd_start = jd_mid
            else:
                jd_end = jd_mid
        else:
            jd_end = jd_mid

    return (jd_start + jd_end) / 2.0


# ---------------------------------------------------------------------------
# Seeder: sankranti_table
# ---------------------------------------------------------------------------

def seed_sankranti(conn, ayanamsha_id: str, swe_id: int, verbose: bool = True) -> int:
    """
    Compute and insert Sun sign-entry (sankranti) timestamps for all 12 signs
    for every year in START_YEAR..END_YEAR.

    Returns the number of rows inserted (excluding ON CONFLICT skips).
    """
    cur = conn.cursor()
    rows = []

    if verbose:
        print(f"[sankranti] {ayanamsha_id}: computing 1950-2100 …", flush=True)

    for year in range(START_YEAR, END_YEAR + 1):
        # Aries ingress: Sun enters 0° sidereal ≈ mid-March for Lahiri.
        # We bracket it between Jan 1 and May 1 of the same year.
        jd_jan1 = swe.julday(year, 1, 1, 0.0)
        jd_may1 = swe.julday(year, 5, 1, 0.0)

        # Find Aries ingress first (sign 1, target_lon = 0°)
        jd_aries = find_sankranti(0.0, jd_jan1, jd_may1, swe_id)

        # From Aries ingress, find each subsequent sign ~30 days later
        prev_jd = jd_aries
        for sign_idx in range(12):  # 0..11 → signs 1..12
            sign_number = sign_idx + 1
            target_lon = float(sign_idx * 30)

            if sign_idx == 0:
                jd_entry = jd_aries
            else:
                # Bracket: 20–40 days after the previous ingress
                jd_entry = find_sankranti(
                    target_lon,
                    prev_jd + 20.0,
                    prev_jd + 50.0,
                    swe_id,
                )
            prev_jd = jd_entry

            dt, date_str, entry_year = jd_to_datetime_utc(jd_entry)
            sign_name = SIGNS[sign_idx]

            rows.append((
                ayanamsha_id,
                sign_number,
                sign_name,
                jd_entry,
                date_str,
                dt,
                year,
            ))

        if verbose and year % 25 == 0:
            print(f"  … year {year} done", flush=True)

    # Bulk insert with ON CONFLICT DO NOTHING
    psycopg2.extras.execute_values(
        cur,
        """
        INSERT INTO sankranti_table
            (ayanamsha_id, sign_number, sign_name, entry_jd, entry_date, entry_utc, year)
        VALUES %s
        ON CONFLICT (ayanamsha_id, sign_number, year) DO NOTHING
        """,
        rows,
        template="(%s, %s, %s, %s, %s, %s, %s)",
        page_size=500,
    )
    conn.commit()
    inserted = cur.rowcount
    cur.close()

    if verbose:
        print(f"[sankranti] {ayanamsha_id}: {len(rows)} rows computed, {inserted} inserted", flush=True)

    return inserted


# ---------------------------------------------------------------------------
# Seeder: saturn_sign_changes
# ---------------------------------------------------------------------------

def seed_saturn_ingresses(conn, ayanamsha_id: str, swe_id: int, verbose: bool = True) -> int:
    """
    Detect and insert Saturn sign-ingress events for START_YEAR..END_YEAR.

    Strategy:
    - Step through JDs every 10 days (Saturn moves ~0.03°/day; needs ~1000 days
      to traverse a sign, so 10-day steps safely bracket every ingress).
    - When sign changes between two 10-day steps, binary-search for the exact JD.
    - Record is_retrograde_ingress from speed at the ingress moment.

    Returns the number of rows inserted (excluding ON CONFLICT skips).
    """
    cur = conn.cursor()
    rows = []

    jd_start_global = swe.julday(START_YEAR, 1, 1, 0.0)
    jd_end_global = swe.julday(END_YEAR, 12, 31, 0.0)

    if verbose:
        print(f"[saturn] {ayanamsha_id}: scanning 1950-2100 every 10 days …", flush=True)

    STEP = 10.0  # days
    jd = jd_start_global
    prev_sign = get_saturn_sign(jd, swe_id)
    prev_jd = jd

    while jd <= jd_end_global:
        jd += STEP
        curr_sign = get_saturn_sign(jd, swe_id)

        if curr_sign != prev_sign:
            # Binary-search for exact ingress within (prev_jd, jd)
            ingress_jd = find_saturn_ingress(curr_sign, prev_jd, jd, swe_id)
            retrograde = is_saturn_retrograde(ingress_jd, swe_id)
            dt, date_str, _year = jd_to_datetime_utc(ingress_jd)

            rows.append((
                ayanamsha_id,
                prev_sign,           # from_sign_number
                SIGNS[prev_sign - 1],  # from_sign_name
                curr_sign,           # to_sign_number
                SIGNS[curr_sign - 1],  # to_sign_name
                ingress_jd,
                date_str,
                dt,
                retrograde,
            ))

        prev_sign = curr_sign
        prev_jd = jd

    # Bulk insert
    psycopg2.extras.execute_values(
        cur,
        """
        INSERT INTO saturn_sign_changes
            (ayanamsha_id, from_sign_number, from_sign_name,
             to_sign_number, to_sign_name,
             ingress_jd, ingress_date, ingress_utc, is_retrograde_ingress)
        VALUES %s
        ON CONFLICT (ayanamsha_id, ingress_jd) DO NOTHING
        """,
        rows,
        template="(%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        page_size=200,
    )
    conn.commit()
    inserted = cur.rowcount
    cur.close()

    if verbose:
        print(f"[saturn] {ayanamsha_id}: {len(rows)} ingresses found, {inserted} inserted", flush=True)

    return inserted


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Bootstrap sankranti_table and saturn_sign_changes (G6 + G21)."
    )
    parser.add_argument(
        "--ayanamsha",
        default="all",
        help="Comma-separated ayanamsha IDs or 'all' (default: all)",
    )
    parser.add_argument(
        "--table",
        default="all",
        choices=["all", "sankranti", "saturn"],
        help="Which table to seed (default: all)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress per-year progress output",
    )
    args = parser.parse_args()

    verbose = not args.quiet

    if args.ayanamsha == "all":
        ayanamshas = list(AYANAMSHA_MAP.keys())
    else:
        ayanamshas = [a.strip() for a in args.ayanamsha.split(",")]

    # Validate
    unknown = [a for a in ayanamshas if a not in AYANAMSHA_MAP]
    if unknown:
        print(f"ERROR: Unknown ayanamsha(s): {unknown}", file=sys.stderr)
        print(f"Valid: {list(AYANAMSHA_MAP.keys())}", file=sys.stderr)
        sys.exit(1)

    conn = psycopg2.connect(**DB_PARAMS)

    total_sankranti = 0
    total_saturn = 0

    for ayanamsha_id in ayanamshas:
        swe_id = AYANAMSHA_MAP[ayanamsha_id]
        if args.table in ("all", "sankranti"):
            total_sankranti += seed_sankranti(conn, ayanamsha_id, swe_id, verbose=verbose)
        if args.table in ("all", "saturn"):
            total_saturn += seed_saturn_ingresses(conn, ayanamsha_id, swe_id, verbose=verbose)

    conn.close()

    print("Bootstrap complete.")
    if args.table in ("all", "sankranti"):
        print(f"  sankranti rows inserted : {total_sankranti}")
    if args.table in ("all", "saturn"):
        print(f"  saturn ingress rows inserted : {total_saturn}")
    print("operator_action_pending: run bootstrap_sankranti_saturn.py --ayanamsha all")


if __name__ == "__main__":
    main()
