import { describe, it, expect, vi, beforeEach } from 'vitest'

// ── Mocks ─────────────────────────────────────────────────────────────────────

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({
  query: (...args: unknown[]) => mockQuery(...args),
}))

const mockSetGate = vi.fn()
const mockGetGate = vi.fn()
vi.mock('@/lib/config/configService', () => ({
  setGate: (...args: unknown[]) => mockSetGate(...args),
  getGate: (...args: unknown[]) => mockGetGate(...args),
}))

import {
  handleBudgetAlert,
  isBudgetKillSwitchEngaged,
  BUDGET_KILL_SWITCH_GATE,
  type BudgetAlertPayload,
} from '../budget_guard'

const SAMPLE: BudgetAlertPayload = {
  budgetDisplayName: 'marsys-monthly-cap',
  alertThresholdExceeded: 0.8,
  costAmount: 412.55,
  budgetAmount: 500,
  currencyCode: 'USD',
}

describe('observability/budget_guard', () => {
  beforeEach(() => {
    mockQuery.mockReset()
    mockSetGate.mockReset()
    mockGetGate.mockReset()
    mockQuery.mockResolvedValue({ rows: [{ id: 'row-1' }] })
  })

  describe('handleBudgetAlert', () => {
    it('writes a gate_status row with the alert payload and reason', async () => {
      const res = await handleBudgetAlert(SAMPLE)
      expect(mockQuery).toHaveBeenCalledOnce()
      const [sql, params] = mockQuery.mock.calls[0]
      expect(sql).toMatch(/INSERT INTO gate_status/)
      expect(sql).toMatch(/budget_alert/)
      expect(params).toEqual([
        BUDGET_KILL_SWITCH_GATE,
        JSON.stringify(SAMPLE),
        expect.stringContaining('budget=marsys-monthly-cap'),
      ])
      expect(res.gateStatusRowId).toBe('row-1')
      expect(res.thresholdRatio).toBe(0.8)
    })

    it('does NOT flip the kill-switch below the 100% threshold (default)', async () => {
      const res = await handleBudgetAlert({ ...SAMPLE, alertThresholdExceeded: 0.8 })
      expect(res.killSwitchFlipped).toBe(false)
      expect(mockSetGate).not.toHaveBeenCalled()
    })

    it('flips the kill-switch when threshold >= 1.0', async () => {
      const res = await handleBudgetAlert({ ...SAMPLE, alertThresholdExceeded: 1.0 })
      expect(res.killSwitchFlipped).toBe(true)
      expect(mockSetGate).toHaveBeenCalledOnce()
      const [key, value, principal, opts] = mockSetGate.mock.calls[0]
      expect(key).toBe(BUDGET_KILL_SWITCH_GATE)
      expect(value).toBe(true)
      expect(principal).toBe('system:budget-guard')
      expect(opts.reason).toContain('budget kill-switch')
    })

    it('respects a custom kill threshold', async () => {
      const res = await handleBudgetAlert(
        { ...SAMPLE, alertThresholdExceeded: 0.8 },
        { killThreshold: 0.5 },
      )
      expect(res.killSwitchFlipped).toBe(true)
      expect(mockSetGate).toHaveBeenCalledOnce()
    })

    it('preserves the gate_status row even when setGate throws', async () => {
      mockSetGate.mockRejectedValueOnce(new Error('UNKNOWN_GATE'))
      const res = await handleBudgetAlert({ ...SAMPLE, alertThresholdExceeded: 1.2 })
      // gate_status row written first, succeeded
      expect(res.gateStatusRowId).toBe('row-1')
      // flip attempted but failed → killSwitchFlipped reflects reality
      expect(res.killSwitchFlipped).toBe(false)
      expect(mockSetGate).toHaveBeenCalledOnce()
    })

    it('returns reason string surfacing budget, threshold, cost', async () => {
      const res = await handleBudgetAlert(SAMPLE)
      expect(res.reason).toContain('budget=marsys-monthly-cap')
      expect(res.reason).toContain('threshold=80%')
      expect(res.reason).toContain('412.55USD')
      expect(res.reason).toContain('500.00USD')
    })
  })

  describe('isBudgetKillSwitchEngaged', () => {
    it('returns true when the gate is set to true', async () => {
      mockGetGate.mockResolvedValueOnce(true)
      expect(await isBudgetKillSwitchEngaged()).toBe(true)
      expect(mockGetGate).toHaveBeenCalledWith(BUDGET_KILL_SWITCH_GATE)
    })

    it('returns false when the gate is unset (false)', async () => {
      mockGetGate.mockResolvedValueOnce(false)
      expect(await isBudgetKillSwitchEngaged()).toBe(false)
    })

    it('tolerates a missing/unregistered gate (returns false)', async () => {
      mockGetGate.mockRejectedValueOnce(new Error('UNKNOWN_GATE'))
      expect(await isBudgetKillSwitchEngaged()).toBe(false)
    })
  })
})
