---
canonical_id: PHASE_4B_DERIVED_ENRICHMENT_BRIEF
version: 1.0
status: AUTHORED_READY_TO_EXECUTE
campaign: PHASE_4_EPHEMERIS_ACCESSIBILITY
sub_phase: 4B
authored_on: 2026-05-19
estimated_sessions: 1-2
two_stream_branch: analysis/backend-data-pipeline-perf-audit
depends_on: 4A (bd41f13 — query_ephemeris tool + R-TC rule shipped)
---

# §4.B — Derived Ephemeris Enrichment + MEAN_NODE Rahu Fix

## §1 Scope

Enrich `ephemeris_daily` with Vedic-interpretable derived state so the synthesis layer can reason over transit interpretation (not just raw longitudes). Six derived columns + the MEAN_NODE Rahu hygiene fix + a 657K-row rebuild against the existing bootstrap path + extend `query_ephemeris` to surface the new columns via a `derived_fields` param.

What ships:

1. **Migration `059_ephemeris_derived_columns.sql`** — adds six nullable columns to `ephemeris_daily` (mirrored in `ephemeris_daily_staging`).
2. **`platform/python-sidecar/pipeline/ephemeris_derivations.py`** — pure-Python derivation module with BPHS-canonical dignity, combust thresholds, vargottama, sign-ingress, graha-yuddha, whole-sign-house computation. Importable from bootstrap + backfill.
3. **`platform/python-sidecar/pipeline/bootstrap_ephemeris.py`** — updated to compute the 6 derived columns inline AND switch `swe.TRUE_NODE` → `swe.MEAN_NODE` for the Rahu/Ketu calculation.
4. **`platform/python-sidecar/pipeline/enrich_ephemeris_daily.py`** — new one-shot backfill script for existing rows when the operator wants to enrich without a full rebuild. Idempotent; reads existing rows, computes derivations, UPDATEs.
5. **`platform/src/lib/retrieve/query_ephemeris.ts`** — extended with `derived_fields` param; returns derived columns by default; opt-out for tight token budgets.
6. **`retrieval_capability_spec.ts`** — entry updated to advertise the new fields + give patterns the planner can copy.
7. **Tests** — 5 new unit tests on the TS side + a Python-side smoke that derives a known date (1984-02-05 natal) and asserts against FORENSIC-canonical values.
8. **Golden-set entries GT.070–GT.073** — 4 new R-TC entries exercising the derived fields (combust query, dignity query, vargottama query, whole-sign-house query) + paired regression-baseline.
9. **Runbook artifact `RUNBOOK_EPHEMERIS_REBUILD_v1_0.md`** — operator-facing steps for the 657K-row rebuild against production Cloud SQL (NOT executed by the brief; native approves and runs).

What this brief does **NOT** ship (deferred to §4.C / §4.D):

- Panchanga (`query_panchanga` tool — §4.C).
- Transit-event search (`query_transit_event` — §4.D).
- New ayanamshas, Bhava-Chalit houses, asteroid positions (out-of-scope per §6 approved decisions).
- The actual production data rebuild — the executor delivers code + runbook; the operator triggers the rebuild.

## §2 What you must NOT do

- **No branch other than `analysis/backend-data-pipeline-perf-audit`**. Verify before starting.
- **No Chat V2 files**. Same off-limits globs as §4.A.
- **No autonomous `npm run answer:eval`**. Pre-commit gates only.
- **No autonomous production rebuild against Cloud SQL**. The brief delivers the runbook; native approves and executes. Test slice (≤900 rows: 100 days × 9 planets) is acceptable for verification.
- **No new dependencies** beyond what `requirements.txt` already has (pyswisseph 2.10.x is sufficient).
- **No changes to the existing 657K rows' base columns** (longitude/sign/nakshatra/pada/retrograde). The migration adds new columns only; backfill UPDATEs only the new columns. The Rahu fix is delivered via the rebuild path (operator-supervised), not by mutating existing rows mid-brief.

## §3 Approved decisions to honor (from EPHEMERIS_ACCESSIBILITY_RESEARCH §6)

1. **Rahu = MEAN_NODE** — `swe.TRUE_NODE` → `swe.MEAN_NODE` in `bootstrap_ephemeris.py` (line ~160). Comment retained explaining why (consistency with all other compute paths, Vedic always-retrograde convention).
2. **Combustion = BPHS classical** asymmetric per-planet:
   - Sun–Moon: 12°
   - Sun–Mars: 17°
   - Sun–Mercury: 14° direct / 12° retrograde
   - Sun–Jupiter: 11°
   - Sun–Venus: 10° direct / 8° retrograde
   - Sun–Saturn: 15°
3. **Vedic dignity (D1)** — classical Parashari conventions:
   | Planet | Exalted (deg) | Debilitated (deg) | Own sign(s) | Mooltrikona |
   |---|---|---|---|---|
   | Sun | Aries (10°) | Libra (10°) | Leo | Leo 0–20° |
   | Moon | Taurus (3°) | Scorpio (3°) | Cancer | Taurus 3–30° |
   | Mars | Capricorn (28°) | Cancer (28°) | Aries, Scorpio | Aries 0–12° |
   | Mercury | Virgo (15°) | Pisces (15°) | Gemini, Virgo | Virgo 16–20° |
   | Jupiter | Cancer (5°) | Capricorn (5°) | Sagittarius, Pisces | Sagittarius 0–10° |
   | Venus | Pisces (27°) | Virgo (27°) | Taurus, Libra | Libra 0–15° |
   | Saturn | Libra (20°) | Aries (20°) | Capricorn, Aquarius | Aquarius 0–20° |
   | Rahu | Taurus (any) | Scorpio (any) | — | — |
   | Ketu | Scorpio (any) | Taurus (any) | — | — |
   Rahu/Ketu use sign-only (no exact degree) — convention varies, this is the most-cited Parashari form.
