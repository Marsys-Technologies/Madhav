#!/usr/bin/env tsx
/**
 * r_tc_transit_context_smoke.ts — focused planner-only smoke test for the
 * Phase 4A query_ephemeris tool and the R-TC transit-context planner rule
 * encoded in PLANNER_PROMPT_v2_0.md.
 *
 * What this proves vs. doesn't:
 *   - PROVES: the live LLM-first planner, reading the updated
 *     RETRIEVAL_CAPABILITY_SPEC + PLANNER_PROMPT_v2_0.md (R-TC rule +
 *     §4.25 few-shot), selects query_ephemeris for transit-anchored queries
 *     and OMITS it for pure-natal queries.
 *   - DOES NOT PROVE: end-to-end pipeline correctness, runtime DB hits,
 *     or synthesis quality.
 *
 * Scope: GT.065–GT.069 (5 entries, Phase 4A).
 *   GT.065 (positive): transit at LEL event date — lel_query + msr_sql + query_ephemeris
 *   GT.066 (positive): current planet snapshot — query_ephemeris only
 *   GT.067 (positive): retrograde lookup for historical date — query_ephemeris
 *   GT.068 (positive): current transit picture for career — msr_sql + query_ephemeris
 *   GT.069 (negative): pure-natal house query — msr_sql ONLY, NO query_ephemeris
 *
 * Pass criteria:
 *   POSITIVE (GT.065–GT.068):
 *     - All 4 entries select query_ephemeris in tool_calls.
 *     - No entry violates its forbidden_tools list.
 *   NEGATIVE (GT.069):
 *     - query_ephemeris must NOT appear in predicted tool_calls.
 *     - No forbidden_tools violation.
 *   HARD GATE:
 *     - Zero planner errors.
 *     - All positive + negative criteria met.
 *
 * Env:
 *   PLANNER_MODEL_ID  (default: gemini-2.5-flash — production planner_fast.primary)
 *   CHART_ID          (default: test-native)
 *   VERBOSE=1         (optional, prints full predicted tool_calls per entry)
 *
 * Usage:
 *   npx tsx --conditions=react-server --env-file-if-exists=../.env.local \
 *     tests/eval/r_tc_transit_context_smoke.ts
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
}

interface PlannerResult {
  tool_calls: PlannerCall[]
}

interface PerEntryResult {
  id: string
  query: string
  is_negative_test: boolean
  predicted_tools: string[]
  ephemeris_selected: boolean
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

// Positive entries: planner SHOULD select query_ephemeris.
const POSITIVE_ENTRY_IDS = ['GT.065', 'GT.066', 'GT.067', 'GT.068'] as const

// Negative entries: planner must NOT select query_ephemeris.
const NEGATIVE_ENTRY_IDS = ['GT.069'] as const

const ALL_ENTRY_IDS = [...POSITIVE_ENTRY_IDS, ...NEGATIVE_ENTRY_IDS]

// Default matches production routing: planner_fast.primary = gemini-2.5-flash
// (registry.ts:1180). gemini-2.5-pro rejects thinkingBudget: 0 as of 2026-05-17,
// and callPipelinePlanner sets reasoning: 'disable' → thinkingBudget: 0.
const MODEL_ID = process.env.PLANNER_MODEL_ID ?? 'gemini-2.5-flash'
const CHART_ID = process.env.CHART_ID ?? 'test-native'
const VERBOSE = process.env.VERBOSE === '1'

const NOW_ISO = new Date().toISOString()
const OUTPUT_DIR = path.join(path.resolve(here, '..', '..'), 'scripts', 'eval')
const OUTPUT_FILE = path.join(
  OUTPUT_DIR,
  `r_tc_transit_context_smoke_${NOW_ISO.replace(/[:.]/g, '-')}.json`
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
  console.log('R-TC Transit-Context Smoke — Phase 4A query_ephemeris')
  console.log('━'.repeat(78))
  console.log(`Model:    ${MODEL_ID}`)
  console.log(`Chart:    ${CHART_ID}`)
  console.log(`Run time: ${NOW_ISO}`)
  console.log(`Scope:    GT.065–GT.069 (4 positive + 1 negative)`)
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
    const ephemerisSelected = predicted.includes('query_ephemeris')
    const forbiddenViolations = (entry.forbidden_tools ?? []).filter(t => predicted.includes(t))

    // Positive: must select query_ephemeris + no forbidden violations.
    // Negative: must NOT select query_ephemeris + no forbidden violations.
    const passes = error === null && forbiddenViolations.length === 0 &&
      (isNegative ? !ephemerisSelected : ephemerisSelected)

    results.push({
      id,
      query: entry.query,
      is_negative_test: isNegative,
      predicted_tools: predicted,
      ephemeris_selected: ephemerisSelected,
      forbidden_violations: forbiddenViolations,
      passes,
      error,
      latency_ms,
    })

    const verdict = error ? '✗ ERR' : passes ? '✓' : '✗'
    const tag = isNegative ? ' [negative]' : ' [positive]'
    console.log(
      `  ${verdict} ${id}${tag} (${latency_ms}ms)  "${entry.query.slice(0, 64)}${entry.query.length > 64 ? '…' : ''}"`
    )
    if (error) {
      console.log(`      └─ ERROR: ${error}`)
    } else if (VERBOSE) {
      console.log(`      └─ predicted: [${predicted.join(', ')}]`)
    } else if (!passes) {
      console.log(`      └─ predicted: [${predicted.join(', ')}]`)
      if (isNegative && ephemerisSelected) {
        console.log(`      └─ FAIL: query_ephemeris appeared in pure-natal query (R-TC false positive)`)
      } else if (!isNegative && !ephemerisSelected) {
        console.log(`      └─ FAIL: query_ephemeris missing from transit-anchored query (R-TC miss)`)
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

  console.log(`Positive (query_ephemeris SELECTED): ${positivePass}/${positiveTotal}`)
  console.log(`Negative (query_ephemeris ABSENT):   ${negativePass}/${negativeTotal}`)
  console.log(`Planner errors:                      ${totalErrors}`)

  const forbiddenViolationCount = results.reduce((n, r) => n + r.forbidden_violations.length, 0)
  console.log(`Forbidden violations:                ${forbiddenViolationCount}`)

  const allPass =
    positivePass === positiveTotal &&
    negativePass === negativeTotal &&
    totalErrors === 0 &&
    forbiddenViolationCount === 0

  console.log('')
  console.log('─'.repeat(78))
  console.log(`${'Entry'.padEnd(10)} ${'Type'.padEnd(12)} ${'Ephemeris?'.padEnd(14)} Verdict`)
  console.log('─'.repeat(78))
  for (const r of results) {
    const type = r.is_negative_test ? 'negative' : 'positive'
    const eph = r.ephemeris_selected ? 'selected' : 'absent'
    console.log(
      `${r.id.padEnd(10)} ${type.padEnd(12)} ${eph.padEnd(14)} ${r.passes ? '✅ PASS' : '❌ FAIL'}`
    )
  }

  // ── Write JSON report ──
  if (!existsSync(OUTPUT_DIR)) mkdirSync(OUTPUT_DIR, { recursive: true })
  const report = {
    probe_name: 'r_tc_transit_context_smoke',
    run_at: NOW_ISO,
    model_id: MODEL_ID,
    chart_id: CHART_ID,
    scope: 'GT.065-GT.069 (Phase 4A: 4 positive + 1 negative for R-TC rule)',
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
    console.log('\n✅ R-TC rule verified: query_ephemeris wired correctly in planner.')
    process.exit(0)
  } else {
    console.log('\n❌ R-TC smoke failed. Investigate before commit.')
    if (totalErrors > 0) {
      console.log(`   • ${totalErrors} planner error(s) — check API keys + network.`)
    }
    if (positivePass < positiveTotal) {
      console.log(`   • R-TC positive failures: ${positiveTotal - positivePass} transit-anchored queries missed query_ephemeris.`)
    }
    if (negativePass < negativeTotal) {
      console.log(`   • R-TC negative failures: ${negativeTotal - negativePass} natal-only queries incorrectly included query_ephemeris.`)
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
