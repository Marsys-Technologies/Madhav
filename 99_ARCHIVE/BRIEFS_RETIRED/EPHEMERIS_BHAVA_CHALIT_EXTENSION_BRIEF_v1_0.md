---
canonical_id: EPHEMERIS_BHAVA_CHALIT_EXTENSION_BRIEF
version: 1.0
status: AUTHORED_READY_TO_EXECUTE
authored_on: 2026-05-19
category: phase-4-followup
closes: Phase 4 locked decision §6.6 deferral
estimated_sessions: 1-2 (medium)
two_stream_branch: feat/ephemeris-bhava-chalit
depends_on: §4.B Path A rebuild (660,726 ephemeris_daily rows MEAN_NODE-anchored, derived columns populated)
---

# Ephemeris Bhava-Chalit Extension — Sripati Cusps on `ephemeris_daily`

## §1 Scope

Phase 4 §6.6 locked decision: "House systems = add Whole-Sign as peer; keep Placidus where wired; **defer Bhava-Chalit**." This brief closes that deferral.

What ships:

1. **Migration `061_ephemeris_bhava_chalit.sql`** — adds one nullable column to `ephemeris_daily` + `ephemeris_daily_staging`: `bhava_chalit_house SMALLINT` (values 1–12).
2. **Pure-Python derivation** in `ephemeris_derivations.py` — `compute_bhava_chalit_house(planet_lon, cusps_array)`. Takes the 12 natal Sripati cusps + a transit-planet longitude; returns 1–12 using the cusps-as-midpoint convention (Bhava N spans the half-arc around cusps[N]).
3. **Natal-cusp computation** in `bootstrap_ephemeris.py` — once per script run, compute the 12 Sripati cusps for the native via `swe.houses_ex(jd_birth, lat, lon, b'S', FLG_SIDEREAL)`. Cache the array. For each daily row, apply `compute_bhava_chalit_house` to the planet's longitude.
4. **Backfill in `enrich_ephemeris_daily.py`** — mirror update so existing rows can be patched without a full rebuild.
5. **Surface in `query_ephemeris.ts`** — extend response shape with `bhava_chalit_house`; add `'house_bc'` to the `derived_fields` enum.
6. **RCS update** — `retrieval_capability_spec.ts` query_ephemeris entry mentions Bhava-Chalit as a peer of Whole-Sign house.
7. **Synthesis prompt note** in `shared.ts DIVISIONAL_INTEGRATION_GATE` — instruct synthesis to consult BOTH house systems for sandhi planets (within 3° of a sign boundary).
8. **~8 Python unit tests** on `compute_bhava_chalit_house` (sandhi cases, native birthday spot-check) + ~2 TS tests on `query_ephemeris` response shape.
9. **Runbook §6 addendum** — operator backfill steps via `enrich_ephemeris_daily.py`.

## §2 What you must NOT do

- **No branch other than `feat/ephemeris-bhava-chalit`**.
- **No Chat V2 files**.
- **No autonomous `npm run answer:eval`**.
- **No autonomous full ephemeris rebuild** — backfill via the enrich script is sufficient since Bhava-Chalit is a pure function of existing `longitude_deg` + the natal Sripati cusps. Full rebuild not required.
- **Do not change** the existing `whole_sign_house` column or its semantics — Whole-Sign and Bhava-Chalit coexist as peer surfaces.
- **No multi-native generalization** — single-native mode (Aries lagna, Bhubaneswar observer) is the only supported config. M7 multi-native extension is out of scope per project policy.

## §3 Approved discipline (re-stated from Phase 4 §6)

1. **Sripati cusps via `swe.houses_ex(jd_birth, lat, lon, b'S', FLG_SIDEREAL)`** — Lahiri sidereal, Sripati house system code 'S'.
2. **Cusps-as-midpoint convention**: Bhava N is the half-arc-band centered on cusps[N]. Bhava N's range = `[midpoint(cusps[N-1], cusps[N]) .. midpoint(cusps[N], cusps[N+1]))` modulo 360°.
3. **Native lagna = Aries 12°23′55″** (per FORENSIC `MET.LAGNA.SIGN`). The 12 cusps for this native at birth time will cluster around the canonical Aries-lagna bhava-midpoints with corrections for Bhubaneswar latitude (20.27°N).
4. **Observer**: Bhubaneswar (20.27021°N, 85.82966°E, alt 45m) — same as §4.C panchanga.
5. **Birth moment** for natal cusp computation: 1984-02-05T10:43:00+05:30 IST (= 1984-02-05T05:13:00 UTC).

