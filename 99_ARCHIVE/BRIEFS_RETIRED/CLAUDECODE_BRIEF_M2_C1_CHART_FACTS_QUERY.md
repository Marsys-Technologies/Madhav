---
brief_id: M2_C1_CHART_FACTS_QUERY
karn_session_name: KARN-W4-R3-CHART-FACTS-QUERY
wave: 4
stream: B
status: COMPLETE
authored_by: Claude (Cowork) 2026-04-30 — Wave 3 close
authored_for: Claude Code execution (autonomous, long-running)
session_type: implementation (TypeScript retrieval tool × 1, classifier prompt update, QueryPlan type extension, ≥10 tests, deploy)
target_branch: redesign/r0-foundation
parent_plan: 00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md §B3
karn_protocol: 00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md
karn_session_log: 00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md
related_briefs:
  predecessor: KARN-W2-R2-CHART-FACTS-ETL (chart_facts 795 rows / 37 categories ✅)
  blocks: M2_D7_PER_TOOL_PLANNER (D2 plans against chart_facts_query as its richest tool)
parallel_stream_note: |
  Two other Wave-4 briefs run concurrently:
  - KARN-W4-R1-A-MINOR (Stream A — Python sidecar; no TS overlap)
  - KARN-W4-R2-C234-BUNDLE (Stream B — kp_query + saham_query + divisional_query)
  W4-R3 and W4-R2 are both Stream B but scope is disjoint:
  - W4-R2 owns: kp_query.ts + saham_query.ts + divisional_query.ts (3 small tools)
  - W4-R3 owns: chart_facts_query.ts (1 large parametric tool)
  Both sessions modify index.ts and router/prompt.ts — COORDINATE by appending only.
  Do NOT rewrite existing exports; append new entries.
  If a merge conflict occurs on index.ts or prompt.ts: resolve by including all additions
  from both sessions. No deletions.
estimated_time: ½–1 day single Claude Code session

carry_forward_notes:
  - "chart_facts has 795 rows / 37 categories as of Wave 3 close. The full category enum:
     house, dasha_chara, planet, dasha_vimshottari, saham, sensitive_point, birth_metadata,
     strength_extra, yoga, dasha_yogini, deity_assignment, shadbala, ashtakavarga_sav,
     kp_cusp, navatara, panchang, cusp, arudha_occupancy, bhava_bala, chandra_placement,
     mrityu_bhaga, longevity_indicator, arudha, aspect, chalit_shift, kp_planet,
     special_lagna, strength, upagraha, ashtakavarga_bav, kakshya_zone, mercury_convergence,
     ashtakavarga_pinda, ishta_kashta, kp_significator, varshphal, avastha."
  - "This tool is the 'big one' — it is the primary gateway for quantitative chart queries.
     The classifier should prefer it for any numerical ranking (shadbala, BAV bindus, strength)
     or specific fact lookup (saham by name, yoga register, ashtakavarga). The small-bundle
     tools (kp_query, saham_query, divisional_query from W4-R2) may overlap in coverage —
     that is acceptable; the classifier will authorize the most specific tool available."
  - "Pre-existing Jest ESM issue: 13 suites fail. Baseline ~964 passing. Do not regress."
  - "W4-R1 may add nakshatra_pada to planet rows' value_json. chart_facts_query should pass
     nakshatra_pada as a filter param so classifiers can use it once it's populated."

scope_summary: |
  chart_facts_query is the parametric retrieval tool that makes the entire 795-row
  chart_facts table queryable by the classifier. It accepts a rich set of filter
  parameters (category, planet, house, sign, nakshatra, pada, divisional_chart, rank_by,
  limit) and returns structured rows. The classifier learns to use it for any query
  that involves a quantitative chart fact: strengths, BAV bindus, sahams, placements,
  yogas, aspects, etc.

  This is Stream B's "B3" brief — the single most impactful retrieval tool in Wave 4
  because it enables the LLM to perform arbitrary chart-fact retrieval without knowing
  which specific sub-category the fact lives in.

  Key query patterns the tool must satisfy:
  - "Rank my planets by Shadbala" → category='shadbala', rank_by='total_rupas'
  - "What is the BAV of Mars in Capricorn?" → category='ashtakavarga_bav', planet='Mars', sign='Capricorn'
  - "What is my Saham Vivaha?" → category='saham', keyword='Vivaha'
  - "Show me my yoga register" → category='yoga'
  - "What is my ashtakavarga SAV score for Sagittarius?" → category='ashtakavarga_sav', sign='Sagittarius'
  - "My bhava bala rankings" → category='bhava_bala', rank_by='value_number'
  - "What planets are in my 4th house?" → category='house', house=4
  - "What is my Moon's nakshatra pada?" → category='planet', planet='Moon'
  - "Show me all longevity indicators" → category='longevity_indicator'
  - "What upagrahas are significant?" → category='upagraha'

