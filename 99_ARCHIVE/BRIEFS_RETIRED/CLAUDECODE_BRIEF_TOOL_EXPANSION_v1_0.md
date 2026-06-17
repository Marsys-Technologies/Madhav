---
canonical_id: CLAUDECODE_BRIEF_TOOL_EXPANSION
version: 1.0
status: READY
authored: 2026-05-27
description: >
  Three-workstream expansion of the MARSYS-JIS MCP server. Based on original
  design document audited and corrected against actual codebase state.
  A: Register 17 ready-but-unregistered tools (40→57). B: Implement three
  sidecar stub endpoints (/sade_sati, /retrogrades, /eclipses). C: KP
  discrepancy investigation only.
---

# MARSYS-JIS Tool Expansion — Claude Code Brief
## Three Workstreams: Tool Registration · Sidecar Stubs · KP Investigation

---

## §0 — AUDIT: What the original design document got wrong

Before implementing anything, read these corrections. They supersede the original
design document in every case of conflict.

### FATAL ERROR 1 — msr_sql and query_signals are NOT the same tool

The original document claims "`query_signals` was a ghost alias for `msr_sql`"
and proposes renaming `msr_sql` to `query_signals`. **This is wrong.**
They are two distinct tools with different purposes:

- **`msr_sql`** (`tools/msr_sql.ts`) — raw SQL query, chart_id UUID scoping,
  `signal_type` array filter, `forward_looking`, `confidence_floor`, `valence` array,
  `dasha_activation` array, `entities_involved_any`. No calibration applied.
- **`query_signals`** (`tools/query_signals.ts`) — applies LL.1 calibration weights,
  Pancha-Mahapurusha clique dedup, domain-specific confidence floors. Has `planet`,
  `dasha_lord`, `valence` enum, `temporal_activation` enum, `min_confidence`.

Both are registered in `server.ts` and must remain. **Do NOT remove or rename either.**
Workstream C Task C1 from the original document is CANCELLED.

### FATAL ERROR 2 — flag_disagreement inputSchema is completely wrong

The original document says the inputSchema is:
`{tool_name, expected_value, actual_value, context}`

**The actual schema** (from `tools/flag_disagreement.ts`) is:
```typescript
{
  class: enum('factual' | 'interpretive' | 'structural' | 'mirror_desync' |
               'scope' | 'output_conflict' | 'version_disagreement' |
               'scope_disagreement' | 'closure_disagreement' |
               'l3_zero_supports' | 'panel_divergence' | 'school_disagreement' |
               'acceptance_rate_anomaly'),
  description: string,      // required
  source_session: string,   // required
  proposed_resolution: string  // optional
}
```
Do NOT modify this schema. The description block in the manifest must match it.

### ERROR 3 — Tool count is 40 registered, not 38

`server.ts` currently registers **40 tools**. `catalog.ts` declares **57 tools**,
meaning **17 tools have complete handler files and descriptions but are NOT yet
registered in server.ts**. Workstream A is to close this gap, not to create a
manifest.json and refactor server.ts to load tools dynamically.

### ERROR 4 — Dynamic manifest loading is unnecessary and risky

The original document proposes refactoring `server.ts` to load tools dynamically
from a `manifest.json` at startup. The server already has `catalog.ts` +
`tier_catalog.ts` for exactly this purpose. **Do NOT touch the server.ts boot path.**
Workstream A is a targeted `server.ts` import + registration addition only.

### ERROR 5 — Python pipeline scripts already exist

The original document proposes writing three new standalone Python pipeline scripts.
In reality:
- `/platform/scripts/data/populate_sade_sati.py` **already exists**
- `platform/python-sidecar/pipeline/ingest_eclipses_retrogrades.py` **already exists**
  (loads `ECLIPSES_1900_2100.csv` + `RETROGRADES_1900_2100.csv` from GCS)
- The sidecar routers for `/sade_sati`, `/retrogrades`, `/eclipses` are **stub files**
  returning `{"status": "not_implemented"}`

**Workstream B is: implement those three stub router files** to read from the DB tables
that already have data. No new standalone scripts needed.

### ERROR 6 — query_kp_ruling_planets must NOT be decommissioned

The original C2 task says to retire `query_kp_ruling_planets` as "conflicting." The
tool's own header comment explicitly states both tools **coexist by design**:
- `kp_query` → FORENSIC-anchored authoritative values from `chart_facts`
- `query_kp_ruling_planets` → swisseph-Lahiri computed `kp_sublords`, useful for
  non-FORENSIC charts and forward-looking transit-time KP queries

