// @vitest-environment node
//
// Retrieval Plane Elevation — plan R-1 item 3 ("single bootstrap", W2b lane).
//
// Proves BOTH states of the RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED feature flag on
// /api/retrieval/capability/route.ts:
//
//   flag=false (default) — route.ts keeps its own hand-maintained per-wave
//     registration list. Byte-for-byte the same dispatch behavior as before
//     this lane, INCLUDING the pre-existing, documented gap: capabilities
//     registered only via registry/catalog.ts's import chain (currently just
//     `marsys://tool/synthesis/compose_large_n`) are NOT reachable here.
//
//   flag=true — route.ts imports its registration list EXCLUSIVELY from
//     registry/catalog.ts's getCatalog(). After this lane's catalog.ts
//     completeness fix (registerRouterCapabilities()/registerMaroCapabilities()/
//     registerD6SynergyCapabilities() now also fire from catalog.ts), the
//     single-bootstrap catalog is a superset of everything route.ts ever
//     hand-registered, PLUS the reverse gap (synth_compose_large_n).
//
// The flag itself is never flipped on in any committed env/deploy config by
// this lane — see feature_flags.ts DEFAULT_FLAGS (default false) and the
// "defaults off" test below.

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { NextRequest } from 'next/server'

const ORIGINAL_ENV = { ...process.env }

function makeReq(body: unknown): NextRequest {
  return new NextRequest('http://localhost/api/retrieval/capability', {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-mcp-internal-token': 'test-token',
    },
    body: JSON.stringify(body),
  })
}

/** Every registration entry point route.ts's flag=false path hand-registers today. */
const HAND_REGISTERED_GLOBAL_PROBE_URIS = [
  'marsys://tool/maro/orchestrate',
  'marsys://tool/maro/mcp_surface',
  'marsys://resource/maro/profiles',
  // synergy/pipeline + synergy/cross_layer are DB-backed (no-op here — see
  // the completeness assertion below, which checks registration presence
  // via listCapabilityUris() rather than dispatching them).
]

beforeEach(() => {
  vi.resetModules()
  process.env.MCP_INTERNAL_TOKEN = 'test-token'
  delete process.env.MARSYS_FLAG_RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED
})

afterEach(() => {
  process.env = { ...ORIGINAL_ENV }
})

describe('RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED — defaults off', () => {
  it('DEFAULT_FLAGS carries the flag as false', async () => {
    const { DEFAULT_FLAGS } = await import('@/lib/config/feature_flags')
    expect(DEFAULT_FLAGS.RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED).toBe(false)
  })

  it('configService.getFlag reads false with no env override present', async () => {
    delete process.env.MARSYS_FLAG_RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED
    const { configService } = await import('@/lib/config/index')
    expect(configService.getFlag('RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED')).toBe(false)
  })
})

describe('flag=false (default) — regression-proof, byte-for-byte today behavior', () => {
  for (const uri of HAND_REGISTERED_GLOBAL_PROBE_URIS) {
    it(`still dispatches ${uri} (route.ts's own hand-registered list, unchanged)`, async () => {
      const { POST } = await import('../route')
      const res = await POST(makeReq({ uri, args: {} }))
      expect(res.status).toBe(200)
      const json = await res.json()
      expect(json.ok).toBe(true)
    })
  }

  it('does NOT serve synth_compose_large_n — the pre-existing documented gap is preserved', async () => {
    const { POST } = await import('../route')
    const res = await POST(
      makeReq({ uri: 'marsys://tool/synthesis/compose_large_n', args: {} })
    )
    expect(res.status).toBe(404)
    const json = await res.json()
    expect(json.ok).toBe(false)
    expect(json.error).toContain('Unknown capability URI')
  })

  it('unknown URI still 404s exactly as today (no change to the not-found path)', async () => {
    const { POST } = await import('../route')
    const res = await POST(makeReq({ uri: 'marsys://tool/does/not/exist', args: {} }))
    expect(res.status).toBe(404)
  })
})

