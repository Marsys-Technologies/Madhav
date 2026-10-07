import { describe, it, expect } from 'vitest'
import { NextRequest } from 'next/server'
import { proxy } from '@/proxy'
describe('Anonymous share links stop at the read-only public boundary', () => {
  it.each(['/share/k3v9','/share/k3v9/print'])('admits %s without requiring a private account', async path => {
    expect((await proxy(new NextRequest(`http://localhost${path}`))).status).toBe(200)
  })
  it.each(['/share/k3v9/delete','/sharex/k3v9','/clients/chart/pariprashna/print?conversationId=reading','/readings/reading'])('keeps private/non-share route %s session-gated', async path => {
    expect((await proxy(new NextRequest(`http://localhost${path}`))).status).toBe(307)
  })
  it('keeps share creation and revoke APIs session-gated', async () => {
    expect((await proxy(new NextRequest('http://localhost/api/conversations/reading/share',{method:'POST'}))).status).toBe(401)
  })
})
