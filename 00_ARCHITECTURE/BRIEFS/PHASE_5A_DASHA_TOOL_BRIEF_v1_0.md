---
canonical_id: PHASE_5A_DASHA_TOOL_BRIEF
version: 1.0
status: AUTHORED_READY_TO_EXECUTE
campaign: PHASE_5_DASHA_CORRECTNESS
sub_phase: 5A
authored_on: 2026-05-19
estimated_sessions: 1-2
two_stream_branch: analysis/backend-data-pipeline-perf-audit
depends_on: none (Phase 4 — bd41f13 / c63ef9f / abab885 / d7ec853 — must be on main but no direct dependency)
---

# §5A — `query_dasha_periods` Tool + R-DA Planner Rule + Baseline Audit

## §1 Scope

The Vimshottari dasha schedule lives in `chart_facts` as 50 `category='dasha_vimshottari'` rows covering 1984-02-05 → 2060-08-21 (Mercury MD → Ketu MD → Venus MD → Sun MD). The data is correct; the planner can't see it. §5A makes it reachable.

What ships:

1. **Stage 0 — Baseline audit** measurement: read recent `audit_events` rows, extract dasha-related synthesis claims, sample 20, count wrong-next-MD errors. Emit `DASHA_BASELINE_AUDIT_v1_0.md` artifact recording the pre-campaign failure rate.

2. **`chart_facts_query` RCS + impl extension**: advertise `dasha_vimshottari` / `dasha_yogini` / `dasha_chara` categories with optimal patterns. Extend TS query builder to support `as_of_date` (returns row where `start_date ≤ d < end_date`) and `from_date` / `to_date` (range filter).

3. **`query_dasha_periods` retrieval tool** — 30th tool. Surgical dasha surface with system / level / as_of_date / next_count / prev_count / md_lord / ad_lord / from_date / to_date / limit params. Default empty params returns today's active chain + next 3 MDs. Read-through to `chart_facts` table; no new migration.

4. **R-DA (Dasha Anchor) planner rule** in PLANNER_PROMPT_v2_0.md. Fires `query_dasha_periods` for any query mentioning dasha terminology. Priority 1 for explicit dasha queries; priority 2 alongside R-TC for general predictive. §4.28 few-shot example demonstrates R-DA on a "what's my next MD?" query.

5. **Golden set extension**: GT.083 (current MD), GT.084 (next MD — the canonical failure case), GT.085 (specific lord history), GT.086 (NEGATIVE — natal MD-significance via chart_facts_query + msr_sql, not query_dasha_periods).

6. **Planner-only smoke test** + paired regression baseline.

What does NOT ship (deferred to §5B / §5C):

- Synthesis prompt DASHA DISCIPLINE GATE (§5B).
- `checkpoint_dasha.ts` post-synthesis validator (§5C).
- Yogini/Chara/Narayana validator coverage (validator stays Vimshottari-only initially per approved decision §6.4).

## §2 What you must NOT do

- **No branch other than `analysis/backend-data-pipeline-perf-audit`**.
- **No Chat V2 files**.
- **No autonomous `npm run answer:eval`**. Pre-commit gates only.
- **No new migration** — `chart_facts` already has the 50 `dasha_vimshottari` rows.
- **No edits to `single_model_strategy.ts` checkpoint orchestration** — that's §5C scope.
- **No edits to synthesis prompt templates** — that's §5B scope.
- **No autonomous DB writes** — Stage 0 is read-only against `audit_events`.

## §3 Approved decisions to honor (re-stated from dossier §6)

1. Validator behavior — §5C scope; not §5A.
2. Synthesis gate scope — §5B scope; not §5A.
3. **`query_dasha_periods` as separate tool** (not folded into `chart_facts_query`).
4. **Multi-system from day one**: `system: 'vimshottari' | 'yogini' | 'chara'` param accepted on day one. All three categories exist in `chart_facts`.
5. **Baseline audit as Stage 0**: measure pre-campaign rate before any code lands.

## §4 Stages

### §4.0 Stage 0 — Baseline audit (read-only, ~15 min)

Before any code change, measure the failure rate. The brief writes `00_ARCHITECTURE/DASHA_BASELINE_AUDIT_v1_0.md` recording the methodology + result.