4. **Whole-sign house** — native lagna = **Aries** (12°23′55″ Ashwini pada 4, per `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md`). For Aries lagna, whole_sign_house index = `transit_sign_index + 1` (zero-indexed Aries = 0). The migration stores the integer 1–12 for each (date, planet) row. Note in the migration header: "single-native mode — M7 multi-native extension will require recomputation per-native or query-time JOIN against chart_facts."
5. **Vargottama** — true when transit planet's sign in D1 == sign in D9. D9 sign computation per Parashari (`(d9_index = (d1_sign_index × 9 + nakshatra_pada_within_sign_block) mod 12)` is one form, but use the standard Parashari mapping: each sign's D9 starts based on movable/fixed/dual; book references in `00_ARCHITECTURE/`. Use this canonical table: each 3°20′ navamsha within a sign maps to a specific D9 sign starting from: Aries→Aries; Taurus→Capricorn; Gemini→Libra; Cancer→Cancer; Leo→Aries; Virgo→Capricorn; … (full 12×9 table in `ephemeris_derivations.py` constant).
6. **Graha yuddha** — within 1° of another planet AMONG {Mars, Mercury, Jupiter, Venus, Saturn} only. Sun/Moon/Rahu/Ketu excluded. Latitude difference NOT required for this column (BPHS strict-form would require latitude check; we ship the simpler longitude-difference rule with a `// TODO §4.D refinement` note).
7. **Sign ingress** — `sign_ingress_today=true` when this row's `sign` differs from the prior calendar day's `sign` for the same planet. Computed during bootstrap or via window function in backfill.

## §4 Files to create or modify

### §4.1 New file — `platform/migrations/059_ephemeris_derived_columns.sql`

```sql
-- Phase 4B: Derived Vedic-interpretable columns on ephemeris_daily.
-- Single-native mode: whole_sign_house is anchored to native lagna = Aries.
-- Backfill via platform/python-sidecar/pipeline/enrich_ephemeris_daily.py
-- after migration applies.
--
-- The base columns (longitude/latitude/sign/...) are unchanged. These
-- six columns are nullable initially and populated by the enrichment
-- pass or by bootstrap on a fresh build.
BEGIN;

ALTER TABLE ephemeris_daily
  ADD COLUMN IF NOT EXISTS is_combust BOOLEAN,
  ADD COLUMN IF NOT EXISTS combust_orb_deg NUMERIC(7,4),
  ADD COLUMN IF NOT EXISTS dignity_d1 TEXT,         -- 'exalted'|'debilitated'|'own_sign'|'mooltrikona'|'neutral'
  ADD COLUMN IF NOT EXISTS vargottama_today BOOLEAN,
  ADD COLUMN IF NOT EXISTS sign_ingress_today BOOLEAN,
  ADD COLUMN IF NOT EXISTS graha_yuddha_with TEXT,  -- nullable planet name when within 1° of another
  ADD COLUMN IF NOT EXISTS whole_sign_house SMALLINT;  -- 1..12, anchored to native lagna = Aries

ALTER TABLE ephemeris_daily_staging
  ADD COLUMN IF NOT EXISTS is_combust BOOLEAN,
  ADD COLUMN IF NOT EXISTS combust_orb_deg NUMERIC(7,4),
  ADD COLUMN IF NOT EXISTS dignity_d1 TEXT,
  ADD COLUMN IF NOT EXISTS vargottama_today BOOLEAN,
  ADD COLUMN IF NOT EXISTS sign_ingress_today BOOLEAN,
  ADD COLUMN IF NOT EXISTS graha_yuddha_with TEXT,
  ADD COLUMN IF NOT EXISTS whole_sign_house SMALLINT;

-- Targeted indexes for common synthesis-layer filters.
CREATE INDEX IF NOT EXISTS idx_ephemeris_combust ON ephemeris_daily(planet, date) WHERE is_combust = TRUE;
CREATE INDEX IF NOT EXISTS idx_ephemeris_dignity ON ephemeris_daily(planet, dignity_d1) WHERE dignity_d1 IN ('exalted','debilitated');
CREATE INDEX IF NOT EXISTS idx_ephemeris_ingress ON ephemeris_daily(planet, date) WHERE sign_ingress_today = TRUE;
CREATE INDEX IF NOT EXISTS idx_ephemeris_house ON ephemeris_daily(planet, whole_sign_house, date);

COMMIT;
```

### §4.2 New file — `platform/python-sidecar/pipeline/ephemeris_derivations.py`

Pure-Python derivation module. No I/O. Importable from bootstrap + backfill + tests.

