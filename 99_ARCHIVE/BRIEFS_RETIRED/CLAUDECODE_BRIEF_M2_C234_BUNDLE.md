---
brief_id: M2_C234_BUNDLE
karn_session_name: KARN-W4-R2-C234-BUNDLE
wave: 4
stream: B
status: COMPLETE
authored_by: Claude (Cowork) 2026-04-30 — Wave 3 close
authored_for: Claude Code execution (autonomous, long-running)
session_type: implementation (TypeScript retrieval tools × 3, classifier prompt update, tests, deploy)
target_branch: redesign/r0-foundation
parent_plan: 00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md §B2
karn_protocol: 00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md
karn_session_log: 00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md
related_briefs:
  predecessor: KARN-W2-R2-CHART-FACTS-ETL (chart_facts has kp_cusp/kp_planet/kp_significator/saham/house categories ✅)
  blocks: M2_D7_PER_TOOL_PLANNER (D2 plans against all tools including these three)
parallel_stream_note: |
  Two other Wave-4 briefs run concurrently:
  - KARN-W4-R1-A-MINOR (Stream A — Python sidecar + chart_facts re-ingest; no TS overlap)
  - KARN-W4-R3-CHART-FACTS-QUERY (Stream B — chart_facts_query.ts CREATE only)
  W4-R2 and W4-R3 are both Stream B but scope is disjoint:
  - W4-R2 owns: kp_query.ts + saham_query.ts + divisional_query.ts (CREATE new files)
  - W4-R3 owns: chart_facts_query.ts (CREATE new file)
  Both sessions modify index.ts and router/prompt.ts — COORDINATE by appending only.
  Do NOT rewrite existing exports or rules; append new entries. The last-commit-wins pattern
  on r0-foundation means whichever session commits second will carry both sets of changes.
  If a merge conflict occurs on index.ts or prompt.ts, resolve by including all additions
  from both sessions (no deletions).
estimated_time: ½–1 day single Claude Code session

carry_forward_notes:
  - "chart_facts has 795 rows / 37 categories as of Wave 3 close. Relevant categories:
       kp_cusp(12), kp_planet(9), kp_significator(7), saham(36), house(149).
     Do NOT run any chart_facts migrations — data is already present."
  - "Pre-existing Jest ESM issue: 13 suites fail with Babel/ESM config. Baseline ~964 passing.
     Do not treat as regression."
  - "RETRIEVAL_TOOLS array currently has 10 tools. After this session: 13."

scope_summary: |
  Three small TypeScript retrieval tools that surface the KP, Saham, and divisional
  chart data that was loaded into chart_facts by W2-R2. All data exists in the DB;
  this session writes only TypeScript and tests.

  Tools:
  1. kp_query — queries chart_facts where category IN ('kp_cusp', 'kp_planet', 'kp_significator').
     Parameters: cusp? (1-12), planet? (planet name), query_type? ('significators'|'star_lord'|'sub_lord'|'all').
     Returns the KP cusp-significator map or planet-significator lookup structured for synthesis.

  2. saham_query — queries chart_facts where category='saham'.
     Parameters: saham_name? (e.g. 'Vivaha', 'Raja', 'Putra', etc.), sign?, house?, nakshatra?.
     Returns the 36 Tajika lot rows (or filtered subset) with longitude, nakshatra, sign, house, meaning.

  3. divisional_query — queries chart_facts for a specific divisional chart.
     Parameters: varga ('D1'|'D2'|'D3'|'D4'|'D7'|'D9'|'D10'|'D12'|'D16'|'D20'|'D24'|'D27'|'D30'|'D40'|'D45'|'D60'),
                 planet? (planet name), house? (1-12), category? ('house'|'planet'|'strength').
     Returns placements or house-cusps for the named divisional chart, filtered by planet/house if supplied.

  Each tool:
  - Queries chart_facts via a direct DB query (same pattern as msr_sql.ts — no sidecar call needed)
  - Is registered in RETRIEVAL_TOOLS + CAPABILITY_MANIFEST
  - Has ≥5 test cases
  - Has a tool-guidance block added to the classifier router prompt

