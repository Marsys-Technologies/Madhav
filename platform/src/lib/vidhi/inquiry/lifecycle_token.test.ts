import { describe, expect, it, vi } from 'vitest'
import { hashJti, issueInquiryLifecycleToken, verifyInquiryLifecycleToken } from './lifecycle_token'

const key = 'test-only-inquiry-key-at-least-thirty-two-bytes-long'
const base = {
  sub: 'user-1', inquiry_id: 'inquiry-1', chart_id: 'chart-1',
  contract_hash: 'sha256:contract', execution_plan_hash: 'sha256:plan', contract_state_hash: 'sha256:state', catalog_hash: 'sha256:catalog', compatibility_version: 'planner-scu-v1', overlay_version: null, chart_build_id: null,
  revision: 0, allowed_transition: 'execute' as const, next_action_ids: ['item-001'],
}

describe('inquiry lifecycle token', () => {
  it('binds subject, chart, contract, revision, and next actions', () => {
    const issued = issueInquiryLifecycleToken(base, key)
    const claims = verifyInquiryLifecycleToken(issued.token, key, 'user-1')
    expect(claims).toMatchObject(base)
    expect(hashJti(claims.jti)).toMatch(/^sha256:[a-f0-9]{64}$/)
  })

  it('rejects tampering and a different principal', () => {
    const issued = issueInquiryLifecycleToken(base, key)
    expect(() => verifyInquiryLifecycleToken(`${issued.token.slice(0, -1)}x`, key, 'user-1')).toThrow('INQUIRY_TOKEN_INVALID_SIGNATURE')
    expect(() => verifyInquiryLifecycleToken(issued.token, key, 'user-2')).toThrow('INQUIRY_TOKEN_WRONG_SUBJECT')
  })

  it('rejects expiry and weak signing keys', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-09-13T00:00:00Z'))
    const issued = issueInquiryLifecycleToken({ ...base, ttl_seconds: 60 }, key)
    vi.setSystemTime(new Date('2026-09-13T00:02:00Z'))
    expect(() => verifyInquiryLifecycleToken(issued.token, key, 'user-1')).toThrow('INQUIRY_TOKEN_EXPIRED')
    expect(() => issueInquiryLifecycleToken(base, 'weak')).toThrow('INQUIRY_SIGNING_KEY_INVALID')
    vi.useRealTimers()
  })
})
