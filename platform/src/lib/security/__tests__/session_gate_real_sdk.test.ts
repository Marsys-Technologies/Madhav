/**
 * session_gate_real_sdk.test.ts — proves `classifyVerifyError` / `verifySessionForGate`
 * against the REAL firebase-admin verifier for every rejection that is decided
 * BEFORE the public-key fetch (so it needs no network and no real credential).
 *
 * Why: the mocked suites copy SDK messages by hand; this file guards against
 * the classifier drifting from what the installed SDK really throws (§N.8: a
 * signal must be backed by a detector that can read false).
 *
 * The service account here is synthetic (a throw-away RSA key generated in this
 * process, project `test-proj`). The signature-verification step (which would
 * fetch Google's keys) and the expiry step are NOT exercised here; they are
 * covered with the mocked verifier in session_gate.test.ts.
 */

import { generateKeyPairSync } from 'node:crypto'

import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import { __resetSessionGateForTest, classifyVerifyError, verifySessionForGate } from '../session_gate'

const PROJECT = 'test-proj'
const b64 = (o: object) => Buffer.from(JSON.stringify(o)).toString('base64url')

function jwt(header: object, payload: object): string {
  return `${b64(header)}.${b64(payload)}.c2ln`
}

const goodHeader = { alg: 'RS256', kid: 'kid1', typ: 'JWT' }
const now = Math.floor(Date.now() / 1000)
const goodPayload = {
  aud: PROJECT,
  iss: `https://session.firebase.google.com/${PROJECT}`,
  sub: 'u1',
  iat: now - 10,
  exp: now + 3600,
}

let savedCreds: string | undefined

beforeAll(() => {
  savedCreds = process.env.FIREBASE_ADMIN_CREDENTIALS
  const { privateKey } = generateKeyPairSync('rsa', { modulusLength: 2048 })
  process.env.FIREBASE_ADMIN_CREDENTIALS = JSON.stringify({
    type: 'service_account',
    project_id: PROJECT,
    private_key: privateKey.export({ type: 'pkcs8', format: 'pem' }).toString(),
    client_email: `sa@${PROJECT}.iam.gserviceaccount.com`,
  })
  __resetSessionGateForTest()
})

afterAll(() => {
  if (savedCreds === undefined) delete process.env.FIREBASE_ADMIN_CREDENTIALS
  else process.env.FIREBASE_ADMIN_CREDENTIALS = savedCreds
})

describe('classifier vs the real firebase-admin verifier (offline rejections)', () => {
  it.each([
    ['not a JWT at all', 'garbage', 'bad_format'],
    ['no kid', jwt({ alg: 'RS256', typ: 'JWT' }, goodPayload), 'bad_format'],
    ['wrong algorithm', jwt({ alg: 'HS256', kid: 'k', typ: 'JWT' }, goodPayload), 'bad_format'],
    ['wrong audience (other project)', jwt(goodHeader, { ...goodPayload, aud: 'other-proj' }), 'wrong_audience'],
    ['wrong issuer (attacker-chosen, shape-valid)', jwt(goodHeader, { ...goodPayload, iss: 'https://session.firebase.google.com/other-proj' }), 'wrong_issuer'],
    ['issuer that merely CONTAINS the old shape-check substring', jwt(goodHeader, { ...goodPayload, iss: 'https://evil.example/session.firebase.google.com' }), 'wrong_issuer'],
    ['missing sub', jwt(goodHeader, { ...goodPayload, sub: undefined }), 'bad_format'],
  ])('%s -> %s', async (_label, cookie, reason) => {
    __resetSessionGateForTest()
    const outcome = await verifySessionForGate(cookie)
    expect(outcome).toEqual({ ok: false, reason, infra: false })
  })

  it('the old shape check would have accepted the wrong-issuer cookie (documents the forgery the gate closes)', () => {
    const payload = { exp: now + 3600, iss: 'https://evil.example/session.firebase.google.com' }
    expect(payload.iss.includes('session.firebase.google.com')).toBe(true)
  })

  it('missing credentials: the REAL cert({}) error is classified as infrastructure', async () => {
    const { cert } = await import('firebase-admin/app')
    let thrown: unknown
    try {
      cert({})
    } catch (e) {
      thrown = e
    }
    expect(thrown).toBeDefined() // a detector that can read false: cert({}) must really throw
    expect(classifyVerifyError(thrown)).toEqual({ reason: 'verify_error', infra: true })
  })
})
