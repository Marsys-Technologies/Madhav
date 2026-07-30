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
build (no divisional charts, no houses-of-grahas) and it does NOT compute
rarity scores or the matched sub-cohort itself; those are later-wave consumers
of this table, not this writer's job.

MD-LORD CHAIN (bg_synthetic_cohort_md) — second pass, same writer, same asset
─────────────────────────────────────────────────────────────────────────────
KALA_W2_FIELD_DESIGN_v1_0.md §6.3 (ANTARYĀMIN ADJUDICATION-1) authorizes a
SECOND table, `bg_synthetic_cohort_md`, that this same writer also populates:
an age-based Vimśottarī mahādaśā-lord CHAIN (10 rows per chart spanning ages
[0, 120) years — 9 in the measure-zero case where the Moon sits exactly on a
nakshatra boundary), derived PURELY from the Moon `sidereal_longitude` already
computed and stored above in `positions` — no new ephemeris call, no
swisseph, no PyJHora at build time. This is why it is a second pass of THIS
writer (same `asset_id='bg_cohort'`) and not a new asset: no new
`asset_registry` row, no new `depends_on` edge (§6.3).

An age-interval CHAIN, not a scalar `md_lord` column, because the cohort
spans births 1900-2099 (roughly half in the future relative to any fixed
"today"), so "the current MD lord as of <date>" is undefined/goes-stale for
half the cohort; age is birth-relative and comparable across the whole
200-year sample (§6.3's own reasoning — recorded so this is never
"simplified" back to a scalar).

The Vimśottarī constants below (`VIMSHOTTARI_YEARS`, `NAK_LORD_CYCLE`) are
verified byte-identical to the shipped dasha engine's own source of truth —
`platform/python-sidecar/pyjhora_adapter/dashas.py::_VIMSHOTTARI_YEARS`
(keyed there by PyJHora planet id, resolved through
`pyjhora_adapter/_names.py::PLANET_NAMES`) and
`pyjhora_adapter/_names.py::_NAK_LORD_CYCLE` — and are HARDCODED here rather
than imported, for the same reason this module already hardcodes SIGN_NAMES/
NAKSHATRA_NAMES instead of importing brahmagyan.ganita.l1_positions: importing
`pyjhora_adapter.dashas` pulls in its `._jhora` (PyJHora/Qt-offscreen) import
chain at module load, which would make this "pure arithmetic over an
already-stored longitude" function only unit-testable with the full PyJHora
stack installed. Hardcoding keeps `compute_md_lord_chain()` — no DB, no
swisseph, no PyJHora — testable in total isolation, exactly like the rest of
this writer's sampling math. Sum of `VIMSHOTTARI_YEARS.values()` = 120,
asserted at import time.

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

# ── MD-lord chain constants (KALA_W2_FIELD_DESIGN_v1_0.md §6.3) ──────────────
# Verified byte-identical to pyjhora_adapter/dashas.py's `_VIMSHOTTARI_YEARS`
# (there keyed by PyJHora planet id, resolved through
# pyjhora_adapter/_names.py::PLANET_NAMES: 0=Sun 1=Moon 2=Mars 3=Mercury
# 4=Jupiter 5=Venus 6=Saturn 7=Rahu 8=Ketu) and to that module's own
# `_NAK_LORD_CYCLE`. Hardcoded here rather than imported — see module
# docstring for why (keeps this file's dasha arithmetic PyJHora-import-free).
VIMSHOTTARI_YEARS: dict[str, int] = {
    "Sun": 6, "Moon": 10, "Mars": 7, "Mercury": 17, "Jupiter": 16,
    "Venus": 20, "Saturn": 19, "Rahu": 18, "Ketu": 7,
}
assert sum(VIMSHOTTARI_YEARS.values()) == 120, "Vimshottari cycle must total 120 years"

# Nakshatra-lord cycle, 0-based nakshatra index (nak0 = 0..26): the lord of
# nakshatra `nak0` (0-based) is NAK_LORD_CYCLE[nak0 % 9]. Identical to
# pyjhora_adapter/_names.py::_NAK_LORD_CYCLE (there indexed 1-based via
# NAKSHATRA_LORDS[i] = _NAK_LORD_CYCLE[(i - 1) % 9]).
NAK_LORD_CYCLE: list[str] = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
]

CHAIN_VERSION = "vim_md_age_v1"


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


