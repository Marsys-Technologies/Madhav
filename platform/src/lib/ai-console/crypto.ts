import 'server-only'
import { createCipheriv, createDecipheriv, createHmac, randomBytes, timingSafeEqual } from 'node:crypto'
import { inspect, types as utilTypes } from 'node:util'
import { AI_ERROR_CODES } from './errors'

export interface EncryptedCredential {
  ciphertext: Buffer
  wrappedDataKey: Buffer
  nonce: Buffer
  authTag: Buffer
  wrapNonce: Buffer
  wrapAuthTag: Buffer
  keyVersion: string
  mask: string
  fingerprint: string
}

const CONFIG_ERROR = 'AI_CREDENTIAL_CONFIG_INVALID'
const DECRYPT_ERROR = 'AI_CREDENTIAL_DECRYPT_FAILED'
const VERSION = /^[A-Za-z0-9][A-Za-z0-9_]{0,63}$/
const MAX_CREDENTIAL_BYTES = 16_384
const REDACTED = '[REDACTED]'

/** Runtime injection only. No dotenv, database key, build-time cache, or fallback. */
function configuration() {
  const keys = new Map<string, Buffer>()
  let fingerprintKey: Buffer | undefined
  const dispose = () => {
    keys.forEach(key => key.fill(0))
    fingerprintKey?.fill(0)
  }
  const decode = (value: string | undefined): Buffer => {
    if (!value || !/^[A-Za-z0-9+/]{43}=$/.test(value)) throw new Error(CONFIG_ERROR)
    const key = Buffer.from(value, 'base64')
    if (key.length !== 32 || key.toString('base64') !== value) {
      key.fill(0)
      throw new Error(CONFIG_ERROR)
    }
    return key
  }
  try {
    const version = process.env.MARSYS_AI_ACTIVE_KEK_VERSION
    if (!version || !VERSION.test(version)) throw new Error(CONFIG_ERROR)
    for (const name of Object.keys(process.env)) {
      if (!name.startsWith('MARSYS_AI_KEK_')) continue
      const keyVersion = name.slice('MARSYS_AI_KEK_'.length)
      if (!VERSION.test(keyVersion)) throw new Error(CONFIG_ERROR)
      keys.set(keyVersion, decode(process.env[name]))
    }
    if (!keys.has(version)) throw new Error(CONFIG_ERROR)
    fingerprintKey = decode(process.env.MARSYS_AI_FINGERPRINT_SECRET)
    for (const key of keys.values()) {
      if (timingSafeEqual(key, fingerprintKey)) throw new Error(CONFIG_ERROR)
    }
    return { version, keys, fingerprintKey, dispose }
  } catch {
    dispose()
    throw new Error(CONFIG_ERROR)
  }
}

function aad(record: Pick<EncryptedCredential, 'keyVersion' | 'mask' | 'fingerprint'>): Buffer {
  return Buffer.from(JSON.stringify(['ai-console:credential:v1', record.keyVersion, record.mask, record.fingerprint]))
}

