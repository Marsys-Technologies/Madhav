#!/usr/bin/env tsx
/**
 * evals/k2/benchmark_pairs_runner.ts — Lane K2 item 4 (EL-05, EL-14).
 *
 * Grades captured naive/expert transcript PAIRS (evals/k2/benchmark_pairs_v1_0.json membership)
 * with the K2 consumption grader and reports the naive→expert DELTA per pair — a reusable,
 * repeatable instrument for the exact comparison EL-05's founding incident made by hand
 * (DARPANA S1-01 naive vs S1-07 expert: ~1/5 vs 5/5 founding-incident findings, same chart).
 *
 * This script does NOT itself run the sealed-harness consumer sub-agents (that requires a fresh
 * agent invocation per question — see SEALED_EVALUATOR_HARNESS_v1_0.md §1 — which is an
 * execution-time activity, not something a standalone script can do). It is the GRADING half:
 * feed it a manifest mapping each pair_id to its already-captured naive/expert transcript files
 * (+ optional final-answer text files) and it computes the deltas. Pairs missing a captured run
 * are reported as an honest `not_yet_run` gap, never silently skipped or fabricated.
 *
 * Manifest shape (JSON):
 * {
 *   "chart_id": "482012f1-710e-4a25-994a-93821f5871aa",
 *   "runs": {
 *     "BP-WEALTH-01": {
 *       "naive":  { "transcript": "path/to/naive.json",  "final_answer_file": "path/to/naive.answer.txt" },
 *       "expert": { "transcript": "path/to/expert.json", "final_answer_file": "path/to/expert.answer.txt" }
 *     }
 *   }
 * }
 *
 * Usage:
 *   npx tsx evals/k2/benchmark_pairs_runner.ts <manifest.json>
 */
import { existsSync, readFileSync } from 'fs'
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'
import { gradeConsumption, DEFAULT_TOP_FINDINGS_482012F1, type FindingRef } from './consumption_grader.js'
import { loadTranscript } from './transcript_utils.js'

const __dirname = dirname(fileURLToPath(import.meta.url))

interface PairDef {
  pair_id: string
  domain: string
  topic: string
  naive: { question: string }
  expert: { question: string }
  same_underlying_topic: string
}
interface PairsFile {
  pairs: PairDef[]
}

interface RunRef {
  transcript: string
  final_answer_file?: string
}
interface Manifest {
  chart_id: string
  runs: Record<string, { naive: RunRef; expert: RunRef }>
}

interface PairGradeDelta {
  pair_id: string
  domain: string
  topic: string
  status: 'graded' | 'not_yet_run'
  naive?: { consumption_ratio: number; volunteered_findings_count: number; volunteering_ratio: number }
  expert?: { consumption_ratio: number; volunteered_findings_count: number; volunteering_ratio: number }
  delta?: { consumption_ratio: number; volunteering_ratio: number }
}

function readFinalAnswer(ref: RunRef, transcriptFinalAnswer: string): string {
  if (ref.final_answer_file && existsSync(ref.final_answer_file)) return readFileSync(ref.final_answer_file, 'utf-8')
  return transcriptFinalAnswer
}

export function gradePair(
  pairDef: PairDef,
  chartId: string,
  runRef: { naive: RunRef; expert: RunRef } | undefined,
  topFindings?: FindingRef[],
): PairGradeDelta {
  if (!runRef) {
    return { pair_id: pairDef.pair_id, domain: pairDef.domain, topic: pairDef.topic, status: 'not_yet_run' }
  }
  const naiveTranscript = loadTranscript(runRef.naive.transcript)
  const expertTranscript = loadTranscript(runRef.expert.transcript)
  const naiveAnswer = readFinalAnswer(runRef.naive, naiveTranscript.final_answer)
  const expertAnswer = readFinalAnswer(runRef.expert, expertTranscript.final_answer)

  const naiveGrade = gradeConsumption(pairDef.domain, chartId, naiveTranscript, naiveAnswer, topFindings)
  const expertGrade = gradeConsumption(pairDef.domain, chartId, expertTranscript, expertAnswer, topFindings)

  return {
    pair_id: pairDef.pair_id,
    domain: pairDef.domain,
    topic: pairDef.topic,
    status: 'graded',
    naive: {
      consumption_ratio: naiveGrade.consumption.consumption_ratio,
      volunteered_findings_count: naiveGrade.volunteered_findings.volunteered_findings_count,
      volunteering_ratio: naiveGrade.volunteered_findings.volunteering_ratio,
    },
    expert: {
      consumption_ratio: expertGrade.consumption.consumption_ratio,
      volunteered_findings_count: expertGrade.volunteered_findings.volunteered_findings_count,
      volunteering_ratio: expertGrade.volunteered_findings.volunteering_ratio,
    },
    delta: {
      consumption_ratio: expertGrade.consumption.consumption_ratio - naiveGrade.consumption.consumption_ratio,
      volunteering_ratio:
        expertGrade.volunteered_findings.volunteering_ratio - naiveGrade.volunteered_findings.volunteering_ratio,
    },
  }
}

export interface BenchmarkPairsReport {
  generated_at: string
  chart_id: string
  pairs_total: number
  pairs_graded: number
  pairs_not_yet_run: number
  mean_consumption_ratio_delta: number | null
  mean_volunteering_ratio_delta: number | null
  results: PairGradeDelta[]
}

export function runBenchmarkPairs(pairsFile: PairsFile, manifest: Manifest): BenchmarkPairsReport {
  const results = pairsFile.pairs.map((p) =>
    gradePair(p, manifest.chart_id, manifest.runs[p.pair_id], DEFAULT_TOP_FINDINGS_482012F1[p.domain as 'wealth' | 'career']),
  )
  const graded = results.filter((r) => r.status === 'graded')
  const mean = (xs: number[]) => (xs.length > 0 ? xs.reduce((a, b) => a + b, 0) / xs.length : null)
  return {
    generated_at: new Date().toISOString(),
    chart_id: manifest.chart_id,
    pairs_total: results.length,
    pairs_graded: graded.length,
    pairs_not_yet_run: results.length - graded.length,
    mean_consumption_ratio_delta: mean(graded.map((r) => r.delta!.consumption_ratio)),
    mean_volunteering_ratio_delta: mean(graded.map((r) => r.delta!.volunteering_ratio)),
    results,
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// CLI
// ─────────────────────────────────────────────────────────────────────────────

function isMain(): boolean {
  return process.argv[1] != null && import.meta.url === `file://${process.argv[1]}`
}

if (isMain()) {
  const [manifestPath] = process.argv.slice(2)
  if (!manifestPath) {
    console.error('Usage: npx tsx evals/k2/benchmark_pairs_runner.ts <manifest.json>')
    process.exit(1)
  }
  const pairsFile = JSON.parse(readFileSync(join(__dirname, 'benchmark_pairs_v1_0.json'), 'utf-8')) as PairsFile
  const manifest = JSON.parse(readFileSync(manifestPath, 'utf-8')) as Manifest
  const report = runBenchmarkPairs(pairsFile, manifest)
  console.log(JSON.stringify(report, null, 2))
  if (report.pairs_not_yet_run > 0) {
    console.warn(
      `\n${report.pairs_not_yet_run}/${report.pairs_total} pair(s) have no captured run yet — ` +
        `honest gap, not fabricated. Run the sealed-harness consumer for both members of each ` +
        `missing pair and add its transcript paths to the manifest.`,
    )
  }
}
