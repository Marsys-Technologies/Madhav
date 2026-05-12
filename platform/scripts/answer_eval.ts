#!/usr/bin/env tsx
/**
 * answer_eval.ts — MARSYS-JIS synthesis answer eval harness
 *
 * Scores synthesis answers against the 5 criteria defined in
 * SYNTHESIS_PROMPT_v1_0.md §6. Runs golden queries against the live
 * /api/chat/consume endpoint and prints a formatted results table.
 *
 * Usage:
 *   npm run answer:eval                    # run all 15 golden queries
 *   npm run answer:eval -- --query-id GQ-001  # run one query
 *
 * Env:
 *   BASE_URL   — endpoint base URL (default: http://localhost:3000)
 *   CHART_ID   — chart ID to query against (required for live calls)
 *   EVAL_STACK — model stack to use (default: nim)
 */

import { GOLDEN_QUERIES, MIN_CITATIONS_BY_CATEGORY, type GoldenQuery, type QueryCategory } from './golden_queries'
import {
  writeEvalRun,
  writeEvalPerformanceRow,
  finalizeEvalRun,
} from '../src/lib/performance/ingestion'

const BASE_URL = process.env.BASE_URL ?? 'http://localhost:3000'
const CHART_ID = process.env.CHART_ID ?? 'default'
const EVAL_STACK = process.env.EVAL_STACK ?? 'nim'

// ─────────────────────────────────────────────────────────────────────────────
// Scoring
// ─────────────────────────────────────────────────────────────────────────────

const L2_5_MARKERS: Record<string, string[]> = {
  MSR:  ['MSR', 'Master Signal Register', '025_HOLISTIC_SYNTHESIS/MSR'],
  UCN:  ['UCN', 'Unified Chart Narrative', '025_HOLISTIC_SYNTHESIS/UCN'],
  CDLM: ['CDLM', 'Cross-Domain Linkage', '025_HOLISTIC_SYNTHESIS/CDLM'],
  CGM:  ['CGM', 'Causal Graph Model', '025_HOLISTIC_SYNTHESIS/CGM'],
  RM:   ['RM', 'Resonance Map', '025_HOLISTIC_SYNTHESIS/RM'],
}

const FORENSIC_MARKERS = ['FORENSIC', 'L1', 'birth chart', 'natal chart']

const PROBABILISTIC_MARKERS = [
  /\bsuggests?\b/gi, /\bindicates?\b/gi, /\bmay\b/gi, /\blikely\b/gi,
  /\btends? to\b/gi, /\bpattern of\b/gi, /\binclines?\b/gi,
  /\bpoints? to\b/gi, /\bcould\b/gi, /\bpotential(ly)?\b/gi,
]

const ORACULAR_MARKERS = [
  /\bwill happen\b/gi, /\bdefinitely\b/gi, /\bcertain(ly)?\b/gi,
  /\bguaranteed?\b/gi, /\bwill definitely\b/gi, /\bwithout (a )?doubt\b/gi,
]

