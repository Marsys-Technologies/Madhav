import { createHmac, createHash, randomUUID, timingSafeEqual } from 'node:crypto'

export interface InquiryLifecycleClaims {
  readonly iss: 'madhav-platform'
  readonly aud: 'madhav-inquiry'
  readonly sub: string
  readonly inquiry_id: string
  readonly chart_id: string
  readonly contract_hash: string
  readonly execution_plan_hash: string
  /** Authenticates the mutable, revision-specific contract progress. */
  readonly contract_state_hash: string
  readonly catalog_hash: string
  readonly compatibility_version: string
  readonly overlay_version: string | null
  readonly chart_build_id: string | null
  readonly revision: number
  readonly allowed_transition: 'execute' | 'finalize'
  readonly next_action_ids: readonly string[]
  readonly iat: number
  readonly exp: number
  readonly jti: string
}

export interface InquiryLifecycleSigningKey {
  /** Public, non-secret key-version identifier carried in the JWT header. */
  readonly kid: string
  /** Raw HMAC key material. Environment parsing decodes this from base64url. */
  readonly material: string | Buffer
}

export interface InquiryLifecycleSigningKeyRing {
  /** The only key used to issue new tokens. */
  readonly current: InquiryLifecycleSigningKey
  /** Verification-only overlap keys retained until every old token has expired. */
  readonly previous?: readonly InquiryLifecycleSigningKey[]
}

export type InquiryLifecycleSigningSource = string | InquiryLifecycleSigningKeyRing

const KID_PATTERN = /^inquiry-v[1-9][0-9]{0,8}$/
const BASE64URL_PATTERN = /^[A-Za-z0-9_-]+$/
const MINIMUM_KEY_BYTES = 32

function encode(value: unknown): string { return Buffer.from(JSON.stringify(value)).toString('base64url') }

function decodeObject(encoded: string): Record<string, unknown> {
  try {
    const value = JSON.parse(Buffer.from(encoded, 'base64url').toString('utf8')) as unknown
    if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('not an object')
    return value as Record<string, unknown>
  } catch {
    throw new Error('INQUIRY_TOKEN_MALFORMED')
  }
}

function validateKey(key: InquiryLifecycleSigningKey): InquiryLifecycleSigningKey {
  const byteLength = typeof key.material === 'string'
    ? Buffer.byteLength(key.material, 'utf8')
    : key.material.byteLength
  if (!KID_PATTERN.test(key.kid) || byteLength < MINIMUM_KEY_BYTES) {
    throw new Error('INQUIRY_SIGNING_KEY_INVALID')
  }
  return key
}

function normalizeKeyRing(source: InquiryLifecycleSigningSource): InquiryLifecycleSigningKeyRing {
  // Preserve the source API used by non-environment unit callers while routing
  // production configuration through the strictly decoded key-ring loader below.
  if (typeof source === 'string') return { current: validateKey({ kid: 'inquiry-v1', material: source }) }
  const current = validateKey(source.current)
  const previous = (source.previous ?? []).map(validateKey)
  const kids = [current.kid, ...previous.map((key) => key.kid)]
  if (new Set(kids).size !== kids.length) throw new Error('INQUIRY_SIGNING_KEY_INVALID')
  return { current, previous }
}

function decodeEnvironmentKey(value: string | undefined): Buffer {
  if (!value || !BASE64URL_PATTERN.test(value) || value.includes('=')) {
    throw new Error('INQUIRY_SIGNING_KEY_INVALID')
  }
  const decoded = Buffer.from(value, 'base64url')
  // Buffer's decoder is intentionally permissive. Round-tripping makes the
  // accepted representation canonical and rejects truncated/ambiguous input.
  if (decoded.byteLength < MINIMUM_KEY_BYTES || decoded.toString('base64url') !== value) {
    throw new Error('INQUIRY_SIGNING_KEY_INVALID')
  }
  return decoded
}

/**
 * Parse the versioned lifecycle signing ring without accepting passphrases,
 * implicit defaults, partial overlap configuration, or duplicate key ids.
 * Secret values are base64url-encoded random bytes; kids are non-secret.
 */
export function loadInquiryLifecycleSigningKeyRing(
  env: Readonly<Record<string, string | undefined>> = process.env,
): InquiryLifecycleSigningKeyRing {
  const currentKid = env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT_KID
  const currentValue = env.INQUIRY_LIFECYCLE_SIGNING_KEY_CURRENT
  if (!currentKid || !currentValue) throw new Error('INQUIRY_SIGNING_KEY_INVALID')

  const previousKid = env.INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS_KID
  const previousValue = env.INQUIRY_LIFECYCLE_SIGNING_KEY_PREVIOUS
  if (Boolean(previousKid) !== Boolean(previousValue)) throw new Error('INQUIRY_SIGNING_KEY_INVALID')

  return normalizeKeyRing({
    current: { kid: currentKid, material: decodeEnvironmentKey(currentValue) },
    previous: previousKid && previousValue
      ? [{ kid: previousKid, material: decodeEnvironmentKey(previousValue) }]
      : [],
  })
}

