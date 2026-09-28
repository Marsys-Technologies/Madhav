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

  it('retains normalized codes but does not trust mask or fingerprint shapes', () => {
    expect(redactAiSecret({ mask: '••••abcd', fingerprint: 'a'.repeat(64), code: 'AI_CONNECTION_INVALID',
      status: 'validated', detail: 'untrusted provider content', retryable: false })).toEqual({
      mask: '[REDACTED]', fingerprint: '[REDACTED]', code: 'AI_CONNECTION_INVALID',
      status: 'validated', detail: '[REDACTED]', retryable: false,
    })
    expect(redactAiSecret({ mask: 'raw secret', fingerprint: 'raw secret', code: 'raw secret' })).toEqual({
      mask: '[REDACTED]', fingerprint: '[REDACTED]', code: '[REDACTED]',
    })
    expect(redactAiSecret('unlabelled credential')).toBe('[REDACTED]')
  })

  it('redacts hex-shaped credentials and fabricated masks at every nesting level', () => {
    const secret = randomBytes(32).toString('hex')
    const mask = `••••${secret.slice(-4)}`
    const output = redactAiSecret({ fingerprint: secret, mask,
      nested: [{ fingerprint: secret, mask, ok: true }] })
    expect(JSON.stringify(output).includes(secret)).toBe(false)
    expect(JSON.stringify(output).includes(mask)).toBe(false)
    expect(output).toEqual({ fingerprint: '[REDACTED]', mask: '[REDACTED]',
      nested: [{ fingerprint: '[REDACTED]', mask: '[REDACTED]', ok: true }] })
  })

  it('rejects changing-length array proxies before invoking any traps', () => {
    let accesses = 0
    let introspections = 0
    const proxy = new Proxy([], {
      get(target, key, receiver) {
        accesses++
        return key === 'length' ? (accesses === 1 ? 1 : 10_001) : Reflect.get(target, key, receiver)
      },
      getPrototypeOf(target) { introspections++; return Reflect.getPrototypeOf(target) },
      ownKeys(target) { introspections++; return Reflect.ownKeys(target) },
      getOwnPropertyDescriptor(target, key) { introspections++; return Reflect.getOwnPropertyDescriptor(target, key) },
    })
    expect(redactAiSecret(proxy) === '[REDACTED]').toBe(true)
    expect(accesses).toBe(0)
    expect(introspections).toBe(0)
    const revoked = Proxy.revocable([], {})
    revoked.revoke()
    expect(redactAiSecret(revoked.proxy)).toBe('[REDACTED]')
  })

  it('bounds oversized arrays and object containers without invoking accessors', () => {
    let invoked = false
    const sparse = new Array(2 ** 32 - 1)
    const dense = Array.from({ length: 10_001 }, () => true)
    const container = Object.fromEntries(Array.from({ length: 10_001 }, (_, i) => [`entry${i}`, true]))
    for (const item of [sparse, dense, container]) {
      Object.defineProperty(item, 'detail', { enumerable: true, get() { invoked = true; return 'untrusted' } })
      expect(redactAiSecret(item)).toBe('[REDACTED]')
    }
    const arrayWithGetter = Object.defineProperty([true], '0', { get() { invoked = true; return 'untrusted' } })
    expect(redactAiSecret(arrayWithGetter)).toEqual(['[REDACTED]'])
    expect(invoked).toBe(false)
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
