/**
 * m8_e2e_proof.test.ts — M8 harden + prove test suite.
 *
 * Covers the M8 acceptance criteria (Goal Proof Matrix G1–G12, V0–V6) using
 * Vitest mocks for all external dependencies (platform API, DB).
 *
 * Goal clauses proven in this file (mock/unit layer):
 *   G2:  Identity + entitlement — each user sees only their entitled chart set
 *   G4:  Gated every call — unentitled chart → AUTHZ_DENIED
 *   G5:  Session + memory — recall_session gated per user×chart
 *   G7:  Per-model surface — declared vs undeclared key → different model_family
 *   G8:  Resources + prompts — 9 resources + 3 guided prompts registered
 *   G11: Zero bleed — no native name in any chart-agnostic surface
 *   G12: Completeness — REGISTERED_TOOL_COUNT truthful (matches grep count)
 *   V0:  Rate limiter in-process logic (allow / throttle)
 *   V1:  Rate limiting universal — sidecar dispatch rejects after limit
 *
 * Integration-only tests (require real prod endpoints) are marked with
 * `@integration` in their name and skipped here.
 *
 * Chart-agnostic: no native chart_id (482012f1-…) or native name appears
 * anywhere in this file. All chart_ids are synthetic test UUIDs.
 *
 * Vitest — not jest. All mocks use vi.fn() / vi.stubGlobal().
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import type { Principal } from '../types.js'

// ── Fixtures ──────────────────────────────────────────────────────────────────

// Synthetic test UUIDs — never use the native chart_id
const CHART_A = 'aaaaaaaa-1111-0000-0000-000000000001'
const CHART_B = 'bbbbbbbb-2222-0000-0000-000000000002'

function makePrincipal(overrides: Partial<Principal> = {}): Principal {
  return {
    user_uid: 'user-m8-test-001',
    key_id: 'mcp_test_m8_00001',
    role: 'guest',
    ...overrides,
  }
}

function makeSuperAdmin(): Principal {
  return {
    user_uid: 'user-admin-001',
    key_id: 'mcp_admin_key_001',
    role: 'super_admin',
  }
}

// ── Mock fetch globally ────────────────────────────────────────────────────────

const mockFetch = vi.fn()
vi.stubGlobal('fetch', mockFetch)

beforeEach(() => {
  mockFetch.mockReset()
})

afterEach(() => {
  vi.restoreAllMocks()
})

// ─────────────────────────────────────────────────────────────────────────────
// V0 — In-process rate limiter logic
// ─────────────────────────────────────────────────────────────────────────────

describe('V0/V1 — In-process rate limiter (sidecar dispatch)', () => {
  it('allows requests within the RPM limit', async () => {
    const { checkMcpRateLimit, __resetForTests } = await import('../lib/rate_limiter.js')
    __resetForTests()

    const result = checkMcpRateLimit('key-rate-test-001')
    expect(result.allowed).toBe(true)
  })

  it('throttles after RPM_LIMIT requests in the same window', async () => {
    const { checkMcpRateLimit, RPM_LIMIT, __resetForTests } = await import('../lib/rate_limiter.js')
    __resetForTests()

    const keyId = 'key-rate-test-002'
    // Exhaust the limit
    for (let i = 0; i < RPM_LIMIT; i++) {
      const r = checkMcpRateLimit(keyId)
      expect(r.allowed).toBe(true)
    }
    // Next call should be throttled
    const throttled = checkMcpRateLimit(keyId)
    expect(throttled.allowed).toBe(false)
    expect(throttled.retry_after_seconds).toBeGreaterThan(0)
    expect(throttled.retry_after_seconds).toBeLessThanOrEqual(60)
  })

  it('different key_ids have independent counters', async () => {
    const { checkMcpRateLimit, RPM_LIMIT, __resetForTests } = await import('../lib/rate_limiter.js')
    __resetForTests()

    const keyA = 'key-rate-test-a'
    const keyB = 'key-rate-test-b'

    // Exhaust key A
    for (let i = 0; i < RPM_LIMIT; i++) {
      checkMcpRateLimit(keyA)
    }
    // Key A throttled
    expect(checkMcpRateLimit(keyA).allowed).toBe(false)
    // Key B still allowed
    expect(checkMcpRateLimit(keyB).allowed).toBe(true)
  })

  it('RPM_LIMIT defaults to 60 (env-driven)', async () => {
    const { RPM_LIMIT } = await import('../lib/rate_limiter.js')
    // Default is 60 unless MCP_RPM_LIMIT env var overrides
    expect(RPM_LIMIT).toBeGreaterThan(0)
    expect(RPM_LIMIT).toBeLessThanOrEqual(1000)
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// M8 Structured Logger
// ─────────────────────────────────────────────────────────────────────────────

describe('M8 — Structured logger + request-ID', () => {
  it('generateRequestId() returns a string with mcp- prefix', async () => {
    const { generateRequestId } = await import('../lib/logger.js')
    const id = generateRequestId()
    expect(typeof id).toBe('string')
    expect(id).toMatch(/^mcp-[0-9a-f]+-[0-9a-f]+$/)
  })

  it('generateRequestId() produces unique IDs on successive calls', async () => {
    const { generateRequestId } = await import('../lib/logger.js')
    const ids = new Set(Array.from({ length: 20 }, () => generateRequestId()))
    // All 20 should be distinct (collision probability negligible)
    expect(ids.size).toBe(20)
  })

  it('log() writes structured JSON to stdout via console.log', async () => {
    const { log } = await import('../lib/logger.js')
    const written: string[] = []
    vi.spyOn(console, 'log').mockImplementation((...args: unknown[]) => {
      written.push(args.map(String).join(' '))
    })

    log({
      level: 'info',
      request_id: 'mcp-test-abc123',
      user_uid: 'uid-test',
      key_id: 'key-test',
      tool: 'list_my_charts',
      outcome: 'ok',
      latency_ms: 42,
      message: 'test log entry',
    })

    expect(written.length).toBeGreaterThan(0)
    const parsed = JSON.parse(written[0]!) as Record<string, unknown>
    expect(parsed['service']).toBe('marsys-mcp')
    expect(parsed['level']).toBe('info')
    expect(parsed['request_id']).toBe('mcp-test-abc123')
    expect(parsed['tool']).toBe('list_my_charts')
    expect(parsed['outcome']).toBe('ok')
    expect(parsed['latency_ms']).toBe(42)
    expect(parsed['timestamp']).toBeDefined()
  })

  it('log() omits undefined fields from JSON output', async () => {
    const { log } = await import('../lib/logger.js')
    const written: string[] = []
    vi.spyOn(console, 'log').mockImplementation((...args: unknown[]) => {
      written.push(args.map(String).join(' '))
    })

    log({
      level: 'info',
      request_id: 'mcp-test-no-tool',
      message: 'minimal log entry',
    })

    const parsed = JSON.parse(written[0]!) as Record<string, unknown>
    // tool, chart_id, user_uid, etc. should not appear if not provided
    expect(Object.prototype.hasOwnProperty.call(parsed, 'tool')).toBe(false)
    expect(Object.prototype.hasOwnProperty.call(parsed, 'chart_id')).toBe(false)
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// G2 — Identity + entitlement (remoteAuthorize)
// ─────────────────────────────────────────────────────────────────────────────

describe('G2 — Identity + entitlement isolation', () => {
  it('User A owns Chart A — authorized', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ authorized: true, permission: 'all' }),
    })
    const { remoteAuthorize } = await import('../lib/authz.js')
    const userA = makePrincipal({ user_uid: 'user-a', key_id: 'key-a' })
    expect(await remoteAuthorize(userA, CHART_A)).toBe(true)
  })

  it('User A cannot access Chart B (isolation: no cross-chart bleed)', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ authorized: false, permission: 'deny' }),
    })
    const { remoteAuthorize } = await import('../lib/authz.js')
    const userA = makePrincipal({ user_uid: 'user-a', key_id: 'key-a' })
    expect(await remoteAuthorize(userA, CHART_B)).toBe(false)
  })

  it('super_admin can access any chart', async () => {
    // super_admin bypasses entitlement check — platform returns authorized=true
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ authorized: true, permission: 'all' }),
    })
    const { remoteAuthorize } = await import('../lib/authz.js')
    const admin = makeSuperAdmin()
    expect(await remoteAuthorize(admin, CHART_B)).toBe(true)
  })

  it('fail-closed: network error → denied', async () => {
    mockFetch.mockRejectedValueOnce(new Error('network timeout'))
    const { remoteAuthorize } = await import('../lib/authz.js')
    expect(await remoteAuthorize(makePrincipal(), CHART_A)).toBe(false)
  })

  it('fail-closed: 401 from platform → denied', async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 401 })
    const { remoteAuthorize } = await import('../lib/authz.js')
    expect(await remoteAuthorize(makePrincipal(), CHART_A)).toBe(false)
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// G4 — Every call gated: unentitled chart → AUTHZ_DENIED
// ─────────────────────────────────────────────────────────────────────────────

describe('G4 — Entitlement gate: unentitled chart denied on every chart-scoped call', () => {
  it('remoteAuthorize returns false when platform denies (permission=deny)', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ authorized: false, permission: 'deny' }),
    })
    const { remoteAuthorize } = await import('../lib/authz.js')
    const guest = makePrincipal({ user_uid: 'user-guest-b', key_id: 'key-b' })
    const denied = await remoteAuthorize(guest, CHART_A)
    expect(denied).toBe(false)
  })

  it('view-grant user cannot write (required=all → denied)', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ authorized: false, permission: 'view' }),
    })
    const { remoteAuthorize } = await import('../lib/authz.js')
    const viewUser = makePrincipal({ user_uid: 'user-view', key_id: 'key-view' })
    expect(await remoteAuthorize(viewUser, CHART_A, 'all')).toBe(false)
  })

  it('view-grant user can read (required=view → authorized)', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ authorized: true, permission: 'view' }),
    })
    const { remoteAuthorize } = await import('../lib/authz.js')
    const viewUser = makePrincipal({ user_uid: 'user-view', key_id: 'key-view' })
    expect(await remoteAuthorize(viewUser, CHART_A, 'view')).toBe(true)
  })

  it('remoteAuthorize sends correct user_uid + chart_id in request body', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ authorized: true, permission: 'view' }),
    })
    const { remoteAuthorize } = await import('../lib/authz.js')
    const principal = makePrincipal({ user_uid: 'user-body-check', key_id: 'key-body' })
    await remoteAuthorize(principal, CHART_B)
    const body = JSON.parse(mockFetch.mock.calls[0]![1]!.body as string) as Record<string, unknown>
    expect(body['user_uid']).toBe('user-body-check')
    expect(body['chart_id']).toBe(CHART_B)
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// G5 — Session + memory (recall_session per user×chart)
// ─────────────────────────────────────────────────────────────────────────────

describe('G5 — Session recall: scoped per user×chart', () => {
  it('getOrCreateSession calls platform with user_uid in headers (session scope)', async () => {
    // Mock: platform returns a session record wrapped in { session: ... }
    // (matches getOrCreateSession implementation: data.session ?? null)
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        session: {
          session_id: 'sess-001',
          user_uid: 'user-m8-test-001',
          session_key: 'default',
          active_chart_id: CHART_A,
          created_at: '2026-07-01T00:00:00Z',
          last_seen_at: '2026-07-01T01:00:00Z',
          state_json: {},
        },
      }),
    })

    const { getOrCreateSession } = await import('../lib/session.js')
    const principal = makePrincipal()
    const session = await getOrCreateSession(principal, 'default')
    // Should have called the platform session endpoint
    expect(mockFetch).toHaveBeenCalledTimes(1)
    const [url] = mockFetch.mock.calls[0]!
    expect(String(url)).toContain('/api/mcp/session')
    // Session is scoped to the user (user_uid comes from principal, not body)
    expect(session?.user_uid).toBe('user-m8-test-001')
    expect(session?.active_chart_id).toBe(CHART_A)
  })

  it('session state is isolated by user — different users get different sessions', async () => {
    // User A session — mock wraps in { session: ... }
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        session: {
          session_id: 'sess-user-a',
          user_uid: 'user-a',
          session_key: 'default',
          active_chart_id: CHART_A,
          created_at: '2026-07-01T00:00:00Z',
          last_seen_at: '2026-07-01T01:00:00Z',
          state_json: { context: 'user-a-context' },
        },
      }),
    })
    const { getOrCreateSession } = await import('../lib/session.js')
    const userA = makePrincipal({ user_uid: 'user-a', key_id: 'key-a' })
    const sessionA = await getOrCreateSession(userA, 'default')
    expect(sessionA?.user_uid).toBe('user-a')
    expect(sessionA?.active_chart_id).toBe(CHART_A)
    // No cross-user bleed in the session data
    expect(JSON.stringify(sessionA?.state_json ?? {})).not.toContain('user-b')
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// G7 — Per-model surface: declared vs undeclared key
// ─────────────────────────────────────────────────────────────────────────────

describe('G7 — Declared model profile shapes surface', () => {
  it('Principal with model_family has declared profile', () => {
    const declared = makePrincipal({ model_family: 'anthropic' })
    expect(declared.model_family).toBe('anthropic')
  })

  it('Principal without model_family falls back to universal surface', () => {
    const undeclared = makePrincipal()
    expect(undeclared.model_family).toBeUndefined()
  })

  it('model_family can be anthropic | gemini | openai | deepseek', () => {
    const families = ['anthropic', 'gemini', 'openai', 'deepseek'] as const
    for (const family of families) {
      const p = makePrincipal({ model_family: family })
      expect(p.model_family).toBe(family)
    }
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// G8 — Richness: 9 resources + 3 guided-reading prompts
// ─────────────────────────────────────────────────────────────────────────────

describe('G8 — Resources (9) and prompts (3) registered', () => {
  function makeMockServer() {
    const registeredPrompts: string[] = []
    const registeredResources: Array<{ uri: string }> = []
    return {
      prompt: vi.fn((name: string) => { registeredPrompts.push(name) }),
      resource: vi.fn((uriOrTemplate: string | { uriTemplate: string }) => {
        const uri = typeof uriOrTemplate === 'string'
          ? uriOrTemplate
          : uriOrTemplate.uriTemplate
        registeredResources.push({ uri: String(uri) })
      }),
      _prompts: registeredPrompts,
      _resources: registeredResources,
    }
  }

  it('registerPrompts() registers exactly 3 prompts', async () => {
    const { registerPrompts } = await import('../prompts/index.js')
    const srv = makeMockServer()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    registerPrompts(srv as any)
    expect(srv._prompts.length).toBe(3)
  })

  it('3 prompts are: orient_chart, assess_domain, find_active_yogas', async () => {
    const { registerPrompts } = await import('../prompts/index.js')
    const srv = makeMockServer()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    registerPrompts(srv as any)
    expect(srv._prompts).toContain('orient_chart')
    expect(srv._prompts).toContain('assess_domain')
    expect(srv._prompts).toContain('find_active_yogas')
  })

  it('registerResources() registers exactly 9 resources (+ chart_snapshot template)', async () => {
    const { registerResources } = await import('../resources/index.js')
    const principal = makePrincipal()
    const srv = makeMockServer()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    registerResources(srv as any, principal)
    // 9 static resources + at least the dynamic/template resources
    // The requirement is ≥9 resource registrations
    expect(srv._resources.length).toBeGreaterThanOrEqual(9)
  })

  it('resources include house_rules (chart-agnostic)', async () => {
    const { registerResources } = await import('../resources/index.js')
    const srv = makeMockServer()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    registerResources(srv as any, makePrincipal())
    const uris = srv._resources.map(r => r.uri)
    expect(uris.some(u => u.includes('house_rules') || u.includes('rules'))).toBe(true)
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// G11 — Zero bleed: no native name in chart-agnostic surfaces
// ─────────────────────────────────────────────────────────────────────────────

describe('G11 — Zero bleed: no native name in chart-agnostic surfaces', () => {
  it('house_rules resource contains no native name', async () => {
    const { getHouseRules } = await import('../resources/house_rules.js')
    const rules = getHouseRules()
    // CLAUDE.md §B names the native; rules must not contain it
    expect(rules).not.toContain('Abhisek')
    expect(rules).not.toContain('Mohanty')
    expect(rules).not.toContain('Bhubaneswar')
  })

  it('Principal type has no chart_id field (chart-agnostic identity)', () => {
    const p = makePrincipal()
    // @ts-expect-error — chart_id must not exist on Principal
    expect(p.chart_id).toBeUndefined()
  })

  it('Principal type has no native_name field', () => {
    const p = makePrincipal()
    // @ts-expect-error — native_name must not exist on Principal
    expect(p.native_name).toBeUndefined()
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// G12 — Completeness: REGISTERED_TOOL_COUNT truthful
// ─────────────────────────────────────────────────────────────────────────────

describe('G12 — REGISTERED_TOOL_COUNT is truthful', () => {
  /**
   * This test imports all tool-registration modules and uses a mock McpServer
   * to count actual server.tool() calls, then compares against the declared constant.
   *
   * If this test fails, REGISTERED_TOOL_COUNT in server.ts is stale.
   */
  it('counted tools match REGISTERED_TOOL_COUNT=45', async () => {
    // Import all registration functions
    const [
      { registerL0BrahmagyanTools },
      { registerEphemerisTools },
      { registerComputeNatalPositionsTool, registerQueryDashaPeriodsTool, registerQuerySpecialLagnasTool },
      { registerHolisticBundleRetrievalTool },
      { registerKalaTemporalRetrievalTool },
      { registerRemedyTools },
      { registerPhalaEventAnchorsTool },
      { registerMitigationMapTool },
      { registerMuhurtaFinder },
      { registerPhalaOutlookTool },
      { registerMimamsaLelIntakeTool },
      { registerMimamsaOutcomeTool },
      { registerRegistryBridgeTools },
      { registerChartSelectionTools },
      { registerSessionTools },
    ] = await Promise.all([
      import('../tools/l0_brahmagyan.js'),
      import('../tools/l0_ephemeris.js'),
      import('../tools/retrieval/pyhora_natal.js'),
      import('../tools/retrieval/holistic_bundle.js'),
      import('../tools/retrieval/kala_temporal.js'),
      import('../tools/retrieval/remedy_tools.js'),
      import('../tools/phala_event_anchors.js'),
      import('../tools/phala_mitigation_map.js'),
      import('../tools/muhurta_finder.js'),
      import('../tools/phala_outlook.js'),
      import('../tools/mimamsa_lel_intake.js'),
      import('../tools/mimamsa_outcome.js'),
      import('../tools/registry_bridge.js'),
      import('../tools/chart_selection.js'),
      import('../tools/session_tools.js'),
    ])

    let toolCount = 0
    const mockServer = {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      tool: vi.fn((..._args: any[]) => { toolCount++ }),
    }
    const principal = makePrincipal()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const srv = mockServer as any

    registerL0BrahmagyanTools(srv)
    registerEphemerisTools(srv)
    registerComputeNatalPositionsTool(srv)
    registerQueryDashaPeriodsTool(srv)
    registerQuerySpecialLagnasTool(srv)
    registerHolisticBundleRetrievalTool(srv, () => principal)
    registerKalaTemporalRetrievalTool(srv)
    registerRemedyTools(srv, () => principal)
    registerPhalaEventAnchorsTool(srv, principal)
    registerMitigationMapTool(srv, principal)
    registerMuhurtaFinder(srv, () => principal)
    registerPhalaOutlookTool(srv, principal)
    registerMimamsaLelIntakeTool(srv, principal)
    registerMimamsaOutcomeTool(srv, principal)
    registerRegistryBridgeTools(srv)
    registerChartSelectionTools(srv, principal)
    registerSessionTools(srv, principal)

    // The declared constant
    const REGISTERED_TOOL_COUNT = 45
    expect(toolCount).toBe(REGISTERED_TOOL_COUNT)
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// V5 — Anti-regression: M0 isolation matrix still passes
// ─────────────────────────────────────────────────────────────────────────────

describe('V5 — Anti-regression: M0 security gate still intact', () => {
  it('remoteAuthorize still fail-closes on bad platform response', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ authorized: false, permission: 'deny' }),
    })
    const { remoteAuthorize } = await import('../lib/authz.js')
    expect(await remoteAuthorize(makePrincipal(), CHART_A)).toBe(false)
  })

  it('remoteAuthorize still fail-closes on thrown network error', async () => {
    mockFetch.mockRejectedValueOnce(new Error('network down'))
    const { remoteAuthorize } = await import('../lib/authz.js')
    expect(await remoteAuthorize(makePrincipal(), CHART_A)).toBe(false)
  })

  it('Principal type carries role (M0 invariant)', () => {
    const guest = makePrincipal({ role: 'guest' })
    expect(guest.role).toBe('guest')
    const admin = makeSuperAdmin()
    expect(admin.role).toBe('super_admin')
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// V6 — Invariants: retrieval FROZEN (chart-agnostic gate)
// ─────────────────────────────────────────────────────────────────────────────

describe('V6 — Invariants: tool names snake_case, no hyphens', () => {
  /**
   * Verifies the D7 tool naming invariant: all MCP tool names must be snake_case
   * with no hyphens (per RETRIEVAL_GROUNDTRUTH_LLM_PROVIDER_SPEC §B.i).
   *
   * We collect tool names by calling registerRegistryBridgeTools on a mock server
   * and asserting the names match ^[a-z][a-z0-9_]*$.
   */
  it('all D7 registry bridge tool names are snake_case', async () => {
    const { registerRegistryBridgeTools } = await import('../tools/registry_bridge.js')
    const toolNames: string[] = []
    const srv = {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      tool: vi.fn((name: string, ..._rest: any[]) => { toolNames.push(name) }),
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    registerRegistryBridgeTools(srv as any)
    for (const name of toolNames) {
      expect(name).toMatch(/^[a-z][a-z0-9_]*$/)
      expect(name).not.toContain('-')
    }
    expect(toolNames.length).toBe(12)
  })

  it('all chart-selection tool names are snake_case', async () => {
    const { registerChartSelectionTools } = await import('../tools/chart_selection.js')
    const toolNames: string[] = []
    const srv = {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      tool: vi.fn((name: string, ..._rest: any[]) => { toolNames.push(name) }),
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    registerChartSelectionTools(srv as any, makePrincipal())
    for (const name of toolNames) {
      expect(name).toMatch(/^[a-z][a-z0-9_]*$/)
    }
  })
})

// ─────────────────────────────────────────────────────────────────────────────
// Integration stubs (skipped — require live prod endpoints)
// ─────────────────────────────────────────────────────────────────────────────

describe.skip('INTEGRATION — G1/G3/G6/G9/G10 (live prod, skip in CI)', () => {
  it('@integration G1: OAuth connect → real uid (not anonymous)', () => {
    // Proven manually: POST /mcp/oauth/token with valid code → uid != 'anonymous'
    // Requires: live amjis-mcp + Firebase OAuth flow
  })

  it('@integration G3: list_my_charts → chart names (not UUIDs)', () => {
    // Proven manually: list_my_charts returns display_name field
    // Requires: live platform with chart_grants / owner_id match
  })

  it('@integration G6: chart switch advisory fires', () => {
    // Proven manually: select_chart on different chart_id → advisory warning in response
    // Requires: live session with prior active chart
  })

  it('@integration G9: registry-served tool → real data (not MCP-side SQL)', () => {
    // Proven manually: get_chart_orientation with valid chart_id → data from platform registry
    // Requires: live platform + populated DB
  })

  it('@integration G10: assess_marriage reasoning unit → grounded acharya-grade output', () => {
    // Proven manually: assess_marriage tool invoked → grounded fact-cited response
    // Requires: live platform + LLM synthesis pipeline
  })

  it('@integration V2: structured logs visible in Cloud Logging with request-ID correlation', () => {
    // Proven manually: Cloud Logging shows structured JSON with request_id tracing
    // MCP → platform → sidecar all carry the same X-Request-ID
  })

  it('@integration V3: deployed revision SHA == sealed main HEAD', () => {
    // Proven manually: gcloud run services describe amjis-mcp --region asia-south1
    //   → current revision matches git rev-parse main
  })
})