const EXTERNAL_COMPUTATION_MARKER = /\[EXTERNAL_COMPUTATION_REQUIRED/gi

const FABRICATION_PATTERNS = [
  // Naked degree assertions (e.g., "Saturn is at 15°32'") without L1 citation
  /\b\d{1,2}°\s*\d{0,2}'?\s*(?:of\s+)?\w+\b/gi,
]

interface CriteriaScores {
  layer_coverage: number
  b10_compliance: number
  b11_signal: number
  citation_presence: number
  calibration_language: number
}

function scoreLayerCoverage(text: string, expectedLayers: string[]): number {
  if (expectedLayers.length === 0) return 1.0
  const normalizedText = text.toLowerCase()
  let hits = 0
  for (const layer of expectedLayers) {
    const markers = layer === 'FORENSIC' ? FORENSIC_MARKERS : (L2_5_MARKERS[layer] ?? [layer])
    if (markers.some(m => normalizedText.includes(m.toLowerCase()))) hits++
  }
  return hits / expectedLayers.length
}

function scoreB10Compliance(text: string, query: string): number {
  // If the query asks for computed values and the answer uses [EXTERNAL_COMPUTATION_REQUIRED], score 1.0
  const hasExtComputeMarker = EXTERNAL_COMPUTATION_MARKER.test(text)
  // Reset lastIndex after test
  EXTERNAL_COMPUTATION_MARKER.lastIndex = 0

  // Check for naked numerical fabrications (degree assertions without L1 markers)
  let fabricationCount = 0
  for (const pat of FABRICATION_PATTERNS) {
    const matches = text.match(pat) ?? []
    // Only penalize if there's no L1 citation nearby (heuristic: FORENSIC not mentioned)
    if (matches.length > 0 && !text.toLowerCase().includes('forensic') && !text.toLowerCase().includes('l1')) {
      fabricationCount += matches.length
    }
  }

  if (fabricationCount > 3) return 0.0
  if (fabricationCount > 0) return 0.5
  return 1.0
}

function scoreB11Signal(text: string, category: QueryCategory, expectedLayers: string[]): number {
  const normalizedText = text.toLowerCase()

  // Count cross-layer references (references to 2+ different L2.5 artifacts in same paragraph)
  const paragraphs = text.split(/\n{2,}/)
  let crossLayerParagraphs = 0
  for (const para of paragraphs) {
    const lowerPara = para.toLowerCase()
    const layerHits = Object.keys(L2_5_MARKERS).filter(layer =>
      L2_5_MARKERS[layer].some(m => lowerPara.includes(m.toLowerCase()))
    )
    if (layerHits.length >= 2) crossLayerParagraphs++
  }

  // Count total layer references across the full text
  const totalLayerHits = Object.keys(L2_5_MARKERS).filter(layer =>
    L2_5_MARKERS[layer].some(m => normalizedText.includes(m.toLowerCase()))
  ).length

  // Score based on category
  if (category === 'holistic' || category === 'discovery') {
    // Require cross-layer connections and broad layer coverage
    const crossLayerScore = Math.min(crossLayerParagraphs / 2, 1.0)
    const coverageScore = Math.min(totalLayerHits / 3, 1.0)
    return (crossLayerScore + coverageScore) / 2
  } else {
    // Interpretive/predictive: require at least one cross-layer reference
    const crossLayerScore = crossLayerParagraphs > 0 ? 1.0 : 0.0
    const coverageScore = Math.min(totalLayerHits / 2, 1.0)
    return (crossLayerScore + coverageScore) / 2
  }
}

function scoreCitationPresence(text: string, category: QueryCategory, minExpected: number): number {
  // Count citations in format (→ ...) or (→ ...) or → signal-id
  const citationPattern = /\(→[^)]+\)|→\s+\w+-[\w-]+/g
  const citations = text.match(citationPattern) ?? []
  const count = citations.length
  if (minExpected === 0) return 1.0
  return Math.min(count / minExpected, 1.0)
}

function scoreCalibrationLanguage(text: string): number {
  let probabilisticCount = 0
  let oracularCount = 0

  for (const pat of PROBABILISTIC_MARKERS) {
    const matches = text.match(pat) ?? []
    probabilisticCount += matches.length
  }
  for (const pat of ORACULAR_MARKERS) {
    const matches = text.match(pat) ?? []
    oracularCount += matches.length
  }

  return probabilisticCount / (probabilisticCount + oracularCount + 1)
}

function scoreAnswer(text: string, query: GoldenQuery): CriteriaScores {
  return {
    layer_coverage:      scoreLayerCoverage(text, query.expected_layers),
    b10_compliance:      scoreB10Compliance(text, query.query),
    b11_signal:          scoreB11Signal(text, query.category, query.expected_layers),
    citation_presence:   scoreCitationPresence(text, query.category, query.min_citation_count),
    calibration_language: scoreCalibrationLanguage(text),
  }
}

function isPass(scores: CriteriaScores, category: QueryCategory): boolean {
  if (scores.b10_compliance < 0.9) return false
  // Factual queries state verified chart facts — probabilistic framing is
  // not expected and correctly absent. Exempt from calibration gate.
  const calibrationPass = category === 'factual' ? true : scores.calibration_language >= 0.7
  const remaining = [
    scores.layer_coverage >= 0.6,
    scores.b11_signal >= 0.5,
    scores.citation_presence >= 0.6,
    calibrationPass,
  ]
  return remaining.filter(Boolean).length >= 3
}

// ─────────────────────────────────────────────────────────────────────────────
// API call
// ─────────────────────────────────────────────────────────────────────────────

