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

export function hashJti(jti: string): string {
  return `sha256:${createHash('sha256').update(jti).digest('hex')}`
}

export function issueInquiryLifecycleToken(args: Omit<InquiryLifecycleClaims, 'iss' | 'aud' | 'iat' | 'exp' | 'jti'> & { ttl_seconds?: number }, signingKey: string): { token: string; claims: InquiryLifecycleClaims } {
  if (signingKey.length < 32) throw new Error('INQUIRY_SIGNING_KEY_INVALID')
  const now = Math.floor(Date.now() / 1000)
  const claims: InquiryLifecycleClaims = {
    iss: 'madhav-platform', aud: 'madhav-inquiry', ...args,
    iat: now, exp: now + Math.max(60, Math.min(args.ttl_seconds ?? 900, 3600)), jti: randomUUID(),
  }
  const header = encode({ alg: 'HS256', typ: 'JWT', kid: 'inquiry-v1' })
  const payload = encode(claims)
  const signature = createHmac('sha256', signingKey).update(`${header}.${payload}`).digest('base64url')
  return { token: `${header}.${payload}.${signature}`, claims }
}

export function verifyInquiryLifecycleToken(token: string, signingKey: string, expectedSubject: string): InquiryLifecycleClaims {
  if (signingKey.length < 32) throw new Error('INQUIRY_SIGNING_KEY_INVALID')
  const parts = token.split('.')
  if (parts.length !== 3) throw new Error('INQUIRY_TOKEN_MALFORMED')
  const [header, payload, provided] = parts
  const expected = createHmac('sha256', signingKey).update(`${header}.${payload}`).digest()
  const actual = Buffer.from(provided, 'base64url')
  if (actual.length !== expected.length || !timingSafeEqual(actual, expected)) throw new Error('INQUIRY_TOKEN_INVALID_SIGNATURE')
  const decodedHeader = decodeObject(header)
  if (decodedHeader.alg !== 'HS256' || decodedHeader.typ !== 'JWT' || decodedHeader.kid !== 'inquiry-v1') {
    throw new Error('INQUIRY_TOKEN_MALFORMED')
  }
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
  return claims
}
