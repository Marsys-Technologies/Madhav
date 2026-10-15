"""
KP (Krishnamurti Paddhati) sublord computation engine.

M3-W3-C2 deliverable. Uses pyswisseph (Moshier ephemeris by default; falls back
gracefully if SE_EPHE_PATH points to .se1 files) with Lahiri ayanamsha to compute
each planet's sidereal longitude, identify its nakshatra (and the nakshatra
"star lord"), and subdivide the 13°20' nakshatra in Vimshottari proportions to
produce the planet's KP sub-lord and sub-sub-lord (significator level).

KP rule recap:
  - Nakshatra width = 360 / 27 = 13.3333... deg = 800 arcmin.
  - Within a nakshatra, sub-lords cycle in Vimshottari order, BUT starting at
    the nakshatra's own lord (its star lord), not at Ketu.
  - Sub-lord segment width = (lord_vim_years / 120) * 800 arcmin.
  - The sub-sub-lord subdivides the sub-lord segment by the same Vimshottari
    proportions, starting at the sub-lord itself.

Per CLAUDE.md §I B.10 (no fabricated computation): all chart-numerical outputs
trace to a swisseph call. The script does not invent values; if pyswisseph is
absent, the script halts and emits an [EXTERNAL_COMPUTATION_REQUIRED] note.

Per PROJECT_ARCHITECTURE §B.1 (Facts/Interpretation separation): outputs of this
script are L1.5 (computed from L1 chart inputs via Swiss Ephemeris); they are
not L2.5 interpretations. The output JSON is the substrate the temporal engine
queries at synthesis time.

Run direct (chart id and birth datetime are required):
    python3 platform/scripts/temporal/compute_kp.py

Run with explicit args:
    python3 platform/scripts/temporal/compute_kp.py \\
        --chart-id <chart-uuid> \\
        --birth <ISO8601-birth-datetime-with-offset> \\
        --output 05_TEMPORAL_ENGINES/kp/KP_SUBLORDS_RAW_v1_0.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

try:
    import swisseph as swe
except ImportError:
    print(
        "[EXTERNAL_COMPUTATION_REQUIRED]: pyswisseph not installed. "
        "Install with `pip install pyswisseph` and re-run.",
        file=sys.stderr,
    )
    sys.exit(2)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VIMSHOTTARI_LORDS = (
    "Ketu", "Venus", "Sun", "Moon", "Mars",
    "Rahu", "Jupiter", "Saturn", "Mercury",
)
VIMSHOTTARI_DURATIONS_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
VIMSHOTTARI_TOTAL_YEARS = 120

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
NAK_SIZE_ARCMIN = NAK_SIZE_DEG * 60.0  # 800 arcmin

# Nakshatra lord cycle: each nakshatra is owned by VIMSHOTTARI_LORDS[idx % 9].
# Ashwini=Ketu, Bharani=Venus, Krittika=Sun, ..., Revati=Mercury.

PLANETS_ORDER = (
    "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu",
)
SWE_PLANET_CODE = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
    # Rahu is the Mean Node; Ketu = Rahu + 180.
    "Rahu": swe.MEAN_NODE,
}

ZODIAC_SIGNS = (
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
)


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

@dataclass
class KpRow:
    chart_id: str
    planet: str
    sidereal_lon: float          # absolute sidereal longitude in degrees [0, 360)
    sign: str                     # zodiac sign
    nakshatra: str
    nakshatra_lord: str           # KP "star lord"
    sub_lord: str
    sub_sub_lord: str
    computed_by: str
    ayanamsha: str
    needs_verification: bool = False
    verification_note: str | None = None


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def parse_iso8601(s: str) -> datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def setup_swe(*, ayanamsha: str, ephe_path: str | None) -> tuple[int, str]:
    """Return (calc_flags, ephe_mode)."""
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
    return flags, ephe_mode


def jd_for(birth_dt: datetime) -> float:
    if birth_dt.tzinfo is None:
        raise ValueError("birth_dt must be timezone-aware")
    utc_dt = birth_dt.astimezone(timezone.utc)
    return swe.julday(
        utc_dt.year, utc_dt.month, utc_dt.day,
        utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0,
    )


def compute_planet_sidereal_lon(
    jd_ut: float, planet: str, flags: int,
) -> float:
    """Return sidereal longitude in degrees [0, 360)."""
    if planet == "Ketu":
        rahu_pos, _ = swe.calc_ut(jd_ut, swe.MEAN_NODE, flags)
        return (rahu_pos[0] + 180.0) % 360.0
    pos, _ = swe.calc_ut(jd_ut, SWE_PLANET_CODE[planet], flags)
    return pos[0] % 360.0


# ---------------------------------------------------------------------------
# KP sub-lord algorithm
# ---------------------------------------------------------------------------

def nakshatra_index(sidereal_lon_deg: float) -> int:
    return int(sidereal_lon_deg // NAK_SIZE_DEG) % 27


def nakshatra_lord(nak_idx: int) -> str:
    return VIMSHOTTARI_LORDS[nak_idx % 9]


def vim_cycle_starting_at(start_lord: str) -> list[str]:
    """The 9-lord Vimshottari cycle starting at start_lord."""
    start_idx = VIMSHOTTARI_LORDS.index(start_lord)
    return [VIMSHOTTARI_LORDS[(start_idx + k) % 9] for k in range(9)]


def kp_sub_lord(
    sidereal_lon_deg: float,
) -> tuple[str, str, str, dict]:
    """
    Given a sidereal longitude, return (nakshatra_name, sub_lord, sub_sub_lord, diagnostics).
    """
    nak_idx = nakshatra_index(sidereal_lon_deg)
    nak_name = NAKSHATRAS[nak_idx]
    star_lord = nakshatra_lord(nak_idx)

    # Position within the nakshatra in arcminutes [0, 800).
    pos_in_nak_deg = sidereal_lon_deg - nak_idx * NAK_SIZE_DEG
    pos_in_nak_arcmin = pos_in_nak_deg * 60.0

    # Sub-lord chain begins with the nakshatra's own lord, then Vimshottari cycle.
    sub_chain = vim_cycle_starting_at(star_lord)
    cumulative_arcmin = 0.0
    sub_lord = None
    sub_lord_start = 0.0
    sub_lord_width = 0.0
    for lord in sub_chain:
        width = VIMSHOTTARI_DURATIONS_YEARS[lord] / VIMSHOTTARI_TOTAL_YEARS * NAK_SIZE_ARCMIN
        end = cumulative_arcmin + width
        if pos_in_nak_arcmin < end - 1e-9:
            sub_lord = lord
            sub_lord_start = cumulative_arcmin
            sub_lord_width = width
            break
        cumulative_arcmin = end
    if sub_lord is None:
        # Edge of nakshatra; assign final lord.
        sub_lord = sub_chain[-1]
        sub_lord_start = NAK_SIZE_ARCMIN - (
            VIMSHOTTARI_DURATIONS_YEARS[sub_lord] / VIMSHOTTARI_TOTAL_YEARS * NAK_SIZE_ARCMIN
        )
        sub_lord_width = NAK_SIZE_ARCMIN - sub_lord_start

    # Sub-sub-lord: subdivide the sub-lord segment by the same Vimshottari
    # proportions, starting at the sub-lord itself.
    sub_sub_chain = vim_cycle_starting_at(sub_lord)
    pos_in_sub_arcmin = pos_in_nak_arcmin - sub_lord_start
    cumulative2 = 0.0
    sub_sub_lord = None
    for lord in sub_sub_chain:
        width = VIMSHOTTARI_DURATIONS_YEARS[lord] / VIMSHOTTARI_TOTAL_YEARS * sub_lord_width
        end = cumulative2 + width
        if pos_in_sub_arcmin < end - 1e-9:
            sub_sub_lord = lord
            break
        cumulative2 = end
    if sub_sub_lord is None:
        sub_sub_lord = sub_sub_chain[-1]

    diag = {
        "nakshatra_idx": nak_idx,
        "nakshatra_name": nak_name,
        "star_lord": star_lord,
        "pos_in_nakshatra_arcmin": pos_in_nak_arcmin,
        "sub_lord_start_arcmin": sub_lord_start,
        "sub_lord_width_arcmin": sub_lord_width,
        "pos_in_sub_lord_arcmin": pos_in_sub_arcmin,
    }
    return nak_name, sub_lord, sub_sub_lord, diag


def sign_for(sidereal_lon_deg: float) -> str:
    return ZODIAC_SIGNS[int(sidereal_lon_deg // 30.0) % 12]


# ---------------------------------------------------------------------------
# Top-level pipeline
# ---------------------------------------------------------------------------

def compute_kp(
    *,
    chart_id: str,
    birth_dt: datetime,
    ayanamsha: str = "lahiri",
    ephe_path: str | None = None,
) -> tuple[list[KpRow], dict]:
    flags, ephe_mode = setup_swe(ayanamsha=ayanamsha, ephe_path=ephe_path)
    jd_ut = jd_for(birth_dt)

    rows: list[KpRow] = []
    per_planet_diag: dict = {}
    for planet in PLANETS_ORDER:
        lon = compute_planet_sidereal_lon(jd_ut, planet, flags)
        nak_name, sub, sub_sub, diag = kp_sub_lord(lon)
        per_planet_diag[planet] = {
            "sidereal_lon_deg": lon,
            **diag,
        }
        rows.append(KpRow(
            chart_id=chart_id,
            planet=planet,
            sidereal_lon=lon,
            sign=sign_for(lon),
            nakshatra=nak_name,
            nakshatra_lord=diag["star_lord"],
            sub_lord=sub,
            sub_sub_lord=sub_sub,
            computed_by="pyswisseph",
            ayanamsha=ayanamsha,
        ))

    diagnostics = {
        "ephe_mode": ephe_mode,
        "ayanamsha": ayanamsha,
        "computed_by": "pyswisseph",
        "birth_iso": birth_dt.isoformat(),
        "jd_ut": jd_ut,
        "per_planet": per_planet_diag,
    }
    return rows, diagnostics


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

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
    parser.add_argument(
        "--output",
        default="05_TEMPORAL_ENGINES/kp/KP_SUBLORDS_RAW_v1_0.json",
    )
    args = parser.parse_args()

    birth_dt = parse_iso8601(args.birth)
    rows, diag = compute_kp(
        chart_id=args.chart_id,
        birth_dt=birth_dt,
        ayanamsha=args.ayanamsha,
        ephe_path=args.ephe_path,
    )

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "1.0",
        "computed_at": datetime.now(tz=timezone.utc).isoformat(),
        "chart_id": args.chart_id,
        "ayanamsha": args.ayanamsha,
        "computed_by": "pyswisseph",
        "diagnostics": diag,
        "row_count": len(rows),
        "rows": [asdict(r) for r in rows],
    }
    out_path.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {len(rows)} KP rows to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
