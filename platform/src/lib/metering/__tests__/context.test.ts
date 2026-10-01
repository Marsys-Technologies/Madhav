import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({ meter: vi.fn() }))
vi.mock('../model', () => ({ meterModel: mocks.meter }))

import { meteringRequest, meterSharedModel, setMeteringAttribution } from '../context'

const model = { specificationVersion: 'v3' as const, provider: 'test', modelId: 'test' } as never
beforeEach(() => { mocks.meter.mockReset().mockReturnValue({ metered: true }); vi.stubEnv('MARSYS_FLAG_AI_METERING_ENABLED', 'true') })
afterEach(() => vi.unstubAllEnvs())

describe('enabled shared-model attribution', () => {
  it('fails closed without admitted request ownership', () => {
    expect(() => meterSharedModel(model, 'openai', 'test', 'planner')).toThrow('Metering attribution required')
    expect(mocks.meter).not.toHaveBeenCalled()
  })

  it('retains ownership across awaits and isolates simultaneous requests', async () => {
    await Promise.all(['alice', 'bob'].map(async userId => meteringRequest(async () => {
      setMeteringAttribution({ userId, conversationId: `conversation-${userId}`, turnId: `turn-${userId}`,
        channel: 'web', purpose: 'customer', payer: 'platform' })
      await Promise.resolve()
      expect(meterSharedModel(model, 'openai', 'test', 'planner')).toEqual({ metered: true })
    })))
    const contexts = mocks.meter.mock.calls.map(([, context]) => context)
    expect(contexts).toHaveLength(2)
    expect(contexts).toEqual(expect.arrayContaining([
      expect.objectContaining({ userId: 'alice', turnId: 'turn-alice', conversationId: 'conversation-alice' }),
      expect.objectContaining({ userId: 'bob', turnId: 'turn-bob', conversationId: 'conversation-bob' }),
    ]))
    expect(() => meterSharedModel(model, 'openai', 'test', 'planner')).toThrow('Metering attribution required')
  })

  it('returns the original model when metering is disabled', () => {
    vi.stubEnv('MARSYS_FLAG_AI_METERING_ENABLED', 'false')
    expect(meterSharedModel(model, 'openai', 'test', 'planner')).toBe(model)
    expect(mocks.meter).not.toHaveBeenCalled()
  })
})