may_touch:
  - platform/src/lib/retrieve/kp_query.ts                                    # CREATE
  - platform/src/lib/retrieve/saham_query.ts                                 # CREATE
  - platform/src/lib/retrieve/divisional_query.ts                            # CREATE
  - platform/src/lib/retrieve/__tests__/kp_query.test.ts                     # CREATE
  - platform/src/lib/retrieve/__tests__/saham_query.test.ts                  # CREATE
  - platform/src/lib/retrieve/__tests__/divisional_query.test.ts             # CREATE
  - platform/src/lib/retrieve/index.ts                                       # append 3 imports + 3 exports + 3 RETRIEVAL_TOOLS entries
  - platform/src/lib/retrieve/types.ts                                       # add KpQueryInput, SahamQueryInput, DivisionalQueryInput if needed
  - platform/src/lib/router/prompt.ts                                        # append 3 tool-guidance blocks
  - platform/src/lib/router/types.ts                                         # add optional fields to QueryPlan if needed
  - platform/src/lib/db/types.ts                                             # add ChartFactsRow type if not already present
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_C234_BUNDLE.md                # status flip
  - 00_ARCHITECTURE/BRIEFS/M2_C234_VERIFICATION_<DATE>.txt                   # CREATE
  - 00_ARCHITECTURE/CAPABILITY_MANIFEST.json                                 # append 3 tool entries (append-only, sorted)

