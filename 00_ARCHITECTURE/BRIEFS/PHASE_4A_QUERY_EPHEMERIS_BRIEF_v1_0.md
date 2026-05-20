---
canonical_id: PHASE_4A_QUERY_EPHEMERIS_BRIEF
version: 1.0
status: AUTHORED_READY_TO_EXECUTE
campaign: PHASE_4_EPHEMERIS_ACCESSIBILITY
sub_phase: 4A
authored_on: 2026-05-18
estimated_sessions: 1
two_stream_branch: analysis/backend-data-pipeline-perf-audit
---

# §4.A — `query_ephemeris` Retrieval Tool + R-TC Transit-Context Rule

## §1 Scope

Wrap the 657,450-row `ephemeris_daily` Postgres table (1900–2100 daily, Lahiri sidereal, midnight UT) as a planner-reachable `RetrievalTool` called `query_ephemeris`. Encode the R-TC transit-context rule in the planner prompt so any non-natal query automatically attaches `query_ephemeris` with the relevant date(s). Pair with golden-set + regression-baseline extension + planner-only smoke test.

This closes the coverage gap: the daily ephemeris becomes the 27th planner-reachable tool and the canonical "what was the sky doing on date X?" surface.

## §2 What you must NOT do

- **No branch other than `analysis/backend-data-pipeline-perf-audit`**. If git shows you on a different branch, STOP.
- **No Chat V2 files**. Forbidden globs: `platform/src/components/consume/*`, `platform/src/components/chat/*`, `platform/tests/{unit,integration,e2e,component,components}/chat-v2/*`, `00_ARCHITECTURE/CHAT_V2_*`, `00_ARCHITECTURE/chat_v2_briefs/*`, `CHAT_V2_PROGRESS.md`.
- **No `npm run answer:eval`**. Production eval runs only as part of a consolidated batch (per the campaign discipline in master plan §C). Pre-commit verification is planner-only smoke + unit tests + tsc.
- **No `bootstrap_ephemeris.py` changes**. The TRUE_NODE → MEAN_NODE Rahu fix is §4.B scope, NOT §4.A. Read `ephemeris_daily` as-is.
- **No new ayanamshas, no Bhava-Chalit, no derived columns**. Those are §4.B and §4.C.
- **No `swisseph`/`pyswisseph` imports in TypeScript**. The tool is a thin SQL wrapper over the already-populated table.

## §3 Files to create or modify

### §3.1 New file — `platform/src/lib/retrieve/query_ephemeris.ts`

Implementation pattern: model after `query_signal_state.ts` (closest sibling: reads a Postgres table, supports date OR date-range, has diagnostic fallback when no rows match).

