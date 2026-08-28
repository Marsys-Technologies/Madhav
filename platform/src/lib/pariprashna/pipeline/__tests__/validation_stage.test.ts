/**
 * validation_stage.test.ts — V3-E-039 remediation proof (EDIR_V3_REGISTER_v1_0.md,
 * S2, synergy/boundary-contract CROSS S8→S9; "worst of the 10 boundary-contract
 * findings: no signal at all, not even a wrong grade").
 *
 * `runValidationStage` is documented, by its own module header, to NEVER fail
 * the turn: an internal error inside the citation/grounding gate is caught and
 * the PASS default (initialized before the try block) is returned. The S4
 * assurance boundary-contract investigation (`.s4_scratch/boundary_contracts.test.ts`,
 * "Boundary 8") proved live that feeding malformed `accumulatedText` throws
 * INSIDE `validateCitationsForStream`, is caught — but because the throw
 * happens BEFORE `em.grade({subject:'citation_gate', ...})` is reached, no wire
 * event fires at all for that turn: not PASS, not WARN, not ERROR. Total
 * silence, not a wrong grade.
 *
 * This test reproduces that exact malformed-input probe against the REAL,
 * unmocked `validateCitationsForStream` (only the pipeline-boundary function
 * under test, `runValidationStage`, is exercised directly — no route-level
 * mocking needed) and proves the fix: the catch block now emits a
 * `citation_gate_errored` flag (and pushes the matching judgment-flag string)
 * BEFORE returning the still-unchanged PASS default. The pass/fail serving
 * decision itself is asserted UNCHANGED (still PASS) — this is an additive
 * signal-emission fix only, per the approved fix scope.
 *
 * Emitter stub pattern (Proxy that records every method call + its body)
 * mirrors `.s4_scratch/boundary_contracts.test.ts`'s own `stubEmitter()`.
 */
import { describe, it, expect } from 'vitest'
import { runValidationStage } from '../validation_stage'
import type { PariprashnaEmitter } from '@/lib/pariprashna/protocol/emitter'

function stubEmitter(): { em: PariprashnaEmitter; calls: Array<{ method: string; body: unknown }> } {
  const calls: Array<{ method: string; body: unknown }> = []
  const handler: ProxyHandler<Record<string, unknown>> = {
    get(_target, prop: string) {
      return (body: unknown) => {
        calls.push({ method: prop, body })
      }
    },
  }
  return { em: new Proxy({}, handler) as unknown as PariprashnaEmitter, calls }
}

describe('V3-E-039 — runValidationStage emits an honest signal on internal error (previously: total silence)', () => {
  it('accumulatedText is undefined (malformed) — PASS default is preserved AND a citation_gate_errored flag now fires', () => {
    const { em, calls } = stubEmitter()
    const judgmentFlags: string[] = []

    let threw: unknown = null
    let result: ReturnType<typeof runValidationStage> | null = null
    try {
      result = runValidationStage({
        em,
        accumulatedText: undefined as unknown as string, // MISSING required field — throws inside validateCitationsForStream
        bundle: { assets: [] },
        validToolResults: [],
        plan: { query_class: 'factual' } as never,
        judgmentFlags,
      })
    } catch (err) {
      threw = err
    }

    // The module's own documented contract: the gate NEVER fails the turn.
    // Unchanged by this fix — same assertion boundary_contracts.test.ts's
    // "Boundary 8" made against the pre-fix code.
    expect(threw).toBeNull()
    expect(result?.gateResult).toBe('PASS')

    // THE FIX: before this change, `calls` would be empty here — no `grade`,
    // no `flag`, nothing. Now the catch block emits a designed signal.
    const gradeCalls = calls.filter((c) => c.method === 'grade')
    expect(gradeCalls, 'em.grade is never reached on this path (the throw happens before it) — unchanged').toHaveLength(0)

    const errorFlag = calls.find(
      (c) => c.method === 'flag' && (c.body as { code?: string }).code === 'citation_gate_errored',
    )
    expect(errorFlag, 'expected a citation_gate_errored flag emitted from the catch block').toBeDefined()
    expect((errorFlag?.body as { level?: string }).level).toBe('error')
    expect(judgmentFlags).toContain('citation_gate_errored')
  })

  it('bundle is circular (a second, independent internal-error cause — JSON.stringify throws) — same silent-PASS-plus-now-signaled behavior', () => {
    const { em, calls } = stubEmitter()
    const judgmentFlags: string[] = []

    // A circular bundle makes `JSON.stringify({ bundle, tool_results })` inside
    // runValidationStage's try block throw "Converting circular structure to
    // JSON" — a DIFFERENT internal-error cause than test 1's malformed
    // accumulatedText, proving the fix covers the catch block generally, not
    // one specific throw site.
    const circular: Record<string, unknown> = {}
    circular.self = circular

    let threw: unknown = null
    let result: ReturnType<typeof runValidationStage> | null = null
    try {
      result = runValidationStage({
        em,
        accumulatedText: 'Your Moon is in Purva Bhadrapada.',
        bundle: circular,
        validToolResults: [],
        plan: { query_class: 'factual' } as never,
        judgmentFlags,
      })
    } catch (err) {
      threw = err
    }

    expect(threw).toBeNull()
    expect(result?.gateResult).toBe('PASS')
    const errorFlag = calls.find(
      (c) => c.method === 'flag' && (c.body as { code?: string }).code === 'citation_gate_errored',
    )
    expect(errorFlag).toBeDefined()
    expect(judgmentFlags).toContain('citation_gate_errored')
  })

  it('NEGATIVE CONTROL: well-formed input that legitimately PASSes emits NO citation_gate_errored flag (proves the assertion is conditional, not vacuous)', () => {
    const { em, calls } = stubEmitter()
    const judgmentFlags: string[] = []

    const result = runValidationStage({
      em,
      accumulatedText: 'A short, uncontroversial reading with no citations required.',
      bundle: { assets: [] },
      validToolResults: [],
      plan: { query_class: 'factual' } as never,
      judgmentFlags,
    })

    expect(result.gateResult).toBe('PASS')
    const errorFlag = calls.find(
      (c) => c.method === 'flag' && (c.body as { code?: string }).code === 'citation_gate_errored',
    )
    expect(errorFlag, 'a real (non-throwing) PASS must NOT raise the errored flag').toBeUndefined()
    expect(judgmentFlags).not.toContain('citation_gate_errored')
    // The healthy path still reaches em.grade (unlike the malformed-input path above).
    expect(calls.some((c) => c.method === 'grade' && (c.body as { subject?: string }).subject === 'citation_gate')).toBe(true)
  })
})
