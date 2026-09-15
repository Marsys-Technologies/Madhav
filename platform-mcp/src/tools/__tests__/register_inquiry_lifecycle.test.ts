import { beforeEach, describe, expect, it, vi } from 'vitest'
import { registerInquiryLifecycleTools, type InquiryRegisteringServer } from '../register_inquiry_lifecycle.js'
import { callInquiryLifecycle } from '../../lib/inquiry_bridge.js'

vi.mock('../../lib/inquiry_bridge.js', () => ({ callInquiryLifecycle: vi.fn(async (_principal, body) => ({ ok: true, echo: body })) }))
const principal = { user_uid: 'user-1', key_id: 'key-1', role: 'guest' as const }

describe('raw inquiry lifecycle MCP surface', () => {
  const handlers = new Map<string, (args: unknown) => Promise<unknown>>()
  beforeEach(() => {
    handlers.clear()
    const server: InquiryRegisteringServer = { tool(name, _description, _schema, handler) { handlers.set(name, handler) } }
    registerInquiryLifecycleTools(server, principal, 'full')
  })

  it('registers start, server execution, and finalize as one lifecycle', () => {
    expect([...handlers.keys()].sort()).toEqual(['inquiry_execute_next', 'inquiry_finalize', 'inquiry_start'])
  })

  it('forwards a strict start contract with authenticated principal out of caller control', async () => {
    await handlers.get('inquiry_start')?.({
      chart_id: '482012f1-0000-4000-8000-000000000001', question: 'wealth outlook',
      scope_tuple: { intent: 'domain_assessment', domains: ['wealth'], width: 'broad', depth: 'deep', horizon: 'far', intervention: 'none', entitlement: 'native' },
    })
    expect(callInquiryLifecycle).toHaveBeenCalledWith(principal, expect.objectContaining({ action: 'start', question: 'wealth outlook' }))
  })

  it('does not expose lifecycle execution outside the full profile', async () => {
    const restricted = new Map<string, (args: unknown) => Promise<unknown>>()
    registerInquiryLifecycleTools({ tool(name, _description, _schema, handler) { restricted.set(name, handler) } }, principal, 'compact')
    const result = await restricted.get('inquiry_finalize')?.({ lifecycle_token: 'token' }) as { isError?: boolean; structuredContent?: { error?: string } }
    expect(result.isError).toBe(true)
    expect(result.structuredContent?.error).toContain('full MCP profile')
  })
})
