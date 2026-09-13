import { createHmac, createHash, randomUUID, timingSafeEqual } from 'node:crypto'

export interface InquiryLifecycleClaims {
  readonly iss: 'madhav-platform'
  readonly aud: 'madhav-inquiry'
  readonly sub: string
  readonly inquiry_id: string
  readonly chart_id: string
  readonly contract_hash: string
  readonly execution_plan_hash: string
  readonly catalog_hash: string
  readonly compatibility_version: string
  readonly overlay_version: string | null
  readonly revision: number
  readonly allowed_transition: 'execute' | 'finalize'
  readonly next_action_ids: readonly string[]
  readonly iat: number
  readonly exp: number
  readonly jti: string
}

function encode(value: unknown): string { return Buffer.from(JSON.stringify(value)).toString('base64url') }

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
  const claims = JSON.parse(Buffer.from(payload, 'base64url').toString('utf8')) as InquiryLifecycleClaims
  const now = Math.floor(Date.now() / 1000)
  if (claims.iss !== 'madhav-platform' || claims.aud !== 'madhav-inquiry') throw new Error('INQUIRY_TOKEN_WRONG_AUDIENCE')
  if (claims.sub !== expectedSubject) throw new Error('INQUIRY_TOKEN_WRONG_SUBJECT')
  if (!claims.exp || claims.exp <= now) throw new Error('INQUIRY_TOKEN_EXPIRED')
  return claims
}