The discrepancy (Saturn sub_sub_lord Venus vs Ketu) is a real data discrepancy to
investigate (see Workstream C), but **do NOT remove or hide the tool.**

### ERROR 7 — domain is a free string, not an enum

The original document lists `domain` enum as
`dharma|artha|kama|moksha|health|relationships|finance|spirituality|timing`.
Both `query_signals` and `msr_sql` accept `domain` as a free string.
Real domain values in the corpus: `career`, `health`, `relationships`, `spiritual`,
`wealth`, `finance`.

---

## §1 — Codebase orientation (read before touching anything)

**Paths:**
```
platform-mcp/src/server.ts           ← MCP server, 40 tools registered
platform-mcp/src/tools/              ← 61 .ts handler files (17 not yet in server.ts)
platform-mcp/src/tools/catalog.ts    ← CATALOG array, 57 entries (source of truth for names)
platform/python-sidecar/main.py      ← FastAPI sidecar, 40 routers
platform/python-sidecar/routers/     ← one .py per endpoint
platform/python-sidecar/pipeline/    ← batch data pipeline scripts
platform/scripts/data/               ← existing standalone data scripts
```

**Key rule:** The 17 unregistered tools are listed in `catalog.ts` but NOT in `server.ts`.
To find exactly which ones: compare `CATALOG` entries against `server.ts` import list.
The gap is:
```
tara_balam_for_native        chandra_balam_for_native
query_transits_over_natal    query_yogas_active_now
interpret_current_dasha      list_canonical_artifact_versions
query_jaimini_chara_dasha    query_planetary_period_predictions
query_eclipse_transits       query_planet_war
list_assets                  get_planet_avastha
get_shadbala_full            query_drekkana_drishti
query_dasamsha_career        query_shashtiamsha
query_remedies_prescribed
```

---

## §2 — Branch and worktree

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
git worktree add ../MadhavToolExpansion feature/tool-expansion 2>/dev/null || \
  git worktree add ../MadhavToolExpansion -b feature/tool-expansion
cd ../MadhavToolExpansion
```

All work in `/Users/Dev/Vibe-Coding/Apps/MadhavToolExpansion`.

---

## WORKSTREAM A — Register the 17 unregistered tools in server.ts

### Goal

The 17 tools listed in §1 have complete handler files and descriptions already in
`catalog.ts`. They just need to be wired into `server.ts`. Bringing the count
from 40 → 57 matches what `catalog.ts` already declares.

### Step A.1 — Verify each handler compiles and registers correctly

Before editing `server.ts`, for each of the 17 files, confirm:
1. The file exists in `platform-mcp/src/tools/`
2. It exports a `register*` function (grep `export function register`)
3. It has an entry in `catalog.ts` CATALOG array

Run:
```bash
cd platform-mcp/src/tools
for f in tara_balam_for_native chandra_balam_for_native query_transits_over_natal \
  query_yogas_active_now interpret_current_dasha list_canonical_artifact_versions \
  query_jaimini_chara_dasha query_planetary_period_predictions query_eclipse_transits \
  query_planet_war list_assets get_planet_avastha get_shadbala_full \
  query_drekkana_drishti query_dasamsha_career query_shashtiamsha \
  query_remedies_prescribed; do
  echo "=== $f ==="; grep "^export function register" ${f}.ts 2>/dev/null || echo "MISSING"
done
```

Any file missing a `register*` export must be investigated before proceeding.

### Step A.2 — Add imports to server.ts

Find the last `// Tier 3: UDA-2-S8` import block in `server.ts` (currently at
`registerTimelineQuery` and `registerQuerySignalState`). After that block, add
a new import group:

```typescript
// Tier 3: Wave 2 additions (catalog.ts entries not yet registered)
import { registerTaraBalamForNative } from './tools/tara_balam_for_native.js'
import { registerChandraBalamForNative } from './tools/chandra_balam_for_native.js'
import { registerQueryTransitsOverNatal } from './tools/query_transits_over_natal.js'
import { registerQueryYogasActiveNow } from './tools/query_yogas_active_now.js'
import { registerInterpretCurrentDasha } from './tools/interpret_current_dasha.js'
import { registerListCanonicalArtifactVersions } from './tools/list_canonical_artifact_versions.js'
import { registerQueryJaiminiCharaDasha } from './tools/query_jaimini_chara_dasha.js'
import { registerQueryPlanetaryPeriodPredictions } from './tools/query_planetary_period_predictions.js'
import { registerQueryEclipseTransits } from './tools/query_eclipse_transits.js'
import { registerQueryPlanetWar } from './tools/query_planet_war.js'
import { registerListAssets } from './tools/list_assets.js'
import { registerGetPlanetAvastha } from './tools/get_planet_avastha.js'
import { registerGetShadbalaFull } from './tools/get_shadbala_full.js'
import { registerQueryDrekkhanaDrishti } from './tools/query_drekkana_drishti.js'
import { registerQueryDashamshaCareer } from './tools/query_dasamsha_career.js'
import { registerQueryShashtiamsha } from './tools/query_shashtiamsha.js'
import { registerQueryRemediesPrescribed } from './tools/query_remedies_prescribed.js'
```

**Important:** Read each tool file first to get the exact exported function name —
the import names above are guesses based on convention. Adjust to match actual exports.

### Step A.3 — Add registrations in server.ts

After the existing `registerQuerySignalState(server, getPrincipal)` call, add:

```typescript
  // Wave 2 additions — catalog.ts entries now registered (40 → 57 tools)
  registerTaraBalamForNative(server, getPrincipal)
  registerChandraBalamForNative(server, getPrincipal)
  registerQueryTransitsOverNatal(server, getPrincipal)
  registerQueryYogasActiveNow(server, getPrincipal)
  registerInterpretCurrentDasha(server, getPrincipal)
  registerListCanonicalArtifactVersions(server, getPrincipal)
  registerQueryJaiminiCharaDasha(server, getPrincipal)
  registerQueryPlanetaryPeriodPredictions(server, getPrincipal)
  registerQueryEclipseTransits(server, getPrincipal)
  registerQueryPlanetWar(server, getPrincipal)
  registerListAssets(server, getPrincipal)
  registerGetPlanetAvastha(server, getPrincipal)
  registerGetShadbalaFull(server, getPrincipal)
  registerQueryDrekkhanaDrishti(server, getPrincipal)
  registerQueryDashamshaCareer(server, getPrincipal)
  registerQueryShashtiamsha(server, getPrincipal)
  registerQueryRemediesPrescribed(server, getPrincipal)
```

### Step A.4 — Update the server.ts header comment

Update the tool count comment at the top of `server.ts`:
- Change `40 tools registered (v4.5, ...)` → `57 tools registered (v4.6, ...)`
- Add `Wave 2 additions (17 tools): tara_balam_for_native, chandra_balam_for_native, ...` to the Tier 3 list

### Step A.5 — Build and test

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavToolExpansion/platform-mcp
npm run build
npm test
```

Build must pass. If a test references the old tool count (40), update it to 57.
Check `test/tool_descriptions.test.ts` — it likely asserts CATALOG.length.

---

## WORKSTREAM B — Implement three sidecar stub endpoints

### Goal

Three sidecar routes return `{"status": "not_implemented"}`. The underlying DB
tables already have data (loaded by prior pipeline runs). Implement each router
to read from its DB table.

### Step B.0 — Confirm DB tables exist and have data

Connect to the DB (via proxy on port 5433 or DATABASE_URL env var) and run:

```sql
-- Check which tables exist and row counts
SELECT tablename FROM pg_tables WHERE schemaname = 'public'
  AND tablename IN ('eclipses', 'retrograde_stations', 'sade_sati_phases',
                    'retrogrades', 'eclipse_events', 'sade_sati');

