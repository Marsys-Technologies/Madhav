/**
 * catalog.ts completeness — Retrieval Plane Elevation plan R-1 item 3
 * ("single bootstrap", W2b lane).
 *
 * GT-40 named 6 capabilities diverging between getCatalog() (catalog.ts) and
 * /api/retrieval/capability/route.ts's own separate registration list: 5
 * present in route.ts but absent from catalog.ts (synergy/pipeline,
 * synergy/cross_layer, maro/orchestrate, maro/mcp_surface,
 * resource/maro/profiles), and 1 the reverse (synth_compose_large_n).
 *
 * Re-verifying that finding for this fix surfaced a 7th, since-GT-40
 * divergence in the same failure class: `marsys://tool/router/route` was
 * ALSO unreachable via catalog.ts's getCatalog() (a bare, non-calling
 * `import './layers/router_registration'` — the file was imported but its
 * exported `registerRouterCapabilities()` was never invoked). Caught
 * mechanically by this lane's flag=false-vs-flag=true completeness diff in
 * single_bootstrap_flag.test.ts, not by re-reading the stale GT-40 list.
 *
 * This test proves the full 6-item forward gap (5 GT-40 + 1 newly-found) is
 * closed: catalog.ts's own getCatalog() now includes all 6, mechanically
 * (via listCapabilityUris()), not by trusting the import list. The reverse
 * item (synth_compose_large_n) was already correctly present in catalog.ts
 * before this lane — asserted here too so a future regression on either side
 * of the fix is caught.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'

beforeEach(() => {
  vi.resetModules()
})

const FORMERLY_MISSING_FROM_CATALOG = [
  'marsys://tool/synergy/pipeline',
  'marsys://tool/synergy/cross_layer',
  'marsys://tool/maro/orchestrate',
  'marsys://tool/maro/mcp_surface',
  'marsys://resource/maro/profiles',
  'marsys://tool/router/route',
]

describe('catalog.ts getCatalog() — GT-40 completeness fix', () => {
  it('includes all 6 previously-missing capabilities (5 GT-40 + 1 newly-found router/route)', async () => {
    const { getCatalog } = await import('./catalog')
    const uris = getCatalog().map((c) => c.uri)

    for (const uri of FORMERLY_MISSING_FROM_CATALOG) {
      expect(uris, `${uri} still missing from catalog.ts's getCatalog()`).toContain(uri)
    }
  })

  it('still includes synth_compose_large_n (the pre-existing correct reverse item)', async () => {
    const { getCatalog } = await import('./catalog')
    const uris = getCatalog().map((c) => c.uri)
    expect(uris).toContain('marsys://tool/synthesis/compose_large_n')
  })

  it('no duplicate URIs in the returned catalog', async () => {
    const { getCatalog } = await import('./catalog')
    const uris = getCatalog().map((c) => c.uri)
    expect(new Set(uris).size).toBe(uris.length)
  })

  it('the 5 fixed capabilities carry a real handler function (genuinely registered, not a placeholder)', async () => {
    const { getCatalog } = await import('./catalog')
    const catalog = getCatalog()
    for (const uri of FORMERLY_MISSING_FROM_CATALOG) {
      const cap = catalog.find((c) => c.uri === uri)
      expect(cap, `${uri} not found in catalog`).toBeDefined()
      const callable = cap!.handler ?? (cap as unknown as Record<string, unknown>)['loader']
      expect(typeof callable, `${uri} has no callable handler/loader`).toBe('function')
    }
  })
})
