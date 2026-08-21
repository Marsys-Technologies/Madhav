/**
 * RATE-07 route-wiring proof — every OAuth MUTATION endpoint is gated.
 *
 * The checklist item this file discharges is "route-wiring tests for authorize,
 * callback, token, refresh, and dynamic registration". A unit test of the gate
 * function proves the gate works; it proves nothing about whether the gate is
 * actually ATTACHED. This file reads the real `server.ts` source and asserts the
 * attachment, so that adding a sixth OAuth mutation route without a limiter, or
 * quietly deleting a limiter from an existing one, fails the build.
 *
 * WHY SOURCE INSPECTION RATHER THAN BOOTING THE APP: importing `server.ts`
 * executes the whole MCP server module graph (it registers ~88 tools, opens
 * clients, and reads a dozen env vars at module load). A source-level assertion
 * is the honest tool for "is the middleware present in the route declaration",
 * which is a syntactic property. It is deliberately paired with
 * `rate07_oauth_rate_limit.test.ts`, which proves the behaviour of what is being
 * attached — neither file is sufficient alone and both are required by CI.
 */
import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

import { ROUTE_LIMITS } from '../lib/oauth_rate_limit.js'

const HERE = dirname(fileURLToPath(import.meta.url))
const SERVER_SRC = readFileSync(resolve(HERE, '../server.ts'), 'utf8')
const TOKEN_SRC = readFileSync(resolve(HERE, '../oauth/token.ts'), 'utf8')

/**
 * The five OAuth mutation endpoints, and the route key each must be gated with.
 *
 * NOTE `/refresh` shares `oauth_token`, it does not have its own key: it forces
 * grant_type=refresh_token and delegates to the same handleToken that `/token`
 * serves. Giving it a separate bucket handed a refresh-token guessing attack the
 * per-IP budget twice (once per URL) while advertising it once — found by
 * adversarial review.
 */
const MUTATION_ROUTES: Array<{ method: 'post' | 'get'; path: string; key: keyof typeof ROUTE_LIMITS }> = [
  { method: 'post', path: '/mcp/oauth/authorize', key: 'oauth_authorize' },
  { method: 'get',  path: '/mcp/oauth/callback',  key: 'oauth_callback' },
  { method: 'post', path: '/mcp/oauth/token',     key: 'oauth_token' },
  { method: 'post', path: '/mcp/oauth/refresh',   key: 'oauth_token' },
  { method: 'post', path: '/mcp/oauth/register',  key: 'oauth_register' },
]

/** Extract the argument list of `app.<method>('<path>', ...` up to the first newline. */
function routeDeclaration(method: string, path: string): string {
  const needle = `app.${method}('${path}'`
  const at = SERVER_SRC.indexOf(needle)
  expect(at, `route declaration not found: app.${method}('${path}'`).toBeGreaterThan(-1)
  const eol = SERVER_SRC.indexOf('\n', at)
  return SERVER_SRC.slice(at, eol === -1 ? undefined : eol)
}

