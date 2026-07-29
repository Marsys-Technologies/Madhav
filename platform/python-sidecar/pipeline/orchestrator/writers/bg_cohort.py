"""
pipeline/orchestrator/writers/bg_cohort.py
L0 Brahmagyan synthetic reference cohort writer — seeds bg_synthetic_cohort.

ṢAḌ-DARŚANA campaign, registry item 22 ("Synthetic reference cohort (~10⁴⁺)").
SHAD_DARSHANA_BRIEF_v2_0.md §2 names this writer `bg_cohort.py` — "synthetic
reference cohort (global; L0 idempotency = upsert)".

WHAT THIS WRITER BUILDS (and does not build)
─────────────────────────────────────────────
A large set of SYNTHETIC birth charts (NOT real people) used later, by a later
wave (W2, item 15 "Rarity axis from cohort" + Elevation §12.3's matched
sub-cohort), as a statistical base-rate population: "how often does
configuration X happen across a broad population" needs something to compare
the native's chart against. This writer only POPULATES that reference table —
it computes and stores each synthetic chart's graha positions by sign/
nakshatra (+ Lagna sign/nakshatra, since Elevation §12.3 names "same lagna" as
one of the two matched-sub-cohort keys). It is explicitly NOT a full chart
build (no divisional charts, no dashas, no houses-of-grahas, no MD-lord — the
other §12.3 matching key — since that needs the dasha engine, out of scope
here) and it does NOT compute rarity scores or the matched sub-cohort itself;
those are later-wave consumers of this table, not this writer's job.

SAMPLING METHODOLOGY (a deterministic statistical/computational choice per
CLAUDE.md §N.4 / B.10 — Claude never invents chart values; every position
below is a real pyswisseph computation, only the INPUT birth parameters are
synthetic):

  * N = 10,000 synthetic charts (COHORT_SIZE below) — satisfies the brief's
    "~10⁴⁺" floor for item 22. The floor is aspirational per §N.4: this is
    the count the writer targets, not a number backfilled to hit a target.
  * Birth instant: uniform-random over a 200-year window, 1900-01-01 →
    2099-12-31 (COHORT_WINDOW_START/END), drawn with a FIXED RNG seed
    (COHORT_RNG_SEED) so the cohort is byte-for-byte reproducible across
    rebuilds. 200 years was chosen, not an arbitrary round number: it spans
    ~6.8 Jupiter cycles (~12y) and ~2 full Saturn/Rahu/Ketu cycles (~29.5y/
    ~18.6y), so even the slowest-moving bodies this table tracks complete
    enough revolutions to populate all 12 signs / 27 nakshatras with usable
    density for base-rate statistics — a narrower window would leave the
    slow movers' rarer sign placements under-sampled. It also sits inside
    the coverage bg_ephemeris already builds (1900-01-01 → 2150-12-31), so
    every sampled date is within the ephemeris's verified range.
  * Birth location: latitude uniform over [-60°, +60°], longitude uniform
    over [-180°, +180°]. Latitude/longitude only matter here for the Lagna/
    house computation (planetary sidereal longitudes are geocentric —
    time-only); a coarse uniform draw over the inhabited band is a
    defensible, simple, and fully deterministic proxy for "any place a
    person could be born." ±60° (not the full ±90°) is a deliberate,
    verified choice: the Placidus house system this writer uses for Lagna
    (matching brahmagyan.ganita.l1_positions's own convention) is
    numerically undefined/unstable inside the polar circles (~66.5°+) —
    empirically verified zero swe.houses() failures across a 5,000-sample
    probe at |lat|<=60 vs. frequent failures above ~66.7°. Rather than
    fabricate a placeholder Ascendant for the rare failure case (forbidden
    by CLAUDE.md §N.7 "an honest null beats an invented judgment"), the
    sampling window is drawn narrow enough that the failure case does not
    arise; compute_synthetic_positions() below still degrades to an honest
    `None` (never a fake Aries 0° value) if a future edge case slips through.
  * Ayanamsha: Lahiri (Chitrapaksha) ONLY — the project's primary ayanamsha
    (brahmagyan.ganita.l1_positions AYANAMSHAS orders Lahiri first and the
    native's own chart_facts treat it as canonical). A base-rate cohort only
    needs ONE consistent reference frame to compare a chart's own Lahiri-
    sidereal positions against; computing all 5 ayanamshas here would be
    5× the swisseph cost for no rarity-scoring benefit (W2 always compares
    like-for-like within one ayanamsha).

Each synthetic chart is ONE row: birth parameters + a `positions` JSONB blob
with Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu, Lagna →
{sidereal_longitude, sign_id, sign, nakshatra_id, nakshatra, nakshatra_pada,
is_retrograde}. The per-body sidereal-longitude→sign/nakshatra/pada parsing
mirrors brahmagyan.ganita.l1_positions._parse (same formulas, independently
reproduced here since l1_positions is native-chart-specific / not a reusable
library function).

Conforms to FROZEN WriterBase contract (ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md
§2):
- uses ctx.db_conn exclusively (never opens, commits, or closes it)
- returns WriterResult with actual rows_inserted
- honours ctx.dry_run

L0 idempotency (CLAUDE.md §N.3): global reference table, `ON CONFLICT
(synthetic_id) DO NOTHING` — safe to upsert; the fixed RNG seed makes every
rebuild recompute byte-identical rows, so a re-run correctly reports zero new
inserts (mirrors bg_ephemeris's ON CONFLICT DO NOTHING convention exactly).

ZERO LLM use. Pure deterministic pyswisseph / algorithmic computation +
Python's stdlib `random.Random` with a fixed seed for the synthetic sampling
(a deterministic transform, not generative curation — permitted per CLAUDE.md
§N.4 "Deterministic-first").
"""
from __future__ import annotations