## §4 Files to create / modify

### §4.1 New file — `platform/migrations/061_ephemeris_bhava_chalit.sql`

```sql
-- Phase 4 §6.6 follow-up: Bhava-Chalit (Sripati cusp) house position on ephemeris_daily.
-- Single-native mode: bhava_chalit_house is anchored to native birth chart's
-- Sripati cusps computed once at bootstrap_ephemeris start. M7 multi-native
-- extension will require either per-native column duplication or query-time
-- on-the-fly computation against per-native cusps.
--
-- The column complements (does NOT replace) whole_sign_house from §4.B.
-- Whole-Sign and Bhava-Chalit are peer surfaces; senior acharyas consult
-- both, especially for sandhi (sign-boundary) planets.
BEGIN;

ALTER TABLE ephemeris_daily
  ADD COLUMN IF NOT EXISTS bhava_chalit_house SMALLINT;  -- 1..12

ALTER TABLE ephemeris_daily_staging
  ADD COLUMN IF NOT EXISTS bhava_chalit_house SMALLINT;

CREATE INDEX IF NOT EXISTS idx_ephemeris_bhava_chalit
  ON ephemeris_daily(planet, bhava_chalit_house, date);

COMMIT;
```

### §4.2 Extend — `platform/python-sidecar/pipeline/ephemeris_derivations.py`

Add at the end of the existing file (after `compute_graha_yuddha`):

```python
# ── Bhava-Chalit (Sripati cusps) — Phase 4 §6.6 follow-up ─────────────────────
#
# Sripati cusps are computed once at chart birth via Swiss Ephemeris's houses_ex
# function with house system code 'S'. The 12 cusps are FIXED for the native
# chart (they do not change with transit time — they're properties of the
# birth moment + observer). For a transit-planet longitude L, the Bhava-Chalit
# house is determined by which cusp-midpoint band L falls into.
#
# Convention: cusps[N] is the MIDPOINT of bhava N (Sripati tradition). Bhava N
# spans the half-arc band centered on cusps[N]:
#   boundary_start_N = midpoint(cusps[N-1], cusps[N])
#   boundary_end_N   = midpoint(cusps[N], cusps[N+1])
#
# This differs from the Whole-Sign convention (where each sign IS a house) and
# from the Equal-house convention (where each house is exactly 30°). For the
# native's Aries lagna at 12°23'55", Whole-Sign and Bhava-Chalit will mostly
# agree for non-sandhi planets but diverge at sign boundaries.

def midpoint_arc(a: float, b: float) -> float:
    """Shortest-arc midpoint between two longitudes (degrees, 0-360)."""
    a = a % 360.0
    b = b % 360.0
    diff = (b - a) % 360.0
    if diff > 180.0:
        diff -= 360.0
    return (a + diff / 2.0) % 360.0


def compute_bhava_chalit_house(planet_lon: float, cusps: list[float]) -> int:
    """
    Return the Bhava-Chalit house (1..12) for a planet at planet_lon, given
    the native's 12 natal Sripati cusps.

    `cusps` is a length-12 list where cusps[i] is the midpoint of bhava i+1
    (i.e., cusps[0] is the midpoint of the 1st bhava ≈ ascendant degree).

    Sripati convention: bhava N spans the half-arc band centered on cusps[N-1].
    """
    if len(cusps) != 12:
        raise ValueError(f"compute_bhava_chalit_house: expected 12 cusps, got {len(cusps)}")

    planet_lon = planet_lon % 360.0
    # Compute the 12 boundary points: between consecutive cusp midpoints
    boundaries = [midpoint_arc(cusps[i], cusps[(i + 1) % 12]) for i in range(12)]

    # bhava N starts at boundaries[N-1] and ends at boundaries[N] (mod 12).
    # i.e., bhava 1 spans boundaries[11] → boundaries[0] (the band centered on cusps[0]).
    for n in range(12):
        start = boundaries[(n - 1) % 12]
        end = boundaries[n]
        if _in_arc(planet_lon, start, end):
            return n + 1

    raise RuntimeError(f"compute_bhava_chalit_house: longitude {planet_lon} did not match any bhava — cusps={cusps}")


def _in_arc(lon: float, start: float, end: float) -> bool:
    """True if lon lies in the arc from start to end going forward (mod 360)."""
    lon = lon % 360.0
    start = start % 360.0
    end = end % 360.0
    if start <= end:
        return start <= lon < end
    return lon >= start or lon < end
```

