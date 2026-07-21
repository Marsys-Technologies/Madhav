#!/usr/bin/env tsx
/**
 * planner_blind_fix_smoke.ts — focused planner-only smoke test for the four
 * tools wired into RETRIEVAL_CAPABILITY_SPEC on 2026-05-17 (audit findings
 * F.PIPE.1 + F.SYNTH.1: lel_query, query_signal_state,
 * query_kp_ruling_planets, query_varshaphala).
 *
 * What this proves vs. doesn't:
 *   - PROVES: the live LLM-first planner, reading the updated
 *     RETRIEVAL_CAPABILITY_SPEC + PLANNER_PROMPT_v2_0.md (R28/R29/R30 +
 *     worked examples), actually SELECTS these tools when given queries
 *     that should trigger them.
 *   - DOES NOT PROVE: end-to-end pipeline correctness, runtime DB hits,
 *     or synthesis quality. Use sla:probe-planner-blind for retrieve()
 *     latency + answer:eval (post-deploy) for end-to-end synthesis.
 *
 * Scope: only the 12 golden-set entries GT.053-GT.064 (added 2026-05-17 to
 * exercise the four restored tools). Existing 52 golden entries are NOT
 * re-run here — see `npm run eval:planner` for the full sweep.
 *
 * Pass criteria (per tool):
 *   - At least one of the tool's 3 dedicated GT entries selects it
 *     in tool_calls.
 *   - At least one of the tool's 3 entries selects it AS a required tool
 *     (i.e. without rate-limiting / fallback degradation).
 *
 * Hard gate (overall):
 *   - Each of the four tools meets the per-tool pass criteria.
 *   - No golden entry produces a planner error.
 *
 * Env:
 *   PLANNER_MODEL_ID  (default: gemini-2.5-flash — matches production routing
 *                       planner_fast.primary per registry.ts:1180. Do NOT default
 *                       to gemini-2.5-pro: as of 2026-05-17, the Gemini API rejects
 *                       thinkingBudget: 0 on gemini-2.5-pro ["Budget 0 is invalid.
 *                       This model only works in thinking mode"], and the planner
 *                       intentionally disables thinking for speed via
 *                       reasoning: 'disable' → thinkingBudget: 0.)
 *   CHART_ID          (default: test-native)
 *   VERBOSE=1         (optional, prints full predicted tool_calls per query)
 *
 * Usage:
 *   npm run eval:planner-blind-fix
 *   or:
 *   npx tsx --conditions=react-server --env-file-if-exists=../.env.local \
 *     tests/eval/planner_blind_fix_smoke.ts
 *
 * Exit code: 0 if all four tools hit pass criteria, 1 otherwise.
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
  query_class: string
  target_tool: string
  predicted_tools: string[]
  target_selected: boolean
  target_was_required: boolean
  forbidden_violations: string[]
  error: string | null
  latency_ms: number
}

interface PerToolReport {
  tool_name: string
  entry_ids: string[]
  selected_count: number       // how many of its 3 entries selected the tool
  required_count: number       // how many had it in required_tools AND it was selected
  passes_smoke_test: boolean
  details: PerEntryResult[]
}

// ────────────────────────────────────────────────────────────────────────────
// Config
// ────────────────────────────────────────────────────────────────────────────

const here = path.dirname(fileURLToPath(import.meta.url))
const GOLDEN_SET_PATH = path.resolve(here, 'planner_golden_set.json')

// Phase 1 tools restored to RCS visibility on 2026-05-17 (GT.053–064)
// + Phase 2A M9 tools wired on 2026-05-18 (GT.050–052 — pre-existing M9 golden entries).
const TARGET_TOOLS = {
  lel_query: ['GT.053', 'GT.054', 'GT.055'],
  query_signal_state: ['GT.056', 'GT.057', 'GT.058'],
  query_kp_ruling_planets: ['GT.059', 'GT.060', 'GT.061'],
  query_varshaphala: ['GT.062', 'GT.063', 'GT.064'],
  multi_school_signal_lookup: ['GT.050', 'GT.051', 'GT.052'],
  convergence_score_lookup: ['GT.050', 'GT.051', 'GT.052'],
} as const

// Default matches production routing: planner_fast.primary = gemini-2.5-flash
// (registry.ts:1180). gemini-2.5-pro rejects thinkingBudget: 0 as of 2026-05-17,
// and callPipelinePlanner sets reasoning: 'disable' which maps to budget 0.
const MODEL_ID = process.env.PLANNER_MODEL_ID ?? 'gemini-2.5-flash'
const CHART_ID = process.env.CHART_ID ?? 'test-native'
const VERBOSE = process.env.VERBOSE === '1'

const NOW_ISO = new Date().toISOString()
const OUTPUT_DIR = path.join(path.resolve(here, '..', '..'), 'scripts', 'eval')
const OUTPUT_FILE = path.join(
  OUTPUT_DIR,
  `planner_blind_fix_smoke_${NOW_ISO.replace(/[:.]/g, '-')}.json`
)

// ────────────────────────────────────────────────────────────────────────────
// Helpers
// ────────────────────────────────────────────────────────────────────────────

function loadGoldenSet(): GoldenSet {
  const raw = readFileSync(GOLDEN_SET_PATH, 'utf-8')
  return JSON.parse(raw) as GoldenSet
}

function pickEntries(set: GoldenSet, ids: readonly string[]): GoldenEntry[] {
  const byId = new Map(set.entries.map(e => [e.id, e]))
  const out: GoldenEntry[] = []
  for (const id of ids) {
    const e = byId.get(id)
    if (!e) throw new Error(`Golden entry ${id} not found in ${GOLDEN_SET_PATH}`)
    out.push(e)
  }
  return out
}

// ────────────────────────────────────────────────────────────────────────────
// Main
// ────────────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  console.log('━'.repeat(78))
  console.log('Planner-Only Smoke — Restored Tools (RCS Fix 2026-05-17)')
  console.log('━'.repeat(78))
  console.log(`Model:    ${MODEL_ID}`)
  console.log(`Chart:    ${CHART_ID}`)
  console.log(`Run time: ${NOW_ISO}`)
  console.log(`Scope:    15 unique entries (GT.050-064) × 6 tools (Phase 1 + Phase 2A M9)`)
  console.log('')

  // Dynamic import keeps server-only resolver deps out of vitest CI.
  const { callPipelinePlanner } = await import('@/lib/pipeline/pipeline_planner')

  const goldenSet = loadGoldenSet()
  const perToolReports: PerToolReport[] = []
  let totalErrors = 0

  for (const [toolName, entryIds] of Object.entries(TARGET_TOOLS)) {
    console.log(`── ${toolName} ──`)
    const entries = pickEntries(goldenSet, entryIds)
    const details: PerEntryResult[] = []

    for (const entry of entries) {
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

      const selected = predicted.includes(toolName)
      const wasRequired = entry.required_tools.includes(toolName)
      const targetWasRequired = wasRequired && selected
      const forbiddenViolations = (entry.forbidden_tools ?? []).filter(t =>
        predicted.includes(t)
      )

      details.push({
        id: entry.id,
        query: entry.query,
        query_class: entry.query_class,
        target_tool: toolName,
        predicted_tools: predicted,
        target_selected: selected,
        target_was_required: targetWasRequired,
        forbidden_violations: forbiddenViolations,
        error,
        latency_ms,
      })

      const symbol = error ? '✗' : selected ? '✓' : '✗'
      const requiredFlag = wasRequired ? ' [required]' : ''
      console.log(
        `  ${symbol} ${entry.id}${requiredFlag} (${latency_ms}ms)  "${entry.query.slice(0, 64)}${entry.query.length > 64 ? '…' : ''}"`
      )
      if (error) {
        console.log(`      └─ ERROR: ${error}`)
      } else if (VERBOSE) {
        console.log(`      └─ predicted: [${predicted.join(', ')}]`)
      } else if (!selected) {
        console.log(`      └─ predicted: [${predicted.join(', ')}]`)
        console.log(`      └─ MISS: target ${toolName} not in predicted set`)
      }
      if (forbiddenViolations.length > 0) {
        console.log(`      └─ FORBIDDEN VIOLATIONS: ${forbiddenViolations.join(', ')}`)
      }
    }

    const selectedCount = details.filter(d => d.target_selected).length
    const requiredCount = details.filter(d => d.target_was_required).length
    const passesSmoke = selectedCount >= 1 && requiredCount >= 1

    perToolReports.push({
      tool_name: toolName,
      entry_ids: [...entryIds],
      selected_count: selectedCount,
      required_count: requiredCount,
      passes_smoke_test: passesSmoke,
      details,
    })

    console.log(
      `   → selected ${selectedCount}/${entries.length} | required-hit ${requiredCount}/${
        entries.filter(e => e.required_tools.includes(toolName)).length
      } | ${passesSmoke ? 'PASS' : 'FAIL'}`
    )
    console.log('')
  }

  // ── Aggregate ──
  console.log('━'.repeat(78))
  console.log('AGGREGATE')
  console.log('━'.repeat(78))

  console.log(`%-30s %-12s %-12s %-8s`.replace(/%-(\d+)s/g, (_, n) => `Tool`.padEnd(Number(n))))
  console.log(
    `${'Tool'.padEnd(30)} ${'Selected'.padEnd(12)} ${'Required-hit'.padEnd(14)} Verdict`
  )
  console.log('─'.repeat(78))
  for (const r of perToolReports) {
    console.log(
      `${r.tool_name.padEnd(30)} ${`${r.selected_count}/3`.padEnd(12)} ${`${r.required_count}/3`.padEnd(14)} ${
        r.passes_smoke_test ? '✅ PASS' : '❌ FAIL'
      }`
    )
  }

  const allPass = perToolReports.every(r => r.passes_smoke_test) && totalErrors === 0

  // ── Write JSON report ──
  if (!existsSync(OUTPUT_DIR)) mkdirSync(OUTPUT_DIR, { recursive: true })
  const report = {
    probe_name: 'planner_blind_fix_smoke',
    run_at: NOW_ISO,
    model_id: MODEL_ID,
    chart_id: CHART_ID,
    scope: 'GT.053-064 (12 entries × 4 tools restored to RCS on 2026-05-17)',
    target_tools: TARGET_TOOLS,
    per_tool_reports: perToolReports,
    total_planner_errors: totalErrors,
    overall_pass: allPass,
  }
  writeFileSync(OUTPUT_FILE, JSON.stringify(report, null, 2))
  console.log('')
  console.log(`📄 Report → ${path.relative(process.cwd(), OUTPUT_FILE)}`)

  if (allPass) {
    console.log('\n✅ All four tools are reachable by the LLM-first planner.')
    process.exit(0)
  } else {
    console.log('\n❌ At least one tool failed smoke. Investigate before commit.')
    if (totalErrors > 0) {
      console.log(`   • ${totalErrors} planner error(s) — check API keys + network.`)
    }
    for (const r of perToolReports) {
      if (!r.passes_smoke_test) {
        console.log(`   • ${r.tool_name}: selected ${r.selected_count}/3, required-hit ${r.required_count}/3`)
      }
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