-- Check row counts for whatever tables exist
SELECT 'eclipses' as t, COUNT(*) FROM eclipses UNION ALL
SELECT 'retrograde_stations', COUNT(*) FROM retrograde_stations UNION ALL
SELECT 'sade_sati_phases', COUNT(*) FROM sade_sati_phases;
-- (adjust table names based on what actually exists)
```

Also check the existing ingest scripts to understand the actual table and column names:
```bash
cat platform/python-sidecar/pipeline/ingest_eclipses_retrogrades.py
cat platform/scripts/data/populate_sade_sati.py
```

Look for `CREATE TABLE` statements or `INSERT INTO` targets — these give exact table
names and column names to query in the router implementations.

**Do not implement endpoints until you know the exact table names and columns.**

### Step B.1 — Implement `/eclipses` router

File: `platform/python-sidecar/routers/eclipses.py`

Replace the stub with a real implementation that:
1. Accepts params: `date_from` (ISO string), `date_to` (ISO string), `eclipse_type`
   (optional: 'solar'|'lunar'), `limit` (int, default 20)
2. Queries the eclipses DB table (use exact column names from Step B.0)
3. Returns eclipse events sorted by eclipse_date ASC
4. Uses DATABASE_URL env var for DB connection (same as other routers — check
   `platform/python-sidecar/routers/ephemeris.py` for the DB connection pattern)

```python
# Pattern to follow — read ephemeris.py for the exact psycopg/asyncpg import style
# and connection pool pattern used by this sidecar.
```

### Step B.2 — Implement `/retrogrades` router

File: `platform/python-sidecar/routers/retrogrades.py`

Replace the stub with a real implementation that:
1. Accepts params: `planet` (optional), `station_type` (optional: 'retrograde'|'direct'),
   `date_from` (ISO string), `date_to` (ISO string), `limit` (int, default 30)
2. Queries the retrograde_stations (or equivalent) DB table
3. Returns station events sorted by station_date ASC

### Step B.3 — Implement `/sade_sati` router

File: `platform/python-sidecar/routers/sade_sati.py`

Replace the stub with a real implementation that:
1. Accepts params: `native_id` (optional, default 'abhisek_mohanty'),
   `include_past` (boolean, default false)
2. Queries the sade_sati_phases (or equivalent) DB table
3. Returns all phases for the native, with current_phase flag if today falls within
   a phase's date range

If the sade_sati table is EMPTY (the script exists but hasn't been run), note this
in the response body rather than failing:
```python
if not rows:
    return {"status": "no_data", "message": "Sade Sati phases not yet computed. Run platform/scripts/data/populate_sade_sati.py first."}
```

### Step B.4 — Test the implementations

```bash
# Start the sidecar locally
cd /Users/Dev/Vibe-Coding/Apps/MadhavToolExpansion/platform/python-sidecar
DATABASE_URL=<local_or_proxy_url> uvicorn main:app --port 8001

# Test each endpoint
curl -X POST http://localhost:8001/eclipses \
  -H "Content-Type: application/json" \
  -d '{"params": {"date_from": "2026-01-01", "date_to": "2027-01-01"}}'

curl -X POST http://localhost:8001/retrogrades \
  -H "Content-Type: application/json" \
  -d '{"params": {"planet": "Saturn", "date_from": "2024-01-01", "date_to": "2026-12-31"}}'

curl -X POST http://localhost:8001/sade_sati \
  -H "Content-Type: application/json" \
  -d '{"params": {}}'
```

Each must return real data (or a "no_data" message for empty tables), not
`{"status": "not_implemented"}`.

---

## WORKSTREAM C — KP Sub_sub_lord Discrepancy Investigation

### Goal

Investigate why `kp_query` (FORENSIC-anchored) and `query_kp_ruling_planets`
(swisseph-computed) disagree on Saturn's sub_sub_lord (Venus vs Ketu).
Document the root cause. Do NOT change any tool's behavior until root cause is known.

### Step C.1 — Query both data sources

```sql
-- Source 1: FORENSIC-anchored chart_facts (kp_query reads this)
SELECT category, subcategory, key, value, source_canonical_id
FROM chart_facts
WHERE category IN ('kp_cusp', 'kp_planet', 'kp_significator')
  AND (value ILIKE '%saturn%' OR subcategory ILIKE '%saturn%')
ORDER BY category, subcategory, key;

-- Source 2: swisseph-computed kp_sublords (query_kp_ruling_planets reads this)
SELECT planet, star_lord, sub_lord, sub_sub_lord, ayanamsha, birth_jd
FROM kp_sublords
WHERE planet ILIKE '%saturn%';
```

Also find the FORENSIC source data:
```bash
find /Users/Dev/Vibe-Coding/Apps/MadhavToolExpansion \
  -name "*FORENSIC*" -name "*.md" | head -5
grep -i "saturn\|sub_sub\|sub-sub" \
  01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md | head -20
```

### Step C.2 — Check birth data used by each source

For `kp_sublords`: convert `birth_jd` (Julian Day) to a datetime and compare
with the FORENSIC canonical birth data (1984-02-05 10:43:00 IST, Bhubaneswar).

The standard Julian Day for 1984-02-05 10:43:00 IST =
1984-02-05 05:13:00 UTC = JD 2445737.717 (approximately).

Any deviation of even 1–2 minutes in birth time CAN shift KP sub_sub_lord assignments.
Check:
1. Does `birth_jd` in `kp_sublords` match this UTC time?
2. What ayanamsha is used? ('lahiri' vs 'krishnamurti' — KP traditionally uses Krishnamurti)
3. What cusp calculation method? (KP system uses Placidus)

### Step C.3 — Write investigation document

Create `platform-mcp/docs/kp_discrepancy_investigation.md`:

```markdown
# KP Sub_sub_lord Discrepancy — Saturn (Venus vs Ketu)