```ts
/**
 * MARSYS-JIS Retrieval tool — query_ephemeris (Phase 4A)
 *
 * Surfaces date-indexed planetary positions from the ephemeris_daily table
 * (migration 015). 9 grahas × ~73,050 days = 657K rows, 1900-01-01 → 2100-12-31,
 * Lahiri sidereal, midnight UT, populated by bootstrap_ephemeris.py.
 *
 * Use this for any query that needs transit-context — that is, planetary
 * positions at a specific date (past LEL event, current moment, future event,
 * or date range). Pairs with the R-TC planner rule which attaches this tool
 * at priority 2 for any non-natal query.
 *
 * Distinct from:
 *   - chart_facts_query: natal placements only
 *   - temporal: Vedic event-window data (sade sati, eclipses, retrogrades,
 *     dasha chain) — not raw planet positions
 *   - cross_varga_dignity_query: D1/D9/D10 natal dignity
 *
 * Date range: 1900-01-01 through 2100-12-31. Outside this window the tool
 * returns a diagnostic empty row.
 */

import crypto from 'crypto'
import { getStorageClient } from '@/lib/storage'
import { writeToolExecutionLog } from '@/lib/db/monitoring-write'
import type { QueryPlan, ToolBundle, ToolBundleResult, RetrievalTool } from './types'

const TOOL_NAME = 'query_ephemeris'
const TOOL_VERSION = '1.0.0'

// All 9 grahas as stored in ephemeris_daily.planet (lowercase).
const VALID_PLANETS = ['sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu'] as const
type PlanetName = (typeof VALID_PLANETS)[number]

export interface QueryEphemerisInput {
  /** Single date (YYYY-MM-DD). Defaults to today UTC if neither date nor start_date provided. */
  date?: string
  /** Start of date range (YYYY-MM-DD). When set with end_date, returns inclusive range. */
  start_date?: string
  /** End of date range (YYYY-MM-DD). Required when start_date is set. */
  end_date?: string
  /** Single planet (canonical or capitalized name, normalized to lowercase). */
  planet?: string
  /** Multiple planets. */
  planets?: string[]
  /** Maximum rows. Clamped to [1, 500]. Defaults to 100. */
  limit?: number
}

interface EphemerisRow {
  date: string          // pg DATE → ISO string
  planet: string
  longitude_deg: string // NUMERIC → string from pg
  latitude_deg: string | null
  speed_deg_per_day: string
  is_retrograde: boolean
  sign: string
  sign_degree: string
  nakshatra: string
  nakshatra_pada: number
  ayanamsha: string
  ephemeris_version: string
}

function normalizePlanet(p: string): PlanetName | null {
  const lower = p.toLowerCase().trim()
  return (VALID_PLANETS as readonly string[]).includes(lower) ? (lower as PlanetName) : null
}

function buildWhere(p: QueryEphemerisInput): { where: string; args: unknown[] } {
  const conditions: string[] = []
  const args: unknown[] = []
  let idx = 1

  // Date conditions
  if (p.start_date && p.end_date) {
    conditions.push(`date >= $${idx}::date`)
    args.push(p.start_date)
    idx++
    conditions.push(`date <= $${idx}::date`)
    args.push(p.end_date)
    idx++
  } else if (p.date) {
    conditions.push(`date = $${idx}::date`)
    args.push(p.date)
    idx++
  } else {
    conditions.push(`date = CURRENT_DATE`)
  }

  // Planet conditions
  const planetList: string[] = []
  if (p.planet) {
    const np = normalizePlanet(p.planet)
    if (np) planetList.push(np)
  }
  if (p.planets) {
    for (const x of p.planets) {
      const np = normalizePlanet(x)
      if (np) planetList.push(np)
    }
  }
  if (planetList.length > 0) {
    conditions.push(`planet = ANY($${idx}::text[])`)
    args.push(planetList)
    idx++
  }

  return { where: conditions.join(' AND '), args }
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
      data_asset_id: 'EPHEMERIS_DAILY',
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
  const input = (params ?? {}) as QueryEphemerisInput
  const limit = Math.max(1, Math.min(500, input.limit ?? 100))

  const { where, args } = buildWhere(input)

  const sql = `
    SELECT
      date::text AS date,
      planet,
      longitude_deg::text AS longitude_deg,
      latitude_deg::text AS latitude_deg,
      speed_deg_per_day::text AS speed_deg_per_day,
      is_retrograde,
      sign,
      sign_degree::text AS sign_degree,
      nakshatra,
      nakshatra_pada,
      ayanamsha,
      ephemeris_version
    FROM ephemeris_daily
    WHERE ${where}
    ORDER BY date ASC, planet ASC
    LIMIT ${limit}
  `

  const storage = getStorageClient()
  const result = await storage.query(sql, args)
  const rows = result.rows as EphemerisRow[]

  const results: ToolBundleResult[] = rows.length > 0
    ? rows.map(r => ({
        content: JSON.stringify({
          date: r.date,
          planet: r.planet,
          longitude_deg: Number(r.longitude_deg),
          latitude_deg: r.latitude_deg !== null ? Number(r.latitude_deg) : null,
          speed_deg_per_day: Number(r.speed_deg_per_day),
          is_retrograde: r.is_retrograde,
          sign: r.sign,
          sign_degree: Number(r.sign_degree),
          nakshatra: r.nakshatra,
          nakshatra_pada: r.nakshatra_pada,
          ayanamsha: r.ayanamsha,
          ephemeris_version: r.ephemeris_version,
        }),
        source_canonical_id: 'EPHEMERIS_DAILY',
        source_version: '1.0',
        confidence: 1.0,
        significance: 0.85,
      }))
    : [{
        content: JSON.stringify({
          note: 'ephemeris_daily empty or out-of-range for requested params. Date range supported: 1900-01-01 to 2100-12-31.',
          params: input,
        }),
        source_canonical_id: 'EPHEMERIS_DAILY',
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
    invocation_params: { ...input, limit },
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
    rows_returned: rows.length,
    latency_ms: bundle.latency_ms,
    token_estimate: Math.ceil(JSON.stringify(results).length / 4),
    data_asset_id: 'EPHEMERIS_DAILY',
    error_code: null,
    served_from_cache: false,
    fallback_used: rows.length === 0,
  })

  return bundle
}

export const tool: RetrievalTool = {
  name: TOOL_NAME,
  version: TOOL_VERSION,
  description:
    'Date-indexed planetary position lookup from the ephemeris_daily table ' +
    '(1900-01-01 to 2100-12-31, 9 grahas, Lahiri sidereal, midnight UT). ' +
    'Returns longitude, sign, nakshatra+pada, retrograde, speed for the queried date(s). ' +
    'Default surface for any non-natal query that needs transit context (past LEL event, ' +
    'present moment, future date, or date range). Pairs with the R-TC planner rule.',
  retrieve,
}
```