```bash
# Run from analysis worktree with Cloud SQL proxy on 5433 + DATABASE_URL set.
# Read audit_events for recent (last 30 days) responses that mention dasha
# terminology in the response_text.

psql "$DATABASE_URL" -A -t -F $'\t' -c "
  SELECT
    audit_id,
    query_text,
    SUBSTRING(response_text FROM '(?i)\\m(mahadasha|MD|antardasha|AD|vimshottari|next.{0,30}dasha)\\M.{0,200}')
      AS response_excerpt,
    created_at
  FROM audit_events
  WHERE created_at > NOW() - INTERVAL '30 days'
    AND response_text ~* '(mahadasha|vimshottari|antardasha|\\mMD\\M|\\mAD\\M)'
  ORDER BY created_at DESC
  LIMIT 50;
" > /tmp/dasha_audit_sample.tsv

wc -l /tmp/dasha_audit_sample.tsv
head -5 /tmp/dasha_audit_sample.tsv
```

Then **manually inspect 20 of those rows** (read each response excerpt) and classify each as:

| Class | Meaning |
|---|---|
| `correct_current_md` | Synthesis correctly named Mercury MD as current |
| `correct_next_md` | Synthesis correctly named Ketu MD as next |
| `wrong_next_md_saturn` | Synthesis claimed Saturn MD next (the canonical failure) |
| `wrong_next_md_other` | Other wrong next lord (Jupiter, Sun, etc.) |
| `wrong_ad_under_md` | MD correct but wrong AD lord/dates |
| `no_dasha_claim` | Response mentioned dasha but didn't make a sequence claim |
| `pre_phase4_skip` | Response predates 2026-05-19 — out of measurement window |

Author `00_ARCHITECTURE/DASHA_BASELINE_AUDIT_v1_0.md` with:

```markdown
---
canonical_id: DASHA_BASELINE_AUDIT
version: 1.0
status: BASELINE — pre-Phase-5 measurement
captured_on: <date>
method: manual classification of 20 audit_events rows from last 30 days
sample_size: <N actual — may be less than 20 if not enough audit data>
---

# Dasha Baseline Audit

Pre-§5A measurement of dasha-correctness failure rate.

## Method
[describe — SQL query above, manual classification of N rows]

## Classification

| Class | Count | % |
|---|---|---|
| correct_current_md | A | ... |
| correct_next_md | B | ... |
| wrong_next_md_saturn | C | ... |
| wrong_next_md_other | D | ... |
| wrong_ad_under_md | E | ... |
| no_dasha_claim | F | ... |

## Failure rate
Wrong-next-MD claims = (C + D) / (B + C + D) = X%

## Sample-size caveat
N=20 is small. The post-campaign measurement (after §5C closes) will use
the same methodology against the post-Phase-5 audit_events; the delta is
the success metric.
```

If the `audit_events` table has fewer than 5 dasha-mentioning rows in the last 30 days (i.e., the eval discipline kept production traffic minimal), record `sample_size: insufficient — defer baseline to post-§5C measurement only` and proceed to Stage 1 without blocking.

### §4.1 Stage 1 — Extend `chart_facts_query` RCS + impl

**RCS update** in `platform/src/lib/router/retrieval_capability_spec.ts`:

Update the `chart_facts_query` entry's description, supported_params, and optimal_patterns to include dasha categories.

```ts
description:
  'PRIMARY tool for quantitative chart-fact retrieval — 795 chart_facts rows ' +
  'across 37 categories: shadbala, ashtakavarga (BAV/SAV/Pinda), bhava_bala, ' +
  'sahams, yogas, longevity indicators, upagrahas, mrityu_bhaga, avastha, ' +
  'planet placements, house contents, AND DASHA SCHEDULES ' +
  '(dasha_vimshottari with 50 rows covering 1984-2060, dasha_yogini, ' +
  'dasha_chara). Use for any strength ranking, BAV bindu count, yoga register ' +
  'lookup, quantitative placement question, OR specific historical dasha ' +
  'period lookup. For "what is the current/next dasha?" semantic queries, ' +
  'prefer query_dasha_periods (semantically richer; surfaces next_count + ' +
  'prev_count + active-chain shortcuts).',
supported_params:
  '{ category?: string|string[] (e.g. "shadbala", "ashtakavarga_bav", ' +
  '"bhava_bala", "saham", "yoga", "planet", "house", "longevity_indicator", ' +
  '"upagraha", "mrityu_bhaga", "avastha", "dasha_vimshottari", "dasha_yogini", ' +
  '"dasha_chara"); planet?: string; house?: number; sign?: string; ' +
  'nakshatra?: string; divisional_chart?: string ("D1".."D60"); keyword?: ' +
  'string; rank_by?: string; as_of_date?: YYYY-MM-DD (filters dasha rows ' +
  'where start_date <= d < end_date); from_date?: YYYY-MM-DD (range start); ' +
  'to_date?: YYYY-MM-DD (range end); limit?: number (default 10) }',
optimal_patterns: [
  'Strength ranking: {category:"shadbala", rank_by:"total_rupas", limit:9}',
  'BAV by planet+sign: {category:"ashtakavarga_bav", planet:"Mars", sign:"Capricorn"}',
  'Yoga register: {category:"yoga"}',
  'Saham lookup: {category:"saham", keyword:"Vivaha"}',
  'House contents: {category:"house", house:7}',
  'Specific dasha row: {category:"dasha_vimshottari", as_of_date:"2008-04-15"} (returns Mercury MD/Mars AD-equivalent for that date)',
  'Historical MD lookup: {category:"dasha_vimshottari", keyword:"Saturn"} (returns rows where md_lord=Saturn)',
],
```

