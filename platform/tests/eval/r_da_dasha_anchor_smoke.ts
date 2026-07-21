#!/usr/bin/env tsx
/**
 * r_da_dasha_anchor_smoke.ts — focused planner-only smoke test for the
 * Phase 5A query_dasha_periods tool and the R-DA dasha-anchor planner rule
 * encoded in PLANNER_PROMPT_v2_0.md.
 *
 * What this proves vs. doesn't:
 *   - PROVES: the live LLM-first planner, reading the updated
 *     RETRIEVAL_CAPABILITY_SPEC + PLANNER_PROMPT_v2_0.md (R-DA rule +
 *     §4.28 few-shot), selects query_dasha_periods for dasha-mentioning
 *     queries and OMITS it (or uses it only at priority ≥ 3) for pure
 *     interpretive natal queries.
 *   - DOES NOT PROVE: end-to-end pipeline correctness, runtime DB hits,
 *     or synthesis quality.
 *
 * Scope: GT.083–GT.086 (4 entries, Phase 5A).
 *   GT.083 (positive): current MD — query_dasha_periods (empty params)
 *   GT.084 (positive): next MD after Mercury — canonical failure-case test
 *   GT.085 (positive): Saturn MD historical — md_lord filter
 *   GT.086 (negative): interpretive MD-lord query — msr_sql + chart_facts_query PRIMARY; query_dasha_periods MAY appear at priority 3 but msr_sql REQUIRED
 *
 * Pass criteria:
 *   POSITIVE (GT.083–GT.085):
 *     - All 3 entries select query_dasha_periods in tool_calls.
 *     - No entry violates its forbidden_tools list.
 *   NEGATIVE (GT.086):
 *     - msr_sql must appear in predicted tool_calls (primary surface).
 *     - chart_facts_query must appear in predicted tool_calls.
 *     - No forbidden_tools violation.
 *   HARD GATE:
 *     - Zero planner errors.
 *     - All positive + negative criteria met.
 *
 * Campaign significance:
 *   GT.084 is THE canonical failure-case test. Pre-Phase-5A the planner would
 *   not fire query_dasha_periods, leading to synthesis hallucinating "Saturn MD
 *   next" (from pretrained knowledge) instead of the correct "Ketu MD next
 *   (2027-08-19 → 2034-08-21)". This smoke passing proves the discoverability
 *   gap is closed.
 *
 * Env:
 *   PLANNER_MODEL_ID  (default: gemini-2.5-flash — production planner_fast.primary)
 *   CHART_ID          (default: test-native)
 *   VERBOSE=1         (optional, prints full predicted tool_calls per entry)
 *
 * Usage:
 *   npx tsx --conditions=react-server --env-file-if-exists=../.env.local \
 *     tests/eval/r_da_dasha_anchor_smoke.ts
 *
 * Exit code: 0 if all criteria met, 1 otherwise.
 */

import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

// ────────────────────────────────────────────────────────────────────────────
// Types
// ────────────────────────────────────────────────────────────────────────────

interface GoldenEntry {
  id: string
  query: string
  query_class: string
  category: string
  expected_tools: string[]
  required_tools: string[]
  forbidden_tools: string[]
  required_asset_ids?: string[]
  notes?: string
}

interface GoldenSet {
  entries: GoldenEntry[]
}

interface PlannerCall {
  tool_name: string
  priority?: number
}

interface PlannerResult {
  tool_calls: PlannerCall[]
}

interface PerEntryResult {
  id: string
  query: string
  is_negative_test: boolean
  predicted_tools: string[]
  dasha_selected: boolean
  msr_sql_selected: boolean
  chart_facts_selected: boolean
  forbidden_violations: string[]
  passes: boolean
  error: string | null
  latency_ms: number
}

// ────────────────────────────────────────────────────────────────────────────
// Config
// ────────────────────────────────────────────────────────────────────────────

const here = path.dirname(fileURLToPath(import.meta.url))
const GOLDEN_SET_PATH = path.resolve(here, 'planner_golden_set.json')

// Positive entries: planner SHOULD select query_dasha_periods.
const POSITIVE_ENTRY_IDS = ['GT.083', 'GT.084', 'GT.085'] as const

// Negative entries: msr_sql + chart_facts_query must appear; query_dasha_periods
// may appear at priority 3 but is not the primary surface.
const NEGATIVE_ENTRY_IDS = ['GT.086'] as const

const ALL_ENTRY_IDS = [...POSITIVE_ENTRY_IDS, ...NEGATIVE_ENTRY_IDS]

const MODEL_ID = process.env.PLANNER_MODEL_ID ?? 'gemini-2.5-flash'
const CHART_ID = process.env.CHART_ID ?? 'test-native'
const VERBOSE = process.env.VERBOSE === '1'