describe('flag=true — single bootstrap exclusively from catalog.ts', () => {
  beforeEach(() => {
    process.env.MARSYS_FLAG_RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED = 'true'
  })

  for (const uri of HAND_REGISTERED_GLOBAL_PROBE_URIS) {
    it(`still dispatches ${uri} (present via catalog.ts after the completeness fix)`, async () => {
      const { POST } = await import('../route')
      const res = await POST(makeReq({ uri, args: {} }))
      expect(res.status).toBe(200)
      const json = await res.json()
      expect(json.ok).toBe(true)
    })
  }

  it('serves synth_compose_large_n — the reverse gap is closed under single bootstrap', async () => {
    const { POST } = await import('../route')
    const res = await POST(
      makeReq({ uri: 'marsys://tool/synthesis/compose_large_n', args: {} })
    )
    // per_chart scope with no chart_id supplied — must NOT be the "unknown
    // capability" 404; it should reach the real per-chart validation gate
    // instead (400 CHART_REQUIRED), proving the capability IS registered.
    expect(res.status).not.toBe(404)
    const json = await res.json()
    if (res.status !== 200) {
      const message = JSON.stringify(json)
      expect(message).not.toMatch(/Unknown capability URI/)
    }
  })

  it('unknown URI still 404s (single-bootstrap path preserves the not-found behavior)', async () => {
    const { POST } = await import('../route')
    const res = await POST(makeReq({ uri: 'marsys://tool/does/not/exist', args: {} }))
    expect(res.status).toBe(404)
  })
})

describe('flag=true vs flag=false — mechanical completeness diff (no missing, no duplicated)', () => {
  it('the flag=true registered URI set is a strict superset of the flag=false set, with the exact known GT-40 divergence', async () => {
    // ── Pass 1: flag=false — bootstrap route.ts's hand-maintained list, snapshot the registry.
    vi.resetModules()
    process.env.MCP_INTERNAL_TOKEN = 'test-token'
    delete process.env.MARSYS_FLAG_RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED
    {
      const { POST } = await import('../route')
      await POST(makeReq({ uri: 'marsys://tool/maro/mcp_surface', args: {} }))
    }
    const { listCapabilityUris: listFalse } = await import('@/lib/retrieval/registry')
    const falseUris = listFalse()

    // ── Pass 2: flag=true — bootstrap exclusively from catalog.ts, snapshot the registry.
    vi.resetModules()
    process.env.MCP_INTERNAL_TOKEN = 'test-token'
    process.env.MARSYS_FLAG_RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED = 'true'
    {
      const { POST } = await import('../route')
      await POST(makeReq({ uri: 'marsys://tool/maro/mcp_surface', args: {} }))
    }
    const { listCapabilityUris: listTrue } = await import('@/lib/retrieval/registry')
    const trueUris = listTrue()

    // No duplicates in either set (Map-backed registry guarantees this structurally;
    // asserted explicitly per this lane's instructions, not just trusted).
    expect(new Set(falseUris).size).toBe(falseUris.length)
    expect(new Set(trueUris).size).toBe(trueUris.length)

    // No missing: every URI route.ts serves today (flag=false) is still served
    // once single bootstrap is on (flag=true) — mechanically diffed, not hand-listed.
    const trueSet = new Set(trueUris)
    const missingUnderSingleBootstrap = falseUris.filter((uri) => !trueSet.has(uri))
    expect(
      missingUnderSingleBootstrap,
      `URIs served today (flag=false) but MISSING under single bootstrap (flag=true):\n${missingUnderSingleBootstrap.join('\n')}`
    ).toHaveLength(0)

    // No duplicated capability EITHER direction: the only URIs present under
    // flag=true but absent under flag=false are exactly the known reverse gap
    // (synth_compose_large_n) — a full symmetric mechanical diff, not a spot check.
    // (Verified by hand against a live run of this exact diff before writing this
    // assertion: FALSE_ONLY=[] / TRUE_ONLY=['marsys://tool/synthesis/compose_large_n'].)
    const falseSet = new Set(falseUris)
    const trueOnly = trueUris.filter((uri) => !falseSet.has(uri))
    expect(trueOnly).toEqual(['marsys://tool/synthesis/compose_large_n'])

    // The forward-divergent items (5 GT-40 originals + 1 newly-found —
    // marsys://tool/router/route was ALSO unreachable via catalog.ts before this
    // lane's fix, a bare non-calling `import` of router_registration.ts): present
    // in both sets (route.ts always hand-registered them; catalog.ts now also
    // registers them post-fix, so they survive the flag switch either way).
    const forwardDivergentItems = [
      'marsys://tool/synergy/pipeline',
      'marsys://tool/synergy/cross_layer',
      'marsys://tool/maro/orchestrate',
      'marsys://tool/maro/mcp_surface',
      'marsys://resource/maro/profiles',
      'marsys://tool/router/route',
    ]
    for (const uri of forwardDivergentItems) {
      expect(falseUris, `${uri} missing from flag=false set`).toContain(uri)
      expect(trueUris, `${uri} missing from flag=true set`).toContain(uri)
    }
  })
})