### §3.2 Register in `platform/src/lib/retrieve/index.ts`

Add (anywhere reasonable, but keep §-grouped):

```ts
// Phase 4A — date-indexed ephemeris lookup (closes ephemeris-accessibility gap)
import * as queryEphemeris from './query_ephemeris'
```

And in the `RETRIEVAL_TOOLS` array, append:

```ts
  queryEphemeris.tool,
```

### §3.3 Register in `platform/src/lib/router/retrieval_capability_spec.ts`

Add a new entry mirroring the M9 + M8-G pattern. Place between `convergence_score_lookup` and the registry array (i.e., at the end of the entry declarations). Use this body verbatim:

```ts
// ────────────────────────────────────────────────────────────────────────────
// Phase 4A — date-indexed ephemeris lookup
// ────────────────────────────────────────────────────────────────────────────

const query_ephemeris: RetrievalCapabilityEntry = {
  tool_name: 'query_ephemeris',
  description:
    'Date-indexed planetary positions from the ephemeris_daily table (657K rows, ' +
    '1900-01-01 to 2100-12-31, 9 grahas, Lahiri sidereal, midnight UT, computed by ' +
    'pyswisseph at bootstrap and persisted). Returns per-planet per-day longitude, ' +
    'sign, nakshatra+pada, sign_degree, retrograde flag, speed. ' +
    'CANONICAL SURFACE for transit context: divisional_query / chart_facts_query give ' +
    'natal positions; query_ephemeris gives transit positions at any date in the ' +
    'supported range. Use whenever a query is not purely natal — past LEL event date, ' +
    'present moment, future date, or date range. The planner attaches this tool by ' +
    'default at priority 2 under rule R-TC (transit-context).',
  data_surface:
    'L1 — table ephemeris_daily (migration 015). Fields: date, planet (lowercase: ' +
    'sun..ketu), longitude_deg (sidereal Lahiri 0-360), latitude_deg, ' +
    'speed_deg_per_day, is_retrograde, sign, sign_degree (0-30), nakshatra, ' +
    'nakshatra_pada (1-4), ayanamsha (lahiri), ephemeris_version (pyswisseph-2.10.x).',
  supported_params:
    '{ date?: YYYY-MM-DD (single date; default today UTC); ' +
    'start_date?: YYYY-MM-DD; end_date?: YYYY-MM-DD (range mode); ' +
    'planet?: string (canonical name, case-insensitive); ' +
    'planets?: string[] (multiple); ' +
    'limit?: number (default 100, max 500). ' +
    'Date range supported: 1900-01-01 to 2100-12-31. Out-of-range returns diagnostic row. }',
  optimal_patterns: [
    'Transit on a specific past event: {date:"2008-04-15"} (then read planet=Saturn for "Saturn at marriage")',
    'Current transits: {} (no params, defaults to today UTC, all 9 planets)',
    'Single planet history: {start_date:"2018-01-01", end_date:"2019-12-31", planet:"Mars"}',
    'Future transit window: {start_date:"2027-08-21", end_date:"2034-08-21", planet:"Ketu"} (Ketu MD)',
    'Multi-planet snapshot: {date:"2026-05-18", planets:["Sun","Moon","Saturn"]}',
  ],
  cost_tier: 'low',
  requires_temporal: true,
}
```