**TS implementation update** in `platform/src/lib/retrieve/chart_facts_query.ts`:

Extend `ChartFactsQueryInput` interface with `as_of_date?: string` + `from_date?: string` + `to_date?: string`. In `buildWhereClause`, when the category is one of the dasha categories AND `as_of_date` is set:

```ts
if (p.as_of_date) {
  conditions.push(
    `(value_json->>'start_date')::date <= $${idx}::date AND ` +
    `(value_json->>'end_date')::date > $${idx + 1}::date`
  )
  args.push(p.as_of_date, p.as_of_date)
  idx += 2
}
if (p.from_date) {
  conditions.push(`(value_json->>'end_date')::date >= $${idx}::date`)
  args.push(p.from_date)
  idx++
}
if (p.to_date) {
  conditions.push(`(value_json->>'start_date')::date <= $${idx}::date`)
  args.push(p.to_date)
  idx++
}
```

Add 3 unit tests covering each new filter.

### §4.2 Stage 2 — Build `query_dasha_periods` (30th retrieval tool)

**New file** `platform/src/lib/retrieve/query_dasha_periods.ts`. Model after the M8-G wrapper pattern + `query_signal_state` for the date-range semantics. Imports nothing exotic.

```ts
/**
 * MARSYS-JIS Retrieval tool — query_dasha_periods (Phase 5A)
 *
 * Surgical dasha-schedule lookup. Reads chart_facts rows where category is
 * one of the three dasha categories (vimshottari / yogini / chara) and
 * value_json carries {md_lord, ad_lord, start_date, end_date}.
 *
 * 50 dasha_vimshottari rows (1984-02-05 → 2060-08-21). Coverage: Jupiter
 * MD (partial first) → Saturn MD → Mercury MD (current) → Ketu MD (next) →
 * Venus MD → Sun MD.
 *
 * Default empty params returns: today's active 5-level chain (M/A row +
 * synthesizes "active row at this moment") PLUS the next 3 MDs. This is
 * the "what's my dasha situation?" one-tool-call answer.
 *
 * Distinct from chart_facts_query: chart_facts_query handles 37 categories
 * including dasha; this tool is semantically dasha-only with helpers for
 * next_count / prev_count / active-chain shortcuts that the planner can
 * compose without needing to assemble date arithmetic itself.
 *
 * Distinct from temporal.dasha_context_required: that calls /dasha_chain
 * sidecar which returns the active 5-level chain at ONE date only. This
 * tool returns the schedule from the canonical chart_facts table, with
 * full upcoming + historical visibility.
 */

import crypto from 'crypto'
import { getStorageClient } from '@/lib/storage'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'query_dasha_periods'
const TOOL_VERSION = '1.0.0'

type DashaSystem = 'vimshottari' | 'yogini' | 'chara'
type DashaLevel = 'M' | 'A' | 'P' | 'all'
const SYSTEM_CATEGORY: Record<DashaSystem, string> = {
  vimshottari: 'dasha_vimshottari',
  yogini: 'dasha_yogini',
  chara: 'dasha_chara',
}

export interface QueryDashaPeriodsInput {
  /** Defaults to 'vimshottari'. */
  system?: DashaSystem
  /** Default 'all'. Currently chart_facts rows are MD/AD pairs; treat 'M' as md_lord-only deduplication. */
  level?: DashaLevel
  /** ISO date. Returns row whose start_date <= d < end_date. */
  as_of_date?: string
  /** If set with as_of_date or alone (then defaults to today), returns next N MD-transition rows after that date. */
  next_count?: number
  /** Same shape as next_count, but for previous MD transitions before the date. */
  prev_count?: number
  /** Filter to MD lord (canonical name; case-insensitive ILIKE). */
  md_lord?: string
  /** Filter to AD lord. */
  ad_lord?: string
  /** Range start. */
  from_date?: string
  /** Range end. */
  to_date?: string
  /** Max rows. Default 30, max 100. */
  limit?: number
}

interface DashaRow {
  fact_id: string
  category: string
  value_json: {
    md_lord: string
    ad_lord: string
    start_date: string
    end_date: string
  }
  source_section: string | null
}

async function retrieve(plan: QueryPlan, params?: Record<string, unknown>): Promise<ToolBundle> {
  const start = Date.now()
  try {
    return await retrieveImpl(plan, params, start)
  } catch (err) {
    void writeToolExecutionLog({
      query_id: plan.query_plan_id,
      tool_name: TOOL_NAME,
      params_json: (params ?? null) as Record<string, unknown> | null,
      status: 'error',
      rows_returned: 0,
      latency_ms: Date.now() - start,
      token_estimate: 0,
      data_asset_id: 'CHART_FACTS_DASHA',
      error_code: err instanceof Error ? err.message : String(err),
      served_from_cache: false,
      fallback_used: false,
    })
    throw err
  }
}

async function retrieveImpl(
  plan: QueryPlan,
  params: Record<string, unknown> | undefined,
  start: number,
): Promise<ToolBundle> {
  const input = (params ?? {}) as QueryDashaPeriodsInput
  const system: DashaSystem = input.system ?? 'vimshottari'
  const category = SYSTEM_CATEGORY[system]
  const limit = Math.max(1, Math.min(100, input.limit ?? 30))
  const today = new Date().toISOString().slice(0, 10)

  // Build WHERE clause
  const conditions: string[] = ['is_stale = false', 'category = $1']
  const args: unknown[] = [category]
  let idx = 2

  if (input.as_of_date) {
    conditions.push(
      `(value_json->>'start_date')::date <= $${idx}::date AND ` +
      `(value_json->>'end_date')::date > $${idx + 1}::date`
    )
    args.push(input.as_of_date, input.as_of_date)
    idx += 2
  }

  if (input.md_lord) {
    conditions.push(`value_json->>'md_lord' ILIKE $${idx}`)
    args.push(`%${input.md_lord}%`)
    idx++
  }

  if (input.ad_lord) {
    conditions.push(`value_json->>'ad_lord' ILIKE $${idx}`)
    args.push(`%${input.ad_lord}%`)
    idx++
  }

  // Range OR next/prev count logic — they compose
  let anchorDate: string | undefined
  if (input.from_date) {
    conditions.push(`(value_json->>'end_date')::date >= $${idx}::date`)
    args.push(input.from_date)
    idx++
  } else if (input.next_count) {
    anchorDate = input.as_of_date ?? today
    conditions.push(`(value_json->>'start_date')::date >= $${idx}::date`)
    args.push(anchorDate)
    idx++
  } else if (input.prev_count) {
    anchorDate = input.as_of_date ?? today
    conditions.push(`(value_json->>'end_date')::date <= $${idx}::date`)
    args.push(anchorDate)
    idx++
  }

  if (input.to_date) {
    conditions.push(`(value_json->>'start_date')::date <= $${idx}::date`)
    args.push(input.to_date)
    idx++
  }

  // When level='M', deduplicate to one row per md_lord (the first AD row in each MD cluster).
  // Otherwise return all matching rows.
  const orderDir = input.prev_count ? 'DESC' : 'ASC'
  let actualLimit = limit
  if (input.next_count) actualLimit = Math.min(limit, input.next_count * 9)  // 9 ADs per MD
  if (input.prev_count) actualLimit = Math.min(limit, input.prev_count * 9)

  const sql = `
    SELECT fact_id, category, value_json, source_section
    FROM chart_facts
    WHERE ${conditions.join(' AND ')}
    ORDER BY (value_json->>'start_date')::date ${orderDir}
    LIMIT ${actualLimit}
  `

  const storage = getStorageClient()
  const result = await storage.query(sql, args)
  const rows = result.rows as DashaRow[]

  // Level filter (post-SQL because dedup is cleaner in TS)
  let filteredRows = rows
  if (input.level === 'M') {
    // Deduplicate by md_lord — first row per cluster
    const seenMd = new Set<string>()
    filteredRows = rows.filter(r => {
      const key = `${r.value_json.md_lord}-${r.value_json.start_date.slice(0, 4)}`
      if (seenMd.has(key)) return false
      // Heuristic: AD row where ad_lord == md_lord is the start of each MD cluster
      if (r.value_json.ad_lord === r.value_json.md_lord) {
        seenMd.add(key)
        return true
      }
      return false
    })
  }

  // Cap next_count / prev_count to N MD clusters (each ~9 AD rows)
  if (input.next_count) {
    const clusters: Set<string> = new Set()
    filteredRows = filteredRows.filter(r => {
      const k = r.value_json.md_lord + r.value_json.start_date.slice(0, 4)
      clusters.add(k)
      return clusters.size <= input.next_count!
    })
  }

  const results: ToolBundleResult[] = filteredRows.length > 0
    ? filteredRows.map(r => ({
        content: JSON.stringify({
          fact_id: r.fact_id,
          system,
          level: r.value_json.ad_lord === r.value_json.md_lord ? 'M_start' : 'A',
          md_lord: r.value_json.md_lord,
          ad_lord: r.value_json.ad_lord,
          start_date: r.value_json.start_date,
          end_date: r.value_json.end_date,
          source_section: r.source_section,
        }),
        source_canonical_id: 'FORENSIC',
        source_version: '8.0',
        confidence: 1.0,
        significance: 1.0,
      }))
    : [{
        content: JSON.stringify({
          note: `No ${category} rows match the given filters. Available date range: 1984-02-05 to 2060-08-21.`,
          params: input,
        }),
        source_canonical_id: 'CHART_FACTS_DASHA',
        source_version: '1.0',
        confidence: 0,
        significance: 0,
      }]

  const result_hash =
    'sha256:' +
    crypto
      .createHash('sha256')
      .update(JSON.stringify(results.map(r => r.content.slice(0, 80)).sort()))
      .digest('hex')

  const bundle: ToolBundle = {
    tool_bundle_id: crypto.randomUUID(),
    tool_name: TOOL_NAME,
    tool_version: TOOL_VERSION,
    invocation_params: { ...input, system, limit: actualLimit },
    results,
    served_from_cache: false,
    latency_ms: Date.now() - start,
    result_hash,
    schema_version: '1.0',
  }

  void writeToolExecutionLog({
    query_id: plan.query_plan_id,
    tool_name: TOOL_NAME,
    params_json: input as Record<string, unknown>,
    status: 'success',
    rows_returned: filteredRows.length,
    latency_ms: bundle.latency_ms,
    token_estimate: Math.ceil(JSON.stringify(results).length / 4),
    data_asset_id: 'CHART_FACTS_DASHA',
    error_code: null,
    served_from_cache: false,
    fallback_used: filteredRows.length === 0,
  })

  return bundle
}

export const tool: RetrievalTool = {
  name: TOOL_NAME,
  version: TOOL_VERSION,
  description:
    'Surgical Vimshottari / Yogini / Chara dasha schedule lookup. Reads ' +
    'chart_facts dasha rows (50 Vimshottari rows covering 1984-02-05 → ' +
    '2060-08-21) with semantic helpers for active-chain / next-N / prev-N / ' +
    'specific-lord queries. Default empty params returns today\'s active ' +
    'row plus next 3 MDs.',
  retrieve,
}
```

