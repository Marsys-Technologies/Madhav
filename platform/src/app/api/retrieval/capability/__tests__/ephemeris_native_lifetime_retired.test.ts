// @vitest-environment node
//
// SS N-373 (PR-S2) — `ephemeris_cache_native_lifetime` is RETIRED.
//
// The capability was `scope: 'global'`, so the per-chart entitlement gate on
// /api/retrieval/capability never ran for it; it ignored the caller and proxied a
// sidecar route that returned the native's HARD-CODED birth data to any holder of the
// shared MCP internal token. These tests pin its ABSENCE on every registry surface and
// on the live dispatch route, under both bootstrap paths.

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { NextRequest } from 'next/server'

const ORIGINAL_ENV = { ...process.env }

const RETIRED_NAME = 'ephemeris_cache_native_lifetime'
const RETIRED_URI = 'marsys://resource/ephemeris-cache/native-lifetime'
// The (never-resolvable) bridge-table spelling the old TOOL_NAME_TO_URI entry used.
const RETIRED_BRIDGE_URI = 'marsys://resource/L0/ephemeris_cache_native_lifetime'

function makeReq(body: unknown): NextRequest {
  return new NextRequest('http://localhost/api/retrieval/capability', {
    method: 'POST',
    headers: {
      'content-type': 'application/json',
      'x-mcp-internal-token': 'test-token',
      'x-mcp-user': 'test-user-uid',
      'x-mcp-key-id': 'mcp_test_KEY001',
    },
    body: JSON.stringify(body),
  })
}

beforeEach(() => {
  vi.resetModules()
  process.env.MCP_INTERNAL_TOKEN = 'test-token'
  delete process.env.MARSYS_FLAG_RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED
})

afterEach(() => {
  process.env = { ...ORIGINAL_ENV }
})

describe('registry surfaces carry no ephemeris_cache_native_lifetime', () => {
  it('getCatalog() has neither the retired name nor the retired URI', async () => {
    const { getCatalog } = await import('@/lib/retrieval/registry/catalog')
    const catalog = getCatalog()
    expect(catalog.length).toBeGreaterThan(0)
    expect(catalog.map((c) => c.name)).not.toContain(RETIRED_NAME)
    expect(catalog.map((c) => c.uri as string)).not.toContain(RETIRED_URI)
    expect(JSON.stringify(catalog)).not.toContain('native-lifetime')
  })

  it('getCapability(retired URI) is undefined and the sibling ephemeris_cache_year survives', async () => {
    const { getCatalog, getCapability } = await import('@/lib/retrieval/registry/catalog')
    getCatalog()
    expect(getCapability(RETIRED_URI as Parameters<typeof getCapability>[0])).toBeUndefined()
    expect(
      getCapability('marsys://resource/ephemeris-cache/year/{yyyy}' as Parameters<typeof getCapability>[0]),
    ).toBeDefined()
  })

  it('registerL0Capabilities() does not register it either (legacy bootstrap list)', async () => {
    const { registerL0Capabilities } = await import('@/lib/retrieval/registry/layers/L0_brahmagyan/index')
    const { listCapabilities } = await import('@/lib/retrieval/registry')
    registerL0Capabilities()
    expect(listCapabilities().map((c) => c.name)).not.toContain(RETIRED_NAME)
  })

  it('the MCP name-to-URI bridge table no longer maps the retired name', async () => {
    const { mcpToolNameToUri, getRegistryCapabilitiesForMcp } = await import(
      '@/lib/retrieval/registry/mcp_capability_bridge'
    )
    expect(mcpToolNameToUri(RETIRED_NAME)).toBeUndefined()
    const table = getRegistryCapabilitiesForMcp()
    expect(Object.keys(table)).not.toContain(RETIRED_NAME)
    expect(Object.values(table) as string[]).not.toContain(RETIRED_BRIDGE_URI)
    expect(Object.values(table) as string[]).not.toContain(RETIRED_URI)
  })
})

describe('/api/retrieval/capability answers unknown-capability for the retired capability', () => {
  for (const flag of ['true', 'false'] as const) {
    describe(`RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED=${flag}`, () => {
      beforeEach(() => {
        process.env.MARSYS_FLAG_RETRIEVAL_SINGLE_BOOTSTRAP_ENABLED = flag
      })

      for (const uri of [RETIRED_URI, RETIRED_BRIDGE_URI, `marsys://tool/L0/${RETIRED_NAME}`]) {
        it(`404 Unknown capability URI for ${uri}, no native data in the body`, async () => {
          const { POST } = await import('../route')
          const res = await POST(makeReq({ uri, args: {} }))
          expect(res.status).toBe(404)
          const text = JSON.stringify(await res.json())
          expect(text).toContain('Unknown capability URI')
          for (const needle of ['Abhisek', 'Bhubaneswar', '1984-02-05', '10:43']) {
            expect(text).not.toContain(needle)
          }
        })
      }
    })
  }
})
