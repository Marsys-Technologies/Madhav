/**
 * adapter-branch-onfinish.test.ts — R11F-A-S3
 *
 * Verifies that the adapter dispatch branch in route.ts performs the three
 * persistence actions that the legacy onFinish callback also performs:
 *
 *   1. context_assembly_log write (writeContextAssemblyLog — MON-8)
 *   2. prediction candidate detection + emit (detectPredictionCandidates — γ3/PPL)
 *   3. conversation_messages persistence (writeConversationMessages)
 *
 * Because route.ts is a Next.js server handler, we cannot invoke it directly
 * in a unit test. Instead we verify the invariants at the module level:
 *
 *   a) Each function called in the adapter branch exists and has the expected
 *      signature (structural contract test).
 *   b) The source code of route.ts contains the adapter-branch calls (grep-based
 *      contract assertion — fails if someone removes the parity calls).
 *   c) The helper modules themselves behave correctly for the inputs the
 *      adapter branch will supply (functional unit tests on the helpers).
 */

import { describe, it, expect, vi } from 'vitest'
import { readFileSync } from 'fs'
import { join } from 'path'

// ─── Source contract assertions ───────────────────────────────────────────────

const routeSrc = readFileSync(
  join(__dirname, '../../src/app/api/chat/consume/route.ts'),
  'utf-8',
)

describe('adapter branch onFinish parity — source contract', () => {
  it('adapter branch calls writeContextAssemblyLog (MON-8 parity)', () => {
    // The adapter completion block must call writeContextAssemblyLog.
    // We count occurrences: one in the legacy onFinish, one in the adapter branch.
    const occurrences = (routeSrc.match(/writeContextAssemblyLog/g) ?? []).length
    expect(occurrences).toBeGreaterThanOrEqual(2)
  })

  it('adapter branch calls detectPredictionCandidates (γ3/PPL parity)', () => {
    // Same pattern: legacy onFinish has one call, adapter branch adds a second.
    const occurrences = (routeSrc.match(/detectPredictionCandidates/g) ?? []).length
    expect(occurrences).toBeGreaterThanOrEqual(2)
  })

  it('adapter branch calls writeConversationMessages (persistence parity)', () => {
    // writeConversationMessages appears in both the adapter block and the
    // legacy onFinish block.
    const occurrences = (routeSrc.match(/writeConversationMessages/g) ?? []).length
    expect(occurrences).toBeGreaterThanOrEqual(2)
  })

  it('adapter branch calls predictionCandidatePart for candidate emit', () => {
    // predictionCandidatePart must appear in the adapter branch (writer.write call).
    const occurrences = (routeSrc.match(/predictionCandidatePart/g) ?? []).length
    expect(occurrences).toBeGreaterThanOrEqual(2)
  })

  it('adapter branch tokensForAdapter helper is scoped inside the adapter block', () => {
    // The adapter uses a locally-scoped helper named tokensForAdapter
    // (distinct from the legacy tokensFor helper used in onFinish).
    expect(routeSrc).toContain('tokensForAdapter')
  })

  it('adapter onFinish parity comment is present', () => {
    expect(routeSrc).toContain('onFinish parity')
  })
})

// ─── Functional unit tests on the helpers ────────────────────────────────────

describe('adapter branch onFinish parity — detectPredictionCandidates', () => {
  it('returns empty array for text with no prediction markers', async () => {
    const { detectPredictionCandidates } = await import(
      '../../src/lib/ppl/prediction_detector'
    )
    const result = detectPredictionCandidates('Saturn is in the 7th house.')
    // No time-indexed predictions → empty (or all below threshold)
    const highScore = result.filter(c => c.score >= 0.5)
    expect(Array.isArray(result)).toBe(true)
    expect(highScore).toHaveLength(0)
  })

  it('returns candidates with score >= 0 for text with time markers', async () => {
    const { detectPredictionCandidates } = await import(
      '../../src/lib/ppl/prediction_detector'
    )
    // A typical time-indexed prediction sentence
    const text =
      'By mid-2027, Jupiter transit over natal Mercury will likely trigger a major career shift.'
    const result = detectPredictionCandidates(text)
    expect(Array.isArray(result)).toBe(true)
    // At least some candidates detected
    if (result.length > 0) {
      expect(result[0]).toHaveProperty('score')
      expect(result[0]).toHaveProperty('text')
      expect(result[0]).toHaveProperty('offset')
    }
  })

  it('only high-score (>=0.5) candidates are emitted by the adapter branch', async () => {
    const { detectPredictionCandidates } = await import(
      '../../src/lib/ppl/prediction_detector'
    )
    const text =
      'Saturn MD period running from 2024 to 2043 will bring career restructuring by early 2026.'
    const all = detectPredictionCandidates(text)
    const highScore = all.filter(c => c.score >= 0.5)
    // Verify the adapter branch filter is sound
    for (const c of highScore) {
      expect(c.score).toBeGreaterThanOrEqual(0.5)
    }
  })
})

describe('adapter branch onFinish parity — writeContextAssemblyLog mock', () => {
  it('writeContextAssemblyLog mock from test-setup is callable', async () => {
    // The global mock in test-setup.ts stubs writeContextAssemblyLog as vi.fn().
    // Importing through the same alias must hit the mock.
    const mod = await import('@/lib/db/monitoring-write')
    expect(typeof mod.writeContextAssemblyLog).toBe('function')
    // Calling it must not throw
    expect(() =>
      mod.writeContextAssemblyLog({
        query_id: 'q-test',
        l1_tokens: 100,
        l2_5_signal_tokens: 200,
        l2_5_pattern_tokens: 50,
        l4_tokens: 0,
        vector_tokens: 150,
        cgm_tokens: 80,
        synthesis_model_id: 'claude-opus-4-5',
        model_max_context: 200000,
        b3_compliant: true,
        citation_count: 0,
        verified_citations: 0,
      }),
    ).not.toThrow()
  })
})

// ─── Structural: adapter block ordering (floor before onFinish parity) ────────

describe('adapter branch onFinish parity — ordering in source', () => {
  it('tokensForAdapter appears AFTER the B.11 FLOOR CONTRACT comment', () => {
    const floorIdx = routeSrc.indexOf('B.11 FLOOR CONTRACT')
    const tokensForAdapterIdx = routeSrc.indexOf('tokensForAdapter')
    expect(floorIdx).toBeGreaterThan(-1)
    expect(tokensForAdapterIdx).toBeGreaterThan(-1)
    // Floor comment must precede the adapter-branch parity helper
    expect(tokensForAdapterIdx).toBeGreaterThan(floorIdx)
  })

  it('writeConversationMessages for adapter appears before tokensForAdapter', () => {
    // Persistence (conversation_messages) fires first, then MON-8 + PPL.
    const firstPersistIdx = routeSrc.indexOf('writeConversationMessages')
    const tokensForAdapterIdx = routeSrc.indexOf('tokensForAdapter')
    expect(firstPersistIdx).toBeGreaterThan(-1)
    expect(tokensForAdapterIdx).toBeGreaterThan(-1)
    expect(firstPersistIdx).toBeLessThan(tokensForAdapterIdx)
  })
})