```python
"""
ephemeris_derivations — Vedic-interpretable derived state for ephemeris_daily.

All derivations are pure functions of base columns (date, planet, longitude_deg,
sign, sign_degree, nakshatra_pada, is_retrograde) and prior-day state (sign at
date - 1 day) plus a same-day sun row (for combust + graha-yuddha).

Constants are BPHS-canonical Parashari. See PHASE_4B brief §3 for sources.

Single-native mode: whole_sign_house is anchored to NATIVE_LAGNA_SIGN_INDEX = 0
(Aries). Multi-native extension is M7 scope.
"""
from __future__ import annotations
from typing import Iterable, Optional

# Sign index: 0=Aries, 1=Taurus, ..., 11=Pisces.
SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
    "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces",
]
SIGN_TO_IDX = {s: i for i, s in enumerate(SIGNS)}

NATIVE_LAGNA_SIGN = "Aries"
NATIVE_LAGNA_IDX = SIGN_TO_IDX[NATIVE_LAGNA_SIGN]

# ── Combust thresholds (BPHS classical) ───────────────────────────────────────
# Direction-aware for Mercury and Venus (their retrograde orbs are tighter).
# Keyed by planet (lowercase), value is (direct_deg, retrograde_deg).
# For planets without direction variance, both values are equal.
COMBUST_THRESHOLDS_DEG = {
    "moon":    (12.0, 12.0),   # only meaningful for amavasya proximity
    "mars":    (17.0, 17.0),
    "mercury": (14.0, 12.0),
    "jupiter": (11.0, 11.0),
    "venus":   (10.0,  8.0),
    "saturn":  (15.0, 15.0),
    # Sun/Rahu/Ketu: combustion N/A (Sun is the reference; nodes are shadows).
}

# ── D1 dignity tables ─────────────────────────────────────────────────────────
# Each entry: {planet: (exalted_sign, exalt_deg, debilitated_sign, debil_deg,
#                        own_signs:list, mooltrikona_sign, mooltrikona_range:(start,end))}
# Rahu/Ketu use sign-only (no exact deg) — set deg=None.
DIGNITY_TABLE = {
    "sun":     ("Aries",      10.0, "Libra",       10.0, ["Leo"],                       "Leo",         (0.0, 20.0)),
    "moon":    ("Taurus",      3.0, "Scorpio",      3.0, ["Cancer"],                    "Taurus",      (3.0, 30.0)),
    "mars":    ("Capricorn",  28.0, "Cancer",      28.0, ["Aries", "Scorpio"],          "Aries",       (0.0, 12.0)),
    "mercury": ("Virgo",      15.0, "Pisces",      15.0, ["Gemini", "Virgo"],           "Virgo",       (16.0, 20.0)),
    "jupiter": ("Cancer",      5.0, "Capricorn",    5.0, ["Sagittarius", "Pisces"],     "Sagittarius", (0.0, 10.0)),
    "venus":   ("Pisces",     27.0, "Virgo",       27.0, ["Taurus", "Libra"],           "Libra",       (0.0, 15.0)),
    "saturn":  ("Libra",      20.0, "Aries",       20.0, ["Capricorn", "Aquarius"],     "Aquarius",    (0.0, 20.0)),
    "rahu":    ("Taurus",     None, "Scorpio",     None, [],                            None,          None),
    "ketu":    ("Scorpio",    None, "Taurus",      None, [],                            None,          None),
}

# ── D9 navamsha mapping ──────────────────────────────────────────────────────
# For each sign, the D9 starts based on movable/fixed/dual:
#   - Movable (Aries, Cancer, Libra, Capricorn): D9 starts at the same sign.
#   - Fixed (Taurus, Leo, Scorpio, Aquarius): D9 starts at the 9th from that sign.
#   - Dual (Gemini, Virgo, Sagittarius, Pisces): D9 starts at the 5th from that sign.
# Each navamsha spans 3°20'.
def _movable() -> set[str]: return {"Aries", "Cancer", "Libra", "Capricorn"}
def _fixed() -> set[str]:   return {"Taurus", "Leo", "Scorpio", "Aquarius"}

def d9_sign(sign: str, sign_degree: float) -> str:
    """Return the D9 (navamsha) sign for a given D1 sign and degree-within-sign."""
    navamsha_idx = int(sign_degree // (30.0 / 9))  # 0..8
    sign_idx = SIGN_TO_IDX[sign]
    if sign in _movable():
        start_offset = 0
    elif sign in _fixed():
        start_offset = 8  # 9th from = +8 (0-indexed)
    else:  # dual
        start_offset = 4  # 5th from = +4
    d9_idx = (sign_idx + start_offset + navamsha_idx) % 12
    return SIGNS[d9_idx]


# ── Derivation functions ─────────────────────────────────────────────────────
def compute_dignity(planet: str, sign: str, sign_degree: float) -> str:
    """Return one of: 'exalted', 'debilitated', 'own_sign', 'mooltrikona', 'neutral'."""
    p = planet.lower()
    if p not in DIGNITY_TABLE:
        return "neutral"
    exalted, ex_deg, debil, deb_deg, own, mt_sign, mt_range = DIGNITY_TABLE[p]
    # Rahu/Ketu: sign-only check.
    if ex_deg is None:
        if sign == exalted: return "exalted"
        if sign == debil:   return "debilitated"
        return "neutral"
    # Standard planets: mooltrikona takes precedence over own_sign within range.
    if mt_sign and sign == mt_sign:
        lo, hi = mt_range
        if lo <= sign_degree < hi:
            return "mooltrikona"
        # Outside mooltrikona range but in mooltrikona sign → still own_sign if listed.
        if sign in own:
            return "own_sign"
    if sign == exalted:
        return "exalted"
    if sign == debil:
        return "debilitated"
    if sign in own:
        return "own_sign"
    return "neutral"


def compute_combust(
    planet: str,
    longitude_deg: float,
    sun_longitude_deg: float,
    is_retrograde: bool,
) -> tuple[bool, Optional[float]]:
    """Return (is_combust, combust_orb_deg). Returns (False, None) when N/A."""
    p = planet.lower()
    if p == "sun" or p == "rahu" or p == "ketu":
        return False, None
    if p not in COMBUST_THRESHOLDS_DEG:
        return False, None
    direct_orb, retro_orb = COMBUST_THRESHOLDS_DEG[p]
    threshold = retro_orb if is_retrograde else direct_orb
    # Shortest arc between planet and Sun longitudes.
    diff = abs(longitude_deg - sun_longitude_deg) % 360.0
    if diff > 180.0:
        diff = 360.0 - diff
    return (diff <= threshold), round(diff, 4)


def compute_vargottama(sign: str, sign_degree: float) -> bool:
    """True when D1 sign == D9 sign."""
    return d9_sign(sign, sign_degree) == sign


def compute_whole_sign_house(sign: str, native_lagna_idx: int = NATIVE_LAGNA_IDX) -> int:
    """Return whole-sign house 1..12 relative to native lagna."""
    sign_idx = SIGN_TO_IDX[sign]
    return ((sign_idx - native_lagna_idx + 12) % 12) + 1


def compute_sign_ingress(today_sign: str, prior_day_sign: Optional[str]) -> bool:
    """True when sign changed from prior day. False for the very first day in the table."""
    if prior_day_sign is None:
        return False
    return today_sign != prior_day_sign


def compute_graha_yuddha(
    planet: str,
    longitude_deg: float,
    same_day_positions: dict[str, float],
) -> Optional[str]:
    """
    Return the OTHER planet's name when this planet is within 1° of another.
    Only checked among {mars, mercury, jupiter, venus, saturn}.
    same_day_positions: {planet_name: longitude_deg} for the same date.
    """
    YUDDHA_PARTICIPANTS = {"mars", "mercury", "jupiter", "venus", "saturn"}
    p = planet.lower()
    if p not in YUDDHA_PARTICIPANTS:
        return None
    for other, other_lon in same_day_positions.items():
        o = other.lower()
        if o == p or o not in YUDDHA_PARTICIPANTS:
            continue
        diff = abs(longitude_deg - other_lon) % 360.0
        if diff > 180.0:
            diff = 360.0 - diff
        if diff <= 1.0:
            return o
    return None
```

