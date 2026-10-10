/**
 * route_auth_guard.test.ts — governance REGRESSION test (SS N-373, PR-S3 part B;
 * `SESSION_GATE_AUDIT.md` §9c).
 *
 * `proxy.ts` historically authenticated nothing (shape check only; now optionally
 * verified, see `lib/security/session_gate.ts`), so every route handler must
 * verify the caller itself. This test fails when ANY exported HTTP method handler
 * under `src/app/api/**\/route.{ts,tsx,js,jsx,mjs}` has no recognised verification
 * call and is not on an explicit, reasoned list.
 *
 * Where this lives, and why: the repo's source-scan detectors with a
 * "demonstrated-can-fail" self-proof are vitest files under `tests/governance/`
 * and `tests/pariprashna/` (`life_events_tools_scope.test.ts`,
 * `no_auto_promotion.test.ts`): pure `fs` walks of `src/**`, no DB, no network, run
 * by the ordinary `npx vitest run` unit job. The Python guards under
 * `scripts/governance/` scan SQL/Python/JSON assets; route handlers are TypeScript
 * and the recogniser needs the same tokenisation the code is written in, so a
 * vitest next to its siblings is the idiomatic home.
 *
 * Three lists, one ratchet:
 *   - guarded    : a RECOGNISED verification call is reachable from the handler.
 *   - ALLOWLIST  : deliberately unguarded (public by design / dead stub), each
 *                  with a reason; stub entries are additionally shape-checked.
 *   - KNOWN_UNGUARDED_PENDING_FIX : real gaps whose fix is owned by another PR or
 *                  an owner decision. Green today, but the ratchet fails the
 *                  moment an entry becomes guarded (remove it) or goes stale, and
 *                  a NEW unguarded handler fails immediately.
 *
 * What a pass means (§N.8): "a recognised verification call is reachable from
 * every handler", measured on code only (comments, strings and regex literals are
 * blanked). It does NOT prove the reject branch or the principal are right; the
 * per-route `route.authz.test.ts` files own that. The self-tests at the bottom
 * prove the detector reads FALSE on synthetic unguarded handlers, on guards that
 * live only in a comment/string, and on a guard in a different method.
 */

import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs'
import { join, relative, resolve, sep } from 'node:path'

import { describe, expect, it } from 'vitest'

import {
  AUTHZ_ONLY_CALLS,
  analyseRouteSource,
  type HttpMethod,
  mentionsRecognisedCall,
  reachOfFunction,
  RECOGNISED_VERIFICATION_CALLS,
  stripNonCode,
} from './route_auth_recogniser'

const PLATFORM_ROOT = resolve(__dirname, '../../')
const API_ROOT = join(PLATFORM_ROOT, 'src/app/api')
const APP_ROOT = join(PLATFORM_ROOT, 'src/app')

// ── Lists ─────────────────────────────────────────────────────────────────────

interface ListedRoute {
  /** Exported methods covered by this entry (anything else exported is NOT covered). */
  methods: HttpMethod[]
  reason: string
  /**
   * When set, the source must look like a stub: only `next/server` imports and
   * (if given) the literal status code. A "410 stub" that grows data access
   * stops being allow-listable.
   */
  stub?: { status?: number }
  /** Entry may be absent from the tree without failing the stale-entry ratchet. */
  optionalIfMissing?: boolean
  /**
   * Calls (in code: comments, strings and regex literals are blanked) the route
   * source must still make for its reason to be true, e.g. the abuse controls of
   * a public endpoint. §N.8: a reason that asserts "rate limited" needs a
   * detector, otherwise it is prose.
   */
  mustCall?: string[]
}

interface PendingRoute {
  methods: HttpMethod[]
  /** Who removes this entry by guarding the handler. */
  owner: string
  reason: string
}

