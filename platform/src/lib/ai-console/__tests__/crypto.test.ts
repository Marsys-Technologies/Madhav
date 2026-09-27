import { createDecipheriv, randomBytes } from 'node:crypto'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { decryptCredential, encryptCredential, type EncryptedCredential } from '../crypto'

const configError = 'AI_CREDENTIAL_CONFIG_INVALID'
let secret: string
let firstKek: string

beforeEach(() => {
  for (const name of Object.keys(process.env)) {
    if (name.startsWith('MARSYS_AI_KEK_')) vi.stubEnv(name, undefined)
  }
  firstKek = randomBytes(32).toString('base64')
  vi.stubEnv('MARSYS_AI_ACTIVE_KEK_VERSION', 'V1')
  vi.stubEnv('MARSYS_AI_KEK_V1', firstKek)
  vi.stubEnv('MARSYS_AI_FINGERPRINT_SECRET', randomBytes(32).toString('base64'))
  secret = `synthetic-${randomBytes(24).toString('hex')}`
})
afterEach(() => vi.unstubAllEnvs())

describe('credential envelope', () => {
  it('round trips exact UTF-8 input and exposes only approved metadata through JSON', () => {
    const input = `${secret}-देव`
    const record = encryptCredential(input)
    expect(decryptCredential(record) === input).toBe(true)
    expect(record.ciphertext.includes(Buffer.from(input))).toBe(false)
    expect(record.nonce).toHaveLength(12)
    expect(record.authTag).toHaveLength(16)
    expect(record.wrapNonce).toHaveLength(12)
    expect(record.wrapAuthTag).toHaveLength(16)
    expect(record.wrappedDataKey).toHaveLength(32)
    expect(Object.keys(JSON.parse(JSON.stringify(record))).sort()).toEqual(['fingerprint', 'keyVersion', 'mask'])
    expect(JSON.stringify(record).includes(secret)).toBe(false)
  })

  it('generates independent data keys and nonces for repeated credentials', () => {
    const one = encryptCredential(secret)
    const two = encryptCredential(secret)
    for (const field of ['ciphertext', 'wrappedDataKey', 'nonce', 'wrapNonce'] as const) {
      expect(one[field].equals(two[field])).toBe(false)
    }
    // Independently unwrap to distinguish fresh DEKs from merely fresh wrapping nonces.
    const unwrap = (record: EncryptedCredential) => {
      const decipher = createDecipheriv('aes-256-gcm', Buffer.from(firstKek, 'base64'), record.wrapNonce)
      decipher.setAAD(Buffer.from(JSON.stringify(['ai-console:credential:v1', record.keyVersion, record.mask, record.fingerprint])))
      decipher.setAuthTag(record.wrapAuthTag)
      return Buffer.concat([decipher.update(record.wrappedDataKey), decipher.final()])
    }
    const keys = [unwrap(one), unwrap(two)]
    try { expect(keys[0].equals(keys[1])).toBe(false) } finally { keys.forEach(key => key.fill(0)) }
  })

  it.each(['ciphertext', 'nonce', 'authTag', 'wrappedDataKey', 'wrapNonce', 'wrapAuthTag'] as const)(
    'rejects tampered %s with a stable error and no raw cause', field => {
      const record = encryptCredential(secret)
      record[field][0] ^= 1
      try {
        decryptCredential(record)
        expect.fail('Tampered envelope was accepted')
      } catch (error) {
        expect(error).toBeInstanceOf(Error)
        expect((error as Error).message).toBe('AI_CREDENTIAL_DECRYPT_FAILED')
        expect((error as Error).cause).toBeUndefined()
        expect(String(error).includes(secret)).toBe(false)
      }
    },
  )

  it.each(['mask', 'fingerprint', 'keyVersion'] as const)('authenticates %s metadata', field => {
    const record = encryptCredential(secret)
    vi.stubEnv('MARSYS_AI_KEK_V2', firstKek)
    record[field] = field === 'keyVersion' ? 'V2'
      : field === 'mask' ? (record.mask === '••••abcd' ? '••••efgh' : '••••abcd')
        : `${record.fingerprint[0] === 'a' ? 'b' : 'a'}${record.fingerprint.slice(1)}`
    expect(() => decryptCredential(record)).toThrow('AI_CREDENTIAL_DECRYPT_FAILED')
  })

  it('uses the new active version while retaining old-version reads and fingerprints', () => {
    const old = encryptCredential(secret)
    vi.stubEnv('MARSYS_AI_ACTIVE_KEK_VERSION', 'V2')
    vi.stubEnv('MARSYS_AI_KEK_V2', randomBytes(32).toString('base64'))
    const current = encryptCredential(secret)
    expect(current.keyVersion).toBe('V2')
    expect(decryptCredential(old) === secret).toBe(true)
    expect(decryptCredential(current) === secret).toBe(true)
    expect(current.fingerprint === old.fingerprint).toBe(true)
    vi.stubEnv('MARSYS_AI_KEK_V1', undefined)
    expect(() => decryptCredential(old)).toThrow('AI_CREDENTIAL_DECRYPT_FAILED')
  })

  it('fingerprints are keyed, deterministic, and sensitive to the complete credential', () => {
    const one = encryptCredential(secret)
    expect(one.fingerprint).toMatch(/^[a-f0-9]{64}$/)
    expect(encryptCredential(secret).fingerprint === one.fingerprint).toBe(true)
    expect(encryptCredential(`${secret}x`).fingerprint === one.fingerprint).toBe(false)
    vi.stubEnv('MARSYS_AI_FINGERPRINT_SECRET', randomBytes(32).toString('base64'))
    expect(encryptCredential(secret).fingerprint === one.fingerprint).toBe(false)
  })

  it('shows at most four safe suffix characters and hides short or unsafe suffixes', () => {
    expect(encryptCredential(`${secret}abcd`).mask).toBe('••••abcd')
    for (const value of ['x', 'abcd', '12345678', `${secret}\n\r\t!`, `${secret}देव`]) {
      expect(encryptCredential(value).mask).toBe('••••')
    }
    expect(() => encryptCredential('')).toThrow('AI_CREDENTIAL_INPUT_INVALID')
    expect(() => encryptCredential('   ')).toThrow('AI_CREDENTIAL_INPUT_INVALID')
  })

  it.each(['MARSYS_AI_ACTIVE_KEK_VERSION', 'MARSYS_AI_KEK_V1', 'MARSYS_AI_FINGERPRINT_SECRET'])(
    'fails closed when %s is absent, for both writes and reads', name => {
      const record = encryptCredential(secret)
      vi.stubEnv(name, undefined)
      expect(() => encryptCredential(secret)).toThrow(configError)
      expect(() => decryptCredential(record)).toThrow(configError)
    },
  )

  it.each(['not-base64', 'A'.repeat(44), Buffer.alloc(31).toString('base64'), Buffer.alloc(33).toString('base64'), `${Buffer.alloc(32).toString('base64')}\n`])(
    'rejects malformed or wrong-length configured material (%#)', value => {
      vi.stubEnv('MARSYS_AI_KEK_V1', value)
      expect(() => encryptCredential(secret)).toThrow(configError)
      vi.stubEnv('MARSYS_AI_KEK_V1', firstKek)
      vi.stubEnv('MARSYS_AI_FINGERPRINT_SECRET', value)
      expect(() => encryptCredential(secret)).toThrow(configError)
    },
  )

  it('rejects fingerprint reuse of either active or retained KEKs', () => {
    vi.stubEnv('MARSYS_AI_FINGERPRINT_SECRET', firstKek)
    expect(() => encryptCredential(secret)).toThrow(configError)
    vi.stubEnv('MARSYS_AI_ACTIVE_KEK_VERSION', 'V2')
    vi.stubEnv('MARSYS_AI_KEK_V2', randomBytes(32).toString('base64'))
    expect(() => encryptCredential(secret)).toThrow(configError)
  })

  it('rejects malformed version identifiers and malformed retained KEKs', () => {
    vi.stubEnv('MARSYS_AI_ACTIVE_KEK_VERSION', '../V1')
    expect(() => encryptCredential(secret)).toThrow(configError)
    vi.stubEnv('MARSYS_AI_ACTIVE_KEK_VERSION', 'V1')
    vi.stubEnv('MARSYS_AI_KEK_OLD', 'malformed')
    expect(() => encryptCredential(secret)).toThrow(configError)
  })

  it('rejects malformed records without leaking input through crypto errors', () => {
    const record = encryptCredential(secret)
    for (const field of ['ciphertext', 'nonce', 'authTag', 'wrappedDataKey', 'wrapNonce', 'wrapAuthTag'] as const) {
      expect(() => decryptCredential({ ...record, [field]: Buffer.alloc(0) })).toThrow('AI_CREDENTIAL_DECRYPT_FAILED')
    }
    expect(() => decryptCredential(null as unknown as EncryptedCredential)).toThrow('AI_CREDENTIAL_DECRYPT_FAILED')
  })
})