### §4.3 Stage 3 — Registry updates (mirror Phase 4 pattern)

- `platform/src/lib/retrieve/index.ts`: import + append `queryDashaPeriods.tool` to `RETRIEVAL_TOOLS` array.
- `platform/src/lib/router/retrieval_capability_spec.ts`: append `query_dasha_periods` entry (use the body below) + append to `RETRIEVAL_CAPABILITY_SPEC` array.
- `platform/src/lib/trace/types.ts`: append `'query_dasha_periods'` to `ALL_21_RETRIEVAL_TOOLS`; literal count 29 → 30; update comment.

**RCS entry body**:

```ts
const query_dasha_periods: RetrievalCapabilityEntry = {
  tool_name: 'query_dasha_periods',
  description:
    'Surgical dasha schedule lookup (Vimshottari / Yogini / Chara). Reads ' +
    'chart_facts dasha rows with semantic helpers for active-chain / next-N / ' +
    'prev-N / specific-lord queries. Default empty params returns today\'s ' +
    'active chain row + next 3 MD-transitions. CANONICAL SURFACE for any ' +
    'query asking about current / next / upcoming / previous dasha periods. ' +
    'Pairs with R-DA planner rule. Distinct from temporal.dasha_context_required ' +
    '(which returns only the active 5-level chain at one date via sidecar); ' +
    'this tool surfaces the full schedule from chart_facts with multi-MD ' +
    'visibility.',
  data_surface:
    'L1 — chart_facts table (50 dasha_vimshottari rows covering 1984-02-05 → ' +
    '2060-08-21 = DSH.V.001 through DSH.V.050+, plus dasha_yogini and ' +
    'dasha_chara categories). value_json: {md_lord, ad_lord, start_date, end_date}. ' +
    'Source: FORENSIC §5.1 (Lahiri sidereal, GAP.09 resolved — FORENSIC dates ' +
    'are canonical over JH dates).',
  supported_params:
    '{ system?: "vimshottari"|"yogini"|"chara" (default vimshottari); ' +
    'level?: "M"|"A"|"P"|"all" (default all; "M" deduplicates to one row per MD cluster); ' +
    'as_of_date?: YYYY-MM-DD (returns active row where start_date <= d < end_date); ' +
    'next_count?: number (returns next N MD transitions after as_of_date or today); ' +
    'prev_count?: number (returns prev N MD transitions before as_of_date or today); ' +
    'md_lord?: string (filter by MD lord, ILIKE); ' +
    'ad_lord?: string (filter by AD lord, ILIKE); ' +
    'from_date?: YYYY-MM-DD; to_date?: YYYY-MM-DD; ' +
    'limit?: number (default 30, max 100) }',
  optimal_patterns: [
    'Current dasha snapshot: {} (no params; returns today\'s active row + next 3 MDs)',
    'What is my next MD?: {level:"M", next_count:1}',
    'Specific date lookup: {as_of_date:"2008-04-15"} (returns the MD/AD running at marriage)',
    'All Mercury MD rows: {md_lord:"Mercury"} (9 ADs under Mercury MD)',
    'Historical MD scan: {level:"M", from_date:"1984-02-05", to_date:"2030-01-01"}',
    'Yogini schedule: {system:"yogini", next_count:3}',
  ],
  cost_tier: 'low',
  requires_temporal: true,
}
```