must_not_touch:
  - platform/migrations/**                                                   # no schema changes needed
  - platform/python-sidecar/**                                               # W4-R1 territory
  - platform/src/lib/retrieve/chart_facts_query.ts                           # W4-R3 territory (may not exist yet — do not create)
  - platform/src/lib/retrieve/msr_sql.ts                                     # existing tool, do not modify
  - platform/src/lib/retrieve/temporal.ts                                    # existing tool, do not modify
  - platform/src/lib/retrieve/vector_search.ts                               # existing tool, do not modify
  - platform/src/lib/retrieve/cgm_graph_walk.ts                              # existing tool, do not modify
  - platform/src/lib/retrieve/pattern_register.ts                            # existing tool, do not modify
  - platform/src/lib/retrieve/resonance_register.ts                          # existing tool, do not modify
  - platform/src/lib/retrieve/cluster_atlas.ts                               # existing tool, do not modify
  - platform/src/lib/retrieve/contradiction_register.ts                      # existing tool, do not modify
  - platform/src/lib/retrieve/manifest_query.ts                              # existing tool, do not modify
  - platform/src/lib/retrieve/query_msr_aggregate.ts                         # existing tool, do not modify
  - platform/src/app/**                                                      # UI/UX scope
  - platform/src/components/**                                               # UI/UX scope
  - 035_DISCOVERY_LAYER/**                                                   # Stream C territory
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_A_MINOR.md                   # sibling Wave-4
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_C1_CHART_FACTS_QUERY.md      # sibling Wave-4
---

# KARN-W4-R2-C234-BUNDLE — Execution Brief

## §0 — Context

This is an autonomous Claude Code session. Read this entire brief before writing any code. Then execute
§1 (pre-flight) before touching anything. Halt immediately if any pre-flight check fails.

Parent plan: `M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md §B2`. You are adding three new TypeScript retrieval
tools that surface KP, Saham, and divisional chart data from the `chart_facts` table. This is a
TypeScript-only session — no Python sidecar changes, no migrations.

**Parallel context:** W4-R3 (chart_facts_query) runs concurrently and will also CREATE a file and
modify index.ts + prompt.ts. If you commit after W4-R3, ensure you include W4-R3's changes (do not
overwrite them). If W4-R3's file (chart_facts_query.ts) already exists when you check, do not modify it.

---

## §1 — Pre-flight self-diagnostics

```bash
# PF.1 — Branch check
git branch --show-current
# Expected: redesign/r0-foundation. Any other → HALT.

# PF.2 — Working tree clean
git status --short
# Expected: clean or only files in may_touch list. Unexpected modifications → HALT.

# PF.3 — chart_facts KP + saham + divisional data present
psql "host=127.0.0.1 port=5433 dbname=amjis user=amjis-app" -c \
  "SELECT category, COUNT(*) FROM chart_facts
   WHERE category IN ('kp_cusp','kp_planet','kp_significator','saham','house')
     AND is_stale=false
   GROUP BY category ORDER BY category;"
# Expected:
#   house        | 149
#   kp_cusp      | 12
#   kp_planet    | 9
#   kp_significator | 7
#   saham        | 36
# If any category is missing or zero → HALT with "Prerequisite data not present".

# PF.4 — Sample a kp_cusp row to understand value_json shape
psql "host=127.0.0.1 port=5433 dbname=amjis user=amjis-app" -c \
  "SELECT fact_id, value_text, value_json
   FROM chart_facts WHERE category='kp_cusp' AND is_stale=false LIMIT 3;"
# Record the value_json shape. This determines the TypeScript return type.

# PF.5 — Sample a saham row
psql "host=127.0.0.1 port=5433 dbname=amjis user=amjis-app" -c \
  "SELECT fact_id, value_text, value_json
   FROM chart_facts WHERE category='saham' AND is_stale=false LIMIT 3;"

# PF.6 — Sample house rows by divisional_chart to understand varga variety
psql "host=127.0.0.1 port=5433 dbname=amjis user=amjis-app" -c \
  "SELECT divisional_chart, COUNT(*) FROM chart_facts
   WHERE category='house' AND is_stale=false
   GROUP BY divisional_chart ORDER BY divisional_chart;"

# PF.7 — TypeScript test baseline
cd platform && npx vitest run --reporter=verbose 2>&1 | tail -10
# Record pass/fail counts as baseline.

# PF.8 — Check if chart_facts_query.ts already exists (W4-R3 territory)
ls platform/src/lib/retrieve/chart_facts_query.ts 2>/dev/null && echo "EXISTS — do not modify" || echo "NOT YET"

# PF.9 — Check current index.ts RETRIEVAL_TOOLS count
grep -c "tool," platform/src/lib/retrieve/index.ts 2>/dev/null || grep -c "\.tool" platform/src/lib/retrieve/index.ts
# Expected: 10 tools registered currently.
```

---

## §2 — Implementation

### §2.0 — DB query helper pattern (follow msr_sql.ts style)

Study `platform/src/lib/retrieve/msr_sql.ts` for the correct pattern:
- Direct SQL via `sql` tagged template or the project's DB client
- Returns a `ToolBundle` with `results: ToolBundleResult[]`
- Each result has `content`, `source_canonical_id`, `source_version`, `confidence`, `significance`
- Tool has `name`, `version`, `description`, `retrieve(plan, params?)` function
- Tool is also exported as `tool: RetrievalTool` for the registry

Also check `platform/src/lib/db/types.ts` for any existing `ChartFactsRow` type.
If it doesn't exist, define a minimal one:

```typescript
export interface ChartFactsRow {
  id: string
  fact_id: string
  category: string
  divisional_chart: string
  value_text: string | null
  value_number: number | null
  value_json: Record<string, unknown> | null
  source_section: string
  provenance: Record<string, unknown>
}
```

---

### §2.1 — kp_query.ts

**Create `platform/src/lib/retrieve/kp_query.ts`:**

```typescript
/**
 * MARSYS-JIS Stream B — Tool: kp_query (M2-C.2)
 *
 * Queries chart_facts for Krishnamurti Paddhati (KP) data:
 * cusp significators, planet significators, star lord / sub lord chains.
 *
 * Categories covered: kp_cusp (12 rows), kp_planet (9 rows), kp_significator (7 rows)
 */

import crypto from 'crypto'
import { getDb } from '@/lib/db'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'kp_query'
const TOOL_VERSION = '1.0'

export interface KpQueryInput {
  cusp?: number          // 1-12; filter to a specific house cusp
  planet?: string        // e.g. 'Sun', 'Moon', 'Mars'; filter to a planet
  query_type?: 'significators' | 'star_lord' | 'sub_lord' | 'sub_sub_lord' | 'all'
}