class MdChainAuthorityDivergence(ValueError):
    """
    Raised when the age-chain's derived birth nakshatra disagrees with the
    nakshatra_id already stored in `positions['Moon']` (§N.5 halt-worthy —
    "if a signal's derivation disagrees with the L1/L0 fact it cites, that is
    a halt-worthy bug, not a stored divergence"). Both sides share the exact
    same `int(sid_lon / (360/27))` formula (see `_parse_sidereal` above), so
    this is structurally near-unreachable; it exists as a real detector, not
    a decorative one (§N.8 — a guard needs a code path that could fail).
    """


def compute_md_lord_chain(positions: dict[str, Any] | None) -> list[dict[str, Any]]:
    """
    Pure age-interval Vimśottarī MD-lord chain for one synthetic chart, per
    KALA_W2_FIELD_DESIGN_v1_0.md §6.3 — the exact algorithm cited there from
    `pyjhora_adapter/dashas.py::compute_dashas()` / `jhora`'s own
    `vimsottari_mahadasa()`, reproduced here in age-years so it needs no
    ephemeris/PyJHora call: it reads only the already-stored Moon
    `sidereal_longitude` (§N.5 — never recomputed).

    No DB, no swisseph, no PyJHora — pure arithmetic, unit-testable in
    isolation.

    Returns a list of dicts (each a future `bg_synthetic_cohort_md` row minus
    `synthetic_id`): `md_index` (1..10), `md_lord`, `start_age_years`,
    `end_age_years`, `md_full_years`, `is_partial`. Exactly 10 rows in the
    general case; exactly 9 in the measure-zero case where the Moon sits
    precisely on a nakshatra boundary (`frac == 0.0`, i.e. `elapsed == 0.0`).

    Honest-empty: returns `[]` if `positions` is falsy or has no `Moon` entry
    (Moon is never expected to be null per this writer's own docstring — only
    Lagna can fail — but a single missing/malformed row must never crash the
    whole 10,000-row batch; see the writer's `run()` for how this is counted).

    Raises `MdChainAuthorityDivergence` if the derived birth nakshatra
    disagrees with the stored `positions['Moon']['nakshatra_id']` — a
    halt-worthy bug per §N.5, never silently absorbed.
    """
    if not positions:
        return []
    moon = positions.get("Moon")
    if not moon:
        return []

    moon_lon = float(moon["sidereal_longitude"])
    stored_nak_id = int(moon["nakshatra_id"])

    one_star = 360.0 / 27.0
    nak0 = int(moon_lon / one_star)  # 0..26 — same floor _parse_sidereal takes
    if (nak0 + 1) != stored_nak_id:
        raise MdChainAuthorityDivergence(
            f"l1_authority_divergence: derived birth nakshatra {nak0 + 1} != "
            f"stored positions['Moon']['nakshatra_id']={stored_nak_id} "
            f"(moon_lon={moon_lon})"
        )

    frac = (moon_lon - nak0 * one_star) / one_star  # portion of nakshatra traversed
    lord = NAK_LORD_CYCLE[nak0 % 9]
    full = VIMSHOTTARI_YEARS[lord]
    elapsed = frac * full  # years of the birth MD consumed pre-birth

    rows: list[dict[str, Any]] = [{
        "md_index": 1,
        "md_lord": lord,
        "start_age_years": 0.0,
        "end_age_years": full - elapsed,
        "md_full_years": full,
        "is_partial": frac > 0.0,
    }]
    age = full - elapsed
    first_lord = lord
    idx = nak0 % 9
    for k in range(2, 10):  # the next eight lords
        idx = (idx + 1) % 9
        lord = NAK_LORD_CYCLE[idx]
        y = VIMSHOTTARI_YEARS[lord]
        rows.append({
            "md_index": k,
            "md_lord": lord,
            "start_age_years": age,
            "end_age_years": age + y,
            "md_full_years": y,
            "is_partial": False,
        })
        age += y
    if elapsed > 0.0:  # the cycle repeats to close the cover at exactly age 120
        rows.append({
            "md_index": 10,
            "md_lord": first_lord,
            "start_age_years": age,
            "end_age_years": 120.0,
            "md_full_years": VIMSHOTTARI_YEARS[first_lord],
            "is_partial": True,
        })
    return rows