## Sources
- kp_query (chart_facts, source: FORENSIC §4): Saturn sub_sub_lord = Venus
- query_kp_ruling_planets (kp_sublords, swisseph): Saturn sub_sub_lord = Ketu

## Data comparison
[Fill in: exact degree, sign, star_lord, sub_lord, sub_sub_lord from each source]

## Root cause
[Fill in after investigation: birth_jd discrepancy? ayanamsha? cusp method?]

## Authoritative answer
FORENSIC v8.0 is the canonical authority per CLAUDE.md §B. The chart_facts
value (Venus) is correct until FORENSIC is updated.

## Recommended fix
[Fill in based on findings]
```

---

## §3 — Build, test, and commit sequence

### After completing all workstreams:

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavToolExpansion

# A: MCP server build + test
cd platform-mcp
npm run build
npm test
# Expected: all tests pass, tool count 57

# B: Sidecar test (if you have DB access)
cd ../platform/python-sidecar
python -m pytest tests/ -x  # check existing tests pass

# Commit
git add platform-mcp/src/server.ts \
        platform-mcp/src/tools/catalog.ts \
        platform/python-sidecar/routers/eclipses.py \
        platform/python-sidecar/routers/retrogrades.py \
        platform/python-sidecar/routers/sade_sati.py \
        platform-mcp/docs/kp_discrepancy_investigation.md

git commit -m "feat(mcp): register 17 tools (40→57) + implement 3 sidecar stubs + KP investigation

Workstream A: register 17 tools from catalog.ts that had complete handlers but
were not wired in server.ts. Tool count: 40 → 57.
New tools: tara_balam_for_native, chandra_balam_for_native, query_transits_over_natal,
query_yogas_active_now, interpret_current_dasha, list_canonical_artifact_versions,
query_jaimini_chara_dasha, query_planetary_period_predictions, query_eclipse_transits,
query_planet_war, list_assets, get_planet_avastha, get_shadbala_full,
query_drekkana_drishti, query_dasamsha_career, query_shashtiamsha, query_remedies_prescribed

Workstream B: implement /eclipses, /retrogrades, /sade_sati sidecar routers.
Previously returned not_implemented stub. Now read from DB tables populated
by ingest_eclipses_retrogrades.py + populate_sade_sati.py.

Workstream C: KP discrepancy investigation document authored at
platform-mcp/docs/kp_discrepancy_investigation.md"

git push origin feature/tool-expansion
```

---

## §4 — Acceptance criteria

- [ ] AC-A.1: `tools/list` returns exactly 57 tools (not 40)
- [ ] AC-A.2: All 17 new tools appear in the list with names matching `catalog.ts`
- [ ] AC-A.3: `npm run build` exits 0 in `platform-mcp/`
- [ ] AC-A.4: `npm test` passes all tests in `platform-mcp/`
- [ ] AC-B.1: POST `/eclipses` returns eclipse rows (not `not_implemented`)
- [ ] AC-B.2: POST `/retrogrades` returns station rows (not `not_implemented`)
- [ ] AC-B.3: POST `/sade_sati` returns phase data or a `no_data` message (not `not_implemented`)
- [ ] AC-C.1: `platform-mcp/docs/kp_discrepancy_investigation.md` exists with root cause filled in
- [ ] AC-C.2: `kp_query` and `query_kp_ruling_planets` are both still registered (not removed)

---

## §5 — Must NOT touch

- `platform/src/app/api/` — portal routes
- `CLAUDE.md`, `CURRENT_STATE_v1_0.md`, `SESSION_LOG.md`
- Any tool's `inputSchema` except `query_kp_ruling_planets` description (doc-only)
- `msr_sql.ts` and `query_signals.ts` — do NOT rename, merge, or remove either
- `platform-mcp/src/tools/flag_disagreement.ts` schema — it is correct as-is
- Any migration file
- `server.ts` server boot path / transport / auth logic

---

*End of CLAUDECODE_BRIEF_TOOL_EXPANSION_v1_0.md*