export function hashJti(jti: string): string {
  return `sha256:${createHash('sha256').update(jti).digest('hex')}`
}

export function issueInquiryLifecycleToken(args: Omit<InquiryLifecycleClaims, 'iss' | 'aud' | 'iat' | 'exp' | 'jti'> & { ttl_seconds?: number }, signingSource: InquiryLifecycleSigningSource): { token: string; claims: InquiryLifecycleClaims } {
  const signingKey = normalizeKeyRing(signingSource).current
  const now = Math.floor(Date.now() / 1000)
  const claims: InquiryLifecycleClaims = {
    iss: 'madhav-platform', aud: 'madhav-inquiry', ...args,
    iat: now, exp: now + Math.max(60, Math.min(args.ttl_seconds ?? 900, 3600)), jti: randomUUID(),
  }
  const header = encode({ alg: 'HS256', typ: 'JWT', kid: signingKey.kid })
  const payload = encode(claims)
  const signature = createHmac('sha256', signingKey.material).update(`${header}.${payload}`).digest('base64url')
  return { token: `${header}.${payload}.${signature}`, claims }
}

export function verifyInquiryLifecycleToken(
  token: string,
  signingSource: InquiryLifecycleSigningSource,
  expectedSubject: string,
  onVerifiedKid?: (kid: string) => void,
): InquiryLifecycleClaims {
  const ring = normalizeKeyRing(signingSource)
  const parts = token.split('.')
  if (parts.length !== 3) throw new Error('INQUIRY_TOKEN_MALFORMED')
  const [header, payload, provided] = parts
  const decodedHeader = decodeObject(header)
  if (decodedHeader.alg !== 'HS256' || decodedHeader.typ !== 'JWT' || typeof decodedHeader.kid !== 'string') {
    throw new Error('INQUIRY_TOKEN_MALFORMED')
  }
  const signingKey = [ring.current, ...(ring.previous ?? [])]
    .find((candidate) => candidate.kid === decodedHeader.kid)
  if (!signingKey) throw new Error('INQUIRY_TOKEN_UNKNOWN_KID')
  if (!BASE64URL_PATTERN.test(provided) || provided.includes('=')) throw new Error('INQUIRY_TOKEN_INVALID_SIGNATURE')
  const expected = createHmac('sha256', signingKey.material).update(`${header}.${payload}`).digest()
  const actual = Buffer.from(provided, 'base64url')
  if (actual.length !== expected.length || !timingSafeEqual(actual, expected)) throw new Error('INQUIRY_TOKEN_INVALID_SIGNATURE')
  const decoded = decodeObject(payload)
  const now = Math.floor(Date.now() / 1000)
  if (typeof decoded.iss !== 'string' || typeof decoded.aud !== 'string'
    || typeof decoded.sub !== 'string' || decoded.sub.length === 0
    || typeof decoded.inquiry_id !== 'string' || decoded.inquiry_id.length === 0
    || typeof decoded.chart_id !== 'string' || decoded.chart_id.length === 0
    || typeof decoded.contract_hash !== 'string' || decoded.contract_hash.length === 0
    || typeof decoded.execution_plan_hash !== 'string' || decoded.execution_plan_hash.length === 0
    || typeof decoded.contract_state_hash !== 'string' || decoded.contract_state_hash.length === 0
    || typeof decoded.catalog_hash !== 'string' || decoded.catalog_hash.length === 0
    || typeof decoded.compatibility_version !== 'string' || decoded.compatibility_version.length === 0
    || !Array.isArray(decoded.next_action_ids)
    || !decoded.next_action_ids.every((item) => typeof item === 'string' && /^item-[0-9]{3}$/.test(item))
    || new Set(decoded.next_action_ids).size !== decoded.next_action_ids.length
    || !Number.isInteger(decoded.revision) || (decoded.revision as number) < 0
    || !['execute', 'finalize'].includes(decoded.allowed_transition as string)
    || !(decoded.overlay_version === null || typeof decoded.overlay_version === 'string')
    || !(decoded.chart_build_id === null || typeof decoded.chart_build_id === 'string')
    || !Number.isInteger(decoded.iat) || (decoded.iat as number) <= 0
    || !Number.isInteger(decoded.exp) || (decoded.exp as number) <= (decoded.iat as number)
    || typeof decoded.jti !== 'string' || decoded.jti.length === 0) {
    throw new Error('INQUIRY_TOKEN_MALFORMED')
  }
  const claims = decoded as unknown as InquiryLifecycleClaims
  if (claims.iss !== 'madhav-platform' || claims.aud !== 'madhav-inquiry') throw new Error('INQUIRY_TOKEN_WRONG_AUDIENCE')
  if (claims.sub !== expectedSubject) throw new Error('INQUIRY_TOKEN_WRONG_SUBJECT')
  if (!claims.exp || claims.exp <= now) throw new Error('INQUIRY_TOKEN_EXPIRED')
  onVerifiedKid?.(signingKey.kid)
  return claims
}
