/**
 * completeness_receipt.test.ts — D-2 Lane V-0 (BIND_D-2.md §F1.7 ledger row 3).
 *
 * V-2 has not shipped the live completeness-receipt surface yet (cycle-2 lane) — these tests
 * exercise the validator against the DOCUMENTED expected shape per the task's own instruction
 * ("write the validator now against a documented expected shape; it will be exercised live once
 * V-2 deploys"), plus confirm the live-probe entrypoint reports SKIPPED (never a fabricated
 * pass) until V-2's tool/field names are known.
 */
import { describe, it, expect } from 'vitest'
import { validateReceipt, crStatusIsDarkEligible, validateLiveReceipt } from '../completeness_receipt.js'
import type { McpClient } from '../mcp_client.js'

describe('completeness_receipt — validateReceipt (documented shape)', () => {
  it('accepts a well-formed receipt: served/empty/dark disjoint and total', () => {
    const receipt = {
      served: [{ floor_item_id: 'dhana_yoga', source: 'judgment_query.bearing_yogas' }],
      empty: [{ floor_item_id: 'ghati_lagna', empty_reason: 'special_lagna surface returned zero rows for this class' }],
      dark: [{ floor_item_id: 'kp_sublord_significators', cr_row: 'CR-75' }],
    }
    const result = validateReceipt(receipt)
    expect(result.valid).toBe(true)
    expect(result.floor_item_total).toBe(3)
    expect(result.served).toBe(1)
    expect(result.empty).toBe(1)
    expect(result.dark).toBe(1)
  })

  it('rejects a receipt missing the served/empty/dark arrays', () => {
    const result = validateReceipt({ served: [] })
    expect(result.valid).toBe(false)
    expect(result.issues.some((i) => i.message.includes('receipt.empty'))).toBe(true)
    expect(result.issues.some((i) => i.message.includes('receipt.dark'))).toBe(true)
  })

  it('rejects an empty item with no empty_reason (unexplained empty = B.10 violation)', () => {
    const result = validateReceipt({ served: [], empty: [{ floor_item_id: 'x' }], dark: [] })
    expect(result.valid).toBe(false)
    expect(result.issues.some((i) => i.message.includes('B.10'))).toBe(true)
  })

  it('rejects a dark item whose cr_row does not match /^CR-\\d+$/', () => {
    const result = validateReceipt({ served: [], empty: [], dark: [{ floor_item_id: 'x', cr_row: 'defect-75' }] })
    expect(result.valid).toBe(false)
    expect(result.issues.some((i) => i.message.includes('does not match'))).toBe(true)
  })

  it('rejects a dark item citing CR-57 (CLOSED_WITH_EVIDENCE per the register)', () => {
    const result = validateReceipt({ served: [], empty: [], dark: [{ floor_item_id: 'varga_divergence', cr_row: 'CR-57' }] })
    expect(result.valid).toBe(false)
    expect(result.issues.some((i) => i.message.includes('CLOSED'))).toBe(true)
  })

  it('rejects a floor_item_id appearing in two buckets (must be disjoint)', () => {
    const result = validateReceipt({
      served: [{ floor_item_id: 'dup' }],
      empty: [{ floor_item_id: 'dup', empty_reason: 'x' }],
      dark: [],
    })
    expect(result.valid).toBe(false)
    expect(result.issues.some((i) => i.message.includes('more than one'))).toBe(true)
  })

  it('rejects a totally empty receipt (nothing accounted for)', () => {
    const result = validateReceipt({ served: [], empty: [], dark: [] })
    expect(result.valid).toBe(false)
  })
})

describe('completeness_receipt — crStatusIsDarkEligible', () => {
  it('classifies OPEN/LOGGED as eligible, CLOSED* as ineligible, unresolved as unknown', () => {
    expect(crStatusIsDarkEligible('OPEN — ELEVATED')).toBe('eligible')
    expect(crStatusIsDarkEligible('LOGGED')).toBe('eligible')
    expect(crStatusIsDarkEligible('CLOSED_WITH_EVIDENCE [...]')).toBe('ineligible')
    expect(crStatusIsDarkEligible(null)).toBe('unknown')
  })
})

describe('completeness_receipt — validateLiveReceipt (V-2 not shipped yet)', () => {
  it('reports skipped_v2_not_shipped rather than a fabricated pass', async () => {
    const fakeClient = { callTool: async () => ({ raw: { ok: true, status: 200, body: '' }, content: {}, isToolError: false }) } as unknown as McpClient
    const result = await validateLiveReceipt(fakeClient, '482012f1-710e-4a25-994a-93821f5871aa', 'wealth')
    expect(result.status).toBe('skipped_v2_not_shipped')
    expect(result.detail).toMatch(/not shipped/)
  })
})