### §4.4 Stage 4 — R-DA planner rule + §4.28 few-shot

Append to `00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md` §3, after R-TE (the Phase 4D rule, before "Style rules"):

```
R-DA. DASHA ANCHOR: Attach `query_dasha_periods` to tool_calls for any query
     referencing Vimshottari, Yogini, or Chara dasha periods. The schedule
     lives in chart_facts; the canonical 50-row FORENSIC §5.1 table is
     reachable through this single tool — synthesis MUST NOT extrapolate
     dasha sequences from pretrained knowledge.

     Triggers:
       (a) Mahadasha / MD / Vimshottari / current dasha / next dasha /
           upcoming dasha / previous dasha / which dasha
       (b) Antardasha / AD / Pratyantardasha / PD / Sookshma / Prana
       (c) A specific dasha lord by name in temporal context
           ("when is my Saturn dasha", "Mars antardasha")
       (d) Yogini, Chara, or Narayana dasha system names

     Priority:
       - Pure dasha-lookup query → priority 1
       - Predictive query mentioning dasha as a timing layer → priority 1
       - General predictive (R-TC fires) → priority 2

     Param selection:
       - "current / now / today" → {} (no params; default returns active row + next 3 MDs)
       - "next" / "upcoming" → {level:"M", next_count:1}
       - "previous / past" → {level:"M", prev_count:1}
       - Specific date → {as_of_date:"YYYY-MM-DD"}
       - Specific lord → {md_lord:"<lord>"}
       - Date range → {from_date:"...", to_date:"..."}

     Exclusions:
       - Pure natal MD-lord-significance query ("what does my Mercury MD lord
         mean for my career") goes through chart_facts_query + msr_sql (the
         natal karaka interpretation). R-DA still attaches at priority 3 for
         cross-reference (date anchor) but the natal layer is the answer.
       - Multi-school triangulation queries (R31/R32 STOP at step 5).
```