/** Route dir (relative to `src/app/api`, forward slashes) -> entry. */
export const ALLOWLIST: Record<string, ListedRoute> = {
  health: { methods: ['GET'], reason: 'public liveness probe, returns {status:"ok"}; proxy PUBLIC list', stub: {} },
  'auth/callback': { methods: ['GET'], reason: 'legacy stub: static redirect to /login, nothing to protect', stub: {} },
  'access-requests': {
    methods: ['POST'],
    reason: 'public access-request intake BY DESIGN (pre-login); proxy PUBLIC list; rate-limit TODO tracked in audit section 9b item 9',
  },
  'auth/recover': {
    methods: ['POST'],
    reason: 'public password-recovery trigger BY DESIGN (pre-login, matcher-excluded); rate-limit hardening tracked in audit section 9b items 4 and 11',
  },
  'build/active': { methods: ['GET'], reason: '410 Gone stub (decommissioned)', stub: { status: 410 } },
  'build/cancel/[buildId]': { methods: ['POST'], reason: '410 Gone stub (decommissioned)', stub: { status: 410 } },
  'build/events/[buildId]': { methods: ['GET'], reason: '410 Gone stub (decommissioned)', stub: { status: 410 } },
  'build/reap': { methods: ['POST'], reason: '410 Gone stub (decommissioned)', stub: { status: 410 } },
  'build/recent': { methods: ['GET'], reason: '410 Gone stub (decommissioned)', stub: { status: 410 } },
  'build/start': { methods: ['POST'], reason: '410 Gone stub (decommissioned)', stub: { status: 410 } },
  'build/task': { methods: ['POST'], reason: '410 Gone stub (decommissioned)', stub: { status: 410 } },
  'build/telemetry': { methods: ['GET'], reason: '410 Gone stub (decommissioned)', stub: { status: 410 } },
  'chat/consume': {
    methods: ['GET', 'POST'],
    reason: '308 redirect alias to /api/chat/consult; the target verifies the session',
    stub: { status: 308 },
  },
  'chat/consume/continue': {
    methods: ['GET', 'POST'],
    reason: '308 redirect alias to /api/chat/consult/continue; the target verifies the session',
    stub: { status: 308 },
  },
  'chat/consume/regenerate': {
    methods: ['GET', 'POST'],
    reason: '308 redirect alias to /api/chat/consult/regenerate; the target verifies the session',
    stub: { status: 308 },
  },
  'chat/consume/resume': {
    methods: ['GET', 'POST'],
    reason: '308 redirect alias to /api/chat/consult/resume; the target verifies the session',
    stub: { status: 308 },
  },
  'auth/resolve-username': {
    methods: ['POST'],
    // Listed like auth/recover and access-requests above: a public, pre-login,
    // matcher-excluded endpoint. The S1 fix did not add authentication (it cannot:
    // the caller has no session yet); it added the abuse controls, which are
    // asserted below by `mustCall` so the claim in the reason cannot silently rot.
    reason: 'public by design: returns an email for username login; rate limited, uniform timing (S1)',
    mustCall: ['limiter.check', 'getTrustedClientIp', 'padToUniformDuration'],
  },
}

/**
 * Real, currently-unguarded handlers. NOT an allowlist: each is a gap whose fix
 * is owned elsewhere. The ratchet below fails when an entry becomes guarded
 * (delete it) or stale, and the test is red for any unguarded handler not here.
 *
 * Deliberately NOT listed (they contain a recognised call today, so a
 * presence-detector cannot flag them; their weakness is authorisation depth, not
 * a missing check): auth/session (verifyIdToken without checkRevoked/email_verified),
 * mcp/db/query and retrieval/capability (validateServiceToken, header-asserted
 * principal) -- owner decisions / S2 per the session-gate audit.
 */
export const KNOWN_UNGUARDED_PENDING_FIX: Record<string, PendingRoute> = {
  // Empty since S1 (icr/confirm, icr/patches, admin/maintenance/trace-cleanup,
  // admin/model-health) landed guards and auth/resolve-username moved to ALLOWLIST
  // (public by design, rate limited). Kept as the ratchet's home for future gaps.
}

/**
 * Server-side data-loading pages/layouts that carry NO guard of their own
 * (a layout check does not protect a page: Next may skip layouts on RSC
 * navigation). Same ratchet semantics as KNOWN_UNGUARDED_PENDING_FIX.
 */
export const KNOWN_UNGUARDED_PAGES_PENDING_FIX: Record<string, { owner: string; reason: string }> = {
  // cockpit/page.tsx and information/atlas/page.tsx (S1: requireSuperAdminPage) and
  // share/[slug]/page.tsx (S4: requireActiveUserPage) now guard themselves and were
  // removed by the ratchet. panchang/page.tsx is still unguarded: S1 did not touch it.
  'panchang/page.tsx': { owner: 'S1', reason: 'LOW: sidecar panchanga fetch guarded only by panchang/layout.tsx (audit section 6); S1 left it unguarded' },
}

/**
 * Page-level guard helpers (defined once in lib/auth). Like WRAPPER_DEFINITIONS,
 * they are trusted by name, so this test checks each still reaches real session
 * verification; a helper turned into a no-op would otherwise keep every page that
 * calls it "guarded".
 */
export const PAGE_GUARD_DEFINITIONS: Record<string, { file: string; mustReach: string[] }> = {
  requireSuperAdminPage: { file: 'src/lib/auth/super-admin-page-guard.ts', mustReach: ['getServerUserWithProfile'] },
  requireActiveUserPage: { file: 'src/lib/auth/active-user-page-guard.ts', mustReach: ['getServerUserWithProfile'] },
}

/**
 * Verification helpers that are WRAPPERS around other verification (defined in a
 * shared file, not in the route). Each is trusted by name, so this test checks
 * that its definition still exists and still reaches the inner call it is
 * trusted for; a wrapper silently turned into a no-op would otherwise keep
 * every route "guarded".
 */
export const WRAPPER_DEFINITIONS: Record<string, { file: string; mustReach: string[] }> = {
  getServerUser: { file: 'src/lib/firebase/server.ts', mustReach: ['verifySessionCookie'] },
  getServerUserWithProfile: { file: 'src/lib/auth/access-control.ts', mustReach: ['getServerUser'] },
  requireSuperAdmin: { file: 'src/lib/auth/access-control.ts', mustReach: ['getServerUserWithProfile'] },
  accountOwner: { file: 'src/lib/account/guard.ts', mustReach: ['getServerUserWithProfile'] },
  usageOwner: { file: 'src/lib/metering/http.ts', mustReach: ['getServerUserWithProfile'] },
  withAiConsole: { file: 'src/app/api/ai-console/_shared.ts', mustReach: ['getServerUserWithProfile'] },
  withAiConsoleMutation: { file: 'src/app/api/ai-console/_shared.ts', mustReach: ['withAiConsole'] },
  guardObservatoryRoute: { file: 'src/app/api/admin/observatory/_guard.ts', mustReach: ['requireSuperAdmin'] },
  resolveChartPageAccess: { file: 'src/lib/auth/chart-page-guard.ts', mustReach: ['getServerUser'] },
  admitRequest: { file: 'src/lib/pariprashna/pipeline/safety_gate.ts', mustReach: ['getServerUser'] },
}