async function retrieve(plan: QueryPlan, params?: KpQueryInput): Promise<ToolBundle> {
  const start = Date.now()
  const db = getDb()

  // Determine which categories to query
  const categories = ['kp_cusp', 'kp_planet', 'kp_significator']

  // If cusp is specified, restrict to kp_cusp + kp_significator
  // If planet is specified, restrict to kp_planet
  let categoryFilter = categories
  if (params?.cusp !== undefined) {
    categoryFilter = ['kp_cusp', 'kp_significator']
  } else if (params?.planet) {
    categoryFilter = ['kp_planet']
  }

  // Build query
  const conditions: string[] = [
    `category = ANY($1)`,
    `is_stale = false`,
  ]
  const queryParams: unknown[] = [categoryFilter]
  let paramIdx = 2

  if (params?.cusp !== undefined) {
    conditions.push(`(value_json->>'cusp')::int = $${paramIdx}`)
    queryParams.push(params.cusp)
    paramIdx++
  }

  if (params?.planet) {
    conditions.push(`(value_json->>'planet' ILIKE $${paramIdx} OR fact_id ILIKE $${paramIdx})`)
    queryParams.push(`%${params.planet}%`)
    paramIdx++
  }

  const sql = `
    SELECT fact_id, category, divisional_chart, value_text, value_json, source_section
    FROM chart_facts
    WHERE ${conditions.join(' AND ')}
    ORDER BY category, fact_id
    LIMIT 50
  `

  const rows = await db.query(sql, queryParams)

  const results: ToolBundleResult[] = rows.map((row: Record<string, unknown>) => ({
    content: JSON.stringify({
      fact_id: row.fact_id,
      category: row.category,
      value_text: row.value_text,
      kp_data: row.value_json,
      source: row.source_section,
    }),
    source_canonical_id: 'FORENSIC',
    source_version: '8.0',
    confidence: 1.0,
    significance: 0.85,
  }))

  return {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: TOOL_NAME,
    tool_version: TOOL_VERSION,
    invocation_params: {
      cusp: params?.cusp,
      planet: params?.planet,
      query_type: params?.query_type ?? 'all',
    },
    results,
    latency_ms: Date.now() - start,
    item_count: results.length,
    cached: false,
  }
}

export const tool: RetrievalTool = {
  name: TOOL_NAME,
  version: TOOL_VERSION,
  description: 'KP (Krishnamurti Paddhati) cusp and planet significator lookup. ' +
    'Returns star lord, sub lord, sub-sub lord chains for cusps 1–12 and all 9 planets. ' +
    'Use for KP-system house occupation, signification, and ruling planet queries.',
  retrieve,
}
```

**NOTE:** Check the actual DB client import pattern in `msr_sql.ts` and mirror it exactly.
If the project uses `import { sql } from '@vercel/postgres'` or `import pool from '@/lib/db/pool'`
or similar — use whatever is already established. Do not introduce a new DB client.

---

### §2.2 — saham_query.ts

**Create `platform/src/lib/retrieve/saham_query.ts`:**

```typescript
/**
 * MARSYS-JIS Stream B — Tool: saham_query (M2-C.3)
 *
 * Queries chart_facts for Tajika Saham (Arabic Part / Lot) data.
 * 36 sahams from FORENSIC §12.2 — each has longitude, nakshatra, sign, house, meaning.
 *
 * Category: saham (36 rows)
 */

import crypto from 'crypto'
import { getDb } from '@/lib/db'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'saham_query'
const TOOL_VERSION = '1.0'

export interface SahamQueryInput {
  saham_name?: string    // e.g. 'Vivaha', 'Raja', 'Putra', 'Mrityu', 'Karma' (partial match)
  sign?: string          // zodiac sign filter
  house?: number         // 1-12 house filter
  nakshatra?: string     // nakshatra filter
}