### §4.3 Extend — `platform/python-sidecar/pipeline/bootstrap_ephemeris.py`

Add a one-time Sripati-cusp computation at the start of `run()`:

```python
# Around the existing _init_swe() call, after Lahiri mode is set:
def _compute_native_sripati_cusps(swe) -> list[float]:
    """
    Compute the 12 Sripati cusps for the native chart, once at script start.
    Returns a length-12 array where index i is the midpoint of bhava i+1.

    Native: 1984-02-05T10:43:00+05:30 IST (= 05:13:00 UTC), Bhubaneswar.
    """
    NATIVE_BIRTH_JD_UT = swe.julday(1984, 2, 5, 5 + 13/60)  # 05:13:00 UTC
    NATIVE_LAT = 20.27021   # Bhubaneswar
    NATIVE_LON = 85.82966
    cusps, ascmc = swe.houses_ex(
        NATIVE_BIRTH_JD_UT,
        NATIVE_LAT,
        NATIVE_LON,
        b'S',  # Sripati
        swe.FLG_SIDEREAL,
    )
    # cusps is a 13-element tuple; cusps[1] through cusps[12] are the 12 bhava cusps.
    # We return them as a Python list of length 12 (index 0 = bhava 1 midpoint).
    return [cusps[i] for i in range(1, 13)]


# In run() or _compute_day(), pass the cusps array through and apply:
from .ephemeris_derivations import compute_bhava_chalit_house

# When building the per-planet derived dict, add:
bhava_chalit = compute_bhava_chalit_house(planet_lon, native_sripati_cusps)
row['bhava_chalit_house'] = bhava_chalit
```

The `_UPSERT_SQL` constant needs to be extended to include `bhava_chalit_house`:

```python
_UPSERT_SQL = """
INSERT INTO ephemeris_daily_staging (
    date, planet, longitude_deg, latitude_deg, speed_deg_per_day,
    is_retrograde, sign, sign_degree, nakshatra, nakshatra_pada,
    ayanamsha, ephemeris_version, build_id,
    -- §4.B derived columns
    dignity_d1, is_combust, combust_orb_deg, vargottama_today,
    sign_ingress_today, whole_sign_house, graha_yuddha_with,
    -- §6.6 follow-up: Bhava-Chalit
    bhava_chalit_house
) VALUES (...)
ON CONFLICT (date, planet) DO UPDATE SET
    ...
    bhava_chalit_house = EXCLUDED.bhava_chalit_house;
"""
```

### §4.4 Extend — `platform/python-sidecar/pipeline/enrich_ephemeris_daily.py`

The enrich script becomes the canonical backfill path. Logic:

1. Compute Sripati cusps once at script start (same `_compute_native_sripati_cusps` helper).
2. SELECT all rows where `bhava_chalit_house IS NULL` — filter by `is_stale=false` if applicable.
3. For each row, apply `compute_bhava_chalit_house(longitude_deg, native_sripati_cusps)`.
4. UPDATE the row.

```python
def backfill_bhava_chalit(db_url: str, batch_size: int = 5000, dry_run: bool = False) -> int:
    """Backfill bhava_chalit_house for all ephemeris_daily rows where it is NULL."""
    swe = _init_swe()
    cusps = _compute_native_sripati_cusps(swe)
    logger.info("Sripati cusps for native (Aries lagna, Bhubaneswar): %s", cusps)

    import psycopg2
    import psycopg2.extras
    conn = psycopg2.connect(db_url)
    conn.autocommit = False

    total = 0
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT id, longitude_deg
            FROM ephemeris_daily
            WHERE bhava_chalit_house IS NULL
            ORDER BY id
        """)
        rows = cur.fetchall()

    logger.info("Backfilling %d rows", len(rows))

    updates = []
    for r in rows:
        bhava = compute_bhava_chalit_house(float(r['longitude_deg']), cusps)
        updates.append({'id': r['id'], 'bhava': bhava})
        if len(updates) >= batch_size:
            total += _flush_bhava_updates(conn, updates, dry_run)
            updates = []
    total += _flush_bhava_updates(conn, updates, dry_run)

    conn.close()
    return total
```

Add a CLI flag `--backfill-bhava-chalit` so the operator can invoke this independently.

### §4.5 Extend — `platform/src/lib/retrieve/query_ephemeris.ts`

Add `'house_bc'` to the `derived_fields` enum + include `bhava_chalit_house` in the SELECT + response shape:

```ts
export interface QueryEphemerisInput {
  // ... existing fields ...
  derived_fields?: ('dignity' | 'combust' | 'vargottama' | 'ingress' | 'yuddha' | 'house' | 'house_bc')[]
}
```

Update the SELECT to include `bhava_chalit_house`. Update the response-shaping logic so `house_bc` (or default-include-all) surfaces it. When `derived_fields` is omitted, both `house` (Whole-Sign) and `house_bc` (Bhava-Chalit) are returned by default.

### §4.6 Update — `platform/src/lib/router/retrieval_capability_spec.ts`

Edit the `query_ephemeris` RCS entry's description + optimal_patterns + supported_params to mention Bhava-Chalit:

```ts
description: '... AND derived state: dignity, combust, vargottama, sign-ingress, ' +
  'whole-sign-house (anchored to native lagna = Aries — Parashari/Vedic default), ' +
  'bhava-chalit-house (Sripati-cusp-based — angular bhava for sandhi-planet ' +
  'refinement; consult alongside whole-sign for planets within 3° of a sign boundary), ' +
  'graha-yuddha. ...',
supported_params:
  '... derived_fields?: ("dignity"|"combust"|"vargottama"|"ingress"|"yuddha"|"house"|"house_bc")[] ' +
  '(default ALL — empty array opts out) ...',
optimal_patterns: [
  // ... existing patterns ...
  'Bhava-Chalit check for a sandhi planet: {date:"2018-06-15", planet:"Saturn", derived_fields:["house","house_bc"]} (compare whole_sign_house vs bhava_chalit_house — if they differ, the planet is in sandhi)',
],
```

### §4.7 Synthesis prompt note — `platform/src/lib/prompts/templates/shared.ts`

Small addition to the existing `DIVISIONAL_INTEGRATION_GATE`. Find the section discussing house systems and append:

```
For planets within 3° of a sign boundary (sandhi planets), the bundle now
surfaces BOTH whole_sign_house (Parashari) and bhava_chalit_house (Sripati)
in the query_ephemeris result. When the two values DIFFER, name this
explicitly in the response — sandhi planets are read differently by the
two conventions, and the cross-check belongs in the synthesis surface
("Saturn at Aries 28° sits in the 1st by Whole-Sign but the 2nd by
Bhava-Chalit; for predictive timing of the Saturn signification, the
Bhava-Chalit reading takes precedence as the angular bhava is closer
to its true sign-boundary moment.").

If only one house value is present (e.g., for backfilled rows where
Bhava-Chalit is null), proceed with the available value and note the
absence:  [BHAVA_CHALIT_NOT_BACKFILLED for date <D>, planet <P>;
default to whole_sign_house only].
```

### §4.8 Tests — `platform/python-sidecar/pipeline/__tests__/test_ephemeris_derivations.py`

Add ~8 new tests for `compute_bhava_chalit_house`:

1. `test_bhava_chalit_planet_at_ascendant_degree_is_house_1` — planet at cusps[0] → bhava 1
2. `test_bhava_chalit_planet_one_degree_after_ascendant_is_house_1` — small offset still in 1st
3. `test_bhava_chalit_planet_at_midpoint_to_2nd_is_house_2` — exact half-arc boundary edge case
4. `test_bhava_chalit_planet_at_descendant_is_house_7` — opposite ascendant
5. `test_bhava_chalit_wraps_around_360_at_12_to_1` — boundary crossing 0°/360°
6. `test_bhava_chalit_handles_lon_350_with_asc_5deg` — wraparound case
7. `test_bhava_chalit_native_birthday_saturn_spot_check` — for 1984-02-05, Saturn at sidereal Libra ~22° → expect bhava 7 (Saturn opposite Aries lagna)
8. `test_midpoint_arc_handles_wraparound` — helper function unit test (a=350, b=10 → midpoint 0)
9. `test_compute_bhava_chalit_raises_on_wrong_cusp_count` — input validation

Add 2 TS tests in `query_ephemeris.test.ts` asserting `bhava_chalit_house` appears in response when present + `house_bc` in derived_fields filters correctly.

### §4.9 Runbook §6 addendum — `00_ARCHITECTURE/RUNBOOK_EPHEMERIS_REBUILD_v1_0.md`

Add a new section §6 documenting the Bhava-Chalit backfill:

```markdown
## §6 Bhava-Chalit Backfill (Phase 4 §6.6 follow-up)

After migration 061 lands, the `bhava_chalit_house` column is added to
ephemeris_daily (nullable, IF NOT EXISTS). Backfill via the enrich script
takes ~5-10 min for 660K rows (pure-Python derivation, no Swiss Ephemeris
recompute — just SELECT + UPDATE).

### Steps

1. Apply migration 061:
   ```bash
   psql "$DATABASE_URL" -f platform/migrations/061_ephemeris_bhava_chalit.sql
   ```

2. Run the backfill (idempotent — only patches rows where bhava_chalit_house IS NULL):
   ```bash
   cd platform/python-sidecar
   python -m pipeline.enrich_ephemeris_daily --backfill-bhava-chalit
   ```

3. Verify completeness:
   ```sql
   SELECT COUNT(*) AS total,
          COUNT(*) FILTER (WHERE bhava_chalit_house IS NULL) AS still_null
   FROM ephemeris_daily;
   -- Expect: still_null = 0
   ```

4. Spot-check native birth day (1984-02-05). For Aries lagna at 12°23'55",
   Saturn at Libra ~22° (opposite ascendant) should be in bhava 7:
   ```sql
   SELECT date, planet, longitude_deg, sign, whole_sign_house, bhava_chalit_house
   FROM ephemeris_daily
   WHERE date = '1984-02-05' AND planet IN ('saturn','sun','moon','mars')
   ORDER BY planet;
   -- Expected: Saturn whole_sign_house=7, bhava_chalit_house=7 (close to ascendant axis)
   ```

### Rollback

```sql
UPDATE ephemeris_daily SET bhava_chalit_house = NULL;
-- Or to drop the column entirely:
ALTER TABLE ephemeris_daily DROP COLUMN bhava_chalit_house;
ALTER TABLE ephemeris_daily_staging DROP COLUMN bhava_chalit_house;
```
```

## §5 Verification gates (pre-commit, NOT post-deploy)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-bhava-chalit/platform

# G1: TypeScript compiles
npx tsc --noEmit

# G2: TS unit tests
npx vitest run src/lib/retrieve/__tests__/query_ephemeris.test.ts
npx vitest run src/lib/

# G3: Python derivation tests
cd python-sidecar
python -m pytest pipeline/__tests__/test_ephemeris_derivations.py -v
cd ..