Then append `query_ephemeris` to the `RETRIEVAL_CAPABILITY_SPEC` array (last entry):

```ts
  multi_school_signal_lookup,
  convergence_score_lookup,
  query_ephemeris,  // Phase 4A
] as const
```

### §3.4 Register in `platform/src/lib/trace/types.ts`

Update `ALL_21_RETRIEVAL_TOOLS` to add three entries — `query_ephemeris` AND the two trace-display residuals (`classical_text_search`, `classical_attribution_lookup`). This closes the cosmetic trace gap surfaced in the consolidated view as a bonus.

Update the comment to reflect the new literal count (27):

```ts
/**
 * Retrieval tools registered in the RETRIEVAL_TOOLS manifest.
 * Sub-rows for unfired tools render dimmed in the Retrieval container.
 *
 * Updated 2026-05-17: added lel_query (planner-blind RCS fix).
 * Updated 2026-05-18 (Phase 2A): added multi_school_signal_lookup + convergence_score_lookup.
 * Updated 2026-05-18 (Phase 4A): added query_ephemeris + closed cosmetic trace gap by
 * adding classical_text_search + classical_attribution_lookup (which had shipped in
 * production via M8-G but were missing from this array). Name retained as
 * `ALL_21_RETRIEVAL_TOOLS` for callsite compatibility; literal count is now 27.
 */
```

Then add the three entries at the appropriate positions (end of array is fine):

```ts
  'classical_text_search',
  'classical_attribution_lookup',
  'multi_school_signal_lookup',
  'convergence_score_lookup',
  'query_ephemeris',
] as const
```

### §3.5 Encode R-TC in `00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md`

This is the planner-prompt amendment. It has TWO parts:

**Part A — add R-TC rule** (after R-GSH, before the "Style rules" section in §3. System prompt):

Find the existing block ending with R-GSH (graph seed hints). Append the R-TC rule immediately after, BEFORE the line `Style rules (unchanged from v1.7):`:

```
  R-TC. TRANSIT-CONTEXT ENRICHMENT: For ANY query that is NOT pure-natal-only,
       attach `query_ephemeris` to tool_calls at priority 2. The trigger is
       any temporal anchor (now/past/future date or named event) — divisional
       charts give the natal positions, ephemeris gives the present/historical/
       future transit positions, and the synthesis layer needs BOTH to reason
       about timing.

       Date param selection:
         - "now" / "currently" / "today" / "at this point" / "in my life right now"
           → params.date = today UTC (server fills CURRENT_DATE; planner emits
             empty params {} which the tool defaults).
         - LEL-known past event (marriage, job change, illness, etc.)
           → also schedule lel_query at priority 1; the synthesis layer joins
             query_ephemeris on the LEL event_date.
         - Specific past or future date stated
           → params.date = stated date (YYYY-MM-DD).
         - Date range or implied range ("next 2 years", "2026-2028", "this quarter")
           → params.start_date + params.end_date (YYYY-MM-DD).
         - Named dasha period
           → params.start_date + params.end_date matching the dasha window
             (also schedule temporal with dasha_context_required:true).

       Exclusions (R-TC does NOT fire for):
         - Pure natal positional queries: "what house is X in", "what is my Y",
           "describe my Z", "what's my lagna lord" — no temporal anchor.
         - Pure classical interpretation: "what does Saturn in 10H mean classically".
         - Remedial codex lookup: "what gemstone for Venus".
         - Multi-school triangulation queries (R31/R32 STOP at step 5; do NOT
           append query_ephemeris when on the SCHOOL/CONVERGENCE PATH).

       Pairing with existing rules:
         - R-TW1 (eclipse temporal scope): keep temporal for the eclipse window;
           R-TC adds query_ephemeris for Sun/Moon positions at the eclipse moment.
         - R-TW2 (antardasha date-range): keep time_window semantics; R-TC adds
           the actual ephemeris lookup at the dasha window boundaries.
         - R7c (transit ban on vector_search for pure-timing): unaffected;
           query_ephemeris and vector_search serve different purposes.

       The default behavior is INCLUSION. When in doubt, attach query_ephemeris.
       Synthesis tolerates extra context; missing transit context is the failure
       mode that R-TC fixes.

```