/** AES-256-GCM for both payload and DEK; wrapping fields map directly to SQL columns. */
export function encryptCredential(plaintext: string): EncryptedCredential {
  const config = configuration()
  let dataKey: Buffer | undefined
  let input: Buffer | undefined
  try {
    if (typeof plaintext !== 'string' || !plaintext.trim() || Buffer.byteLength(plaintext) > MAX_CREDENTIAL_BYTES) {
      throw new Error('AI_CREDENTIAL_INPUT_INVALID')
    }
    input = Buffer.from(plaintext, 'utf8')
    dataKey = randomBytes(32)
    const nonce = randomBytes(12)
    const wrapNonce = randomBytes(12)
    const mask = plaintext.length > 8 && /^[A-Za-z0-9_-]{4}$/.test(plaintext.slice(-4))
      ? `••••${plaintext.slice(-4)}` : '••••'
    const fingerprint = createHmac('sha256', config.fingerprintKey).update(input).digest('hex')
    const metadata = { keyVersion: config.version, mask, fingerprint }
    const authenticated = aad(metadata)
    const cipher = createCipheriv('aes-256-gcm', dataKey, nonce)
    cipher.setAAD(authenticated)
    const ciphertext = Buffer.concat([cipher.update(input), cipher.final()])
    const wrapper = createCipheriv('aes-256-gcm', config.keys.get(config.version)!, wrapNonce)
    wrapper.setAAD(authenticated)
    const wrappedDataKey = Buffer.concat([wrapper.update(dataKey), wrapper.final()])
    const record: EncryptedCredential = { ...metadata, ciphertext, nonce, authTag: cipher.getAuthTag(),
      wrappedDataKey, wrapNonce, wrapAuthTag: wrapper.getAuthTag() }
    // Accidental JSON/console inspection must not serialize cryptographic material.
    // Persistence reads the explicit fields; API code still uses safe projections.
    Object.defineProperties(record, {
      toJSON: { value: () => ({ ...metadata }) },
      [inspect.custom]: { value: () => ({ ...metadata }) },
    })
    return record
  } catch (error) {
    if (error instanceof Error && error.message === 'AI_CREDENTIAL_INPUT_INVALID') throw error
    throw new Error('AI_CREDENTIAL_ENCRYPT_FAILED')
  } finally {
    dataKey?.fill(0)
    input?.fill(0)
    config.dispose()
  }
}

/** Call only after user ownership/activity authorization, immediately before invocation. */
export function decryptCredential(record: EncryptedCredential): string {
  const config = configuration()
  const temporary: Buffer[] = []
  try {
    if (!record || typeof record.keyVersion !== 'string' || !VERSION.test(record.keyVersion)
      || typeof record.mask !== 'string' || !/^••••(?:[A-Za-z0-9_-]{4})?$/.test(record.mask)
      || typeof record.fingerprint !== 'string' || !/^[a-f0-9]{64}$/.test(record.fingerprint)) throw new Error(DECRYPT_ERROR)
    for (const [field, length] of [['nonce', 12], ['authTag', 16], ['wrapNonce', 12],
      ['wrapAuthTag', 16], ['wrappedDataKey', 32]] as const) {
      if (!Buffer.isBuffer(record[field]) || record[field].length !== length) throw new Error(DECRYPT_ERROR)
    }
    if (!Buffer.isBuffer(record.ciphertext) || record.ciphertext.length === 0
      || record.ciphertext.length > MAX_CREDENTIAL_BYTES) throw new Error(DECRYPT_ERROR)
    const kek = config.keys.get(record.keyVersion)
    if (!kek) throw new Error(DECRYPT_ERROR)
    const authenticated = aad(record)
    const wrapper = createDecipheriv('aes-256-gcm', kek, record.wrapNonce)
    wrapper.setAAD(authenticated)
    wrapper.setAuthTag(record.wrapAuthTag)
    // Register update buffers before final() can throw, so unauthenticated bytes are wiped too.
    const keyPart = wrapper.update(record.wrappedDataKey)
    temporary.push(keyPart)
    const keyFinal = wrapper.final()
    temporary.push(keyFinal)
    const dataKey = Buffer.concat([keyPart, keyFinal])
    temporary.push(dataKey)
    const decipher = createDecipheriv('aes-256-gcm', dataKey, record.nonce)
    decipher.setAAD(authenticated)
    decipher.setAuthTag(record.authTag)
    const part = decipher.update(record.ciphertext)
    temporary.push(part)
    const final = decipher.final()
    temporary.push(final)
    const plaintext = Buffer.concat([part, final])
    temporary.push(plaintext)
    return plaintext.toString('utf8')
  } catch {
    throw new Error(DECRYPT_ERROR)
  } finally {
    temporary.forEach(buffer => buffer.fill(0))
    config.dispose()
  }
}

const SENSITIVE_FIELD = /key|secret|credential|token|password|authorization|cookie|cipher|nonce|tag|wrapped|kek|header|body|response|request|message|stack|cause|stderr|stdout|prompt|completion|error|tojson|mask|fingerprint/i
const SAFE_CODES = new Set<string>([...AI_ERROR_CODES, CONFIG_ERROR, DECRYPT_ERROR,
  'AI_CREDENTIAL_ENCRYPT_FAILED', 'AI_CREDENTIAL_INPUT_INVALID'])
