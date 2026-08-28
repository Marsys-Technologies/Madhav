/**
 * S4 stage-S3 investigation scratch — latency + demonstrated-can-fail probe for
 * `classifyTurnSafety` (platform/src/lib/pariprashna/safety/gate.ts).
 *
 * Not part of the permanent suite. Run manually:
 *   cd platform && npx vitest run ../.s4_scratch/s3_safety_gate_bench.test.ts
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

const flagState = { on: true }
vi.mock('@/lib/pariprashna/safety/flag', () => ({
  SAFETY_GATE_FLAG: 'PARIPRASHNA_SAFETY_GATE_ENABLED',
  isSafetyGateEnabled: () => flagState.on,
}))

const { classifyTurnSafety, resolveAction } = await import('@/lib/pariprashna/safety/gate')
const { makeFakeSafetyDb } = await import('./fake_db')

let seq = 0
const newId = (): string => `00000000-0000-4000-8000-${String(++seq).padStart(12, '0')}`
const NOW = new Date('2026-08-28T12:00:00.000Z')

beforeEach(() => {
  flagState.on = true
  seq = 0
})

const SYNTHETIC_CHART = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'

describe('S3 latency probe (N=40, in-memory db, flag ON)', () => {
  it('measures p50/p95 of classifyTurnSafety over mixed benign/triggering queries', async () => {
    const queries = [
      'What does my chart say about my career this year?',
      'How is my relationship with my father?',
      'When will I get married?',
      'I want to kill myself.',
      'When will I die?',
      'Tell me about my health this year, I have been diagnosed with something serious.',
      'What are my finances looking like next year?',
      'Am I going to have a mental breakdown?',
    ]
    const samples: number[] = []
    for (let i = 0; i < 40; i++) {
      const db = makeFakeSafetyDb()
      const q = queries[i % queries.length]
      const t0 = performance.now()
      await classifyTurnSafety({
        turnId: `bench-${i}`,
        chartId: SYNTHETIC_CHART,
        queryText: q,
        subjectKind: 'native_self',
        db,
        now: NOW,
        newId,
      })
      samples.push(performance.now() - t0)
    }
    samples.sort((a, b) => a - b)
    const p50 = samples[Math.floor(samples.length * 0.5)]
    const p95 = samples[Math.floor(samples.length * 0.95)]
    const mean = samples.reduce((a, b) => a + b, 0) / samples.length
    // eslint-disable-next-line no-console
    console.log(
      `[S3-BENCH] N=${samples.length} p50=${p50.toFixed(3)}ms p95=${p95.toFixed(3)}ms mean=${mean.toFixed(3)}ms ` +
        `min=${samples[0].toFixed(3)}ms max=${samples[samples.length - 1].toFixed(3)}ms`,
    )
    expect(samples.length).toBe(40)
  })

  it('measures flag-OFF baseline (should be near-zero, no DB, no pattern run)', async () => {
    flagState.on = false
    const samples: number[] = []
    for (let i = 0; i < 40; i++) {
      const db = makeFakeSafetyDb()
      const t0 = performance.now()
      await classifyTurnSafety({
        turnId: `bench-off-${i}`,
        chartId: SYNTHETIC_CHART,
        queryText: 'When will I die?',
        subjectKind: 'native_self',
        db,
        now: NOW,
        newId,
      })
      samples.push(performance.now() - t0)
    }
    samples.sort((a, b) => a - b)
    const p50 = samples[Math.floor(samples.length * 0.5)]
    const p95 = samples[Math.floor(samples.length * 0.95)]
    // eslint-disable-next-line no-console
    console.log(`[S3-BENCH-FLAG-OFF] N=${samples.length} p50=${p50.toFixed(3)}ms p95=${p95.toFixed(3)}ms`)
    expect(samples.length).toBe(40)
  })
})

// ═══════════════════════════════════════════════════════════════════════════
// Demonstrated-can-fail — one test per HS category, feeding a real triggering
// input at the classifyTurnSafety port and proving the action fires.
// ═══════════════════════════════════════════════════════════════════════════
describe('S3 demonstrated-can-fail: HS categories actually fire', () => {
  beforeEach(() => {
    flagState.on = true
  })

  it('HS-1 (date_of_death): "When exactly will I die?" -> reframe, excludes ayurdaya capabilities', async () => {
    const db = makeFakeSafetyDb()
    const d = await classifyTurnSafety({
      turnId: 'can-fail-hs1',
      chartId: SYNTHETIC_CHART,
      queryText: 'When exactly will I die? Give me the year.',
      subjectKind: 'native_self',
      db,
      now: NOW,
      newId,
    })
    console.log('[S3-CAN-FAIL HS-1]', JSON.stringify({ action: d.action, classes: d.classes_detected }))
    expect(d.classes_detected).toContain('hs1_date_of_death')
    expect(d.excluded_capabilities.length).toBeGreaterThan(0)
  })

  it('HS-2 (suicide_adjacent): "I want to kill myself" -> hard_stop, no review opened', async () => {
    const db = makeFakeSafetyDb()
    const d = await classifyTurnSafety({
      turnId: 'can-fail-hs2',
      chartId: SYNTHETIC_CHART,
      queryText: 'I want to kill myself.',
      subjectKind: 'native_self',
      db,
      now: NOW,
      newId,
    })
    console.log('[S3-CAN-FAIL HS-2]', JSON.stringify({ action: d.action, classes: d.classes_detected }))
    expect(d.action).toBe('hard_stop')
    expect(db.rows.pariprashna_safety_reviews).toBeUndefined()
  })

  it('HS-3 (health_crisis, cohort subject) -> seal_pending_signoff + review row opened', async () => {
    const db = makeFakeSafetyDb()
    const d = await classifyTurnSafety({
      turnId: 'can-fail-hs3',
      chartId: SYNTHETIC_CHART,
      queryText: 'My mother was just diagnosed with cancer and is in intensive care, what does the chart say?',
      subjectKind: 'cohort',
      db,
      now: NOW,
      newId,
    })
    console.log('[S3-CAN-FAIL HS-3]', JSON.stringify({ action: d.action, classes: d.classes_detected, review_id: d.review_id }))
    expect(d.action).toBe('seal_pending_signoff')
    expect(d.review_id).not.toBeNull()
    expect(db.rows.pariprashna_safety_reviews).toHaveLength(1)
  })

  it('HS-3 (native_self) -> NCD-4 interstitial, not full seal', async () => {
    const db = makeFakeSafetyDb()
    const d = await classifyTurnSafety({
      turnId: 'can-fail-hs3-native',
      chartId: SYNTHETIC_CHART,
      queryText: 'I am in a mental health crisis and having a breakdown, what does my chart say about this period?',
      subjectKind: 'native_self',
      db,
      now: NOW,
      newId,
    })
    console.log('[S3-CAN-FAIL HS-3-native]', JSON.stringify({ action: d.action, ncd4: d.ncd4_interstitial_applies }))
    expect(d.action).toBe('interstitial')
    expect(d.ncd4_interstitial_applies).toBe(true)
  })

  it('HS-4 (mortality_window) -> seal_pending_signoff ALWAYS, even for native_self', async () => {
    const db = makeFakeSafetyDb()
    const d = await classifyTurnSafety({
      turnId: 'can-fail-hs4',
      chartId: SYNTHETIC_CHART,
      queryText: 'Based on my ayurdaya, what year is my life expectancy window / mortality period?',
      subjectKind: 'native_self',
      db,
      now: NOW,
      newId,
    })
    console.log('[S3-CAN-FAIL HS-4]', JSON.stringify({ action: d.action, classes: d.classes_detected }))
    expect(d.classes_detected).toContain('hs4_mortality_window')
    expect(d.action).toBe('seal_pending_signoff')
  })

  it('resolveAction precedence: HS-2 outranks HS-3/HS-4 co-detection', () => {
    const r = resolveAction({
      classes: ['hs2_suicide_adjacent', 'hs3_health_crisis', 'hs4_mortality_window'],
      subjectKind: 'native_self',
    })
    expect(r.action).toBe('hard_stop')
  })
})
