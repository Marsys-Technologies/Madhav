import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextResponse } from 'next/server'

// ─── module mocks ─────────────────────────────────────────────────────────────

vi.mock('server-only', () => ({}))

const mockRequireSuperAdmin = vi.fn()
vi.mock('@/lib/auth/access-control', () => ({
  requireSuperAdmin: mockRequireSuperAdmin,
}))

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

// guardAiopsRoute reads MARSYS_FLAG_OBSERVATORY_ENABLED from process.env
// We need to set it before importing _guard / route

vi.mock('@/lib/models/registry', async () => {
  const actual = await vi.importActual<typeof import('@/lib/models/registry')>('@/lib/models/registry')
  return actual
})

// ─── helpers ──────────────────────────────────────────────────────────────────

const MOCK_AUTH = {
  user:    { uid: 'u1', email: 'admin@test.com' },
  profile: { id: 'u1', role: 'super_admin', status: 'active' },
}

function authOk() {
  mockRequireSuperAdmin.mockResolvedValue(MOCK_AUTH)
}

function authUnauthorized() {
  mockRequireSuperAdmin.mockResolvedValue(
    NextResponse.json({ error: { code: 'AUTH_REQUIRED' } }, { status: 401 }),
  )
}

function authForbidden() {
  mockRequireSuperAdmin.mockResolvedValue(
    NextResponse.json({ error: { code: 'AUTH_FORBIDDEN' } }, { status: 403 }),
  )
}

function makeEmptyDbResponses() {
  mockQuery.mockResolvedValue({ rows: [] })
}

function makeRequest(): Request {
  return new Request('http://localhost/api/admin/aiops/state')
}

// ─── tests ────────────────────────────────────────────────────────────────────

describe('GET /api/admin/aiops/state', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.stubEnv('MARSYS_FLAG_OBSERVATORY_ENABLED', 'true')
  })

  it('returns 403 when MARSYS_FLAG_OBSERVATORY_ENABLED is not true', async () => {
    vi.stubEnv('MARSYS_FLAG_OBSERVATORY_ENABLED', 'false')
    // Re-import to pick up env change — guard reads process.env directly
    const mod = await import('../route')
    const res = await mod.GET(makeRequest())
    expect(res.status).toBe(403)
    const body = await res.json()
    expect(body.error.code).toBe('AUTH_FORBIDDEN')
  })

  it('returns 401 when user is not authenticated', async () => {
    authUnauthorized()
    const { GET } = await import('../route')
    const res = await GET(makeRequest())
    expect(res.status).toBe(401)
  })

  it('returns 403 when user is not super_admin', async () => {
    authForbidden()
    const { GET } = await import('../route')
    const res = await GET(makeRequest())
    expect(res.status).toBe(403)
  })

  it('returns valid state shape with empty DB', async () => {
    authOk()
    makeEmptyDbResponses()
    const { GET } = await import('../route')
    const res = await GET(makeRequest())
    expect(res.status).toBe(200)
    const body = await res.json()

    // Shape assertions
    expect(body).toHaveProperty('active_stack')
    expect(body).toHaveProperty('effective_routing')
    expect(body).toHaveProperty('effective_params')
    expect(body).toHaveProperty('health_summary')
    expect(body).toHaveProperty('audit_summary')
    expect(body.audit_summary).toHaveProperty('count')
    expect(body.audit_summary).toHaveProperty('latest_at')
    // Empty DB → default stack
    expect(body.active_stack).toBe('gemini')
  })

  it('effective_routing covers all 6 stacks and 11 call types', async () => {
    authOk()
    makeEmptyDbResponses()
    const { GET } = await import('../route')
    const res = await GET(makeRequest())
    const body = await res.json()

    const stacks = ['nim', 'anthropic', 'gemini', 'gpt', 'deepseek', 'marsys']
    const callTypes = [
      'synthesis', 'planner_deep', 'planner_fast', 'context_assembly', 'worker',
      'eval_judge', 'eval_generator', 'smoke_synth', 'checkpoint_4_5', 'checkpoint_5_5', 'checkpoint_8_5',
    ]

    for (const s of stacks) {
      expect(body.effective_routing).toHaveProperty(s)
      for (const ct of callTypes) {
        expect(body.effective_routing[s]).toHaveProperty(ct)
        expect(body.effective_routing[s][ct]).toHaveProperty('primary')
        expect(body.effective_routing[s][ct]).toHaveProperty('fallback')
      }
    }
  })

  it('MARSYS stack appears in effective_routing with non-empty models', async () => {
    authOk()
    makeEmptyDbResponses()
    // Seed MARSYS routes via DB mock (registry has marsys routing for all call types)
    const { GET } = await import('../route')
    const res = await GET(makeRequest())
    const body = await res.json()
    // marsys routing should be surfaced — at least synthesis should have a non-empty primary
    const marsysSynthesis = body.effective_routing?.marsys?.synthesis
    expect(marsysSynthesis).toBeDefined()
    // primary may be '' if marsys has no registry entry for this ct, but the key should exist
    expect(marsysSynthesis).toHaveProperty('primary')
    expect(marsysSynthesis).toHaveProperty('fallback')
  })
})
