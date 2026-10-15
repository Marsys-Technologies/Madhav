"""
Vimshottari Mahadasha / Antardasha / Pratyantardasha computation engine.

M3-W2-B1 deliverable. Uses pyswisseph (Moshier ephemeris by default; falls back
gracefully if SE_EPHE_PATH points to .se1 files) with Lahiri ayanamsha to compute
the Moon's sidereal longitude at birth, derive nakshatra-lord and the balance of
the first dasha, and emit the full M/A/P sequence over a configurable horizon.

Per CLAUDE.md §I B.10 (no fabricated computation): all chart-numerical outputs
trace to a swisseph call. The script does not invent values; if pyswisseph is
absent, the script halts and emits an [EXTERNAL_COMPUTATION_REQUIRED] note.

Per PROJECT_ARCHITECTURE §B.1 (Facts/Interpretation separation): outputs of this
script are L1.5 (computed from L1 chart inputs via Swiss Ephemeris); they are
not L2.5 interpretations. The output JSON is the substrate the temporal engine
queries at synthesis time (M3-B+ scope).

Run direct (chart id and birth datetime are required):
    python3 platform/scripts/temporal/compute_vimshottari.py

Run with explicit args:
    python3 platform/scripts/temporal/compute_vimshottari.py \\
        --chart-id <chart-uuid> \\
        --birth <ISO8601-birth-datetime-with-offset> \\
        --horizon-end 2050-12-31 \\
        --output 05_TEMPORAL_ENGINES/dasha/vimshottari/VIMSHOTTARI_RAW_v1_0.json

Outputs:
    - List[dict] with M/A/P entries; written to --output as JSON.
    - Each row: chart_id, dasha_level (M|A|P), planet, start_date, end_date,
                duration_days, computed_by='pyswisseph', ayanamsha='lahiri'.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterator

try:
    import swisseph as swe
except ImportError:
    print(
        "[EXTERNAL_COMPUTATION_REQUIRED]: pyswisseph not installed. "
        "Install with `pip install pyswisseph` and re-run.",
        file=sys.stderr,
    )
    sys.exit(2)


VIMSHOTTARI_LORDS = (
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury",
)
VIMSHOTTARI_DURATIONS_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
VIMSHOTTARI_TOTAL_YEARS = 120
DAYS_PER_YEAR = 365.25  # Parashari classical convention (Julian year).

NAKSHATRAS = (
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha",
    "Magha", "PurvaPhalguni", "UttaraPhalguni", "Hasta",
    "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "PurvaAshadha", "UttaraAshadha",
    "Shravana", "Dhanishta", "Shatabhisha",
    "PurvaBhadrapada", "UttaraBhadrapada", "Revati",
)
NAK_SIZE_DEG = 360.0 / 27.0


@dataclass
class DashaRow:
    chart_id: str
    dasha_level: str          # 'M' | 'A' | 'P'
    planet: str
    start_date: str           # ISO date 'YYYY-MM-DD'
    end_date: str             # ISO date 'YYYY-MM-DD'
    duration_days: int
    computed_by: str
    ayanamsha: str
    parent_md: str | None = None     # for A: the MD lord; for P: the MD lord
    parent_ad: str | None = None     # for P: the AD lord


def parse_iso8601(s: str) -> datetime:
    """Parse ISO8601 datetime; accept 'Z' or '+HH:MM' offsets."""
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def compute_moon_sidereal_longitude(
    birth_dt: datetime,
    *,
    ayanamsha: str = "lahiri",
    ephe_path: str | None = None,
) -> tuple[float, dict]:
    """
    Returns (moon_sidereal_longitude_deg, diagnostics).

    Uses Moshier ephemeris by default (no .se1 file required, sub-arcsecond
    accuracy 1800-2400 CE for Moon). If ephe_path is set and points to
    valid .se1 files, Swiss Ephemeris is used instead.
    """
    if ayanamsha != "lahiri":
        raise NotImplementedError(f"Only 'lahiri' ayanamsha implemented; got {ayanamsha!r}")

    if ephe_path:
        swe.set_ephe_path(ephe_path)
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        ephe_mode = "swisseph_files"
    else:
        flags = swe.FLG_MOSEPH | swe.FLG_SIDEREAL
        ephe_mode = "moshier"

    swe.set_sid_mode(swe.SIDM_LAHIRI)

    # Convert to UTC for julday.
    if birth_dt.tzinfo is None:
        raise ValueError("birth_dt must be timezone-aware")
    utc_dt = birth_dt.astimezone(timezone.utc)
    jd_ut = swe.julday(
        utc_dt.year, utc_dt.month, utc_dt.day,
        utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0,
    )

    moon_pos, retflag = swe.calc_ut(jd_ut, swe.MOON, flags)
    moon_lon = moon_pos[0] % 360.0
    diagnostics = {
        "jd_ut": jd_ut,
        "utc_iso": utc_dt.isoformat(),
        "ephe_mode": ephe_mode,
        "swe_retflag": retflag,
        "moon_sidereal_lon_deg": moon_lon,
    }
    return moon_lon, diagnostics


def derive_first_md(moon_lon_deg: float) -> tuple[str, float, dict]:
    """
    From Moon's sidereal longitude, return (md_lord, balance_years, diagnostics).
    """
    nak_idx = int(moon_lon_deg // NAK_SIZE_DEG)
    pos_in_nak = moon_lon_deg - nak_idx * NAK_SIZE_DEG
    fraction_elapsed = pos_in_nak / NAK_SIZE_DEG
    md_lord = VIMSHOTTARI_LORDS[nak_idx % 9]
    md_total = VIMSHOTTARI_DURATIONS_YEARS[md_lord]
    balance_years = md_total * (1.0 - fraction_elapsed)
    diag = {
        "nakshatra_idx": nak_idx,
        "nakshatra_name": NAKSHATRAS[nak_idx],
        "position_in_nakshatra_deg": pos_in_nak,
        "fraction_elapsed": fraction_elapsed,
        "md_lord": md_lord,
        "md_total_years": md_total,
        "balance_years": balance_years,
    }
    return md_lord, balance_years, diag


def add_years(start: datetime, years: float) -> datetime:
    """Add fractional years to a datetime using DAYS_PER_YEAR convention."""
    return start + timedelta(days=years * DAYS_PER_YEAR)


def md_sequence(first_lord: str) -> Iterator[str]:
    """Yield the cyclic MD-lord sequence starting at first_lord."""
    start_idx = VIMSHOTTARI_LORDS.index(first_lord)
    i = start_idx
    while True:
        yield VIMSHOTTARI_LORDS[i]
        i = (i + 1) % 9


def ad_sequence(md_lord: str) -> list[str]:
    """The 9 AD lords inside a given MD: starts with the MD lord itself, then cycles."""
    start_idx = VIMSHOTTARI_LORDS.index(md_lord)
    return [VIMSHOTTARI_LORDS[(start_idx + k) % 9] for k in range(9)]


def compute_vimshottari(
    *,
    chart_id: str,
    birth_dt: datetime,
    ayanamsha: str = "lahiri",
    ephe_path: str | None = None,
    horizon_end: datetime,
    include_pratyantar: bool = True,
) -> tuple[list[DashaRow], dict]:
    """
    Compute the full Vimshottari MD/AD/(PD) sequence from birth_dt to horizon_end.

    Returns (rows, diagnostics).
    """
    moon_lon, eph_diag = compute_moon_sidereal_longitude(
        birth_dt, ayanamsha=ayanamsha, ephe_path=ephe_path,
    )
    first_lord, balance_yrs, derive_diag = derive_first_md(moon_lon)

    diagnostics = {
        **eph_diag, **derive_diag,
        "birth_iso": birth_dt.isoformat(),
        "horizon_end_iso": horizon_end.isoformat(),
        "ayanamsha": ayanamsha,
        "computed_by": "pyswisseph",
        "days_per_year": DAYS_PER_YEAR,
    }

    rows: list[DashaRow] = []

    md_iter = md_sequence(first_lord)
    md_lord = next(md_iter)
    md_start = birth_dt
    # First MD: only the residual balance after birth.
    md_remaining_years = balance_yrs

    while md_start < horizon_end:
        md_end = add_years(md_start, md_remaining_years)
        # MD row.
        rows.append(DashaRow(
            chart_id=chart_id,
            dasha_level="M",
            planet=md_lord,
            start_date=md_start.date().isoformat(),
            end_date=md_end.date().isoformat(),
            duration_days=(md_end.date() - md_start.date()).days,
            computed_by="pyswisseph",
            ayanamsha=ayanamsha,
        ))
        # ADs inside this MD.
        ad_lords = ad_sequence(md_lord)
        ad_start = md_start
        for ad_lord in ad_lords:
            # AD duration = (MD_total_years_full * AD_lord_years) / 120
            # but the FIRST MD is partial, so AD spans get scaled.
            # In Parashari standard: each AD in any MD = (MD_full_years * AD_lord_years) / 120,
            # except for the first (partial) MD where the AD subdivision happens within the
            # remaining_years pro-rata.
            #
            # The cleanest classical rule: full-MD ADs use the formula
            #   AD_years = MD_full_years * AD_lord_years / 120
            # For the partial first MD, scale all ADs by (balance / md_full):
            #   AD_years_partial = AD_years_full * (balance / md_full)
            md_full_years = VIMSHOTTARI_DURATIONS_YEARS[md_lord]
            ad_full_years = md_full_years * VIMSHOTTARI_DURATIONS_YEARS[ad_lord] / VIMSHOTTARI_TOTAL_YEARS
            scale = md_remaining_years / md_full_years
            ad_years = ad_full_years * scale
            ad_end = add_years(ad_start, ad_years)
            # Cap AD end at MD end to avoid float drift.
            if ad_end > md_end:
                ad_end = md_end
            rows.append(DashaRow(
                chart_id=chart_id,
                dasha_level="A",
                planet=ad_lord,
                start_date=ad_start.date().isoformat(),
                end_date=ad_end.date().isoformat(),
                duration_days=(ad_end.date() - ad_start.date()).days,
                computed_by="pyswisseph",
                ayanamsha=ayanamsha,
                parent_md=md_lord,
            ))
            # PDs inside this AD.
            if include_pratyantar:
                pd_start = ad_start
                pd_lords = ad_sequence(ad_lord)
                for pd_lord in pd_lords:
                    pd_full_years = (
                        md_full_years
                        * VIMSHOTTARI_DURATIONS_YEARS[ad_lord]
                        * VIMSHOTTARI_DURATIONS_YEARS[pd_lord]
                        / (VIMSHOTTARI_TOTAL_YEARS ** 2)
                    )
                    pd_years = pd_full_years * scale
                    pd_end = add_years(pd_start, pd_years)
                    if pd_end > ad_end:
                        pd_end = ad_end
                    rows.append(DashaRow(
                        chart_id=chart_id,
                        dasha_level="P",
                        planet=pd_lord,
                        start_date=pd_start.date().isoformat(),
                        end_date=pd_end.date().isoformat(),
                        duration_days=(pd_end.date() - pd_start.date()).days,
                        computed_by="pyswisseph",
                        ayanamsha=ayanamsha,
                        parent_md=md_lord,
                        parent_ad=ad_lord,
                    ))
                    pd_start = pd_end
            ad_start = ad_end

        # Advance to the next MD (always full duration).
        md_start = md_end
        md_lord = next(md_iter)
        md_remaining_years = float(VIMSHOTTARI_DURATIONS_YEARS[md_lord])

    return rows, diagnostics


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--chart-id", required=True,
                        help="Chart UUID (the charts.chart_id of the chart under test). REQUIRED.")
    parser.add_argument(
        "--birth", required=True,
        help="ISO8601 birth datetime of the chart under test (timezone-aware), from its `charts` row. REQUIRED: no birth datetime is embedded in this script.",
    )
    parser.add_argument("--ayanamsha", default="lahiri")
    parser.add_argument(
        "--ephe-path", default=os.environ.get("SE_EPHE_PATH"),
        help="Optional Swiss Ephemeris .se1 file directory.",
    )
    parser.add_argument("--horizon-end", default="2050-12-31")
    parser.add_argument(
        "--output",
        default="05_TEMPORAL_ENGINES/dasha/vimshottari/VIMSHOTTARI_RAW_v1_0.json",
    )
    parser.add_argument("--no-pratyantar", action="store_true",
                        help="Skip Pratyantardasha rows (faster).")
    args = parser.parse_args()

    birth_dt = parse_iso8601(args.birth)
    horizon_end_dt = datetime.fromisoformat(args.horizon_end + "T00:00:00+00:00")

    rows, diag = compute_vimshottari(
        chart_id=args.chart_id,
        birth_dt=birth_dt,
        ayanamsha=args.ayanamsha,
        ephe_path=args.ephe_path,
        horizon_end=horizon_end_dt,
        include_pratyantar=not args.no_pratyantar,
    )

    # Counts.
    count_m = sum(1 for r in rows if r.dasha_level == "M")
    count_a = sum(1 for r in rows if r.dasha_level == "A")
    count_p = sum(1 for r in rows if r.dasha_level == "P")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema_version": "1.0",
        "computed_at": datetime.now(tz=timezone.utc).isoformat(),
        "chart_id": args.chart_id,
        "ayanamsha": args.ayanamsha,
        "computed_by": "pyswisseph",
        "diagnostics": diag,
        "row_counts": {"M": count_m, "A": count_a, "P": count_p, "total": len(rows)},
        "rows": [asdict(r) for r in rows],
    }

    out_path.write_text(json.dumps(payload, indent=2))
    print(
        f"Wrote {len(rows)} rows (M={count_m} A={count_a} P={count_p}) "
        f"to {out_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
