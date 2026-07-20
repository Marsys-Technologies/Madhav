/**
 * service_manifest.test.ts — W1 Lane L1c sanity/parity checks
 * =====================================================================
 * Guards the two claims the manifest makes about itself:
 *   1. Its computed router+endpoint set exactly matches the committed
 *      openapi_snapshot.json (the mechanical-extraction ground truth) —
 *      so a hand-authored edit to service_manifest.json can't silently
 *      drift from the snapshot without this test catching it.
 *   2. The dark_set entries it declares (ka_graha_sancara, ka_muhurta_seva)
 *      are NOT present in the openapi snapshot's paths — i.e. the "dark"
 *      claim is itself checkable against the live-fetched ground truth,
 *      not just asserted in prose.
 *
 * This is a v1 static-file parity test, not a live network probe — it does
 * not re-fetch /openapi.json. Re-fetching + diffing against a fresh live
 * snapshot is future/W2 census-harness scope.
 */
import { describe, it, expect } from 'vitest'
import { serviceManifest, getTotalRouterEndpointCount, getDarkServiceIds } from '../index'
import openapiSnapshot from '../openapi_snapshot.json'

describe('service_manifest — W1 L1c', () => {
  it('validation block self-reports a clean match against the openapi snapshot', () => {
    expect(serviceManifest.validation.clean_match).toBe(true)
    expect(serviceManifest.validation.missing_from_openapi).toEqual([])
    expect(serviceManifest.validation.extra_in_openapi_not_in_manifest).toEqual([])
  })

  it('every manifest router endpoint actually exists in the committed openapi snapshot', () => {
    const openapiPaths = new Set<string>()
    for (const [path, methods] of Object.entries(openapiSnapshot.paths as Record<string, Record<string, unknown>>)) {
      for (const method of Object.keys(methods)) {
        openapiPaths.add(`${method.toUpperCase()} ${path}`)
      }
    }

    for (const router of serviceManifest.routers) {
      for (const ep of router.provides_apis) {
        expect(openapiPaths.has(`${ep.method} ${ep.path}`)).toBe(true)
      }
    }
  })

  it('reports 20 mounted routers with 49 total endpoints (+ /health = 50, matching the snapshot total)', () => {
    expect(serviceManifest.routers.length).toBe(20)
    expect(getTotalRouterEndpointCount()).toBe(49)
    const totalOpenapiPaths = Object.values(openapiSnapshot.paths).reduce(
      (n, methods) => n + Object.keys(methods as object).length,
      0,
    )
    expect(getTotalRouterEndpointCount() + serviceManifest.app_level_endpoints.length).toBe(totalOpenapiPaths)
  })

  it('dark_set services (ka_graha_sancara, ka_muhurta_seva) have no live path in the openapi snapshot', () => {
    // Neither dark service has a dedicated sidecar route today — confirm the
    // snapshot carries no path whose name implies one, so the "dark" claim
    // stays honest if a future wave silently adds one without updating dark_set.
    const allPaths = Object.keys(openapiSnapshot.paths)
    expect(allPaths.some(p => p.includes('ephemeris_at_t'))).toBe(false)
    expect(allPaths.some(p => p.includes('muhurta_score'))).toBe(false)
    expect(getDarkServiceIds()).toEqual(['ka_graha_sancara', 'ka_muhurta_seva'])
  })

  it('every router entry has a non-empty cost_class and at least one endpoint', () => {
    for (const router of serviceManifest.routers) {
      expect(['cheap', 'medium', 'expensive']).toContain(router.concurrency_cap.cost_class)
      expect(router.provides_apis.length).toBeGreaterThan(0)
      expect(router.endpoint_count).toBe(router.provides_apis.length)
    }
  })
})
