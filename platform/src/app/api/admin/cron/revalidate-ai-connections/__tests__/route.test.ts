import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { Pool } from 'pg'
import { configService } from '@/lib/config'
import { POST } from '../route'

const execute = vi.fn()
beforeEach(() => {
  vi.stubEnv('MARSYS_CRON_SECRET', 'test-cron-secret')
  configService.setFlag('AI_CONSOLE_BYOK', true)
  execute.mockReset().mockResolvedValue({ rows: [], rowCount: 0 });
  (globalThis as typeof globalThis & { __pgPool?: Pool }).__pgPool = { query: execute, connect: async () => ({ query: execute, release() {} }) } as unknown as Pool
})
afterEach(() => { vi.unstubAllEnvs(); configService.setFlag('AI_CONSOLE_BYOK', false) })
describe('AI connection cron exact admin guard', () => {
  it.each<Record<string, string>>([{}, { authorization: 'Bearer test-cron-secret' }, { 'x-marsys-cron-secret': 'wrong' }])('rejects unauthorized requests before database work', async headers => {
    expect((await POST(new Request('https://example.test', { method: 'POST', headers }))).status).toBe(401)
    expect(execute).not.toHaveBeenCalled()
  })
  it('rejects absent server secret, including an empty supplied header', async () => {
    vi.stubEnv('MARSYS_CRON_SECRET', '')
    expect((await POST(new Request('https://example.test', { method: 'POST', headers: { 'x-marsys-cron-secret': '' } }))).status).toBe(401)
    expect(execute).not.toHaveBeenCalled()
  })
  it('keeps the feature off and does no work while disabled', async () => {
    configService.setFlag('AI_CONSOLE_BYOK', false)
    expect((await POST(new Request('https://example.test', { method: 'POST', headers: { 'x-marsys-cron-secret': 'test-cron-secret' } }))).status).toBe(404)
    expect(execute).not.toHaveBeenCalled()
  })
  it('accepts the custom header alongside Cloud Scheduler OIDC and returns only counts', async () => {
    const response = await POST(new Request('https://example.test', { method: 'POST', headers: { 'x-marsys-cron-secret': 'test-cron-secret', authorization: 'Bearer unrelated-oidc' } }))
    expect(response.status).toBe(200)
    expect(await response.json()).toEqual({ checked: 0, validated: 0, needsAttention: 0, invalid: 0, unreachable: 0, failed: 0 })
    expect(response.headers.get('cache-control')).toBe('no-store')
    expect(execute.mock.calls.some(([sql]) => String(sql).includes('SKIP LOCKED'))).toBe(true)
  })
  it('redacts unexpected infrastructure failures', async () => {
    execute.mockRejectedValue(new Error('provider-and-database-secret'))
    const response = await POST(new Request('https://example.test', { method: 'POST', headers: { 'x-marsys-cron-secret': 'test-cron-secret' } }))
    expect(response.status).toBe(503)
    expect(await response.text()).not.toContain('provider-and-database-secret')
  })
})
