/**
 * INF7-S2: Stop-Confidence Wiring
 *
 * Computes a confidence score (0–1) after each agentic loop iteration based
 * on tool call coverage, source citation density, and chart_facts breadth.
 * When score >= STOP_CONFIDENCE_THRESHOLD the loop may exit early.
 *
 * Configurable via MARSYS_STOP_CONFIDENCE env var (default 0.85).
 *
 * [BUILD-ORCH-J-09] INF7-S2
 */

import type { LoopToolResult } from './agentic_loop'

// ── Constants ─────────────────────────────────────────────────────────────────

export const DEFAULT_STOP_CONFIDENCE_THRESHOLD = 0.85

export function getStopConfidenceThreshold(): number {
  const env = process.env['MARSYS_STOP_CONFIDENCE']
  if (!env) return DEFAULT_STOP_CONFIDENCE_THRESHOLD
  const val = parseFloat(env)
  return isNaN(val) || val < 0 || val > 1 ? DEFAULT_STOP_CONFIDENCE_THRESHOLD : val
}

// ── Types ─────────────────────────────────────────────────────────────────────

export interface ConfidenceInput {
  /** Tool calls made this loop, with their outputs. */
  toolResults: LoopToolResult[]
  /** Synthesis text from the model after the last iteration. */
  synthesisText: string
  /** Iteration count (1-based). */
  iteration: number
  /** Max iterations cap. */
  maxIterations: number
}

export interface ConfidenceScore {
  /** 0–1 composite confidence score. */
  score: number
  /** Whether the loop should exit early based on this score. */
  shouldStop: boolean
  /** Component scores for observability. */
  components: {
    toolCoverage: number
    citationDensity: number
    iterationPenalty: number
  }
}

// ── Scoring ───────────────────────────────────────────────────────────────────

const CITATION_PATTERNS = [
  /\[FORENSIC[^\]]*\]/gi,
  /\[LEL[^\]]*\]/gi,
  /\bSIG\.MSR\.\d+/gi,
  /\[MSR[^\]]*\]/gi,
  /\[GA\.\d+\]/gi,
  /\[B\.11\]/gi,
  /fact_id:/gi,
]

const EXPECTED_TOOL_CATEGORIES = [
  'chart_facts', 'planet', 'house', 'dasha', 'yoga', 'panchang',
  'shadbala', 'ashtakavarga', 'msr', 'cdlm', 'cgm',
]

/**
 * Compute a confidence score for the current loop state.
 * Higher = more complete retrieval + denser citations.
 */
export function computeConfidence(input: ConfidenceInput): ConfidenceScore {
  const toolCoverage = scoreToolCoverage(input.toolResults)
  const citationDensity = scoreCitationDensity(input.synthesisText)
  const iterationPenalty = scoreIterationPenalty(input.iteration, input.maxIterations)

  // Weighted composite: coverage 40%, citations 40%, iteration 20%
  const score = Math.min(
    1,
    toolCoverage * 0.4 + citationDensity * 0.4 + iterationPenalty * 0.2,
  )

  const threshold = getStopConfidenceThreshold()

  return {
    score: Math.round(score * 1000) / 1000,
    shouldStop: score >= threshold,
    components: { toolCoverage, citationDensity, iterationPenalty },
  }
}

function scoreToolCoverage(results: LoopToolResult[]): number {
  if (results.length === 0) return 0

  const toolNames = results.map((r) => r.name.toLowerCase())
  const successCount = results.filter((r) => !r.isError).length
  const successRate = successCount / results.length

  // Count how many expected tool categories were hit
  const covered = EXPECTED_TOOL_CATEGORIES.filter((cat) =>
    toolNames.some((name) => name.includes(cat)),
  ).length
  const categoryFraction = Math.min(covered / 4, 1) // ≥4 categories = full score

  return successRate * 0.6 + categoryFraction * 0.4
}

function scoreCitationDensity(text: string): number {
  if (!text || text.length < 50) return 0

  let totalMatches = 0
  for (const pat of CITATION_PATTERNS) {
    const matches = text.match(pat)
    if (matches) totalMatches += matches.length
  }

  // Normalize: 5+ citations = full score, penalize very short responses
  const wordsPerCitation = totalMatches > 0 ? text.split(/\s+/).length / totalMatches : Infinity
  const citationRate = Math.min(totalMatches / 5, 1)
  const densityBonus = wordsPerCitation <= 100 ? 0.2 : 0

  return Math.min(citationRate + densityBonus, 1)
}

function scoreIterationPenalty(iteration: number, maxIterations: number): number {
  // Reward later iterations (more tool calls = more complete)
  // 1st iteration = 0.3, last = 1.0, linear
  const fraction = iteration / maxIterations
  return 0.3 + fraction * 0.7
}