**Part B — add a few-shot example** demonstrating R-TC firing. Append at the end of §4. Few-shot examples, as `### 4.25 R-TC transit-context — historical LEL event`:

```markdown
### 4.25 R-TC transit-context — historical LEL event

Query: "What was Saturn doing when I got married in 2008?"

```json
{
  "query_class": "predictive",
  "query_intent_summary": "Saturn transit at marriage event — natal-vs-transit comparison.",
  "asset_bundle": [
    { "asset_id": "FORENSIC", "priority": 1, "reason": "Natal Saturn placement." },
    { "asset_id": "LEL", "priority": 1, "reason": "Marriage event date." },
    { "asset_id": "CGM", "priority": 2, "reason": "Saturn's natal aspect graph." }
  ],
  "tool_calls": [
    { "tool_name": "lel_query", "params": {"category":"relationship","significance":"major"}, "token_budget": 600, "priority": 1, "reason": "Marriage event date from LEL." },
    { "tool_name": "msr_sql", "params": {"planets":["Saturn"], "min_significance":0.6, "limit":20}, "token_budget": 1200, "priority": 1, "reason": "Natal Saturn signals." },
    { "tool_name": "query_ephemeris", "params": {"planet":"Saturn"}, "token_budget": 400, "priority": 2, "reason": "R-TC transit Saturn position at marriage date (synthesis layer joins on lel_query result)." },
    { "tool_name": "pattern_register", "params": {"planets":["Saturn"], "min_strength":0.6}, "token_budget": 800, "priority": 2, "reason": "R7a predictive cross-domain lens — Saturn-keyed patterns." }
  ],
  "synthesis_guidance": "Compare natal Saturn (msr_sql) against transit Saturn at marriage date (query_ephemeris joined to lel_query event_date). Surface dignity, sign, retrograde, and any Saturn-aspect activation patterns.",
  "expected_output_shape": "time_indexed_prediction",
  "history_mode": "synthesized",
  "planets": ["Saturn"],
  "houses": [],
  "domains": ["relationships"],
  "forward_looking": false,
  "prior_turn_relevance": { "used": 0, "reason": "Independent question — chart facts + LEL event are enough.", "mode": "independent" }
}
```

This example shows R-TC firing alongside R7a (predictive cross-domain lens) for a LEL-anchored historical-event transit query. The planner does NOT need to compute the marriage date itself — `lel_query` supplies it and the synthesis layer joins. `query_ephemeris` runs with `{planet:"Saturn"}` and an implicit `date = today UTC` fallback, BUT in this LEL-paired case the synthesis layer SHOULD pass the LEL event_date forward (the tool param schema supports `date` — planner can later set it explicitly when LEL is in the bundle and the date is resolvable pre-execution; for now the join happens at synthesis time).
```

### §3.6 Extend `platform/tests/eval/planner_golden_set.json`

Append 5 new entries `GT.065` through `GT.069`. Use the existing GT entry shape; here are the entries to add verbatim:

```json
{
  "id": "GT.065",
  "query": "What was Mars doing when I changed jobs in 2018?",
  "query_class": "predictive",
  "required_tools": ["lel_query", "msr_sql", "query_ephemeris", "pattern_register"],
  "forbidden_tools": ["temporal"],
  "asset_bundle_must_include": ["FORENSIC", "LEL"],
  "planets": ["Mars"],
  "domains": ["career"],
  "forward_looking": false,
  "notes": "R-TC + R7a. Historical LEL-anchored transit query. lel_query supplies job-change date; query_ephemeris reads Mars transit position at that date; msr_sql gives natal Mars signals; pattern_register satisfies R7a predictive cross-domain lens. temporal is NOT needed (no eclipse/sade-sati/retrograde-window dependency)."
},
{
  "id": "GT.066",
  "query": "Where are the planets right now?",
  "query_class": "factual",
  "required_tools": ["query_ephemeris"],
  "forbidden_tools": ["vector_search", "pattern_register", "cluster_atlas"],
  "asset_bundle_must_include": ["FORENSIC"],
  "planets": [],
  "domains": [],
  "forward_looking": false,
  "notes": "R-TC + R-FACT. Pure transit positional query. query_ephemeris with empty params defaults to today UTC for all 9 planets. R-FACT bans vector_search and registers; R-TC fires query_ephemeris."
},
{
  "id": "GT.067",
  "query": "Was Mercury retrograde in January 2019?",
  "query_class": "factual",
  "required_tools": ["query_ephemeris"],
  "forbidden_tools": ["vector_search", "pattern_register"],
  "asset_bundle_must_include": ["FORENSIC"],
  "planets": ["Mercury"],
  "domains": [],
  "forward_looking": false,
  "notes": "R-TC + R-FACT. Date-range factual transit query. params: {start_date:'2019-01-01', end_date:'2019-01-31', planet:'Mercury'}. R-FACT bans registers; R-TC fires query_ephemeris."
},
{
  "id": "GT.068",
  "query": "What's the current transit picture for my career?",
  "query_class": "predictive",
  "required_tools": ["msr_sql", "query_ephemeris", "pattern_register"],
  "forbidden_tools": [],
  "asset_bundle_must_include": ["FORENSIC", "CGM"],
  "planets": [],
  "domains": ["career"],
  "forward_looking": true,
  "notes": "R-TC + R7a. Domain-scoped present-tense transit query. msr_sql with domain=career; query_ephemeris with empty params (today); pattern_register satisfies R7a."
},
{
  "id": "GT.069",
  "query": "What house is my Saturn in?",
  "query_class": "factual",
  "required_tools": ["msr_sql"],
  "forbidden_tools": ["query_ephemeris", "vector_search", "pattern_register"],
  "asset_bundle_must_include": ["FORENSIC"],
  "planets": ["Saturn"],
  "domains": [],
  "forward_looking": false,
  "notes": "NEGATIVE for R-TC. Pure natal positional query, NO temporal anchor. R-TC must NOT fire; query_ephemeris is forbidden. R-FACT enforces single-tool msr_sql."
}
```

### §3.7 Paired extension of `platform/tests/eval/fixtures/regression_baseline.json`

Per the lesson from da140c8: extending `planner_golden_set.json` REQUIRES paired extension of `regression_baseline.json` or the `planner_regression_gate.test.ts` will fail with size-mismatch.

Read the file, count its current entries, and append GT.065 through GT.069 with the same shape that other GT entries use (typically `{id, expected_required, expected_forbidden, expected_asset_bundle}`). Mirror the exact field names from the existing file — do not invent shape.

### §3.8 Unit test — `platform/src/lib/retrieve/__tests__/query_ephemeris.test.ts`

Mirror the `query_signal_state.test.ts` pattern (mocked storage client, mocked monitoring log). Five test cases minimum:

1. `returns rows for default (CURRENT_DATE, all planets)` — empty params, asserts `date = CURRENT_DATE` in SQL.
2. `returns rows for specific date + planet` — `{date:'2008-04-15', planet:'Saturn'}`, asserts `date = $1::date` and `planet = ANY($2::text[])` with `['saturn']`.
3. `returns rows for date range + multiple planets` — `{start_date:'2018-01-01', end_date:'2019-12-31', planets:['Mars','Mercury']}`, asserts both `date >= $1::date` AND `date <= $2::date`.
4. `normalizes capitalized planet names` — `{planet:'SATURN'}` → SQL receives `['saturn']`.
5. `returns diagnostic row when no rows match` — mock empty result, assert single result with `confidence=0` and `note` field.

Use the same `vi.mock` setup. Pattern is identical to query_signal_state.test.ts §1-§30. Read that file first if unclear.

### §3.9 Planner-only smoke test

Add to the existing planner smoke runner (`platform/tests/eval/planner_blind_fix_smoke.ts` or equivalent — check current convention by reading the file). New smoke entries: GT.065 through GT.069. The runner should pass all 5 when complete.

If a new smoke file is preferred, create `platform/tests/eval/r_tc_transit_context_smoke.ts` following the same template — load PLANNER_PROMPT, run the planner over the 5 queries, assert the `tool_calls` array satisfies `required_tools` and excludes `forbidden_tools`.

## §4 Verification gates (run pre-commit, NOT after deploy)

Run in order; halt on first failure.

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis/platform

# Gate 1 — TypeScript compiles
npx tsc --noEmit

# Gate 2 — unit tests pass (new + regression on existing)
npx vitest run src/lib/retrieve/__tests__/query_ephemeris.test.ts
npx vitest run src/lib/retrieve/__tests__/      # all retrieval tests, regression check

