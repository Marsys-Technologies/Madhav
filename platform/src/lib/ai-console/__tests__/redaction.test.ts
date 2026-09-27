import { randomBytes } from 'node:crypto'
import { describe, expect, it } from 'vitest'
import { redactAiSecret } from '../crypto'

describe('secret redaction', () => {
  it('recursively removes secrets and raw error/probe fields without mutating input', () => {
    const secret = randomBytes(32).toString('hex')
    const fields = ['apiKey', 'api_key', 'Authorization', 'x-api-key', 'token', 'access_token',
      'refreshToken', 'clientSecret', 'password', 'credential', 'ciphertext', 'wrappedDataKey',
      'wrapped_dek', 'nonce', 'authTag', 'wrapNonce', 'wrapAuthTag', 'kek', 'privateKey',
      'cookie', 'headers', 'body', 'response', 'request', 'message', 'stack', 'cause',
      'stderr', 'stdout', 'prompt', 'completion', 'rawError', 'error_description']
    const input = { nested: [Object.fromEntries(fields.map(field => [field, secret]))], count: 2, ok: true }
    const output = redactAiSecret(input)
    expect(JSON.stringify(output).includes(secret)).toBe(false)
    expect(output).toEqual({ nested: [Object.fromEntries(fields.map(field => [field, '[REDACTED]']))], count: 2, ok: true })
    expect(input.nested[0].apiKey === secret).toBe(true)
  })

  it('retains validated masks, fingerprints and normalized codes but drops arbitrary text', () => {
    expect(redactAiSecret({ mask: '••••abcd', fingerprint: 'a'.repeat(64), code: 'AI_CONNECTION_INVALID',
      status: 'validated', detail: 'untrusted provider content', retryable: false })).toEqual({
      mask: '••••abcd', fingerprint: 'a'.repeat(64), code: 'AI_CONNECTION_INVALID',
      status: 'validated', detail: '[REDACTED]', retryable: false,
    })
    expect(redactAiSecret({ mask: 'raw secret', fingerprint: 'raw secret', code: 'raw secret' })).toEqual({
      mask: '[REDACTED]', fingerprint: '[REDACTED]', code: '[REDACTED]',
    })
    expect(redactAiSecret('unlabelled credential')).toBe('[REDACTED]')
  })

  it('does not serialize errors, binary data, custom instances, or execute getters/toJSON', () => {
    const secret = randomBytes(32).toString('hex')
    let invoked = false
    const object = Object.defineProperty({}, 'detail', { enumerable: true, get() { invoked = true; throw new Error(secret) } })
    const value = { object, error: new Error(secret), bytes: Buffer.from(secret),
      typed: new Uint8Array([1, 2]), custom: new Map([['key', secret]]),
      serialization: { toJSON() { invoked = true; return secret } } }
    expect(JSON.stringify(redactAiSecret(value)).includes(secret)).toBe(false)
    expect(invoked).toBe(false)
  })

  it('handles cycles, deep structures and hostile proxies with a safe finite result', () => {
    const cyclic: Record<string, unknown> = { ok: true }
    cyclic.self = cyclic
    expect(() => JSON.stringify(redactAiSecret(cyclic))).not.toThrow()
    let deep: unknown = 'secret'
    for (let i = 0; i < 1000; i++) deep = { nested: deep }
    expect(() => redactAiSecret(deep)).not.toThrow()
    expect(redactAiSecret(new Proxy({}, { ownKeys() { throw new Error('secret') } }))).toBe('[REDACTED]')
  })

  it('does not expose credentials used as property names in upstream objects', () => {
    const secret = `sk-${randomBytes(16).toString('hex')}`
    expect(JSON.stringify(redactAiSecret({ [secret]: true })).includes(secret)).toBe(false)
  })
})
