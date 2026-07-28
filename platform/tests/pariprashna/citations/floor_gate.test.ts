/**
 * citations/floor_gate.test.ts — PB-2 (SMṚTI) lane M-4.
 *
 * THE CORE DELIVERABLE: proves a `prior_reading`-grade citation can NEVER by
 * itself satisfy the B.11 acharya-floor completeness receipt
 * (`platform/src/lib/vidhi/completeness_receipt.ts`'s `emitCompletenessReceipt`).
 *
 * Two levels of proof:
 *   1. Unit-level — `deriveFloorObservation` returns `status: 'empty'` for
 *      EVERY `prior_reading` input, swept across many floor_item_ids/sources
 *      (a property-style check that there is no input shape that flips it).
 *   2. End-to-end — a REAL compiled vidhi contract (via `compileContract` +
 *      `defaultRegistry`, unmodified) has observations derived for every one
 *      of its floor items using ONLY `prior_reading`-graded citations, fed
 *      through the REAL, unmodified `emitCompletenessReceipt`. The receipt's
 *      `coverage.served` is asserted to be exactly 0 — the floor is reported
 *      unmet/incomplete, never satisfied — with a CONTRAST case (grade
 *      `primary`) proving the same contract's SAME floor items DO reach full
 *      `served` coverage when the evidence is genuinely live-turn, so the
 *      zero-served result above is the grade gate at work, not a fixture that
 *      happens to always read empty.
 */
import { describe, expect, it } from 'vitest'
import { deriveFloorObservation, deriveFloorObservations } from '@/lib/pariprashna/citations/floor_gate'
import type { CitationGrade } from '@/lib/pariprashna/citations/types'
import { emitCompletenessReceipt } from '@/lib/vidhi/completeness_receipt'
import { compileContract, defaultRegistry } from '@/lib/vidhi/compiler'
import type { ScopeTuple } from '@/lib/vidhi/types'

const CHART_ID = '482012f1-710e-4a25-994a-93821f5871aa'

function buildTuple(overrides: Partial<ScopeTuple> = {}): ScopeTuple {
  return {
    intent: 'retrieval_only',
    domains: [],
    width: 'standard',
    depth: 'structure',
    horizon: 'natal',
    intervention: false,
    entitlement: 'native',
    ...overrides,
  }
}

describe('deriveFloorObservation — unit-level structural sweep', () => {
  const sources = ['ganita_positions_get', 'bodha_signals_get', 'kala_windows_get', 'phala_outlook_get', 'mimamsa_insight_get']
  const floorItemIds = ['P-01', 'P-02', 'P-03', 'structural_lagna', 'strength_shadbala', 'temporal_dasha']

  it('NEVER returns served for grade prior_reading, across every (floor_item_id, source) combination', () => {
    for (const floor_item_id of floorItemIds) {
      for (const source of sources) {
        const obs = deriveFloorObservation({ floor_item_id, grade: 'prior_reading', source })
        expect(obs.status).toBe('empty')
        expect(obs.floor_item_id).toBe(floor_item_id)
        if (obs.status === 'empty') {
          expect(obs.empty_reason).toMatch(/prior_reading citation cannot satisfy the B\.11 acharya floor/)
        }
      }
    }
  })

  it('has no parameter that can force prior_reading to served (input surface check)', () => {
    // FloorObservationInput only has floor_item_id / grade / source — there is
    // no `force`, `override`, or `status` field a caller could pass to flip
    // the outcome. This test documents that guarantee at the type level: the
    // object below is the FULL input shape, and it still yields `empty`.
    const obs = deriveFloorObservation({ floor_item_id: 'X', grade: 'prior_reading', source: 'anything' })
    expect(obs.status).toBe('empty')
  })

  it('unverified (hallucination-flagged) also never satisfies the floor', () => {
    const obs = deriveFloorObservation({ floor_item_id: 'X', grade: 'unverified', source: 'ghost_ref' })
    expect(obs.status).toBe('empty')
  })

  it('CONTRAST: primary/supporting/contextual DO satisfy the floor (served)', () => {
    const satisfying: CitationGrade[] = ['primary', 'supporting', 'contextual']
    for (const grade of satisfying) {
      const obs = deriveFloorObservation({ floor_item_id: 'X', grade, source: 'ganita_positions_get' })
      expect(obs.status).toBe('served')
      if (obs.status === 'served') expect(obs.source).toBe('ganita_positions_get')
    }
  })
})

describe('floor-rejection proof — real compiled contract + real emitCompletenessReceipt', () => {
  const registry = defaultRegistry()
  const contract = compileContract(buildTuple(), registry, CHART_ID)
  const allFloorItems = [...contract.floor, ...contract.machine_band]

  it('sanity: the compiled contract has at least one floor item to test against', () => {
    expect(allFloorItems.length).toBeGreaterThan(0)
  })

  it('a plan/turn relying ONLY on prior_reading citations reports the floor as UNMET — coverage.served === 0', () => {
    const observations = deriveFloorObservations(
      allFloorItems.map((item) => ({
        floor_item_id: item.primitive_id,
        grade: 'prior_reading' as const,
        source: item.live_tool,
      })),
    )

    const receipt = emitCompletenessReceipt(contract, observations)

    expect(receipt.served).toHaveLength(0)
    expect(receipt.coverage.served).toBe(0)
    // Every floor item is accounted for (served ∪ empty ∪ dark = total), and
    // since none are served, the full set lands in empty ∪ dark.
    expect(receipt.coverage.floor_item_total).toBe(receipt.empty.length + receipt.dark.length)
    expect(receipt.coverage.empty + receipt.coverage.dark).toBe(receipt.coverage.floor_item_total)
  })

  it('CONTRAST: the SAME contract + SAME floor items DO reach full served coverage with primary-grade evidence', () => {
    const observations = deriveFloorObservations(
      allFloorItems.map((item) => ({
        floor_item_id: item.primitive_id,
        grade: 'primary' as const,
        source: item.live_tool,
      })),
    )

    const receipt = emitCompletenessReceipt(contract, observations)

    // "Served takes priority" in emitCompletenessReceipt's own logic (see its
    // header comment) — every item, dark-eligible or not, is served here.
    expect(receipt.coverage.served).toBe(allFloorItems.length)
    expect(receipt.empty).toHaveLength(0)
    expect(receipt.dark).toHaveLength(0)
  })

  it('a MIX of primary (live) + prior_reading (recalled) evidence serves only the live-evidenced items', () => {
    if (allFloorItems.length < 2) return // guard against a degenerate registry shrink
    const [liveItem, ...recalledItems] = allFloorItems

    const observations = deriveFloorObservations([
      { floor_item_id: liveItem.primitive_id, grade: 'primary', source: liveItem.live_tool },
      ...recalledItems.map((item) => ({
        floor_item_id: item.primitive_id,
        grade: 'prior_reading' as const,
        source: item.live_tool,
      })),
    ])

    const receipt = emitCompletenessReceipt(contract, observations)

    expect(receipt.coverage.served).toBe(1)
    expect(receipt.served[0].floor_item_id).toBe(liveItem.primitive_id)
    // None of the recalled-only items appear in served.
    for (const item of recalledItems) {
      expect(receipt.served.some((s) => s.floor_item_id === item.primitive_id)).toBe(false)
    }
  })
})