Append §4.28 few-shot example:

```markdown
### 4.28 R-DA dasha anchor — next MD query

Query: "What's my next mahadasha?"

{
  "query_class": "factual",
  "query_intent_summary": "Next Vimshottari MD transition from today.",
  "asset_bundle": [
    { "asset_id": "FORENSIC", "priority": 1, "reason": "§5.1 dasha schedule." }
  ],
  "tool_calls": [
    { "tool_name": "query_dasha_periods", "params": {"level":"M","next_count":1}, "token_budget": 300, "priority": 1, "reason": "R-DA: next MD lookup via chart_facts." }
  ],
  "synthesis_guidance": "Cite the DSH.V.NNN fact_id from the result. Format: 'next MD is <lord> (→ DSH.V.NNN, start_date to end_date)'. Do NOT extrapolate from pretrained Vimshottari knowledge.",
  "expected_output_shape": "single_answer",
  "history_mode": "synthesized",
  "planets": [],
  "houses": [],
  "domains": [],
  "forward_looking": true,
  "prior_turn_relevance": { "used": 0, "reason": "Independent factual lookup.", "mode": "independent" }
}
```

### §4.5 Stage 5 — Golden set + regression baseline + smoke

Append to `platform/tests/eval/planner_golden_set.json`:

```json
{
  "id": "GT.083",
  "query": "What's my current mahadasha?",
  "query_class": "factual",
  "required_tools": ["query_dasha_periods"],
  "forbidden_tools": ["vector_search", "pattern_register"],
  "asset_bundle_must_include": ["FORENSIC"],
  "planets": [],
  "domains": [],
  "forward_looking": false,
  "notes": "R-DA + R-FACT. Empty params return today's active row + next 3 MDs. msr_sql is NOT required (this is a pure schedule lookup, not natal interpretation)."
},
{
  "id": "GT.084",
  "query": "What is my next mahadasha after Mercury?",
  "query_class": "factual",
  "required_tools": ["query_dasha_periods"],
  "forbidden_tools": ["vector_search", "pattern_register", "msr_sql"],
  "asset_bundle_must_include": ["FORENSIC"],
  "planets": [],
  "domains": [],
  "forward_looking": true,
  "notes": "R-DA canonical failure-case test. CORRECT answer must cite Ketu MD via DSH.V.024+. msr_sql FORBIDDEN here — would surface signals associated with Mercury, not the schedule lookup. This is THE test that the campaign is designed to fix."
},
{
  "id": "GT.085",
  "query": "When was my Saturn mahadasha?",
  "query_class": "factual",
  "required_tools": ["query_dasha_periods"],
  "forbidden_tools": ["vector_search"],
  "asset_bundle_must_include": ["FORENSIC"],
  "planets": ["Saturn"],
  "domains": [],
  "forward_looking": false,
  "notes": "R-DA with md_lord='Saturn' filter. Returns DSH.V.006-014 (Saturn MD 1991-2010). NEGATIVE for R7c — no transit ban issue since not predictive."
},
{
  "id": "GT.086",
  "query": "What does it mean that my current dasha lord is Mercury?",
  "query_class": "interpretive",
  "required_tools": ["msr_sql", "chart_facts_query"],
  "forbidden_tools": [],
  "asset_bundle_must_include": ["FORENSIC", "MSR"],
  "planets": ["Mercury"],
  "domains": [],
  "forward_looking": false,
  "notes": "NEGATIVE for R-DA pure-lookup path. This is natal interpretation of MD-lord significance, NOT a schedule query. query_dasha_periods MAY attach at priority 3 for date anchor, but msr_sql + chart_facts_query are the primary surfaces. Tests that R-DA doesn't over-fire on interpretive queries."
}
```

