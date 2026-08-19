/**
 * Paripraśna pipeline — VALIDATION STAGE (P0-C / RF-1).
 *
 * Port: `Grounding/Safety Validation`.
 *
 * The B.11 citation gate at adapter-path parity: the turn's prose is validated
 * against the assembled evidence context and the result is surfaced as a
 * `grade` plus, on WARN/ERROR, a `flag` and a judgment-flag entry.
 *
 * The gate NEVER fails the turn. A throw inside the validator is caught,
 * logged, and swallowed — the reader keeps their reading and the outcome stays
 * at its PASS default. That is a deliberate pre-existing behaviour, carried
 * over verbatim; note that it means "no citation_gate grade on the wire" is the
 * only observable signal that the gate errored. Flagged for a later lane, not
 * changed here.
 */

import { validateCitationsForStream } from '@/lib/synthesis/streaming_citation_validator'
import { configService } from '@/lib/config/index'
import type { PipelinePlan } from '@/lib/pipeline/types'
import type { ToolBundle } from '@/lib/retrieval/shared_types'
import type { PariprashnaEmitter } from '@/lib/pariprashna/protocol/emitter'

export interface CitationGateOutcome {
  gateResult: 'PASS' | 'WARN' | 'ERROR'
  layer1Count: number
  layer2Verified: number
}

export function runValidationStage(args: {
  em: PariprashnaEmitter
  accumulatedText: string
  bundle: unknown
  validToolResults: ToolBundle[]
  plan: PipelinePlan
  /** Mutated in place, exactly as the single-closure route did. */
  judgmentFlags: string[]
}): CitationGateOutcome {
  const { em, accumulatedText, bundle, validToolResults, plan, judgmentFlags } = args

  let citationGateResult: 'PASS' | 'WARN' | 'ERROR' = 'PASS'
  let citationL1Count = 0
  let citationL2Verified = 0
  try {
    const assembledContextJson = JSON.stringify({ bundle, tool_results: validToolResults })
    const overrideOn = configService.getFlag('CITATION_GATE_OVERRIDE')
    const validation = validateCitationsForStream(
      accumulatedText,
      assembledContextJson,
      plan.query_class as Parameters<typeof validateCitationsForStream>[2],
      overrideOn,
    )
    citationGateResult = validation.gateResult
    citationL1Count = validation.layer1Count
    citationL2Verified = validation.layer2Verified
    em.grade({ subject: 'citation_gate', grade: validation.gateResult, detail: validation.gateReason })
    if (validation.gateResult === 'WARN') {
      judgmentFlags.push('citation_gate_warn')
      em.flag({ code: 'citation_gate_warn', level: 'warn', detail: validation.gateReason })
    } else if (validation.gateResult === 'ERROR') {
      judgmentFlags.push('citation_gate_error')
      em.flag({ code: 'citation_gate_error', level: 'error', detail: validation.gateReason })
    }
  } catch (err) {
    console.error('[pariprashna] citation gate error', err)
  }

  return {
    gateResult: citationGateResult,
    layer1Count: citationL1Count,
    layer2Verified: citationL2Verified,
  }
}