may_touch:
  - platform/src/lib/retrieve/chart_facts_query.ts                          # CREATE — the tool
  - platform/src/lib/retrieve/__tests__/chart_facts_query.test.ts           # CREATE — ≥10 tests
  - platform/src/lib/retrieve/index.ts                                      # append 1 import + 1 RETRIEVAL_TOOLS entry
  - platform/src/lib/retrieve/types.ts                                      # add ChartFactsQueryInput type
  - platform/src/lib/router/prompt.ts                                       # append chart_facts_query guidance block
  - platform/src/lib/router/types.ts                                        # add chart_facts_query field to QueryPlan
  - platform/src/lib/db/types.ts                                            # add ChartFactsRow type if absent
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_C1_CHART_FACTS_QUERY.md     # status flip
  - 00_ARCHITECTURE/BRIEFS/M2_C1_VERIFICATION_<DATE>.txt                   # CREATE
  - 00_ARCHITECTURE/CAPABILITY_MANIFEST.json                               # append tool entry

must_not_touch:
  - platform/migrations/**                                                  # no schema changes needed
  - platform/python-sidecar/**                                              # W4-R1 territory
  - platform/src/lib/retrieve/kp_query.ts                                   # W4-R2 territory (may not exist yet)
  - platform/src/lib/retrieve/saham_query.ts                                # W4-R2 territory
  - platform/src/lib/retrieve/divisional_query.ts                           # W4-R2 territory
  - platform/src/lib/retrieve/msr_sql.ts                                    # existing tool
  - platform/src/lib/retrieve/temporal.ts                                   # existing tool
  - platform/src/lib/retrieve/vector_search.ts                              # existing tool
  - platform/src/lib/retrieve/cgm_graph_walk.ts                             # existing tool
  - platform/src/lib/retrieve/pattern_register.ts                           # existing tool
  - platform/src/lib/retrieve/resonance_register.ts                         # existing tool
  - platform/src/lib/retrieve/cluster_atlas.ts                              # existing tool
  - platform/src/lib/retrieve/contradiction_register.ts                     # existing tool
  - platform/src/lib/retrieve/manifest_query.ts                             # existing tool
  - platform/src/lib/retrieve/query_msr_aggregate.ts                        # existing tool
  - platform/src/app/**                                                     # UI/UX scope
  - platform/src/components/**                                              # UI/UX scope
  - 035_DISCOVERY_LAYER/**                                                  # Stream C territory
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_A_MINOR.md                  # sibling Wave-4
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_C234_BUNDLE.md              # sibling Wave-4
---

# KARN-W4-R3-CHART-FACTS-QUERY — Execution Brief

## §0 — Context

This is an autonomous Claude Code session. Read this entire brief before writing any code.
Execute §1 (pre-flight) before touching anything. Halt on any pre-flight failure.

Parent plan: `M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md §B3`. You are building the parametric
`chart_facts_query` tool — the most important retrieval addition in Wave 4. This tool turns
all 795 rows of chart_facts into a queryable surface for the classifier. No migrations needed;
the data is already there.

**Parallel context:** W4-R2 (C234-BUNDLE) runs concurrently and also modifies `index.ts`
and `router/prompt.ts`. Coordinate by appending only — never rewrite. If W4-R2's three tools
(kp_query, saham_query, divisional_query) already exist when you start, do not modify them.

---

## §1 — Pre-flight self-diagnostics

```bash
# PF.1 — Branch check
git branch --show-current
# Expected: redesign/r0-foundation. Any other → HALT.

# PF.2 — Working tree clean
git status --short
# Expected: clean or only may_touch files. Unexpected modifications → HALT.

# PF.3 — chart_facts total row count
psql "host=127.0.0.1 port=5433 dbname=amjis user=amjis-app" -c \
  "SELECT COUNT(*) FROM chart_facts WHERE is_stale=false;"
# Expected: ≥795. Record actual count.

# PF.4 — Full category inventory (establish what filters are valid)
psql "host=127.0.0.1 port=5433 dbname=amjis user=amjis-app" -c \
  "SELECT category, COUNT(*) FROM chart_facts WHERE is_stale=false
   GROUP BY category ORDER BY category;"
# Record all categories. This determines the category enum in ChartFactsQueryInput.

# PF.5 — Sample value_json shapes for key categories
psql "host=127.0.0.1 port=5433 dbname=amjis user=amjis-app" -c \
  "SELECT category, fact_id, value_json FROM chart_facts
   WHERE category IN ('shadbala','ashtakavarga_bav','planet','yoga','saham')
     AND is_stale=false
   ORDER BY category, fact_id LIMIT 10;"
# Record the JSON shapes. These determine rank_by field names and return type structure.

# PF.6 — Confirm shadbala has value_number for ranking
psql "host=127.0.0.1 port=5433 dbname=amjis user=amjis-app" -c \
  "SELECT fact_id, value_number, value_json->>'planet' AS planet
   FROM chart_facts WHERE category='shadbala' AND is_stale=false ORDER BY value_number DESC;"
# Expected: 14 rows (per W2-R2 verification). value_number should be shadbala total.

# PF.7 — TypeScript test baseline
cd platform && npx vitest run --reporter=verbose 2>&1 | tail -10
# Record pass/fail counts.

# PF.8 — Check if W4-R2 tools already exist
ls platform/src/lib/retrieve/kp_query.ts platform/src/lib/retrieve/saham_query.ts \
   platform/src/lib/retrieve/divisional_query.ts 2>/dev/null && echo "W4-R2 complete" || echo "W4-R2 pending"
# Note: regardless of result, do not touch those files.

# PF.9 — Check RETRIEVAL_TOOLS current count
grep -c "\.tool" platform/src/lib/retrieve/index.ts 2>/dev/null
# Baseline: 10 (or 13 if W4-R2 committed first). chart_facts_query will bring it to 11 or 14.
```

---

## §2 — Implementation

### §2.0 — Study the value_json shapes

**Critical first step:** Before writing any TypeScript, run PF.4 and PF.5 and study the
actual value_json shapes from the live DB. The types must match what's actually stored.

Key shapes to record (from W2-R2 verification — confirm these are correct):

```
shadbala:         {planet, components{}, total_rupas, rank}
ashtakavarga_bav: {planet, by_sign{}, total_bindus}
ashtakavarga_sav: {sign, house, sav_forensic, sav_jh}
ashtakavarga_pinda: {planet, pinda, shuddha_pinda}
aspect:           {type, from_sign, aspect_rays[]}
avastha:          {planet, role, baladi, deeptadi, lajjitadi}
chalit_shift:     {planet, rashi_house, chalit_house, shift}
bhava_bala:       {house, bhava_bala}
longevity_indicator: {system, value, interpretation}
yoga:             {name, planets, houses, classification}
planet (D1):      {planet, sign, house, abs_longitude, nakshatra, [nakshatra_pada?], retrograde, dignity}
saham:            {name, longitude, sign, house, nakshatra, meaning}
```

Adjust the TypeScript types below to match what PF.5 actually returns.

---

### §2.1 — chart_facts_query.ts

**Create `platform/src/lib/retrieve/chart_facts_query.ts`:**

```typescript
/**
 * MARSYS-JIS Stream B — Tool: chart_facts_query (M2-C.1)
 *
 * Parametric retrieval over chart_facts. This is the primary gateway for
 * all quantitative chart-fact queries: strengths, BAV bindus, placements,
 * sahams, yogas, aspects, longevity indicators, and more.
 *
 * chart_facts has 795 rows across 37 categories (post Wave 2–4 ETL).
 * This tool surfaces any subset of them via filter params.
 */

