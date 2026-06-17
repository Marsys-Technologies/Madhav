---
brief_id: M2_A_MINOR
karn_session_name: KARN-W4-R1-A-MINOR
wave: 4
stream: A
status: COMPLETE
authored_by: Claude (Cowork) 2026-04-30 — Wave 3 close
authored_for: Claude Code execution (autonomous, long-running)
session_type: implementation (sidecar endpoint + chart_facts extractor extension + re-ingest + verify)
target_branch: redesign/r0-foundation
parent_plan: 00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md §A4
karn_protocol: 00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md
karn_session_log: 00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md
related_briefs:
  predecessor: KARN-W1-R1-PHASE-ALPHA (activation matrix), KARN-W2-R2-CHART-FACTS-ETL (chart_facts 795 rows baseline)
  blocks: M2_C5_TEMPORAL_EXTENSION (B4 depends on dasha_chain endpoint being live)
parallel_stream_note: |
  Two other Wave-4 briefs run concurrently:
  - KARN-W4-R2-C234-BUNDLE (Stream B, TypeScript — kp_query + saham_query + divisional_query)
  - KARN-W4-R3-CHART-FACTS-QUERY (Stream B, TypeScript — chart_facts_query parametric tool)
  Disjoint scopes:
  - W4-R1 owns: python-sidecar/ + chart_facts_extractor.py (re-ingest planet rows only)
  - W4-R2 owns: retrieve/kp_query.ts + saham_query.ts + divisional_query.ts (CREATE only)
  - W4-R3 owns: retrieve/chart_facts_query.ts (CREATE only)
  No file-path collision is possible.
estimated_time: ½–1 day single Claude Code session

carry_forward_notes:
  - "Next mahadasha is Ketu MD (2027-2034), NOT Saturn MD. Saturn MD was historical (1992-2010).
     Any dasha_chain output or test fixture referencing the native's upcoming MD must use Ketu."
  - "137 rag_chunks (126 UCN H3 + 11 LEL) have 0 embeddings from W3-R1 (Vertex AI not triggered
     in standalone runs). If this session triggers a full pipeline build, those embeddings will land.
     Not a W4-R1 obligation, but note it in closing summary if observed."
  - "Pre-existing Jest ESM issue: 13 test suites fail with Babel/ESM config. Baseline is
     13 failed / ~964 passed. Do NOT treat these as regressions."

scope_summary: |
  Three consolidated extensions collectively completing M2-A.3 through M2-A.5:

  1. M2-A.3 — dasha_chain endpoint. New Python sidecar endpoint /dasha_chain that accepts
     {native_id, date} and returns the full 5-level Vimshottari period active at that date:
     MD / AD / PD / SD / PD2 (Maha / Antar / Pratyantar / Sookshma / Prana dasha).
     Computation uses the proportional subdivision algorithm from the Vimshottari 120-year
     system applied to the native's epoch (derived from ephemeris_positions or FORENSIC data).
     Date range: 1900-01-01 through 2100-12-31. Required by W5-R1 (temporal extension brief).

  2. M2-A.4 — nakshatra_pada in chart_facts. Ensure chart_facts rows in the `planet` category
     (D1 placements, 9 planets + Lagna) carry nakshatra_pada (1–4) in value_json. Pre-flight
     check determines whether this is already present. If absent, extend chart_facts_extractor.py
     §2.1 parser to derive pada from the planet's absolute longitude (which §2.1 carries). Re-upsert
     only the affected rows (planet category, D1, is_stale=false). Target: 10/10 planet+Lagna rows
     have non-NULL nakshatra_pada in value_json.

  3. M2-A.5 — chalit dual-house verification. Confirm chart_facts exposes both rashi_house and
     chalit_house per planet. The W2-R2 brief already landed the `chalit_shift` category (9 rows)
     with rashi_house + chalit_house in value_json. This session verifies those rows are correct and
     that the planet D1 rows ALSO carry rashi_house in value_json (they may already — verify and
     patch if absent). No separate migration needed; value_json is already jsonb.

  Net effect: the sidecar can answer "which dasha level am I in at date X" with 5-level precision;
  chart_facts planet rows are fully annotated with pada and dual-house; downstream tools (W4-R2/R3)
  can filter by pada and surface both house systems.