import json
import logging
import random
import time
from datetime import date, datetime, timedelta, timezone
from typing import Any

from pipeline.orchestrator.writers import (
    ContextSpec,
    WriterBase,
    WriterResult,
    register,
)

logger = logging.getLogger(__name__)

# ── Sampling constants (documented above) ────────────────────────────────────

COHORT_SIZE = 10_000
COHORT_RNG_SEED = 20260729  # fixed — reproducibility, not a magic number
COHORT_WINDOW_START = date(1900, 1, 1)
COHORT_WINDOW_END = date(2099, 12, 31)
COHORT_LAT_MIN, COHORT_LAT_MAX = -60.0, 60.0
COHORT_LON_MIN, COHORT_LON_MAX = -180.0, 180.0
AYANAMSHA_KEY = "lahiri"
SAMPLING_METHOD_VERSION = "uniform_1900_2099_lat60_lon180_v1"
SOURCE_CITATION = "pyswisseph DE441 (Swiss Ephemeris); Lahiri ayanamsha; synthetic sampled birth parameters"

SIGN_NAMES = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigasira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni",
    "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Moola", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishtha",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]


# ── Synthetic birth-parameter sampling (pure, no DB/swisseph — testable) ─────

def sample_birth_params(n: int = COHORT_SIZE, seed: int = COHORT_RNG_SEED) -> list[dict[str, Any]]:
    """
    Deterministically sample n synthetic birth parameter sets.

    Returns a list of dicts: {synthetic_id, birth_datetime_utc, lat, lon}.
    Pure function — no DB, no swisseph — so it is independently unit-testable
    for determinism (same seed → same output) without a live DB or ephemeris.
    """
    rng = random.Random(seed)
    window_days = (COHORT_WINDOW_END - COHORT_WINDOW_START).days
    out: list[dict[str, Any]] = []
    for i in range(n):
        offset_days = rng.uniform(0, window_days)
        offset_seconds = rng.uniform(0, 86400)
        birth_dt = (
            datetime(
                COHORT_WINDOW_START.year, COHORT_WINDOW_START.month,
                COHORT_WINDOW_START.day, tzinfo=timezone.utc,
            )
            + timedelta(days=offset_days, seconds=offset_seconds)
        )
        lat = rng.uniform(COHORT_LAT_MIN, COHORT_LAT_MAX)
        lon = rng.uniform(COHORT_LON_MIN, COHORT_LON_MAX)
        out.append({
            "synthetic_id": i + 1,
            "birth_datetime_utc": birth_dt,
            "lat": round(lat, 4),
            "lon": round(lon, 4),
        })
    return out