import crypto from 'crypto'
import { getDb } from '@/lib/db'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'chart_facts_query'
const TOOL_VERSION = '1.0'

// All valid chart_facts categories (37 post Wave 2 ETL)
export type ChartFactsCategory =
  | 'house' | 'dasha_chara' | 'planet' | 'dasha_vimshottari' | 'saham'
  | 'sensitive_point' | 'birth_metadata' | 'strength_extra' | 'yoga'
  | 'dasha_yogini' | 'deity_assignment' | 'shadbala' | 'ashtakavarga_sav'
  | 'kp_cusp' | 'navatara' | 'panchang' | 'cusp' | 'arudha_occupancy'
  | 'bhava_bala' | 'chandra_placement' | 'mrityu_bhaga' | 'longevity_indicator'
  | 'arudha' | 'aspect' | 'chalit_shift' | 'kp_planet' | 'special_lagna'
  | 'strength' | 'upagraha' | 'ashtakavarga_bav' | 'kakshya_zone'
  | 'mercury_convergence' | 'ashtakavarga_pinda' | 'ishta_kashta'
  | 'kp_significator' | 'varshphal' | 'avastha'

export type RankBy =
  | 'value_number'        // generic numeric ranking
  | 'total_rupas'         // shadbala total
  | 'total_bindus'        // ashtakavarga BAV total bindus
  | 'bhava_bala'          // bhava bala score
  | 'pinda'               // Pinda value
  | 'confidence'          // (not in chart_facts — ignore if specified)