/** Leaf verifiers / authz primitives: only their definition must still exist. */
export const LEAF_DEFINITIONS: Record<string, string> = {
  verifySessionCookie: 'src/lib/firebase/server.ts',
  validateServiceToken: 'src/lib/mcp/service_token.ts',
  validateMcpServiceRequest: 'src/lib/mcp/service_token.ts',
  validateMcpKey: 'src/lib/mcp/auth.ts',
  verifyOidcToken: 'src/lib/auth/oidc.ts',
  verifyFeedToken: 'src/lib/security/sign_url.ts',
  requireChartPermission: 'src/lib/auth/requireChartPermission.ts',
  authorizeChartAccess: 'src/lib/auth/authorizeChartAccess.ts',
  // verifyIdToken is the firebase-admin SDK method itself: no local definition.
}

// ── Enumeration ───────────────────────────────────────────────────────────────

const ROUTE_FILE_RE = /^route\.(?:ts|tsx|js|jsx|mjs)$/

function walk(dir: string, accept: (name: string) => boolean, out: string[] = []): string[] {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name)
    if (statSync(full).isDirectory()) {
      if (name === '__tests__' || name === 'node_modules' || name === '.next') continue
      walk(full, accept, out)
    } else if (accept(name)) {
      out.push(full)
    }
  }
  return out
}

const posix = (p: string) => p.split(sep).join('/')

interface RouteEntry {
  dir: string // 'charts/[id]'
  file: string // absolute
  rel: string // 'src/app/api/charts/[id]/route.ts'
  source: string
}

function enumerateRoutes(): RouteEntry[] {
  return walk(API_ROOT, (n) => ROUTE_FILE_RE.test(n))
    .sort()
    .map((file) => ({
      file,
      rel: posix(relative(PLATFORM_ROOT, file)),
      dir: posix(relative(API_ROOT, file)).replace(/\/route\.[a-z]+$/, '').replace(/^route\.[a-z]+$/, ''),
      source: readFileSync(file, 'utf8'),
    }))
}

const ROUTES = enumerateRoutes()
const ROUTE_BY_DIR = new Map(ROUTES.map((r) => [r.dir, r]))

interface HandlerRow {
  dir: string
  method: HttpMethod
  guarded: boolean
  via: string[]
  unresolved: boolean
}

const HANDLERS: HandlerRow[] = ROUTES.flatMap((r) =>
  analyseRouteSource(r.source).map((v) => ({
    dir: r.dir,
    method: v.method,
    guarded: v.guarded,
    via: v.via,
    unresolved: Boolean(v.unresolved),
  })),
)
const handlerKey = (dir: string, method: string) => `${dir} ${method}`

// ── The regression guard ──────────────────────────────────────────────────────

describe('route auth guard: enumeration is real (cannot pass vacuously)', () => {
  it('finds the route inventory', () => {
    // 209 route files / 264 handlers at the time of writing. A floor, not a target:
    // it exists so that a broken glob/walk cannot turn the whole suite into a no-op.
    expect(ROUTES.length).toBeGreaterThan(150)
    expect(HANDLERS.length).toBeGreaterThan(200)
    for (const sentinel of ['health', 'charts/[id]', 'icr/confirm', 'mcp/session', 'admin/cron/reap-pending-streams', 'ai-console/default']) {
      expect(ROUTE_BY_DIR.has(sentinel), `sentinel route missing from enumeration: ${sentinel}`).toBe(true)
    }
  })

  it('every route file exports at least one HTTP method handler', () => {
    const noMethods = ROUTES.filter((r) => analyseRouteSource(r.source).length === 0).map((r) => r.rel)
    expect(noMethods, 'route file with no recognisable exported HTTP method (parser gap or empty route)').toEqual([])
  })

  it('the recogniser sees a large guarded majority (a recogniser that matched nothing would show 0)', () => {
    const guarded = HANDLERS.filter((h) => h.guarded).length
    expect(guarded).toBeGreaterThan(200)
  })
})