describe('RATE-07 — all five OAuth mutation endpoints are rate limited', () => {
  it.each(MUTATION_ROUTES)('$method $path is gated with oauthRateLimit(\'$key\')', ({ method, path, key }) => {
    const decl = routeDeclaration(method, path)
    expect(decl, `${path} must pass through oauthRateLimit`).toContain('oauthRateLimit(')
    expect(decl, `${path} must be gated with the '${key}' limit profile`).toContain(`oauthRateLimit('${key}')`)
  })

  it('the gate is the FIRST middleware on each route — before any handler work', () => {
    for (const { method, path } of MUTATION_ROUTES) {
      const decl = routeDeclaration(method, path)
      // Everything between the path literal and the gate must be only ", ".
      const afterPath = decl.slice(decl.indexOf(`'${path}'`) + path.length + 2)
      const gateAt = afterPath.indexOf('oauthRateLimit(')
      expect(gateAt, `${path}: gate not found after the path argument`).toBeGreaterThan(-1)
      expect(
        afterPath.slice(0, gateAt).trim().replace(/,$/, '').trim(),
        `${path}: something runs before the rate-limit gate`,
      ).toBe('')
    }
  })

  it('every route key used in server.ts has a limit profile defined', () => {
    const used = [...SERVER_SRC.matchAll(/oauthRateLimit\('([^']+)'\)/g)].map((m) => m[1]!)
    expect(used.length).toBe(MUTATION_ROUTES.length)
    for (const key of used) {
      expect(Object.keys(ROUTE_LIMITS), `no limit profile for '${key}'`).toContain(key)
    }
  })

  it('no OAuth mutation route is left ungated (exhaustive scan of app.post/app.get on /mcp/oauth)', () => {
    const declared = [...SERVER_SRC.matchAll(/app\.(post|get|put|patch|delete)\('(\/mcp\/oauth\/[^']*)'/g)]
    // Discovery endpoints live under /mcp/.well-known, not /mcp/oauth, so every
    // hit here is a mutation surface and every one must carry the gate.
    expect(declared.length).toBeGreaterThanOrEqual(MUTATION_ROUTES.length)
    for (const m of declared) {
      const decl = routeDeclaration(m[1]!, m[2]!)
      expect(decl, `UNGATED OAuth route: ${m[1]} ${m[2]}`).toContain('oauthRateLimit(')
    }
  })
})

describe('RATE-07 — post-validation charging happens after validation, never before', () => {
  it('/mcp/oauth/register charges the principal only after validateMcpKeyFromHeader succeeds', () => {
    const at = SERVER_SRC.indexOf("app.post('/mcp/oauth/register'")
    const block = SERVER_SRC.slice(at, at + 3000)

    const validateAt = block.indexOf('validateMcpKeyFromHeader(')
    const chargeAt = block.indexOf('chargeValidatedSubject(')
    expect(validateAt, 'register must validate the Bearer key').toBeGreaterThan(-1)
    expect(chargeAt, 'register must charge a per-principal bucket').toBeGreaterThan(-1)
    expect(chargeAt, 'the principal bucket must be charged AFTER validation, not before').toBeGreaterThan(validateAt)

    // And it must charge the RESOLVED principal, not anything from the request.
    expect(block).toContain("chargeValidatedSubject(res, 'oauth_register', 'principal', principal.user_uid)")
  })

  it('the token endpoint charges the client bucket only after validateOAuthClient succeeds', () => {
    const validateAt = TOKEN_SRC.indexOf('validateOAuthClient(')
    const chargeAt = TOKEN_SRC.indexOf('chargeValidatedSubject(')
    expect(validateAt, 'token must validate the client').toBeGreaterThan(-1)
    expect(chargeAt, 'token must charge a per-client bucket').toBeGreaterThan(-1)
    expect(chargeAt, 'the client bucket must be charged AFTER validation, not before').toBeGreaterThan(validateAt)

    // The charge must sit after the invalid_client rejection, so a caller that
    // fails validation never reaches the per-client bucket at all.
    const invalidClientAt = TOKEN_SRC.indexOf("res.status(401).json({ error: 'invalid_client' })")
    expect(invalidClientAt).toBeGreaterThan(-1)
    expect(chargeAt).toBeGreaterThan(invalidClientAt)
  })

  it('chargeValidatedSubject only ever receives a subject sourced from a VALIDATION RESULT', () => {
    // This assertion used to read `not.toMatch(/req\.(body|query|headers)/)`.
    // An adversarial review showed that was a §N.8 defect in the detector
    // itself: `token.ts` does `const params = req.body`, so the real call site
    // passes `params.client_id` — a raw body field wearing an alias — and the
    // regex reported clean on the one call it most needed to catch. Checking
    // spelling is not checking the claim.
    //
    // Inverted to an ALLOWLIST: the subject must be a property of an object
    // that a validation step returned or produced. A new call site passing
    // anything else fails, alias or not.
    const ALLOWED_SUBJECT_SOURCES = /^(principal|clientResult|authCode|tokenRecord)\./

    let found = 0
    for (const src of [SERVER_SRC, TOKEN_SRC]) {
      for (const m of src.matchAll(/chargeValidatedSubject\(\s*([^)]*?)\s*\)/g)) {
        const args = m[1]!.split(',').map((a) => a.trim())
        expect(args.length, `unexpected arity in: ${m[0]}`).toBe(4)
        const subjectArg = args[3]!
        found += 1
        expect(
          subjectArg,
          `chargeValidatedSubject subject "${subjectArg}" must come from a validation result ` +
            `(one of ${ALLOWED_SUBJECT_SOURCES.source}), not from request input — even via an alias`,
        ).toMatch(ALLOWED_SUBJECT_SOURCES)
      }
    }
    // Guard the guard: if the call sites are ever renamed away, this test must
    // fail loudly rather than pass vacuously over zero matches.
    expect(found, 'expected at least one chargeValidatedSubject call site to check').toBeGreaterThan(0)
  })
})