export interface ChartFactsQueryInput {
  // Primary filter — which category of fact to retrieve
  category?: ChartFactsCategory | ChartFactsCategory[]

  // Dimension filters (ANDed together; all are optional)
  planet?: string              // e.g. 'Sun', 'Moon', 'Mars', 'Rahu', 'Ketu', 'Jupiter', 'Venus', 'Saturn', 'Mercury'
  house?: number               // 1-12
  sign?: string                // e.g. 'Aries', 'Taurus', ... 'Pisces'
  nakshatra?: string           // e.g. 'Ashwini', 'Rohini', 'Uttara Bhadrapada', ...
  nakshatra_pada?: 1 | 2 | 3 | 4
  divisional_chart?: string    // e.g. 'D1', 'D9', 'D10', 'D7', 'BIRTH'

  // Keyword search across value_text (case-insensitive partial match)
  // Useful for: saham_name='Vivaha', yoga_name='Sasha'
  keyword?: string

  // Ranking and limit
  rank_by?: RankBy             // sort descending by this field; default: no sort (DB order)
  limit?: number               // default: 20; max: 100
}

// Return shape for a single chart_facts row
export interface ChartFactsResult {
  fact_id: string
  category: string
  divisional_chart: string
  value_text: string | null
  value_number: number | null
  value_json: Record<string, unknown> | null
  source_section: string
}

function buildWhereClause(params: ChartFactsQueryInput): { where: string; args: unknown[] } {
  const conditions: string[] = ['is_stale = false']
  const args: unknown[] = []
  let idx = 1

  // Category filter
  if (params.category) {
    const cats = Array.isArray(params.category) ? params.category : [params.category]
    conditions.push(`category = ANY($${idx})`)
    args.push(cats)
    idx++
  }

  // Planet filter — check value_json->>'planet' OR fact_id contains planet name
  if (params.planet) {
    conditions.push(
      `(value_json->>'planet' ILIKE $${idx} OR fact_id ILIKE $${idx + 1})`
    )
    args.push(`%${params.planet}%`, `%${params.planet}%`)
    idx += 2
  }

  // House filter — value_json->>'house'
  if (params.house !== undefined) {
    conditions.push(`(value_json->>'house')::int = $${idx}`)
    args.push(params.house)
    idx++
  }

  // Sign filter — value_json->>'sign'
  if (params.sign) {
    conditions.push(`value_json->>'sign' ILIKE $${idx}`)
    args.push(`%${params.sign}%`)
    idx++
  }

  // Nakshatra filter — value_json->>'nakshatra'
  if (params.nakshatra) {
    conditions.push(`value_json->>'nakshatra' ILIKE $${idx}`)
    args.push(`%${params.nakshatra}%`)
    idx++
  }

  // Nakshatra pada filter (added by W4-R1 for planet rows)
  if (params.nakshatra_pada !== undefined) {
    conditions.push(`(value_json->>'nakshatra_pada')::int = $${idx}`)
    args.push(params.nakshatra_pada)
    idx++
  }

  // Divisional chart filter
  if (params.divisional_chart) {
    conditions.push(`divisional_chart = $${idx}`)
    args.push(params.divisional_chart)
    idx++
  }

  // Keyword search across value_text
  if (params.keyword) {
    conditions.push(
      `(value_text ILIKE $${idx} OR fact_id ILIKE $${idx + 1} OR value_json::text ILIKE $${idx + 2})`
    )
    args.push(`%${params.keyword}%`, `%${params.keyword}%`, `%${params.keyword}%`)
    idx += 3
  }

  return { where: conditions.join(' AND '), args }
}

