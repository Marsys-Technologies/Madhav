"""
Yogini Mahadasha / Antardasha computation engine.

M3-W2-B2 deliverable. Mirrors compute_vimshottari.py: pyswisseph (Moshier
default) + Lahiri sidereal -> Moon's sidereal longitude -> nakshatra index ->
first Yogini lord + balance. Emits the M/A sequence over a configurable horizon.

Yogini scheme:
    8 lords -> Mangala (1y), Pingala (2y), Dhanya (3y), Bhramari (4y),
              Bhadrika (5y), Ulka (6y), Siddha (7y), Sankata (8y).
    36-year cycle total.

Sequence-start formula (classical, with the +3 offset on the 1-indexed Janma
Nakshatra count). The session brief proposed `(nak_idx_0 mod 8)` mapping starting
at Mangala -> for a Moon in Purva Bhadrapada (nak_idx_0 = 24, worked example) this
yields Mangala. FORENSIC v8.0 §5.2 records **Bhramari** as the canonical chart's first
Yogini (DSH.Y.001). The classical formula
`((Janma Nakshatra count, 1-indexed) + 3) mod 8` (with 0 -> 8) yields:
    (25 + 3) mod 8 = 4 -> 4th in [Mangala, Pingala, Dhanya, Bhramari, ...] = Bhramari.
Equivalently, in 0-indexed lord indices: `(nak_idx_0 + 3) mod 8`. This engine
implements the +3 offset; CROSSCHECK_v1_0.md documents the brief-vs-FORENSIC
reconciliation. FORENSIC is authoritative per CLAUDE.md §I B.10.

Per CLAUDE.md §I B.10 (no fabricated computation): all chart-numerical outputs
trace to a swisseph call. The script halts with [EXTERNAL_COMPUTATION_REQUIRED]
if pyswisseph is unavailable.

Per PROJECT_ARCHITECTURE §B.1 (Facts/Interpretation separation): outputs are
L1.5 (computed from L1 chart inputs); they are not L2.5 interpretations.

Run direct (chart id and birth datetime are required; horizon defaults to 2061-01-01):
    python3 platform/scripts/temporal/compute_yogini.py --chart-id <chart-uuid> --birth <ISO8601-birth-datetime-with-offset>
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


# Yogini lord ordering (0-indexed). Mangala starts the 8-lord cycle.
YOGINI_LORDS = (
    "Mangala", "Pingala", "Dhanya", "Bhramari",
    "Bhadrika", "Ulka", "Siddha", "Sankata",
)
# Each Yogini's planetary ruler (informational; not used in cycle math).
YOGINI_RULER = {
    "Mangala": "Moon", "Pingala": "Sun", "Dhanya": "Jupiter",
    "Bhramari": "Mars", "Bhadrika": "Mercury", "Ulka": "Saturn",
    "Siddha": "Venus", "Sankata": "Rahu",
}
YOGINI_DURATIONS_YEARS = {
    "Mangala": 1, "Pingala": 2, "Dhanya": 3, "Bhramari": 4,
    "Bhadrika": 5, "Ulka": 6, "Siddha": 7, "Sankata": 8,
}
YOGINI_TOTAL_YEARS = 36
DAYS_PER_YEAR = 365.25  # Match compute_vimshottari convention.

NAK_SIZE_DEG = 360.0 / 27.0
NAKSHATRAS = (
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha",
    "Magha", "PurvaPhalguni", "UttaraPhalguni", "Hasta",
    "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "PurvaAshadha", "UttaraAshadha",
    "Shravana", "Dhanishta", "Shatabhisha",
    "PurvaBhadrapada", "UttaraBhadrapada", "Revati",
)


@dataclass
class YoginiRow:
    chart_id: str
    system: str               # 'yogini'
    planet: str               # ruler planet (e.g. 'Mars' for Bhramari)
    yogini_name: str          # 'Bhramari', 'Bhadrika', ...
    level: str                # 'M' | 'A'
    start_date: str
    end_date: str
    duration_days: int
    parent_md: str | None     # ruler of MD parent (for A rows)
    parent_ad: str | None     # always None at this level granularity
    computed_by: str
    ayanamsha: str
    needs_verification: bool
    verification_note: str


def parse_iso8601(s: str) -> datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def compute_moon_sidereal_longitude(
    birth_dt: datetime,
    *,
    ayanamsha: str = "lahiri",
    ephe_path: str | None = None,
) -> tuple[float, dict]:
    """Return (moon_sidereal_longitude_deg, diagnostics)."""
    if ayanamsha != "lahiri":
        raise NotImplementedError(f"Only 'lahiri' implemented; got {ayanamsha!r}")
    if ephe_path:
        swe.set_ephe_path(ephe_path)
        flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
        ephe_mode = "swisseph_files"
    else:
        flags = swe.FLG_MOSEPH | swe.FLG_SIDEREAL
        ephe_mode = "moshier"
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    if birth_dt.tzinfo is None:
        raise ValueError("birth_dt must be timezone-aware")
    utc_dt = birth_dt.astimezone(timezone.utc)
    jd_ut = swe.julday(
        utc_dt.year, utc_dt.month, utc_dt.day,
        utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0,
    )
    moon_pos, retflag = swe.calc_ut(jd_ut, swe.MOON, flags)
    moon_lon = moon_pos[0] % 360.0
    return moon_lon, {
        "jd_ut": jd_ut,
        "utc_iso": utc_dt.isoformat(),
        "ephe_mode": ephe_mode,
        "swe_retflag": retflag,
        "moon_sidereal_lon_deg": moon_lon,
    }


def derive_first_yogini(moon_lon_deg: float) -> tuple[str, float, dict]:
    """
    From Moon's sidereal longitude, return (first_yogini, balance_years, diagnostics).

    Classical formula: first Yogini index (0-based in [Mangala..Sankata]) =
    (nakshatra_index_0_based + 3) mod 8. The +3 offset matches FORENSIC §5.2.
    """
    nak_idx = int(moon_lon_deg // NAK_SIZE_DEG)
    pos_in_nak = moon_lon_deg - nak_idx * NAK_SIZE_DEG
    fraction_elapsed = pos_in_nak / NAK_SIZE_DEG
    yogini_idx = (nak_idx + 3) % 8
    first_yogini = YOGINI_LORDS[yogini_idx]
    full_years = YOGINI_DURATIONS_YEARS[first_yogini]
    balance_years = full_years * (1.0 - fraction_elapsed)
    return first_yogini, balance_years, {
        "nakshatra_idx_0_based": nak_idx,
        "nakshatra_name": NAKSHATRAS[nak_idx],
        "position_in_nakshatra_deg": pos_in_nak,
        "fraction_elapsed": fraction_elapsed,
        "yogini_idx_0_based": yogini_idx,
        "first_yogini": first_yogini,
        "ruler_planet": YOGINI_RULER[first_yogini],
        "first_yogini_full_years": full_years,
        "balance_years": balance_years,
        "formula": "(nakshatra_idx_0_based + 3) mod 8 -> YOGINI_LORDS index",
    }


def add_years(start: datetime, years: float) -> datetime:
    return start + timedelta(days=years * DAYS_PER_YEAR)


def yogini_sequence(first_yogini: str) -> Iterator[str]:
    """Yield the cyclic Yogini-lord sequence starting at first_yogini."""
    start_idx = YOGINI_LORDS.index(first_yogini)
    i = start_idx
    while True:
        yield YOGINI_LORDS[i]
        i = (i + 1) % 8


def ad_sequence(md_yogini: str) -> list[str]:
    """The 8 AD Yoginis inside a given MD: starts with the MD Yogini itself, then cycles."""
    start_idx = YOGINI_LORDS.index(md_yogini)
    return [YOGINI_LORDS[(start_idx + k) % 8] for k in range(8)]


def compute_yogini(
    *,
    chart_id: str,
    birth_dt: datetime,
    ayanamsha: str = "lahiri",
    ephe_path: str | None = None,
    horizon_end: datetime,
    include_antardasha: bool = True,
) -> tuple[list[YoginiRow], dict]:
    """Compute the full Yogini MD/(AD) sequence from birth_dt to horizon_end."""
    moon_lon, eph_diag = compute_moon_sidereal_longitude(
        birth_dt, ayanamsha=ayanamsha, ephe_path=ephe_path,
    )
    first_yogini, balance_yrs, derive_diag = derive_first_yogini(moon_lon)

    diagnostics = {
        **eph_diag, **derive_diag,
        "birth_iso": birth_dt.isoformat(),
        "horizon_end_iso": horizon_end.isoformat(),
        "ayanamsha": ayanamsha,
        "computed_by": "pyswisseph",
        "days_per_year": DAYS_PER_YEAR,
    }

    verification_note = (
        "FORENSIC §5.2 baseline available; cross-check in "
        "05_TEMPORAL_ENGINES/dasha/yogini/CROSSCHECK_v1_0.md"
    )

    rows: list[YoginiRow] = []
    md_iter = yogini_sequence(first_yogini)
    md_yogini = next(md_iter)
    md_start = birth_dt
    md_remaining_years = balance_yrs

    while md_start < horizon_end:
        md_end = add_years(md_start, md_remaining_years)
        ruler = YOGINI_RULER[md_yogini]
        rows.append(YoginiRow(
            chart_id=chart_id,
            system="yogini",
            planet=ruler,
            yogini_name=md_yogini,
            level="M",
            start_date=md_start.date().isoformat(),
            end_date=md_end.date().isoformat(),
            duration_days=(md_end.date() - md_start.date()).days,
            parent_md=None,
            parent_ad=None,
            computed_by="pyswisseph",
            ayanamsha=ayanamsha,
            needs_verification=False,
            verification_note=verification_note,
        ))
        if include_antardasha:
            md_full_years = YOGINI_DURATIONS_YEARS[md_yogini]
            scale = md_remaining_years / md_full_years
            ad_start = md_start
            for ad_yogini in ad_sequence(md_yogini):
                ad_full_years = (
                    md_full_years
                    * YOGINI_DURATIONS_YEARS[ad_yogini]
                    / YOGINI_TOTAL_YEARS
                )
                ad_years = ad_full_years * scale
                ad_end = add_years(ad_start, ad_years)
                if ad_end > md_end:
                    ad_end = md_end
                rows.append(YoginiRow(
                    chart_id=chart_id,
                    system="yogini",
                    planet=YOGINI_RULER[ad_yogini],
                    yogini_name=ad_yogini,
                    level="A",
                    start_date=ad_start.date().isoformat(),
                    end_date=ad_end.date().isoformat(),
                    duration_days=(ad_end.date() - ad_start.date()).days,
                    parent_md=md_yogini,
                    parent_ad=None,
                    computed_by="pyswisseph",
                    ayanamsha=ayanamsha,
                    needs_verification=False,
                    verification_note=verification_note,
                ))
                ad_start = ad_end
        md_start = md_end
        md_yogini = next(md_iter)
        md_remaining_years = float(YOGINI_DURATIONS_YEARS[md_yogini])

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
    parser.add_argument("--horizon-end", default="2061-01-01")
    parser.add_argument(
        "--output",
        default="05_TEMPORAL_ENGINES/dasha/yogini/YOGINI_RAW_v1_0.json",
    )
    parser.add_argument("--no-antardasha", action="store_true",
                        help="Skip Antardasha rows (faster).")
    args = parser.parse_args()

    birth_dt = parse_iso8601(args.birth)
    horizon_end_dt = datetime.fromisoformat(args.horizon_end + "T00:00:00+00:00")

    rows, diag = compute_yogini(
        chart_id=args.chart_id,
        birth_dt=birth_dt,
        ayanamsha=args.ayanamsha,
        ephe_path=args.ephe_path,
        horizon_end=horizon_end_dt,
        include_antardasha=not args.no_antardasha,
    )

    count_m = sum(1 for r in rows if r.level == "M")
    count_a = sum(1 for r in rows if r.level == "A")

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "schema_version": "1.0",
        "computed_at": datetime.now(tz=timezone.utc).isoformat(),
        "chart_id": args.chart_id,
        "system": "yogini",
        "ayanamsha": args.ayanamsha,
        "computed_by": "pyswisseph",
        "diagnostics": diag,
        "row_counts": {"M": count_m, "A": count_a, "total": len(rows)},
        "rows": [asdict(r) for r in rows],
    }

    out_path.write_text(json.dumps(payload, indent=2))
    print(
        f"Wrote {len(rows)} Yogini rows (M={count_m} A={count_a}) "
        f"to {out_path}"
    )
    print(
        f"  first_yogini={diag['first_yogini']} ruler={diag['ruler_planet']} "
        f"balance_years={diag['balance_years']:.4f}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
