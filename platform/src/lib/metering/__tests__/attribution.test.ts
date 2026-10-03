import { describe, expect, it } from 'vitest'
import { classifyMeteringContext } from '../attribution'
import type { MeteringContext } from '../types'

const context = (userId: string, channel: MeteringContext['channel']): MeteringContext => ({
  userId, conversationId: 'conversation', turnId: 'turn', operationId: 'operation',
  channel, purpose: 'customer', payer: 'platform', provider: 'google', model: 'model',
  role: 'planner', aggregation: 'transport',
})

describe('canary metering attribution', () => {
  it('separates an authenticated API probe from customer activity', () => {
    expect(classifyMeteringContext(context('probe-service-account', 'web'))).toMatchObject({
      userId: 'probe-service-account', channel: 'api', purpose: 'validation',
    })
  })

  it('preserves the MCP channel and ordinary customer attribution', () => {
    expect(classifyMeteringContext(context('probe-service-account', 'mcp'))).toMatchObject({
      channel: 'mcp', purpose: 'validation',
    })
    const customer = context('customer-1', 'web')
    expect(classifyMeteringContext(customer)).toBe(customer)
  })
})