Pair with `platform/tests/eval/fixtures/regression_baseline.json` extension (4 new entries).

Author planner-only smoke at `platform/tests/eval/r_da_dasha_anchor_smoke.ts` mirroring the §4.A pattern.

## §5 Files to create or modify

| Path | Action |
|---|---|
| `platform/src/lib/retrieve/query_dasha_periods.ts` | new |
| `platform/src/lib/retrieve/__tests__/query_dasha_periods.test.ts` | new (5+ tests: empty params, next_count, prev_count, as_of_date, md_lord filter, diagnostic fallback) |
| `platform/src/lib/retrieve/chart_facts_query.ts` | extend with as_of_date / from_date / to_date filters |
| `platform/src/lib/retrieve/__tests__/chart_facts_query.test.ts` | +3 tests for new filters |
| `platform/src/lib/retrieve/index.ts` | import + append 30th tool |
| `platform/src/lib/router/retrieval_capability_spec.ts` | update chart_facts_query desc + append query_dasha_periods entry |
| `platform/src/lib/trace/types.ts` | append `'query_dasha_periods'`; literal count 29 → 30 |
| `00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md` | append R-DA rule + §4.28 few-shot |
| `platform/tests/eval/planner_golden_set.json` | append GT.083-086 |
| `platform/tests/eval/fixtures/regression_baseline.json` | paired extension |
| `platform/tests/eval/r_da_dasha_anchor_smoke.ts` | new planner-only smoke |
| `00_ARCHITECTURE/DASHA_BASELINE_AUDIT_v1_0.md` | Stage 0 baseline measurement artifact |

## §6 Verification gates (pre-commit, NOT post-deploy)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis/platform

# G0: Baseline audit artifact exists with at least sample_size + classification
test -f ../00_ARCHITECTURE/DASHA_BASELINE_AUDIT_v1_0.md && \
  grep -q "Classification" ../00_ARCHITECTURE/DASHA_BASELINE_AUDIT_v1_0.md

# G1: TypeScript compiles
npx tsc --noEmit

# G2: TS unit tests — new + regression
npx vitest run src/lib/retrieve/__tests__/query_dasha_periods.test.ts
npx vitest run src/lib/retrieve/__tests__/chart_facts_query.test.ts
npx vitest run src/lib/retrieve/__tests__/

# G3: Planner regression gate (size assertion + behavior preservation)
npx vitest run tests/eval/planner_regression_gate.test.ts