# G4: planner_regression_gate (small RCS update — should not regress planner output)
npx vitest run tests/eval/planner_regression_gate.test.ts
```

All 4 gates green before commit. Migration syntax check is REVIEW-ONLY (no autonomous DB apply).

## §6 Commit + PR

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-bhava-chalit

git add platform/migrations/061_ephemeris_bhava_chalit.sql \
        platform/python-sidecar/pipeline/ephemeris_derivations.py \
        platform/python-sidecar/pipeline/bootstrap_ephemeris.py \
        platform/python-sidecar/pipeline/enrich_ephemeris_daily.py \
        platform/python-sidecar/pipeline/__tests__/test_ephemeris_derivations.py \
        platform/src/lib/retrieve/query_ephemeris.ts \
        platform/src/lib/retrieve/__tests__/query_ephemeris.test.ts \
        platform/src/lib/router/retrieval_capability_spec.ts \
        platform/src/lib/prompts/templates/shared.ts \
        00_ARCHITECTURE/RUNBOOK_EPHEMERIS_REBUILD_v1_0.md

git commit -m "feat(ephemeris): Bhava-Chalit (Sripati cusp) house surface (Phase 4 §6.6 follow-up)

Closes the Phase 4 locked-decision §6.6 deferral. Adds Bhava-Chalit
(Sripati-cusp) house position as a peer to whole_sign_house from §4.B.
Senior Vedic acharyas consult both house systems — Whole-Sign for the
classical Parashari read, Bhava-Chalit for angular-bhava refinement on
sandhi (sign-boundary) planets.

Migration 061: adds bhava_chalit_house SMALLINT column (nullable) to
ephemeris_daily + ephemeris_daily_staging, plus a targeted index for
(planet, bhava_chalit_house, date) queries.

Pure-Python derivation in ephemeris_derivations.py:
  - compute_bhava_chalit_house(planet_lon, cusps_array) — Sripati
    cusps-as-midpoint convention; Bhava N spans the half-arc band
    centered on cusps[N-1]
  - midpoint_arc + _in_arc helpers handle 360°-wraparound correctly

bootstrap_ephemeris.py: computes 12 Sripati cusps once at script start
via swe.houses_ex(jd_birth, lat, lon, b'S', FLG_SIDEREAL) for the native
(1984-02-05T05:13:00 UTC, Bhubaneswar 20.27N 85.83E). Cusps cached;
per-row apply.

enrich_ephemeris_daily.py: new --backfill-bhava-chalit mode patches
existing rows where bhava_chalit_house IS NULL. Pure-Python derivation,
no Swiss Ephemeris recompute — ~5-10 min for 660K rows.

query_ephemeris.ts: derived_fields enum extended with 'house_bc'; response
shape includes bhava_chalit_house. Default empty derived_fields returns
both whole_sign_house and bhava_chalit_house — synthesis can compare.

RCS entry rewritten to advertise Bhava-Chalit as peer surface.
DIVISIONAL_INTEGRATION_GATE in shared.ts gets a sandhi-planet note
instructing synthesis to surface both house values explicitly when
they differ.

Test coverage: 8 Python unit tests + 2 TS tests + spot-check for native
birth day (Saturn opposite Aries lagna → bhava 7 in both systems).

Production rebuild: code + migration + runbook ship in this commit. The
~5-10 min backfill is deferred to operator per RUNBOOK §6. Full
ephemeris rebuild is NOT required — Bhava-Chalit is pure function of
existing longitude + natal cusps, so the enrich-only path is sufficient.

Single-native mode: bhava_chalit_house is anchored to native lagna +
Bhubaneswar Sripati cusps. M7 multi-native extension is out of scope
per project policy.

Refs: 00_ARCHITECTURE/briefs/EPHEMERIS_BHAVA_CHALIT_EXTENSION_BRIEF_v1_0.md
Closes: Phase 4 locked-decision §6.6 deferral"

git push origin feat/ephemeris-bhava-chalit

gh pr create \
  --base main \
  --head feat/ephemeris-bhava-chalit \
  --title "feat(ephemeris): Bhava-Chalit (Sripati cusp) house surface (Phase 4 §6.6 follow-up)" \
  --body "Closes the Phase 4 locked-decision §6.6 deferral. Adds Bhava-Chalit alongside Whole-Sign as a peer house surface.

Migration 061 + ephemeris_derivations extension + bootstrap update + enrich-script backfill + query_ephemeris response shape + RCS update + synthesis-prompt sandhi-planet note + 10 tests + RUNBOOK §6.

Production backfill via enrich script: ~5-10 min. Full ephemeris rebuild NOT required.

Single-native mode (Aries lagna, Bhubaneswar). M7 multi-native deferred.

Refs: 00_ARCHITECTURE/briefs/EPHEMERIS_BHAVA_CHALIT_EXTENSION_BRIEF_v1_0.md"

gh pr merge feat/ephemeris-bhava-chalit --merge --auto
```

## §7 Acceptance criteria

- [ ] Migration 061 created with column + index + transaction guard
- [ ] `compute_bhava_chalit_house` + `midpoint_arc` + `_in_arc` ship in `ephemeris_derivations.py`
- [ ] `bootstrap_ephemeris.py` computes Sripati cusps once + applies per-row; `_UPSERT_SQL` extended
- [ ] `enrich_ephemeris_daily.py` has `--backfill-bhava-chalit` mode; idempotent on NULL rows
- [ ] `query_ephemeris.ts` extended with `house_bc` enum + response shape
- [ ] RCS `query_ephemeris` entry rewritten with Bhava-Chalit advertisement + optimal_patterns
- [ ] `DIVISIONAL_INTEGRATION_GATE` in shared.ts gets the sandhi-planet note
- [ ] 8 Python unit tests pass; 2 TS tests pass
- [ ] `tsc --noEmit` clean
- [ ] Full src/lib/ regression green
- [ ] `planner_regression_gate` green
- [ ] Runbook §6 addendum authored
- [ ] Commit lands on `feat/ephemeris-bhava-chalit`; PR opened + auto-merge
- [ ] No Chat V2 files; no autonomous DB apply or rebuild

## §8 Report back

When complete:

1. Closing commit SHA + `git log --oneline -3` on the feat branch.
2. PR URL + merge status.
3. Test counts.
4. The 12 Sripati cusps the script computed for the native (sanity check — these are project-defining values for the rest of the chart's life, so worth printing once and recording).
5. Recommendation on the operator backfill: run via Cloud SQL proxy session, or trigger via a one-shot Cloud Run job?
6. Any surprises (e.g., cusp-midpoint convention edge case I missed).

I'll then record the close in memory + flag the Phase 4 §6.6 deferral as resolved.
