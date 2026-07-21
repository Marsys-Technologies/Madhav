/**
 * completeness_receipt.test.ts — web-side port parity + honesty invariants (W4 core step 4).
 *
 * Mirrors the MCP emitter's contract (platform-mcp/src/lib/completeness_receipt.ts, exercised by
 * platform-mcp/src/__tests__/vidhi_delivery.test.ts): served/empty/dark partition the compiled
 * floor TOTALLY and DISJOINTLY; dark items cite a CR-\d+; observations flip pending→served/empty.
 */
import { describe, expect, it } from 'vitest'
import { compileContract, defaultRegistry } from '../compiler'
import type { ScopeTuple } from '../types'
import {
  emitCompletenessReceipt,
  type FloorItemObservation,
} from '../completeness_receipt'

const CHART = '482012f1-710e-4a25-994a-93821f5871aa'

/** A deepdive tuple compiles a rich floor + machine band (includes known_gap primitives). */
function wealthDeepdiveTuple(): ScopeTuple {
  return {
    intent: 'wealth_deepdive',
    domains: ['wealth'],
    width: 'standard',
    depth: 'deepdive',
    horizon: 'natal',
    intervention: false,
    entitlement: 'native',
  }
}

describe('emitCompletenessReceipt — partition invariants', () => {
  it('served ∪ empty ∪ dark totals the unique compiled floor item set (TOTAL)', () => {
    const contract = compileContract(wealthDeepdiveTuple(), defaultRegistry(), CHART)
    const receipt = emitCompletenessReceipt(contract)

    const uniqueIds = new Set(
      [...contract.floor, ...contract.machine_band].map(i => i.primitive_id),
    )
    const total = receipt.served.length + receipt.empty.length + receipt.dark.length
    expect(total).toBe(uniqueIds.size)
    expect(receipt.coverage.floor_item_total).toBe(uniqueIds.size)
  })

  it('the three buckets are pairwise DISJOINT (each id in exactly one)', () => {
    const contract = compileContract(wealthDeepdiveTuple(), defaultRegistry(), CHART)
    const receipt = emitCompletenessReceipt(contract)
    const seen = new Set<string>()
    for (const id of [
      ...receipt.served.map(s => s.floor_item_id),
      ...receipt.empty.map(e => e.floor_item_id),
      ...receipt.dark.map(d => d.floor_item_id),
    ]) {
      expect(seen.has(id)).toBe(false)
      seen.add(id)
    }
  })

  it('every dark item cites a CR-\\d+ row and carries a note', () => {
    const contract = compileContract(wealthDeepdiveTuple(), defaultRegistry(), CHART)
    const receipt = emitCompletenessReceipt(contract)
    expect(receipt.dark.length).toBeGreaterThan(0) // wealth_deepdive floor has known_gap primitives
    for (const d of receipt.dark) {
      expect(d.cr_row).toMatch(/^CR-\d+$/)
      expect(typeof d.note).toBe('string')
    }
  })

  it('at plan issuance (no observations) every non-dark item is empty with a pending_execution reason', () => {
    const contract = compileContract(wealthDeepdiveTuple(), defaultRegistry(), CHART)
    const receipt = emitCompletenessReceipt(contract)
    expect(receipt.served).toHaveLength(0)
    for (const e of receipt.empty) {
      expect(e.empty_reason).toMatch(/^pending_execution:/)
    }
  })
})

describe('emitCompletenessReceipt — observations', () => {
  it('a served observation moves a non-dark item into served with its source', () => {
    const contract = compileContract(wealthDeepdiveTuple(), defaultRegistry(), CHART)
    const nonDark = [...contract.floor, ...contract.machine_band].filter(i => i.known_gap === null)
    expect(nonDark.length).toBeGreaterThan(1)

    const obs: FloorItemObservation[] = [
      { floor_item_id: nonDark[0]!.primitive_id, status: 'served', source: nonDark[0]!.live_tool },
      { floor_item_id: nonDark[1]!.primitive_id, status: 'empty', empty_reason: 'route_empty' },
    ]
    const receipt = emitCompletenessReceipt(contract, obs)
    expect(receipt.served.some(s => s.floor_item_id === nonDark[0]!.primitive_id && s.source === nonDark[0]!.live_tool)).toBe(true)
    expect(receipt.empty.some(e => e.floor_item_id === nonDark[1]!.primitive_id && e.empty_reason === 'route_empty')).toBe(true)
  })

  it('served takes priority over a known_gap — a served known-gap item is served, not dark', () => {
    const contract = compileContract(wealthDeepdiveTuple(), defaultRegistry(), CHART)
    const darkItem = [...contract.floor, ...contract.machine_band].find(i => i.known_gap !== null)
    expect(darkItem).toBeDefined()
    const receipt = emitCompletenessReceipt(contract, [
      { floor_item_id: darkItem!.primitive_id, status: 'served', source: 'live' },
    ])
    expect(receipt.served.some(s => s.floor_item_id === darkItem!.primitive_id)).toBe(true)
    expect(receipt.dark.some(d => d.floor_item_id === darkItem!.primitive_id)).toBe(false)
  })
})
