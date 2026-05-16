/**
 * β10 — Streaming Citation Validator
 *
 * Validates MSR signal citations in synthesis output and returns structured
 * data part payloads for emission into the UI message stream.
 *
 * This module replaces the "decorative" onFinish gate that only logged.
 * It is called from the route's onFinish (post-stream, but still inside the
 * writer's execution context) and emits citation_gate data parts that the
 * client can render (γ4 adds the visual layer).
 *
 * Gate logic delegates to the existing validateCitations() function in
 * citation_check.ts — this module is a thin adapter that maps results to
 * data part payloads.
 */

import { validateCitations } from '@/lib/synthesis/citation_check'
import type { CitationGatePart } from '@/lib/streams/data_parts'

export interface CitationValidationResult {
  /** The data part to emit, or null if the gate passes cleanly. */
  dataPart: CitationGatePart | null
  /** Raw gate result for trace/logging. */
  gateResult: 'PASS' | 'WARN' | 'ERROR'
  /** Human-readable gate reason. */
  gateReason: string
  /** Distinct citation count in output. */
  layer1Count: number
  /** Citations verified against assembled context. */
  layer2Verified: number
  /** Citations not found in context (training-data leak risk). */
  layer2Leaked: number
}

/**
 * Validate citations in accumulated text against the assembled context.
 * Returns a structured result including the data part to emit (if any).
 *
 * @param outputText     Full assistant response text.
 * @param contextJson    JSON-serialized bundle + tool_results (the assembled context).
 * @param queryClass     Query class for per-class threshold checks.
 * @param gateOverride   When true, ERROR is downgraded to WARN.
 */
export function validateCitationsForStream(
  outputText: string,
  contextJson: string,
  queryClass: string,
  gateOverride: boolean = false,
): CitationValidationResult {
  const raw = validateCitations(outputText, contextJson, queryClass)
  const effectiveResult = raw.gate_result === 'ERROR' && gateOverride ? 'WARN' : raw.gate_result

  let dataPart: CitationGatePart | null = null

  if (effectiveResult === 'ERROR') {
    dataPart = {
      type: 'citation_gate',
      status: 'fail',
      issues: [raw.gate_reason],
    }
  } else if (effectiveResult === 'WARN') {
    dataPart = {
      type: 'citation_gate',
      status: 'warn',
      issues: [raw.gate_reason],
    }
  }
  // PASS: no data part emitted (no news is good news for the client)

  return {
    dataPart,
    gateResult: effectiveResult,
    gateReason: raw.gate_reason,
    layer1Count: raw.layer1_count,
    layer2Verified: raw.layer2_verified,
    layer2Leaked: raw.layer2_leaked,
  }
}