async function callSynthesisEndpoint(query: string): Promise<string> {
  const url = `${BASE_URL}/api/chat/consume`
  const body = {
    chartId: CHART_ID,
    stack: EVAL_STACK,
    messages: [{ role: 'user', parts: [{ type: 'text', text: query }] }],
  }

  const AUTH_TOKEN = process.env.AUTH_TOKEN
  const evalHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
    // Disable keep-alive so a timed-out or reset connection is never reused
    // by the next request (fixes cascading fetch-failed after GQ-006 timeout)
    'Connection': 'close',
  }
  // Server uses cookie-based session auth (__session); Bearer fallback for forward compat
  if (AUTH_TOKEN) evalHeaders['Cookie'] = `__session=${AUTH_TOKEN}`

  const res = await fetch(url, {
    method: 'POST',
    headers: evalHeaders,
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(130_000), // 2m10s — slight buffer over server timeout
  })

  if (!res.ok) {
    throw new Error(`HTTP ${res.status} ${res.statusText}`)
  }

  // Handle streaming (text/event-stream or data: chunks)
  const contentType = res.headers.get('content-type') ?? ''
  if (contentType.includes('text/event-stream') || contentType.includes('text/plain')) {
    const reader = res.body?.getReader()
    if (!reader) return ''
    const decoder = new TextDecoder()
    let text = ''
    let buffer = ''
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      // Parse SSE data lines
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6)
          if (data === '[DONE]') continue
          try {
            const parsed = JSON.parse(data)
            // Vercel AI UI message stream format (x-vercel-ai-ui-message-stream)
            if (parsed.type === 'text-delta' && parsed.delta) text += parsed.delta
            else if (parsed.type === 'error') throw new Error(parsed.errorText ?? 'stream error')
            // Legacy / OpenAI-compatible formats
            else if (typeof parsed === 'string') text += parsed
            else if (parsed.text) text += parsed.text
            else if (parsed.choices?.[0]?.delta?.content) text += parsed.choices[0].delta.content
            else if (parsed.content) text += parsed.content
          } catch (e) {
            if (e instanceof Error && e.message !== 'stream error') {
              // Raw text chunk (JSON parse failed)
              if (data && data !== '[DONE]') text += data
            } else {
              throw e
            }
          }
        }
      }
    }
    return text.trim()
  } else {
    // Non-streaming JSON response
    const json = await res.json() as Record<string, unknown>
    return String(json.text ?? json.content ?? json.answer ?? JSON.stringify(json))
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Formatting
// ─────────────────────────────────────────────────────────────────────────────

function pct(score: number): string {
  return `${Math.round(score * 100)}%`.padStart(4)
}

function printTable(results: Array<{ query: GoldenQuery; scores: CriteriaScores; pass: boolean; error?: string }>): void {
  console.log('\n' + '─'.repeat(110))
  console.log(
    'QID    '.padEnd(8) +
    'Category    '.padEnd(14) +
    'LayerCov'.padEnd(10) +
    'B10'.padEnd(7) +
    'B11'.padEnd(7) +
    'Cites'.padEnd(8) +
    'Calib'.padEnd(8) +
    'RESULT'
  )
  console.log('─'.repeat(110))

  for (const r of results) {
    if (r.error) {
      console.log(`${r.query.id.padEnd(8)}${r.query.category.padEnd(14)}${'SKIPPED — ' + r.error}`)
      continue
    }
    const s = r.scores
    console.log(
      r.query.id.padEnd(8) +
      r.query.category.padEnd(14) +
      pct(s.layer_coverage).padEnd(10) +
      pct(s.b10_compliance).padEnd(7) +
      pct(s.b11_signal).padEnd(7) +
      pct(s.citation_presence).padEnd(8) +
      pct(s.calibration_language).padEnd(8) +
      (r.pass ? '✅ PASS' : '❌ FAIL')
    )
  }

  console.log('─'.repeat(110))

  const completed = results.filter(r => !r.error)
  const passed = completed.filter(r => r.pass)
  const skipped = results.filter(r => r.error)

  const avgScore = (dim: keyof CriteriaScores) =>
    completed.length > 0
      ? completed.reduce((s, r) => s + r.scores[dim], 0) / completed.length
      : 0

  console.log('\nAGGREGATE:')
  console.log(`  Queries run:   ${completed.length} / ${results.length} (${skipped.length} skipped)`)
  console.log(`  Pass rate:     ${passed.length} / ${completed.length} (${completed.length > 0 ? Math.round(passed.length / completed.length * 100) : 0}%)`)
  console.log(`  Avg scores:    layer_coverage=${pct(avgScore('layer_coverage'))}  b10=${pct(avgScore('b10_compliance'))}  b11=${pct(avgScore('b11_signal'))}  citations=${pct(avgScore('citation_presence'))}  calibration=${pct(avgScore('calibration_language'))}`)
  console.log('')
}

// ─────────────────────────────────────────────────────────────────────────────
// Main
// ─────────────────────────────────────────────────────────────────────────────

async function main(): Promise<void> {
  const args = process.argv.slice(2)
  const queryIdFlag = args.indexOf('--query-id')
  const targetQueryId = queryIdFlag >= 0 ? args[queryIdFlag + 1] : undefined

  const queries = targetQueryId
    ? GOLDEN_QUERIES.filter(q => q.id === targetQueryId)
    : GOLDEN_QUERIES

  if (queries.length === 0) {
    console.error(`No queries found${targetQueryId ? ` matching id: ${targetQueryId}` : ''}`)
    process.exit(1)
  }

  console.log(`\nMARSYS-JIS Answer Eval Harness`)
  console.log(`BASE_URL: ${BASE_URL}  CHART_ID: ${CHART_ID}  STACK: ${EVAL_STACK}`)
  console.log(`Running ${queries.length} golden ${queries.length === 1 ? 'query' : 'queries'}...\n`)

  const results: Array<{ query: GoldenQuery; scores: CriteriaScores; pass: boolean; error?: string }> = []

  // Gate I auto-hook: persist this eval invocation as an eval_runs row +
  // one performance_queries row per query. Best-effort: a DB outage logs a
  // warning and skips persistence; the eval itself still runs.
  let evalRunId: string | null = null
  try {
    const r = await writeEvalRun({
      golden_set_version: process.env.GOLDEN_SET_VERSION ?? '1.0',
      synthesis_prompt_version: process.env.SYNTHESIS_PROMPT_VERSION,
      triggered_by: 'answer_eval.ts',
    })
    evalRunId = r.runId
  } catch (err) {
    console.warn('  (gate1 eval auto-hook disabled — could not write eval_runs row):', err instanceof Error ? err.message : err)
  }

  for (const query of queries) {
    process.stdout.write(`  ${query.id} [${query.category}] ... `)
    try {
      const answer = await callSynthesisEndpoint(query.query)
      if (!answer) {
        process.stdout.write('empty response\n')
        results.push({ query, scores: { layer_coverage: 0, b10_compliance: 0, b11_signal: 0, citation_presence: 0, calibration_language: 0 }, pass: false, error: 'empty response' })
        continue
      }
      const scores = scoreAnswer(answer, query)
      const pass = isPass(scores, query.category)
      process.stdout.write(pass ? '✅\n' : '❌\n')
      results.push({ query, scores, pass })
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      process.stdout.write(`skipped (${msg.slice(0, 60)})\n`)
      results.push({
        query,
        scores: { layer_coverage: 0, b10_compliance: 0, b11_signal: 0, citation_presence: 0, calibration_language: 0 },
        pass: false,
        error: msg.slice(0, 80),
      })
    }
  }

  printTable(results)

  if (evalRunId) {
    try {
      // Per-query performance rows. The script's scoring is per-criterion;
      // we map its `pass` boolean to `plan_accuracy_label='correct'|'wrong'`
      // and the b10/b11 sub-scores to the corresponding violation flags.
      const completed = results.filter((r) => !r.error)
      for (const r of completed) {
        const isPredictive = r.query.category === 'predictive'
        await writeEvalPerformanceRow(evalRunId, {
          query_id: r.query.id,
          query_text: r.query.query,
          query_class: r.query.category,
          plan_type: isPredictive ? 'time_indexed_prediction' : 'single_answer',
          plan_tools_selected: [],
          planner_confidence: null,
          latency_planner_ms: null,
          latency_retrieval_ms: null,
          latency_synthesis_ms: null,
          latency_total_ms: null,
          citations_present: r.scores.citation_presence > 0,
          citation_count: Math.round(r.scores.citation_presence * 10),
          synthesis_status: 'success',
          validator_verdict: r.pass ? 'pass' : 'fail',
          disclosure_tier: 'super_admin',
          b10_violation: r.scores.b10_compliance < 1,
          b11_violation: r.scores.b11_signal < 1,
          retrieval_hit: r.scores.layer_coverage > 0,
          retrieval_score_top1: null,
          plan_accuracy_label: r.pass ? 'correct' : 'wrong',
          is_prediction: isPredictive,
        })
      }
      const passed = completed.filter((r) => r.pass)
      const avg = (k: keyof CriteriaScores) =>
        completed.length === 0 ? null : completed.reduce((s, r) => s + r.scores[k], 0) / completed.length
      await finalizeEvalRun(evalRunId, {
        finishedAt: new Date(),
        queryCount: completed.length,
        recall: completed.length > 0 ? passed.length / completed.length : null,
        precision: completed.length > 0 ? passed.length / completed.length : null,
        citationRate: avg('citation_presence'),
        avgLatencyMs: null,
        synthesisPassRate: completed.length > 0 ? passed.length / completed.length : null,
        retrievalHitRate: avg('layer_coverage'),
        b10ComplianceRate: avg('b10_compliance'),
        b11ComplianceRate: avg('b11_signal'),
        notes: `stack=${EVAL_STACK} chart=${CHART_ID}`,
      })
      console.log(`\n  gate1: eval_run ${evalRunId} persisted with ${completed.length} performance_queries rows.`)
    } catch (err) {
      console.warn('  (gate1 eval auto-hook: persistence failed):', err instanceof Error ? err.message : err)
    }
  }
}

main().catch(err => {
  console.error('Fatal:', err)
  process.exit(1)
})