const NOW_ISO = new Date().toISOString()
const OUTPUT_DIR = path.join(path.resolve(here, '..', '..'), 'scripts', 'eval')
const OUTPUT_FILE = path.join(
  OUTPUT_DIR,
  `r_da_dasha_anchor_smoke_${NOW_ISO.replace(/[:.]/g, '-')}.json`
)

// ────────────────────────────────────────────────────────────────────────────
// Helpers
// ────────────────────────────────────────────────────────────────────────────

function loadGoldenSet(): GoldenSet {
  const raw = readFileSync(GOLDEN_SET_PATH, 'utf-8')
  return JSON.parse(raw) as GoldenSet
}

function pickEntry(set: GoldenSet, id: string): GoldenEntry {
  const entry = set.entries.find(e => e.id === id)
  if (!entry) throw new Error(`Golden entry ${id} not found in ${GOLDEN_SET_PATH}`)
  return entry
}

// ────────────────────────────────────────────────────────────────────────────
// Main
// ────────────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  console.log('━'.repeat(78))
  console.log('R-DA Dasha-Anchor Smoke — Phase 5A query_dasha_periods')
  console.log('━'.repeat(78))
  console.log(`Model:    ${MODEL_ID}`)
  console.log(`Chart:    ${CHART_ID}`)
  console.log(`Run time: ${NOW_ISO}`)
  console.log(`Scope:    GT.083–GT.086 (3 positive + 1 negative)`)
  console.log(`Campaign: Ketu-MD discoverability gap (canonical failure-case = GT.084)`)
  console.log('')

  // Dynamic import keeps server-only resolver deps out of vitest CI.
  const { callPipelinePlanner } = await import('@/lib/pipeline/pipeline_planner')

  const goldenSet = loadGoldenSet()
  const results: PerEntryResult[] = []
  let totalErrors = 0

  for (const id of ALL_ENTRY_IDS) {
    const entry = pickEntry(goldenSet, id)
    const isNegative = (NEGATIVE_ENTRY_IDS as readonly string[]).includes(id)

    const start = Date.now()
    let predicted: string[] = []
    let error: string | null = null

    try {
      const outcome = await callPipelinePlanner(
        entry.query,
        [],
        MODEL_ID,
        CHART_ID
      )
      // W4: only the happy-path 'plan' outcome carries tool_calls.
      const result = (outcome.outcome === 'plan' ? outcome.plan : { tool_calls: [] }) as PlannerResult
      predicted = (result.tool_calls ?? []).map(c => c.tool_name)
    } catch (err) {
      error = err instanceof Error ? err.message : String(err)
      totalErrors++
    }

    const latency_ms = Date.now() - start
    const dashaSelected = predicted.includes('query_dasha_periods')
    const msrSqlSelected = predicted.includes('msr_sql')
    const chartFactsSelected = predicted.includes('chart_facts_query')
    const forbiddenViolations = (entry.forbidden_tools ?? []).filter(t => predicted.includes(t))

    // Positive: must select query_dasha_periods + no forbidden violations.
    // Negative (GT.086): msr_sql + chart_facts_query must appear as primary surfaces.
    const passes = error === null && forbiddenViolations.length === 0 &&
      (isNegative
        ? msrSqlSelected && chartFactsSelected
        : dashaSelected)

    results.push({
      id,
      query: entry.query,
      is_negative_test: isNegative,
      predicted_tools: predicted,
      dasha_selected: dashaSelected,
      msr_sql_selected: msrSqlSelected,
      chart_facts_selected: chartFactsSelected,
      forbidden_violations: forbiddenViolations,
      passes,
      error,
      latency_ms,
    })

    const verdict = error ? '✗ ERR' : passes ? '✓' : '✗'
    const tag = isNegative ? ' [negative]' : ' [positive]'
    const campaignTag = id === 'GT.084' ? ' ★CANONICAL★' : ''
    console.log(
      `  ${verdict} ${id}${tag}${campaignTag} (${latency_ms}ms)  "${entry.query.slice(0, 60)}${entry.query.length > 60 ? '…' : ''}"`
    )
    if (error) {
      console.log(`      └─ ERROR: ${error}`)
    } else if (VERBOSE) {
      console.log(`      └─ predicted: [${predicted.join(', ')}]`)
    } else if (!passes) {
      console.log(`      └─ predicted: [${predicted.join(', ')}]`)
      if (!isNegative && !dashaSelected) {
        console.log(`      └─ FAIL: query_dasha_periods missing — dasha hallucination gap NOT closed`)
        if (id === 'GT.084') {
          console.log(`      └─ CAMPAIGN FAILURE: Ketu MD answer will be hallucinated as Saturn MD`)
        }
      } else if (isNegative && !msrSqlSelected) {
        console.log(`      └─ FAIL: msr_sql missing from interpretive MD-lord query`)
      } else if (isNegative && !chartFactsSelected) {
        console.log(`      └─ FAIL: chart_facts_query missing from interpretive MD-lord query`)
      }
    }
    if (forbiddenViolations.length > 0) {
      console.log(`      └─ FORBIDDEN VIOLATIONS: ${forbiddenViolations.join(', ')}`)
    }
  }

  console.log('')

  // ── Aggregate ──
  console.log('━'.repeat(78))
  console.log('AGGREGATE')
  console.log('━'.repeat(78))

  const positiveResults = results.filter(r => !r.is_negative_test)
  const negativeResults = results.filter(r => r.is_negative_test)

  const positivePass = positiveResults.filter(r => r.passes).length
  const positiveTotal = positiveResults.length
  const negativePass = negativeResults.filter(r => r.passes).length
  const negativeTotal = negativeResults.length

  console.log(`Positive (query_dasha_periods SELECTED): ${positivePass}/${positiveTotal}`)
  console.log(`Negative (msr_sql+chart_facts PRIMARY):  ${negativePass}/${negativeTotal}`)
  console.log(`Planner errors:                          ${totalErrors}`)

  const forbiddenViolationCount = results.reduce((n, r) => n + r.forbidden_violations.length, 0)
  console.log(`Forbidden violations:                    ${forbiddenViolationCount}`)

  const canonicalResult = results.find(r => r.id === 'GT.084')
  if (canonicalResult) {
    const canonicalVerdict = canonicalResult.passes ? '✅ PASS — Ketu MD discoverable' : '❌ FAIL — hallucination gap NOT closed'
    console.log(`GT.084 canonical failure-case:           ${canonicalVerdict}`)
  }

  const allPass =
    positivePass === positiveTotal &&
    negativePass === negativeTotal &&
    totalErrors === 0 &&
    forbiddenViolationCount === 0

  console.log('')
  console.log('─'.repeat(78))
  console.log(`${'Entry'.padEnd(10)} ${'Type'.padEnd(12)} ${'Dasha?'.padEnd(12)} ${'msr_sql?'.padEnd(12)} Verdict`)
  console.log('─'.repeat(78))
  for (const r of results) {
    const type = r.is_negative_test ? 'negative' : 'positive'
    const dasha = r.dasha_selected ? 'selected' : 'absent'
    const msr = r.msr_sql_selected ? 'selected' : 'absent'
    console.log(
      `${r.id.padEnd(10)} ${type.padEnd(12)} ${dasha.padEnd(12)} ${msr.padEnd(12)} ${r.passes ? '✅ PASS' : '❌ FAIL'}`
    )
  }

  // ── Write JSON report ──
  if (!existsSync(OUTPUT_DIR)) mkdirSync(OUTPUT_DIR, { recursive: true })
  const report = {
    probe_name: 'r_da_dasha_anchor_smoke',
    run_at: NOW_ISO,
    model_id: MODEL_ID,
    chart_id: CHART_ID,
    scope: 'GT.083-GT.086 (Phase 5A: 3 positive + 1 negative for R-DA rule)',
    campaign_note: 'GT.084 is the canonical failure-case: next-MD-after-Mercury must resolve to Ketu (DSH.V.024+), not Saturn',
    positive_entry_ids: POSITIVE_ENTRY_IDS,
    negative_entry_ids: NEGATIVE_ENTRY_IDS,
    results,
    positive_pass: positivePass,
    positive_total: positiveTotal,
    negative_pass: negativePass,
    negative_total: negativeTotal,
    forbidden_violation_count: forbiddenViolationCount,
    total_planner_errors: totalErrors,
    overall_pass: allPass,
  }
  writeFileSync(OUTPUT_FILE, JSON.stringify(report, null, 2))
  console.log('')
  console.log(`Report → ${path.relative(process.cwd(), OUTPUT_FILE)}`)

  if (allPass) {
    console.log('\n✅ R-DA rule verified: query_dasha_periods wired correctly in planner.')
    console.log('   Ketu MD discoverability gap closed. Phase 5A smoke PASS.')
    process.exit(0)
  } else {
    console.log('\n❌ R-DA smoke failed. Investigate before commit.')
    if (totalErrors > 0) {
      console.log(`   • ${totalErrors} planner error(s) — check API keys + network.`)
    }
    if (positivePass < positiveTotal) {
      const misses = positiveResults.filter(r => !r.passes).map(r => r.id).join(', ')
      console.log(`   • R-DA positive failures (${misses}): dasha queries missed query_dasha_periods.`)
    }
    if (negativePass < negativeTotal) {
      console.log(`   • R-DA negative failures: interpretive query missing msr_sql or chart_facts_query.`)
    }
    if (forbiddenViolationCount > 0) {
      console.log(`   • ${forbiddenViolationCount} forbidden tool violation(s).`)
    }
    process.exit(1)
  }
}

const invokedAsCli =
  typeof process.argv[1] === 'string' &&
  import.meta.url === pathToFileURL(process.argv[1]).href

if (invokedAsCli) {
  main().catch(err => {
    console.error('Fatal:', err)
    process.exit(1)
  })
}