describe('route auth guard: every handler is verified, allow-listed, or a ratcheted pending gap', () => {
  it('no NEW unguarded handler (not guarded, not allow-listed, not pending)', () => {
    const violations: string[] = []
    for (const h of HANDLERS) {
      if (h.guarded) continue
      const allowed = ALLOWLIST[h.dir]?.methods.includes(h.method)
      const pending = KNOWN_UNGUARDED_PENDING_FIX[h.dir]?.methods.includes(h.method)
      if (allowed || pending) continue
      violations.push(
        `${h.dir} ${h.method}${h.unresolved ? ' (unresolvable export form)' : ''}: no recognised verification call. ` +
          `Add one of [${RECOGNISED_VERIFICATION_CALLS.join(', ')}] or MARSYS_CRON_SECRET to the handler, ` +
          `or (public/dead only) add an ALLOWLIST entry with a reason.`,
      )
    }
    expect(violations, `\n${violations.join('\n')}\n`).toEqual([])
  })

  it('RATCHET: a pending entry whose handler is now guarded must be removed from KNOWN_UNGUARDED_PENDING_FIX', () => {
    const fixed: string[] = []
    for (const [dir, entry] of Object.entries(KNOWN_UNGUARDED_PENDING_FIX)) {
      for (const m of entry.methods) {
        const h = HANDLERS.find((x) => x.dir === dir && x.method === m)
        if (h?.guarded) fixed.push(`${handlerKey(dir, m)} is now guarded (owner ${entry.owner}): delete it from KNOWN_UNGUARDED_PENDING_FIX`)
      }
    }
    expect(fixed, `\n${fixed.join('\n')}\n`).toEqual([])
  })

  it('RATCHET: a pending/allow-listed entry that no longer exists is stale and must be removed', () => {
    const stale: string[] = []
    const check = (listName: string, dir: string, methods: HttpMethod[], optional = false) => {
      const route = ROUTE_BY_DIR.get(dir)
      if (!route) {
        if (!optional) stale.push(`${listName}: ${dir} has no route file any more: delete the entry`)
        return
      }
      const exported = new Set(analyseRouteSource(route.source).map((v) => v.method))
      for (const m of methods) {
        if (!exported.has(m)) stale.push(`${listName}: ${handlerKey(dir, m)} is no longer exported: delete it from the entry`)
      }
    }
    for (const [dir, e] of Object.entries(ALLOWLIST)) check('ALLOWLIST', dir, e.methods, e.optionalIfMissing)
    for (const [dir, e] of Object.entries(KNOWN_UNGUARDED_PENDING_FIX)) check('KNOWN_UNGUARDED_PENDING_FIX', dir, e.methods)
    expect(stale, `\n${stale.join('\n')}\n`).toEqual([])
  })

  it('RATCHET: an allow-listed handler that has gained a recognised guard no longer needs the allowlist', () => {
    const redundant: string[] = []
    for (const [dir, entry] of Object.entries(ALLOWLIST)) {
      for (const m of entry.methods) {
        const h = HANDLERS.find((x) => x.dir === dir && x.method === m)
        if (h?.guarded) redundant.push(`${handlerKey(dir, m)} is now guarded: delete it from ALLOWLIST`)
      }
    }
    expect(redundant, `\n${redundant.join('\n')}\n`).toEqual([])
  })

  it('the two lists are disjoint and every entry carries a reason (and an owner for pending)', () => {
    for (const dir of Object.keys(ALLOWLIST)) expect(KNOWN_UNGUARDED_PENDING_FIX[dir], `${dir} is on both lists`).toBeUndefined()
    for (const [dir, e] of Object.entries(ALLOWLIST)) {
      expect(e.reason.trim().length, `${dir} allowlist reason`).toBeGreaterThan(10)
      expect(e.methods.length).toBeGreaterThan(0)
    }
    for (const [dir, e] of Object.entries(KNOWN_UNGUARDED_PENDING_FIX)) {
      expect(e.reason.trim().length, `${dir} pending reason`).toBeGreaterThan(10)
      expect(e.owner.trim().length, `${dir} pending owner`).toBeGreaterThan(1)
      expect(e.methods.length).toBeGreaterThan(0)
    }
  })

  it('allow-listed STUBS stay stubs: only next/server imports (and the stated status) -- no data access', () => {
    const bad: string[] = []
    for (const [dir, entry] of Object.entries(ALLOWLIST)) {
      if (!entry.stub) continue
      const route = ROUTE_BY_DIR.get(dir)
      if (!route) continue
      const specifiers = [...route.source.matchAll(/\bfrom\s+['"]([^'"]+)['"]/g)].map((m) => m[1])
      const requires = [...stripNonCode(route.source).matchAll(/\brequire\s*\(/g)]
      const dynamicImports = [...stripNonCode(route.source).matchAll(/\bimport\s*\(/g)]
      const foreign = specifiers.filter((s) => s !== 'next/server')
      if (foreign.length > 0 || requires.length > 0 || dynamicImports.length > 0) {
        bad.push(`${dir}: allow-listed as a stub but imports ${JSON.stringify([...foreign, ...(requires.length ? ['require()'] : []), ...(dynamicImports.length ? ['import()'] : [])])}`)
      }
      if (entry.stub.status !== undefined && !new RegExp(`\\b${entry.stub.status}\\b`).test(stripNonCode(route.source))) {
        bad.push(`${dir}: allow-listed as a ${entry.stub.status} stub but the status literal is absent`)
      }
    }
    expect(bad, `\n${bad.join('\n')}\n`).toEqual([])
  })
})

/** The names in `names` that the route source does not CALL in code (comments/strings blanked). */
export function missingCalls(source: string, names: string[]): string[] {
  const code = stripNonCode(source)
  return names.filter((n) => !new RegExp(`(?:^|[^\\w$])${n.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\s*\\(`).test(code))
}

describe('route auth guard: allow-list reasons that assert a control are backed by a detector', () => {
  it('every mustCall control is still called by its allow-listed route', () => {
    const bad: string[] = []
    for (const [dir, entry] of Object.entries(ALLOWLIST)) {
      if (!entry.mustCall) continue
      const route = ROUTE_BY_DIR.get(dir)
      if (!route) continue
      const missing = missingCalls(route.source, entry.mustCall)
      if (missing.length > 0) bad.push(`${dir}: allow-listed on the strength of ${JSON.stringify(entry.mustCall)} but no longer calls ${JSON.stringify(missing)}`)
    }
    expect(bad, `\n${bad.join('\n')}\n`).toEqual([])
  })

  it('at least one allow-list entry carries mustCall (the check is not vacuous)', () => {
    expect(Object.values(ALLOWLIST).filter((e) => e.mustCall && e.mustCall.length > 0).length).toBeGreaterThan(0)
  })

  it('missingCalls reads FALSE when the control is absent, only in a comment, or only in a string', () => {
    expect(missingCalls('export async function POST() { const r = limiter.check(k); await pad(); }', ['limiter.check', 'pad'])).toEqual([])
    expect(missingCalls('export async function POST() { return Response.json({}) }', ['limiter.check'])).toEqual(['limiter.check'])
    expect(missingCalls('// limiter.check(k)\nexport async function POST() { return 1 }', ['limiter.check'])).toEqual(['limiter.check'])
    expect(missingCalls("export async function POST() { return 'limiter.check(k)' }", ['limiter.check'])).toEqual(['limiter.check'])
    expect(missingCalls('export async function POST() { return notlimiter.check(k) }', ['limiter.check'])).toEqual(['limiter.check'])
  })
})

describe('route auth guard: trusted wrapper helpers still really verify', () => {
  it.each(Object.entries(WRAPPER_DEFINITIONS))('%s is defined and still reaches its inner verification', (name, def) => {
    const path = join(PLATFORM_ROOT, def.file)
    expect(existsSync(path), `${def.file} missing`).toBe(true)
    const reach = reachOfFunction(readFileSync(path, 'utf8'), name)
    expect(reach, `${name} not found as a declaration in ${def.file}`).not.toBeNull()
    for (const inner of def.mustReach) {
      expect(reach, `${name} (${def.file}) no longer calls ${inner}`).toContain(inner)
    }
  })

  it.each(Object.entries(PAGE_GUARD_DEFINITIONS))('page guard %s is defined and still reaches real session verification', (name, def) => {
    const path = join(PLATFORM_ROOT, def.file)
    expect(existsSync(path), `${def.file} missing`).toBe(true)
    const reach = reachOfFunction(readFileSync(path, 'utf8'), name)
    expect(reach, `${name} not found as a declaration in ${def.file}`).not.toBeNull()
    for (const inner of def.mustReach) {
      expect(reach, `${name} (${def.file}) no longer calls ${inner}`).toContain(inner)
    }
  })

  it.each(Object.entries(LEAF_DEFINITIONS))('%s is still defined', (name, file) => {
    const path = join(PLATFORM_ROOT, file)
    expect(existsSync(path), `${file} missing`).toBe(true)
    expect(reachOfFunction(readFileSync(path, 'utf8'), name), `${name} not declared in ${file}`).not.toBeNull()
  })

  it('every recognised name is accounted for as a wrapper, a leaf, the SDK method, or an authz-only primitive', () => {
    const accounted = new Set([...Object.keys(WRAPPER_DEFINITIONS), ...Object.keys(LEAF_DEFINITIONS), 'verifyIdToken'])
    const unaccounted = RECOGNISED_VERIFICATION_CALLS.filter((n) => !accounted.has(n))
    expect(unaccounted).toEqual([])
    for (const n of AUTHZ_ONLY_CALLS) expect(RECOGNISED_VERIFICATION_CALLS).toContain(n)
  })
})

// ── Pages / layouts that load data server-side ────────────────────────────────

/** A server module that imports one of these (or calls fetch) loads data on the server. */
const DATA_IMPORT_RE = /\bfrom\s+['"]@\/lib\/(?:db|metering|build)(?:\/[^'"]*)?['"]/
const PAGE_GUARDS = [...RECOGNISED_VERIFICATION_CALLS, 'readAccountProfile', 'requireAdminPage', ...Object.keys(PAGE_GUARD_DEFINITIONS)]

export function pageLoadsDataWithoutOwnGuard(source: string): { loadsData: boolean; guarded: boolean } {
  if (/^\s*(?:['"]use client['"])/m.test(source.split('\n').slice(0, 5).join('\n'))) return { loadsData: false, guarded: true }
  const code = stripNonCode(source)
  const loadsData = DATA_IMPORT_RE.test(source) || /\bfetch\s*\(/.test(code)
  const guarded = new RegExp(`\\b(?:${PAGE_GUARDS.join('|')})\\s*\\(`).test(code)
  return { loadsData, guarded }
}

const PAGE_FILES = walk(APP_ROOT, (n) => /^(?:page|layout)\.(?:tsx|ts|jsx|js)$/.test(n)).filter(
  (f) => !posix(relative(APP_ROOT, f)).startsWith('api/'),
)

describe('route auth guard: server-side data-loading pages/layouts guard themselves', () => {
  const rows = PAGE_FILES.map((f) => ({ rel: posix(relative(APP_ROOT, f)), ...pageLoadsDataWithoutOwnGuard(readFileSync(f, 'utf8')) }))

  it('enumerates the page inventory', () => {
    expect(PAGE_FILES.length).toBeGreaterThan(50)
    expect(rows.filter((r) => r.loadsData).length).toBeGreaterThan(10)
  })

  it('no NEW data-loading page without its own guard (a layout guard does not count)', () => {
    const violations = rows
      .filter((r) => r.loadsData && !r.guarded && !KNOWN_UNGUARDED_PAGES_PENDING_FIX[r.rel])
      .map((r) => `${r.rel}: loads data server-side but calls no recognised guard itself`)
    expect(violations, `\n${violations.join('\n')}\n`).toEqual([])
  })

  it('RATCHET: pending pages that are now guarded, or gone, must be removed', () => {
    const msgs: string[] = []
    for (const [rel, e] of Object.entries(KNOWN_UNGUARDED_PAGES_PENDING_FIX)) {
      const row = rows.find((r) => r.rel === rel)
      if (!row) msgs.push(`${rel} no longer exists: delete it from KNOWN_UNGUARDED_PAGES_PENDING_FIX`)
      else if (!row.loadsData) msgs.push(`${rel} no longer loads data server-side: delete it from KNOWN_UNGUARDED_PAGES_PENDING_FIX`)
      else if (row.guarded) msgs.push(`${rel} is now guarded (owner ${e.owner}): delete it from KNOWN_UNGUARDED_PAGES_PENDING_FIX`)
    }
    expect(msgs, `\n${msgs.join('\n')}\n`).toEqual([])
  })
})

// ── Detector self-tests (it must be able to read FALSE) ───────────────────────

function verdicts(src: string) {
  return Object.fromEntries(analyseRouteSource(src).map((v) => [v.method, v.guarded]))
}

describe('recogniser self-tests on synthetic route sources', () => {
  it('guarded: a direct recognised call in the handler', () => {
    expect(
      verdicts(`
import { getServerUser } from '@/lib/firebase/server'
export async function GET() {
  const user = await getServerUser()
  if (!user) return new Response(null, { status: 401 })
  return Response.json({ ok: true })
}`),
    ).toEqual({ GET: true })
  })

  it('UNGUARDED: a handler with no verification reads false', () => {
    expect(verdicts(`export async function GET() { return Response.json({ secret: 1 }) }`)).toEqual({ GET: false })
    expect(
      verdicts(`
import { db } from '@/lib/db'
export async function POST(request: Request) {
  const body = await request.json()
  await db.query('DELETE FROM x WHERE id = $1', [body.id])
  return Response.json({ ok: true })
}`),
    ).toEqual({ POST: false })
  })

  it('UNGUARDED: the guard name appears only in a comment', () => {
    expect(
      verdicts(`
// TODO: call getServerUser() and requireSuperAdmin() here
/* const u = await getServerUser(); validateServiceToken(req) */
/**
 * @example await verifySessionCookie(c)
 */
export async function POST() { return Response.json({}) }`),
    ).toEqual({ POST: false })
  })

  it('UNGUARDED: the guard name appears only in a string or template literal', () => {
    expect(
      verdicts(`
const msg = "getServerUser() failed"
const other = 'requireSuperAdmin()'
export async function POST() { return new Response(\`call getServerUser() first \${msg} \${other}\`) }`),
    ).toEqual({ POST: false })
    expect(verdicts(`export async function GET() { return Response.json({ doc: 'validateServiceToken(req)' }) }`)).toEqual({ GET: false })
  })

  it('UNGUARDED: the guard name appears only in a regex literal', () => {
    expect(verdicts(`export async function GET(r: Request) { return Response.json({ m: /getServerUser\\(/.test(r.url) }) }`)).toEqual({ GET: false })
  })

  it('per-method: a guard in GET does not cover POST', () => {
    expect(
      verdicts(`
export async function GET() { const u = await getServerUser(); return Response.json({ u }) }
export async function POST() { return Response.json({ wrote: true }) }`),
    ).toEqual({ GET: true, POST: false })
    // ...and the reverse order, so the result does not depend on source order
    expect(
      verdicts(`
export async function POST() { return Response.json({ wrote: true }) }
export async function DELETE() { const u = await getServerUser(); return Response.json({ u }) }`),
    ).toEqual({ POST: false, DELETE: true })
  })

  it('wrapper helper: a file-local helper that verifies covers the handlers that call it', () => {
    expect(
      verdicts(`
async function guard() {
  const u = await getServerUser()
  if (!u) throw new Response(null, { status: 401 })
  return u
}
export async function GET() { await guard(); return Response.json({}) }
export async function POST() { return Response.json({}) }`),
    ).toEqual({ GET: true, POST: false })
  })

  it('wrapper helper: transitive through two file-local helpers', () => {
    expect(
      verdicts(`
const inner = async () => { return requireSuperAdmin() }
async function outer() { return inner() }
export async function GET() { return outer() }`),
    ).toEqual({ GET: true })
  })

  it('wrapper helper: defined but never called is NOT a guard', () => {
    expect(
      verdicts(`
async function guard() { return getServerUser() }
export async function GET() { return Response.json({}) }`),
    ).toEqual({ GET: false })
  })

  it('wrapper helper: a call-wrapper expression (withAiConsole / withAiConsoleMutation)', () => {
    expect(verdicts(`export const GET = withAiConsole(async (userId) => Response.json({ userId }))`)).toEqual({ GET: true })
    expect(verdicts(`export async function PUT() { return withAiConsoleMutation(async () => Response.json({})) }`)).toEqual({ PUT: true })
    expect(verdicts(`export const GET = async () => Response.json({})`)).toEqual({ GET: false })
  })

  it('export forms: const alias and `export { local as METHOD }` resolve to the local body', () => {
    expect(
      verdicts(`
const handler = async () => { await getServerUser(); return Response.json({}) }
export const POST = handler`),
    ).toEqual({ POST: true })
    expect(
      verdicts(`
async function read() { return Response.json({}) }
async function write() { await getServerUser(); return Response.json({}) }
export { read as GET, write as POST }`),
    ).toEqual({ GET: false, POST: true })
  })

  it('export forms: a re-export from another module cannot be verified, so it is unguarded', () => {
    expect(analyseRouteSource(`export { GET, POST } from '../shared/handlers'`)).toEqual([
      { method: 'GET', guarded: false, via: [], unresolved: true },
      { method: 'POST', guarded: false, via: [], unresolved: true },
    ])
  })

  it('authz-only primitives do not authenticate: requireChartPermission on a caller-supplied uid is unguarded', () => {
    expect(
      verdicts(`
export async function POST(request: Request) {
  const { uid, chartId } = await request.json()
  const denied = await requireChartPermission({ uid, chartId, access: 'write' })
  if (denied) return denied
  return Response.json({})
}`),
    ).toEqual({ POST: false })
    expect(
      verdicts(`
export async function POST(request: Request) {
  const user = await getServerUser()
  const denied = await requireChartPermission({ uid: user!.uid, chartId: 'c', access: 'write' })
  return denied ?? Response.json({})
}`),
    ).toEqual({ POST: true })
  })

  it('service verifiers: token, MCP key, OIDC, feed token, cron secret', () => {
    expect(verdicts(`export async function POST(req: Request) { if (!validateServiceToken(req)) return new Response(null, { status: 401 }); return Response.json({}) }`)).toEqual({ POST: true })
    expect(verdicts(`export async function POST(req: Request) { const p = await validateMcpKey(req.headers.get('authorization')); return Response.json({ p }) }`)).toEqual({ POST: true })
    expect(verdicts(`export async function POST(req: Request) { await verifyOidcToken(req.headers.get('authorization'), 'aud'); return Response.json({}) }`)).toEqual({ POST: true })
    expect(verdicts(`export async function GET(req: Request) { const r = verifyFeedToken(new URL(req.url).searchParams.get('t')!); return Response.json({ r }) }`)).toEqual({ GET: true })
    expect(verdicts(`export async function POST(req: Request) { const expected = process.env.MARSYS_CRON_SECRET; if (!expected || req.headers.get('x-marsys-cron-secret') !== expected) return new Response(null, { status: 401 }); return Response.json({}) }`)).toEqual({ POST: true })
    expect(verdicts(`export async function POST(req: Request) { const expected = process.env['MARSYS_CRON_SECRET']; if (!expected) return new Response(null, { status: 401 }); return Response.json({}) }`)).toEqual({ POST: true })
  })

  it('cron secret: only an env READ in code counts (not a comment, a string, or a bare mention)', () => {
    expect(verdicts(`// uses MARSYS_CRON_SECRET\nexport async function POST() { return Response.json({}) }`)).toEqual({ POST: false })
    expect(verdicts(`export async function POST() { return Response.json({ hint: 'MARSYS_CRON_SECRET' }) }`)).toEqual({ POST: false })
    expect(verdicts(`const MARSYS_CRON_SECRET = 'x'\nexport async function POST() { return Response.json({ MARSYS_CRON_SECRET }) }`)).toEqual({ POST: false })
  })

  it('tokenizer robustness: apostrophes in comments, // inside strings, division, braces in strings', () => {
    expect(
      verdicts(`
// don't break on this apostrophe
const url = 'http://example.com/a//b'
const half = 10 / 2 / 5
const braces = '}{'
/* it's fine */
export async function GET() {
  return Response.json({ url, half, braces })
}
export async function POST() {
  const u = await getServerUser() // check the user
  return Response.json({ u })
}`),
    ).toEqual({ GET: false, POST: true })
  })

  it('template-literal expressions are code (a real call inside ${} counts, the literal text does not)', () => {
    expect(verdicts("export async function GET() { return new Response(`${await getServerUser()}`) }")).toEqual({ GET: true })
    expect(verdicts("export async function GET() { return new Response(`getServerUser()`) }")).toEqual({ GET: false })
  })

  it('mentionsRecognisedCall agrees with the analyser on the basics', () => {
    expect(mentionsRecognisedCall('await getServerUser()')).toBe(true)
    expect(mentionsRecognisedCall('return 1')).toBe(false)
  })

  it('exported methods are only the HTTP verbs (helpers and config exports are ignored)', () => {
    expect(verdicts(`export const dynamic = 'force-dynamic'\nexport const maxDuration = 30\nexport async function helper() { return getServerUser() }\nexport async function GET() { return Response.json({}) }`)).toEqual({ GET: false })
  })
})

describe('detector proven on REAL code: neutering the recognised calls un-guards every handler', () => {
  // The strongest vacuity check: take the actual route sources, rename every
  // recognised verification identifier, and require that NO handler remains
  // "guarded". If the recogniser were satisfied by anything other than those
  // calls (a comment, a flag, an import), some handler would survive.
  const NEUTER = new RegExp(`\\b(?:${[...RECOGNISED_VERIFICATION_CALLS, 'MARSYS_CRON_SECRET'].join('|')})\\b`, 'g')

  it('before: a large majority guarded; after neutering: zero guarded', () => {
    let guardedBefore = 0
    let guardedAfter = 0
    const survivors: string[] = []
    for (const r of ROUTES) {
      for (const v of analyseRouteSource(r.source)) if (v.guarded) guardedBefore++
      for (const v of analyseRouteSource(r.source.replace(NEUTER, 'neutered'))) {
        if (v.guarded) {
          guardedAfter++
          survivors.push(`${r.dir} ${v.method} still guarded via ${v.via.join(',')}`)
        }
      }
    }
    expect(guardedBefore).toBeGreaterThan(200)
    expect(survivors, `\n${survivors.join('\n')}\n`).toEqual([])
    expect(guardedAfter).toBe(0)
  })

  it('neutering a SINGLE real guarded route flips exactly that route to unguarded', () => {
    const target = ROUTE_BY_DIR.get('charts/[id]')!
    expect(analyseRouteSource(target.source).every((v) => v.guarded)).toBe(true)
    const flipped = analyseRouteSource(target.source.replace(NEUTER, 'neutered'))
    expect(flipped.length).toBeGreaterThan(0)
    expect(flipped.every((v) => !v.guarded)).toBe(true)
  })

  it('a real unguarded (allow-listed) handler reads false and real guarded handlers read true (the lists are measuring something)', () => {
    // A real UNGUARDED handler (allow-listed public endpoint) reads false ...
    expect(HANDLERS.find((h) => h.dir === 'auth/resolve-username' && h.method === 'POST')?.guarded).toBe(false)
    expect(HANDLERS.find((h) => h.dir === 'auth/recover' && h.method === 'POST')?.guarded).toBe(false)
    // ... and real handlers that S1 fixed (previously pending) and a long-guarded sibling read true.
    expect(HANDLERS.find((h) => h.dir === 'icr/confirm' && h.method === 'POST')?.guarded).toBe(true)
    expect(HANDLERS.find((h) => h.dir === 'admin/users' && h.method === 'GET')?.guarded).toBe(true)
  })

  it('page detector: synthetic unguarded data-loading page reads false; guarded and client pages read true', () => {
    expect(pageLoadsDataWithoutOwnGuard(`import { db } from '@/lib/db'\nexport default async function Page() { return db.query('x') }`)).toEqual({ loadsData: true, guarded: false })
    expect(pageLoadsDataWithoutOwnGuard(`import { db } from '@/lib/db'\n// getServerUser()\nexport default async function Page() { return db.query('x') }`)).toEqual({ loadsData: true, guarded: false })
    expect(pageLoadsDataWithoutOwnGuard(`import { db } from '@/lib/db'\nexport default async function Page() { await getServerUser(); return db.query('x') }`)).toEqual({ loadsData: true, guarded: true })
    expect(pageLoadsDataWithoutOwnGuard(`import { db } from '@/lib/db'\nexport default async function Page() { await requireSuperAdminPage(); return db.query('x') }`)).toEqual({ loadsData: true, guarded: true })
    expect(pageLoadsDataWithoutOwnGuard(`import { db } from '@/lib/db'\nexport default async function Page() { await requireActiveUserPage('/login'); return db.query('x') }`)).toEqual({ loadsData: true, guarded: true })
    expect(pageLoadsDataWithoutOwnGuard(`import { db } from '@/lib/db'\n// await requireSuperAdminPage()\nexport default async function Page() { return db.query('x') }`)).toEqual({ loadsData: true, guarded: false })
    expect(pageLoadsDataWithoutOwnGuard(`import { db } from '@/lib/db'\nimport { requireActiveUserPage } from '@/lib/auth/active-user-page-guard'\nexport default async function Page() { return db.query('x') }`)).toEqual({ loadsData: true, guarded: false })
    expect(pageLoadsDataWithoutOwnGuard(`'use client'\nimport { db } from '@/lib/db'\nexport default function P() { return null }`)).toEqual({ loadsData: false, guarded: true })
    expect(pageLoadsDataWithoutOwnGuard(`export default async function Page() { const r = await fetch('http://sidecar/x'); return r.json() }`)).toEqual({ loadsData: true, guarded: false })
  })
})