// Known saham names from FORENSIC §12.2 (for classifier reference)
export const KNOWN_SAHAMS = [
  'Punya', 'Vidya', 'Vikrama', 'Ksema', 'Upapada', 'Dara', 'Santana',
  'Vivaha', 'Kalatra', 'Putra', 'Karma', 'Raja', 'Mrityu', 'Paradesa',
  'Artha', 'Roga', 'Kali', 'Sastra', 'Bandhu', 'Matra', 'Pitra',
  'Pitrvyaya', 'Rajya', 'Jalapatana', 'Irsha', 'Paradara', 'Vanik',
  'Karyasiddhi', 'Vivaha2', 'Labha', 'Bhratru', 'Ayu', 'Saubhagya',
  'Shitila', 'Shatru', 'Jiva',
]

async function retrieve(plan: QueryPlan, params?: SahamQueryInput): Promise<ToolBundle> {
  const start = Date.now()
  const db = getDb()

  const conditions: string[] = [`category = 'saham'`, `is_stale = false`]
  const queryParams: unknown[] = []
  let paramIdx = 1

  if (params?.saham_name) {
    conditions.push(`(fact_id ILIKE $${paramIdx} OR value_text ILIKE $${paramIdx} OR value_json->>'name' ILIKE $${paramIdx})`)
    queryParams.push(`%${params.saham_name}%`)
    paramIdx++
  }

  if (params?.sign) {
    conditions.push(`value_json->>'sign' ILIKE $${paramIdx}`)
    queryParams.push(`%${params.sign}%`)
    paramIdx++
  }

  if (params?.house !== undefined) {
    conditions.push(`(value_json->>'house')::int = $${paramIdx}`)
    queryParams.push(params.house)
    paramIdx++
  }

  if (params?.nakshatra) {
    conditions.push(`value_json->>'nakshatra' ILIKE $${paramIdx}`)
    queryParams.push(`%${params.nakshatra}%`)
    paramIdx++
  }

  const sql = `
    SELECT fact_id, value_text, value_json, source_section
    FROM chart_facts
    WHERE ${conditions.join(' AND ')}
    ORDER BY fact_id
    LIMIT 36
  `

  const rows = await db.query(sql, queryParams)

  const results: ToolBundleResult[] = rows.map((row: Record<string, unknown>) => ({
    content: JSON.stringify({
      fact_id: row.fact_id,
      value_text: row.value_text,
      saham: row.value_json,
      source: row.source_section,
    }),
    source_canonical_id: 'FORENSIC',
    source_version: '8.0',
    confidence: 1.0,
    significance: 0.80,
  }))

  return {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: TOOL_NAME,
    tool_version: TOOL_VERSION,
    invocation_params: {
      saham_name: params?.saham_name,
      sign: params?.sign,
      house: params?.house,
      nakshatra: params?.nakshatra,
    },
    results,
    latency_ms: Date.now() - start,
    item_count: results.length,
    cached: false,
  }
}

export const tool: RetrievalTool = {
  name: TOOL_NAME,
  version: TOOL_VERSION,
  description: 'Tajika Saham (Lot/Arabic Part) lookup. Returns any of the 36 Sahams from the ' +
    'native\'s chart with their longitude, nakshatra, sign, house, and traditional meaning. ' +
    'Use for questions about Saham Vivaha (marriage), Raja (power), Putra (children), ' +
    'Mrityu (death), Karma (profession), or any other Tajika lot.',
  retrieve,
}
```

---

### §2.3 — divisional_query.ts

**Create `platform/src/lib/retrieve/divisional_query.ts`:**

```typescript
/**
 * MARSYS-JIS Stream B — Tool: divisional_query (M2-C.4)
 *
 * Queries chart_facts for divisional chart (varga) placements.
 * Covers D1 through D60 — filtered by divisional_chart column.
 *
 * Categories covered: house (149 rows), planet (45 rows)
 */

import crypto from 'crypto'
import { getDb } from '@/lib/db'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'divisional_query'
const TOOL_VERSION = '1.0'

export type VargaCode =
  | 'D1' | 'D2' | 'D3' | 'D4' | 'D7' | 'D9' | 'D10'
  | 'D12' | 'D16' | 'D20' | 'D24' | 'D27' | 'D30'
  | 'D40' | 'D45' | 'D60' | 'BIRTH'