# ── Position computation for one synthetic birth (mirrors l1_positions) ──────

def _parse_sidereal(sid_lon: float, speed: float) -> dict[str, Any]:
    sid_lon = sid_lon % 360.0
    sign_idx = int(sid_lon / 30)
    nak_span = 360.0 / 27
    nak_idx = int(sid_lon / nak_span)
    nak_pos = sid_lon % nak_span
    pada = int(nak_pos / (nak_span / 4)) + 1
    return {
        "sidereal_longitude": round(sid_lon, 6),
        "sign_id": sign_idx + 1,
        "sign": SIGN_NAMES[sign_idx],
        "nakshatra_id": nak_idx + 1,
        "nakshatra": NAKSHATRA_NAMES[nak_idx],
        "nakshatra_pada": pada,
        "is_retrograde": speed < 0,
    }


def compute_synthetic_positions(
    birth_dt: datetime, lat: float, lon: float, swe: Any, ephe_path: str | None,
) -> dict[str, dict[str, Any]]:
    """
    Compute Lahiri-sidereal Sun..Ketu + Lagna for one synthetic birth instant.

    Returns {graha_name: {sidereal_longitude, sign_id, sign, nakshatra_id,
    nakshatra, nakshatra_pada, is_retrograde}}.
    """
    if ephe_path is not None:
        swe.set_ephe_path(ephe_path)

    jd_utc = swe.julday(
        birth_dt.year, birth_dt.month, birth_dt.day,
        birth_dt.hour + birth_dt.minute / 60.0 + birth_dt.second / 3600.0,
    )
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    aya_val = swe.get_ayanamsa_ut(jd_utc)

    planet_ids = [
        ("Sun", swe.SUN), ("Moon", swe.MOON), ("Mars", swe.MARS),
        ("Mercury", swe.MERCURY), ("Jupiter", swe.JUPITER), ("Venus", swe.VENUS),
        ("Saturn", swe.SATURN), ("Rahu", swe.TRUE_NODE),
    ]

    positions: dict[str, dict[str, Any]] = {}
    rahu_trop = 0.0
    for name, pid in planet_ids:
        flags = swe.FLG_SWIEPH | swe.FLG_SPEED
        result, _ = swe.calc_ut(jd_utc, pid, flags)
        trop_lon, speed = result[0], result[3]
        sid_lon = trop_lon - aya_val
        positions[name] = _parse_sidereal(sid_lon, speed)
        if name == "Rahu":
            rahu_trop = trop_lon

    # Ketu = Rahu + 180°
    ketu_sid = (rahu_trop + 180.0) - aya_val
    ketu_row = _parse_sidereal(ketu_sid, 0.0)
    ketu_row["is_retrograde"] = False
    positions["Ketu"] = ketu_row

    # Lagna (Ascendant) — needs lat/lon; Placidus per l1_positions convention.
    try:
        cusps, ascmc = swe.houses(jd_utc, lat, lon, b"P")
        asc_trop = ascmc[0]
        lagna_row = _parse_sidereal(asc_trop - aya_val, 0.0)
        lagna_row["is_retrograde"] = False
        positions["Lagna"] = lagna_row
    except Exception as exc:  # pragma: no cover — swisseph edge cases (near polar lat)
        # Per CLAUDE.md §N.7 ("an honest null beats an invented judgment"): a failed
        # Ascendant computation is stored as an honest null, never a fabricated
        # placeholder position. The ±60° sampling bound (see module docstring) makes
        # this branch empirically unreachable in practice; it exists as a documented
        # fallback, not a silent substitution.
        logger.warning("[bg_cohort] Lagna computation failed lat=%s lon=%s: %s", lat, lon, exc)
        positions["Lagna"] = None

    return positions


