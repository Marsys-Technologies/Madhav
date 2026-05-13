import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('server-only', () => ({}))

const { mockProbeModel } = vi.hoisted(() => ({ mockProbeModel: vi.fn() }))

vi.mock('../prober', () => ({ probeModel: mockProbeModel }))
vi.mock('@/lib/models/registry', () => ({
  MODELS: [
    { id: 'model-a' },
    { id: 'model-b' },
    { id: 'model-a' }, // duplicate — should deduplicate
    { id: 'model-c' },
  ],
}))

import { probeAllModels } from '../bulk'

describe('probeAllModels', () => {
  beforeEach(() => { vi.clearAllMocks() })

  it('deduplicates model IDs before probing', async () => {
    mockProbeModel.mockResolvedValue({ model_id: 'x', status: 'pass', latency_ms: 10 })
    await probeAllModels()
    // model-a appears twice in registry but should only probe once
    expect(mockProbeModel).toHaveBeenCalledTimes(3)
  })

  it('tallies pass/fail/timeout correctly', async () => {
    mockProbeModel
      .mockResolvedValueOnce({ model_id: 'model-a', status: 'pass', latency_ms: 10 })
      .mockResolvedValueOnce({ model_id: 'model-b', status: 'fail', latency_ms: null })
      .mockResolvedValueOnce({ model_id: 'model-c', status: 'timeout', latency_ms: null })

    const report = await probeAllModels()
    expect(report.total).toBe(3)
    expect(report.pass).toBe(1)
    expect(report.fail).toBe(1)
    expect(report.timeout).toBe(1)
  })

  it('includes all results in report', async () => {
    mockProbeModel.mockResolvedValue({ model_id: 'any', status: 'pass', latency_ms: 1 })
    const report = await probeAllModels()
    expect(report.results).toHaveLength(3)
  })
})