export interface DivisionalQueryInput {
  varga: VargaCode         // required — which divisional chart
  planet?: string          // optional — filter to specific planet
  house?: number           // optional — filter to specific house (1-12)
  category?: 'house' | 'planet' | 'both'  // default: 'both'
}

async function retrieve(plan: QueryPlan, params?: DivisionalQueryInput): Promise<ToolBundle> {
  const start = Date.now()
  const db = getDb()

  if (!params?.varga) {
    // Default to D9 for unspecified divisional queries (most common in synthesis)
    params = { ...params, varga: 'D9' }
  }

  const categories = params.category === 'house' ? ['house']
    : params.category === 'planet' ? ['planet']
    : ['house', 'planet', 'strength', 'chalit_shift']  // 'both' includes strength + chalit

  const conditions: string[] = [
    `divisional_chart = $1`,
    `category = ANY($2)`,
    `is_stale = false`,
  ]
  const queryParams: unknown[] = [params.varga, categories]
  let paramIdx = 3

  if (params.planet) {
    conditions.push(`(value_json->>'planet' ILIKE $${paramIdx} OR fact_id ILIKE $${paramIdx})`)
    queryParams.push(`%${params.planet}%`)
    paramIdx++
  }

  if (params.house !== undefined) {
    conditions.push(`(value_json->>'house')::int = $${paramIdx}`)
    queryParams.push(params.house)
    paramIdx++
  }

  const sql = `
    SELECT fact_id, category, divisional_chart, value_text, value_json, source_section
    FROM chart_facts
    WHERE ${conditions.join(' AND ')}
    ORDER BY category, fact_id
    LIMIT 60
  `

  const rows = await db.query(sql, queryParams)

  const results: ToolBundleResult[] = rows.map((row: Record<string, unknown>) => ({
    content: JSON.stringify({
      fact_id: row.fact_id,
      category: row.category,
      varga: params!.varga,
      value_text: row.value_text,
      placement: row.value_json,
      source: row.source_section,
    }),
    source_canonical_id: 'FORENSIC',
    source_version: '8.0',
    confidence: 1.0,
    significance: 0.85,
  }))

  return {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: TOOL_NAME,
    tool_version: TOOL_VERSION,
    invocation_params: {
      varga: params.varga,
      planet: params.planet,
      house: params.house,
      category: params.category ?? 'both',
    },
    results,
    latency_ms: Date.now() - start,
    item_count: results.length,
    cached: false,
  }
}

export const tool: RetrievalTool = {
  name: TOOL_NAME,
  version: TOOL_VERSION,
  description: 'Divisional chart (varga) placement lookup. Returns house positions and planet ' +
    'placements in any divisional chart: D1 (rashi), D9 (navamsha), D10 (dasamsha), ' +
    'D7 (saptamsha), D2 (hora), D12 (dwadasamsha), D3 (drekkana), D60 (shashtiamsha), etc. ' +
    'Use when the query involves a specific varga chart or requires varga confirmation of D1 placements.',
  retrieve,
}
```

---

### §2.4 — Update index.ts

Append to `platform/src/lib/retrieve/index.ts` (DO NOT rewrite the file; append after existing content):

```typescript
// Wave 4 additions — M2-C234-BUNDLE
import * as kpQuery from './kp_query'
import * as sahamQuery from './saham_query'
import * as divisionalQuery from './divisional_query'
```

And push the three tools into the RETRIEVAL_TOOLS array. If the array is declared with `const`,
change to a mutable approach or extend in-place — mirror whatever pattern the existing file uses.

---

### §2.5 — Update router/prompt.ts

Append three tool-guidance blocks to the classifier prompt. Find the section with guidance for
existing tools (like the vector_search filter guidance from W1-R2). Add after the last existing block:

```
## KP Query Guidance (kp_query tool)
Authorize `kp_query` for queries about:
- KP cusp significators: "What planets signify house 7?", "KP 7th house planets"
- Star lord / sub lord chains: "Star lord of my 10th cusp", "sub lord of ascendant"
- KP planet significators: "which houses does Saturn signify in KP?"
- Any query containing "KP", "Krishnamurti", "star lord", "sub lord", "cusp significator"
Pass `cusp` param when a specific house number is mentioned.
Pass `planet` param when a specific planet significator is queried.

