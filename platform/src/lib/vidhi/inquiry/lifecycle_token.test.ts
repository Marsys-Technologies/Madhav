import { createHmac } from 'node:crypto'
import { describe, expect, it, vi } from 'vitest'
import {
  hashJti,
  issueInquiryLifecycleToken,
  loadInquiryLifecycleSigningKeyRing,
  verifyInquiryLifecycleToken,
  type InquiryLifecycleSigningKeyRing,
} from './lifecycle_token'

const key = 'test-only-inquiry-key-at-least-thirty-two-bytes-long'
const nextKey = 'test-only-next-inquiry-key-at-least-thirty-two-bytes'
const base = {
  sub: 'user-1', inquiry_id: 'inquiry-1', chart_id: 'chart-1',
  contract_hash: 'sha256:contract', execution_plan_hash: 'sha256:plan', contract_state_hash: 'sha256:state', catalog_hash: 'sha256:catalog', compatibility_version: 'planner-scu-v1', overlay_version: null, chart_build_id: null,
  revision: 0, allowed_transition: 'execute' as const, next_action_ids: ['item-001'],
}

function signRawPayload(payload: string, kid = 'inquiry-v1', material = key): string {
  const header = Buffer.from(JSON.stringify({ alg: 'HS256', typ: 'JWT', kid })).toString('base64url')
  const encoded = Buffer.from(payload).toString('base64url')
  const signature = createHmac('sha256', material).update(`${header}.${encoded}`).digest('base64url')
  return `${header}.${encoded}.${signature}`
}

function signClaims(overrides: Record<string, unknown>): string {
  return signRawPayload(JSON.stringify({
    iss: 'madhav-platform', aud: 'madhav-inquiry', ...base,
    iat: 1_800_000_000, exp: 2_000_000_000, jti: 'jti-1', ...overrides,
  }))
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
    const [header, payload, signature] = issued.token.split('.')
    const replacement = payload[0] === 'A' ? 'B' : 'A'
    const tampered = `${header}.${replacement}${payload.slice(1)}.${signature}`
    expect(() => verifyInquiryLifecycleToken(tampered, key, 'user-1')).toThrow('INQUIRY_TOKEN_INVALID_SIGNATURE')
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

  it('issues only with the current kid while accepting a previous key during overlap', () => {
    const beforeRotation = issueInquiryLifecycleToken(base, {
      current: { kid: 'inquiry-v1', material: key },
    })
    const overlap: InquiryLifecycleSigningKeyRing = {
      current: { kid: 'inquiry-v2', material: nextKey },
      previous: [{ kid: 'inquiry-v1', material: key }],
    }
    const afterRotation = issueInquiryLifecycleToken(base, overlap)

    expect(JSON.parse(Buffer.from(afterRotation.token.split('.')[0], 'base64url').toString('utf8')))
      .toMatchObject({ kid: 'inquiry-v2' })
    expect(verifyInquiryLifecycleToken(beforeRotation.token, overlap, 'user-1')).toMatchObject(base)
    expect(verifyInquiryLifecycleToken(afterRotation.token, overlap, 'user-1')).toMatchObject(base)
    expect(() => verifyInquiryLifecycleToken(beforeRotation.token, {
      current: { kid: 'inquiry-v2', material: nextKey },
    }, 'user-1')).toThrow('INQUIRY_TOKEN_UNKNOWN_KID')
  })

  it('loads canonical random-byte configuration and fails closed on malformed rings', () => {
    const current = Buffer.alloc(32, 11).toString('base64url')
    const previous = Buffer.alloc(48, 17).toString('base64url')
    const loaded = loadInquiryLifecycleSigningKeyRing({
      INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID: 'inquiry-v2',
      INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT: current,
      INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS_KID: 'inquiry-v1',
      INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS: previous,
    })
    expect(loaded.current).toMatchObject({ kid: 'inquiry-v2' })
    expect(loaded.previous?.[0]).toMatchObject({ kid: 'inquiry-v1' })

    for (const env of [
      {},
      { INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID: 'inquiry-v1' },
      { INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID: 'not-versioned', INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT: current },
      { INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID: 'inquiry-v1', INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT: 'plain-text-passphrase-that-is-long-enough' },
      { INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID: 'inquiry-v1', INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT: Buffer.alloc(31).toString('base64url') },
      { INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID: 'inquiry-v1', INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT: current, INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS_KID: 'inquiry-v0', INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS: previous },
      { INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID: 'inquiry-v1', INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT: current, INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS_KID: 'inquiry-v1', INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS: previous },
      { INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID: 'inquiry-v1', INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT: current, INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS_KID: 'inquiry-v2' },
      { INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID: 'inquiry-v1', INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT: current, INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS_KID: 'inquiry-v2', INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS: previous },
    ]) {
      expect(() => loadInquiryLifecycleSigningKeyRing(env)).toThrow('INQUIRY_SIGNING_KEY_INVALID')
    }

    expect(() => issueInquiryLifecycleToken(base, {
      current: { kid: 'inquiry-v1', material: key },
      previous: [{ kid: 'inquiry-v2', material: nextKey }],
    })).toThrow('INQUIRY_SIGNING_KEY_INVALID')
  })

  it('rejects a signed token whose kid is outside the configured ring', () => {
    expect(() => verifyInquiryLifecycleToken(
      signRawPayload(JSON.stringify({
        iss: 'madhav-platform', aud: 'madhav-inquiry', ...base,
        iat: 1_800_000_000, exp: 2_000_000_000, jti: 'jti-1',
      }), 'inquiry-v9', nextKey),
      { current: { kid: 'inquiry-v2', material: nextKey } },
      'user-1',
    )).toThrow('INQUIRY_TOKEN_UNKNOWN_KID')
  })

  it('emits only the public kid audit signal after complete verification', () => {
    const onVerifiedKid = vi.fn()
    const issued = issueInquiryLifecycleToken(base, {
      current: { kid: 'inquiry-v2', material: nextKey },
    })
    verifyInquiryLifecycleToken(
      issued.token,
      { current: { kid: 'inquiry-v2', material: nextKey } },
      'user-1',
      onVerifiedKid,
    )
    expect(onVerifiedKid).toHaveBeenCalledExactlyOnceWith('inquiry-v2')
    expect(() => verifyInquiryLifecycleToken(
      issued.token,
      { current: { kid: 'inquiry-v2', material: nextKey } },
      'wrong-user',
      onVerifiedKid,
    )).toThrow('INQUIRY_TOKEN_WRONG_SUBJECT')
    expect(onVerifiedKid).toHaveBeenCalledTimes(1)
  })

  it('normalizes signed invalid JSON to the public malformed-token error', () => {
    expect(() => verifyInquiryLifecycleToken(signRawPayload('{'), key, 'user-1'))
      .toThrow('INQUIRY_TOKEN_MALFORMED')
  })

  it('rejects signed claims with malformed temporal or replay identity fields', () => {
    for (const overrides of [
      { exp: 'never' },
      { iat: 'now' },
      { jti: '' },
      { next_action_ids: ['not-an-action'] },
    ]) {
      expect(() => verifyInquiryLifecycleToken(signClaims(overrides), key, 'user-1'))
        .toThrow('INQUIRY_TOKEN_MALFORMED')
    }
  })
})