function buildOrderBy(rank_by?: RankBy): string {
  if (!rank_by) return 'ORDER BY category, fact_id'

  // Map rank_by to actual SQL expressions
  const rankMap: Record<RankBy, string> = {
    value_number: 'ORDER BY value_number DESC NULLS LAST, fact_id',
    total_rupas:  'ORDER BY (value_json->>\'total_rupas\')::numeric DESC NULLS LAST, fact_id',
    total_bindus: 'ORDER BY (value_json->>\'total_bindus\')::numeric DESC NULLS LAST, fact_id',
    bhava_bala:   'ORDER BY (value_json->>\'bhava_bala\')::numeric DESC NULLS LAST, fact_id',
    pinda:        'ORDER BY (value_json->>\'pinda\')::numeric DESC NULLS LAST, fact_id',
    confidence:   'ORDER BY fact_id',  // not applicable; fall back to default
  }
  return rankMap[rank_by] ?? 'ORDER BY category, fact_id'
}

async function retrieve(plan: QueryPlan, params?: ChartFactsQueryInput): Promise<ToolBundle> {
  const start = Date.now()
  const db = getDb()

  // Extract chart_facts_query params from the QueryPlan if not passed directly
  // The classifier may embed them in plan.chart_facts_query
  const effectiveParams: ChartFactsQueryInput = {
    ...((plan as Record<string, unknown>).chart_facts_query as ChartFactsQueryInput | undefined),
    ...params,
  }

  const limit = Math.min(effectiveParams.limit ?? 20, 100)
  const { where, args } = buildWhereClause(effectiveParams)
  const orderBy = buildOrderBy(effectiveParams.rank_by)

  const sql = `
    SELECT
      fact_id,
      category,
      divisional_chart,
      value_text,
      value_number,
      value_json,
      source_section
    FROM chart_facts
    WHERE ${where}
    ${orderBy}
    LIMIT ${limit}
  `

  const rows: ChartFactsResult[] = await db.query(sql, args)

  const results: ToolBundleResult[] = rows.map((row) => ({
    content: JSON.stringify({
      fact_id: row.fact_id,
      category: row.category,
      divisional_chart: row.divisional_chart,
      value_text: row.value_text,
      value_number: row.value_number,
      data: row.value_json,
      source: row.source_section,
    }),
    source_canonical_id: 'FORENSIC',
    source_version: '8.0',
    confidence: 1.0,
    significance: 0.9,
  }))

  return {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: TOOL_NAME,
    tool_version: TOOL_VERSION,
    invocation_params: {
      category: effectiveParams.category,
      planet: effectiveParams.planet,
      house: effectiveParams.house,
      sign: effectiveParams.sign,
      nakshatra: effectiveParams.nakshatra,
      nakshatra_pada: effectiveParams.nakshatra_pada,
      divisional_chart: effectiveParams.divisional_chart,
      keyword: effectiveParams.keyword,
      rank_by: effectiveParams.rank_by,
      limit,
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
  description:
    'Parametric chart facts retrieval. Queries the chart_facts table (795 rows, 37 categories) ' +
    'with fine-grained filters. Use for: (1) Strength rankings — shadbala total, BAV bindus, ' +
    'bhava bala; (2) Specific fact lookup — a saham by name, a yoga, an aspect; (3) Placement ' +
    'retrieval — planets in a house, in a sign, in a nakshatra pada; (4) Divisional confirmation ' +
    '— D9/D10 placements; (5) Any quantitative chart fact not covered by a more specific tool. ' +
    'Preferred over saham_query/kp_query/divisional_query when multiple categories are relevant ' +
    'or when a ranking (rank_by) is needed.',
  retrieve,
}
```

---

### §2.2 — Type extensions

**In `platform/src/lib/router/types.ts`:** Add `chart_facts_query` field to `QueryPlan`:
```typescript
// In QueryPlan interface, add:
chart_facts_query?: import('@/lib/retrieve/chart_facts_query').ChartFactsQueryInput
```

**In `platform/src/lib/retrieve/types.ts`:** If `ChartFactsQueryInput` needs to be referenced
from types.ts, add a re-export. Otherwise leave types.ts minimal.

---

### §2.3 — Update index.ts

Append to `platform/src/lib/retrieve/index.ts`:
```typescript
// Wave 4 — M2-C1-CHART-FACTS-QUERY
import * as chartFactsQuery from './chart_facts_query'
// Add chartFactsQuery.tool to RETRIEVAL_TOOLS array
```

Follow the established pattern for extending the RETRIEVAL_TOOLS array.

---

### §2.4 — Classifier prompt guidance

Append to `platform/src/lib/router/prompt.ts`:

```
## Chart Facts Query Guidance (chart_facts_query tool)

chart_facts_query is the PRIMARY tool for quantitative chart-fact retrieval.
Use it (and populate chart_facts_query in the QueryPlan) for queries about:

**Strength rankings** (rank_by required):
- "Rank my planets by Shadbala" → category='shadbala', rank_by='total_rupas'
- "Which planets have highest ashtakavarga score?" → category='ashtakavarga_bav', rank_by='total_bindus'
- "Strongest house by bhava bala" → category='bhava_bala', rank_by='value_number'

**Specific quantitative lookups** (category + keyword or planet):
- "BAV of Mars in Capricorn" → category='ashtakavarga_bav', planet='Mars', sign='Capricorn'
- "Saturn SAV score in 6th house" → category='ashtakavarga_sav', house=6
- "Saham Vivaha" → category='saham', keyword='Vivaha'
- "Yoga register" → category='yoga'
- "Sasha Mahapurusha Yoga" → category='yoga', keyword='Sasha'
- "Moon's nakshatra pada" → category='planet', planet='Moon', divisional_chart='D1'
- "Longevity indicators" → category='longevity_indicator'
- "Upagrahas" → category='upagraha'
- "Mrityu Bhaga planets" → category='mrityu_bhaga'
- "Avastha of Saturn" → category='avastha', planet='Saturn'

**Placement queries**:
- "Planets in 7th house" → category='house', house=7 (OR category='planet', house=7)
- "What is in Capricorn?" → sign='Capricorn'
- "D9 placements" → divisional_chart='D9' (prefer divisional_query if single varga needed)

**Avoid chart_facts_query for**:
- MSR signal retrieval (use msr_sql)
- CGM graph traversal (use cgm_graph_walk)
- Pattern or cluster lookup (use pattern_register, cluster_atlas)
- Temporal / dasha queries (use temporal or msr_sql with temporal_activation filter)

Always set `limit` to a reasonable number (5–20). Set `rank_by` whenever ranking is implied.
```

---

### §2.5 — Tests (≥10 test cases)

**Create `platform/src/lib/retrieve/__tests__/chart_facts_query.test.ts`:**

The tests must cover the 10 key query patterns from the brief's scope summary.
Mock the DB client to return pre-canned rows for each test (follow msr_sql.test.ts mock pattern).

```typescript
// Required test cases (≥10):
describe('chart_facts_query', () => {
  // TC.1 — Shadbala ranking query
  it('returns shadbala rows sorted by total_rupas when rank_by=total_rupas', async () => {
    // Mock DB returns 14 shadbala rows; verify results.length == 14, tool_name == 'chart_facts_query'
  })

  // TC.2 — BAV bindu lookup with planet + sign filter
  it('filters by planet and sign for ashtakavarga_bav query', async () => {
    // Mock returns 1 row (Mars in Capricorn BAV); verify content includes 'Mars'
  })

  // TC.3 — Saham lookup by keyword
  it('returns Vivaha saham when keyword=Vivaha', async () => {
    // Mock returns 1 row; verify fact_id contains 'VIV' or value_text contains 'Vivaha'
  })

  // TC.4 — Yoga register (no filters)
  it('returns all yoga rows when category=yoga', async () => {
    // Mock returns 18 rows; verify all have category='yoga'
  })

  // TC.5 — House query (planets in house 7)
  it('returns house 7 entries when house=7', async () => {
    // Mock returns rows; verify all have house=7 in value_json or value_text
  })

  // TC.6 — Multiple categories (array)
  it('accepts array of categories', async () => {
    // params: {category: ['shadbala', 'bhava_bala']}; verify results from both categories
  })

  // TC.7 — nakshatra_pada filter
  it('filters by nakshatra_pada when provided', async () => {
    // params: {category: 'planet', nakshatra_pada: 2}; verify SQL includes pada condition
  })

  // TC.8 — limit respected
  it('respects limit param (defaults to 20, max 100)', async () => {
    // params: {limit: 5}; verify results.length <= 5
    // params: {limit: 200}; verify results.length <= 100 (capped)
  })

  // TC.9 — ToolBundle shape
  it('returns correctly shaped ToolBundle', async () => {
    // Verify: tool_bundle_id (uuid), tool_name='chart_facts_query', results array,
    // item_count matches results.length, latency_ms >= 0
  })

  // TC.10 — Empty result for impossible filter
  it('returns empty results for impossible filter without error', async () => {
    // params: {category: 'shadbala', planet: 'NonExistentPlanet'}
    // DB mock returns []; verify results.length == 0, no exception thrown
  })

  // TC.11 (bonus) — rank_by=total_bindus
  it('applies total_bindus ordering for ashtakavarga BAV query', async () => {
    // Verify ORDER BY clause includes total_bindus
  })

  // TC.12 (bonus) — keyword search hits value_text
  it('keyword search matches across value_text', async () => {
    // params: {keyword: 'Sasha'}; verify the SQL ILIKE condition is present
  })
})
```

**Mock pattern:** Study `msr_sql.test.ts` and follow exactly. If it uses `vi.mock('@/lib/db')`,
do the same. If it uses a jest mock, use the same jest mock approach. Do NOT introduce a new
mocking library.

---

## §3 — Acceptance criteria

### AC.1 — Branch state
`git branch --show-current` returns `redesign/r0-foundation`.

### AC.2 — chart_facts_query.ts created
`ls platform/src/lib/retrieve/chart_facts_query.ts` exits 0.

### AC.3 — Tool registered in RETRIEVAL_TOOLS
```bash
grep "chart_facts_query" platform/src/lib/retrieve/index.ts
```
Returns at least 2 lines (import + RETRIEVAL_TOOLS entry).

### AC.4 — QueryPlan type has chart_facts_query field
```bash
grep "chart_facts_query" platform/src/lib/router/types.ts
```
Returns ≥ 1 line.

### AC.5 — Classifier prompt has chart_facts_query guidance
```bash
grep "chart_facts_query" platform/src/lib/router/prompt.ts
```
Returns ≥ 5 lines (the guidance block).

### AC.6 — Shadbala ranking: returns correct rows
Using the live DB (or mock): retrieve() with `{category: 'shadbala', rank_by: 'total_rupas'}`
returns:
- `tool_name == 'chart_facts_query'`
- `results.length == 14` (14 shadbala rows in DB post W2-R2)
- First result's content has the highest total_rupas planet

### AC.7 — Saham keyword: returns Vivaha saham
retrieve() with `{category: 'saham', keyword: 'Vivaha'}` returns ≥ 1 result whose
content includes 'Vivaha' (case-insensitive).

### AC.8 — Yoga query: returns ≥10 yoga rows
retrieve() with `{category: 'yoga'}` returns results.length ≥ 10 (DB has 18 yoga rows).

### AC.9 — Limit is respected and capped at 100
retrieve() with `{limit: 5}` returns results.length ≤ 5.
retrieve() with `{limit: 500}` does NOT crash and returns ≤ 100 results.

### AC.10 — TypeScript compiles clean
```bash
cd platform && npx tsc --noEmit 2>&1 | grep -v "node_modules" | head -20
```
No new TypeScript errors from chart_facts_query.ts or associated type additions.

### AC.11 — ≥10 tests passing, no new failures
```bash
cd platform && npx vitest run src/lib/retrieve/__tests__/chart_facts_query.test.ts
```
All ≥10 tests pass. Total test suite: no regressions vs pre-flight baseline.

### AC.12 — Cloud Run revision updated with tool in production
```bash
bash platform/scripts/cloud_build_submit.sh
```
New revision serving 100%. `chart_facts_query` is imported and available at runtime.
Verify with a smoke query that the tool appears in RETRIEVAL_TOOLS via:
```bash
curl -s $APP_URL/api/tools | jq '.[] | select(.name=="chart_facts_query")'
```
(If no /api/tools endpoint exists, verify via the Cloud Run logs that the import succeeded.)

---

## §4 — Halt conditions

Halt immediately if:

1. **PF.1 fails:** Branch not `redesign/r0-foundation`.
2. **PF.3 fails:** chart_facts has 0 rows. ETL did not run; tool has nothing to query.
3. **DB client pattern unclear:** If the project has no obvious `getDb()` or `sql` pattern
   after checking msr_sql.ts — HALT with a description of what you found. Do not invent a
   DB client from scratch.
4. **types.ts conflict with W4-R2:** If W4-R2 already added a `chart_facts_query` field to
   QueryPlan with a conflicting type — do NOT silently overwrite. HALT and describe the conflict.
5. **Test count regression > 5 new failures:** Halt before deploy.
6. **TypeScript errors in existing (pre-existing) files caused by type additions:** If adding
   `chart_facts_query` to QueryPlan causes cascade failures in existing files — HALT and report.
   The type should be optional (`?:`) so it cannot break existing callers.

Non-halting:
- W4-R2's tools already exist in index.ts (good — append yours without touching theirs)
- Some AC.6/7/8 row counts differ slightly from expected (note in closing summary; counts
  may vary by a few rows due to is_stale filtering or run-order effects — ±3 is acceptable)

---

## §5 — Closing summary template

```
SESSION CLOSE — M2_C1_CHART_FACTS_QUERY — <ISO timestamp>

ACs result:
  AC.1:  <PASS|FAIL> — branch check
  AC.2:  <PASS|FAIL> — chart_facts_query.ts created
  AC.3:  <PASS|FAIL> — tool in RETRIEVAL_TOOLS
  AC.4:  <PASS|FAIL> — QueryPlan type extended
  AC.5:  <PASS|FAIL> — classifier prompt updated
  AC.6:  <PASS|FAIL> — shadbala ranking returns 14 rows
  AC.7:  <PASS|FAIL> — saham Vivaha keyword lookup
  AC.8:  <PASS|FAIL> — yoga query returns ≥10 rows
  AC.9:  <PASS|FAIL> — limit respected + capped
  AC.10: <PASS|FAIL> — TypeScript compiles clean
  AC.11: <PASS|FAIL> — ≥10 tests passing, no regressions
  AC.12: <PASS|FAIL> — Cloud Run deployed, tool live

Files created/modified:
  platform/src/lib/retrieve/chart_facts_query.ts (CREATE)
  platform/src/lib/retrieve/__tests__/chart_facts_query.test.ts (CREATE)
  platform/src/lib/retrieve/index.ts (modified — 1 import + 1 RETRIEVAL_TOOLS entry)
  platform/src/lib/router/prompt.ts (modified — chart_facts_query guidance block appended)
  platform/src/lib/router/types.ts (modified — chart_facts_query field added to QueryPlan)
  [platform/src/lib/retrieve/types.ts] (modified if re-export added, else unchanged)
  [platform/src/lib/db/types.ts] (modified if ChartFactsRow added, else unchanged)

DB changes: None (chart_facts is read-only for this session)

Cloud Run: <prior revision> → <new revision>

Tests:
  Before: <X passed / Y failed>
  After: <X' passed / Y' failed>
  Delta: <new failures count>

Value_json shape findings from PF.5:
  shadbala: <record what you actually found>
  ashtakavarga_bav: <record what you actually found>
  [etc. for any categories where shape differed from brief's expectation]

Halt-and-report cases: <none | description>

Brief status: <COMPLETE | HALTED_AT_AC.N>
Next brief in stream: M2_C5_TEMPORAL_EXTENSION (W5-R1) — after Wave 4 closes
```

After emitting the closing summary, append a session entry to
`00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md` per protocol §3.1, and flip
`status: COMPLETE` in this brief's frontmatter.

---

*End of CLAUDECODE_BRIEF_M2_C1_CHART_FACTS_QUERY v1.0 (authored 2026-04-30 — Wave 3 close).*