## Saham Query Guidance (saham_query tool)
Authorize `saham_query` for queries about:
- Any named saham/lot: "Saham Vivaha", "Saham Raja", "Saham Putra", "Saham Mrityu"
- Arabic parts / Tajika lots generically: "my marriage lot", "prosperity saham"
- Any query containing "saham", "lot", "Arabic part", "Tajika"
Pass `saham_name` as the named saham when specified.

## Divisional Query Guidance (divisional_query tool)
Authorize `divisional_query` for queries about:
- Specific varga charts: "D9 placement of Venus", "navamsha chart", "dasamsha position"
- Varga confirmation: "Venus in D9", "Saturn in D10", "Moon in D7"
- Any query containing varga codes (D1–D60), "navamsha", "dasamsha", "saptamsha", "drekkana"
Pass `varga` as the identified varga code (e.g. 'D9', 'D10').
Pass `planet` when a specific planet is mentioned.
```

---

### §2.6 — Tests

**Create `platform/src/lib/retrieve/__tests__/kp_query.test.ts`:**
Test cases:
1. retrieve() with no params returns all KP rows (count ≥ 24 = 12+9+7 expected minus overlaps)
2. retrieve() with `cusp: 7` returns only kp_cusp + kp_significator rows for cusp 7
3. retrieve() with `planet: 'Saturn'` returns Saturn's KP significators
4. ToolBundle shape: has tool_bundle_id, tool_name='kp_query', results array
5. Empty result for nonexistent cusp (cusp: 99) returns empty results without error

**Create `platform/src/lib/retrieve/__tests__/saham_query.test.ts`:**
Test cases:
1. retrieve() with no params returns 36 saham rows
2. retrieve() with `saham_name: 'Vivaha'` returns the Vivaha saham row
3. retrieve() with `house: 7` returns sahams falling in house 7
4. ToolBundle shape correct
5. retrieve() with `saham_name: 'NonExistent'` returns empty results without error

**Create `platform/src/lib/retrieve/__tests__/divisional_query.test.ts`:**
Test cases:
1. retrieve() with `varga: 'D9'` returns D9 placements (count > 0)
2. retrieve() with `varga: 'D1'` returns D1 placements (count > 0, divisional_chart='D1')
3. retrieve() with `varga: 'D9', planet: 'Venus'` returns only Venus D9 rows
4. ToolBundle shape correct
5. retrieve() with valid varga but no data returns empty results without error

**Testing approach:** If the DB is not available in the test environment (no Auth Proxy in CI),
mock the DB client similar to how msr_sql.test.ts mocks it. Check msr_sql.test.ts for the mock
pattern and follow it exactly.

---

## §3 — Acceptance criteria

### AC.1 — Branch state
`git branch --show-current` returns `redesign/r0-foundation`.

### AC.2 — Three tool files created
All three files exist:
- `platform/src/lib/retrieve/kp_query.ts`
- `platform/src/lib/retrieve/saham_query.ts`
- `platform/src/lib/retrieve/divisional_query.ts`

### AC.3 — Three tools registered in RETRIEVAL_TOOLS
`grep -c "kp_query\|saham_query\|divisional_query" platform/src/lib/retrieve/index.ts`
Returns at least 3 (one per import + one per RETRIEVAL_TOOLS push).

RETRIEVAL_TOOLS array has 13 entries (was 10).

### AC.4 — Classifier prompt has three guidance blocks
```bash
grep -c "kp_query\|saham_query\|divisional_query" platform/src/lib/router/prompt.ts
```
Returns ≥ 3.

### AC.5 — kp_query returns correct structure for cusp 7 query
Using the live DB (or mock): retrieve() with `{cusp: 7}` returns a ToolBundle where:
- `tool_name == 'kp_query'`
- `results.length > 0`
- Each result's content is valid JSON with `fact_id` field

### AC.6 — saham_query returns 36 rows for unfiltered call
`results.length == 36` when no params provided (or close to 36 — within 2 if some rows are stale).

### AC.7 — divisional_query returns D9 rows for varga='D9'
`results.length > 0` and all results have `varga: 'D9'`.

### AC.8 — Tests: ≥5 per tool file, all passing
```bash
cd platform && npx vitest run src/lib/retrieve/__tests__/kp_query.test.ts \
  src/lib/retrieve/__tests__/saham_query.test.ts \
  src/lib/retrieve/__tests__/divisional_query.test.ts