@register("bg_cohort")
class BgCohortWriter(WriterBase):
    """
    Seeds bg_synthetic_cohort — a ~10,000-row synthetic reference population
    of graha/Lagna sidereal positions (Lahiri) used by later waves for rarity/
    base-rate scoring. See module docstring for the full sampling methodology.

    L0 writer — chart-agnostic, global scope. Idempotency: ON CONFLICT
    (synthetic_id) DO NOTHING — see module docstring.
    """

    asset_id = "bg_cohort"

    # Batch size for executemany round-trips.
    _BATCH_SIZE = 500

    def run(self, ctx: ContextSpec) -> WriterResult:
        from brahmagyan.l0_ephemeris import _resolve_ephe_path

        try:
            import swisseph as swe  # type: ignore[import]
            _swe_available = True
        except ImportError:
            swe = None  # type: ignore[assignment]
            _swe_available = False

        t0 = time.time()

        if ctx.dry_run:
            logger.info("[bg_cohort] dry_run=True — skipping INSERT")
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                notes="dry_run",
                duration_seconds=round(time.time() - t0, 2),
            )

        if not _swe_available:
            logger.warning("[bg_cohort] swisseph not available — skipping computation.")
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=0,
                notes="skipped: swisseph unavailable",
                duration_seconds=round(time.time() - t0, 2),
            )

        ephe_path = _resolve_ephe_path()
        samples = sample_birth_params()

        conn = ctx.db_conn
        rows_written = 0
        try:
            with conn.cursor() as cur:
                batch: list[dict[str, Any]] = []
                for sample in samples:
                    positions = compute_synthetic_positions(
                        sample["birth_datetime_utc"], sample["lat"], sample["lon"],
                        swe, ephe_path,
                    )
                    batch.append({
                        "synthetic_id": sample["synthetic_id"],
                        "birth_datetime_utc": sample["birth_datetime_utc"],
                        "birth_lat": sample["lat"],
                        "birth_lon": sample["lon"],
                        "ayanamsha_key": AYANAMSHA_KEY,
                        "positions": json.dumps(positions),
                        "sampling_method": SAMPLING_METHOD_VERSION,
                        "source_citation": SOURCE_CITATION,
                        "build_id": ctx.build_id,
                    })
                    if len(batch) >= self._BATCH_SIZE:
                        rows_written += self._flush_batch(cur, batch)
                        batch = []
                        if rows_written % (self._BATCH_SIZE * 4) == 0:
                            logger.info("[bg_cohort] %d/%d synthetic charts computed", rows_written, len(samples))
                if batch:
                    rows_written += self._flush_batch(cur, batch)
        except Exception as exc:
            logger.error("[bg_cohort] computation failed after %d rows: %s", rows_written, exc)
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=rows_written,
                notes=f"partial: {exc}",
                duration_seconds=round(time.time() - t0, 2),
            )

        elapsed = round(time.time() - t0, 2)
        logger.info("[bg_cohort] complete — %d rows in %.1fs", rows_written, elapsed)
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=rows_written,
            duration_seconds=elapsed,
            notes=(
                f"cohort_size={len(samples)}; ayanamsha={AYANAMSHA_KEY}; "
                f"sampling={SAMPLING_METHOD_VERSION}; seed={COHORT_RNG_SEED}"
            ),
        )

    @staticmethod
    def _flush_batch(cur: Any, batch: list[dict[str, Any]]) -> int:
        cur.executemany(
            """
            INSERT INTO bg_synthetic_cohort
              (synthetic_id, birth_datetime_utc, birth_lat, birth_lon,
               ayanamsha_key, positions, sampling_method, source_citation,
               build_id, computed_at)
            VALUES
              (%(synthetic_id)s, %(birth_datetime_utc)s, %(birth_lat)s, %(birth_lon)s,
               %(ayanamsha_key)s, %(positions)s::jsonb, %(sampling_method)s,
               %(source_citation)s, %(build_id)s, NOW())
            ON CONFLICT (synthetic_id) DO NOTHING
            """,
            batch,
        )
        return cur.rowcount