# Gate 3 — planner regression gate (the size assertion that bit Phase 1)
npx vitest run tests/eval/planner_regression_gate.test.ts

# Gate 4 — planner-only smoke on the 5 new entries
npx tsx tests/eval/r_tc_transit_context_smoke.ts  # or the equivalent existing runner
```

All 4 gates must be green BEFORE you commit.

## §5 Commit + push

Single commit on `analysis/backend-data-pipeline-perf-audit`:

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav-analysis
git checkout analysis/backend-data-pipeline-perf-audit  # confirm
git status                                               # confirm clean
# ...make changes...
git add platform/src/lib/retrieve/query_ephemeris.ts \
        platform/src/lib/retrieve/__tests__/query_ephemeris.test.ts \
        platform/src/lib/retrieve/index.ts \
        platform/src/lib/router/retrieval_capability_spec.ts \
        platform/src/lib/trace/types.ts \
        00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md \
        platform/tests/eval/planner_golden_set.json \
        platform/tests/eval/fixtures/regression_baseline.json \
        platform/tests/eval/r_tc_transit_context_smoke.ts   # if new file
git commit -m "feat(retrieval): query_ephemeris tool + R-TC transit-context rule (§4.A)

Phase 4A of the ephemeris accessibility campaign. Wraps ephemeris_daily
as a planner-reachable RetrievalTool. Encodes R-TC (transit-context)
in PLANNER_PROMPT so non-natal queries default to attaching the tool.

Tool: query_ephemeris
  - Reads ephemeris_daily (657K rows, 1900-2100, Lahiri sidereal)
  - Supports single date or date range, single or multiple planets
  - Diagnostic row when no rows match
  - Default surface for any query with a temporal anchor

R-TC rule: non-natal queries (now / past LEL event / specific date /
date range / named dasha period) attach query_ephemeris at priority 2.
Pure natal queries (R-FACT, no temporal anchor) do NOT attach.

Also closes the cosmetic trace-display gap by adding classical_text_search
and classical_attribution_lookup to ALL_21_RETRIEVAL_TOOLS (literal count
now 27).

Test coverage: 5 unit tests (mocked storage) + 5 new golden-set entries
GT.065-069 + paired regression_baseline extension + planner-only smoke.

Closes Phase 4A. Production answer:eval deferred to consolidated campaign
batch per master plan §C.

Refs: 00_ARCHITECTURE/PHASE_4_EPHEMERIS_ACCESSIBILITY_MASTER_PLAN_v1_0.md
Refs: 00_ARCHITECTURE/EPHEMERIS_ACCESSIBILITY_RESEARCH_v1_0.md v1.1"
git push origin analysis/backend-data-pipeline-perf-audit
```

## §6 Acceptance criteria

- [ ] `query_ephemeris.ts` created, 26→27 entries in `RETRIEVAL_TOOLS` array, 26→27 in `RETRIEVAL_CAPABILITY_SPEC`, 24→27 in `ALL_21_RETRIEVAL_TOOLS`
- [ ] R-TC rule added to PLANNER_PROMPT_v2_0.md §3 (system prompt body), positioned after R-GSH
- [ ] §4.25 few-shot example added to PLANNER_PROMPT_v2_0.md §4
- [ ] 5 new golden-set entries (GT.065-069) added; paired regression_baseline entries added
- [ ] 5 unit tests in `query_ephemeris.test.ts` all pass
- [ ] `npx tsc --noEmit` clean
- [ ] Planner-only smoke 5/5 PASS on the new entries
- [ ] `planner_regression_gate.test.ts` green (no drop on existing 60+ entries)
- [ ] Commit lands on `analysis/backend-data-pipeline-perf-audit`
- [ ] No Chat V2 files touched in the diff
- [ ] Master plan §B `4A` block updated: `status: CLOSED`, append `closing_commit_sha`

## §7 Report back

When complete, post a Cowork message back with:

1. Closing commit SHA on analysis branch.
2. `git log --oneline -3` output.
3. The 4 verification-gate results (PASS/FAIL each).
4. Any deviations from the brief (with reasoning).
5. Any §4.B/4.C/4.D scope adjustments suggested by what you learned executing §4.A.

I'll then author the §4.B brief based on what you delivered.