```
All tests pass. No new failures vs pre-flight baseline.

### AC.9 — TypeScript compiles without errors
```bash
cd platform && npx tsc --noEmit 2>&1 | grep -v "node_modules" | head -20
```
No new TypeScript errors from the three new files.

### AC.10 — Deploy: Cloud Run revision updated
```bash
bash platform/scripts/cloud_build_submit.sh
```
New revision serving 100%. The three tools are importable at runtime.

---

## §4 — Halt conditions

Halt immediately and emit a 5-line halt summary if:

1. **PF.1 fails:** Branch not `redesign/r0-foundation`.
2. **PF.3 fails — categories missing:** If kp_cusp (12), saham (36), or house (149) categories have
   zero rows in chart_facts. This means W2-R2 did not complete successfully — HALT.
3. **DB client pattern ambiguous:** If the project has two competing DB client patterns and it's
   unclear which to use — HALT with findings. The correct pattern is whatever msr_sql.ts uses.
4. **Index.ts conflict with W4-R3:** If chart_facts_query.ts already exists AND index.ts already
   imports it, proceed carefully — append only. If index.ts would fail to compile with both sets
   of additions, fix the compile error.
5. **Test count regression > 5 new failures:** Halt before deploy.

Non-halting: empty result for a specific query (the data may not match the filter — not a bug);
TypeScript strict mode warnings on the mock DB in tests (suppress with type assertions if needed).

---

## §5 — Closing summary template

```
SESSION CLOSE — M2_C234_BUNDLE — <ISO timestamp>

ACs result:
  AC.1:  <PASS|FAIL> — branch check
  AC.2:  <PASS|FAIL> — three tool files created
  AC.3:  <PASS|FAIL> — RETRIEVAL_TOOLS count 10 → 13
  AC.4:  <PASS|FAIL> — classifier prompt updated
  AC.5:  <PASS|FAIL> — kp_query cusp-7 returns results
  AC.6:  <PASS|FAIL> — saham_query unfiltered returns ≥34 rows
  AC.7:  <PASS|FAIL> — divisional_query D9 returns results
  AC.8:  <PASS|FAIL> — ≥15 tests passing (5 per tool)
  AC.9:  <PASS|FAIL> — TypeScript compiles clean
  AC.10: <PASS|FAIL> — Cloud Run revision updated

Files created/modified:
  platform/src/lib/retrieve/kp_query.ts (CREATE)
  platform/src/lib/retrieve/saham_query.ts (CREATE)
  platform/src/lib/retrieve/divisional_query.ts (CREATE)
  platform/src/lib/retrieve/__tests__/kp_query.test.ts (CREATE)
  platform/src/lib/retrieve/__tests__/saham_query.test.ts (CREATE)
  platform/src/lib/retrieve/__tests__/divisional_query.test.ts (CREATE)
  platform/src/lib/retrieve/index.ts (modified — 3 imports + 3 RETRIEVAL_TOOLS entries)
  platform/src/lib/router/prompt.ts (modified — 3 tool-guidance blocks appended)

DB changes: None (chart_facts is read-only for this session)

Cloud Run: <prior revision> → <new revision>

Tests:
  Before: <X passed / Y failed>
  After: <X' passed / Y' failed>
  Delta: <new failures count>

Halt-and-report cases: <none | description>

Brief status: <COMPLETE | HALTED_AT_AC.N>
Next brief in stream: M2_C5_TEMPORAL_EXTENSION (W5-R1)
```

After emitting the closing summary, append a session entry to
`00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md` per protocol §3.1, and flip
`status: COMPLETE` in this brief's frontmatter.

---

*End of CLAUDECODE_BRIEF_M2_C234_BUNDLE v1.0 (authored 2026-04-30 — Wave 3 close).*