may_touch:
  - platform/python-sidecar/routers/dasha_chain.py                            # CREATE — new router
  - platform/python-sidecar/main.py                                           # register /dasha_chain route
  - platform/python-sidecar/tests/test_dasha_chain.py                         # CREATE — ≥5 tests
  - platform/python-sidecar/pipeline/extractors/chart_facts_extractor.py      # extend §2.1 parser for nakshatra_pada + rashi_house
  - platform/python-sidecar/pipeline/extractors/__tests__/test_chart_facts_extractor.py  # extend tests
  - platform/python-sidecar/pipeline/loaders/chart_facts_loader.py            # no change expected; only if category list needs update
  - platform/python-sidecar/pipeline/ingest_chart_facts.py                    # run re-ingest of planet rows (may already exist or create)
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_A_MINOR.md                     # status flip PENDING → COMPLETE
  - 00_ARCHITECTURE/BRIEFS/M2_A_MINOR_VERIFICATION_<DATE>.txt                 # CREATE — AC evidence
  - 00_ARCHITECTURE/M1_M2_ACTIVATION_MATRIX.md                               # update §4 (A-minor rows) + §7

must_not_touch:
  - CLAUDECODE_BRIEF.md (root)
  - platform/migrations/**                                                    # no schema change needed (value_json is already jsonb)
  - platform/python-sidecar/pipeline/extractors/msr_extractor.py             # W2-R1 territory
  - platform/python-sidecar/pipeline/extractors/cgm_extractor.py             # W2-R3 territory
  - platform/python-sidecar/pipeline/loaders/cgm_loader.py                  # W2-R3 territory
  - platform/python-sidecar/pipeline/chunkers/**                             # W3-R1 territory
  - platform/src/lib/retrieve/**                                             # W4-R2 and W4-R3 territory
  - platform/src/lib/router/**                                               # W4-R2 and W4-R3 territory
  - platform/src/components/**                                               # UI/UX scope
  - platform/src/app/**                                                      # UI/UX scope
  - 035_DISCOVERY_LAYER/**                                                   # Stream C territory
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_C234_BUNDLE.md               # sibling Wave-4
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_C1_CHART_FACTS_QUERY.md      # sibling Wave-4
---

# KARN-W4-R1-A-MINOR — Execution Brief

## §0 — Context

This is an autonomous Claude Code session. Read this entire brief before writing any code. Then execute
§1 (pre-flight) before touching anything. Halt immediately if any pre-flight check fails.

Parent plan: `M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md §A4`. You are delivering three small consolidations
(M2-A.3 + M2-A.4 + M2-A.5) that complete the "A-minor" corpus-fact augmentations. Wave 4 runs
W4-R1 (this session), W4-R2 (TypeScript bundle), and W4-R3 (chart_facts_query) in parallel — you
own only the Python sidecar + chart_facts extractor; do not touch the TypeScript retrieve layer.

**Native:** Abhisek Mohanty, born 1984-02-05, 10:43 IST, Bhubaneswar. Moon in Uttara Bhadrapada.
Current MD: Mercury. Next MD: **Ketu (2027-2034)**, NOT Saturn. Saturn MD was 1992–2010.

---

## §1 — Pre-flight self-diagnostics

Run these checks before any code or DB write. Halt on any failure.

```bash
# PF.1 — Branch check
git branch --show-current
# Expected: redesign/r0-foundation. Any other output → HALT.

# PF.2 — Working tree clean
git status --short
# Expected: clean or only files in may_touch list above. Unexpected modifications → HALT.

# PF.3 — DB connectivity (Cloud SQL Auth Proxy)
pg_isready -h 127.0.0.1 -p 5433
# If not ready: bash platform/scripts/start_db_proxy.sh &; sleep 30; retry.
# Still not ready → HALT with "Auth Proxy unreachable".

# PF.4 — chart_facts baseline
psql "host=127.0.0.1 port=5433 dbname=amjis user=amjis-app" -c \
  "SELECT COUNT(*) FROM chart_facts WHERE is_stale=false;"
# Expected: 795. If materially different, note in closing summary but continue.

# PF.5 — planet rows: do they already have nakshatra_pada?
psql "host=127.0.0.1 port=5433 dbname=amjis user=amjis-app" -c \
  "SELECT fact_id, value_json->>'nakshatra_pada' AS pada
   FROM chart_facts
   WHERE category='planet' AND divisional_chart='D1' AND is_stale=false
   ORDER BY fact_id LIMIT 15;"
# Record: how many rows have non-NULL nakshatra_pada? This determines if M2-A.4 needs work.

# PF.6 — chalit_shift baseline
psql "host=127.0.0.1 port=5433 dbname=amjis user=amjis-app" -c \
  "SELECT fact_id, value_json FROM chart_facts WHERE category='chalit_shift' AND is_stale=false;"
# Expected: 9 rows, each with rashi_house + chalit_house in value_json.
# If missing or zero rows → need to re-run chart_facts_extractor §17 section (note in AC.7).

# PF.7 — dasha_chain: does /dasha_chain endpoint already exist?
grep -r "dasha_chain" platform/python-sidecar/routers/ platform/python-sidecar/main.py 2>/dev/null
# Expected: no output (endpoint not yet created). If already exists, review before overwriting.

# PF.8 — sidecar reachable
curl -s -o /dev/null -w "%{http_code}" "$PYTHON_SIDECAR_URL/health" 2>/dev/null || echo "sidecar-check-skip"
# If 200: note current revision. If not reachable: will need local test mode.

# PF.9 — Python sidecar tests baseline
cd platform/python-sidecar && python -m pytest tests/ rag/chunkers/ -q --tb=no 2>&1 | tail -5
# Record pass/fail counts as baseline.
```

---

## §2 — Implementation

### §2.1 — M2-A.3: /dasha_chain endpoint

**Goal:** New sidecar endpoint that, given `{native_id, date}`, returns the complete 5-level
Vimshottari dasha active at `date` for the native.

**Vimshottari system constants:**

```python
# Period durations in years (total = 120)
VIMSHOTTARI_ORDER = [
    ("Ketu",    7),
    ("Venus",   20),
    ("Sun",     6),
    ("Moon",    10),
    ("Mars",    7),
    ("Rahu",    18),
    ("Jupiter", 16),
    ("Saturn",  19),
    ("Mercury", 17),
]
```

**Proportional subdivision rule:** An antardasha (AD) within a mahadasha (MD) has duration:
`AD_years = MD_years × (AD_lord_years / 120)`

A pratyantardasha (PD) within an AD:
`PD_years = AD_years × (PD_lord_years / 120)`

And so on for sookshma (SD) and prana (PD2).

The sequence within any period always follows the same VIMSHOTTARI_ORDER, starting from the lord
of that period.

**Finding the epoch:** The dasha_chain computation needs a known start date. The most reliable
anchor is the native's birth chart. The Moon is in Uttara Bhadrapada, which makes Saturn the
dasha lord at birth. The exact dasha balance at birth can be found from:
- `chart_facts` rows with `category='dasha_vimshottari'` — these have the MD/AD schedule
- Or from `ephemeris_positions` table for the Moon's longitude at birth

**Approach (in order of preference):**

1. **Query chart_facts for MD start dates** — the `dasha_vimshottari` rows should have the full
   MD schedule. Extract Saturn MD start (≈ 1984-02-05 + balance) and use it as the epoch.
   If chart_facts has the MD periods with start/end dates in value_json, use them directly.

2. **Compute from Moon longitude** — if chart_facts doesn't have explicit date ranges, use the
   Moon's absolute longitude from chart_facts `planet` D1 rows, compute the Moon's nakshatra
   position within Uttara Bhadrapada (Saturn-ruled, spans 306°40' – 320°00' sidereal), derive
   the fraction elapsed, and from that compute the Saturn MD balance at birth. Then build the
   full schedule forward from birth date.

3. **Hard-code the epoch from FORENSIC data** — as a fallback, the FORENSIC document §5.1 has
   the MD/AD schedule explicitly. Read it from the source file if needed.

**Create `platform/python-sidecar/routers/dasha_chain.py`:**

```python
"""
MARSYS-JIS Sidecar — /dasha_chain endpoint (M2-A.3)

Given {native_id, date}, return the full 5-level Vimshottari dasha
active at that date: MD / AD / PD / SD / PD2.

Date range: 1900-01-01 through 2100-12-31.
"""

from datetime import date, timedelta
from decimal import Decimal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import psycopg2
import os

router = APIRouter()

# Vimshottari system: (lord_name, period_years) in canonical order
VIMSHOTTARI = [
    ("Ketu",    7),
    ("Venus",   20),
    ("Sun",     6),
    ("Moon",    10),
    ("Mars",    7),
    ("Rahu",    18),
    ("Jupiter", 16),
    ("Saturn",  19),
    ("Mercury", 17),
]
TOTAL_YEARS = 120  # Vimshottari cycle

DAYS_PER_YEAR = 365.25  # Julian year approximation


class DashaChainRequest(BaseModel):
    native_id: str
    date: str  # ISO format: YYYY-MM-DD


class DashaLevel(BaseModel):
    lord: str
    start: str  # ISO date
    end: str    # ISO date


class DashaChainResponse(BaseModel):
    native_id: str
    query_date: str
    md: DashaLevel
    ad: DashaLevel
    pd: DashaLevel
    sd: DashaLevel
    pd2: DashaLevel


def _years_to_days(years: float) -> float:
    return years * DAYS_PER_YEAR


def _lord_years(lord: str) -> int:
    for name, yrs in VIMSHOTTARI:
        if name == lord:
            return yrs
    raise ValueError(f"Unknown dasha lord: {lord}")


def _sequence_from(lord: str):
    """Return VIMSHOTTARI order starting at lord."""
    idx = next(i for i, (n, _) in enumerate(VIMSHOTTARI) if n == lord)
    return VIMSHOTTARI[idx:] + VIMSHOTTARI[:idx]


def _build_periods(start_date: date, lord: str, total_years: float, level_years_fn):
    """
    Build sub-period schedule for a period of total_years starting at start_date,
    where lord is the MD/AD/PD/SD lord.
    level_years_fn(sub_lord_years) → duration of that sub-period in years.
    Returns list of (lord, start_date, end_date).
    """
    seq = _sequence_from(lord)
    periods = []
    current = start_date
    for sub_lord, sub_lord_years in seq:
        sub_duration_years = level_years_fn(sub_lord_years)
        sub_duration_days = int(_years_to_days(sub_duration_years))
        end = current + timedelta(days=sub_duration_days)
        periods.append((sub_lord, current, end))
        current = end
    return periods


def _get_md_epoch(native_id: str) -> tuple[str, date]:
    """
    Return (md_lord, md_start_date) for the first MD in the schedule
    (i.e., the MD that was active at or before birth, with the start date
    adjusted for dasha balance).

    Strategy: query chart_facts for dasha_vimshottari rows with explicit
    dates in value_json. Fall back to computing from Moon longitude.
    """
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL not set")

    conn = psycopg2.connect(db_url)
    try:
        cur = conn.cursor()
        # Try to get MD periods with start/end dates from chart_facts
        cur.execute("""
            SELECT fact_id, value_text, value_json
            FROM chart_facts
            WHERE native_id IS NULL  -- chart_facts is build-scoped; native_id not a column
               OR TRUE               -- always returns all rows
            -- Filter by dasha_vimshottari MD-level rows (not AD)
            LIMIT 1
        """)
        # NOTE: chart_facts has no native_id column (per §1.2 of ACTIVATION_MATRIX).
        # All rows belong to the native (single-native system).

        # Query dasha_vimshottari rows
        cur.execute("""
            SELECT fact_id, value_text, value_json
            FROM chart_facts
            WHERE category = 'dasha_vimshottari'
              AND is_stale = false
            ORDER BY fact_id
        """)
        rows = cur.fetchall()

        # Try to extract MD start dates from value_json
        # Expected value_json shape: {"lord": "Mercury", "start": "2023-...", "end": "2040-...", "level": "MD"}
        md_periods = []
        for fact_id, value_text, value_json in rows:
            if isinstance(value_json, dict) and value_json.get("level") == "MD":
                lord = value_json.get("lord") or value_json.get("dasha_lord")
                start_str = value_json.get("start") or value_json.get("start_date")
                if lord and start_str:
                    try:
                        md_start = date.fromisoformat(start_str[:10])
                        md_periods.append((lord, md_start))
                    except ValueError:
                        pass

        if md_periods:
            # Return the earliest MD as epoch
            md_periods.sort(key=lambda x: x[1])
            return md_periods[0]

        # Fallback: compute from Moon longitude in planet rows
        cur.execute("""
            SELECT value_json
            FROM chart_facts
            WHERE category = 'planet'
              AND divisional_chart = 'D1'
              AND is_stale = false
              AND (fact_id ILIKE '%MOON%' OR value_json->>'planet' ILIKE 'Moon')
            LIMIT 1
        """)
        moon_row = cur.fetchone()
        if moon_row and moon_row[0]:
            moon_json = moon_row[0]
            abs_long = moon_json.get("abs_longitude") or moon_json.get("absolute_longitude")
            if abs_long:
                return _compute_epoch_from_moon_longitude(float(abs_long))

        raise RuntimeError(
            "Cannot determine dasha epoch: neither MD periods nor Moon longitude "
            "found in chart_facts. Run chart_facts ETL before this endpoint."
        )
    finally:
        conn.close()


def _compute_epoch_from_moon_longitude(moon_abs_long: float) -> tuple[str, date]:
    """
    Given Moon's absolute sidereal longitude, determine the Vimshottari
    dasha balance at birth and return (first_lord, adjusted_start_date).

    Uttara Bhadrapada spans 306°40' to 320°00' sidereal (Saturn-ruled).
    Revati spans 320°00' to 333°20' sidereal (Mercury-ruled).
    Ashwini spans 333°20' to 346°40' sidereal (Ketu-ruled).
    Bharani spans 346°40' to 360°00' / 0°00' sidereal (Venus-ruled).
    ... each nakshatra = 13°20' = 800' of arc.

    Moon longitude 306°40' to 320°00' = Saturn-ruled.
    For native (Uttara Bhadrapada): Saturn-ruled.
    """
    # Each nakshatra = 360/27 = 13.333... degrees
    NAK_SPAN = 360.0 / 27.0
    # Nakshatra index (0-based, starting from Ashwini)
    nak_idx = int(moon_abs_long / NAK_SPAN)
    # Position within nakshatra (0.0 to 1.0)
    nak_fraction = (moon_abs_long % NAK_SPAN) / NAK_SPAN

    # Nakshatra lords in order (Ketu, Venus, Sun, Moon, Mars, Rahu, Jupiter, Saturn, Mercury — repeating)
    NAK_LORDS = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
    lord = NAK_LORDS[nak_idx % 9]
    lord_years = _lord_years(lord)

    # Balance remaining = (1 - fraction) * lord_years
    balance_years = (1.0 - nak_fraction) * lord_years
    balance_days = int(_years_to_days(balance_years))

    # Native birth date
    birth_date = date(1984, 2, 5)
    epoch_start = birth_date - timedelta(days=int(_years_to_days(lord_years)) - balance_days)

    return (lord, epoch_start)


def _find_active_at(query_date: date, start_date: date, lord: str, total_years: float, depth: int):
    """
    Recursively find the active period at depth levels.
    depth=1: MD, depth=2: AD, depth=3: PD, depth=4: SD, depth=5: PD2.
    Returns list of DashaLevel objects (length = depth).
    """
    if depth == 0:
        return []

    def sub_duration(sub_lord_years):
        return total_years * sub_lord_years / TOTAL_YEARS

    periods = _build_periods(start_date, lord, total_years, sub_duration)

    for sub_lord, p_start, p_end in periods:
        if p_start <= query_date < p_end:
            level = DashaLevel(
                lord=sub_lord,
                start=p_start.isoformat(),
                end=p_end.isoformat()
            )
            sub_years = sub_duration(_lord_years(sub_lord))
            sub_levels = _find_active_at(query_date, p_start, sub_lord, sub_years, depth - 1)
            return [level] + sub_levels

    # query_date is past the last period (shouldn't happen for 1900–2100)
    last_lord, last_start, last_end = periods[-1]
    level = DashaLevel(lord=last_lord, start=last_start.isoformat(), end=last_end.isoformat())
    sub_years = sub_duration(_lord_years(last_lord))
    sub_levels = _find_active_at(query_date, last_start, last_lord, sub_years, depth - 1)
    return [level] + sub_levels


@router.post("/dasha_chain", response_model=DashaChainResponse)
async def dasha_chain(request: DashaChainRequest):
    """Return the full 5-level Vimshottari dasha active at request.date."""
    try:
        query_date = date.fromisoformat(request.date)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid date: {request.date}")

    if not (date(1900, 1, 1) <= query_date <= date(2100, 12, 31)):
        raise HTTPException(status_code=400, detail="Date must be between 1900-01-01 and 2100-12-31")

    # Get epoch
    try:
        epoch_lord, epoch_start = _get_md_epoch(request.native_id)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    # Build full MD schedule starting from epoch
    # The full Vimshottari cycle is 120 years; build enough MDs to cover query_date
    # Start from epoch_lord and advance until we cover query_date
    md_start = epoch_start
    md_lord = epoch_lord
    seq = _sequence_from(epoch_lord)
    cycle_idx = 0

    while True:
        lord_name, lord_yrs = seq[cycle_idx % len(seq)]
        md_days = int(_years_to_days(lord_yrs))
        md_end = md_start + timedelta(days=md_days)

        if md_start <= query_date < md_end:
            # Found the active MD
            levels = _find_active_at(query_date, md_start, lord_name, float(lord_yrs), 4)
            # levels[0]=AD, [1]=PD, [2]=SD, [3]=PD2

            if len(levels) < 4:
                # Pad if needed (shouldn't happen)
                while len(levels) < 4:
                    levels.append(DashaLevel(lord="Unknown", start=query_date.isoformat(), end=query_date.isoformat()))

            return DashaChainResponse(
                native_id=request.native_id,
                query_date=request.date,
                md=DashaLevel(lord=lord_name, start=md_start.isoformat(), end=md_end.isoformat()),
                ad=levels[0],
                pd=levels[1],
                sd=levels[2],
                pd2=levels[3],
            )

        md_start = md_end
        cycle_idx += 1
        # Rotate to next lord
        md_lord = seq[cycle_idx % len(seq)][0]
        lord_yrs = seq[cycle_idx % len(seq)][1]

        if cycle_idx > 300:
            raise HTTPException(status_code=500, detail="Dasha chain computation exceeded bounds")
```

**Register in `platform/python-sidecar/main.py`:**

Find the section that imports and includes routers (look for `app.include_router`). Add:
```python
from routers import dasha_chain
app.include_router(dasha_chain.router)
```

---

### §2.2 — M2-A.4: nakshatra_pada in chart_facts planet rows

**Pre-flight finding interpretation:**
- If PF.5 shows ≥10 rows with non-NULL nakshatra_pada: AC.4 is already satisfied. Verify and
  document; skip implementation.
- If PF.5 shows 0 or <10 rows with nakshatra_pada: extend the extractor.

**Approach when extension is needed:**

In `platform/python-sidecar/pipeline/extractors/chart_facts_extractor.py`, find the section
that parses FORENSIC §2.1 (planet placements) and produces rows with `category='planet'`.

The FORENSIC §2.1 table format typically includes columns: Planet | Sign | House | Nakshatra |
Absolute Longitude | Dignity | Retrograde | etc.

**If the source has nakshatra_pada directly:** parse it and add to value_json.

**If the source has absolute longitude but not pada:** derive pada from the longitude:
```python
NAK_SPAN = 360.0 / 27.0  # 13.333... degrees
PADA_SPAN = NAK_SPAN / 4  # 3.333... degrees

def derive_pada(abs_longitude: float) -> int:
    """Derive nakshatra pada (1-4) from absolute sidereal longitude."""
    pos_in_nak = abs_longitude % NAK_SPAN
    pada = int(pos_in_nak / PADA_SPAN) + 1
    return min(pada, 4)  # guard against floating-point edge
```

Add `"nakshatra_pada": derive_pada(abs_longitude)` to the `value_json` dict for each planet row.

For Lagna (Ascendant), compute similarly from the Lagna longitude.

After extending the extractor: create or extend `platform/python-sidecar/pipeline/ingest_chart_facts.py`
(or use whatever existing re-ingest entry point the W2-R2 brief created — check `pipeline/` directory)
to re-upsert the planet category rows. Do NOT re-upsert all 795 rows; use the fact_id prefix
to target only planet rows: `WHERE fact_id LIKE 'PLN.%' OR fact_id LIKE 'LGN.%'`.

---

### §2.3 — M2-A.5: chalit dual-house verification + planet D1 patch

**Step 1 — Verify chalit_shift rows:**
From PF.6: if 9 rows exist with rashi_house + chalit_house in value_json, AC.7 is satisfied.

**Step 2 — Verify planet D1 rows have rashi_house:**
```sql
SELECT fact_id, value_json->>'rashi_house' AS rashi_house
FROM chart_facts
WHERE category = 'planet' AND divisional_chart = 'D1' AND is_stale=false;
```
If all 9 (or 10 with Lagna) rows have non-NULL rashi_house: AC.7 is satisfied.
If missing: extend the §2.1 parser to also store `"rashi_house": house_number` in value_json
for D1 planet rows. This is almost certainly already present — just confirm.

---

## §3 — Acceptance criteria

### AC.1 — Branch state
`git branch --show-current` returns `redesign/r0-foundation`.

### AC.2 — /dasha_chain endpoint registered
`grep -r "dasha_chain" platform/python-sidecar/main.py` returns non-empty.
`platform/python-sidecar/routers/dasha_chain.py` exists.

### AC.3 — /dasha_chain returns correct 5 levels for Mercury MD date
Query with `{native_id: "abhisek_mohanty", date: "2025-06-15"}` (within current Mercury MD).
Response must have:
- `md.lord == "Mercury"` (current MD — Mercury MD active since ~2023)
- `ad` field present with a valid Vimshottari lord
- `pd`, `sd`, `pd2` fields present with valid lords
- All start/end dates in ISO format, start < end, and start ≤ "2025-06-15" < end for md

Verify via: `curl -s -X POST $PYTHON_SIDECAR_URL/dasha_chain -H "Content-Type: application/json" -d '{"native_id":"abhisek_mohanty","date":"2025-06-15"}'`

Or via unit test if sidecar not accessible in test mode.

### AC.4 — /dasha_chain returns Ketu MD for 2028-01-01
Query with `{native_id: "abhisek_mohanty", date: "2028-01-01"}`.
Response must have `md.lord == "Ketu"` (Ketu MD starts 2027, ends 2034).
This validates the future-date computation and confirms Ketu (not Saturn) is the next MD.

### AC.5 — /dasha_chain handles edge dates correctly
Query with `{native_id: "abhisek_mohanty", date: "1984-02-05"}` (birth date).
Response must return a valid 5-level chain without error (no 500 or crash).
The MD at birth should be Saturn (native was born in Saturn MD balance period).

### AC.6 — Tests: ≥5 tests for dasha_chain, all passing
`platform/python-sidecar/tests/test_dasha_chain.py` contains ≥5 tests covering:
- AC.3 scenario (Mercury MD date)
- AC.4 scenario (Ketu MD date)
- AC.5 scenario (birth date)
- Invalid date handling (400 response)
- Out-of-range date handling (400 response)

All tests pass: `python -m pytest tests/test_dasha_chain.py -v`

### AC.7 — nakshatra_pada in chart_facts planet D1 rows
```sql
SELECT COUNT(*) FROM chart_facts
WHERE category = 'planet'
  AND divisional_chart = 'D1'
  AND is_stale = false
  AND value_json->>'nakshatra_pada' IS NOT NULL;
```
Expected: ≥9 (all 9 planets; Lagna counts as bonus if present).

### AC.8 — nakshatra_pada values are 1–4
```sql
SELECT DISTINCT (value_json->>'nakshatra_pada')::int AS pada
FROM chart_facts
WHERE category = 'planet' AND divisional_chart = 'D1' AND is_stale=false
  AND value_json->>'nakshatra_pada' IS NOT NULL;
```
All returned values in {1, 2, 3, 4}.

### AC.9 — chalit_shift rows present with dual-house
```sql
SELECT COUNT(*) FROM chart_facts
WHERE category = 'chalit_shift' AND is_stale=false
  AND value_json->>'rashi_house' IS NOT NULL
  AND value_json->>'chalit_house' IS NOT NULL;
```
Expected: 9.

### AC.10 — planet D1 rows have rashi_house
```sql
SELECT COUNT(*) FROM chart_facts
WHERE category = 'planet' AND divisional_chart = 'D1' AND is_stale=false
  AND value_json->>'rashi_house' IS NOT NULL;
```
Expected: ≥9.

### AC.11 — chart_facts total count preserved or higher
```sql
SELECT COUNT(*) FROM chart_facts WHERE is_stale=false;
```
Expected: ≥795 (no rows deleted by re-ingest).

### AC.12 — Sidecar tests baseline maintained
```bash
python -m pytest tests/ rag/ -q --tb=no 2>&1 | tail -5
```
Pass count ≥ pre-flight baseline. No new failures.

### AC.13 — Deploy or sidecar restart with new endpoint
If sidecar deploys to Cloud Run: new revision created. `/dasha_chain` responds 200 on a test POST.
If sidecar is tested locally only (no deploy in this session): document "sidecar not redeployed;
dasha_chain available on next full deploy" in closing summary.

---

## §4 — Halt conditions

Halt immediately and emit a 5-line halt summary if:

1. **PF.1 fails:** Branch is not `redesign/r0-foundation`. Do not proceed.
2. **PF.3 fails:** Auth Proxy unreachable after 30s retry. Cannot run SQL verification.
3. **Dasha computation produces wrong MD for known date:** If `{date: "2024-01-01"}` does not
   return `md.lord == "Mercury"` (Mercury MD is confirmed current), the epoch derivation is wrong.
   Halt and report the epoch values you computed.
4. **AC.7 fails:** After extractor extension and re-ingest, nakshatra_pada is still NULL in
   planet rows. Halt and report what the FORENSIC source contains for §2.1.
5. **Test count regression > 5 new failures:** Halt before deploy.
6. **Chart_facts count drops below 790:** Something went wrong in the re-ingest. Halt and report.

Non-halting issues (document in closing summary, continue):
- sidecar not redeployable in this session (test locally, note for next deploy)
- nakshatra_pada already present from a prior run (AC.7 pre-satisfied — document and skip extension)
- chalit_shift 9 rows already correct (AC.9 pre-satisfied)

---

## §5 — Closing summary template

Emit this at the end of the session:

```
SESSION CLOSE — M2_A_MINOR — <ISO timestamp>

ACs result:
  AC.1:  <PASS|FAIL> — branch check
  AC.2:  <PASS|FAIL> — /dasha_chain registered
  AC.3:  <PASS|FAIL> — Mercury MD correct for 2025-06-15
  AC.4:  <PASS|FAIL> — Ketu MD correct for 2028-01-01
  AC.5:  <PASS|FAIL> — birth date handled without crash
  AC.6:  <PASS|FAIL> — ≥5 tests passing
  AC.7:  <PASS|FAIL> — nakshatra_pada in ≥9 planet D1 rows
  AC.8:  <PASS|FAIL> — pada values ∈ {1,2,3,4}
  AC.9:  <PASS|FAIL> — 9 chalit_shift rows with dual-house
  AC.10: <PASS|FAIL> — ≥9 planet D1 rows with rashi_house
  AC.11: <PASS|FAIL> — chart_facts count ≥ 795
  AC.12: <PASS|FAIL> — sidecar tests baseline maintained
  AC.13: <PASS|SKIP> — sidecar deploy (SKIP if local-only session)

Files created/modified:
  <path>: <one-line change>

DB changes:
  chart_facts: 795 → <count after> (planet rows re-upserted with nakshatra_pada)

Cloud Run: <revision or "not redeployed this session">

Tests:
  Before: <X passed / Y failed>
  After: <X' passed / Y' failed>
  Delta: <new failures, expected 0>

Halt-and-report cases: <none | description>

Brief status: <COMPLETE | HALTED_AT_AC.N>
Next brief in stream: M2_C5_TEMPORAL_EXTENSION (W5-R1 — depends on this session)
```

After emitting the closing summary, append a session entry to
`00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md` per protocol §3.1, and flip
`status: COMPLETE` in this brief's frontmatter.

---

*End of CLAUDECODE_BRIEF_M2_A_MINOR v1.0 (authored 2026-04-30 — Wave 3 close).*
