import { describe, expect, it } from 'vitest'
import { deriveClientRequestTurnId, isClientRequestId } from '../request_identity'
const chart='10000000-0000-4000-8000-000000000001'
const nonce='20000000-0000-4000-8000-000000000002'
describe('server-owned request identity', () => {
  it('has a fixed purpose namespace and canonical tuple with verified identity', () => {
    const actual=deriveClientRequestTurnId('alice',chart,nonce)
    expect(actual).toBe('36d8b60e-ecd3-55b5-bf76-c7cbb83c967d')
    expect(actual).not.toBe(nonce)
    expect(deriveClientRequestTurnId('bob',chart,nonce)).not.toBe(actual)
    expect(deriveClientRequestTurnId('alice',nonce,nonce)).not.toBe(actual)
    expect(deriveClientRequestTurnId('alice',chart,chart)).not.toBe(actual)
    expect(deriveClientRequestTurnId('alice',chart.toUpperCase(),nonce.toUpperCase())).toBe(actual)
    expect(deriveClientRequestTurnId('alice|bob',chart,nonce)).not.toBe(deriveClientRequestTurnId('alice',chart,nonce))
  })
  it.each([undefined,null,42,{},'', 'not-a-uuid','00000000-0000-0000-0000-000000000000','ffffffff-ffff-ffff-ffff-ffffffffffff'])(
    'rejects invalid nonce %s', value => expect(isClientRequestId(value)).toBe(false))
})