# G4: Planner-only smoke (the campaign's canonical failure-case test)
npx tsx --conditions=react-server --env-file-if-exists=../.env.local tests/eval/r_da_dasha_anchor_smoke.ts
```

All 4 gates green before commit.

## §7 Commit + push

```bash
git add platform/src/lib/retrieve/query_dasha_periods.ts \
        platform/src/lib/retrieve/__tests__/query_dasha_periods.test.ts \
        platform/src/lib/retrieve/chart_facts_query.ts \
        platform/src/lib/retrieve/__tests__/chart_facts_query.test.ts \
        platform/src/lib/retrieve/index.ts \
        platform/src/lib/router/retrieval_capability_spec.ts \
        platform/src/lib/trace/types.ts \
        00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md \
        00_ARCHITECTURE/DASHA_BASELINE_AUDIT_v1_0.md \
        platform/tests/eval/planner_golden_set.json \
        platform/tests/eval/fixtures/regression_baseline.json \
        platform/tests/eval/r_da_dasha_anchor_smoke.ts

git commit -m "feat(dasha): query_dasha_periods tool + R-DA rule + chart_facts_query dasha extension (§5A)

Phase 5A — closes the dasha discoverability gap. The 50 FORENSIC §5.1
dasha rows in chart_facts become planner-reachable via a dedicated
30th retrieval tool plus an R-DA planner rule that fires for any
dasha-mentioning query.

Tool: query_dasha_periods (30th)
  - system: vimshottari (default) / yogini / chara
  - level: M / A / P / all (M deduplicates to MD clusters)
  - as_of_date / from_date / to_date — date range filters
  - next_count / prev_count — forward/backward N MD transitions
  - md_lord / ad_lord — lord filters
  - Default empty params: today's active row + next 3 MDs

R-DA rule: fires query_dasha_periods at priority 1 for explicit dasha
queries, priority 2 for predictive queries with dasha as timing layer.
Pairs with R-TC, R-PA, R-TE.

chart_facts_query extended with as_of_date / from_date / to_date for
the dasha categories (also useful for future panchanga-row date lookups).
RCS description updated to advertise dasha_vimshottari / dasha_yogini /
dasha_chara categories.

Tool count 29 → 30 in all three registries (RETRIEVAL_TOOLS, RCS,
ALL_21_RETRIEVAL_TOOLS).

Test coverage:
  - 5 new query_dasha_periods unit tests
  - 3 new chart_facts_query tests for date filters
  - 4 new golden-set entries GT.083-086 (3 positive + 1 negative)
  - Planner-only smoke r_da_dasha_anchor_smoke.ts

Baseline audit: 00_ARCHITECTURE/DASHA_BASELINE_AUDIT_v1_0.md captures
pre-campaign wrong-next-MD rate from audit_events sample. Post-Phase-5
measurement uses same methodology for delta calculation.

Closes Phase 5A. Synthesis prompt gate (§5B) + post-synthesis validator
(§5C) deferred to subsequent sub-phases.

Refs: 00_ARCHITECTURE/briefs/PHASE_5A_DASHA_TOOL_BRIEF_v1_0.md
Refs: 00_ARCHITECTURE/DASHA_CORRECTNESS_RESEARCH_v1_0.md v1.1
Refs: 00_ARCHITECTURE/PHASE_5_DASHA_CORRECTNESS_MASTER_PLAN_v1_0.md"

git push origin analysis/backend-data-pipeline-perf-audit
```

## §8 Acceptance criteria

- [ ] Stage 0 baseline audit doc `DASHA_BASELINE_AUDIT_v1_0.md` authored with sample_size + classification table + wrong-next-MD rate
- [ ] `query_dasha_periods.ts` created, RetrievalTool registered as 30th in all three registries
- [ ] `chart_facts_query.ts` + RCS entry extended with date filters + dasha categories
- [ ] R-DA rule appended to PLANNER_PROMPT_v2_0.md §3; §4.28 few-shot appended
- [ ] GT.083-086 added to golden set + paired regression baseline
- [ ] 5+ new query_dasha_periods unit tests pass
- [ ] 3+ new chart_facts_query tests pass
- [ ] `tsc --noEmit` clean
- [ ] Planner regression gate green
- [ ] Planner-only smoke 4/4 PASS on GT.083-086 (especially GT.084 — the canonical failure-case test)
- [ ] Commit lands on `analysis/backend-data-pipeline-perf-audit`
- [ ] No Chat V2 files touched in the diff
- [ ] Master plan §B 4A block updated: `status: CLOSED`, append `closing_commit_sha`

## §9 Report back

When complete, post a Cowork message with:

1. Closing commit SHA on analysis branch.
2. `git log --oneline -5`.
3. All 4 verification-gate results.
4. Baseline audit summary (N sampled, wrong-rate % if measurable).
5. The planner-only smoke output for GT.084 specifically (the canonical "next MD" test).
6. Any §5B/5C scope adjustments suggested by §5A execution.

I'll then author the §5B brief (synthesis prompt DASHA DISCIPLINE GATE) based on what §5A delivered.