@register("bg_cohort")
class BgCohortWriter(WriterBase):
    """
    Seeds bg_synthetic_cohort — a ~10,000-row synthetic reference population
    of graha/Lagna sidereal positions (Lahiri) used by later waves for rarity/
    base-rate scoring — AND, second pass same writer/same asset_id,
    bg_synthetic_cohort_md — the age-based Vimśottarī MD-lord chain derived
    from each row's already-computed Moon longitude (KALA_W2_FIELD_DESIGN_v1_0
    §6.3, ANTARYĀMIN ADJUDICATION-1). See module docstring for both.

    L0 writer — chart-agnostic, global scope. Idempotency: ON CONFLICT
    (synthetic_id) DO NOTHING for bg_synthetic_cohort, ON CONFLICT
    (synthetic_id, md_index) DO NOTHING for bg_synthetic_cohort_md — see
    module docstring.
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
        md_rows_written = 0
        md_skipped_honest_null = 0
        try:
            with conn.cursor() as cur:
                batch: list[dict[str, Any]] = []
                md_batch: list[dict[str, Any]] = []
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

                    # ── MD-lord chain, second pass (§6.3) — from the SAME
                    # already-computed `positions`, no extra ephemeris call. A
                    # missing/null Moon (structurally near-unreachable — see
                    # module docstring) is an honest-empty skip, never a crash.
                    chain_rows = compute_md_lord_chain(positions)
                    if not chain_rows:
                        md_skipped_honest_null += 1
                    for row in chain_rows:
                        md_batch.append({
                            "synthetic_id": sample["synthetic_id"],
                            "md_index": row["md_index"],
                            "md_lord": row["md_lord"],
                            "start_age_years": round(row["start_age_years"], 6),
                            "end_age_years": round(row["end_age_years"], 6),
                            "md_full_years": row["md_full_years"],
                            "is_partial": row["is_partial"],
                            "chain_version": CHAIN_VERSION,
                        })

                    # IMPORTANT: bg_synthetic_cohort_md.synthetic_id FK-references
                    # bg_synthetic_cohort.synthetic_id, so the cohort batch for a
                    # given synthetic_id MUST be inserted (even if not yet
                    # committed — same-transaction visibility is enough) before
                    # its MD-chain rows are. Both flushes are therefore gated on
                    # the SAME trigger (the cohort batch's own size), cohort
                    # first, chain second — never chain-batch-size-triggered on
                    # its own, which would flush chain rows for synthetic_ids
                    # still sitting uninserted in the cohort batch.
                    if len(batch) >= self._BATCH_SIZE:
                        rows_written += self._flush_batch(cur, batch)
                        batch = []
                        if rows_written % (self._BATCH_SIZE * 4) == 0:
                            logger.info("[bg_cohort] %d/%d synthetic charts computed", rows_written, len(samples))
                        if md_batch:
                            md_rows_written += self._flush_md_batch(cur, md_batch)
                            md_batch = []
                if batch:
                    rows_written += self._flush_batch(cur, batch)
                if md_batch:
                    md_rows_written += self._flush_md_batch(cur, md_batch)
        except Exception as exc:
            logger.error("[bg_cohort] computation failed after %d rows (%d md rows): %s", rows_written, md_rows_written, exc)
            return WriterResult(
                asset_id=self.asset_id,
                rows_inserted=rows_written,
                notes=f"partial: {exc} (md_rows_inserted={md_rows_written})",
                duration_seconds=round(time.time() - t0, 2),
            )

        elapsed = round(time.time() - t0, 2)
        logger.info(
            "[bg_cohort] complete — %d rows in %.1fs; md-chain: %d rows (%d honest-null skipped)",
            rows_written, elapsed, md_rows_written, md_skipped_honest_null,
        )
        return WriterResult(
            asset_id=self.asset_id,
            rows_inserted=rows_written,
            duration_seconds=elapsed,
            notes=(
                f"cohort_size={len(samples)}; ayanamsha={AYANAMSHA_KEY}; "
                f"sampling={SAMPLING_METHOD_VERSION}; seed={COHORT_RNG_SEED}; "
                f"md_chain_version={CHAIN_VERSION}; md_rows_inserted={md_rows_written}; "
                f"md_skipped_honest_null={md_skipped_honest_null}"
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

    @staticmethod
    def _flush_md_batch(cur: Any, batch: list[dict[str, Any]]) -> int:
        """
        Insert bg_synthetic_cohort_md rows. L0 idempotency (§N.3): ON CONFLICT
        (synthetic_id, md_index) DO NOTHING — the chain is a pure function of
        the already-stored Moon longitude, so a re-run recomputes
        byte-identical rows (mirrors bg_synthetic_cohort's own convention).
        """
        cur.executemany(
            """
            INSERT INTO bg_synthetic_cohort_md
              (synthetic_id, md_index, md_lord, start_age_years, end_age_years,
               md_full_years, is_partial, chain_version, computed_at)
            VALUES
              (%(synthetic_id)s, %(md_index)s, %(md_lord)s, %(start_age_years)s,
               %(end_age_years)s, %(md_full_years)s, %(is_partial)s,
               %(chain_version)s, NOW())
            ON CONFLICT (synthetic_id, md_index) DO NOTHING
            """,
            batch,
        )
        return cur.rowcount
