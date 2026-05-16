/**
 * β10 — Streaming Citation Validator tests.
 *
 * Covers:
 * - validateCitationsForStream returns PASS with no data part when text has verified citations
 * - validateCitationsForStream returns WARN (data-part) when citations are unverified (leak)
 * - validateCitationsForStream returns ERROR (data-part) when no citations in output
 * - gateOverride=true downgrades ERROR to WARN
 * - dataPart shape matches CitationGatePart schema
 * - Route emits citation_gate data part via writer.write (source assertion)
 * - Route uses validateCitationsForStream (not validateCitations directly)
 */
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'fs'
import { join } from 'path'

const src = (rel: string) => readFileSync(join(process.cwd(), rel), 'utf-8')

const route = src('src/app/api/chat/consume/route.ts')
const validatorSrc = src('src/lib/synthesis/streaming_citation_validator.ts')

// ── Unit: validateCitationsForStream ──────────────────────────────────────────

import { validateCitationsForStream } from '@/lib/synthesis/streaming_citation_validator'

const CONTEXT_WITH_SIGNAL = JSON.stringify({
  bundle: { mandatory_context: [{ content: 'SIG.MSR.142 indicates strong Mars placement' }] },
  tool_results: [{ tool_name: 'msr_sql', results: [{ content: 'SIG.MSR.142 verified in L2.5' }] }],
})

const CONTEXT_WITHOUT_SIGNAL = JSON.stringify({
  bundle: { mandatory_context: [{ content: 'No signals here' }] },
  tool_results: [],
})

describe('validateCitationsForStream — PASS case', () => {
  it('returns null dataPart when citation is verified in context', () => {
    const outputText = 'The SIG.MSR.142 signal shows strong Mars energy.'
    const result = validateCitationsForStream(outputText, CONTEXT_WITH_SIGNAL, 'interpretive')
    expect(result.gateResult).toBe('PASS')
    expect(result.dataPart).toBeNull()
    expect(result.layer1Count).toBe(1)
    expect(result.layer2Verified).toBe(1)
    expect(result.layer2Leaked).toBe(0)
  })

  it('returns null dataPart for factual query class with no minimum citations required', () => {
    const result = validateCitationsForStream('Mars in the 1st house.', CONTEXT_WITHOUT_SIGNAL, 'factual')
    expect(result.gateResult).toBe('PASS')
    expect(result.dataPart).toBeNull()
  })
})

describe('validateCitationsForStream — WARN case (training-data leak)', () => {
  it('returns warn dataPart when citations in output but NOT in context', () => {
    const outputText = 'SIG.MSR.999 signals career achievement via 10th lord.'
    const result = validateCitationsForStream(outputText, CONTEXT_WITHOUT_SIGNAL, 'interpretive')
    expect(result.gateResult).toBe('WARN')
    expect(result.dataPart).not.toBeNull()
    expect(result.dataPart?.type).toBe('citation_gate')
    expect(result.dataPart?.status).toBe('warn')
    expect(result.dataPart?.issues).toHaveLength(1)
    expect(result.layer1Count).toBe(1)
    expect(result.layer2Leaked).toBe(1)
  })
})

describe('validateCitationsForStream — ERROR case', () => {
  // Only prescriptive classes (remedial, predictive) trigger ERROR when citations are absent.
  it('returns fail dataPart when prescriptive (remedial) query has no citations', () => {
    const result = validateCitationsForStream(
      'The answer has no citations at all.',
      CONTEXT_WITHOUT_SIGNAL,
      'remedial', // prescriptive class
      false, // no override
    )
    expect(result.gateResult).toBe('ERROR')
    expect(result.dataPart).not.toBeNull()
    expect(result.dataPart?.type).toBe('citation_gate')
    expect(result.dataPart?.status).toBe('fail')
    expect(result.dataPart?.issues).toHaveLength(1)
  })

  it('override=true downgrades ERROR to WARN and returns warn dataPart', () => {
    const result = validateCitationsForStream(
      'The answer has no citations.',
      CONTEXT_WITHOUT_SIGNAL,
      'predictive', // prescriptive class
      true, // override ON
    )
    expect(result.gateResult).toBe('WARN')
    expect(result.dataPart?.status).toBe('warn')
  })
})

describe('validateCitationsForStream — schema compliance', () => {
  it('dataPart conforms to CitationGatePart shape', () => {
    const result = validateCitationsForStream(
      'SIG.MSR.888 unverified citation.',
      CONTEXT_WITHOUT_SIGNAL,
      'holistic',
    )
    const part = result.dataPart
    expect(part).not.toBeNull()
    expect(typeof part?.type).toBe('string')
    expect(part?.type).toBe('citation_gate')
    expect(['pass', 'warn', 'fail']).toContain(part?.status)
    expect(Array.isArray(part?.issues)).toBe(true)
  })
})

// ── Source assertions: route and validator module ─────────────────────────────

describe('route.ts — β10 citation gate at the wire', () => {
  it('imports validateCitationsForStream (not validateCitations directly)', () => {
    expect(route).toContain('validateCitationsForStream')
    expect(route).not.toContain("import { validateCitations }")
  })

  it('emits citation_gate data part via writer.write', () => {
    expect(route).toContain("'data-citation-gate'")
    expect(route).toContain('citationValidation.dataPart')
  })
})

describe('streaming_citation_validator.ts — module structure', () => {
  it('exports validateCitationsForStream', () => {
    expect(validatorSrc).toContain('export function validateCitationsForStream')
  })

  it('returns dataPart field in result', () => {
    expect(validatorSrc).toContain('dataPart')
  })

  it('maps ERROR to fail status', () => {
    expect(validatorSrc).toContain("status: 'fail'")
  })

  it('maps WARN to warn status', () => {
    expect(validatorSrc).toContain("status: 'warn'")
  })

  it('PASS case: dataPart initialized to null (gate returns null when passing)', () => {
    // The module initializes dataPart to null and only sets it on WARN/ERROR.
    expect(validatorSrc).toContain('| null = null')
  })
})