const SAFE_STATUS = new Set(['untested', 'validating', 'validated', 'needs_attention', 'invalid', 'unreachable'])
// Property names are upstream input too. Preserve only recognized structural names.
const SAFE_FIELDS = new Set(['nested', 'data', 'metadata', 'details', 'detail', 'items', 'count', 'ok',
  'retryable', 'status', 'code', 'mask', 'fingerprint', 'id', 'userid', 'connectionid', 'providerid',
  'modelid', 'role', 'source', 'latency', 'durationms', 'retrycount', 'keyversion', 'object', 'self',
  'apikey', 'xapikey', 'authorization', 'token', 'accesstoken', 'refreshtoken', 'clientsecret',
  'password', 'credential', 'ciphertext', 'wrappeddatakey', 'wrappeddek', 'nonce', 'authtag',
  'wrapnonce', 'wrapauthtag', 'kek', 'privatekey', 'cookie', 'headers', 'body', 'response', 'request',
  'message', 'stack', 'cause', 'stderr', 'stdout', 'prompt', 'completion', 'rawerror', 'error',
  'errordescription', 'bytes', 'typed', 'custom', 'serialization', 'tojson'])

/**
 * Defense in depth, not an API projection: unknown free text is discarded since an
 * upstream provider may echo a credential under any field. Only allowlisted
 * codes/statuses survive as strings. Untrusted masks/fingerprints are always
 * redacted; trusted server metadata belongs in a separate typed projection.
 * Unknown property names are removed too. Never calls user getters.
 */
export function redactAiSecret(value: unknown): unknown {
  const seen = new WeakSet<object>()
  let remaining = 10_000
  const visit = (item: unknown, field = '', depth = 0): unknown => {
    if (--remaining < 0 || depth > 32) return REDACTED
    if (item === null || typeof item === 'boolean') return item
    if (typeof item === 'number') return Number.isFinite(item) ? item : REDACTED
    if (typeof item === 'string') {
      if (field === 'code' && SAFE_CODES.has(item)) return item
      if (field === 'status' && SAFE_STATUS.has(item)) return item
      return REDACTED
    }
    if (typeof item !== 'object' || utilTypes.isProxy(item) || seen.has(item)) return REDACTED
    seen.add(item)
    try {
      if (Array.isArray(item)) {
        const lengthDescriptor = Object.getOwnPropertyDescriptor(item, 'length')
        const length: unknown = lengthDescriptor && 'value' in lengthDescriptor ? lengthDescriptor.value : undefined
        if (typeof length !== 'number' || !Number.isSafeInteger(length) || length < 0 || length > remaining) return REDACTED
        const output: unknown[] = []
        for (let index = 0; index < length; index++) {
          if (remaining <= 0) return REDACTED
          const descriptor = Object.getOwnPropertyDescriptor(item, String(index))
          output.push(descriptor && 'value' in descriptor ? visit(descriptor.value, '', depth + 1) : REDACTED)
        }
        return output
      }
      const prototype = Object.getPrototypeOf(item)
      if (prototype !== Object.prototype && prototype !== null) return REDACTED
      const output: Record<string, unknown> = Object.create(null)
      // Inspect one own descriptor at a time; never allocate all descriptors for
      // an oversized container before applying the traversal budget.
      for (const key in item) {
        if (--remaining < 0) return REDACTED
        const descriptor = Object.getOwnPropertyDescriptor(item, key)
        if (!descriptor?.enumerable) continue
        // Do not retain arbitrary token-shaped property names or prototype hooks.
        if (!SAFE_FIELDS.has(key.replace(/[-_]/g, '').toLowerCase())) continue
        output[key] = SENSITIVE_FIELD.test(key) || !('value' in descriptor)
          ? REDACTED : visit(descriptor.value, key, depth + 1)
      }
      return output
    } catch {
      return REDACTED
    }
  }
  return visit(value)
}