### §4.3 Updated — `platform/python-sidecar/pipeline/bootstrap_ephemeris.py`

Two changes:

**Change 1**: line ~160 (Rahu computation), replace `swe.TRUE_NODE` with `swe.MEAN_NODE`. Update the comment block:

```python
    # Rahu (mean node) — Vedic convention is the smoothed 18.6-year cycle.
    # §4.B 2026-05-19 fix: bootstrap previously used TRUE_NODE, which is
    # osculating and occasionally turns briefly direct (contradicts the
    # Jyotish always-retrograde convention). All other compute paths in this
    # codebase use MEAN_NODE — bootstrap is now consistent.
    r_node = swe.calc_ut(jd, swe.MEAN_NODE, flags)
```

**Change 2**: extend `_compute_day()` to populate the 6 derived columns inline. Inside the per-planet loop, AFTER computing the base row, defer derived computation to a second pass once all 9 planets are known (graha-yuddha needs same-day positions; combust needs the Sun's longitude):

```python
from .ephemeris_derivations import (
    compute_dignity, compute_combust, compute_vargottama,
    compute_whole_sign_house, compute_sign_ingress, compute_graha_yuddha,
)

def _compute_day(swe: Any, jd: float, build_id: str, d: date, prior_day_signs: dict[str, str] | None = None) -> list[dict[str, Any]]:
    # ... existing base-row computation for sun/moon/mars/.../ketu ...

    # Second pass: derived columns. Build same_day_positions map first.
    same_day_positions = {row["planet"]: float(row["longitude_deg"]) for row in rows}
    sun_lon = same_day_positions["sun"]

    for row in rows:
        planet = row["planet"]
        lon = float(row["longitude_deg"])
        sign = row["sign"]
        sdeg = float(row["sign_degree"])
        is_retro = bool(row["is_retrograde"])

        dignity = compute_dignity(planet, sign, sdeg)
        is_comb, comb_orb = compute_combust(planet, lon, sun_lon, is_retro)
        vargottama = compute_vargottama(sign, sdeg)
        ws_house = compute_whole_sign_house(sign)
        ingress = compute_sign_ingress(sign, (prior_day_signs or {}).get(planet))
        yuddha = compute_graha_yuddha(planet, lon, same_day_positions)

        row["dignity_d1"] = dignity
        row["is_combust"] = is_comb
        row["combust_orb_deg"] = comb_orb
        row["vargottama_today"] = vargottama
        row["whole_sign_house"] = ws_house
        row["sign_ingress_today"] = ingress
        row["graha_yuddha_with"] = yuddha

    return rows
```

Extend the `_UPSERT_SQL` to include the 7 new columns (combust split into two: is_combust + combust_orb_deg). Pass `prior_day_signs` between iterations of the date loop in `run()`.

Update `EPHEMERIS_VERSION` constant: `"pyswisseph-2.10.03.2+4B-derived-v1"`.

### §4.4 New file — `platform/python-sidecar/pipeline/enrich_ephemeris_daily.py`

One-shot backfill for existing rows without a full rebuild. Reads each (date, planet) row, computes derivations from existing base columns, UPDATEs. Useful for environments where the operator wants the new columns without re-running 657K Swiss-Ephemeris calls.

```python
"""
enrich_ephemeris_daily — backfill the 6 derived columns onto existing
ephemeris_daily rows without re-running Swiss Ephemeris.

Idempotent: skips rows where dignity_d1 IS NOT NULL (already enriched).

Usage:
    python -m pipeline.enrich_ephemeris_daily [--dry-run] [--limit N]
        [--start YYYY-MM-DD] [--end YYYY-MM-DD]
"""
from __future__ import annotations
import argparse, logging, os
from datetime import date
import psycopg2
import psycopg2.extras

from .ephemeris_derivations import (
    compute_dignity, compute_combust, compute_vargottama,
    compute_whole_sign_house, compute_sign_ingress, compute_graha_yuddha,
)

logger = logging.getLogger(__name__)

_SELECT_DAY_SQL = """
    SELECT date, planet, longitude_deg::float8 AS longitude_deg,
           sign, sign_degree::float8 AS sign_degree, is_retrograde,
           LAG(sign) OVER (PARTITION BY planet ORDER BY date) AS prior_sign
    FROM ephemeris_daily
    WHERE date >= %(start)s AND date <= %(end)s
    ORDER BY date ASC, planet ASC
"""

_UPDATE_SQL = """
    UPDATE ephemeris_daily SET
      dignity_d1         = %(dignity_d1)s,
      is_combust         = %(is_combust)s,
      combust_orb_deg    = %(combust_orb_deg)s,
      vargottama_today   = %(vargottama_today)s,
      sign_ingress_today = %(sign_ingress_today)s,
      whole_sign_house   = %(whole_sign_house)s,
      graha_yuddha_with  = %(graha_yuddha_with)s
    WHERE date = %(date)s AND planet = %(planet)s
"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="1900-01-01")
    parser.add_argument("--end",   default="2100-12-31")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=None, help="Stop after N rows (test slice).")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    db_url = os.environ["DATABASE_URL"]

    # Stream rows ordered by (date, planet) so we can build per-day groups in
    # one pass and use the windowed prior_sign for ingress detection.
    with psycopg2.connect(db_url) as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(_SELECT_DAY_SQL, {"start": args.start, "end": args.end})
            rows = cur.fetchall()
            logger.info("Read %d ephemeris rows for enrichment", len(rows))

    # Group by date so we can compute graha-yuddha + combust within each day.
    from itertools import groupby
    updates = []
    for d, planet_rows in groupby(rows, key=lambda r: r["date"]):
        planet_rows = list(planet_rows)
        positions = {r["planet"]: r["longitude_deg"] for r in planet_rows}
        sun_lon = positions.get("sun")
        if sun_lon is None:
            logger.warning("Day %s missing sun row; skipping derived calc", d)
            continue
        for r in planet_rows:
            dignity = compute_dignity(r["planet"], r["sign"], r["sign_degree"])
            is_comb, comb_orb = compute_combust(r["planet"], r["longitude_deg"], sun_lon, r["is_retrograde"])
            vargottama = compute_vargottama(r["sign"], r["sign_degree"])
            ws_house = compute_whole_sign_house(r["sign"])
            ingress = compute_sign_ingress(r["sign"], r["prior_sign"])
            yuddha = compute_graha_yuddha(r["planet"], r["longitude_deg"], positions)

            updates.append({
                "date": r["date"], "planet": r["planet"],
                "dignity_d1": dignity, "is_combust": is_comb,
                "combust_orb_deg": comb_orb, "vargottama_today": vargottama,
                "sign_ingress_today": ingress, "whole_sign_house": ws_house,
                "graha_yuddha_with": yuddha,
            })
            if args.limit and len(updates) >= args.limit:
                break
        if args.limit and len(updates) >= args.limit:
            break

    logger.info("Computed %d row updates", len(updates))

    if args.dry_run:
        logger.info("DRY RUN — first 3 updates:")
        for u in updates[:3]:
            logger.info("  %s", u)
        return

    with psycopg2.connect(db_url) as conn:
        with conn.cursor() as cur:
            psycopg2.extras.execute_batch(cur, _UPDATE_SQL, updates, page_size=500)
        conn.commit()
    logger.info("Wrote %d updates", len(updates))

if __name__ == "__main__":
    main()
```

### §4.5 Updated — `platform/src/lib/retrieve/query_ephemeris.ts`

Extend the input schema + SELECT to surface the 7 new columns (BPHS columns + whole_sign_house). Add `derived_fields` opt-out param.

```ts
export interface QueryEphemerisInput {
  // ... existing fields (date, start_date, end_date, planet, planets, limit) ...
  /**
   * Which derived columns to include. Defaults to all 6 (dignity, combust,
   * vargottama, ingress, yuddha, house). Pass [] to opt out for token-budget
   * tight queries. Pass a subset to include only specific fields.
   */
  derived_fields?: ('dignity' | 'combust' | 'vargottama' | 'ingress' | 'yuddha' | 'house')[]
}
```

Update the SELECT to always fetch the derived columns; let the response shaper filter by `derived_fields`:

```ts
const sql = `
  SELECT
    date::text AS date, planet,
    longitude_deg::text AS longitude_deg,
    latitude_deg::text AS latitude_deg,
    speed_deg_per_day::text AS speed_deg_per_day,
    is_retrograde, sign, sign_degree::text AS sign_degree,
    nakshatra, nakshatra_pada,
    ayanamsha, ephemeris_version,
    -- Phase 4B derived columns
    dignity_d1, is_combust, combust_orb_deg::text AS combust_orb_deg,
    vargottama_today, sign_ingress_today,
    whole_sign_house, graha_yuddha_with
  FROM ephemeris_daily
  WHERE ${where}
  ORDER BY date ASC, planet ASC
  LIMIT ${limit}
`
```

In the row→JSON mapping, conditionally include each derived field based on `derived_fields` (default = include all). The `content` object structure documented in the RCS becomes:

```json
{
  "date": "2008-04-15", "planet": "saturn",
  "longitude_deg": 145.27, "sign": "Leo", "sign_degree": 25.27,
  "nakshatra": "Purva Phalguni", "nakshatra_pada": 4,
  "is_retrograde": false, "speed_deg_per_day": 0.075,
  "ayanamsha": "lahiri", "ephemeris_version": "pyswisseph-2.10.03.2+4B-derived-v1",
  "dignity": "neutral", "is_combust": false, "combust_orb_deg": 142.3,
  "vargottama": false, "sign_ingress": false,
  "whole_sign_house": 5, "graha_yuddha_with": null
}
```

### §4.6 Updated — `platform/src/lib/router/retrieval_capability_spec.ts`

Update the `query_ephemeris` description + params + patterns to advertise the new fields:

```ts
description:
  'Date-indexed planetary positions PLUS Vedic-interpretable derived state from ' +
  'the ephemeris_daily table (657K rows, 1900-2100, 9 grahas, Lahiri sidereal). ' +
  'Returns per-planet per-day: longitude, sign, nakshatra+pada, retrograde, speed, ' +
  'AND derived state: dignity (exalted/debilitated/own/mooltrikona/neutral), ' +
  'combust state + orb degrees, vargottama (D1=D9 sign), whole-sign-house (relative ' +
  'to native lagna = Aries), sign-ingress flag (entered new sign today), ' +
  'graha-yuddha (within 1° of another planet — among Mars/Mercury/Jupiter/Venus/Saturn). ' +
  'CANONICAL SURFACE for any transit-context query — both the raw positions AND ' +
  'their Vedic interpretation. Default attached at priority 2 under R-TC for any ' +
  'non-natal query. Use derived_fields:[] to skip derived columns for token-tight calls.',
supported_params:
  '{ date?: YYYY-MM-DD; start_date?: YYYY-MM-DD; end_date?: YYYY-MM-DD; ' +
  'planet?: string; planets?: string[]; limit?: number (default 100, max 500); ' +
  'derived_fields?: ("dignity"|"combust"|"vargottama"|"ingress"|"yuddha"|"house")[] ' +
  '(default ALL — empty array opts out) }',
optimal_patterns: [
  'Transit at LEL event: {date:"2008-04-15", planet:"Saturn"} (returns Saturn at marriage with dignity + house + combust status)',
  'Combust check: {start_date:"2018-06-01", end_date:"2018-07-31", planet:"Mercury"} (combust_orb_deg + is_combust per day)',
  'Current transits with full state: {} (today UTC, all 9 grahas, all derived fields)',
  'Sign-ingress scan: {start_date:"2026-01-01", end_date:"2026-12-31", planet:"Jupiter"} (sign_ingress_today=true marks each Jupiter sign-change in the year)',
  'Token-tight raw positions: {date:"2026-05-19", derived_fields:[]}',
],
```

### §4.7 Tests

**TypeScript** — extend `platform/src/lib/retrieve/__tests__/query_ephemeris.test.ts` with 5 new tests:

1. `surfaces dignity field in response by default` — mock row with `dignity_d1='exalted'`, assert response JSON contains `dignity: 'exalted'`.
2. `surfaces combust + orb` — mock row `is_combust=true, combust_orb_deg=10.5`, assert response.
3. `surfaces whole_sign_house` — mock row `whole_sign_house=10`, assert.
4. `derived_fields:[] opts out` — same mock, `derived_fields:[]`, assert response omits all 6 derived keys.
5. `derived_fields:['dignity']` returns only dignity — selective surfacing.

**Python** — new file `platform/python-sidecar/pipeline/__tests__/test_ephemeris_derivations.py`:

```python
"""Unit tests for ephemeris_derivations — assert BPHS-canonical values."""
from pipeline.ephemeris_derivations import (
    compute_dignity, compute_combust, compute_vargottama,
    compute_whole_sign_house, compute_sign_ingress, compute_graha_yuddha,
    d9_sign,
)

def test_sun_exalted_in_aries_at_10deg():
    assert compute_dignity("sun", "Aries", 10.0) == "exalted"

def test_sun_debilitated_in_libra():
    assert compute_dignity("sun", "Libra", 10.0) == "debilitated"

def test_saturn_mooltrikona_in_aquarius_first_20():
    assert compute_dignity("saturn", "Aquarius", 10.0) == "mooltrikona"
    assert compute_dignity("saturn", "Aquarius", 25.0) == "own_sign"

def test_mars_debilitated_in_cancer():
    assert compute_dignity("mars", "Cancer", 28.0) == "debilitated"

def test_rahu_exalted_in_taurus():
    assert compute_dignity("rahu", "Taurus", 0.0) == "exalted"

def test_combust_mercury_retrograde_orb():
    # Mercury retrograde combust threshold is 12°; at 11° from Sun → combust.
    is_c, orb = compute_combust("mercury", 100.0, 89.0, is_retrograde=True)
    assert is_c is True
    assert abs(orb - 11.0) < 0.001

def test_combust_mercury_direct_not_at_13deg():
    # Mercury direct combust threshold is 14°; at 13° from Sun → NOT combust… wait, 13<=14 so IS combust.
    # Test the just-over-threshold case: at 15°, NOT combust.
    is_c, orb = compute_combust("mercury", 100.0, 85.0, is_retrograde=False)
    assert is_c is False  # 15° > 14° threshold
    assert abs(orb - 15.0) < 0.001

def test_combust_sun_returns_false():
    assert compute_combust("sun", 100.0, 100.0, False) == (False, None)

def test_whole_sign_house_aries_lagna():
    # Native lagna = Aries (index 0). Transit in Capricorn (index 9) → house 10.
    assert compute_whole_sign_house("Capricorn") == 10
    # Transit in Aries itself → house 1.
    assert compute_whole_sign_house("Aries") == 1

def test_d9_sign_aries_first_navamsha():
    # Aries is movable; D9 starts at Aries; first 3°20' = Aries.
    assert d9_sign("Aries", 1.0) == "Aries"

def test_d9_sign_taurus_first_navamsha():
    # Taurus is fixed; D9 starts at 9th from Taurus = Capricorn.
    assert d9_sign("Taurus", 1.0) == "Capricorn"

def test_vargottama_aries_first_3deg():
    # Aries D1 + Aries D9 → vargottama
    assert compute_vargottama("Aries", 1.0) is True

def test_vargottama_taurus_first_3deg_is_not():
    # Taurus D1 + Capricorn D9 → NOT vargottama
    assert compute_vargottama("Taurus", 1.0) is False

def test_sign_ingress_today_when_changed():
    assert compute_sign_ingress("Taurus", "Aries") is True
    assert compute_sign_ingress("Aries", "Aries") is False
    assert compute_sign_ingress("Aries", None) is False  # first day in table

def test_graha_yuddha_mars_jupiter_within_1deg():
    same_day = {"mars": 100.0, "jupiter": 100.5}
    assert compute_graha_yuddha("mars", 100.0, same_day) == "jupiter"

def test_graha_yuddha_excludes_sun():
    same_day = {"mars": 100.0, "sun": 100.5}
    assert compute_graha_yuddha("mars", 100.0, same_day) is None
```

### §4.8 Golden-set entries GT.070–GT.073

Append to `platform/tests/eval/planner_golden_set.json`:

```json
{
  "id": "GT.070",
  "query": "Was Mercury combust during my January 2019 job interview?",
  "query_class": "predictive",
  "required_tools": ["lel_query", "query_ephemeris"],
  "forbidden_tools": [],
  "asset_bundle_must_include": ["FORENSIC", "LEL"],
  "planets": ["Mercury"],
  "domains": ["career"],
  "forward_looking": false,
  "notes": "R-TC + LEL anchor. query_ephemeris surfaces is_combust + combust_orb_deg for the LEL event date. Synthesis joins on event_date."
},
{
  "id": "GT.071",
  "query": "Where will Jupiter be exalted next?",
  "query_class": "predictive",
  "required_tools": ["query_ephemeris"],
  "forbidden_tools": ["vector_search"],
  "asset_bundle_must_include": ["FORENSIC"],
  "planets": ["Jupiter"],
  "domains": [],
  "forward_looking": true,
  "notes": "R-TC + dignity filter. Planner emits query_ephemeris with start_date=today, end_date=+5 years, planet=jupiter, and synthesis filters dignity_d1='exalted'."
},
{
  "id": "GT.072",
  "query": "Which house is Saturn currently transiting in my chart?",
  "query_class": "factual",
  "required_tools": ["query_ephemeris"],
  "forbidden_tools": ["vector_search", "pattern_register"],
  "asset_bundle_must_include": ["FORENSIC"],
  "planets": ["Saturn"],
  "domains": [],
  "forward_looking": false,
  "notes": "R-TC + R-FACT. query_ephemeris returns whole_sign_house directly. No synthesis needed beyond surfacing the value."
},
{
  "id": "GT.073",
  "query": "When does Jupiter enter Aries in 2027?",
  "query_class": "factual",
  "required_tools": ["query_ephemeris"],
  "forbidden_tools": ["vector_search"],
  "asset_bundle_must_include": ["FORENSIC"],
  "planets": ["Jupiter"],
  "domains": [],
  "forward_looking": true,
  "notes": "R-TC + sign_ingress filter. Planner emits query_ephemeris with start_date=2027-01-01, end_date=2027-12-31, planet=jupiter. Synthesis filters sign_ingress_today=true AND sign='Aries' to find the exact ingress day."
}
```

Paired regression-baseline extension same shape as 4A pattern.

### §4.9 New file — `00_ARCHITECTURE/RUNBOOK_EPHEMERIS_REBUILD_v1_0.md`

Operator-facing runbook for the 657K-row rebuild against production Cloud SQL. DO NOT execute this from the brief — only document. The native runs it post-merge.

```markdown
# Runbook — Ephemeris Daily Rebuild for §4.B

## When to run
After merging the §4.B PR. Native triggers; brief does NOT auto-execute.

## What it does
Rebuilds the entire ephemeris_daily table (657K rows) with:
- Rahu = MEAN_NODE (was TRUE_NODE) — small longitude shift propagates to sign/nakshatra/pada
- 6 new derived columns populated inline

## Steps
1. Start the Cloud SQL Auth proxy on port 5433: `platform/scripts/start_db_proxy.sh`
2. Export DATABASE_URL pointing at the proxy.
3. Two paths — choose based on whether you want the staging-swap discipline:

### Path A (full rebuild via staging swap — recommended for production):
   ```bash
   # Truncate staging then bootstrap into it
   psql "$DATABASE_URL" -c "TRUNCATE ephemeris_daily_staging;"
   cd platform/python-sidecar
   python -m pipeline.bootstrap_ephemeris --build-id "phase-4b-$(date +%Y%m%d)" --skip-csv-check
   # Bootstrap writes to staging; verify count = 657,450
   psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM ephemeris_daily_staging;"
   # Swap atomically
   python -m pipeline.swap_ephemeris_staging
   ```

### Path B (enrichment-only — fast, but does NOT fix MEAN_NODE Rahu):
   ```bash
   cd platform/python-sidecar
   python -m pipeline.enrich_ephemeris_daily --dry-run --limit 100   # verify
   python -m pipeline.enrich_ephemeris_daily                          # full
   ```

   Use Path B if you accept TRUE_NODE Rahu for now and only want the derived columns.

## Verification
After rebuild:
   ```sql
   -- All rows have derived columns populated
   SELECT COUNT(*) FROM ephemeris_daily WHERE dignity_d1 IS NULL;  -- must be 0 post-Path-A or post-Path-B
   -- Spot-check native birth day positions
   SELECT date, planet, sign, sign_degree, dignity_d1, whole_sign_house
   FROM ephemeris_daily WHERE date='1984-02-05' ORDER BY planet;
   ```

## Rollback
- Path A: re-bootstrap with prior build_id; swap reverts.
- Path B: `UPDATE ephemeris_daily SET dignity_d1=NULL, is_combust=NULL, combust_orb_deg=NULL, vargottama_today=NULL, sign_ingress_today=NULL, whole_sign_house=NULL, graha_yuddha_with=NULL;` (the migration's columns are nullable; clearing them restores pre-4B state).
```

## §5 Verification gates (pre-commit, NOT post-deploy)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis/platform

# G1: TypeScript compiles
npx tsc --noEmit

# G2: TS unit tests — query_ephemeris + retrieval regression
npx vitest run src/lib/retrieve/__tests__/query_ephemeris.test.ts
npx vitest run src/lib/retrieve/__tests__/

# G3: Python derivation unit tests (no DB required)
cd python-sidecar
python -m pytest pipeline/__tests__/test_ephemeris_derivations.py -v
cd ..

# G4: Migration test — apply migration against the local proxy (NOT production)
# Operator runs this; brief verifies the SQL parses syntactically only.
# Brief should NOT execute against Cloud SQL.
psql -h localhost -p 5433 -U <local-test-db> -f migrations/059_ephemeris_derived_columns.sql --dry-run  # if dry-run unsupported, skip

# G5: Test slice — 100-day backfill against local test DB OR pure-Python simulation
# Skip if no local test DB. Code review of enrich_ephemeris_daily.py + manual SQL trace must show:
# - SELECT pulls existing rows with LAG window for prior_sign
# - UPDATE writes 7 new columns only
# - Day-grouping ensures graha_yuddha computes against same-day positions

# G6: planner_regression_gate
npx vitest run tests/eval/planner_regression_gate.test.ts
```

All gates must be green. G4 + G5 are operator-supervised — brief verifies code is syntactically correct + tests pass, native runs them against real DB post-merge.

## §6 Commit + push

Single commit on `analysis/backend-data-pipeline-perf-audit`:

```bash
git add platform/migrations/059_ephemeris_derived_columns.sql \
        platform/python-sidecar/pipeline/ephemeris_derivations.py \
        platform/python-sidecar/pipeline/bootstrap_ephemeris.py \
        platform/python-sidecar/pipeline/enrich_ephemeris_daily.py \
        platform/python-sidecar/pipeline/__tests__/test_ephemeris_derivations.py \
        platform/src/lib/retrieve/query_ephemeris.ts \
        platform/src/lib/retrieve/__tests__/query_ephemeris.test.ts \
        platform/src/lib/router/retrieval_capability_spec.ts \
        platform/tests/eval/planner_golden_set.json \
        platform/tests/eval/fixtures/regression_baseline.json \
        00_ARCHITECTURE/RUNBOOK_EPHEMERIS_REBUILD_v1_0.md

git commit -m "feat(ephemeris): derived columns + MEAN_NODE Rahu + query_ephemeris extension (§4.B)

Phase 4B of the ephemeris accessibility campaign. Adds Vedic-interpretable
derived state to ephemeris_daily so synthesis can reason over transit
interpretation, not just raw longitudes.

Migration 059 adds 7 nullable columns:
  - dignity_d1 (exalted/debilitated/own/mooltrikona/neutral)
  - is_combust + combust_orb_deg (BPHS asymmetric per-planet thresholds)
  - vargottama_today (D1 sign == D9 sign)
  - sign_ingress_today (transitioned to a new sign that day)
  - whole_sign_house (1-12 anchored to native lagna = Aries)
  - graha_yuddha_with (within 1° of another planet)

ephemeris_derivations.py is a pure-Python derivation module — BPHS-canonical
Parashari conventions, no I/O, importable from bootstrap + backfill + tests.

bootstrap_ephemeris.py:
  - Switches Rahu from TRUE_NODE to MEAN_NODE (consistency fix with
    compute_kp / compute_varshaphala / etc.; Jyotish always-retrograde
    convention).
  - Computes the 7 derived columns inline during each daily compute.
  - EPHEMERIS_VERSION bumped to pyswisseph-2.10.03.2+4B-derived-v1.

enrich_ephemeris_daily.py is a new idempotent backfill that computes the
derived columns from existing rows without re-running pyswisseph. Two
operator paths documented in RUNBOOK_EPHEMERIS_REBUILD_v1_0.md.

query_ephemeris (Phase 4A tool) extended with derived_fields opt-out param;
default returns ALL derived columns. RCS entry updated to advertise the new
capability.

Tests:
  - 5 new TS unit tests on the response shape
  - 14 Python unit tests on the derivation pure-functions (BPHS spot-checks)
  - 4 new golden-set entries GT.070-073 + paired regression baseline

Production rebuild deferred to native-supervised runbook. The commit ships
code + migration + runbook; native triggers the actual 657K-row rebuild.

Refs: 00_ARCHITECTURE/briefs/PHASE_4B_DERIVED_ENRICHMENT_BRIEF_v1_0.md
Refs: 00_ARCHITECTURE/PHASE_4_EPHEMERIS_ACCESSIBILITY_MASTER_PLAN_v1_0.md
Refs: 00_ARCHITECTURE/EPHEMERIS_ACCESSIBILITY_RESEARCH_v1_0.md §6"

git push origin analysis/backend-data-pipeline-perf-audit
```

## §7 Acceptance criteria

- [ ] Migration 059 created; ALTER TABLE adds 7 columns to both `ephemeris_daily` + `ephemeris_daily_staging`; 4 indexes created.
- [ ] `ephemeris_derivations.py` ships with BPHS-canonical constants + 6 pure functions + d9_sign helper.
- [ ] `bootstrap_ephemeris.py` updated: `TRUE_NODE → MEAN_NODE`; derived-columns inline pass; UPSERT SQL extended; EPHEMERIS_VERSION bumped.
- [ ] `enrich_ephemeris_daily.py` created; idempotent backfill with dry-run + limit flags; day-grouping for graha-yuddha + combust same-day join.
- [ ] `query_ephemeris.ts` extended: SELECT pulls 7 new columns; `derived_fields` param controls response shaping; default = all included.
- [ ] RCS entry rewritten with new description + params + optimal_patterns.
- [ ] 14 Python unit tests pass (`pytest`).
- [ ] 5 new TS unit tests pass (`vitest`).
- [ ] GT.070–GT.073 added to golden set + regression baseline.
- [ ] `RUNBOOK_EPHEMERIS_REBUILD_v1_0.md` authored at 00_ARCHITECTURE/.
- [ ] `tsc --noEmit` clean.
- [ ] `planner_regression_gate.test.ts` green.
- [ ] Commit lands on `analysis/backend-data-pipeline-perf-audit`.
- [ ] No Chat V2 files touched.
- [ ] Master plan §B 4B block updated: `status: CLOSED` + closing_commit_sha.
- [ ] No production rebuild executed by the brief; runbook delivered for native.

## §8 Report back

When complete:

1. Closing commit SHA on analysis branch.
2. `git log --oneline -3`.
3. All gates pass/fail.
4. Python pytest output.
5. Whether the operator-supervised rebuild was triggered (likely "no — deferred to native") + which path (A or B) you'd recommend.
6. Any §4.C/4.D scope adjustments suggested by what §4.B revealed.

I'll then author the §4.C brief (panchanga) based on what §4.B delivered.
