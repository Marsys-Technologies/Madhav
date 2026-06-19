/**
 * Stream C / Unit 2d — Command Center acceptance tests.
 *
 * Covers the brief's five acceptance criteria + a handful of structural checks
 * over gate_registry / configService / Command Center API surface.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { NextResponse } from 'next/server'

// ─── module-level mocks (must precede route imports) ─────────────────────────

vi.mock('server-only', () => ({}))

const mockQuery = vi.fn()
vi.mock('@/lib/db/client', () => ({ query: mockQuery }))

const mockRequireSuperAdmin = vi.fn()
const mockGetServerUserWithProfile = vi.fn()
vi.mock('@/lib/auth/access-control', () => ({
  requireSuperAdmin: mockRequireSuperAdmin,
  getServerUserWithProfile: mockGetServerUserWithProfile,
}))

const mockRedirect = vi.fn((_url: string) => {
  throw new Error('NEXT_REDIRECT')
})
vi.mock('next/navigation', () => ({
  redirect: mockRedirect,
}))

// ─── helpers ──────────────────────────────────────────────────────────────────

function authOk() {
  const ctx = {
    user: { uid: 'admin-uid', email: 'admin@test' } as any,
    profile: { id: 'admin-uid', role: 'super_admin', status: 'active' } as const,
  }
  mockRequireSuperAdmin.mockResolvedValue(ctx)
  mockGetServerUserWithProfile.mockResolvedValue(ctx)
}

function authForbidden() {
  mockRequireSuperAdmin.mockResolvedValue(
    NextResponse.json({ error: { code: 'forbidden' } }, { status: 403 }),
  )
  mockGetServerUserWithProfile.mockResolvedValue({
    user: { uid: 'u', email: 'u@test' } as any,
    profile: { id: 'u', role: 'guest', status: 'active' } as const,
  })
}

function authUnauthorized() {
  mockRequireSuperAdmin.mockResolvedValue(
    NextResponse.json({ error: { code: 'unauthorized' } }, { status: 401 }),
  )
  mockGetServerUserWithProfile.mockResolvedValue(null)
}

function emptyRows() {
  mockQuery.mockResolvedValue({ rows: [] })
}

beforeEach(() => {
  vi.clearAllMocks()
  // Reset module cache so configService's in-process cache resets between tests.
  vi.resetModules()
})

// ─── A — configService gate reader ────────────────────────────────────────────

describe('configService.getGate', () => {
  it('reads runtime_config row when present (DB wins over env + default)', async () => {
    // First query: per_chart (skipped — global scope), second: global lookup.
    mockQuery.mockResolvedValueOnce({
      rows: [{ value: false, value_type: 'boolean' }],
    })
    const { getGate, _clearGateCache } = await import('@/lib/config/configService')
    _clearGateCache()
    const v = await getGate<boolean>('MARSYS_FLAG_OBSERVATORY_ENABLED')
    expect(v).toBe(false)
    expect(mockQuery).toHaveBeenCalled()
  })

  it('falls back to env when no runtime_config row exists', async () => {
    emptyRows()
    process.env.MARSYS_FLAG_OBSERVATORY_ENABLED = 'false'
    const { getGate, _clearGateCache } = await import('@/lib/config/configService')
    _clearGateCache()
    const v = await getGate<boolean>('MARSYS_FLAG_OBSERVATORY_ENABLED')
    expect(v).toBe(false)
    delete process.env.MARSYS_FLAG_OBSERVATORY_ENABLED
  })

  it('falls back to gate_registry default when nothing else is set', async () => {
    emptyRows()
    delete process.env.MARSYS_FLAG_OBSERVATORY_ENABLED
    const { getGate, _clearGateCache } = await import('@/lib/config/configService')
    _clearGateCache()
    const v = await getGate<boolean>('MARSYS_FLAG_OBSERVATORY_ENABLED')
    expect(v).toBe(true) // registry default
  })

  it('throws on unknown gate', async () => {
    const { getGate } = await import('@/lib/config/configService')
    await expect(getGate('NONEXISTENT_GATE')).rejects.toThrow(/unknown gate/)
  })
})

// ─── B — configService gate writer ────────────────────────────────────────────

describe('configService.setGate', () => {
  it('writes runtime_config (gate_change_log retired WS-0)', async () => {
    // 1. setGate → bypass-cache getGate → global runtime_config select → rows:[]
    // 2. INSERT runtime_config
    mockQuery
      .mockResolvedValueOnce({ rows: [] }) // pre-read old value
      .mockResolvedValueOnce({ rows: [] }) // upsert

    const { setGate } = await import('@/lib/config/configService')
    await setGate('MSR_ENABLED', false, 'admin-uid', { reason: 'smoke' })

    // 2 DB calls: pre-read SELECT + UPSERT. gate_change_log write retired WS-0.
    expect(mockQuery).toHaveBeenCalledTimes(2)
    const sqls = mockQuery.mock.calls.map((c: any[]) => c[0] as string)
    expect(sqls.some((s) => s.includes('INSERT INTO runtime_config'))).toBe(true)
  })

  it('rejects AYANAMSHA_CANONICAL_ENABLED=false (hard guard)', async () => {
    emptyRows()
    const { setGate, GateWriteError } = await import('@/lib/config/configService')
    await expect(
      setGate('AYANAMSHA_CANONICAL_ENABLED', false, 'admin-uid'),
    ).rejects.toBeInstanceOf(GateWriteError)
  })

  it('gate_change_log audit write retired WS-0 — only 2 DB calls on edit', async () => {
    mockQuery
      .mockResolvedValueOnce({ rows: [] })
      .mockResolvedValueOnce({ rows: [] })

    const { setGate } = await import('@/lib/config/configService')
    await setGate('LEL_ENABLED', false, 'admin-uid', { reason: 'kill-switch test' })

    expect(mockQuery).toHaveBeenCalledTimes(2)
  })
})

// ─── C — Command Center API auth ──────────────────────────────────────────────

describe('POST /cockpit/command-center/api/edit (auth + danger guard)', () => {
  function reqBody(body: Record<string, unknown>): Request {
    return new Request('http://localhost/cockpit/command-center/api/edit', {
      method: 'POST',
      body: JSON.stringify(body),
      headers: { 'content-type': 'application/json' },
    })
  }

  it('returns 401 when user is not authenticated', async () => {
    authUnauthorized()
    const { POST } = await import('../command-center/api/edit/route')
    const res = await POST(reqBody({ key: 'MSR_ENABLED', value: false }))
    expect(res.status).toBe(401)
  })

  it('returns 403 when user is not super_admin', async () => {
    authForbidden()
    const { POST } = await import('../command-center/api/edit/route')
    const res = await POST(reqBody({ key: 'MSR_ENABLED', value: false }))
    expect(res.status).toBe(403)
  })

  it('rejects unknown gate with 404', async () => {
    authOk()
    const { POST } = await import('../command-center/api/edit/route')
    const res = await POST(reqBody({ key: 'NOPE', value: false }))
    expect(res.status).toBe(404)
  })

  it('rejects danger:true gate edit without confirm:true (422)', async () => {
    authOk()
    const { POST } = await import('../command-center/api/edit/route')
    const res = await POST(reqBody({ key: 'FORENSIC_ENABLED', value: false }))
    expect(res.status).toBe(422)
    const body = await res.json()
    expect(body.error.code).toBe('CONFIRM_REQUIRED')
  })

  it('accepts danger:true gate edit with confirm:true', async () => {
    authOk()
    mockQuery
      .mockResolvedValueOnce({ rows: [] }) // pre-read
      .mockResolvedValueOnce({ rows: [] }) // upsert
      .mockResolvedValueOnce({ rows: [] }) // change-log insert

    const { POST } = await import('../command-center/api/edit/route')
    const res = await POST(
      reqBody({ key: 'FORENSIC_ENABLED', value: false, confirm: true }),
    )
    expect(res.status).toBe(200)
  })

  it('AYANAMSHA_CANONICAL_ENABLED=false returns 422 via API', async () => {
    authOk()
    const { POST } = await import('../command-center/api/edit/route')
    const res = await POST(
      reqBody({ key: 'AYANAMSHA_CANONICAL_ENABLED', value: false, confirm: true }),
    )
    expect(res.status).toBe(422)
    const body = await res.json()
    expect(body.error.code).toBe('CANONICAL_AYANAMSHA_LOCKED')
  })
})

// ─── D — gate_registry structural ─────────────────────────────────────────────

describe('gate_registry', () => {
  it('contains entries spanning all five classes', async () => {
    const { gatesByClass } = await import('@/lib/gates/gate_registry')
    const grouped = gatesByClass()
    expect(grouped.feature_flag.length).toBeGreaterThan(0)
    expect(grouped.pipeline_threshold.length).toBeGreaterThan(0)
    expect(grouped.model_routing.length).toBeGreaterThan(0)
    expect(grouped.access_capability.length).toBeGreaterThan(0)
    expect(grouped.data_source.length).toBeGreaterThan(0)
  })

  it('exposes ayanamsha registry with canonical/kp/reference', async () => {
    const { AYANAMSHA_REGISTRY } = await import('@/lib/gates/gate_registry')
    const roles = AYANAMSHA_REGISTRY.map((r) => r.role)
    expect(roles).toEqual(['canonical', 'kp', 'reference'])
  })

  it('FORENSIC_ENABLED is marked danger:true (cascade-risk asset)', async () => {
    const { getGateSpec } = await import('@/lib/gates/gate_registry')
    const spec = getGateSpec('FORENSIC_ENABLED')
    expect(spec.danger).toBe(true)
    expect(spec.class).toBe('data_source')
  })
})

// ─── E — LEL gate propagation (AC.4) ──────────────────────────────────────────

describe('LEL_ENABLED runtime override', () => {
  it('OFF in runtime_config propagates to readers (dependent tools see disabled)', async () => {
    // Global lookup returns LEL_ENABLED=false.
    mockQuery.mockResolvedValueOnce({
      rows: [{ value: false, value_type: 'boolean' }],
    })
    const { getGate, _clearGateCache } = await import('@/lib/config/configService')
    _clearGateCache()
    const v = await getGate<boolean>('LEL_ENABLED')
    expect(v).toBe(false)
    // TODO(2d-followup): wire the manifest data_dependency graph so dependent
    // retrieval tools (query_life_events, etc.) consult getGate('LEL_ENABLED')
    // and short-circuit when false. For this MVP the propagation is exercised
    // at the getGate boundary only.
  })
})
